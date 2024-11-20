import os
import sys
import json
import boto3
from dotenv import load_dotenv
from django.db import transaction

# Django 프로젝트의 최상위 디렉터리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'epa_project'))

# Django 설정 초기화
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "epa_project.settings")
import django
django.setup()

from core.models import LessonNovel, LessonConversation, LessonPhonics

# .env 파일 로드
load_dotenv()

# AWS 자격 증명과 S3 버킷 이름 로드
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME_STANDARD')

# S3 클라이언트 설정
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Data 경로 정규화
AUDIO_FOLDER_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../Data/audio/novel'))
JSON_FILE_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../Data/text/novel.json'))

def upload_to_s3(file_path, s3_key):
    """S3에 파일 업로드"""
    try:
        s3.upload_file(file_path, BUCKET_NAME, s3_key)
        url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
        return url
    except Exception as e:
        print(f"Error uploading {file_path} to S3: {e}")
        return None

def get_lesson_model(category_name):
    """카테고리 이름에 따라 Lesson 모델 선택"""
    if category_name == 'novel':
        return LessonNovel
    elif category_name == 'conversation':
        return LessonConversation
    elif category_name == 'phonics':
        return LessonPhonics
    else:
        raise ValueError(f"Unknown category_name: {category_name}")

def populate_lessons():
    """Lesson 테이블 채우기"""
    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    for category in data['categories']:
        category_name = category['category_name']
        LessonModel = get_lesson_model(category_name)

        for level_data in category['levels']:
            level = level_data['level']
            for script in level_data['scripts']:
                title = script['title']
                sentences = script['contents']

                # 해당 script의 오디오 파일 폴더 경로
                audio_folder = os.path.join(AUDIO_FOLDER_PATH, f"level_{level}", title)
                if not os.path.exists(audio_folder):
                    print(f"Audio folder not found: {audio_folder}")
                    continue

                # 오디오 파일과 sentence 매핑
                for i, sentence in enumerate(sentences, start=1):
                    audio_filename = f"{title}_line_{i}.wav"
                    audio_file_path = os.path.join(audio_folder, audio_filename)

                    if os.path.exists(audio_file_path):
                        s3_key = f"{category_name}/level_{level}/{title}/{audio_filename}"
                        audio_url = upload_to_s3(audio_file_path, s3_key)

                        if audio_url:
                            lesson = LessonModel(
                                level=level,
                                title=title,
                                sentence=sentence,
                                audio_file=audio_url
                            )
                            try:
                                lesson.save()
                                print(f"Saved: {lesson}")
                            except Exception as e:
                                print(f"Error saving lesson for {audio_filename}: {e}")
                    else:
                        print(f"Audio file not found: {audio_file_path}")

if __name__ == "__main__":
    try:
        with transaction.atomic():
            populate_lessons()
    except Exception as e:
        print(f"Error populating lessons: {e}")
