import pandas as pd
import os
import re

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

# 3) 정규화 함수들 -----------------------------------------------------

def normalize_number(x):
    """숫자만 남기기 (등록번호용)"""
    if pd.isna(x):
        return None
    return re.sub(r"[^0-9]", "", str(x))

def normalize_text(x):
    """공백 제거 (이름/상호용)"""
    if pd.isna(x):
        return None
    return re.sub(r"\s+", "", str(x))

# 4) 중개사_카운트 정규화 ---------------------------------------------

# 등록번호 정규화
count_df["등록번호_norm"] = count_df["등록번호"].map(normalize_number)

# 이름 정규화: 중개사명, 대표자
count_df["중개사명_norm"] = count_df["중개사명"].map(normalize_text)
count_df["대표자_norm"]   = count_df["대표자"].map(normalize_text)

# 5) 부동산중개업자정보 정규화 ----------------------------------------

info_df["등록번호_norm"]   = info_df["등록번호"].map(normalize_number)
info_df["사업자상호_norm"] = info_df["사업자상호"].map(normalize_text)
info_df["중개업자명_norm"] = info_df["중개업자명"].map(normalize_text)

# 이 세 개가 다 있는 행만 사용 (매칭 대상)
info_norm = info_df.dropna(
    subset=["등록번호_norm", "사업자상호_norm", "중개업자명_norm"]
).copy()

# 6) (등록번호_norm + 사업자상호_norm + 중개업자명_norm) 단위로
#    중개업자종별명, 직위구분명 카운트 ---------------------------------

key_cols = ["등록번호_norm", "사업자상호_norm", "중개업자명_norm"]

# 6-1) 중개업자종별명 카운트
type_counts = (
    info_norm
    .groupby(key_cols + ["중개업자종별명"])
    .size()
    .reset_index(name="count")
)

type_pivot = (
    type_counts
    .pivot_table(
        index=key_cols,
        columns="중개업자종별명",
        values="count",
        fill_value=0,
    )
    .reset_index()
)
type_pivot.columns.name = None  # 멀티인덱스 제거

print("\n🔎 중개업자종별명 피벗 결과 미리보기")
print(type_pivot.head())

# 6-2) 직위구분명 카운트
pos_counts = (
    info_norm
    .groupby(key_cols + ["직위구분명"])
    .size()
    .reset_index(name="count")
)

pos_pivot = (
    pos_counts
    .pivot_table(
        index=key_cols,
        columns="직위구분명",
        values="count",
        fill_value=0,
    )
    .reset_index()
)
pos_pivot.columns.name = None

print("\n🔎 직위구분명 피벗 결과 미리보기")
print(pos_pivot.head())

# 6-3) 대표(매치된 중개업자)의 중개업자종별명 한 칼럼으로 뽑기
#      - 동일 key에 여러 타입이 있으면 '최빈값(mode)' 사용
def pick_main_type(s: pd.Series) -> str:
    m = s.mode()
    if len(m) > 0:
        return m.iloc[0]
    return s.iloc[0]

main_type = (
    info_norm
    .groupby(key_cols)["중개업자종별명"]
    .agg(pick_main_type)
    .reset_index()
    .rename(columns={"중개업자종별명": "대표_중개업자종별명"})
)

print("\n🔎 대표_중개업자종별명 미리보기")
print(main_type.head())

# 6-4) 세 정보를 합쳐 agg_info 생성
agg_info = (
    type_pivot
    .merge(pos_pivot, on=key_cols, how="outer")
    .merge(main_type, on=key_cols, how="outer")
)

print("\n🔎 agg_info 미리보기")
print(agg_info.head())

# 7) 중개사_카운트 쪽 키 (등록번호_norm + 중개사명_norm + 대표자_norm)와
#    부동산중개업자정보 쪽 키 (등록번호_norm + 사업자상호_norm + 중개업자명_norm)를
#    모두 만족하는 경우만 LEFT JOIN -----------------------------------

merged = count_df.merge(
    agg_info,
    left_on=["등록번호_norm", "중개사명_norm", "대표자_norm"],
    right_on=["등록번호_norm", "사업자상호_norm", "중개업자명_norm"],
    how="left",   # ⭐ 중개사_카운트 기준, 행 누락 없음
)

print("\nmerged shape :", merged.shape)
print(merged.head())

# 8) (선택) 정규화/조인용 컬럼 정리 -----------------------------------
# drop_cols = [
#     "등록번호_norm",
#     "중개사명_norm",
#     "대표자_norm",
#     "사업자상호_norm",
#     "중개업자명_norm",
# ]
# merged = merged.drop(columns=[c for c in drop_cols if c in merged.columns])

# 9) 결과 저장 ---------------------------------------------------------

merged.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
print("\n✅ 매칭 + 중개업자종별명/직위구분명 카운트 + 대표_중개업자종별명 완료 →", OUTPUT_PATH)
