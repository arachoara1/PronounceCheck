from rest_framework.parsers import MultiPartParser, FormParser
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
from django.contrib.contenttypes.models import ContentType
from mimetypes import guess_type
import mimetypes
from pathlib import Path
import subprocess
import tempfile
import boto3
import json
import re
import os
from dotenv import load_dotenv
import pdb


# .env 파일 로드
load_dotenv()

# 환경 변수 읽기
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
S3_USER_BUCKET = os.getenv("S3_USER_BUCKET", "user-audio-file")
S3_STANDARD_BUCKET = os.getenv("S3_STANDARD_BUCKET", "standard-audio-file")

# S3 클라이언트 생성
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)
User = get_user_model()


# 회원가입 뷰
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


# 로그인 뷰
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
    # standard_audio_path를 세션에 저장
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
    standard_audio_path = lesson.audio_file
    print(standard_audio_path)
    request.session["standard_audio_path"] = lesson.audio_file
    # ** 템플릿 렌더링에 필요한 데이터 추가 **
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
            "standard_audio_url": lesson.audio_file,  # 표준 음성 파일 URL 추가
            "sentences": all_sentences,  # 전체 문장 리스트
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
        'lesson_id',             # 원래 필드 이름 그대로 반환
        'title',                 # 원래 필드 이름 그대로 반환
        'content_type',          # 원래 필드 이름 그대로 반환
        'last_read_at',          # 원래 필드 이름 그대로 반환
        last_read_sentence_index=F('last_read_sentence_index')  # 어노테이션 이름 변경
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
        print("Received POST data:", request.POST)  # 디버깅용
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            print(f"Trying to authenticate: username={username}, password={password}")
            user = authenticate(request, username=username, password=password)
            if user:
                if user.is_active:
                    print(f"Login successful for user: {username}")
                    login(request, user)
                    return redirect('mypage')
                else:
                    print(f"User {username} is inactive.")
                    messages.error(request, "계정이 비활성화 상태입니다.")
            else:
                print("Authentication failed. Invalid username or password.")
                messages.error(request, "아이디 또는 비밀번호가 잘못되었습니다.")
        else:
            print("Form is invalid:", form.errors)
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


# 로그아웃 뷰
def logout_view(request):
    logout(request)
    messages.success(request, "로그아웃 되었습니다.")
    return redirect('login')


# S3 경로 생성
def generate_s3_path(user_id, content_type, level, title, line_number):
    """
    사용자 음성 파일의 S3 경로를 생성
    """
    # line_number에 이미 "line_"이 포함되어 있으므로 추가하지 않음
    return f"{user_id}/{content_type}/level_{level}/{title}/{title}_{line_number}.wav"


# 표준 음성 경로 생성 함수
def generate_s3_path_for_standard(content_type, level, title, line_number):
    return f"{S3_STANDARD_BUCKET}/{content_type}/level_{level}/{title}/audio_line_{line_number}.wav"


# 문장 번호 추출
def get_sentence_number_from_url(audio_file_url):
    """
    표준 음성 파일 URL에서 문장 번호를 추출
    """
    match = re.search(r"line_\d+", audio_file_url)
    if match:
        return match.group()  # "line_숫자" 형태 반환
    raise ValueError("URL에서 문장 번호를 찾을 수 없습니다.")


# 업로드된 파일 형식 검증
def validate_audio_file(file):
    # 파일 이름에서 MIME 타입 추정
    mime_type, _ = mimetypes.guess_type(file.name)
    # 지원되는 MIME 타입 목록
    valid_mime_types = ['audio/wav', 'audio/x-wav']
    # 지원되는 파일 확장자 목록
    valid_extensions = ['.wav']
    # 확장자 확인
    file_extension = Path(file.name).suffix.lower()
    # MIME 타입과 확장자 검증
    if mime_type not in valid_mime_types or file_extension not in valid_extensions:
        raise ValueError("지원되지 않는 파일 형식입니다. .wav 파일만 업로드 가능합니다.")
    

