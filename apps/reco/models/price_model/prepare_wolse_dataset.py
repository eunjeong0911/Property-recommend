import pandas as pd
from pathlib import Path

BASE_DIR = Path(r"C:\dev\SKN18-FINAL-1TEAM\apps\reco\models\price_model\data")

# -------------------------------
# 1) 월세 데이터 전처리 함수
# -------------------------------
def load_and_filter_monthly(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="cp949")

    # 전월세 구분/면적 컬럼 자동 감지
    col_rent = "전월세구분" if "전월세구분" in df.columns else "전월세 구분"
    col_area = "임대면적" if "임대면적" in df.columns else "임대면적(㎡)"

    # 월세만 사용
    df = df[df[col_rent].astype(str).str.contains("월세", na=False)]

    # 층 처리
    df["층"] = pd.to_numeric(df.get("층", 0), errors="coerce").fillna(0)

    # 건축년도 null 제거
    df = df.dropna(subset=["건축년도"])

    # 계약일 처리 + 기간 필터링
    df["계약일"] = pd.to_datetime(df["계약일"].astype(str), format="%Y%m%d", errors="coerce")
    df = df[(df["계약일"] >= "2024-08-01") & (df["계약일"] <= "2025-10-31")]

    # 필요한 컬럼만 선택 + 통일
    df = df[[
        "자치구명", "법정동명", "층", "계약일",
        col_rent, col_area,
        "보증금(만원)", "임대료(만원)",
        "건축년도", "건물용도"
    ]].rename(columns={col_rent: "전월세구분", col_area: "임대면적"})

    return df


# -------------------------------
# 2) 금리 데이터 로드 함수
# -------------------------------
def load_rate_table(path: Path, id_col: str) -> pd.DataFrame:
    rate = pd.read_csv(path, encoding="utf-8-sig")
    rate.columns = [c.strip() for c in rate.columns]

    # month 컬럼 "2024.08" → "2024-08"
    rename_map = {
        c: f"{c.split('.')[0]}-{c.split('.')[1].zfill(2)}"
        for c in rate.columns if c != id_col
    }
    rate = rate.rename(columns=rename_map)

    # wide → long → wide
    rate_long = rate.melt(id_vars=id_col, var_name="연월", value_name="값")
    rate_pivot = rate_long.pivot(index="연월", columns=id_col, values="값").reset_index()


    # 실제 CSV의 '구분' 값에 맞춰 이름 매핑
    rate_pivot = rate_pivot.rename(columns={
        "소비자물가": "소비자물가",
        "무담보콜금리(1일)": "무담보콜금리",
        "KORIBOR(3개월)": "KORIBOR",
        "CD(91일)": "CD",
        "기업대출": "기업대출",
        "전세자금대출": "전세자금대출",
        "변동형 주택담보대출": "변동형주택담보대출",
    })

    # 숫자 변환
    for col in rate_pivot.columns:
        if col != "연월":
            rate_pivot[col] = pd.to_numeric(rate_pivot[col], errors="coerce")

    return rate_pivot

# -------------------------------
# 3) 한국은행 기준금리 로드 함수
# -------------------------------
def load_base_rate(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]

    id_col = "계정항목"
    rename_map = {
        c: f"{c.split('.')[0]}-{c.split('.')[1].zfill(2)}"
        for c in df.columns if c != id_col
    }
    df = df.rename(columns=rename_map)

    # melt
    long_df = df.melt(id_vars=id_col, var_name="연월", value_name="값")
    base = long_df[long_df[id_col] == "한국은행 기준금리"][["연월", "값"]]
    base = base.rename(columns={"값": "기준금리"})
    base["기준금리"] = pd.to_numeric(base["기준금리"], errors="coerce")
    return base

# -------------------------------
# 4) 실행 파트
# -------------------------------
if __name__ == "__main__":

    # 월세 데이터 합치기
    df_2024 = load_and_filter_monthly(BASE_DIR / "서울특별시_전월세가_2024.csv")
    df_2025 = load_and_filter_monthly(BASE_DIR / "서울특별시_전월세가_2025.csv")

    df = pd.concat([df_2024, df_2025], ignore_index=True)

    # 연월만 사용
    df["연월"] = df["계약일"].dt.to_period("M").astype(str)
    df = df.drop(columns=["계약일"])

    # 숫자형 통일
    for col in ["층", "임대면적", "보증금(만원)", "임대료(만원)", "건축년도"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # -------------------------------
    # 금리 테이블 병합
    # -------------------------------
    rate1 = load_rate_table(BASE_DIR / "(총합)시장금리_및_대출금리(24.8~25.10).csv", "구분")
    base_rate = load_base_rate(BASE_DIR / "한국은행_기준금리(24.08~25.10).csv")

    # 금리 전체 테이블
    rate_all = rate1.merge(base_rate, on="연월", how="left")

    # 월세 데이터와 merge
    df = df.merge(rate_all, on="연월", how="left")

    # -------------------------------
    # 모델링용 컬럼만 유지
    # -------------------------------
    model_cols = [
        "자치구명", "법정동명", "층", "연월",
        "임대면적", "보증금(만원)", "임대료(만원)",
        "건축년도", "건물용도",
        "소비자물가", "무담보콜금리", "KORIBOR", "CD",
        "기업대출", "전세자금대출",
        "변동형주택담보대출", "기준금리"
    ]

    df_model = df[model_cols].copy()

    # 저장
    out = BASE_DIR / "월세_모델링용(24.08~25.10).csv"
    df_model.to_csv(out, index=False, encoding="utf-8-sig")
    print("저장 완료:", out)

    # -------------------------------
    # Train/Test Split
    # -------------------------------
    # Train: 2024-01 ~ 2025-08
    train_months = [f"2024-{m:02d}" for m in range(1, 13)] + [f"2025-{m:02d}" for m in range(1, 9)]

    # Test: 2025-09 ~ 2025-10
    test_months = ["2025-09", "2025-10"]

    df_train = df_model[df_model["연월"].isin(train_months)].copy()
    df_test = df_model[df_model["연월"].isin(test_months)].copy()

    # 저장
    out_train = BASE_DIR / "월세_train(24.01~25.08).csv"
    out_test = BASE_DIR / "월세_test(25.09~25.10).csv"

    df_train.to_csv(out_train, index=False, encoding="utf-8-sig")
    df_test.to_csv(out_test, index=False, encoding="utf-8-sig")

    print("Train 저장 완료:", out_train)
    print("Test 저장 완료:", out_test)

