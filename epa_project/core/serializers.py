from rest_framework import serializers
from .models import UserPronunciation, LessonNovel, LessonConversation, LessonPhonics
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


# 새로운 Serializer 추가
class LessonPhonicsSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()

    class Meta:
        model = LessonPhonics
        fields = ['id', 'title', 'content_type', 'level', 'image_path']

    def get_content_type(self, obj):
        return 'phonics'


class LessonConversationSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()

    class Meta:
        model = LessonConversation
        fields = ['id', 'title', 'content_type', 'level', 'image_path']

    def get_content_type(self, obj):
        return 'conversation'


class LessonNovelSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()

    class Meta:
        model = LessonNovel
        fields = ['id', 'title', 'content_type', 'level', 'image_path']

    def get_content_type(self, obj):
        return 'novel'
