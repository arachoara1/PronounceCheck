from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserPronunciation, LessonNovel, LessonConversation, LessonPhonics
from .serializers import UserPronunciationSerializer, UserSerializer
from .forms import SignUpForm, LoginForm
from .storages import UserAudioStorage
from django.contrib.auth.decorators import login_required


User = get_user_model()


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
def logout_view(request):
    logout(request)
    return redirect('login')


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
    return render(request, 'library.html', {'user': request.user})


class UserPronunciationView(APIView):
    def get(self, request):
        pronunciations = UserPronunciation.objects.all()
        serializer = UserPronunciationSerializer(pronunciations, many=True)
        return Response(serializer.data)

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

        storage = UserAudioStorage()
        try:
            file_name = f"user_{user_id}/lesson_{lesson_id}/{audio_file.name}"
            file_url = storage.save(file_name, audio_file)
        except Exception as e:
            return Response({'error': f"Failed to upload file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        pronunciation_data = {"user": user_id, "lesson": lesson_id, "audio_file": file_url}
        serializer = UserPronunciationSerializer(data=pronunciation_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
