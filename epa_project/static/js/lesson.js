let recorder, audioBlob;
let recordingState = false; // 녹음 상태 변수
let recordingStartTime = null; // 녹음 시작 시간
let recordingTimer = null; // 녹음 타이머

// DOMContentLoaded 이벤트 리스너
document.addEventListener("DOMContentLoaded", () => {
    const sentences = JSON.parse("{{ sentences|safe }}"); // Django에서 전달된 문장 배열
    let currentSentenceIndex = parseInt("{{ current_sentence_index }}"); // 현재 문장 인덱스

    // 문장 보기 업데이트
    function updateSentenceView() {
        document.getElementById("lesson-sentence").textContent =
            sentences[currentSentenceIndex];

        // 이전/다음 버튼 활성화/비활성화
        document.getElementById("prev-btn").disabled =
            currentSentenceIndex === 0;
        document.getElementById("next-btn").disabled =
            currentSentenceIndex === sentences.length - 1;
    }

    // 이전 버튼 클릭
    document.getElementById("prev-btn").addEventListener("click", () => {
        if (currentSentenceIndex > 0) {
            currentSentenceIndex--;
            updateSentenceView();
        }
    });

    // 다음 버튼 클릭
    document.getElementById("next-btn").addEventListener("click", () => {
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
    try {
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

            // 녹음된 데이터로 Blob 생성
            audioBlob = new Blob(audioChunks, { type: "audio/wav" });

            // 디버깅용 로그 추가
            console.log("녹음된 데이터 크기:", audioChunks.length); // 녹음된 데이터 조각의 개수
            console.log("녹음된 데이터:", audioChunks); // 녹음된 데이터 내용 출력
            console.log("생성된 Blob 크기:", audioBlob.size); // Blob의 크기(바이트 단위)
            console.log("Blob 유형:", audioBlob.type); // Blob의 MIME 유형 (audio/wav)

            // Blob에서 URL 생성 및 오디오 미리보기
            const audioUrl = URL.createObjectURL(audioBlob);
            console.log("Blob URL:", audioUrl); // Blob URL 확인
            document.getElementById("audio-preview").src = audioUrl;

            // 업로드 및 다시하기 버튼 활성화
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
    } catch (error) {
        alert("녹음을 시작할 수 없습니다: " + error.message);
    }
}

// 녹음 중지
function stopRecording() {
    if (recorder) {
        recorder.stop();
        document.getElementById("stop-btn").disabled = true;
    }
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
        statusElement.textContent = `녹음 중... ${minutes}:${seconds
            .toString()
            .padStart(2, "0")}`;
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
    if (!audioBlob) {
        alert("녹음 파일이 없습니다. 녹음을 진행해주세요.");
        return;
    }

    const formData = new FormData();
    formData.append("audio_file", audioBlob, "recording.wav");
    formData.append("user", "{{ user.id }}");
    formData.append("lesson", "{{ lesson.id }}");
    formData.append("current_sentence_index", currentSentenceIndex);

    // 디버깅: FormData 출력
    console.log("FormData Content:", formData);

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
            document.getElementById("retry-btn").disabled = true; // 업로드 성공 시 다시하기 버튼 비활성화
        } else {
            const error = await response.json();
            alert("녹음 파일 업로드 실패: " + error.error);
            console.error("서버 응답:", error);
        }
    } catch (e) {
        alert("업로드 중 오류 발생: " + e.message);
        console.error("업로드 오류:", e);
    }
}
