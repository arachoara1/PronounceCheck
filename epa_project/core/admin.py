from django.contrib import admin
from .models import (
    UserLoginLog,
    UserSession,
    LessonNovel,
    LessonConversation,
    LessonPhonics,
    UserPronunciation,
    FeedbackLog,
    Recommendation,
    UserScore,
)

# 사용자 관련 모델
admin.site.register(UserLoginLog)
admin.site.register(UserSession)

# Lesson 관련 모델
admin.site.register(LessonNovel)
admin.site.register(LessonConversation)
admin.site.register(LessonPhonics)

# 기타 모델
admin.site.register(UserPronunciation)
admin.site.register(FeedbackLog)
admin.site.register(Recommendation)
admin.site.register(UserScore)
