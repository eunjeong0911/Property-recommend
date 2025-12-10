"""
데이터 로드 및 결측치 전처리 (거래완료, 등록매물 NaN만 제거)
"""
import pandas as pd
import numpy as np
from pathlib import Path


def load_processed_office_data(filepath: str = "data/processed_office_data.csv") -> pd.DataFrame:
    """
    processed_office_data.csv 파일을 로드하여 DataFrame으로 반환.

    Args:
        filepath (str): 데이터 파일 경로

    Returns:
        pd.DataFrame: 로드된 데이터프레임
    """
    file = Path(filepath)

    if not file.exists():
        raise FileNotFoundError(f"[ERROR] 파일이 존재하지 않음: {filepath}")

    print(f"📊 [1단계] 데이터 로드")
    print(f"   파일: {filepath}")

    df = pd.read_csv(file, encoding="utf-8-sig")

    print(f"   행 수: {len(df):,}")
    print(f"   열 수: {len(df.columns)}")

    if "등록번호" not in df.columns:
        print("   ⚠️ 등록번호 컬럼이 존재하지 않습니다.")

    return df


def basic_preprocessing(df: pd.DataFrame) -> pd.DataFrame:
    """
    거래완료, 등록매물 컬럼 NaN 제거만 실행하는 최소 전처리

    Args:
        df (pd.DataFrame): 원본 데이터프레임

    Returns:
        pd.DataFrame: 전처리된 데이터프레임
    """

    print(f"\n🧹 [2단계] 기본 전처리 (거래완료 & 등록매물 NaN 제거)")

    # 문자열 "건" 제거 및 숫자형 변환
    df["거래완료_숫자"] = pd.to_numeric(df["거래완료"].str.replace("건", ""), errors="coerce")
    df["등록매물_숫자"] = pd.to_numeric(df["등록매물"].str.replace("건", ""), errors="coerce")

    before = len(df)
    df = df.dropna(subset=["거래완료_숫자", "등록매물_숫자"])
    after = len(df)

    print(f"   제거된 행 수: {before - after:,}개")
    print(f"   남은 행 수: {after:,}개")

    return df


def save_preprocessed(df: pd.DataFrame, filepath: str = "data/preprocessed_office_data.csv"):
    """
    전처리된 df 저장

    Args:
        df (pd.DataFrame): 전처리 완료된 데이터프레임
        filepath (str): 저장할 파일 경로
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")

    print(f"\n💾 [3단계] 전처리된 데이터 저장 완료")
    print(f"   저장 파일: {filepath}")


def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("🏠 중개사 신뢰도 모델 - 최소 전처리 모드")
    print("=" * 70)

    # STEP 1: 데이터 로드
    df = load_processed_office_data()

    # STEP 2: 거래완료/등록매물 NaN 제거
    df = basic_preprocessing(df)

    # STEP 3: 저장
    save_preprocessed(df)

    print("\n" + "=" * 70)
    print("✅ 전처리 완료!")
    print("=" * 70)

    return df


if __name__ == "__main__":
    df = main()
