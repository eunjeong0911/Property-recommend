"""
데이터 로드
"""
import pandas as pd
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

    print(f"=== Load processed office data ===")
    print(f"- File: {filepath}")

    df = pd.read_csv(file, encoding="utf-8-sig")

    print(f"- Rows: {len(df)}")
    print(f"- Columns: {len(df.columns)}")

    # 기본적인 Null 제거 또는 필요 컬럼 확인이 가능
    if "등록번호" not in df.columns:
        print("[WARNING] 등록번호 컬럼이 존재하지 않습니다. 이후 단계에서 문제가 발생할 수 있습니다.")

    return df


def main():
    df = load_processed_office_data()
    print("\n=== Preview ===")
    print(df.head())


if __name__ == "__main__":
    main()