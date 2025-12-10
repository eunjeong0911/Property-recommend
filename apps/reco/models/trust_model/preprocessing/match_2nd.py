# =====================================================================
# match_2nd.py (ver.B - [상호 + 대표자] 복합키 매칭)
#
# - 기준: data/raw/match_01.csv
#   · 상호(중개사명): "중개사명"
#   · 대표자: "대표자"
#
# - 대상: data/raw/broker_office.csv
#   · 상호(사업자상호): "bsnmCmpnm"
#   · 대표자: "brkrNm"
#
# ✅ 매칭 기준:
#   1) 상호(이름) 정규화 후 공백 제거 → name_key
#   2) 대표자/브로커명 정규화 후 공백 제거 → rep_key
#   3) name_rep_key = name_key + "|" + rep_key
#   4) name_rep_key 가 같은 경우에만 매칭
#
# 📤 출력:
#   data/raw/match_data.csv
# =====================================================================

import re
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------
# 0. 경로 설정
# ---------------------------------------------------------------------
THIS_FILE = Path(__file__).resolve()
# 예시 경로: .../SKN18-FINAL-1TEAM/apps/reco/models/trust_model/preprocessing/match_2nd.py
# parents[0] = preprocessing
# parents[1] = trust_model
# parents[2] = models
# parents[3] = reco
# parents[4] = apps
# parents[5] = SKN18-FINAL-1TEAM (프로젝트 루트)
PROJECT_ROOT = THIS_FILE.parents[5]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

PATH_MATCH_01 = RAW_DIR / "match_01.csv"
PATH_BROKER   = RAW_DIR / "broker_office.csv"
PATH_OUTPUT   = RAW_DIR / "match_data.csv"   # 필요하면 match_02.csv 등으로 변경

print(f"[경로] match_01      : {PATH_MATCH_01}")
print(f"[경로] broker_office : {PATH_BROKER}")
print(f"[경로] 출력          : {PATH_OUTPUT}")


# ---------------------------------------------------------------------
# 1. 유틸 함수들
# ---------------------------------------------------------------------
def normalize_name(name: str) -> str | None:
    """
    상호/중개사무소 이름 정규화:
    - 양쪽 공백 제거
    - 이상한 공백을 일반 공백으로
    - 연속 공백 → 한 칸
    - 괄호 주변 공백 정리
    """
    if pd.isna(name):
        return None

    s = str(name)

    # 이상한 공백 → 일반 공백
    s = s.replace("\u3000", " ").replace("\xa0", " ")

    # 양쪽 공백 제거
    s = s.strip()
    if not s:
        return None

    # 연속 공백 → 한 칸
    s = re.sub(r"\s+", " ", s)

    # 괄호 앞뒤 공백 정리
    s = re.sub(r"\s*\(\s*", "(", s)
    s = re.sub(r"\s*\)\s*", ")", s)

    # 양 끝 특수문자 트리밍
    s = s.strip("[]{}<>\"'")

    return s or None


def make_name_key(name: str) -> str | None:
    """
    매칭용 상호 키:
    - normalize_name() 적용
    - 모든 공백 제거
    """
    base = normalize_name(name)
    if base is None:
        return None
    key = re.sub(r"\s+", "", base)
    return key or None


def normalize_person_name(s: str) -> str | None:
    """
    대표자/브로커명 정규화:
    - NaN → None
    - 앞뒤 공백 제거
    - 모든 공백 제거 (성/이름 사이 공백도 제거)
    """
    if pd.isna(s):
        return None
    t = str(s).strip()
    if not t:
        return None
    t = re.sub(r"\s+", "", t)
    return t or None


def make_name_rep_key(name_key: str | None, rep_key: str | None) -> str | None:
    """
    상호 키 + 대표자 키 → 복합키
    둘 중 하나라도 없으면 None
    """
    if not name_key or not rep_key:
        return None
    return f"{name_key}|{rep_key}"


# ---------------------------------------------------------------------
# 2. 데이터 로드
# ---------------------------------------------------------------------
match_df = pd.read_csv(PATH_MATCH_01, encoding="utf-8-sig")
broker_df = pd.read_csv(PATH_BROKER,   encoding="utf-8-sig")

