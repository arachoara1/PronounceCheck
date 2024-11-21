document.addEventListener('DOMContentLoaded', () => {
    const readingBooksContainer = document.getElementById('readingBooksContainer');
    const learningBooksContainer = document.getElementById('learningBooksContainer');
    const scrollLeftReading = document.getElementById('scrollLeftReading');
    const scrollRightReading = document.getElementById('scrollRightReading');
    const scrollLeftLearning = document.getElementById('scrollLeftLearning');
    const scrollRightLearning = document.getElementById('scrollRightLearning');
    const contentSelect = document.getElementById('contentSelect');
    const levelSelect = document.getElementById('levelSelect');

    let currentReadingPage = 1;

    // 초기 학습 도서 표시
    function initializeLearningBooks() {
        levelSelect.innerHTML = `
            <option value="1">레벨 1</option>
            <option value="2">레벨 2</option>
        `;
        loadLearningBooks('storybook', '1');
    }

    // 읽고 있는 도서 로드
    function loadReadingBooks() {
        const bookshelf = document.createElement('div');
        bookshelf.classList.add('bookshelf');
        for (let i = 0; i < 10; i++) {
            const book = document.createElement('div');
            book.classList.add('book');
            book.textContent = `읽고 있는 책 ${currentReadingPage}-${i + 1}`;
            book.onclick = () => {
                const lessonId = (currentReadingPage - 1) * 10 + (i + 1);
                window.location.href = `/lesson/${lessonId}/`;
            };
            bookshelf.appendChild(book);
        }
        readingBooksContainer.appendChild(bookshelf);
        currentReadingPage++;
    }

    // 학습 도서 로드
    function loadLearningBooks(content, level) {
        learningBooksContainer.innerHTML = '';
        const bookshelf = document.createElement('div');
        bookshelf.classList.add('bookshelf');
        for (let i = 0; i < 10; i++) {
            const book = document.createElement('div');
            book.classList.add('book');
            book.textContent = `${content} - 레벨 ${level} 책 ${i + 1}`;
            book.onclick = () => {
                const lessonId = `${content}-${level}-${i + 1}`;
                window.location.href = `/lesson/${lessonId}/`;
            };
            bookshelf.appendChild(book);
        }
        learningBooksContainer.appendChild(bookshelf);
    }

    // 콘텐츠 변경 시 레벨 옵션 업데이트
    contentSelect.addEventListener('change', () => {
        const selectedContent = contentSelect.value;
        if (selectedContent === 'storybook') {
            levelSelect.innerHTML = `
                <option value="1">레벨 1</option>
                <option value="2">레벨 2</option>
            `;
        } else {
            levelSelect.innerHTML = `
                <option value="1">레벨 1</option>
                <option value="2">레벨 2</option>
                <option value="3">레벨 3</option>
                <option value="4">레벨 4</option>
                <option value="5">레벨 5</option>
                <option value="6">레벨 6</option>
                <option value="7">레벨 7</option>
            `;
        }
        loadLearningBooks(selectedContent, levelSelect.value);
    });

    // 레벨 변경 시 학습 도서 로드
    levelSelect.addEventListener('change', () => {
        const selectedContent = contentSelect.value;
        const selectedLevel = levelSelect.value;
        loadLearningBooks(selectedContent, selectedLevel);
    });

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
    initializeLearningBooks();
});
