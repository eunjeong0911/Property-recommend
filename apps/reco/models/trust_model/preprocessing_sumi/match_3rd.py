import pandas as pd
import os

BASE_DIR = r"C:/dev/study/eunjeong/SKN18-FINAL-1TEAM"
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")

PATH_SRC   = os.path.join(DATA_DIR, "match_02.csv")
PATH_ONLY  = os.path.join(DATA_DIR, "only_peterpanz.csv")
PATH_MATCH = os.path.join(DATA_DIR, "match_data.csv")

# 1) 데이터 로드
df = pd.read_csv(PATH_SRC, encoding="utf-8-sig")
print("원본 shape :", df.shape)

# ─────────────────────────────────────
# 1. '주소'에 '경기' 또는 '인천' 이 포함된 행 삭제
# ─────────────────────────────────────
addr_str = df["주소"].astype(str)

mask_gyeonggi = addr_str.str.contains("경기", na=False)
mask_incheon  = addr_str.str.contains("인천", na=False)

mask_exclude = mask_gyeonggi | mask_incheon   # 둘 중 하나라도 True면 제거 대상

df_no_region = df[~mask_exclude].copy()
print("'경기' 또는 '인천' 제거 후 shape :", df_no_region.shape)

# ─────────────────────────────────────
# 2. '공인중개사' 와 'estbsBeginDe' 둘 다 값이 없는 행 분리
#    - NaN 이거나 공백/빈문자열("")도 '없는 값'으로 간주
# ─────────────────────────────────────
col_agent = "공인중개사"
col_begin = "estbsBeginDe"

cond_agent_empty = df_no_region[col_agent].isna() | (df_no_region[col_agent].astype(str).str.strip() == "")
cond_begin_empty = df_no_region[col_begin].isna() | (df_no_region[col_begin].astype(str).str.strip() == "")

cond_both_empty = cond_agent_empty & cond_begin_empty

only_peterpanz = df_no_region[cond_both_empty].copy()
match_data     = df_no_region[~cond_both_empty].copy()

print("only_peterpanz shape :", only_peterpanz.shape)
print("match_data shape     :", match_data.shape)

# ─────────────────────────────────────
# 3. 각 결과를 CSV로 저장
# ─────────────────────────────────────
only_peterpanz.to_csv(PATH_ONLY, index=False, encoding="utf-8-sig")
match_data.to_csv(PATH_MATCH, index=False, encoding="utf-8-sig")

print("✅ 저장 완료")
print(" - only_peterpanz :", PATH_ONLY)
print(" - match_data     :", PATH_MATCH)