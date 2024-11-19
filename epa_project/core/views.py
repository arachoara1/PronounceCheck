from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserPronunciation
from .serializers import UserPronunciationSerializer

class UserPronunciationView(APIView):
    def get(self, request):
        # 데이터베이스의 모든 발음 데이터를 JSON으로 반환
        pronunciations = UserPronunciation.objects.all()
        serializer = UserPronunciationSerializer(pronunciations, many=True)
        return Response(serializer.data)

    def post(self, request):
        # 요청 데이터를 바탕으로 새로운 발음 데이터를 생성
        serializer = UserPronunciationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
