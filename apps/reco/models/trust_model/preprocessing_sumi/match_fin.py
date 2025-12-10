# =====================================================================
# _00_load_data.py
# - 입력: data/raw/match_data.csv
#         (이미 '경기', '인천' 제거까지 완료된 데이터)
# - 역할:
#   1) '공인중개사' 값 비어있는 행 → only_agent_empty.csv
#   2) 'estbsBeginDe' 값 비어있는 행 → only_begin_empty.csv
#   3) 두 컬럼 모두 값 있는 행만 match_data_clean.csv 로 저장
# =====================================================================

import os
import pandas as pd

# ---------------------------------------------------------------------
# 0. 경로 설정
# ---------------------------------------------------------------------
BASE_DIR = r"C:/dev/study/eunjeong/SKN18-FINAL-1TEAM"
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")

# ✅ 경기가/인천이 이미 제외된 파일 (입력)
PATH_MATCH_SRC   = os.path.join(DATA_DIR, "match_data.csv")

# ✅ 두 컬럼 모두 값 있는 정제본 (출력)
PATH_MATCH_CLEAN = os.path.join(DATA_DIR, "match_data_clean.csv")

# 나머지 분리해서 저장할 파일들
PATH_ONLY_AGENT  = os.path.join(DATA_DIR, "only_agent_empty.csv")
PATH_ONLY_BEGIN  = os.path.join(DATA_DIR, "only_begin_empty.csv")

print(f"입력 파일 경로: {PATH_MATCH_SRC}")
print("결과 저장 경로:")
print(f"  - only_agent_empty  : {PATH_ONLY_AGENT}")
print(f"  - only_begin_empty  : {PATH_ONLY_BEGIN}")
print(f"  - match_data_clean  : {PATH_MATCH_CLEAN}")

# ---------------------------------------------------------------------
# 1. 데이터 로드 (이미 '경기', '인천' 제거된 상태)
# ---------------------------------------------------------------------
df = pd.read_csv(PATH_MATCH_SRC, encoding="utf-8-sig")
print("\n[원본 match_data] shape :", df.shape)

print("\n컬럼 목록:")
print(df.columns.tolist())

# ---------------------------------------------------------------------
# 2. '공인중개사' / 'estbsBeginDe' 각각 비어있는 행 분리
#    - NaN, 공백, 빈 문자열("") → 모두 '없는 값'으로 간주
#    - 두 컬럼 모두 값 있는 행만 match_data_clean 으로 저장
# ---------------------------------------------------------------------
col_agent = "공인중개사"
col_begin = "estbsBeginDe"

if col_agent not in df.columns:
    raise KeyError(f"컬럼 '{col_agent}' 이(가) 데이터에 없습니다.")
if col_begin not in df.columns:
    raise KeyError(f"컬럼 '{col_begin}' 이(가) 데이터에 없습니다.")

# 공인중개사 값이 비어있는지
cond_agent_empty = (
    df[col_agent].isna()
    | (df[col_agent].astype(str).str.strip() == "")
)

# estbsBeginDe 값이 비어있는지
cond_begin_empty = (
    df[col_begin].isna()
    | (df[col_begin].astype(str).str.strip() == "")
)

# 각각 따로 분리
only_agent_empty = df[cond_agent_empty].copy()   # 공인중개사 없음
only_begin_empty = df[cond_begin_empty].copy()   # estbsBeginDe 없음

# 두 컬럼 모두 값이 있는 행만 최종 정제 데이터로 사용
cond_both_has_value = (~cond_agent_empty) & (~cond_begin_empty)
df_clean = df[cond_both_has_value].copy()

print("\nonly_agent_empty shape :", only_agent_empty.shape)
print("only_begin_empty shape :", only_begin_empty.shape)
print("match_data_clean(정제 후) shape :", df_clean.shape)

# ---------------------------------------------------------------------
# 3. 결과 저장
# ---------------------------------------------------------------------
only_agent_empty.to_csv(PATH_ONLY_AGENT, index=False, encoding="utf-8-sig")
only_begin_empty.to_csv(PATH_ONLY_BEGIN, index=False, encoding="utf-8-sig")

# ✅ match_data_clean.csv 로 최종 정제본 저장
df_clean.to_csv(PATH_MATCH_CLEAN, index=False, encoding="utf-8-sig")

print("\n✅ 저장 완료")
print(f" - only_agent_empty : {PATH_ONLY_AGENT}")
print(f" - only_begin_empty : {PATH_ONLY_BEGIN}")
print(f" - match_data_clean : {PATH_MATCH_CLEAN}")