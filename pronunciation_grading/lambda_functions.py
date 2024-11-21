import boto3
import os
import librosa
import soundfile as sf
from google.cloud import speech
import parselmouth
from scipy.spatial.distance import cosine
import pandas as pd

# Google Cloud Speech-to-Text API 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/google_credentials.json"  # Lambda 환경 변수로 설정
speech_client = speech.SpeechClient()

# 샘플링 속도 확인
def check_sampling_rate(audio_path):
    _, sr = librosa.load(audio_path, sr=None)
    print(f"{audio_path} 샘플링 속도: {sr} Hz")
    return sr

# 샘플링 속도 변경
def resample_audio(input_path, output_path, target_sr):
    y, sr = librosa.load(input_path, sr=None)
    y_resampled = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
    sf.write(output_path, y_resampled, target_sr)
    print(f"{input_path} -> {output_path} 샘플링 속도를 {target_sr} Hz로 변경 완료")

# Google Speech-to-Text 단어별 타임스탬프 추출
def get_word_timestamps(audio_path):
    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=48000,
        language_code="en-US",
        enable_word_time_offsets=True,
    )

    response = speech_client.recognize(config=config, audio=audio)
    word_timestamps = []
    for result in response.results:
        for word_info in result.alternatives[0].words:
            word_timestamps.append(
                {
                    "word": word_info.word,
                    "start_time": word_info.start_time.total_seconds(),
                    "end_time": word_info.end_time.total_seconds(),
                }
            )
    return word_timestamps

# 단어별 피치, 포먼트, 강세 분석
def analyze_audio_features(audio_path, word_info):
    y, sr = librosa.load(audio_path, sr=None)
    start_sample = int(word_info["start_time"] * sr)
    end_sample = int(word_info["end_time"] * sr)
    word_audio = y[start_sample:end_sample]

    pitches, _ = librosa.piptrack(y=word_audio, sr=sr)
    pitch = pitches[pitches > 0].mean() if pitches[pitches > 0].size > 0 else 0

    intensity = librosa.feature.rms(y=word_audio).mean()

    sound = parselmouth.Sound(audio_path)
    formant = parselmouth.praat.call(
        sound, "To Formant (burg)", 0.025, 5, 5500, 0.025, 50
    )
    f1 = parselmouth.praat.call(
        formant,
        "Get value at time",
        1,
        (word_info["start_time"] + word_info["end_time"]) / 2,
        "Hertz",
        "Linear",
    )
    f2 = parselmouth.praat.call(
        formant,
        "Get value at time",
        2,
        (word_info["start_time"] + word_info["end_time"]) / 2,
        "Hertz",
        "Linear",
    )

    return pitch, intensity, (f1, f2)

# 두 음성 파일의 단어별 비교
def compare_audio_features(audio_path1, audio_path2):
    native_timestamps = get_word_timestamps(audio_path1)
    user_timestamps = get_word_timestamps(audio_path2)

    results = []
    min_length = min(len(native_timestamps), len(user_timestamps))
    for i in range(min_length):
        native_word = native_timestamps[i]
        user_word = user_timestamps[i]

        native_duration = native_word["end_time"] - native_word["start_time"]
        user_duration = user_word["end_time"] - user_word["start_time"]
        duration_difference = user_duration - native_duration

        native_pitch, native_intensity, native_formants = analyze_audio_features(audio_path1, native_word)
        user_pitch, user_intensity, user_formants = analyze_audio_features(audio_path2, user_word)

        pitch_ratio = user_pitch / native_pitch if native_pitch != 0 else 0
        intensity_ratio = user_intensity / native_intensity if native_intensity != 0 else 0
        formant_ratio_f1 = user_formants[0] / native_formants[0] if native_formants[0] != 0 else 0
        formant_ratio_f2 = user_formants[1] / native_formants[1] if native_formants[1] != 0 else 0

        results.append({
            "Word": native_word["word"],
            "Pitch Ratio": round(pitch_ratio, 2),
            "Intensity Ratio": round(intensity_ratio, 2),
            "Formant Ratio (F1)": round(formant_ratio_f1, 2),
            "Formant Ratio (F2)": round(formant_ratio_f2, 2),
            "Duration Difference (s)": round(duration_difference, 2),
        })
    return pd.DataFrame(results)

# Lambda 핸들러
def lambda_handler(event, context):
    s3 = boto3.client("s3")

    for record in event["Records"]:
        user_bucket = record["s3"]["bucket"]["name"]
        user_key = record["s3"]["object"]["key"]
        user_audio_path = f"/tmp/{user_key.split('/')[-1]}"
        s3.download_file(user_bucket, user_key, user_audio_path)

        standard_bucket = os.environ["STANDARD_BUCKET_NAME"]
        standard_key = "standard_audio.wav"
        standard_audio_path = "/tmp/standard_audio.wav"
        s3.download_file(standard_bucket, standard_key, standard_audio_path)

        # 샘플링 속도 변경 (필요한 경우)
        target_sr = 48000
        if check_sampling_rate(user_audio_path) != target_sr:
            resample_audio(user_audio_path, user_audio_path, target_sr)
        if check_sampling_rate(standard_audio_path) != target_sr:
            resample_audio(standard_audio_path, standard_audio_path, target_sr)

        # 점수 계산
        comparison_results = compare_audio_features(standard_audio_path, user_audio_path)

        # 결과 출력
        print(comparison_results)

        # 선택적으로 API나 S3에 결과 저장 가능
        return {
            "statusCode": 200,
            "body": comparison_results.to_dict(orient="records"),
        }
