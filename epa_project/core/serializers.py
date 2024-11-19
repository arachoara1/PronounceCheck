from rest_framework import serializers
from .models import UserPronunciation
from .storages import UserAudioStorage

class UserPronunciationSerializer(serializers.ModelSerializer):
    audio_file = serializers.FileField(write_only=True, required=True)  # 파일 업로드를 처리하는 필드
    audio_file_url = serializers.SerializerMethodField(read_only=True)  # 반환 시 URL만 노출

    class Meta:
        model = UserPronunciation
        fields = ['id', 'user', 'lesson', 'audio_file', 'audio_file_url', 'score', 'feedback', 'created_at']

    def create(self, validated_data):
        """
        사용자 업로드 음성을 S3에 저장하고, S3 URL을 모델에 저장.
        """
        audio_file = validated_data.pop('audio_file')  # 업로드된 파일
        user = validated_data['user']
        lesson = validated_data['lesson']

        # S3 스토리지 설정 및 파일 저장
        storage = UserAudioStorage()
        file_name = f"user_{user.id}/lesson_{lesson.id}/{audio_file.name}"  # S3 경로
        file_url = storage.save(file_name, audio_file)  # S3에 저장 및 URL 생성

        # UserPronunciation 객체 생성
        pronunciation = UserPronunciation.objects.create(
            audio_file=file_url,  # S3 URL 저장
            **validated_data
        )
        return pronunciation

    def get_audio_file_url(self, obj):
        """
        읽기 전용으로 S3 URL 반환.
        """
        return obj.audio_file
