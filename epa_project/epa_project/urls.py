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
from core.views import UserPronunciationView
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("홈페이지에 오신 것을 환영합니다!")  # 간단한 메시지 출력

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/pronunciation/", UserPronunciationView.as_view(), name="user_pronunciation"),
    path("", home_view, name="home"),  # 루트 경로 추가
]

# 정적 파일 URL 패턴 추가
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

