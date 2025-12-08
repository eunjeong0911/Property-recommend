import pandas as pd
import os

# 1) 경로 설정
BASE_DIR = r"C:/dev/study/eunjeong/SKN18-FINAL-1TEAM"
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")

PATH_COUNT = os.path.join(DATA_DIR, "중개사_카운트.csv")      # 기준이 되는 쪽
PATH_INFO  = os.path.join(DATA_DIR, "부동산중개업자정보.csv")  # 추가 정보
OUTPUT_PATH = os.path.join(DATA_DIR, "match_01.csv")

print("중개사_카운트 :", PATH_COUNT)
print("부동산중개업자정보 :", PATH_INFO)
print("결과 저장 :", OUTPUT_PATH)

# 2) 데이터 로드
count_df = pd.read_csv(PATH_COUNT, encoding="utf-8-sig")
info_df  = pd.read_csv(PATH_INFO,  encoding="utf-8-sig")

print("count_df shape:", count_df.shape)
print("info_df shape :", info_df.shape)

# 3) 등록번호 정규화 (숫자만 남기기)
count_df["등록번호_norm"] = (
    count_df["등록번호"]
    .astype(str)
    .str.replace(r"\D", "", regex=True)
    .str.strip()
)

info_df["등록번호_norm"] = (
    info_df["등록번호"]
    .astype(str)
    .str.replace(r"\D", "", regex=True)
    .str.strip()
)

# 4) 부동산중개업자정보에서 등록번호_norm + 중개업자종별명 기준으로 인원 수 카운트
#    예: (등록번호_norm=1111020..., 중개업자종별명=공인중개사) -> 1명
#        (등록번호_norm=1111020..., 중개업자종별명=중개보조원) -> 2명
type_counts = (
    info_df
    .groupby(["등록번호_norm", "중개업자종별명"])
    .size()
    .reset_index(name="count")
)

# 5) wide 형태로 피벗: 중개업자종별명이 칼럼 이름이 되도록
#    예: 공인중개사, 중개보조원, 개업공인중개사, 법인 등등
type_pivot = (
    type_counts
    .pivot_table(
        index="등록번호_norm",
        columns="중개업자종별명",
        values="count",
        fill_value=0
    )
    .reset_index()
)

# 컬럼 이름이 멀티인덱스로 나오는 걸 방지하기 위한 정리
type_pivot.columns.name = None

print("\n🔎 중개업자종별명 피벗 결과 미리보기")
print(type_pivot.head())

# 6) 기준: 중개사_카운트 LEFT JOIN (중개업자종별명 피벗)
#    → 중개사_카운트의 행은 모두 유지, 거기에 '공인중개사', '중개보조원' 같은 칼럼이 추가됨
merged = count_df.merge(
    type_pivot,
    on="등록번호_norm",
    how="left"
)

print("\nmerged shape :", merged.shape)
print(merged.head())

# 7) 결과 저장
merged.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
print("\n✅ 매칭 + 중개업자종별명 카운트 완료 →", OUTPUT_PATH)