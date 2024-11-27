from rest_framework import serializers
from .models import (
    UserPronunciation, 
    LessonNovel, 
    LessonConversation, 
    LessonPhonics,
    ReadingLog  # ReadingLog 모델 추가
)
from .storages import UserAudioStorage
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserPronunciationSerializer(serializers.ModelSerializer):
    audio_file = serializers.FileField(required=True)
    audio_file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserPronunciation
        fields = ['id', 'user', 'lesson', 'audio_file', 'audio_file_url', 'score', 'feedback', 'created_at']

    def create(self, validated_data):
        audio_file = validated_data.pop('audio_file')
        user = validated_data['user']
        lesson = validated_data['lesson']

        storage = UserAudioStorage()
        try:
            file_name = f"user_{user.id}/lesson_{lesson.id}/{audio_file.name}"
            file_url = storage.save(file_name, audio_file)
        except Exception as e:
            raise serializers.ValidationError({"audio_file": f"Failed to upload file: {str(e)}"})

        pronunciation = UserPronunciation.objects.create(audio_file=file_url, **validated_data)
        return pronunciation

    def get_audio_file_url(self, obj):
        return str(obj.audio_file)



class LessonPhonicsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonPhonics
        fields = ['id', 'title', 'level', 'image_path']

class LessonConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonConversation
        fields = ['id', 'title', 'level', 'image_path']

class LessonNovelSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonNovel
        fields = ['id', 'title', 'level', 'image_path']

class ReadingLogSerializer(serializers.ModelSerializer):
    image_path = serializers.SerializerMethodField()

    class Meta:
        model = ReadingLog
        fields = ['lesson_id', 'content_type', 'title', 'level', 'image_path']

    def get_image_path(self, obj):
        if obj.content_type == 'phonics':
            lesson = LessonPhonics.objects.filter(id=obj.lesson_id).first()
        elif obj.content_type == 'conversation':
            lesson = LessonConversation.objects.filter(id=obj.lesson_id).first()
        elif obj.content_type == 'novel':
            lesson = LessonNovel.objects.filter(id=obj.lesson_id).first()
        
        return lesson.image_path if lesson else None