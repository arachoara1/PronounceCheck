# import os
# import sys
# import json
# import django

# # Django 프로젝트의 최상위 디렉터리를 Python 경로에 추가
# sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'epa_project'))

# # Django 설정 초기화
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "epa_project.settings")
# django.setup()

# # 모델 임포트
# from core.models import LessonConversation, LessonNovel, LessonPhonics

# # JSON 파일 경로 (여기에 json 파일 경로를 맞게 수정해주세요)
# json_files = [
#     '../../Data/text/translated_conversation.json',
#     '../../Data/text/translated_novel.json',
#     '../../Data/text/translated_phonics.json'
# ]

# # 데이터 추출 후 모델에 저장하기
# def process_json_file(json_file):
#     try:
#         with open(json_file, 'r', encoding='utf-8') as f:
#             data = json.load(f)
#             print(f"Processing file: {json_file}")

#             # 데이터베이스에 저장
#             for category in data['categories']:
#                 category_name = category['category_name']
#                 for level_data in category['levels']:
#                     level = level_data['level']
#                     for script in level_data['scripts']:
#                         title = script['title']
#                         title_kor = script.get('title_kor', '')  # 한글 제목
#                         contents = script['contents']
#                         contents_kor = script['contents_kor']

#                         # 문장 매칭 후 데이터베이스에 저장
#                         for eng, kor in zip(contents, contents_kor):
#                             # 레코드가 존재하는지 확인
#                             lesson = None
#                             if category_name == 'conversation':
#                                 lesson = LessonConversation.objects.filter(level=level, title=title, sentence=eng).first()
#                             elif category_name == 'novel':
#                                 lesson = LessonNovel.objects.filter(level=level, title=title, sentence=eng).first()
#                             elif category_name == 'phonics':
#                                 lesson = LessonPhonics.objects.filter(level=level, title=title, sentence=eng).first()

#                             if lesson:
#                                 # 기존 레코드 업데이트: 기존 데이터는 수정하지 않고, 새로운 컬럼들만 업데이트
#                                 lesson.title_kor = title_kor
#                                 lesson.sentence_kor = kor
#                                 lesson.save()
#                                 print(f"Updated lesson: {lesson}")
#                             else:
#                                 print(f"No lesson found for: {title} - {eng}, skipping update.")

#     except Exception as e:
#         print(f"Error occurred while processing {json_file}: {e}")

# # 메인 처리 함수
# def main():
#     # 모든 JSON 파일을 처리
#     for json_file in json_files:
#         process_json_file(json_file)

# # 실행
# if __name__ == "__main__":
#     try:
#         main()
#     except Exception as e:
#         print(f"Error during execution: {e}")


import os
import sys
import json
import django

# 현재 스크립트가 실행되는 디렉토리를 기준으로 상대 경로 설정
base_dir = os.path.dirname(os.path.abspath(__file__))  # 현재 스크립트의 디렉토리
data_dir = os.path.join(base_dir, '..', '..', 'Data', 'text')  # 상대 경로로 Data/text 폴더 위치 찾기

# JSON 파일 경로
json_files = [
    os.path.join(data_dir, 'translated_conversation.json'),
    os.path.join(data_dir, 'translated_novel.json'),
    os.path.join(data_dir, 'translated_phonics.json')
]

# Django 프로젝트의 최상위 디렉터리를 Python 경로에 추가
sys.path.append(os.path.join(base_dir, '..', '..', 'epa_project'))

# Django 설정 초기화
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "epa_project.settings")
django.setup()

# 모델 임포트
from core.models import LessonConversation, LessonNovel, LessonPhonics

# 데이터 추출 후 모델에 저장하기
def process_json_file(json_file):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"Processing file: {json_file}")

            # 데이터베이스에 저장
            for category in data['categories']:
                category_name = category['category_name']
                for level_data in category['levels']:
                    level = level_data['level']
                    for script in level_data['scripts']:
                        title = script['title']
                        title_kor = script.get('title_kor', '')  # 한글 제목
                        contents = script['contents']
                        contents_kor = script['contents_kor']

                        # 문장 매칭 후 데이터베이스에 저장
                        for eng, kor in zip(contents, contents_kor):
                            # 레코드가 존재하는지 확인
                            lesson = None
                            if category_name == 'conversation':
                                lesson = LessonConversation.objects.filter(level=level, title=title, sentence=eng).first()
                            elif category_name == 'novel':
                                lesson = LessonNovel.objects.filter(level=level, title=title, sentence=eng).first()
                            elif category_name == 'phonics':
                                lesson = LessonPhonics.objects.filter(level=level, title=title, sentence=eng).first()

                            if lesson:
                                # 기존 레코드 업데이트: 기존 데이터는 수정하지 않고, 새로운 컬럼들만 업데이트
                                lesson.title_kor = title_kor
                                lesson.sentence_kor = kor
                                lesson.save()
                                print(f"Updated lesson: {lesson}")
                            else:
                                print(f"No lesson found for: {title} - {eng}, skipping update.")

    except Exception as e:
        print(f"Error occurred while processing {json_file}: {e}")

# 메인 처리 함수
def main():
    # 모든 JSON 파일을 처리
    for json_file in json_files:
        process_json_file(json_file)

# 실행
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error during execution: {e}")
