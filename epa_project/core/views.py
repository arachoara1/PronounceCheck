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
    return render(request, 'library.html', {'user': request.user})

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
        lesson_id=F('lesson_id'),
        title=F('title'),
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

# 템플릿 기반 로그인
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


# 사용자 발음 업로드 및 S3 저장
class UserPronunciationView(APIView):
    def post(self, request):
        user_id = request.data.get('user')
        lesson_id = request.data.get('lesson')
        content_type = request.data.get('content_type')
        level = request.data.get('level')
        title = request.data.get('title')
        sentence = request.data.get('sentence')
        audio_file = request.FILES.get('audio_file')

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
