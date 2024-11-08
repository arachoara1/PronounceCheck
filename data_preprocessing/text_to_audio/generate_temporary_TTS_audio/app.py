from flask import Flask, jsonify, request, send_from_directory
import os
from gtts import gTTS

app = Flask(__name__)

# TTS 생성 함수
def generate_tts(text):
    filename = "temp_audio.mp3"
    tts = gTTS(text)
    tts.save(filename)
    return filename

# HTML 페이지 제공
@app.route('/')
def home():
    return '''
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <title>Audio Recorder</title>
      </head>
      <body>
        <h1>TTS 음성 생성, 사용자 녹음, 그리고 저장 예제</h1>
        
        <p>예시 텍스트: "Hello, this is an example text."</p>
        <button onclick="generateAndPlayTTS()">TTS 음성 생성 및 재생</button>
        <audio id="audioPlayer" controls></audio>
        
        <p>사용자 음성 녹음:</p>
        <button onclick="startRecording()">녹음 시작</button>
        <button onclick="stopRecording()">녹음 중지</button>
        <audio id="userAudioPlayer" controls></audio>
        
        <button onclick="saveRecording()">다음 (녹음 저장 및 TTS 삭제)</button>

        <script>
          let mediaRecorder;
          let audioChunks;

          function generateAndPlayTTS() {
            fetch('/generate_tts')
              .then(response => response.json())
              .then(data => {
                const audioPlayer = document.getElementById("audioPlayer");
                audioPlayer.src = data.url;
                audioPlayer.play();
              });
          }

          function startRecording() {
            navigator.mediaDevices.getUserMedia({ audio: true })
              .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = event => {
                  audioChunks.push(event.data);
                };
                
                mediaRecorder.onstop = () => {
                  const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                  const audioUrl = URL.createObjectURL(audioBlob);
                  const userAudioPlayer = document.getElementById("userAudioPlayer");
                  userAudioPlayer.src = audioUrl;
                  
                  // 녹음 파일 서버로 전송
                  const formData = new FormData();
                  formData.append('audio', audioBlob, 'user_audio.wav');
                  fetch('/save_recording', { method: 'POST', body: formData });
                };
                
                mediaRecorder.start();
              });
          }

          function stopRecording() {
            mediaRecorder.stop();
          }

          function saveRecording() {
            fetch('/delete_tts')
              .then(response => response.json())
              .then(data => alert(data.status));
          }
        </script>
      </body>
    </html>
    '''

# TTS 생성 엔드포인트
@app.route('/generate_tts')
def generate_tts_endpoint():
    text = "Hello, this is an example text."
    filename = generate_tts(text)
    return jsonify({"url": f"/static/{filename}"})

# TTS 음성파일 제공
@app.route('/static/<path:filename>')
def serve_audio(filename):
    return send_from_directory('.', filename)

# TTS 삭제 엔드포인트
@app.route('/delete_tts')
def delete_tts_endpoint():
    if os.path.exists("temp_audio.mp3"):
        os.remove("temp_audio.mp3")
    return jsonify({"status": "TTS 파일이 삭제되었습니다."})

# 사용자 녹음 저장 엔드포인트
@app.route('/save_recording', methods=['POST'])
def save_recording():
    audio = request.files['audio']
    audio.save("user_audio.wav")  # 녹음 파일을 로컬에 저장
    return jsonify({"status": "녹음 파일이 저장되었습니다."})

if __name__ == '__main__':
    app.run(port=5000)
