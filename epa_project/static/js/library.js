document.addEventListener('DOMContentLoaded', () => {
    const readingBooksContainer = document.getElementById('readingBooksContainer');
    const learningBooksContainer = document.getElementById('learningBooksContainer');
    const scrollLeftReading = document.getElementById('scrollLeftReading');
    const scrollRightReading = document.getElementById('scrollRightReading');
    const scrollLeftLearning = document.getElementById('scrollLeftLearning');
    const scrollRightLearning = document.getElementById('scrollRightLearning');
    const contentSelect = document.getElementById('contentSelect');
    const levelSelect = document.getElementById('levelSelect');

    if (!readingBooksContainer || !learningBooksContainer || !contentSelect || !levelSelect) {
        console.error('Required DOM elements are missing. Check your HTML IDs.');
        return;
    }

    // 읽고 있는 도서 로드
    async function loadReadingBooks() {
        readingBooksContainer.innerHTML = '';
        try {
            const response = await fetch('/api/reading_books/');
            if (!response.ok) throw new Error('Failed to load reading books');
            const books = await response.json();

            if (books.length === 0) {
                readingBooksContainer.innerHTML = '<p>아직 읽은 도서가 없습니다.</p>';
                return;
            }

            const bookshelf = document.createElement('div');
            bookshelf.classList.add('bookshelf');

            books.forEach((book) => {
                const bookElement = document.createElement('div');
                bookElement.classList.add('book');
                bookElement.textContent = `${book.title} (레벨 ${book.level})`;
                bookElement.onclick = () => {
                    window.location.href = `/lesson/${book.lesson_id}/`;
                };
                bookshelf.appendChild(bookElement);
            });

            readingBooksContainer.appendChild(bookshelf);
        } catch (error) {
            console.error('Error in loadReadingBooks:', error);
        }
    }

    // 학습 도서 목록 로드
    async function loadLearningBooks(contentType, level) {
        learningBooksContainer.innerHTML = '';
        try {
            const response = await fetch(`/api/lessons/?content_type=${contentType}&level=${level}`);
            if (!response.ok) throw new Error('Failed to load learning books');
            const books = await response.json();

            if (books.length === 0) {
                learningBooksContainer.innerHTML = '<p>해당 콘텐츠와 레벨에 학습 가능한 도서가 없습니다.</p>';
                return;
            }

            const bookshelf = document.createElement('div');
            bookshelf.classList.add('bookshelf');

            books.forEach((book) => {
                const bookElement = document.createElement('div');
                bookElement.classList.add('book');
                bookElement.textContent = `${book.title}`;
                bookElement.onclick = () => {
                    window.location.href = `/lesson/${book.id}/`;
                };
                bookshelf.appendChild(bookElement);
            });

            learningBooksContainer.appendChild(bookshelf);
        } catch (error) {
            console.error('Error in loadLearningBooks:', error);
        }
    }

    // 초기 데이터 로드
    loadReadingBooks();
    loadLearningBooks(contentSelect.value, levelSelect.value);

    // 콘텐츠 변경 시 학습 도서 목록 업데이트
    contentSelect.addEventListener('change', () => {
        loadLearningBooks(contentSelect.value, levelSelect.value);
    });

    // 레벨 변경 시 학습 도서 목록 업데이트
    levelSelect.addEventListener('change', () => {
        loadLearningBooks(contentSelect.value, levelSelect.value);
    });

    // 스크롤 버튼 이벤트
    if (scrollLeftReading && scrollRightReading) {
        scrollLeftReading.addEventListener('click', () => {
            readingBooksContainer.scrollLeft -= 300;
        });
        scrollRightReading.addEventListener('click', () => {
            readingBooksContainer.scrollLeft += 300;
        });
    }

    if (scrollLeftLearning && scrollRightLearning) {
        scrollLeftLearning.addEventListener('click', () => {
            learningBooksContainer.scrollLeft -= 300;
        });
        scrollRightLearning.addEventListener('click', () => {
            learningBooksContainer.scrollLeft += 300;
        });
    }
});
