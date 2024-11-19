from django.contrib import admin
from .models import User, UserSession, Lesson, UserPronunciation, FeedbackLog, Recommendation

# 모델 등록
admin.site.register(User)
admin.site.register(UserSession)
admin.site.register(Lesson)
admin.site.register(UserPronunciation)
admin.site.register(FeedbackLog)
admin.site.register(Recommendation)
