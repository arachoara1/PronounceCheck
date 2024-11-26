**library.html**
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>서재</title>
    {% load static %}
    <link rel="stylesheet" href="{% static 'css/library.css' %}">
    <script src="{% static 'js/library.js' %}" defer></script>
</head>
<body>
    <div class="section-container">
        <h1>{{ user.username }}님의 서재</h1>

        <!-- 읽고 있는 도서 섹션 -->
        <h2>읽고 있는 도서</h2>
        <div class="bookshelf-container-wrapper">
            <button class="scroll-button left" id="scrollLeftReading">&lt;</button>
            <div class="bookshelf-container" id="readingBooksContainer">
                <!-- 정적 이미지 추가 -->
                <img src="{% static 'lesson_images/Phonics/level_2/호흡과.jpg' %}" alt="읽고 있는 도서 이미지" class="book-image">
                <img src="{% static 'lesson_images/Phonics/level_2/다른책.jpg' %}" alt="다른 읽고 있는 도서 이미지" class="book-image">
            </div>
            <button class="scroll-button right" id="scrollRightReading">&gt;</button>
        </div>

        <!-- 학습 도서 목록 섹션 -->
        <h2>학습 도서 목록</h2>
        <div class="dropdown">
            <label for="contentSelect">콘텐츠:</label>
            <select id="contentSelect">
                <option value="phonics">파닉스</option>
                <option value="novel">동화</option>
                <option value="conversation">회화</option>
            </select>
        </div>
        <div class="dropdown">
            <label for="levelSelect">레벨:</label>
            <select id="levelSelect">
                <option value="1">레벨 1</option>
                <option value="2">레벨 2</option>
            </select>
        </div>
        <div class="bookshelf-container-wrapper">
            <button class="scroll-button left" id="scrollLeftLearning">&lt;</button>
            <div class="bookshelf-container" id="learningBooksContainer">
                <!-- 정적 이미지 추가 -->
                <img src="{% static 'lesson_images/Phonics/level_1/샘플이미지.png' %}" alt="학습 도서 이미지" class="book-image">
                <img src="{% static 'lesson_images/Phonics/level_1/다른샘플.jpg' %}" alt="다른 학습 도서 이미지" class="book-image">
            </div>
            <button class="scroll-button right" id="scrollRightLearning">&gt;</button>
        </div>

        <!-- 동적 렌더링 추가 -->
        {% for content_type, levels in image_data.items %}
            <h2>{{ content_type }}</h2>
            {% for level, images in levels.items %}
                <h3>{{ level }}</h3>
                <div class="bookshelf-container-wrapper">
                    <div class="bookshelf-container">
                        {% for img in images %}
                        <div class="book-item">
                            <img src="{% static img.path %}" alt="{{ img.name }}" class="book-image">
                            <p class="book-title">{{ img.name }}</p>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            {% endfor %}
        {% endfor %}

        <a href="{% url 'mypage' %}" class="button">마이페이지로 돌아가기</a>
    </div>
</body>
</html>


**library.css**
body {
    font-family: Arial, sans-serif;
    margin: 2rem;
    overflow-x: hidden;
}

h1, h2 {
    text-align: center;
}

.section-container {
    width: 70%;
    margin: 0 auto;
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 10px;
    background-color: #f9f9f9;
}

.dropdown {
    display: inline-block;
    margin: 10px;
}

select {
    padding: 5px;
    font-size: 14px;
}

.bookshelf-container-wrapper {
    margin: 20px auto; /* 컨테이너 간 여백 */
    position: relative; /* 스크롤 버튼과 연계 */
}

.bookshelf-container {
    overflow-x: auto;
    white-space: nowrap;
    border: 1px solid #ddd;
    display: flex;
    gap: 10px;
    scroll-behavior: smooth;
    padding: 10px;
    height: auto;
}

.bookshelf {
    flex-shrink: 0;
    display: flex;
    flex-wrap: nowrap;
    gap: 10px;
}

