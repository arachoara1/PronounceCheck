"""
URL configuration for epa_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from core.views import (
    signup_view,
    login_view,
    logout_view,
    mypage_view,
    library_view,
    UserPronunciationView,
    UpdateScoreView,
    lesson_view,
)
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

# 간단한 홈 페이지
def home_view(request):
    return HttpResponse("홈페이지에 오신 것을 환영합니다!")  # 홈 화면 메시지

urlpatterns = [
    path("admin/", admin.site.urls),                   # Django Admin
    path("", home_view, name="home"),                  # 홈 페이지
    path("signup/", signup_view, name="signup"),       # 회원가입 페이지
    path("login/", login_view, name="login"),          # 로그인 페이지
    path("logout/", logout_view, name="logout"),       # 로그아웃
    path("mypage/", mypage_view, name="mypage"),       # 마이페이지
    path("library/", library_view, name="library"),    # 서재 페이지
    path("lesson/<int:lesson_id>/", lesson_view, name="lesson"),  # 학습 화면
    path("upload/audio/", UserPronunciationView.as_view(), name="upload_audio"),
    path("update/score/", UpdateScoreView.as_view(), name="update_score"),
]

# 정적 파일 URL 추가 (개발 중에만 사용)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
