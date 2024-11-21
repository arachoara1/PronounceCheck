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
from django.db.models import F
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .models import UserPronunciation, LessonNovel, LessonConversation, LessonPhonics, ReadingLog
from .serializers import UserPronunciationSerializer, UserSerializer
from .forms import SignUpForm, LoginForm
from botocore.exceptions import NoCredentialsError
import boto3
import json

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
def lesson_view(request, lesson_id):
    lesson = (
        LessonPhonics.objects.filter(id=lesson_id).first()
        or LessonNovel.objects.filter(id=lesson_id).first()
        or LessonConversation.objects.filter(id=lesson_id).first()
    )

    if not lesson:
        return redirect("library")  # 잘못된 ID로 접근 시 서재로 리디렉션

    # 콘텐츠 유형 결정
    content_type = (
        "phonics" if isinstance(lesson, LessonPhonics)
        else "novel" if isinstance(lesson, LessonNovel)
        else "conversation"
    )

    # 문장 리스트 분리
    all_sentences = lesson.sentence.split("\n")
    current_sentence_index = int(request.GET.get("sentence_index", 0))  # URL 파라미터로 인덱스 가져옴

    # ReadingLog 업데이트
    ReadingLog.objects.update_or_create(
        user=request.user,
        lesson_id=lesson.id,
        content_type=content_type,
        defaults={
            "title": lesson.title,
            "level": lesson.level,
            "last_read_at": now(),
            "last_read_sentence_index": current_sentence_index,  # 인덱스 저장
        },
    )

    return render(
        request,
        "lesson.html",
        {
            "lesson": lesson,
            "sentences": all_sentences,
            "current_sentence_index": current_sentence_index,
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
        lessons = LessonPhonics.objects.filter(level=level).values("id", "title", "level")
    elif content_type == "novel":
        lessons = LessonNovel.objects.filter(level=level).values("id", "title", "level")
    elif content_type == "conversation":
        lessons = LessonConversation.objects.filter(level=level).values("id", "title", "level")
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

# UserPronunciation 로직 (로그 저장 및 S3 업로드)
class UserPronunciationView(APIView):
    def post(self, request):
        user_id = request.data.get('user')
        lesson_id = request.data.get('lesson')
        audio_file = request.FILES.get('audio_file')

        if not all([user_id, lesson_id, audio_file]):
            return Response({'error': 'Missing required fields: user, lesson, or audio_file.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Invalid user ID.'}, status=status.HTTP_404_NOT_FOUND)

        lesson = (
            LessonNovel.objects.filter(id=lesson_id).first()
            or LessonConversation.objects.filter(id=lesson_id).first()
            or LessonPhonics.objects.filter(id=lesson_id).first()
        )
        if not lesson:
            return Response({'error': 'Invalid lesson ID.'}, status=status.HTTP_404_NOT_FOUND)

        s3 = boto3.client('s3')
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME_USER
        file_name = f"user_{user_id}/lesson_{lesson_id}/{audio_file.name}"
        try:
            s3.upload_fileobj(audio_file, bucket_name, file_name)
            audio_url = f"https://{bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{file_name}"
        except NoCredentialsError:
            return Response({'error': 'S3 credentials not available.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': f"Failed to upload file to S3: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        with transaction.atomic():
            pronunciation = UserPronunciation.objects.create(
                user=user,
                lesson=lesson,
                audio_file=audio_url,
            )

        return Response({'message': 'Audio file uploaded successfully', 'audio_url': audio_url}, status=status.HTTP_200_OK)

class UpdateScoreView(APIView):
    def post(self, request):
        data = request.data
        audio_url = data.get("audio_url")
        score = data.get("score")
        feedback = data.get("feedback", "")

        pronunciation = UserPronunciation.objects.filter(audio_file=audio_url).first()
        if pronunciation:
            pronunciation.score = score
            pronunciation.feedback = feedback
            pronunciation.save()
            return Response({"message": "Score and feedback updated successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Audio file not found"}, status=status.HTTP_404_NOT_FOUND)