/* book-item은 이미지와 텍스트를 포함한 컨테이너 */
.book-item {
    width: 150px; /* 컨테이너 너비 */
    height: 220px; /* 컨테이너 높이 */
    border: 1px solid #ddd; /* 테두리 */
    display: flex; /* Flexbox 사용 */
    flex-direction: column; /* 세로 정렬 */
    justify-content: space-between; /* 이미지와 텍스트 사이 간격 유지 */
    align-items: center; /* 수평 중앙 정렬 */
    overflow: hidden; /* 넘치는 이미지 자르기 */
    padding: 10px; /* 내부 여백 추가 */
    border-radius: 8px; /* 박스 모서리 둥글게 */
    background-color: #f9f9f9; /* 배경색 */
    transition: background-color 0.3s; /* hover 효과 추가 */
}

.book-item:hover {
    background-color: #f0f0f0; /* hover 시 배경색 변경 */
}

/* 이미지 스타일 */
.book-image {
    width: 100%; /* 박스 너비에 맞춤 */
    height: 150px; /* 고정된 높이 */
    object-fit: cover; /* 이미지 비율 유지하며 박스에 맞춤 */
    border-radius: 4px; /* 이미지 모서리 둥글게 */
}

/* 제목 스타일 */
.book-title {
    font-size: 14px; /* 텍스트 크기 */
    text-align: center; /* 텍스트 중앙 정렬 */
    color: #333; /* 제목 색상 */
    margin-top: 5px; /* 이미지와 텍스트 사이 간격 */
    word-wrap: break-word; /* 긴 텍스트를 줄바꿈 */
    line-height: 1.2; /* 줄 간격 */
}


.scroll-button {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    background-color: rgba(0, 0, 0, 0.5);
    color: white;
    border: none;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    cursor: pointer;
    font-size: 18px;
    display: flex;
    justify-content: center;
    align-items: center;
}

.scroll-button.left {
    left: -20px;
}

.scroll-button.right {
    right: -20px;
}

.scroll-button:hover {
    background-color: rgba(0, 0, 0, 0.7);
}

.button {
    display: block;
    margin: 20px auto;
    padding: 10px 20px;
    background-color: #4CAF50;
    color: white;
    text-align: center;
    text-decoration: none;
    border-radius: 5px;
}

.button:hover {
    background-color: #45a049;
}

**library.js**
document.addEventListener('DOMContentLoaded', () => {
    const readingContainer = document.getElementById('readingBooksContainer');
    const lessonContainer = document.getElementById('learningBooksContainer');
    const scrollLeftReading = document.getElementById('scrollLeftReading');
    const scrollRightReading = document.getElementById('scrollRightReading');
    const scrollLeftLesson = document.getElementById('scrollLeftLearning');
    const scrollRightLesson = document.getElementById('scrollRightLearning');
    const contentSelect = document.getElementById('contentSelect');
    const levelSelect = document.getElementById('levelSelect');

    if (!readingContainer || !lessonContainer || !contentSelect || !levelSelect) {
        console.error('Required DOM elements are missing. Check your HTML IDs.');
        return;
    }

    // 콘텐츠별 레벨 설정
    const levelsByContent = {
        phonics: [1, 2],
        novel: [1, 2, 3, 4, 5, 6, 7],
        conversation: [1, 2, 3, 4, 5, 6, 7],
    };

    // 레벨 드롭다운 옵션 업데이트
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

    // 도서 데이터 로드 및 렌더링 함수
    async function loadBooks(container, apiUrl, message, clickCallback) {
        container.innerHTML = '';
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error(`Failed to load books from ${apiUrl}`);
            const books = await response.json();

            if (books.length === 0) {
                container.innerHTML = `<p>${message}</p>`;
                return;
            }

            const bookshelf = document.createElement('div');
            bookshelf.classList.add('bookshelf');

            books.forEach(book => {
                const bookElement = document.createElement('div');
                bookElement.classList.add('book');
            
                // 이미지 추가
                const image = document.createElement('img');
                image.src = `/static/${book.image_path}`; // STATIC_URL을 포함한 경로로 수정
                image.alt = book.title;
            
                // 제목 추가
                const title = document.createElement('p');
                title.textContent = book.title;
            
                // 구성 요소 추가
                bookElement.appendChild(image);
                bookElement.appendChild(title);
            
                bookElement.onclick = () => clickCallback(book);
                bookshelf.appendChild(bookElement);
            });

            container.appendChild(bookshelf);
        } catch (error) {
            console.error('Error in loadBooks:', error);
            container.innerHTML = `<p>${message}</p>`;
        }
    }

    // 읽고 있는 도서 로드
    function loadReading() {
        loadBooks(
            readingContainer,
            '/api/reading_books/',
            '아직 읽은 도서가 없습니다.',
            book => {
                window.location.href = `/lesson/${book.content_type}/${book.lesson_id}/`;
            }
        );
    }

    // 학습 도서 목록 로드
    function loadLessons(contentType, level) {
        loadBooks(
            lessonContainer,
            `/api/lessons/?content_type=${contentType}&level=${level}`,
            '해당 콘텐츠와 레벨에 학습 가능한 도서가 없습니다.',
            book => {
                window.location.href = `/lesson/${contentType}/${book.id}/`;
            }
        );
    }

    // 스크롤 이벤트 처리
    function setupScrollButtons(container, leftButton, rightButton) {
        if (!container || !leftButton || !rightButton) return;

        leftButton.addEventListener('click', () => {
            container.scrollLeft -= 300;
        });
        rightButton.addEventListener('click', () => {
            container.scrollLeft += 300;
        });
    }

    // 초기화
    const initialContentType = contentSelect.value;
    updateLevelOptions(initialContentType);
    loadLessons(initialContentType, levelSelect.value || 1);
    loadReading();

    // 이벤트 리스너 등록
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

    setupScrollButtons(readingContainer, scrollLeftReading, scrollRightReading);
    setupScrollButtons(lessonContainer, scrollLeftLesson, scrollRightLesson);
});

