from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.hashers import make_password, check_password


class User(models.Model):
    """사용자 모델"""
    username = models.CharField(max_length=50, unique=True)  # 사용자 이름
    email = models.EmailField(unique=True)  # 이메일 (고유값)
    password = models.CharField(max_length=128)  # 비밀번호 (암호화 필요)
    is_active = models.BooleanField(default=True)  # 계정 활성화 여부
    is_staff = models.BooleanField(default=False)  # 관리자 여부
    date_joined = models.DateTimeField(auto_now_add=True)  # 가입 날짜

    # Django 인증 시스템에서 요구하는 속성 추가
    @property
    def is_anonymous(self):
        """익명 사용자 여부 (항상 False)"""
        return False

    @property
    def is_authenticated(self):
        """인증된 사용자 여부 (항상 True)"""
        return True

    # Django에서 요구하는 필드
    USERNAME_FIELD = 'username'  # 인증에 사용할 필드
    REQUIRED_FIELDS = ['email']  # createsuperuser 명령어에서 추가로 요구하는 필드

    def __str__(self):
        return self.username

    # 비밀번호 암호화 및 확인 메서드 추가
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

class UserLoginLog(models.Model):
    """사용자 로그인 로그"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 사용자 참조
    login_time = models.DateTimeField(auto_now_add=True)  # 로그인 시간
    ip_address = models.GenericIPAddressField(blank=True, null=True)  # IP 주소
    user_agent = models.CharField(max_length=255, blank=True, null=True)  # 브라우저 정보


class UserSession(models.Model):
    """사용자 세션"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 사용자 참조
    session_id = models.CharField(max_length=255)  # 세션 ID
    created_at = models.DateTimeField(auto_now_add=True)  # 세션 생성 시간
    ip_address = models.GenericIPAddressField(blank=True, null=True)  # IP 주소


class Lesson(models.Model):
    """레슨 정보"""
    title = models.CharField(max_length=255)  # 레슨 제목
    description = models.TextField()  # 레슨 설명
    audio_file = models.URLField()  # 표준 음성 S3 URL
    script = models.TextField()  # 화면에 표시할 스크립트
    created_at = models.DateTimeField(auto_now_add=True)  # 레슨 생성 시간


class UserPronunciation(models.Model):
    """사용자 발음 평가"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 사용자 참조
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)  # 레슨 참조
    audio_file = models.URLField()  # 업로드된 음성 파일 S3 URL
    score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        blank=True,
        null=True,
    )  # 발음 점수
    feedback = models.TextField(blank=True, null=True)  # 발음 피드백
    created_at = models.DateTimeField(auto_now_add=True)  # 업로드 시간


class FeedbackLog(models.Model):
    """사용자 피드백 기록"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 사용자 참조
    feedback_text = models.TextField()  # 피드백 내용
    created_at = models.DateTimeField(auto_now_add=True)  # 작성 시간


class Recommendation(models.Model):
    """추천 레슨"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 사용자 참조
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)  # 레슨 참조
    created_at = models.DateTimeField(auto_now_add=True)  # 추천 시간


class UserScore(models.Model):
    """사용자 점수 누적 관리"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # 사용자와 1:1 관계
    total_score = models.FloatField(default=0.0)  # 누적 점수
    last_updated = models.DateTimeField(auto_now=True)  # 마지막 업데이트 시간

    def update_score(self, new_score):
        """새 점수를 추가하고 누적 점수 업데이트"""
        self.total_score += new_score
        self.save()
