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
                if (!book || !book.content_type || !book.lesson_id) {
                    console.error('Invalid book data:', book);
                    return;
                }

                const bookElement = document.createElement('div');
                bookElement.classList.add('book-item');
                
                const image = document.createElement('img');
                if (book.image_path) {
                    const cleanPath = book.image_path.replace(/^static\/|^\/static\//, '');
                    image.src = `/static/${cleanPath}`;
                }
                image.alt = book.title || '도서 이미지';
                image.classList.add('book-image');
                
                const title = document.createElement('p');
                title.textContent = book.title || '제목 없음';
                title.classList.add('book-title');
                
                bookElement.appendChild(image);
                bookElement.appendChild(title);
                
                bookElement.onclick = () => {
                    try {
                        if (typeof book.content_type === 'string' && 
                            typeof book.lesson_id === 'number') {
                            window.location.href = `/lesson/${book.content_type}/${book.lesson_id}/`;
                        } else {
                            throw new Error('Invalid book data');
                        }
                    } catch (error) {
                        console.error('Navigation error:', error);
                    }
                };
                
                bookshelf.appendChild(bookElement);
            });

            loadReadingBooksContainer.appendChild(bookshelf);
        } catch (error) {
            console.error('Error in loadReading:', error);
            loadReadingBooksContainer.innerHTML = '<p>도서를 불러오는데 실패했습니다.</p>';
        }
    }

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
                bookElement.classList.add('book-item');
                
                const image = document.createElement('img');
                if (book.image_path) {
                    image.src = `/static/${book.image_path}`;  // 경로 단순화
                }
                image.alt = book.title;
                image.classList.add('book-image');
                
                const title = document.createElement('p');
                title.textContent = book.title;
                title.classList.add('book-title');
                
                bookElement.appendChild(image);
                bookElement.appendChild(title);
                bookElement.onclick = () => {
                    window.location.href = `/lesson/${contentType}/${book.id}/`;  // contentType 사용
                };
                bookshelf.appendChild(bookElement);
            });

            loadLessonContainer.appendChild(bookshelf);
        } catch (error) {
            console.error('Error in loadLessons:', error);
            loadLessonContainer.innerHTML = '<p>학습 도서를 불러오는데 실패했습니다.</p>';
        }
    }

    const levelsByContent = {
        phonics: [1, 2],
        novel: [1, 2, 3, 4, 5, 6, 7],
        conversation: [1, 2, 3, 4, 5, 6, 7],
    };

    function updateLevelOptions(contentType) {
        const levels = levelsByContent[contentType] || [];
        levelSelect.innerHTML = '';
        levels.forEach((level) => {
            const option = document.createElement('option');
            option.value = level;
            option.textContent = `레벨 ${level}`;
            levelSelect.appendChild(option);
        });
    }

    contentSelect.addEventListener('change', () => {
        const contentType = contentSelect.value;
        updateLevelOptions(contentType);
        const level = levelSelect.value || 1;
        loadLessons(contentType, level);
    });

    levelSelect.addEventListener('change', () => {
        const contentType = contentSelect.value;
        const level = levelSelect.value;
        loadLessons(contentType, level);
    });

    // 초기 로드
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