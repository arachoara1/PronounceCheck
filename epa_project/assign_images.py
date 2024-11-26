import os
import django
import unicodedata

# Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'epa_project.settings')
django.setup()

from core.models import LessonPhonics, LessonConversation, LessonNovel

def normalize_title(title):
    """
    제목을 정규화하여 파일명과 데이터베이스의 일치를 보장
    """
    # 유니코드 정규화로 특수 문자 처리
    title = unicodedata.normalize('NFKD', title).encode('ASCII', 'ignore').decode('utf-8')
    
    # 작은따옴표 및 변형된 문자들을 처리
    title = title.replace("'", "").replace("'", "").replace("'", "").replace('"', "").strip()
    
    # 공백 및 기타 불필요한 변환 처리
    title = title.replace("  ", " ")
    title = title.replace(" s ", "s ")
    title = title.replace(" ", "_")
    
    return title

def assign_images():
    base_path = 'lesson_images'  # static/ 제거

    content_map = {
        'Phonics': {'model': LessonPhonics, 'levels': range(1, 3)},
        'Conversation': {'model': LessonConversation, 'levels': range(1, 8)},
        'Novel': {'model': LessonNovel, 'levels': range(1, 8)},
    }

    no_match_titles = []

    for content, data in content_map.items():
        model = data['model']
        levels = data['levels']

        for level in levels:
            path = os.path.join('static', base_path, f'{content}/level_{level}')  # static 경로 수정
            if not os.path.exists(path):
                print(f"Directory not found: {path}")
                continue

            for file_name in os.listdir(path):
                if not file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    print(f"Skipping non-image file: {file_name}")
                    continue

                title, _ = os.path.splitext(file_name)
                normalized_title = normalize_title(title)
                # 이미지 경로에서 static/ 제외
                image_path = f'{base_path}/{content}/level_{level}/{file_name}'

                lessons = model.objects.filter(level=level)
                matched = False
                for lesson in lessons:
                    if normalize_title(lesson.title) == normalized_title:
                        lesson.image_path = image_path
                        lesson.save()
                        print(f"Updated {content} image for title '{lesson.title}', level {level}")
                        matched = True
                        break

                if not matched:
                    print(f"No match found for {content} title '{normalized_title}', level {level}")
                    no_match_titles.append((content, title, level))

    if no_match_titles:
        print("\nNo match found for the following titles:")
        for content, title, level in no_match_titles:
            print(f"Content: {content}, Title: '{title}', Level: {level}")

if __name__ == "__main__":
    assign_images()