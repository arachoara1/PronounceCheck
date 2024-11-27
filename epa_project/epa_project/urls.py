from django.views.generic import RedirectView
from django.contrib import admin
from django.urls import path
from core.views import (
    signup_view,
    login_view,
    logout_view,
    mypage_view,
    library_view,
    UserPronunciationView,
    ProcessAudioLambdaView,
    UpdatePronunciationScoreView,
    lesson_view,
    get_lessons,
    get_reading_books,
)
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("홈페이지에 오신 것을 환영합니다!")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home_view, name="home"),
    path("signup/", signup_view, name="signup"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("mypage/", mypage_view, name="mypage"),
    path("library/", library_view, name="library"),
    path("lesson/<str:content_type>/<int:lesson_id>/", lesson_view, name="lesson"),
    path("upload/audio/", UserPronunciationView.as_view(), name="upload_audio"),
    path('upload_user_pronunciation/', UserPronunciationView.as_view(), name='upload_user_pronunciation'),
    path("process_audio_lambda/", ProcessAudioLambdaView.as_view(), name="process_audio_lambda"),
    path('update_pronunciation_score/', UpdatePronunciationScoreView.as_view(), name='update_pronunciation_score'),
    path("api/lessons/", get_lessons, name="get_lessons"),
    path("api/reading_books/", get_reading_books, name="get_reading_books"),
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)