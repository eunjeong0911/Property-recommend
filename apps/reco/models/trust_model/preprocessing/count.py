import json
import os
import re
import pandas as pd

base_dir = "data/landData"  # JSON들이 있는 폴더로 바꿔줘

def parse_int_from_korean(s):
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    if not isinstance(s, str):
        s = str(s)
    # "17건", "1,234건" → 17, 1234
    digits = re.findall(r"\d+", s.replace(",", ""))
    if not digits:
        return None
    return int(digits[0])

# 00_통합_*.json 파일들 자동 탐색
files = [f for f in os.listdir(base_dir) 
         if f.startswith("00_통합_") and f.endswith(".json")]

master_df = pd.DataFrame()

for fname in files:
    path = os.path.join(base_dir, fname)
    type_name = fname.replace("00_통합_", "").replace(".json", "")  # ex) "아파트"

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for item in data:
        info = item.get("중개사_정보") or {}
        if not info:
            continue

        reg_no = info.get("등록번호")
        if not reg_no:
            continue

        row = {
            "중개사명": info.get("중개사명"),
            "대표자": info.get("대표자"),
            "주소": info.get("주소"),
            "등록번호": reg_no,
            "거래완료": parse_int_from_korean(info.get("거래완료")),
            "등록매물": parse_int_from_korean(info.get("등록매물")),
            type_name: 1,  # 이 파일에서 한 번 등장
        }
        rows.append(row)

    if not rows:
        continue

    temp_df = pd.DataFrame(rows)

    # ⚠ 거래완료/등록매물은 중복 합산 안 하고 한 번만 사용 (first)
    agg_dict = {
        "중개사명": "first",
        "대표자": "first",
        "주소": "first",
        "거래완료": "first",
        "등록매물": "first",
        type_name: "sum",  # 이 파일 안에서 몇 번 언급됐는지 카운트
    }
    grouped = temp_df.groupby("등록번호", as_index=False).agg(agg_dict)

    if master_df.empty:
        master_df = grouped
    else:
        master_df = master_df.merge(grouped, on="등록번호", how="outer", suffixes=("", "_new"))

        # 기본 정보 컬럼은 기존 값 우선, 없으면 새 값 채우기
        for col in ["중개사명", "대표자", "주소", "거래완료", "등록매물"]:
            new_col = col + "_new"
            if new_col in master_df.columns:
                master_df[col] = master_df[col].combine_first(master_df[new_col])
                master_df.drop(columns=[new_col], inplace=True)

# 아파트/오피스텔 같은 카운트 컬럼들 NaN → 0, int 변환
type_cols = [c for c in master_df.columns 
             if c not in ["중개사명", "대표자", "주소", "등록번호", "거래완료", "등록매물"]]
for c in type_cols:
    master_df[c] = master_df[c].fillna(0).astype(int)

master_df = master_df.sort_values("등록번호")

# CSV 저장
out_path = os.path.join(base_dir, "중개사_카운트.csv")
master_df.to_csv(out_path, index=False, encoding="utf-8-sig")
print("저장 완료:", out_path)
print(master_df.head())