from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .models import UserPronunciation, LessonNovel, LessonConversation, LessonPhonics
from .serializers import UserPronunciationSerializer, UserSerializer
from .forms import SignUpForm, LoginForm
from .storages import UserAudioStorage
from botocore.exceptions import NoCredentialsError
import boto3


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

# 로그아웃 뷰
def logout_view(request):
    logout(request)
    messages.success(request, "로그아웃 되었습니다.")
    return redirect('login')  # 로그아웃 후 로그인 페이지로 이동

# 마이페이지 뷰
@login_required
def mypage_view(request):
    return render(request, 'mypage.html', {'user': request.user})

# 서재 뷰
@login_required
def library_view(request):
    # 서재 페이지에 표시할 데이터
    books = [{"id": i, "title": f"책 {i}"} for i in range(1, 5)]  # 예제 데이터
    return render(request, 'library.html', {'user': request.user, 'books': books})

@login_required
def lesson_view(request, lesson_id):
    # Lesson 정보를 가져오기
    lesson = (
        LessonNovel.objects.filter(id=lesson_id).first()
        or LessonConversation.objects.filter(id=lesson_id).first()
        or LessonPhonics.objects.filter(id=lesson_id).first()
    )

    if not lesson:
        return redirect("library")  # 잘못된 ID로 접근 시 서재로 리디렉션

    return render(request, "lesson.html", {"user": request.user, "lesson": lesson})


# 템플릿 기반 회원가입
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
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
                # 'next' 파라미터 확인
                next_url = request.GET.get('next', 'mypage')  # 기본값은 'mypage'
                return redirect(next_url)  # 해당 URL로 리디렉션
            else:
                messages.error(request, "아이디 또는 비밀번호가 잘못되었습니다.")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

# 템플릿 기반 로그아웃
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            id = form.cleaned_data['id']
            password = form.cleaned_data['password']
            user = authenticate(request, username=id, password=password)  # `username`에 `id` 전달
            if user:
                login(request, user)
                return redirect('mypage')  # 로그인 후 마이페이지로 리디렉션
            else:
                messages.error(request, "아이디 또는 비밀번호가 잘못되었습니다.")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

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

        # S3에 파일 업로드
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

        # UserPronunciation 테이블에 사용자 데이터 기록
        with transaction.atomic():
            pronunciation = UserPronunciation.objects.create(
                user=user,
                lesson=lesson,
                audio_file=audio_url,
            )

        # 람다 호출로 채점 실행
        lambda_client = boto3.client('lambda', region_name=settings.AWS_S3_REGION_NAME)
        try:
            response = lambda_client.invoke(
                FunctionName='YourLambdaFunctionName',
                InvocationType='Event',  # 비동기 실행
                Payload=json.dumps({
                    'audio_url': audio_url,
                    'lesson_id': lesson_id,
                    'user_id': user_id,
                }),
            )
        except Exception as e:
            return Response({'error': f"Failed to invoke Lambda function: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'message': 'Audio file uploaded successfully',
            'audio_url': audio_url,
            'lambda_status': response['StatusCode']
        }, status=status.HTTP_200_OK)

class UpdateScoreView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        audio_url = data.get("audio_url")
        score = data.get("score")
        feedback = data.get("feedback", "")

        # UserPronunciation 테이블 업데이트
        pronunciation = UserPronunciation.objects.filter(audio_file=audio_url).first()
        if pronunciation:
            pronunciation.score = score
            pronunciation.feedback = feedback
            pronunciation.save()
            return Response({"message": "Score and feedback updated successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Audio file not found"}, status=status.HTTP_404_NOT_FOUND)
