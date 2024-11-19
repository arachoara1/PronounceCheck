from rest_framework import serializers
from .models import UserPronunciation

class UserPronunciationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPronunciation
        fields = '__all__'  # 모든 필드 포함