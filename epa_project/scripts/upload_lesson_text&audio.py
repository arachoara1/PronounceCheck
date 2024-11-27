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
AUDIO_FOLDER_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../Data/audio/phonics'))
JSON_FILE_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../Data/text/translated_phonics_with_kor.json'))


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

def file_exists_in_s3(bucket_name, s3_key):
    """S3에 파일이 존재하는지 확인"""
    try:
        s3.head_object(Bucket=bucket_name, Key=s3_key)
        return True
    except boto3.exceptions.botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise

def upload_to_s3(file_path, s3_key):
    """S3에 파일 업로드 (이미 존재하면 URL 반환)"""
    if file_exists_in_s3(BUCKET_NAME, s3_key):
        print(f"File already exists in S3: {s3_key}")
        return f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_key}"

    try:
        s3.upload_file(file_path, BUCKET_NAME, s3_key)
        url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
        return url
    except Exception as e:
        print(f"Error uploading {file_path} to S3: {e}")
        return None

def populate_lessons():
    """Lesson 테이블 채우기"""
    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        print(f"JSON file path: {JSON_FILE_PATH}")

        for category in data['categories']:
            category_name = category['category_name']
            LessonModel = get_lesson_model(category_name)

            for level_data in category['levels']:
                level = level_data['level']

                # 스크립트 데이터를 한 쌍으로 묶음
                scripts = level_data['scripts']
                paired_scripts = []
                for i in range(0, len(scripts), 2):
                    script = scripts[i]
                    script_kor = scripts[i + 1] if i + 1 < len(scripts) else {}
                    paired_scripts.append({
                        "title": script.get('title'),
                        "title_kor": script_kor.get('title_kor'),
                        "contents": script.get('contents', []),
                        "contents_kor": script_kor.get('contents_kor', [])
                    })

                # 스크립트 데이터 처리
                for script in paired_scripts:
                    title = script.get('title')
                    title_kor = script.get('title_kor', None)
                    sentences = script.get('contents', [])
                    sentences_kor = script.get('contents_kor', [])

                    if not title:
                        print(f"Skipping script with missing title: {script}")
                        continue

                    # 오디오 파일 폴더 경로
                    audio_folder = os.path.join(AUDIO_FOLDER_PATH, f"level_{level}", title)

                    for i, sentence in enumerate(sentences, start=1):
                        sentence_kor = sentences_kor[i - 1] if i - 1 < len(sentences_kor) else None
                        audio_filename = f"{title}_line_{i}.wav"
                        audio_file_path = os.path.join(audio_folder, audio_filename)

                        if os.path.exists(audio_file_path):
                            s3_key = f"{category_name}/level_{level}/{title}/{audio_filename}"
                            audio_url = upload_to_s3(audio_file_path, s3_key)

                            if audio_url:
                                # 중복 확인
                                if LessonModel.objects.filter(
                                    level=level,
                                    title=title,
                                    sentence=sentence
                                ).exists():
                                    print(f"Duplicate entry skipped: Level {level}, Title {title}, Sentence {sentence}")
                                    continue

                                # 데이터 저장
                                lesson = LessonModel(
                                    level=level,
                                    title=title,
                                    title_kor=title_kor,
                                    sentence=sentence,
                                    sentence_kor=sentence_kor,
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
