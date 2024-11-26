document.addEventListener('DOMContentLoaded', () => {
    const readingContainer = document.getElementById('readingBooksContainer');
    const lessonContainer = document.getElementById('learningBooksContainer');
    const contentSelect = document.getElementById('contentSelect');
    const levelSelect = document.getElementById('levelSelect');
    const scrollLeftReading = document.getElementById('scrollLeftReading');
    const scrollRightReading = document.getElementById('scrollRightReading');
    const scrollLeftLesson = document.getElementById('scrollLeftLearning');
    const scrollRightLesson = document.getElementById('scrollRightLearning');

    const levelsByContent = {
        phonics: [1, 2],
        novel: [1, 2, 3, 4, 5, 6, 7],
        conversation: [1, 2, 3, 4, 5, 6, 7],
    };

    function updateLevelOptions(contentType) {
        const levels = levelsByContent[contentType] || [];
        levelSelect.innerHTML = '';
        levels.forEach(level => {
            const option = document.createElement('option');
            option.value = level;
            option.textContent = `레벨 ${level}`;
            levelSelect.appendChild(option);
        });
    }

    async function loadBooks(container, apiUrl, message, clickCallback) {
        container.innerHTML = '';
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error(`Failed to load books`);
            const books = await response.json();
            console.log('Loaded books:', books);
    
            if (!books || books.length === 0) {
                container.innerHTML = `<p class="no-books-message">${message}</p>`;
                return;
            }
    
            const bookshelf = document.createElement('div');
            bookshelf.classList.add('bookshelf');
    
            books.forEach(book => {
                const bookItem = document.createElement('div');
                bookItem.classList.add('book-item');
                
                const image = document.createElement('img');
                if (book.image_path) {
                    const cleanPath = book.image_path.replace(/^static\/|^\/static\//, '');
                    image.src = `/static/${cleanPath}`;
                }
                image.alt = book.title;
                image.classList.add('book-image');
                
                const title = document.createElement('p');
                title.textContent = book.title;
                title.classList.add('book-title');
                
                bookItem.appendChild(image);
                bookItem.appendChild(title);
                bookItem.onclick = () => clickCallback(book);
                
                bookshelf.appendChild(bookItem);
            });
    
            container.appendChild(bookshelf);
        } catch (error) {
            console.error('Error loading books:', error);
            container.innerHTML = `<p class="error-message">${message}</p>`;
        }
    }

    function setupScrollButtons(container, leftButton, rightButton) {
        if (!container || !leftButton || !rightButton) return;
        
        leftButton.addEventListener('click', () => {
            container.scrollLeft -= 300;
        });
        
        rightButton.addEventListener('click', () => {
            container.scrollLeft += 300;
        });
    }

    function loadReading() {
        loadBooks(
            readingContainer,
            '/api/reading_books/',
            '아직 읽은 도서가 없습니다.',
            book => window.location.href = `/lesson/${book.content_type}/${book.lesson_id}/`
        );
    }

    function loadLessons(contentType, level) {
        loadBooks(
            lessonContainer,
            `/api/lessons/?content_type=${contentType}&level=${level}`,
            '해당 콘텐츠와 레벨에 학습 가능한 도서가 없습니다.',
            book => window.location.href = `/lesson/${contentType}/${book.id}/`
        );
    }

    const initialContentType = contentSelect.value;
    updateLevelOptions(initialContentType);
    loadLessons(initialContentType, levelSelect.value || 1);
    loadReading();

    contentSelect.addEventListener('change', () => {
        const contentType = contentSelect.value;
        updateLevelOptions(contentType);
        loadLessons(contentType, levelSelect.value || 1);
    });

    levelSelect.addEventListener('change', () => {
        loadLessons(contentSelect.value, levelSelect.value);
    });

    setupScrollButtons(
        document.querySelector('#readingBooksContainer').parentElement,
        scrollLeftReading,
        scrollRightReading
    );

    setupScrollButtons(
        document.querySelector('#learningBooksContainer').parentElement,
        scrollLeftLesson,
        scrollRightLesson
    );
});