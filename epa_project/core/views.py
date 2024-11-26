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
from core.audio_analysis import analyze_audio  # 채점 함수 임포트
from .models import UserPronunciation, LessonNovel, LessonConversation, LessonPhonics, ReadingLog
from .serializers import UserPronunciationSerializer, UserSerializer
from .forms import SignUpForm, LoginForm
from botocore.exceptions import NoCredentialsError
import boto3
import json
import re
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
    return f"{user_id}/{content_type}/level_{level}/{title}/audio_line_{line_number}.wav"


# 표준 음성 경로 생성 함수
def generate_s3_path_for_standard(content_type, level, title, line_number):
    """
    표준 음성 파일의 S3 경로를 생성
    """
    return f"standard-audio-file/{content_type}/level_{level}/{title}/audio_line_{line_number}.wav"


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
        try:
            # 요청 데이터 검증
            audio_file = request.FILES.get('audio_file')
            user_id = request.data.get('user')
            lesson_id = request.data.get('lesson')
            content_type = request.data.get('content_type')
            level = request.data.get('level')
            title = request.data.get('title')
            sentence = request.data.get('sentence')

            if not all([audio_file, user_id, lesson_id, content_type, level, title, sentence]):
                return Response({'error': '필수 필드가 누락되었습니다.'}, status=status.HTTP_400_BAD_REQUEST)

            if content_type not in ['phonics', 'novel', 'conversation']:
                return Response({'error': '유효하지 않은 content_type입니다.'}, status=status.HTTP_400_BAD_REQUEST)

            # 사용자 및 표준 음성 S3 경로 생성
            line_number = 1  # 첫 번째 문장 번호
            user_audio_path = generate_s3_path(user_id, content_type, level, title, line_number)
            standard_audio_path = generate_s3_path_for_standard(content_type, level, title, line_number)

            # S3 업로드
            s3 = boto3.client('s3')
            s3.upload_fileobj(audio_file, "user-audio-file", user_audio_path)

            # Lambda 트리거 호출
            lambda_client = boto3.client('lambda', region_name="ap-northeast-2")
            payload = {
                "user_audio_key": user_audio_path,
                "standard_audio_key": standard_audio_path,
                "user_id": user_id,
            }
            response = lambda_client.invoke(
                FunctionName="TimestampGeneration",
                InvocationType="Event",
                Payload=json.dumps(payload),
            )
            if response['StatusCode'] != 202:
                return Response({'error': 'Lambda 호출 실패'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # UserPronunciation 데이터베이스 업데이트
            UserPronunciation.objects.update_or_create(
                user_id=user_id,
                object_id=lesson_id,
                defaults={
                    "audio_file": f"https://user-audio-file.s3.amazonaws.com/{user_audio_path}",
                    "status": "pending",
                }
            )

            return Response({'message': '업로드 및 Lambda 트리거 성공'}, status=status.HTTP_200_OK)

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
        try:
            # 요청 데이터 확인
            user_audio_key = request.data.get("user_audio_key")
            standard_audio_key = request.data.get("standard_audio_key")

            if not user_audio_key or not standard_audio_key:
                return Response({'error': 'S3 오디오 키가 제공되지 않았습니다.'}, status=status.HTTP_400_BAD_REQUEST)

            # S3에서 사용자와 표준 음성 파일 다운로드
            s3 = boto3.client('s3')
            user_audio_path = "/tmp/user_audio.wav"
            ref_audio_path = "/tmp/ref_audio.wav"

            s3.download_file("user-audio-file", user_audio_key, user_audio_path)
            s3.download_file("standard-audio-file", standard_audio_key, ref_audio_path)

            # 발음 채점 함수 호출
            from .audio_analysis import analyze_audio  # 발음 채점 함수 임포트
            results = analyze_audio(user_audio_path, ref_audio_path)

            # 채점 결과 파싱
            pitch_similarity = results["Pitch Pattern"]
            rhythm_similarity = results["Rhythm Pattern"]
            speed_ratio = results["Speed"]
            pause_similarity = results["Pause Pattern"]
            mispronounced_words = results["Mispronounced Words"]["list"]
            mispronounced_ratio = results["Mispronounced Words"]["ratio"]

            # S3 경로에서 URL 생성
            user_audio_url = f"https://user-audio-file.s3.amazonaws.com/{user_audio_key}"

            # UserPronunciation 데이터베이스 업데이트
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

            return Response({"message": "점수 업데이트 성공"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
