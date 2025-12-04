# JSON 파일들을 읽어서 하나의 CSV로 통합하는 스크립트

import pandas as pd
import json
import os

# 프로젝트 루트 경로 설정 (현재 파일 기준 상대 경로)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
data_dir = os.path.join(project_root, "data", "landData")

# 1. 통합할 JSON 파일 리스트
json_files = [
    os.path.join(data_dir, "00_통합_빌라주택.json"),
    os.path.join(data_dir, "00_통합_오피스텔.json"),
    os.path.join(data_dir, "00_통합_원투룸.json"),
    os.path.join(data_dir, "00_통합_아파트.json")
]

# 2️. 각 JSON 파일 읽어서 DataFrame 리스트에 저장
df_list = []
for file in json_files:
    print(f"읽는 중: {file}")
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
    df_temp = pd.json_normalize(data)  # JSON 평탄화
    df_list.append(df_temp)
    print(f"  - {len(df_temp)}개 행 로드됨")

# 3️. DataFrame 통합
df = pd.concat(df_list, ignore_index=True)
print(f"\n총 {len(df)}개 행 통합 완료")

# 4️. 리스트형 컬럼 문자열로 변환 (CSV 호환)
list_cols = df.columns[df.applymap(lambda x: isinstance(x, list)).any()]
for col in list_cols:
    df[col] = df[col].apply(lambda x: "|".join(x) if isinstance(x, list) else x)

# 5️. CSV 저장
output_path = os.path.join(project_root, "data", "통합.csv")
df.to_csv(output_path, index=False, encoding="utf-8-sig")
print(f"\n✓ CSV 저장 완료: {output_path}")

# 6️. 확인
print(f"\n데이터 형태: {df.shape}")
print("\n처음 5개 행:")
print(df.head())
