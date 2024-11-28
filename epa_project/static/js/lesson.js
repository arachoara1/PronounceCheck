let mediaRecorder;
let recordedChunks = [];
let recordingStartTime;
let recordingInterval;

document.addEventListener("DOMContentLoaded", () => {
    const sentences = JSON.parse(document.getElementById('sentences-data').textContent);
    let currentSentenceIndex = parseInt(document.getElementById('current-sentence-index').textContent);

    function updateSentenceView() {
        document.getElementById("lesson-sentence").textContent = sentences[currentSentenceIndex];
        document.getElementById("prev-btn").disabled = currentSentenceIndex === 0;
        document.getElementById("next-btn").disabled = currentSentenceIndex === sentences.length - 1;
    }

    // 이전/다음 버튼 이벤트 리스너
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

    // 녹음 관련 버튼 이벤트 리스너
    document.getElementById("record-btn").addEventListener("click", startRecording);
    document.getElementById("stop-btn").addEventListener("click", stopRecording);
    document.getElementById("retry-btn").addEventListener("click", retryRecording);
    document.getElementById("upload-btn").addEventListener("click", uploadAudio);

    updateSentenceView();
});

// 녹음 시작
function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            
            recordingStartTime = Date.now();
            document.getElementById("recording-status").textContent = "녹음 중...";
            document.getElementById("record-btn").disabled = true;
            document.getElementById("stop-btn").disabled = false;

            recordingInterval = setInterval(() => {
                const elapsedSeconds = Math.floor((Date.now() - recordingStartTime) / 1000);
                document.getElementById("recording-status").textContent = `녹음 중... (${elapsedSeconds}초)`;
            }, 1000);

            mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0) {
                    recordedChunks.push(event.data);
                }
            };
        })
        .catch(error => {
            console.error("마이크 접근 실패:", error);
            alert("마이크 접근에 실패했습니다. 권한을 확인해주세요.");
        });
}

// 녹음 중지
function stopRecording() {
    mediaRecorder.stop();
    clearInterval(recordingInterval);
    document.getElementById("recording-status").textContent = "녹음 완료";
    document.getElementById("stop-btn").disabled = true;
    document.getElementById("upload-btn").disabled = false;
    document.getElementById("retry-btn").disabled = false;

    mediaRecorder.onstop = () => {
        const audioBlob = new Blob(recordedChunks, { type: 'audio/wav' });
        const audioURL = URL.createObjectURL(audioBlob);
        document.getElementById("audio-preview").src = audioURL;
    };
}

// 녹음 다시하기
function retryRecording() {
    recordedChunks = [];
    document.getElementById("recording-status").textContent = "녹음 상태: 대기 중";
    document.getElementById("upload-btn").disabled = true;
    document.getElementById("retry-btn").disabled = true;
    document.getElementById("record-btn").disabled = false;
    document.getElementById("audio-preview").src = "";
}

// 녹음 파일 업로드
async function uploadAudio() {
    if (recordedChunks.length === 0) {
        alert("녹음 파일이 없습니다. 녹음을 진행해주세요.");
        return;
    }

    const audioBlob = new Blob(recordedChunks, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append("user", document.getElementById('user-id').value);
    formData.append("lesson", document.getElementById('lesson-id').value);
    formData.append("content_type", document.getElementById('content-type').value);
    formData.append("level", document.getElementById('level').value);
    formData.append("title", document.getElementById('title').value);
    formData.append("sentence", document.getElementById('lesson-sentence').textContent);
    formData.append("audio_file", audioBlob, "recording.wav");

    try {
        const response = await fetch("/upload-pronunciation/", {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        });

        if (response.ok) {
            alert("녹음 파일 업로드 성공!");
            document.getElementById("upload-btn").disabled = true;
        } else {
            const error = await response.json();
            alert(`업로드 실패: ${error.error}`);
        }
    } catch (error) {
        console.error("업로드 실패:", error);
        alert("업로드 중 오류가 발생했습니다.");
    }
}