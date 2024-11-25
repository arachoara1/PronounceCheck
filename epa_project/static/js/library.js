document.addEventListener('DOMContentLoaded', () => {
    const loadReadingBooksContainer = document.getElementById('readingBooksContainer');
    const loadLessonContainer = document.getElementById('learningBooksContainer');
    const scrollLeftReading = document.getElementById('scrollLeftReading');
    const scrollRightReading = document.getElementById('scrollRightReading');
    const scrollLeftLesson = document.getElementById('scrollLeftLearning');
    const scrollRightLesson = document.getElementById('scrollRightLearning');
    const contentSelect = document.getElementById('contentSelect');
    const levelSelect = document.getElementById('levelSelect');

    if (!loadReadingBooksContainer || !loadLessonContainer || !contentSelect || !levelSelect) {
        console.error('Required DOM elements are missing. Check your HTML IDs.');
        return;
    }

    // 읽고 있는 도서 로드
    async function loadReading() {
        loadReadingBooksContainer.innerHTML = '';
        try {
            const response = await fetch('/api/reading_books/');
            if (!response.ok) throw new Error('Failed to load reading books');
            const books = await response.json();

            if (books.length === 0) {
                loadReadingBooksContainer.innerHTML = '<p>아직 읽은 도서가 없습니다.</p>';
                return;
            }

            const bookshelf = document.createElement('div');
            bookshelf.classList.add('bookshelf');

            books.forEach((book) => {
                const bookElement = document.createElement('div');
                bookElement.classList.add('book');
                bookElement.textContent = `${book.title} (레벨 ${book.level})`;
                bookElement.onclick = () => {
                    window.location.href = `/lesson/${book.content_type}/${book.lesson_id}/`;
                };
                bookshelf.appendChild(bookElement);
            });

            loadReadingBooksContainer.appendChild(bookshelf);
        } catch (error) {
            console.error('Error in loadReading:', error);
        }
    }

    // 콘텐츠별 레벨 맵핑
    const levelsByContent = {
        phonics: [1, 2],
        novel: [1, 2, 3, 4, 5, 6, 7],
        conversation: [1, 2, 3, 4, 5, 6, 7],
    };

    // 레벨 드롭다운 업데이트
    function updateLevelOptions(contentType) {
        const levels = levelsByContent[contentType] || [];
        levelSelect.innerHTML = ''; // 기존 옵션 제거
        levels.forEach((level) => {
            const option = document.createElement('option');
            option.value = level;
            option.textContent = `레벨 ${level}`;
            levelSelect.appendChild(option);
        });
    }

    // 학습 도서 목록 로드
    async function loadLessons(contentType, level) {
        loadLessonContainer.innerHTML = '';
        try {
            const response = await fetch(`/api/lessons/?content_type=${contentType}&level=${level}`);
            if (!response.ok) throw new Error('Failed to load lessons');
            const books = await response.json();

            if (books.length === 0) {
                loadLessonContainer.innerHTML = '<p>해당 콘텐츠와 레벨에 학습 가능한 도서가 없습니다.</p>';
                return;
            }

            const bookshelf = document.createElement('div');
            bookshelf.classList.add('bookshelf');

            books.forEach((book) => {
                const bookElement = document.createElement('div');
                bookElement.classList.add('book');
                bookElement.textContent = `${book.title}`;
                bookElement.onclick = () => {
                    window.location.href = `/lesson/${contentType}/${book.id}/`;
                };
                bookshelf.appendChild(bookElement);
            });

            loadLessonContainer.appendChild(bookshelf);
        } catch (error) {
            console.error('Error in loadLessons:', error);
            loadLessonContainer.innerHTML = '<p>학습 도서를 불러오는 데 실패했습니다.</p>';
        }
    }

    // 콘텐츠 변경 시 레벨 드롭다운 업데이트 및 학습 도서 로드
    contentSelect.addEventListener('change', () => {
        const contentType = contentSelect.value;
        updateLevelOptions(contentType);
        const level = levelSelect.value || 1;
        loadLessons(contentType, level);
    });

    // 레벨 변경 시 학습 도서 로드
    levelSelect.addEventListener('change', () => {
        const contentType = contentSelect.value;
        const level = levelSelect.value;
        loadLessons(contentType, level);
    });

    // 초기 데이터 로드
    const initialContentType = contentSelect.value;
    updateLevelOptions(initialContentType);
    loadLessons(initialContentType, levelSelect.value || 1);
    loadReading();

    // 스크롤 버튼 이벤트
    if (scrollLeftReading && scrollRightReading) {
        scrollLeftReading.addEventListener('click', () => {
            loadReadingBooksContainer.scrollLeft -= 300;
        });
        scrollRightReading.addEventListener('click', () => {
            loadReadingBooksContainer.scrollLeft += 300;
        });
    }

    if (scrollLeftLesson && scrollRightLesson) {
        scrollLeftLesson.addEventListener('click', () => {
            loadLessonContainer.scrollLeft -= 300;
        });
        scrollRightLesson.addEventListener('click', () => {
            loadLessonContainer.scrollLeft += 300;
        });
    }
});