**veiws.py**
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from django.utils.timezone import now
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.db.models import F, Min
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .models import UserPronunciation, LessonNovel, LessonConversation, LessonPhonics, ReadingLog
from .serializers import UserPronunciationSerializer, UserSerializer
from .forms import SignUpForm, LoginForm
from botocore.exceptions import NoCredentialsError
import boto3
import json
from dotenv import load_dotenv
from django.http import JsonResponse
import os

load_dotenv()


User = get_user_model()

# REST API 기반 회원가입
@api_view(['POST'])
def register(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not email or not password:
        return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password)
    token = Token.objects.create(user=user)
    return Response({'message': 'User created successfully!', 'token': token.key}, status=status.HTTP_201_CREATED)

# REST API 기반 로그인
@api_view(['POST'])
def api_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({'message': 'Login successful!', 'token': token.key}, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)

# 마이페이지 뷰
@login_required
def mypage_view(request):
    return render(request, 'mypage.html', {'user': request.user})

# 서재 뷰
@login_required
def library_view(request):
    base_dir = os.path.join(settings.BASE_DIR, 'static/lesson_images')
    content_types = ['Phonics', 'Conversation', 'Novel']
    image_data = {}

    for content_type in content_types:
        content_dir = os.path.join(base_dir, content_type)
        if os.path.exists(content_dir):
            image_data[content_type] = {}
            for level_dir in sorted(os.listdir(content_dir)):
                level_path = os.path.join(content_dir, level_dir)
                if os.path.isdir(level_path):
                    images = []
                    for img in sorted(os.listdir(level_path)):
                        if img.endswith(('.png', '.jpg', '.jpeg')):
                            lesson = None
                            if content_type == 'Phonics':
                                lesson = LessonPhonics.objects.filter(title=os.path.splitext(img)[0]).first()
                            elif content_type == 'Novel':
                                lesson = LessonNovel.objects.filter(title=os.path.splitext(img)[0]).first()
                            elif content_type == 'Conversation':
                                lesson = LessonConversation.objects.filter(title=os.path.splitext(img)[0]).first()

                            if lesson:
                                images.append({
                                    "path": f"lesson_images/{content_type}/{level_dir}/{img}",
                                    "name": os.path.splitext(img)[0],
                                    "lesson_id": lesson.id
                                })
                    image_data[content_type][level_dir] = images

    return render(request, 'library.html', {
        'image_data': image_data,
        'user': request.user,
    })


