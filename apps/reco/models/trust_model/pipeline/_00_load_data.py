"""
데이터 로드 및 피처 엔지니어링 모듈
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

def calculate_trust_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    신뢰도 점수(Trust Score) 계산 및 타겟 생성
    
    Logic:
    1. 거래완료비율 계산
    2. 베이지안 보정 (Tug of War)
    3. LCB (Lower Confidence Bound) 적용 -> trust_score
    4. 점수 기반 등급화 (0: 하, 1: 중, 2: 상)
    """
    print("\n[Feature Engineering] Calculating Trust Score...")
    
    # 1. 기본 통계량
    df["transaction_ratio"] = df["거래완료"] / df["총매물수"]
    df["transaction_ratio"] = df["transaction_ratio"].fillna(0)  # 0/0 방지
    
    # 2. 베이지안 파라미터 설정
    # C: 전체 평균 거래율
    C = df["transaction_ratio"].mean()
    # m: 보정 임계값 (중위 매물 수)
    m = df["총매물수"].median()
    
    print(f"   - Global Mean (C): {C:.4f}")
    print(f"   - Threshold (m): {m:.1f}")
    
    # 3. 베이지안 보정 평균 계산
    # formula: (count / (count + m)) * mean + (m / (count + m)) * C
    df["bayesian_score"] = (
        (df["총매물수"] / (df["총매물수"] + m)) * df["transaction_ratio"] +
        (m / (df["총매물수"] + m)) * C
    )
    
    # 4. 신뢰도 가중치 (LCB 유사 개념 적용 - 여기서는 베이지안 점수 자체를 활용하거나 추가 페널티 적용 가능)
    # 간단하게 베이지안 점수를 0~100점 환산
    df["trust_score"] = df["bayesian_score"] * 100
    
    # 5. 타겟 생성 (3등급 분류)
    # qcut을 사용하여 균등 분포로 나눔 (0: 하위 33%, 1: 중위 33%, 2: 상위 33%)
    try:
        df["grade"] = pd.qcut(df["trust_score"], q=3, labels=[0, 1, 2])
        print("   - Target generated: 'grade' (3 quantile classes)")
        print(df["grade"].value_counts())
    except Exception as e:
        print(f"   [Warning] qcut failed, using standard dev binning. Error: {e}")
        # fallback: std 기반
        mean_score = df["trust_score"].mean()
        std_score = df["trust_score"].std()
        df["grade"] = 0
        df.loc[df["trust_score"] >= mean_score - 0.5*std_score, "grade"] = 1
        df.loc[df["trust_score"] >= mean_score + 0.5*std_score, "grade"] = 2
        
    return df

def preprocess_features(df: pd.DataFrame):
    """
    학습에 사용할 피처 선택 및 전처리
    """
    print("\n[Feature Engineering] Selecting Features...")
    
    # 사용할 수치형 피처 후보
    # TODO: '개설시작일' 등을 활용해 '경력(연차)' 피처 추가 가능
    
    features = [
        "총매물수", 
        "거래완료", 
        "등록매물",
        "transaction_ratio",  # 원본 비율
        "bayesian_score",     # 보정 점수 (Target Leakage 주의: 타겟을 이걸로 만들었으므로, 피처로 쓰면 과적합 될 수 있음)
                              # 하지만 '등급' 예측 문제라면 점수 자체가 강력한 피처가 됨.
                              # 여기서는 '등급'을 예측하는 것이 목표이므로 점수 관련 피처는 제외하는게 맞을 수도 있으나,
                              # 현재 데이터셋에 다른 정보가 많이 없으므로 포함하거나 제외를 결정해야 함.
                              # -> 일단 포함해서 '룰 베이스'가 잘 학습되는지 확인.
    ]
    
    # 타겟 생성에 직접 쓰인 변수('bayesian_score', 'trust_score')는 제외하는 것이 일반적
    # 하지만 여기서는 '중개사 특성'으로 '총매물수', '거래완료' 등을 쓰고
    # 이것들이 어떻게 등급으로 매핑되는지 학습시키는 것이 목적이라면 OK.
    
    # X: Features
    X = df[features].copy()
    X = X.fillna(0)
    
    # y: Target
    y = df["grade"].astype(int)
    
    return X, y, features

def main():
    # 1. 데이터 로드
    df = load_processed_office_data()
    
    # 2. 신뢰도 점수 및 타겟 생성
    df = calculate_trust_score(df)
    
    # 3. 피처 선택
    X, y, feature_names = preprocess_features(df)
    
    print("\n=== Data Processed ===")
    print(f"- Feature Shape: {X.shape}")
    print(f"- Target Shape: {y.shape}")
    print(f"- Feature Names: {feature_names}")
    print(f"- Class Distribution:\n{y.value_counts().sort_index()}")
    
    return df, X, y, feature_names

if __name__ == "__main__":
    main()