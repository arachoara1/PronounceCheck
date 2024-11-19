from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserPronunciation
from .serializers import UserPronunciationSerializer
from .storages import UserAudioStorage  # 사용자 음성 파일용 스토리지 클래스

class UserPronunciationView(APIView):
    def get(self, request):
        # 데이터베이스의 모든 발음 데이터를 JSON으로 반환
        pronunciations = UserPronunciation.objects.all()
        serializer = UserPronunciationSerializer(pronunciations, many=True)
        return Response(serializer.data)

    def post(self, request):
        # 요청 데이터에서 audio_file과 추가 정보를 받아옴
        if "audio_file" not in request.FILES:
            return Response(
                {"error": "No audio file provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        audio_file = request.FILES["audio_file"]
        user_id = request.data.get("user")  # 사용자 ID
        lesson_id = request.data.get("lesson")  # 레슨 ID

        # S3에 파일 업로드
        storage = UserAudioStorage()
        file_name = f"user_{user_id}/lesson_{lesson_id}/{audio_file.name}"  # S3 파일 경로
        file_url = storage.save(file_name, audio_file)  # S3에 저장 및 URL 생성

        # UserPronunciation 객체 생성
        pronunciation_data = {
            "user": user_id,
            "lesson": lesson_id,
            "audio_file": file_url,  # 생성된 S3 URL 저장
        }
        serializer = UserPronunciationSerializer(data=pronunciation_data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
