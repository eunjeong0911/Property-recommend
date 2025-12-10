import os
import pandas as pd

# =========================================
# 0. 경로 설정
# =========================================
BASE_DIR = r"C:/dev/study/eunjeong/SKN18-FINAL-1TEAM"
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")

# ✅ 인풋 + 기준 데이터: 이미 경기/인천 제거 + 공인중개사/설립일 필터 끝난 버전
PATH_MATCH_CLEAN = os.path.join(DATA_DIR, "match_data_clean.csv")

# ✅ 대표자 ≠ brkrNm 행만 따로 저장할 파일
PATH_MISMATCH = os.path.join(DATA_DIR, "mismatch_representative.csv")

print(f"입력/기준 파일 경로 : {PATH_MATCH_CLEAN}")
print(f"대표자-중개사명 불일치 저장 : {PATH_MISMATCH}")

# =========================================
# 1. 데이터 로드
# =========================================
df = pd.read_csv(PATH_MATCH_CLEAN, encoding="utf-8-sig")
print("원본 shape :", df.shape)

# 필수 컬럼 체크
for col in ["대표자", "brkrNm"]:
    if col not in df.columns:
        raise KeyError(f"데이터에 '{col}' 컬럼이 없습니다.")

# =========================================
# 2. 대표자 vs brkrNm 비교
#    - 앞뒤 공백 + 모든 공백 제거 후 비교
# =========================================
def clean_name(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
         .str.strip()
         .str.replace(r"\s+", "", regex=True)  # 모든 공백 제거
    )

rep_clean  = clean_name(df["대표자"])
brkr_clean = clean_name(df["brkrNm"])

rep_notna  = df["대표자"].notna()
brkr_notna = df["brkrNm"].notna()

mask_diff = rep_notna & brkr_notna & (rep_clean != brkr_clean)

df_diff = df[mask_diff].copy()
print("대표자 ≠ brkrNm 행 수 :", len(df_diff))

# =========================================
# 3. 결과 저장
# =========================================

# (1) 대표자 ≠ brkrNm 행만 따로 저장
df_diff.to_csv(PATH_MISMATCH, index=False, encoding="utf-8-sig")

# (2) 원본 match_data_clean.csv 는 그대로 둬도 되고,
#     혹시 모를 추후 일관성을 위해 다시 한 번 그대로 덮어쓰기 (실질 내용 변화 없음)
df.to_csv(PATH_MATCH_CLEAN, index=False, encoding="utf-8-sig")

print("\n✅ 처리 완료!")
print(f"- 기준 데이터          → {PATH_MATCH_CLEAN}")
print(f"- 대표자/중개사명 불일치 → {PATH_MISMATCH}")