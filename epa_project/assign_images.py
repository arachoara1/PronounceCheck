import os
import django
import unicodedata
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'epa_project.settings')
django.setup()

from core.models import LessonPhonics, LessonConversation, LessonNovel

def normalize_title(title):
    """
    제목을 정규화하여 파일명과 데이터베이스의 일치를 보장
    """
    # 유니코드 정규화로 특수 문자 처리
    title = unicodedata.normalize('NFKD', title)
    
    # 's를 그대로 유지하고 다른 특수문자만 처리
    title = re.sub(r'[^a-zA-Z0-9\s\']', '', title)
    
    # 연속된 공백 처리
    title = re.sub(r'\s+', ' ', title).strip()
    
    title = title.replace("(", "").replace(")", "")
    title = title.replace(",", "")
    title = title.replace(" ", "")
    
    return title

def assign_images():
    base_path = 'lesson_images'

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
            path = os.path.join('static', base_path, f'{content}/level_{level}')
            if not os.path.exists(path):
                print(f"Directory not found: {path}")
                continue

            for file_name in os.listdir(path):
                if not file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    continue

                title, _ = os.path.splitext(file_name)
                normalized_title = normalize_title(title)
                image_path = f'{base_path}/{content}/level_{level}/{file_name}'

                lessons = model.objects.filter(level=level)
                matched = False
                for lesson in lessons:
                    normalized_lesson_title = normalize_title(lesson.title)
                    if normalized_lesson_title == normalized_title:
                        lesson.image_path = image_path
                        lesson.save()
                        print(f"Updated {content} image for title '{lesson.title}', level {level}")
                        matched = True
                        break

                if not matched:
                    no_match_titles.append((content, title, level))

    # 매칭되지 않은 이미지 목록을 마지막에 정리해서 출력
    if no_match_titles:
        print("\n=== 매칭되지 않은 이미지 목록 ===")
        no_match_titles.sort(key=lambda x: (x[0], x[2]))
        current_content = None
        for content, title, level in no_match_titles:
            if current_content != content:
                print(f"\n[{content}]")
                current_content = content
            print(f"- Level {level}: {title}")

if __name__ == "__main__":
    assign_images()