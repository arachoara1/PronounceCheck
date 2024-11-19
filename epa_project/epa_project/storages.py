from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

# 사용자 음성 파일용 버킷
class UserAudioStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME_USER  # .env에서 불러온 사용자 버킷 이름
    default_acl = 'private'


# 표준 음성 파일용 버킷
class StandardAudioStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME_STANDARD  # .env에서 불러온 표준 버킷 이름
    default_acl = 'private'
