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
from django.contrib.auth.decorators import login_required
from core.models import UserPronunciation, LessonNovel, LessonConversation, LessonPhonics, ReadingLog
from core.forms import SignUpForm, LoginForm
from core.audio_analysis import analyze_audio # audio_analysis.py의 채점 함수 호출
from pydub import AudioSegment
import tempfile
import boto3
import json
import re
import os
from dotenv import load_dotenv
from django.views.decorators.csrf import csrf_exempt

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
    character_range = range(1, 6)  # 캐릭터 선택 범위 전달
    return render(request, 'mypage.html', {'character_range': character_range})

# 서재 뷰
@login_required
def library_view(request):
    return render(request, 'library.html', {'user': request.user})


# 학습 뷰
@login_required
def lesson_view(request, content_type, lesson_id):
    lesson = None
    if content_type == "phonics":
        lesson = LessonPhonics.objects.filter(id=lesson_id).first()
    elif content_type == "novel":
        lesson = LessonNovel.objects.filter(id=lesson_id).first()
    elif content_type == "conversation":
        lesson = LessonConversation.objects.filter(id=lesson_id).first()
    
    if not lesson:
        return redirect("library")

    all_sentences = lesson.sentence.split("\n")
    all_sentences_kor = lesson.sentence_kor.split("\n") if lesson.sentence_kor else []

    last_read_log = ReadingLog.objects.filter(
        user=request.user,
        lesson_id=lesson_id,
        content_type=content_type,
    ).first()
    current_sentence_index = last_read_log.last_read_sentence_index if last_read_log else 0

    try:
        current_sentence = all_sentences[current_sentence_index]
        current_sentence_kor = (
            all_sentences_kor[current_sentence_index]
            if current_sentence_index < len(all_sentences_kor)
            else ""
        )
    except IndexError:
        current_sentence_index = 0
        current_sentence = all_sentences[current_sentence_index]
        current_sentence_kor = (
            all_sentences_kor[current_sentence_index]
            if current_sentence_index < len(all_sentences_kor)
            else ""
        )

    is_prev_enabled = current_sentence_index > 0
    is_next_enabled = current_sentence_index < len(all_sentences) - 1

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

    return render(
        request,
        "lesson.html",
        {
            "lesson": lesson,
            "current_sentence": current_sentence,
            "current_sentence_kor": current_sentence_kor,
            "current_sentence_index": current_sentence_index,
            "is_prev_enabled": is_prev_enabled,
            "is_next_enabled": is_next_enabled,
            "content_type": content_type,
            "standard_audio_url": lesson.audio_file,
            "sentences": all_sentences,
            "lesson_title_kor": lesson.title_kor
        },
    )



# 읽고 있는 도서 (사용자 학습 로그 기반)
@login_required
def get_reading_books(request):
    user = request.user
    logs = ReadingLog.objects.filter(user=user).order_by('-last_read_at')
    reading_books = []

    for log in logs:
        lesson = None
        if log.content_type == 'phonics':
            lesson = LessonPhonics.objects.filter(id=log.lesson_id).first()
        elif log.content_type == 'conversation':
            lesson = LessonConversation.objects.filter(id=log.lesson_id).first()
        elif log.content_type == 'novel':
            lesson = LessonNovel.objects.filter(id=log.lesson_id).first()
        
        if lesson:
            # URL에서 sentence_index 추출
            match = re.search(r'_(\d+)\.wav$', lesson.audio_file)
            sentence_index = int(match.group(1)) if match else 0

            book_data = {
                'lesson_id': log.lesson_id,
                'content_type': log.content_type,
                'title': log.title,
                'level': log.level,
                'image_path': lesson.image_path if lesson.image_path else None,
                'sentence_index': sentence_index,  # 추가
            }
            reading_books.append(book_data)

    return JsonResponse(reading_books, safe=False)