# 학습 뷰
@login_required
def lesson_view(request, content_type, lesson_id):
    # 콘텐츠 타입에 따라 레슨 객체 가져오기
    lesson = None
    if content_type == "phonics":
        lesson = LessonPhonics.objects.filter(id=lesson_id).first()
    elif content_type == "novel":
        lesson = LessonNovel.objects.filter(id=lesson_id).first()
    elif content_type == "conversation":
        lesson = LessonConversation.objects.filter(id=lesson_id).first()

    if not lesson:
        return redirect("library")  # 콘텐츠가 없으면 서재로 리디렉션

    # 문장 리스트 분리
    all_sentences = lesson.sentence.split("\n")
    current_sentence_index = int(request.GET.get("sentence_index", 0))
    current_sentence = all_sentences[current_sentence_index]

    # 이전/다음 버튼 활성화 여부 설정
    is_prev_enabled = current_sentence_index > 0
    is_next_enabled = current_sentence_index < len(all_sentences) - 1

    # ReadingLog 업데이트
    ReadingLog.objects.update_or_create(
        user=request.user,
        lesson_id=lesson.id,
        content_type=content_type,
        defaults={
            "title": lesson.title,
            "level": lesson.level,
            "last_read_at": now(),
            "last_read_sentence_index": current_sentence_index,
        },
    )

    # 템플릿 렌더링
    return render(
        request,
        "lesson.html",
        {
            "lesson": lesson,
            "current_sentence": current_sentence,
            "current_sentence_index": current_sentence_index,
            "is_prev_enabled": is_prev_enabled,
            "is_next_enabled": is_next_enabled,
            "content_type": content_type,
        },
    )


# 읽고 있는 도서 (사용자 학습 로그 기반)
@login_required
def get_reading_books(request):
    """
    사용자가 읽은 도서 목록을 반환합니다.
    """
    user = request.user
    logs = ReadingLog.objects.filter(user=user).order_by('-last_read_at').values(
        annotated_lesson_id=F('lesson_id'),  # 어노테이션 이름 수정
        annotated_title=F('title'),         # 어노테이션 이름 수정
        level=F('level'),
        content_type=F('content_type'),
        last_read_at=F('last_read_at'),
        last_read_sentence_index=F('last_read_sentence_index')  # 마지막으로 읽은 문장 인덱스 추가
    )
    return JsonResponse(list(logs), safe=False)



# 학습 도서 목록
@login_required
def get_lessons(request):
    content_type = request.GET.get("content_type")
    level = int(request.GET.get("level", 1))

    if content_type == "phonics":
        lessons = LessonPhonics.objects.filter(level=level).values(
            "id", "title", "level"
        ).distinct("title")  # 중복 제거
    elif content_type == "novel":
        lessons = LessonNovel.objects.filter(level=level).values(
            "id", "title", "level"
        ).distinct("title")  # 중복 제거
    elif content_type == "conversation":
        lessons = LessonConversation.objects.filter(level=level).values(
            "id", "title", "level"
        ).distinct("title")  # 중복 제거
    else:
        return JsonResponse({"error": "Invalid content type"}, status=400)

    return JsonResponse(list(lessons), safe=False)



# 템플릿 기반 회원가입 뷰
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # 회원가입 후 자동 로그인
            messages.success(request, '회원가입이 성공적으로 완료되었습니다!')
            return redirect('mypage')  # 마이페이지로 리디렉션
    else:
        form = SignUpForm()

    return render(request, 'signup.html', {'form': form})

#템플릿 기반 로그인
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                next_url = request.GET.get('next', 'mypage')
                return redirect(next_url)
            else:
                messages.error(request, "아이디 또는 비밀번호가 잘못되었습니다.")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})




# 로그아웃 뷰
def logout_view(request):
    logout(request)
    messages.success(request, "로그아웃 되었습니다.")
    return redirect('login')

# 사용자 음성 경로 생성 함수
def generate_s3_path(user_id, content_type, level, title, line_number):
    """
    사용자 음성 파일의 S3 경로를 생성
    """
    audio_filename = f"audio_{line_number}.wav"
    return f"user-audio-file/{user_id}/{content_type}/level_{level}/{title}/{audio_filename}"


# 표준 음성 경로 생성 함수
def generate_s3_path_for_standard(content_type, level, title, line_number):
    """
    표준 음성 파일의 S3 경로를 생성
    """
    audio_filename = f"{title}_line_{line_number}.wav"
    return f"standard-audio-file/{content_type}/level_{level}/{title}/{audio_filename}"


# 문장 번호를 표준 음성 URL에서 추출하는 함수
def get_sentence_number_from_url(audio_file_url):
    """
    표준 음성 파일 URL에서 문장 번호를 추출합니다.
    예: 'https://standard-audio-file.s3.amazonaws.com/conversation/level_1/At the Toy Store/At the Toy Store_line_1.wav'
    """
    match = re.search(r'_line_(\d+)\.wav$', audio_file_url)
    if not match:
        raise ValueError("Invalid audio file URL format. Unable to extract line number.")
    return int(match.group(1))

