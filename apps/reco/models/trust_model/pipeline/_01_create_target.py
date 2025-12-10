"""
01_create_target.py
중개사 성사율 기반 Z-score 및 A/B/C 등급 생성
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_preprocessed_data(filepath: str = "data/preprocessed_office_data.csv") -> pd.DataFrame:
    """
    전처리된 CSV 파일을 로드합니다.
    (00_preprocess.py에서 저장된 파일)

    Args:
        filepath (str): 파일 경로

    Returns:
        pd.DataFrame: 로드된 DataFrame
    """
    file = Path(filepath)

    if not file.exists():
        raise FileNotFoundError(f"[ERROR] 파일이 존재하지 않습니다: {filepath}")

    print(f"📂 [1단계] 전처리된 데이터 로드")
    df = pd.read_csv(file, encoding="utf-8-sig")

    print(f"   - 행 수: {len(df):,}")
    print(f"   - 열 수: {len(df.columns)}")

    return df


def create_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    Z-score 기반 타겟 생성 및 A/B/C 등급 매기기

    Args:
        df (pd.DataFrame): 전처리된 데이터프레임

    Returns:
        pd.DataFrame: 타겟 컬럼이 추가된 데이터프레임
    """

    print(f"\n🎯 [2단계] 지역평균 / 표준편차 계산 및 Z-score 생성")

    # ---------------------------------------
    # 1) 거래성사율 계산
    # ---------------------------------------
    df["거래성사율"] = np.where(
        df["등록매물_숫자"] > 0,
        df["거래완료_숫자"] / df["등록매물_숫자"],
        0
    )

    # ---------------------------------------
    # 2) 지역별 평균 & 표준편차 계산
    # ---------------------------------------
    df["지역평균"] = df.groupby("지역명")["거래성사율"].transform("mean")
    df["지역표준편차"] = df.groupby("지역명")["거래성사율"].transform("std")

    # 표준편차가 0일 수 있으므로 안정적 계산
    df["지역표준편차"] = df["지역표준편차"].replace(0, 1e-6)

    # ---------------------------------------
    # 3) 개인별 Z-score 계산
    # ---------------------------------------
    df["Zscore"] = (df["거래성사율"] - df["지역평균"]) / df["지역표준편차"]

    print("   - Z-score 예시:")
    print(df[["지역명", "거래성사율", "지역평균", "지역표준편차", "Zscore"]].head())

    # ---------------------------------------
    # 4) 분위수 기반 A/B/C 등급 생성
    # ---------------------------------------
    print("\n🏷 [3단계] A/B/C 등급 생성 (분위수 기반 30/40/30)")

    q30 = df["Zscore"].quantile(0.30)
    q70 = df["Zscore"].quantile(0.70)

    print(f"   - C 등급 상한(Z ≤): {q30:.4f}")
    print(f"   - B 등급 상한(Z ≤): {q70:.4f}")

    def classify(z):
        if z <= q30:
            return "C"
        elif z <= q70:
            return "B"
        else:
            return "A"

    df["신뢰도등급"] = df["Zscore"].apply(classify)

    print("\n📌 등급 분포:")
    print(df["신뢰도등급"].value_counts(normalize=True).map(lambda x: round(x*100, 1)))

    df["신뢰도등급_숫자"] = df["신뢰도등급"].map({"A": 2, "B": 1, "C": 0})
    df["target"] = df["신뢰도등급_숫자"]

    return df


def save_target(df: pd.DataFrame, filepath: str = "data/office_target.csv"):
    """
    타겟 생성 후 CSV 저장

    Args:
        df (pd.DataFrame): 타겟 포함 데이터프레임
        filepath (str): 저장 경로
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    print(f"\n💾 [4단계] 타겟 생성 파일 저장 완료: {filepath}")


def main():
    print("=" * 70)
    print("🎯 01_create_target.py — 중개사 타겟(Z-score & A/B/C) 생성")
    print("=" * 70)

    # 1) 전처리된 데이터 로드
    df = load_preprocessed_data("data/preprocessed_office_data.csv")

    # 2) 타겟 생성
    df = create_target(df)

    # 3) 저장
    save_target(df)

    print("\n✅ 타겟 생성 완료!")
    print("=" * 70)

    return df


if __name__ == "__main__":
    df = main()