# S3 업로드 및 데이터 저장 뷰
class UserPronunciationView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request):
        try:
            audio_file = request.FILES.get('audio_file')
            user_id = request.data.get('user')
            content_type = request.data.get('content_type')
            level = request.data.get('level')
            title = request.data.get('title')
            sentence = request.data.get('sentence')
            standard_audio_path = request.session.get("standard_audio_path")
            # 검증
            user = User.objects.get(id=user_id)
            if content_type == "phonics":
                content_type_obj = ContentType.objects.get_for_model(LessonPhonics)
            elif content_type == "novel":
                content_type_obj = ContentType.objects.get_for_model(LessonNovel)
            elif content_type == "conversation":
                content_type_obj = ContentType.objects.get_for_model(LessonConversation)
            else:
                return Response({"error": "Invalid content_type"}, status=400)
            line_number = get_sentence_number_from_url(standard_audio_path)
            user_audio_path = generate_s3_path(user.id, content_type, level, title, line_number)
            validate_audio_file(audio_file)
            # S3 업로드
            s3.upload_fileobj(audio_file, S3_USER_BUCKET, user_audio_path)
            uploaded_url = f"https://{S3_USER_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{user_audio_path}"
            # 데이터 저장
            UserPronunciation.objects.update_or_create(
                user=user,
                object_id=user.id,
                content_type=content_type_obj,
                defaults={
                    "audio_file": uploaded_url,
                    "status": "pending",
                },
            )
            return Response({'message': '음성 파일이 S3에 성공적으로 업로드되었습니다.', 'url': uploaded_url}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Lambda가 호출할 엔드포인트 (채점 함수 호출)
class ProcessAudioLambdaView(APIView):
    """
    Lambda에서 호출하여 채점 함수 실행
    """
    def post(self, request):
        try:
            # Lambda로부터 전달된 데이터 가져오기
            user_audio_key = request.data.get("user_audio_key")
            standard_audio_key = request.data.get("standard_audio_key")

            if not user_audio_key or not standard_audio_key:
                return Response({'error': 'S3 오디오 키가 제공되지 않았습니다.'}, status=status.HTTP_400_BAD_REQUEST)

            # S3에서 파일 다운로드
            s3 = boto3.client('s3')
            user_audio_path = "/tmp/user_audio.wav"
            ref_audio_path = "/tmp/ref_audio.wav"

            s3.download_file("user-audio-file", user_audio_key, user_audio_path)
            s3.download_file("standard-audio-file", standard_audio_key, ref_audio_path)

            # 채점 함수 호출
            results = analyze_audio(user_audio_path, ref_audio_path)

            # 채점 결과 저장
            pitch_similarity = results["Pitch Pattern"]
            rhythm_similarity = results["Rhythm Pattern"]
            speed_ratio = results["Speed Ratio"]
            pause_similarity = results["Pause Pattern"]
            mispronounced_words = results["Mispronounced Words"]["list"]
            mispronounced_ratio = results["Mispronounced Words"]["ratio"]

            # UserPronunciation 데이터베이스 업데이트
            user_audio_url = f"https://user-audio-file.s3.amazonaws.com/{user_audio_key}"
            pronunciation = UserPronunciation.objects.filter(audio_file=user_audio_url).first()
            if not pronunciation:
                return Response({"error": "UserPronunciation 데이터가 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)

            pronunciation.pitch_similarity = pitch_similarity
            pronunciation.rhythm_similarity = rhythm_similarity
            pronunciation.speed_ratio = speed_ratio
            pronunciation.pause_similarity = pause_similarity
            pronunciation.mispronounced_words = mispronounced_words
            pronunciation.mispronounced_ratio = mispronounced_ratio
            pronunciation.status = "completed"
            pronunciation.processed_at = now()
            pronunciation.save()

            # 임시 파일 삭제
            os.remove(user_audio_path)
            os.remove(ref_audio_path)

            return Response({"message": "채점 완료 및 데이터베이스 업데이트 성공"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 발음 채점 결과 postgresql 업로드
class UpdatePronunciationScoreView(APIView):
    def post(self, request):
        user_audio_path = None
        ref_audio_path = None
        try:
            # 요청 데이터 확인
            user_id = request.data.get("user_id")  # 사용자 ID
            lesson_id = request.data.get("lesson_id")  # 레슨 ID
            content_type = request.data.get("content_type")  # 콘텐츠 타입 (phonics, novel, conversation)
            title = request.data.get("title")  # 레슨 제목
            level = request.data.get("level")  # 레벨
            standard_audio_url = request.data.get("standard_audio_url")  # 표준 음성 URL
            if not all([user_id, lesson_id, content_type, title, level, standard_audio_url]):
                return Response({'error': '필수 필드가 누락되었습니다.'}, status=status.HTTP_400_BAD_REQUEST)
            # 표준 음성에서 문장 번호 추출
            try:
                line_number = get_sentence_number_from_url(standard_audio_url)
            except ValueError as e:
                return Response({'error': f'표준 음성 URL에서 문장 번호를 추출할 수 없습니다: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
            # 사용자 음성 경로 생성
            user_audio_key = generate_s3_path(user_id, content_type, level, title, line_number)
            standard_audio_key = generate_s3_path_for_standard(content_type, level, title, line_number)
            # S3에서 사용자와 표준 음성 파일 다운로드
            user_audio_path = tempfile.NamedTemporaryFile(delete=False).name
            ref_audio_path = tempfile.NamedTemporaryFile(delete=False).name
            try:
                s3.download_file(S3_USER_BUCKET, user_audio_key, user_audio_path)
                s3.download_file(S3_STANDARD_BUCKET, standard_audio_key, ref_audio_path)
            except Exception as e:
                return Response({'error': f'S3 파일 다운로드 실패: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # 발음 채점 함수 호출
            try:
                results = analyze_audio(user_audio_path, ref_audio_path)
            except Exception as e:
                return Response({'error': f'채점 함수 실행 중 오류 발생: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # 채점 결과 검증
            required_keys = ["Pitch Pattern", "Rhythm Pattern", "Speed Ratio", "Pause Pattern", "Mispronounced Words"]
            if not isinstance(results, dict) or not all(key in results for key in required_keys):
                return Response({'error': '채점 결과 데이터가 올바르지 않습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # 채점 결과 파싱
            pitch_similarity = results["Pitch Pattern"]
            rhythm_similarity = results["Rhythm Pattern"]
            speed_ratio = results["Speed Ratio"]
            pause_similarity = results["Pause Pattern"]
            mispronounced_words = results["Mispronounced Words"]["list"]
            mispronounced_ratio = results["Mispronounced Words"]["ratio"]
            # S3 경로에서 URL 생성
            user_audio_url = f"https://{S3_USER_BUCKET}.s3.amazonaws.com/{user_audio_key}"
            # UserPronunciation 데이터베이스 업데이트
            pronunciation = UserPronunciation.objects.filter(audio_file=user_audio_url).first()
            if not pronunciation:
                return Response({"error": "UserPronunciation 데이터가 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)
            # 채점 결과 업데이트
            pronunciation.pitch_similarity = pitch_similarity
            pronunciation.rhythm_similarity = rhythm_similarity
            pronunciation.speed_ratio = speed_ratio
            pronunciation.pause_similarity = pause_similarity
            pronunciation.mispronounced_words = mispronounced_words
            pronunciation.mispronounced_ratio = mispronounced_ratio
            pronunciation.status = "completed"
            pronunciation.processed_at = now()
            pronunciation.save()
            return Response({"message": "점수 업데이트 성공"}, status=status.HTTP_200_OK)
        except NoCredentialsError as e:
            return Response({'error': f'AWS 자격 증명이 누락되었습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if user_audio_path and os.path.exists(user_audio_path):
                os.remove(user_audio_path)
            if ref_audio_path and os.path.exists(ref_audio_path):
                os.remove(ref_audio_path)