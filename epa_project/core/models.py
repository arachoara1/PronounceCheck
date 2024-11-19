from django.db import models

class User(models.Model):
    username = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # 비밀번호 암호화에 유의
    created_at = models.DateTimeField(auto_now_add=True)

class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

class Lesson(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class UserPronunciation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    audio_file = models.CharField(max_length=512)  # S3 경로 저장
    score = models.FloatField()  # 발음 평가 점수
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class FeedbackLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

