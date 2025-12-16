"""
JSON 데이터 구조 탐색 스크립트
"""
import json
from pathlib import Path

# JSON 파일 로드
json_path = Path("C:/dev/SKN18-FINAL-1TEAM/data/RDB/land/00_통합_아파트.json")
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

output_lines = []
output_lines.append(f"데이터 타입: {type(data)}")
output_lines.append(f"데이터 개수: {len(data)}")
output_lines.append("\n첫 번째 항목의 키 목록:")

if isinstance(data, list) and len(data) > 0:
    keys = list(data[0].keys())
    for i, key in enumerate(keys, 1):
        output_lines.append(f"{i:2d}. {key}")
    
    output_lines.append("\n\n첫 번째 항목 샘플 데이터:")
    sample = data[0]
    for key in keys:  # 모든 키 출력
        value = sample.get(key)
        if isinstance(value, (str, int, float)):
            output_lines.append(f"{key}: {value}")
        elif isinstance(value, dict):
            output_lines.append(f"{key}: dict (keys: {list(value.keys())})")
        elif isinstance(value, list):
            output_lines.append(f"{key}: list (length: {len(value)})")
        else:
            output_lines.append(f"{key}: {type(value)}")

# 파일에 저장
output_file = Path("json_structure.txt")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print(f"출력 파일 저장 완료: {output_file.absolute()}")
