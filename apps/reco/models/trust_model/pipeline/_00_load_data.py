# =====================================================================
# match_3rd.py (또는 match_fin.py)
# - 입력 데이터: 이미 "경기" 제거까지 끝난 CSV (df_no_gyeonggi 저장본)
# - 역할:
#   1) '공인중개사' 값이 없는 행 분리 → only_agent_empty.csv
#   2) 'estbsBeginDe' 값이 없는 행 분리 → only_begin_empty.csv
#   3) 두 컬럼 모두 값이 있는 행만 정리 → match_data_clean.csv
# =====================================================================

import os
import pandas as pd

# ---------------------------------------------------------------------
# 0. 경로 설정
# ---------------------------------------------------------------------
BASE_DIR = r"C:/dev/study/eunjeong/SKN18-FINAL-1TEAM"
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")

# ✅ 여기서 src 파일은 "이미 경기 제거까지 된 데이터"라고 가정
#    (이름은 상황에 맞게 변경해도 OK)
PATH_SRC          = os.path.join(DATA_DIR, "match_data_clean.csv")
PATH_ONLY_AGENT   = os.path.join(DATA_DIR, "only_agent_empty.csv")
PATH_ONLY_BEGIN   = os.path.join(DATA_DIR, "only_begin_empty.csv")
PATH_MATCH_FIN  = os.path.join(DATA_DIR, "match_data_fin.csv")

print("입력 파일 경로:", PATH_SRC)
print("결과 저장 경로:")
print("  - only_agent_empty :", PATH_ONLY_AGENT)
print("  - only_begin_empty :", PATH_ONLY_BEGIN)
print("  - match_data_clean :", PATH_MATCH_CLEAN)

# ---------------------------------------------------------------------
# 1. 데이터 로드 (이미 경기 제거된 버전이라고 가정)
# ---------------------------------------------------------------------
df_no_gyeonggi = pd.read_csv(PATH_SRC, encoding="utf-8-sig")
print("df_no_gyeonggi shape :", df_no_gyeonggi.shape)

# 컬럼 존재 여부 확인 (안 떴을 때 디버그용)
print("\n컬럼 목록:")
print(df_no_gyeonggi.columns.tolist())

# ---------------------------------------------------------------------
# 2. '공인중개사' / 'estbsBeginDe' 각각 비어있는 행 분리
#    - NaN, 공백, 빈 문자열("") → 모두 '값 없음'으로 간주
#    - 둘 다 값이 있는 행만 match_data_clean 으로 사용
# ---------------------------------------------------------------------
col_agent = "공인중개사"
col_begin = "estbsBeginDe"

if col_agent not in df_no_gyeonggi.columns:
    raise KeyError(f"컬럼 '{col_agent}' 이(가) 데이터에 없습니다.")
if col_begin not in df_no_gyeonggi.columns:
    raise KeyError(f"컬럼 '{col_begin}' 이(가) 데이터에 없습니다.")

# 공인중개사 값이 비어 있는지 여부
cond_agent_empty = (
    df_no_gyeonggi[col_agent].isna()
    | (df_no_gyeonggi[col_agent].astype(str).str.strip() == "")
)

# estbsBeginDe 값이 비어 있는지 여부
cond_begin_empty = (
    df_no_gyeonggi[col_begin].isna()
    | (df_no_gyeonggi[col_begin].astype(str).str.strip() == "")
)

# 각각 따로 분리
only_agent_empty = df_no_gyeonggi[cond_agent_empty].copy()   # 공인중개사 없음
only_begin_empty = df_no_gyeonggi[cond_begin_empty].copy()   # estbsBeginDe 없음

# 둘 다 값이 있는 행만 최종 정제 데이터로 사용
cond_both_has_value = (~cond_agent_empty) & (~cond_begin_empty)
match_data_clean    = df_no_gyeonggi[cond_both_has_value].copy()

print("\nonly_agent_empty shape :", only_agent_empty.shape)
print("only_begin_empty shape :", only_begin_empty.shape)
print("match_data_clean shape :", match_data_clean.shape)

# ---------------------------------------------------------------------
# 3. 결과 저장
# ---------------------------------------------------------------------
only_agent_empty.to_csv(PATH_ONLY_AGENT, index=False, encoding="utf-8-sig")
only_begin_empty.to_csv(PATH_ONLY_BEGIN, index=False, encoding="utf-8-sig")
match_data_clean.to_csv(PATH_MATCH_CLEAN, index=False, encoding="utf-8-sig")

print("\n✅ 저장 완료")
print(" - only_agent_empty :", PATH_ONLY_AGENT)
print(" - only_begin_empty :", PATH_ONLY_BEGIN)
print(" - match_data_fin :", PATH_MATCH_FIN)
