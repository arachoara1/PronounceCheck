let mediaRecorder;
let recordedChunks = [];
let recordingStartTime;
let recordingInterval;

document.addEventListener("DOMContentLoaded", () => {
    const sentences = JSON.parse(document.getElementById("sentences-data").textContent);
    let currentSentenceIndex = parseInt(document.getElementById("current-sentence-index").textContent);

    function updateSentenceView() {
        document.getElementById("lesson-sentence").textContent = sentences[currentSentenceIndex];
        document.getElementById("prev-btn").disabled = currentSentenceIndex === 0;
        document.getElementById("next-btn").disabled = currentSentenceIndex === sentences.length - 1;
    }

    // 이전/다음 버튼 이벤트 리스너
    document.getElementById("prev-btn").addEventListener("click", () => {
        const index = parseInt(document.getElementById("current-sentence-index").value, 10);
        navigateSentence(index - 1);
    });
    
    document.getElementById("next-btn").addEventListener("click", () => {
        const index = parseInt(document.getElementById("current-sentence-index").value, 10);
        navigateSentence(index + 1);
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
        .then((stream) => {
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

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    recordedChunks.push(event.data);
                }
            };
        })
        .catch((error) => {
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
        const audioBlob = new Blob(recordedChunks, { type: "audio/wav" });
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
    document.getElementById("stop-btn").disabled = true;
    document.getElementById("audio-preview").src = "";
}

// 녹음 파일 업로드
async function uploadAudio() {
    if (recordedChunks.length === 0) {
        alert("녹음 파일이 없습니다. 녹음을 진행해주세요.");
        return;
    }

    const audioBlob = new Blob(recordedChunks, { type: "audio/wav" });
    const formData = new FormData();
    formData.append("audio_file", audioBlob, "recording.wav");

    // HTML에서 CSRF 토큰과 URL 읽기
    const csrfToken = document.getElementById("csrf-token").value;
    const uploadUrl = document.getElementById("upload-url").value;

    const lessonIdElement = document.getElementById("lesson-id");
    const contentTypeElement = document.getElementById("content-type");
    const levelElement = document.getElementById("level");
    const titleElement = document.getElementById("title");
    const sentenceElement = document.getElementById("lesson-sentence");
    const sentenceIndexElement = document.getElementById("current-sentence-index");

    formData.append("lesson", lessonIdElement ? lessonIdElement.value : "");
    formData.append("content_type", contentTypeElement ? contentTypeElement.value : "");
    formData.append("level", levelElement ? levelElement.value : "");
    formData.append("title", titleElement ? titleElement.value : "");
    formData.append("sentence", sentenceElement ? sentenceElement.textContent : "");
    formData.append("sentence_index", sentenceIndexElement ? sentenceIndexElement.value : "");

    try {
        const response = await fetch(uploadUrl, {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": csrfToken
            }
        });

        if (response.ok) {
            const result = await response.json();
            alert("녹음 파일 업로드 성공!");
            console.log(result);
            document.getElementById("upload-btn").disabled = true;
        } else {
            const error = await response.json();
            console.error("업로드 실패 응답:", error);
            alert(`업로드 실패: ${error.error}`);
        }
    } catch (error) {
        console.error("업로드 중 오류:", error);
        alert("업로드 중 오류가 발생했습니다.");
    }
}
