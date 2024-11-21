let recorder, audioBlob;

// 녹음 시작
async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recorder = new MediaRecorder(stream);
    const audioChunks = [];

    recorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
    };

    recorder.onstop = () => {
        audioBlob = new Blob(audioChunks, { type: "audio/wav" });
        const audioUrl = URL.createObjectURL(audioBlob);
        document.getElementById("audio-preview").src = audioUrl;
        document.getElementById("upload-btn").disabled = false;
        document.getElementById("retry-btn").disabled = false; // 녹음 다시하기 버튼 활성화
    };

    recorder.start();
    document.getElementById("stop-btn").disabled = false;
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
    startRecording(); // 녹음 다시 시작
}

// 파일 업로드
async function uploadAudio() {
    const formData = new FormData();
    formData.append("audio_file", audioBlob, "recording.wav");
    formData.append("user", "{{ user.id }}");
    formData.append("lesson", "{{ lesson.id }}");

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
            document.getElementById("retry-btn").disabled = false; // 업로드 실패 시 다시하기 버튼 활성화
        }
    } catch (e) {
        alert("업로드 중 오류 발생: " + e.message);
        document.getElementById("retry-btn").disabled = false; // 업로드 실패 시 다시하기 버튼 활성화
    }
}
