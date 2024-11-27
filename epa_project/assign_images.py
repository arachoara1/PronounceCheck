import os
import django
import unicodedata
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'epa_project.settings')
django.setup()

from core.models import LessonPhonics, LessonConversation, LessonNovel

def normalize_title(title):
    # 특수문자 및 아포스트로피 처리
    title = unicodedata.normalize('NFKD', title).encode('ASCII', 'ignore').decode('utf-8')
    title = re.sub(r'\([^)]*\)', '', title)  # 괄호와 괄호 안의 내용 제거
    title = title.replace("'s", "s")         # 소유격 처리
    title = title.replace("'", "")           # 다른 아포스트로피 처리
    title = title.replace(",", "")           # 쉼표 제거
    title = title.replace("'", "")           # 작은따옴표 제거
    title = title.replace('"', "")           # 큰따옴표 제거
    title = title.replace("é", "e")          # 프랑스어 악센트 처리
    title = title.replace("è", "e")
    title = title.replace("ê", "e")
    title = title.replace("-", " ")          # 하이픈을 공백으로
    title = ' '.join(title.split())          # 연속된 공백을 하나로

    return title.strip()

def assign_images():
    base_path = 'lesson_images'  # 'on_images'가 아닌 'lesson_images'로 수정

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

                # 같은 제목을 가진 모든 레슨에 이미지 할당
                lessons = model.objects.filter(level=level, title=title)
                matched = False
                
                for lesson in lessons:
                    lesson.image_path = image_path
                    lesson.save()
                    print(f"Updated {content} image for title '{lesson.title}', level {level}")
                    matched = True

                if not matched:
                    no_match_titles.append((content, title, level))

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