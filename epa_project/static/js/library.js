document.addEventListener('DOMContentLoaded', () => {
    const readingBooksContainer = document.getElementById('readingBooksContainer');
    const learningBooksContainer = document.getElementById('learningBooksContainer');
    const scrollLeftReading = document.getElementById('scrollLeftReading');
    const scrollRightReading = document.getElementById('scrollRightReading');
    const scrollLeftLearning = document.getElementById('scrollLeftLearning');
    const scrollRightLearning = document.getElementById('scrollRightLearning');
    let currentReadingPage = 1;
    let currentLearningPage = 1;

    // 읽고 있는 도서 로드
    function loadReadingBooks() {
        const bookshelf = document.createElement('div');
        bookshelf.classList.add('bookshelf');
        for (let i = 0; i < 10; i++) { // 가로로 10개씩
            const book = document.createElement('div');
            book.classList.add('book');
            book.textContent = `읽고 있는 책 ${currentReadingPage}-${i + 1}`;

            // 책 클릭 시 학습 화면으로 이동
            book.onclick = () => {
                const lessonId = (currentReadingPage - 1) * 10 + (i + 1); // 정수형 ID 생성
                window.location.href = `/lesson/${lessonId}/`;
            };

            bookshelf.appendChild(book);
        }
        readingBooksContainer.appendChild(bookshelf);
        currentReadingPage++;
    }

    // 학습 도서 로드
    function loadLearningBooks() {
        const bookshelf = document.createElement('div');
        bookshelf.classList.add('bookshelf');
        for (let i = 0; i < 10; i++) { // 가로로 10개씩
            const book = document.createElement('div');
            book.classList.add('book');
            book.textContent = `학습 책 ${currentLearningPage}-${i + 1}`;

            // 책 클릭 시 학습 화면으로 이동
            book.onclick = () => {
                const lessonId = (currentLearningPage - 1) * 10 + (i + 1); // 정수형 ID 생성
                window.location.href = `/lesson/${lessonId}/`;
            };

            bookshelf.appendChild(book);
        }
        learningBooksContainer.appendChild(bookshelf);
        currentLearningPage++;
    }

    // 스크롤 버튼 이벤트
    scrollLeftReading.addEventListener('click', () => {
        readingBooksContainer.scrollLeft -= 300;
    });
    scrollRightReading.addEventListener('click', () => {
        readingBooksContainer.scrollLeft += 300;
    });
    scrollLeftLearning.addEventListener('click', () => {
        learningBooksContainer.scrollLeft -= 300;
    });
    scrollRightLearning.addEventListener('click', () => {
        learningBooksContainer.scrollLeft += 300;
    });

    // 초기 데이터 로드
    loadReadingBooks();
    loadLearningBooks();
});
