import os
import sys
import django
import boto3
from django.conf import settings

# 프로젝트 루트 경로를 Python 경로에 추가
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 스크립트 경로
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))  # 프로젝트 루트 경로
sys.path.append(PROJECT_ROOT)

# Django 환경 설정 로드
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "epa_project.settings")  # Django 설정 모듈 지정
django.setup()

from core.models import Lesson  # Django 환경 로드 후 모델 임포트

# S3 클라이언트 생성
s3 = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME,
)

# 업로드할 파일의 최상위 디렉토리 경로 설정
BASE_AUDIO_FOLDER = "../../Data"  # Data/novel 폴더 경로
BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME_STANDARD  # 표준 음성 파일용 버킷


# [디버깅] 파일 경로가 유효한지 출력
if not os.path.exists(BASE_AUDIO_FOLDER):
    print(f"Folder not found: {BASE_AUDIO_FOLDER}")
for root, dirs, files in os.walk(BASE_AUDIO_FOLDER):
    print(f"Scanning folder: {root}")
    for file_name in files:
        print(f"Found file: {file_name}")

# [디버깅] boto3 클라이언트가 S3 버킷에 접근할 수 있는지 확인
print(f"AWS_ACCESS_KEY_ID: {settings.AWS_ACCESS_KEY_ID}")
print(f"AWS_STORAGE_BUCKET_NAME_STANDARD: {BUCKET_NAME}")


def upload_standard_audio_to_s3():
    if not os.path.exists(BASE_AUDIO_FOLDER):
        print(f"Folder not found: {BASE_AUDIO_FOLDER}")
        return

    print(f"Processing folder: {BASE_AUDIO_FOLDER}")
    for root, dirs, files in os.walk(BASE_AUDIO_FOLDER):
        for file_name in files:
            if file_name.endswith(".wav"):
                try:
                    file_path = os.path.join(root, file_name)
                    relative_path = os.path.relpath(root, BASE_AUDIO_FOLDER)
                    s3_key = f"standard_audio/{relative_path}/{file_name}"
                    
                    # S3 업로드
                    print(f"Uploading {file_name} to S3 bucket: {BUCKET_NAME}")
                    s3.upload_file(file_path, BUCKET_NAME, s3_key)

                    file_url = f"https://{BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"

                    # 데이터베이스 저장
                    print(f"Saving to database: {file_name}")
                    Lesson.objects.create(
                        title=file_name.replace(".wav", ""),
                        description=f"{relative_path}",
                        audio_file=file_url,
                        script="표준 음성 스크립트 내용 입력"
                    )
                    print(f"Uploaded and saved: {file_name}")

                except Exception as e:
                    print(f"Error processing {file_name}: {e}")

