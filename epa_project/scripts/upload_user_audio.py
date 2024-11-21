import boto3
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from core.models import UserPronunciation

class AudioUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        user = request.user
        file_obj = request.FILES["audio_file"]
        s3 = boto3.client("s3")

        bucket_name = settings.AWS_STORAGE_BUCKET_NAME_USER
        s3_key = f"user-audio/{user.id}/{file_obj.name}"

        try:
            # S3에 파일 업로드
            s3.upload_fileobj(file_obj, bucket_name, s3_key)
            audio_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"

            # UserPronunciation 테이블에 사용자 음성 데이터 저장
            UserPronunciation.objects.create(
                user=user,
                audio_file=audio_url,
            )

            return JsonResponse({"message": "File uploaded successfully", "audio_url": audio_url}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
