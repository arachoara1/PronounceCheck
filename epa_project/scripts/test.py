import os

# 현재 스크립트가 실행되는 디렉토리를 기준으로 상대 경로 설정
base_dir = os.path.dirname(os.path.abspath(__file__))  # 현재 스크립트의 디렉토리
print(f"Base directory: {base_dir}")  # 현재 스크립트 경로 출력

data_dir = os.path.join(base_dir, '..', '..', 'Data', 'text')  # 상대 경로로 Data/text 폴더 위치 찾기
print(f"Data directory: {data_dir}")  # Data/text 경로 출력

json_files = [
    os.path.join(data_dir, 'translated_conversation.json'),
    os.path.join(data_dir, 'translated_novel.json'),
    os.path.join(data_dir, 'translated_phonics.json')
]

# JSON 파일 경로 출력
for json_file in json_files:
    print(f"Checking file: {json_file}")
    if os.path.exists(json_file):
        print(f"File found: {json_file}")
    else:
        print(f"File not found: {json_file}")




