<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lesson</title>
    <style>
        /* CSS 코드 */
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }

        .content-overlay {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%); /* 콘텐츠를 책 중앙에 정렬 */
            width: 90%; /* 콘텐츠가 책 안에 잘 맞도록 조정 */
            height: auto;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            background-color: rgba(255, 255, 255, 0.8); /* 약간 투명한 배경 추가 */
            border-radius: 5px;
            padding: 20px;
            box-sizing: border-box;
        }

        .lesson-container {
             position: relative;
             width: 800px; /* 책 너비를 더 크게 */
             height: 600px; /* 책 높이를 더 크게 */
             background: url("{% static 'images/book.jpg' %}") no-repeat center center;
             background-size: contain; /* 책 이미지를 비율에 맞게 조정 */
             overflow: hidden;
             border-radius: 10px;
             box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); /* 그림자 유지 */
        }    

        h1, h2, h3 {
            margin: 10px 0;
        }

        p {
            margin: 5px 0;
        }

        .buttons, .navigation-buttons {
                margin-top: 15px;
        }

        button {
            padding: 10px 20px;
            margin: 5px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }

        button:hover {
            background-color: #45a049;
        }

        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }

        audio {
            margin-top: 10px;
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="content-overlay">
        <h1 id="lesson-title">{{ lesson.title }}</h1>
        <h2 id="lesson-title-kor">{{ lesson.title_kor }}</h2>

        <div class="content">
            <h2>레벨: <span id="lesson-level">{{ lesson.level }}</span></h2>
            <p id="lesson-sentence">{{ current_sentence }}</p>
            <p id="lesson-sentence-kor">{{ current_sentence_kor }}</p>
        </div>

        <div>
            <h3>마지막으로 읽은 시간</h3>
            <p>{{ lesson.last_read_at }}</p>
        </div>

        <div class="content">
            <h3>표준 발음 오디오</h3>
            <audio id="lesson-audio" controls>
                <source src="{{ lesson.audio_file }}" type="audio/mpeg">
                오디오 파일을 재생할 수 없습니다.
            </audio>
        </div>

        <div class="navigation-buttons">
            <button id="prev-btn" {% if not is_prev_enabled %}disabled{% endif %} onclick="navigateSentence({{ current_sentence_index|add:'-1' }})">이전</button>
            <button id="next-btn" {% if not is_next_enabled %}disabled{% endif %} onclick="navigateSentence({{ current_sentence_index|add:'1' }})">다음</button>
        </div>

        <div id="recording-status">녹음 상태: 대기 중</div>

        <div class="buttons">
            <button id="record-btn" onclick="startRecording()">녹음 시작</button>
            <button id="stop-btn" onclick="stopRecording()" disabled>녹음 중지</button>
            <button id="upload-btn" onclick="uploadAudio()" disabled>업로드</button>
            <button id="retry-btn" onclick="retryRecording()" disabled>녹음 다시하기</button>
        </div>
        <audio id="audio-preview" controls></audio>
    </div>

    <script>
        /* JavaScript 코드 */
        let recorder, audioBlob;
        let recordingState = false;
        let recordingStartTime = null;
        let recordingTimer = null;

        document.addEventListener("DOMContentLoaded", () => {
            const sentences = JSON.parse("{{ sentences|safe }}");
            let currentSentenceIndex = parseInt("{{ current_sentence_index }}");

            function updateSentenceView() {
                document.getElementById("lesson-sentence").textContent =
                    sentences[currentSentenceIndex];

                document.getElementById("prev-btn").disabled =
                    currentSentenceIndex === 0;
                document.getElementById("next-btn").disabled =
                    currentSentenceIndex === sentences.length - 1;
            }

            document.getElementById("prev-btn").addEventListener("click", () => {
                if (currentSentenceIndex > 0) {
                    currentSentenceIndex--;
                    updateSentenceView();
                }
            });

            document.getElementById("next-btn").addEventListener("click", () => {
                if (currentSentenceIndex < sentences.length - 1) {
                    currentSentenceIndex++;
                    updateSentenceView();
                }
            });

            updateSentenceView();
        });

        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                recorder = new MediaRecorder(stream);
                const audioChunks = [];

                recorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };

                recorder.onstop = () => {
                    clearInterval(recordingTimer);
                    recordingState = false;
                    updateRecordingStatus();

                    audioBlob = new Blob(audioChunks, { type: "audio/wav" });

                    const audioUrl = URL.createObjectURL(audioBlob);
                    document.getElementById("audio-preview").src = audioUrl;

                    document.getElementById("upload-btn").disabled = false;
                    document.getElementById("retry-btn").disabled = false;
                };

                recorder.start();
                recordingState = true;
                recordingStartTime = Date.now();
                startRecordingTimer();
                updateRecordingStatus();

                document.getElementById("stop-btn").disabled = false;
                document.getElementById("record-btn").disabled = true;
            } catch (error) {
                alert("녹음을 시작할 수 없습니다: " + error.message);
            }
        }

        function stopRecording() {
            if (recorder) {
                recorder.stop();
                document.getElementById("stop-btn").disabled = true;
            }
        }

        function retryRecording() {
            audioBlob = null;
            document.getElementById("audio-preview").src = "";
            document.getElementById("upload-btn").disabled = true;
            document.getElementById("retry-btn").disabled = true;
            document.getElementById("record-btn").disabled = false;
            clearInterval(recordingTimer);
            document.getElementById("recording-status").textContent = "";
        }

        function updateRecordingStatus() {
            const statusElement = document.getElementById("recording-status");
            if (recordingState) {
                const elapsedTime = Math.floor((Date.now() - recordingStartTime) / 1000);
                const minutes = Math.floor(elapsedTime / 60);
                const seconds = elapsedTime % 60;
                statusElement.textContent = `녹음 중... ${minutes}:${seconds
                    .toString()
                    .padStart(2, "0")}`;
                statusElement.style.color = "red";
            } else {
                statusElement.textContent = "";
            }
        }

        function startRecordingTimer() {
            recordingTimer = setInterval(updateRecordingStatus, 1000);
        }

        async function uploadAudio() {
            if (!audioBlob) {
                alert("녹음 파일이 없습니다. 녹음을 진행해주세요.");
                return;
            }

            const formData = new FormData();
            formData.append("audio_file", audioBlob, "recording.wav");
            formData.append("user", "{{ user.id }}");
            formData.append("lesson", "{{ lesson.id }}");
            formData.append("current_sentence_index", currentSentenceIndex);

            try {
                const response = await fetch("{% url 'upload_user_pronunciation' %}", {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-CSRFToken": "{{ csrf_token }}",
                    },
                });

                if (response.ok) {
                    const result = await response.json();
                    alert("녹음 파일 업로드 성공!");
                    document.getElementById("retry-btn").disabled = true;
                } else {
                    const error = await response.json();
                    alert("녹음 파일 업로드 실패: " + error.error);
                }
            } catch (e) {
                alert("업로드 중 오류 발생: " + e.message);
            }
        }
    </script>
</body>
</html>