print(f"\n[로드] match_01 shape      : {match_df.shape}")
print(f"[로드] broker_office shape : {broker_df.shape}")

# 필요한 컬럼 체크
need_match_cols = ["중개사명", "대표자"]
for col in need_match_cols:
    if col not in match_df.columns:
        raise KeyError(f"match_01.csv 에 '{col}' 컬럼이 없습니다.")

need_broker_cols = ["bsnmCmpnm", "brkrNm"]
for col in need_broker_cols:
    if col not in broker_df.columns:
        raise KeyError(f"broker_office.csv 에 '{col}' 컬럼이 없습니다.")


# ---------------------------------------------------------------------
# 3. match_01 쪽: 상호 + 대표자 복합키 생성
# ---------------------------------------------------------------------
match_df["상호_norm"] = match_df["중개사명"].map(normalize_name)
match_df["name_key"]  = match_df["중개사명"].map(make_name_key)
match_df["rep_key"]   = match_df["대표자"].map(normalize_person_name)

match_df["name_rep_key"] = [
    make_name_rep_key(nk, rk)
    for nk, rk in zip(match_df["name_key"], match_df["rep_key"])
]

print("\n[match_01 예시 상위 5개]")
print(match_df[["중개사명", "대표자", "상호_norm", "name_key", "rep_key", "name_rep_key"]].head())


# ---------------------------------------------------------------------
# 4. broker_office 쪽: 상호 + 대표자 복합키 생성
# ---------------------------------------------------------------------
broker_df["상호_norm"] = broker_df["bsnmCmpnm"].map(normalize_name)
broker_df["name_key"]  = broker_df["bsnmCmpnm"].map(make_name_key)
broker_df["rep_key"]   = broker_df["brkrNm"].map(normalize_person_name)

broker_df["name_rep_key"] = [
    make_name_rep_key(nk, rk)
    for nk, rk in zip(broker_df["name_key"], broker_df["rep_key"])
]

print("\n[broker_office 예시 상위 5개]")
print(
    broker_df[
        ["bsnmCmpnm", "brkrNm", "상호_norm", "name_key", "rep_key", "name_rep_key"]
    ].head()
)


# ---------------------------------------------------------------------
# 5. broker_office 복합키 기준 중복 제거
#    - 같은 [상호+대표자] 조합이 여러 행이면 첫 번째만 사용
# ---------------------------------------------------------------------
broker_key_col = "name_rep_key"

broker_keep_cols = [
    broker_key_col,
    "상호_norm",
    "brkrNm",
    "jurirno",
    "ldCode",
    "ldCodeNm",
    "registDe",
    "sttusSeCodeNm",
    "rdnmadrcode",
    "mnnmadr",
    "rdnmadr",
    "estbsBeginDe",
    "lastUpdtDt",
    "estbsEndDe",
    "sttusSeCode",
    "bsnmCmpnm",
]

# 실제 존재하는 컬럼만 사용
broker_keep_cols = [c for c in broker_keep_cols if c in broker_df.columns]

broker_dedup = (
    broker_df[broker_keep_cols]
    .dropna(subset=[broker_key_col])
    .drop_duplicates(subset=[broker_key_col], keep="first")
)

print("\n[broker_office] 복합키 기준 중복 제거 후 shape :", broker_dedup.shape)


# ---------------------------------------------------------------------
# 6. [상호 + 대표자] 복합키 기준 매칭 (LEFT JOIN: match_01 기준)
# ---------------------------------------------------------------------
merged = match_df.merge(
    broker_dedup,
    on="name_rep_key",
    how="left",
    suffixes=("_match", "_broker"),
)

print("\n[merge] 결과 shape :", merged.shape)

matched_cnt = merged["brkrNm"].notna().sum() if "brkrNm" in merged.columns else 0
print(f"[merge] 실제 매칭된 행 (brkrNm not null): {matched_cnt} / {len(merged)}")


# ---------------------------------------------------------------------
# 7. 결과 저장
# ---------------------------------------------------------------------
merged.to_csv(PATH_OUTPUT, index=False, encoding="utf-8-sig")
print(f"\n✅ 매칭 완료! → {PATH_OUTPUT}")