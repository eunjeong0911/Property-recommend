import pandas as pd
import os

BASE_DIR = r"C:/dev/study/eunjeong/SKN18-FINAL-1TEAM"
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")

PATH_INPUT  = os.path.join(DATA_DIR, "match_data_clean.csv")
PATH_OUTPUT = os.path.join(DATA_DIR, "match_data_clean.csv")  # 덮어쓰기면 파일명 같게

# 1) 데이터 로드
df = pd.read_csv(PATH_INPUT, encoding="utf-8-sig")

# 2) 혹시 모를 타입 정리 (숫자로 변환)
# 총매물수
df["거래완료"] = pd.to_numeric(df["거래완료"], errors="coerce").fillna(0).astype(int)
df["등록매물"] = pd.to_numeric(df["등록매물"], errors="coerce").fillna(0).astype(int)

# 2030 타겟 총매물수
df["빌라주택"] = pd.to_numeric(df["빌라주택"], errors="coerce").fillna(0).astype(int)
df["아파트"] = pd.to_numeric(df["아파트"], errors="coerce").fillna(0).astype(int)
df["오피스텔"] = pd.to_numeric(df["오피스텔"], errors="coerce").fillna(0).astype(int)
df["원투룸"] = pd.to_numeric(df["원투룸"], errors="coerce").fillna(0).astype(int)

# 3) 총매물수 = 거래완료 + 등록매물
df["총매물수"] = df["거래완료"] + df["등록매물"]
df["2030 타겟 총매물수"] = df["빌라주택"] + df["아파트"] + df["오피스텔"] + df["원투룸"]

print(df[["거래완료", "등록매물", "총매물수", "빌라주택", "아파트", "오피스텔", "원투룸", "2030 타겟 총매물수"]].head())
print(df.info())

# 4) 저장
df.to_csv(PATH_OUTPUT, index=False, encoding="utf-8-sig")
print("✅ 저장 완료 →", PATH_OUTPUT)