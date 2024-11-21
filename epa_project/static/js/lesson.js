let recorder, audioBlob;
let recordingState = false; // 녹음 상태 변수
let recordingStartTime = null; // 녹음 시작 시간
let recordingTimer = null; // 녹음 타이머

// DOMContentLoaded 이벤트 리스너
document.addEventListener('DOMContentLoaded', () => {
    const sentences = {{ sentences|safe }}; // Django에서 전달된 문장 배열
    let currentSentenceIndex = {{ current_sentence_index }}; // 현재 문장 인덱스

    // 문장 보기 업데이트
    function updateSentenceView() {
        document.getElementById('lesson-sentence').textContent = sentences[currentSentenceIndex];

        // 이전/다음 버튼 활성화/비활성화
        document.getElementById('prev-btn').disabled = currentSentenceIndex === 0;
        document.getElementById('next-btn').disabled = currentSentenceIndex === sentences.length - 1;
    }

    // 이전 버튼 클릭
    document.getElementById('prev-btn').addEventListener('click', () => {
        if (currentSentenceIndex > 0) {
            currentSentenceIndex--;
            updateSentenceView();
        }
    });

    // 다음 버튼 클릭
    document.getElementById('next-btn').addEventListener('click', () => {
        if (currentSentenceIndex < sentences.length - 1) {
            currentSentenceIndex++;
            updateSentenceView();
        }
    });

    // 초기 문장 표시
    updateSentenceView();
});

// 녹음 시작
async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recorder = new MediaRecorder(stream);
    const audioChunks = [];

    recorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
    };

    recorder.onstop = () => {
        clearInterval(recordingTimer); // 타이머 정지
        recordingState = false; // 녹음 상태 변경
        updateRecordingStatus(); // 녹음 상태 UI 업데이트

        audioBlob = new Blob(audioChunks, { type: "audio/wav" });
        const audioUrl = URL.createObjectURL(audioBlob);
        document.getElementById("audio-preview").src = audioUrl;

        document.getElementById("upload-btn").disabled = false;
        document.getElementById("retry-btn").disabled = false; // 녹음 다시하기 버튼 활성화
    };

    recorder.start();
    recordingState = true; // 녹음 상태 변경
    recordingStartTime = Date.now(); // 녹음 시작 시간 기록
    startRecordingTimer(); // 타이머 시작
    updateRecordingStatus(); // 녹음 상태 UI 업데이트

    document.getElementById("stop-btn").disabled = false;
    document.getElementById("record-btn").disabled = true;
}

// 녹음 중지
function stopRecording() {
    recorder.stop();
    document.getElementById("stop-btn").disabled = true;
}

// 녹음 다시하기
function retryRecording() {
    audioBlob = null; // 기존 녹음 데이터 초기화
    document.getElementById("audio-preview").src = ""; // 미리보기 초기화
    document.getElementById("upload-btn").disabled = true; // 업로드 버튼 비활성화
    document.getElementById("retry-btn").disabled = true; // 다시하기 버튼 비활성화
    document.getElementById("record-btn").disabled = false; // 녹음 시작 버튼 활성화
    clearInterval(recordingTimer); // 기존 타이머 정지
    document.getElementById("recording-status").textContent = ""; // 상태 초기화

    alert("기존 녹음을 초기화하고 다시 시작합니다."); // 알림 메시지 추가
}

// 녹음 상태 및 시간 업데이트
function updateRecordingStatus() {
    const statusElement = document.getElementById("recording-status");
    if (recordingState) {
        const elapsedTime = Math.floor((Date.now() - recordingStartTime) / 1000);
        const minutes = Math.floor(elapsedTime / 60);
        const seconds = elapsedTime % 60;
        statusElement.textContent = `녹음 중... ${minutes}:${seconds.toString().padStart(2, "0")}`;
        statusElement.style.color = "red";
    } else {
        statusElement.textContent = "";
    }
}

// 타이머 시작
function startRecordingTimer() {
    recordingTimer = setInterval(updateRecordingStatus, 1000);
}

// 파일 업로드
async function uploadAudio() {
    const formData = new FormData();
    formData.append("audio_file", audioBlob, "recording.wav");
    formData.append("user", "{{ user.id }}");
    formData.append("lesson", "{{ lesson.id }}");
    formData.append("current_sentence_index", currentSentenceIndex); // 현재 문장 인덱스 추가

    try {
        const response = await fetch("/upload/audio/", {
            method: "POST",
            body: formData,
        });

        if (response.ok) {
            const result = await response.json();
            alert("녹음 파일 업로드 성공!");
            document.getElementById("retry-btn").disabled = true; // 업로드 성공 시 다시하기 버튼 비활성화
        } else {
            const error = await response.json();
            alert("녹음 파일 업로드 실패: " + error.error);
        }
    } catch (e) {
        alert("업로드 중 오류 발생: " + e.message);
    }
}
