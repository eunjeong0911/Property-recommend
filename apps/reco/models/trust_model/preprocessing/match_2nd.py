import pandas as pd
import os
import re

# 1) 경로 설정
BASE_DIR = r"C:/dev/study/eunjeong/SKN18-FINAL-1TEAM"
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")

PATH_MATCH01 = os.path.join(DATA_DIR, "match_01.csv")
PATH_BROKER  = os.path.join(DATA_DIR, "broker_office.csv")
OUTPUT_PATH  = os.path.join(DATA_DIR, "match_02.csv")  # 결과 파일 이름

print("match_01 경로 :", PATH_MATCH01)
print("broker_office 경로 :", PATH_BROKER)
print("결과 저장 경로 :", OUTPUT_PATH)

# 2) 데이터 로드
match_df  = pd.read_csv(PATH_MATCH01, encoding="utf-8-sig")
broker_df = pd.read_csv(PATH_BROKER,  encoding="utf-8-sig")

print("match_df shape :", match_df.shape)
print("broker_df shape:", broker_df.shape)

# 3) 주소에서 "00구 00동" / "00구 00로/길/가" / "00구" 추출 함수
def extract_gu_dong(addr: str):
    """
    예) '서울특별시 강남구 역삼동 123-4' -> '강남구 역삼동'
    """
    m = re.search(r"([가-힣]+구)\s*([가-힣0-9]+동)", str(addr))
    if m:
        return f"{m.group(1)} {m.group(2)}"
    return None

def extract_gu_road_gil_ga(addr: str):
    """
    예)
      '서울특별시 강남구 테헤란로 123' -> '강남구 테헤란로'
      '서울특별시 종로구 새문안길 12' -> '종로구 새문안길'
      '서울특별시 중구 명동가 1'    -> '중구 명동가'
    """
    m = re.search(r"([가-힣]+구)\s*([가-힣0-9]+(?:로|길|가))", str(addr))
    if m:
        return f"{m.group(1)} {m.group(2)}"
    return None

def extract_gu_only(addr: str):
    """
    예) '서울특별시 강남구 역삼동 123-4' -> '강남구'
    """
    m = re.search(r"([가-힣]+구)", str(addr))
    if m:
        return m.group(1)
    return None

# 🔥 공백 제거용 정규화 함수들
def normalize_name(x):
    if pd.isna(x):
        return None
    # 모든 공백 제거
    return re.sub(r"\s+", "", str(x))

def normalize_gu(x):
    if pd.isna(x):
        return None
    return str(x).strip()

# 🔥 4) match_01: 중개사명 / 시군구 정규화
match_df["중개사명_norm"] = match_df["중개사명"].map(normalize_name)

# 시군구명 컬럼이 있으면 우선 사용, 없으면 주소에서 추출
if "시군구명" in match_df.columns:
    match_df["gu_name"] = match_df["시군구명"]
else:
    match_df["gu_name"] = match_df["주소"].map(extract_gu_only)

match_df["gu_norm"] = match_df["gu_name"].map(normalize_gu)

# 🔥 5) broker_office: bsnmCmpnm / 시군구 정규화
broker_df["bsnmCmpnm_norm"] = broker_df["bsnmCmpnm"].map(normalize_name)

if "시군구명" in broker_df.columns:
    broker_df["gu_name"] = broker_df["시군구명"]
else:
    # 없다고 가정하면 mnnmadr(지번) 기준으로 추출
    broker_df["gu_name"] = broker_df["mnnmadr"].map(extract_gu_only)

broker_df["gu_norm"] = broker_df["gu_name"].map(normalize_gu)

# 6) match_01: 주소에서 "구 동" / "구 로·길·가" 추출
match_df["addr_dong"] = match_df["주소"].map(extract_gu_dong)
match_df["addr_road"] = match_df["주소"].map(extract_gu_road_gil_ga)

# 7) broker_office: mnnmadr(지번) / rdnmadr(도로명)에서도 같은 패턴 추출
broker_df["mnn_dong"] = broker_df["mnnmadr"].map(extract_gu_dong)
broker_df["rdn_road"] = broker_df["rdnmadr"].map(extract_gu_road_gil_ga)

# groupby().first() 안 쓰고, 원본에서 직접 조인
mnn_src = broker_df.dropna(subset=["mnn_dong"])
rdn_src = broker_df.dropna(subset=["rdn_road"])

# 8) "00구 00동" 패턴이 있는 행들만 지번주소(mnnmadr)와 매칭
#    조건: gu_norm(시군구) + addr_dong + 중개사명_norm == gu_norm + mnn_dong + bsnmCmpnm_norm
mask_dong = match_df["addr_dong"].notna()
matched_dong = match_df[mask_dong].merge(
    mnn_src,
    left_on=["gu_norm", "addr_dong", "중개사명_norm"],
    right_on=["gu_norm", "mnn_dong", "bsnmCmpnm_norm"],
    how="left",                 # ⭐ match_01 기준 (누락 없음)
    suffixes=("", "_mnn"),
)

# 9) "00구 00로/길/가" 패턴이 있는 행들만 도로명주소(rdnmadr)와 매칭
#    (동 패턴이 있는 애들은 위에서 처리했으니, 여기선 addr_dong 없는 애들만)
mask_road = match_df["addr_road"].notna() & ~mask_dong
matched_road = match_df[mask_road].merge(
    rdn_src,
    left_on=["gu_norm", "addr_road", "중개사명_norm"],
    right_on=["gu_norm", "rdn_road", "bsnmCmpnm_norm"],
    how="left",                 # ⭐ match_01 기준 (누락 없음)
    suffixes=("", "_rdn"),
)

# 10) 어떤 패턴도 안 잡힌 나머지 행들 → broker 정보 없이 그대로 유지
mask_other = ~mask_dong & ~mask_road
other = match_df[mask_other].copy()

# 11) 세 결과를 합쳐서 최종 merged 생성
merged = pd.concat([matched_dong, matched_road, other], ignore_index=True)

print("최종 merged shape:", merged.shape)
print("원본 match_01 행 개수:", len(match_df))
print("dong+road+other 합계 :", len(matched_dong) + len(matched_road) + len(other))

# 12) (선택) 디버깅용 컬럼 정리
# drop_cols = [
#     "addr_dong", "addr_road", "mnn_dong", "rdn_road",
#     "중개사명_norm", "bsnmCmpnm_norm", "gu_name", "gu_norm"
# ]
# merged = merged.drop(columns=[c for c in drop_cols if c in merged.columns])

# 13) 저장
merged.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
print("✅ 매칭 완료 & 저장 →", OUTPUT_PATH)