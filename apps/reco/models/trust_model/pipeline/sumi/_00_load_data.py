"""
데이터 로드 모듈
"""
import pandas as pd
import numpy as np
from pathlib import Path

def load_processed_office_data(filepath: str = "data/processed_office_data_nn.csv") -> pd.DataFrame:
    """
    processed_office_data_nn.csv 파일을 로드하여 DataFrame으로 반환.
    """
    file = Path(filepath)
    if not file.exists():
        raise FileNotFoundError(f"[ERROR] 파일이 존재하지 않음: {filepath}")

    print(f"=== Load processed office data nn ===")
    print(f"- File: {filepath}")

    df = pd.read_csv(file, encoding="utf-8-sig")
    
    # 총매물수 컬럼 생성 (없는 경우)
    if "총매물수" not in df.columns:
        df["총매물수"] = df["거래완료"] + df["등록매물"]
        
    print(f"- Rows: {len(df)}")
    print(f"- Columns: {len(df.columns)}")
    
    return df

def main():
    """메인 실행 함수"""
    print("📊 데이터 로드 및 전처리 중...")

    # STEP 1: 데이터 로드
    df = load_processed_office_data()
    print("\n=== Preview ===")
    print(df.head())
    return df

if __name__ == "__main__":
    df = main()