# 캐릭터 업데이트 뷰
@csrf_exempt
def update_character(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        character_id = data.get('character_id')
        if character_id:
            request.session['character_id'] = character_id
            image_url = f"/static/images/character{character_id}.png"
            return JsonResponse({'success': True, 'image_url': image_url})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# 캐릭터 업데이트 뷰
@csrf_exempt
def update_character(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        character_id = data.get('character_id')
        if character_id:
            request.session['character_id'] = character_id
            image_url = f"/static/images/character{character_id}.png"
            return JsonResponse({'success': True, 'image_url': image_url})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


# 학습 도서 목록
@login_required
def get_lessons(request):
    content_type = request.GET.get('content_type')
    level = int(request.GET.get('level', 1))
    lessons_data = []
    
    if content_type == 'novel':
        titles = LessonNovel.objects.filter(level=level).values_list('title', flat=True).distinct()
        for title in titles:
            lesson = LessonNovel.objects.filter(level=level, title=title).first()
            lessons_data.append({
                'id': lesson.id,
                'title': lesson.title,
                'level': lesson.level,
                'image_path': lesson.image_path,
                'content_type': content_type
            })
            
    elif content_type == 'phonics':
        titles = LessonPhonics.objects.filter(level=level).values_list('title', flat=True).distinct()
        for title in titles:
            lesson = LessonPhonics.objects.filter(level=level, title=title).first()
            lessons_data.append({
                'id': lesson.id,
                'title': lesson.title,
                'level': lesson.level,
                'image_path': lesson.image_path,
                'content_type': content_type
            })
            
    elif content_type == 'conversation':
        titles = LessonConversation.objects.filter(level=level).values_list('title', flat=True).distinct()
        for title in titles:
            lesson = LessonConversation.objects.filter(level=level, title=title).first()
            lessons_data.append({
                'id': lesson.id,
                'title': lesson.title,
                'level': lesson.level,
                'image_path': lesson.image_path,
                'content_type': content_type
            })

    return JsonResponse(lessons_data, safe=False)

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



# 아이디 중복 확인 API
def check_username(request):
    username = request.GET.get('username', None)
    if username and User.objects.filter(username=username).exists():
        return JsonResponse({'exists': True}, status=200)
    return JsonResponse({'exists': False}, status=200)

# 로그아웃 뷰
def logout_view(request):
    logout(request)
    messages.success(request, "로그아웃 되었습니다.")
    return redirect('login')


# 사용자 녹음 파일 처리 및 채점 뷰
# 사용자 녹음 파일 임시 저장 -> 채점 & S3 저장 -> 채점 결과 및 S3 URL 데이터베이스 저장
class UserPronunciationView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    # def get(self, request):
    #     return Response({"message": "이 뷰는 GET 요청을 지원하지 않습니다. POST 요청을 사용하세요."}, status=405)

    def post(self, request):
        try:
            # 요청을 보낸 사용자
            user = request.user
            print(f"요청 유저: {user}")

            # 요청 데이터 추출
            audio_file = request.FILES.get('audio_file')
            content_type = request.data.get('content_type')
            level = request.data.get('level')
            title = request.data.get('title')
            print(f"요청 데이터: audio_file={audio_file}, content_type={content_type}, level={level}, title={title}")

            # 필수 필드 확인
            required_fields = {
                "audio_file": audio_file,
                "content_type": content_type,
                "level": level,
                "title": title,
            }
            missing_fields = [key for key, value in required_fields.items() if not value]
            if missing_fields:
                return Response(
                    {"error": f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}"},
                    status=400,
                )

            # 레슨 정보 가져오기
            lesson = None
            if content_type == "phonics":
                lesson = LessonPhonics.objects.filter(title=title, level=level).first()
            elif content_type == "novel":
                lesson = LessonNovel.objects.filter(title=title, level=level).first()
            elif content_type == "conversation":
                lesson = LessonConversation.objects.filter(title=title, level=level).first()

            if not lesson or not lesson.audio_file:
                return Response({"error": "해당 레슨 또는 표준 오디오 파일이 존재하지 않습니다."}, status=404)
            
            print(f"레슨 정보: {content_type} - Level {lesson.level} - {lesson.title}: {lesson.sentence}")

            # 표준 오디오 URL 및 키 추출
            standard_audio_url = lesson.audio_file
            print(f"표준 오디오 URL: {standard_audio_url}")  # 디버깅: URL 확인
            match = re.search(r'_(\d+)\.wav$', standard_audio_url)
            if match:
                sentence_index = int(match.group(1))
                print(f"추출된 sentence_index: {sentence_index}")  # 디버깅: 추출된 값 확인
            else:
                print("정규식 매칭 실패")  # 디버깅: 매칭 실패 메시지
                return Response(
                    {"error": "표준 오디오 URL에서 sentence_index를 추출할 수 없습니다."},
                    status=400,
                )
            standard_audio_key = standard_audio_url.split("/")[-1]
            print(f"표준 오디오 URL: {standard_audio_url}")
            print(f"S3에서 요청된 키: {standard_audio_key}")

            # 사용자 오디오 파일 임시 저장
            user_audio_path = tempfile.NamedTemporaryFile(delete=False).name
            with open(user_audio_path, 'wb') as temp_file:
                for chunk in audio_file.chunks():
                    temp_file.write(chunk)
            print(f"임시 사용자 오디오 경로: {user_audio_path}")

            # 사용자 오디오 파일을 WAV 형식으로 변환
            user_wav_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            audio = AudioSegment.from_file(user_audio_path)
            audio.export(user_wav_path, format="wav")
            print(f"변환된 사용자 오디오 경로: {user_wav_path}")

            # 표준 오디오 파일 다운로드
            standard_audio_path = tempfile.NamedTemporaryFile(delete=False).name
            try:
                s3.download_file(S3_STANDARD_BUCKET, standard_audio_key, standard_audio_path)
                print(f"표준 오디오 파일 다운로드 성공: {standard_audio_path}")
            except Exception as e:
                print(f"표준 오디오 파일 다운로드 실패: {e}")
                return Response({"error": f"표준 오디오 파일 다운로드 실패: {e}"}, status=404)

            # 오디오 분석 시작
            try:
                results = analyze_audio(user_wav_path, standard_audio_path)
                print(f"오디오 분석 결과: {results}")
            except Exception as e:
                print(f"오디오 분석 중 오류 발생: {e}")
                return Response({"error": f"오디오 분석 중 오류 발생: {e}"}, status=500)

            # 사용자 오디오 파일 S3에 업로드
            user_audio_key = f"{user.id}/{content_type}/level_{level}/{title}/user_audio_sentence_{sentence_index}.wav"
            try:
                s3.upload_file(user_wav_path, S3_USER_BUCKET, user_audio_key)
                uploaded_url = f"https://{S3_USER_BUCKET}.s3.amazonaws.com/{user_audio_key}"
                print(f"사용자 오디오 파일 업로드 성공: {uploaded_url}")
            except Exception as e:
                print(f"사용자 오디오 파일 업로드 실패: {e}")
                return Response({"error": f"사용자 오디오 파일 업로드 실패: {e}"}, status=500)

            # 데이터베이스에 발음 채점 결과 저장
            try:
                UserPronunciation.objects.update_or_create(
                    user=user,
                    content_type=content_type,
                    defaults={
                        "audio_file": uploaded_url,
                        "pitch_similarity": results.get("Pitch Pattern", 0),
                        "rhythm_similarity": results.get("Rhythm Pattern", 0),
                        "speed_ratio": results.get("Speed Ratio", 0),
                        "pause_similarity": results.get("Pause Pattern", 0),
                        "mispronounced_words": results.get("Mispronounced Words", {}).get("list", []),
                        "mispronounced_ratio": results.get("Mispronounced Words", {}).get("ratio", 0),
                        "status": "completed",
                        "processed_at": now(),
                    },
                )
                print("데이터베이스 저장 성공")
            except Exception as e:
                print(f"데이터베이스 저장 실패: {e}")
                return Response({"error": f"데이터베이스 저장 실패: {e}"}, status=500)

            # 임시 파일 삭제
            os.remove(user_audio_path)
            os.remove(user_wav_path)
            os.remove(standard_audio_path)
            print("임시 파일 삭제 완료")

            return Response({"message": "파일 업로드 및 채점 성공", "url": uploaded_url}, status=200)

        except Exception as e:
            print(f"예기치 못한 오류: {e}")
            return Response({"error": str(e)}, status=500)