# 아이디 중복 확인 API
def check_username(request):
    username = request.GET.get('username', None)
    if username and User.objects.filter(username=username).exists():
        return JsonResponse({'exists': True}, status=200)
    return JsonResponse({'exists': False}, status=200)

# 사용자 발음 업로드 및 S3 저장
class UserPronunciationView(APIView):
    def post(self, request):
        print("Content-Type:", request.content_type)  # 요청의 Content-Type 출력
        print("Request FILES:", request.FILES)  # 업로드된 파일 정보 출력
        
        audio_file = request.FILES.get('audio_file')
        if not audio_file:
            return Response({'error': 'No audio file received.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = request.data.get('user')
        lesson_id = request.data.get('lesson')
        if not user_id or not lesson_id:
            return Response({'error': 'Missing user or lesson ID.'}, status=status.HTTP_400_BAD_REQUEST)
        
        content_type = request.data.get('content_type')
        level = request.data.get('level')
        title = request.data.get('title')
        sentence = request.data.get('sentence')
        audio_file = request.FILES.get('audio_file')
        if not audio_file:
            return Response({'error': 'No audio file received.'}, status=status.HTTP_400_BAD_REQUEST)


        # 필수 데이터 확인
        if not all([user_id, lesson_id, content_type, level, title, sentence, audio_file]):
            return Response({'error': 'Missing required fields.'}, status=status.HTTP_400_BAD_REQUEST)

        # content_type 검증
        valid_content_types = ['phonics', 'novel', 'conversation']
        if content_type not in valid_content_types:
            return Response({'error': '유효하지 않은 content_type입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 표준 음성 S3 URL 생성
        standard_audio_url = generate_s3_path_for_standard(content_type, level, title, 1)
        try:
            # URL에서 문장 번호 추출
            line_number = get_sentence_number_from_url(standard_audio_url)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 사용자 음성 S3 경로 생성
        file_path = generate_s3_path(user_id, content_type, level, title, line_number)

        # S3에 업로드
        bucket_name = "user-audio-file"  # 사용자 음성 버킷 이름
        s3 = boto3.client('s3')
        try:
            s3.upload_fileobj(audio_file, bucket_name, file_path)
            audio_url = f"https://{bucket_name}.s3.amazonaws.com/{file_path}"
        except Exception as e:
            return Response({'error': f"Failed to upload file to S3: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # UserPronunciation 객체 생성/업데이트
        try:
            pronunciation, created = UserPronunciation.objects.update_or_create(
                user_id=user_id,
                content_type=ContentType.objects.get(model=content_type),
                object_id=lesson_id,
                defaults={
                    "audio_file": audio_url,
                    "status": "pending",  # 초기 상태 설정
                }
            )
        except Exception as e:
            return Response({'error': f"Failed to update UserPronunciation: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Lambda 함수 트리거
        lambda_client = boto3.client('lambda', region_name="ap-northeast-2")  # 서울 리전 예시
        standard_audio_key = generate_s3_path_for_standard(content_type, level, title, line_number)
        try:
            payload = {
                "user_audio_key": file_path,
                "standard_audio_key": standard_audio_key,
                "google_credentials_key": "credentials/epaproject-442104-c9dda29df7f5.json"
            }
            response = lambda_client.invoke(
                FunctionName="TimestampGeneration",  # Lambda 함수 이름
                InvocationType='Event',  # 비동기 호출
                Payload=json.dumps(payload)
            )
            if response['StatusCode'] != 202:
                return Response({'error': 'Failed to invoke Lambda function.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': f"Failed to trigger Lambda: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'message': 'Audio file uploaded and Lambda triggered successfully.',
            'audio_url': audio_url,
            'status': pronunciation.status,
        }, status=status.HTTP_200_OK)



# Lambda 함수 결과로 채점 데이터를 업데이트
class UpdatePronunciationScoreView(APIView):
    def post(self, request):
        # 람다 함수에서 전달된 데이터 수신
        data = request.data
        audio_url = data.get("audio_url")
        pitch_similarity = data.get("pitch_similarity")
        rhythm_similarity = data.get("rhythm_similarity")
        speed_ratio = data.get("speed_ratio")
        pause_similarity = data.get("pause_similarity")
        mispronounced_words = data.get("mispronounced_words", [])
        mispronounced_ratio = data.get("mispronounced_ratio")
        feedback = data.get("feedback", "")

        # 람다 함수 결과 데이터 검증
        if not audio_url or not isinstance(pitch_similarity, float):
            return Response({'error': '람다 함수 결과 데이터가 유효하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # UserPronunciation 레코드 업데이트
        pronunciation = UserPronunciation.objects.filter(audio_file=audio_url).first()
        if not pronunciation:
            return Response({"error": "Audio file not found in UserPronunciation table."}, status=status.HTTP_404_NOT_FOUND)

        pronunciation.pitch_similarity = pitch_similarity
        pronunciation.rhythm_similarity = rhythm_similarity
        pronunciation.speed_ratio = speed_ratio
        pronunciation.pause_similarity = pause_similarity
        pronunciation.mispronounced_words = mispronounced_words
        pronunciation.mispronounced_ratio = mispronounced_ratio
        pronunciation.feedback = feedback
        pronunciation.status = "completed"  # 처리 완료 상태 업데이트
        pronunciation.processed_at = now()  # 처리 시간 기록
        pronunciation.save()

        return Response({"message": "Pronunciation score updated successfully."}, status=status.HTTP_200_OK)


**assign_images.py**
import os
import django
import unicodedata

# Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'epa_project.settings')
django.setup()

from core.models import LessonPhonics, LessonConversation, LessonNovel

def normalize_title(title):
    """
    제목을 정규화하여 파일명과 데이터베이스의 일치를 보장
    """
    # 유니코드 정규화로 특수 문자 처리 (예: é -> e)
    title = unicodedata.normalize('NFKD', title).encode('ASCII', 'ignore').decode('utf-8')

    # 작은따옴표 및 변형된 문자들을 처리
    title = title.replace("'", "").replace("’", "").replace("‘", "").replace('"', "").strip()

    # 공백 및 기타 불필요한 변환 처리
    title = title.replace("  ", " ")  # 중복된 공백 제거
    title = title.replace(" s ", "s ")  # 's 앞뒤 공백 제거
    title = title.replace(" ", "_")  # 나머지 공백을 모두 언더스코어로 변환

    # 특정 문제 있는 문자 수동 처리
    #title = title.replace("é", "e")  # 'é'를 'e'로 변환
    title = title.replace("Café", "Cafe")  # 예외적인 경우를 수동 처리

    return title


def assign_images():
    base_path = 'static/lesson_images'

    # 콘텐츠와 모델 매핑
    content_map = {
        'Phonics': {'model': LessonPhonics, 'levels': range(1, 3)},  # 레벨 1~2
        'Conversation': {'model': LessonConversation, 'levels': range(1, 8)},  # 레벨 1~7
        'Novel': {'model': LessonNovel, 'levels': range(1, 8)},  # 레벨 1~7
    }

    no_match_titles = []  # 매칭되지 않은 항목 추적

    for content, data in content_map.items():
        model = data['model']
        levels = data['levels']

        for level in levels:
            path = os.path.join(base_path, f'{content}/level_{level}')
            if not os.path.exists(path):
                print(f"Directory not found: {path}")
                continue

            for file_name in os.listdir(path):
                if not file_name.lower().endswith('.png'):
                    print(f"Skipping non-image file: {file_name}")
                    continue

                # 파일명에서 확장자 제거하여 제목 추출 및 정규화
                title, _ = os.path.splitext(file_name)
                normalized_title = normalize_title(title)
                image_path = f'lesson_images/{content}/level_{level}/{file_name}'

                # 데이터베이스 제목도 정규화하여 매칭
                lessons = model.objects.filter(level=level)
                matched = False
                for lesson in lessons:
                    if normalize_title(lesson.title) == normalized_title:
                        lesson.image_path = image_path
                        lesson.save()
                        print(f"Updated {content} image for title '{lesson.title}', level {level}")
                        matched = True
                        break

                if not matched:
                    print(f"No match found for {content} title '{normalized_title}', level {level}")
                    no_match_titles.append((content, title, level))

    # 매칭되지 않은 항목 출력
    if no_match_titles:
        print("\nNo match found for the following titles:")
        for content, title, level in no_match_titles:
            print(f"Content: {content}, Title: '{title}', Level: {level}")

if __name__ == "__main__":
    assign_images()




