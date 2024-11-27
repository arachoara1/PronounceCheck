import os
import boto3
import librosa
import numpy as np
import parselmouth
from google.cloud import speech
from dotenv import load_dotenv
from scipy.spatial.distance import cosine
from django.utils.timezone import now
from core.models import UserPronunciation

# 환경 변수 로드
load_dotenv()

# Google Speech-to-Text API 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("KEY_PATH")
speech_client = speech.SpeechClient()

# S3 클라이언트 생성
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "ap-northeast-2"),
)

USER_BUCKET = os.getenv("AWS_STORAGE_BUCKET_NAME_USER", "user-audio-file")
STANDARD_BUCKET = os.getenv("AWS_STORAGE_BUCKET_NAME_STANDARD", "standard-audio-file")


def preprocess_audio(input_path, target_sr=16000):
    """오디오를 읽고 샘플링 속도를 변환"""
    y, sr = librosa.load(input_path, sr=None)
    if sr != target_sr:
        y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
    return y, target_sr


def recognize_speech(y, sr, language_code="en-US"):
    """Google Speech-to-Text API를 사용해 단어별 타임스탬프 추출"""
    import soundfile as sf
    from io import BytesIO

    buffer = BytesIO()
    sf.write(buffer, y, sr, format="WAV")
    buffer.seek(0)
    audio = speech.RecognitionAudio(content=buffer.read())
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sr,
        language_code=language_code,
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


def calculate_cosine_similarity(vec1, vec2):
    """벡터 간 코사인 유사도 계산 (길이 패딩 포함)"""
    if len(vec1) == 0 or len(vec2) == 0:
        return 0.0
    max_len = max(len(vec1), len(vec2))
    vec1 = np.pad(vec1, (0, max_len - len(vec1)), mode="constant")
    vec2 = np.pad(vec2, (0, max_len - len(vec2)), mode="constant")
    return 1 - cosine(vec1, vec2)


def analyze_audio(user_audio_path, ref_audio_path):
    """사용자와 기준 음성을 분석하여 결과 반환"""
    y_user, sr_user = preprocess_audio(user_audio_path)
    y_ref, sr_ref = preprocess_audio(ref_audio_path)

    user_timestamps = recognize_speech(y_user, sr_user)
    ref_timestamps = recognize_speech(y_ref, sr_ref)

    # 속도와 유사도 계산
    user_words = [word["word"] for word in user_timestamps]
    ref_words = [word["word"] for word in ref_timestamps]

    mispronounced_words = list(set(user_words) - set(ref_words))
    mispronounced_ratio = len(mispronounced_words) / len(ref_words) if ref_words else 0.0

    pitch_similarity = calculate_cosine_similarity(
        librosa.feature.chroma_cqt(y=y_user, sr=sr_user),
        librosa.feature.chroma_cqt(y=y_ref, sr=sr_ref),
    )

    return {
        "Pitch Pattern": pitch_similarity,
        "Mispronounced Words": {"ratio": mispronounced_ratio, "list": mispronounced_words},
    }


def process_and_save_results(user_key, ref_key):
    """S3 파일을 다운로드하고 분석 결과를 저장"""
    user_audio_path = "/tmp/user_audio.wav"
    ref_audio_path = "/tmp/ref_audio.wav"

    try:
        # S3에서 파일 다운로드
        s3.download_file(USER_BUCKET, user_key, user_audio_path)
        s3.download_file(STANDARD_BUCKET, ref_key, ref_audio_path)

        # 분석 함수 호출
        results = analyze_audio(user_audio_path, ref_audio_path)

        # 결과 저장 (예시: UserPronunciation 업데이트)
        user_audio_url = f"https://{USER_BUCKET}.s3.amazonaws.com/{user_key}"
        pronunciation = UserPronunciation.objects.filter(audio_file=user_audio_url).first()
        if pronunciation:
            pronunciation.pitch_similarity = results["Pitch Pattern"]
            pronunciation.mispronounced_words = results["Mispronounced Words"]["list"]
            pronunciation.mispronounced_ratio = results["Mispronounced Words"]["ratio"]
            pronunciation.processed_at = now()
            pronunciation.status = "completed"
            pronunciation.save()
        else:
            print("UserPronunciation 데이터가 존재하지 않습니다.")

    finally:
        # 임시 파일 삭제
        if os.path.exists(user_audio_path):
            os.remove(user_audio_path)
        if os.path.exists(ref_audio_path):
            os.remove(ref_audio_path)