"""
[00] 피처 엔지니어링 및 타겟 생성 모듈
"""
import pandas as pd
import numpy as np

def trust_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    신뢰도 점수(Trust Score) 계산 및 타겟 생성
    
    Logic:
    1. 거래완료비율 계산
    2. 베이지안 보정 (Tug of War)
    3. LCB (Lower Confidence Bound) 적용 -> 신뢰도점수
    4. 점수 기반 등급화 (0: 하, 1: 중, 2: 상) -> 신뢰등급
    """
    print("\n[피처 엔지니어링] 신뢰도 점수 계산 중...")
    
    # 1. 기본 통계량
    df["거래완료비율"] = df["거래완료"] / df["총매물수"]
    df["거래완료비율"] = df["거래완료비율"].fillna(0)  # 0/0 방지
    
    # 2. 베이지안 파라미터 설정
    # C: 전체 평균 거래율
    C = df["거래완료비율"].mean()
    # m: 보정 임계값 (중위 매물 수)
    m = df["총매물수"].median()
    
    print(f"   - 전체 평균 거래율 (C): {C:.4f}")
    print(f"   - 임계값 (m): {m:.1f}")
    
    # 3. 베이지안 보정 평균 계산
    # formula: (count / (count + m)) * mean + (m / (count + m)) * C
    df["베이지안_보정점수"] = (
        (df["총매물수"] / (df["총매물수"] + m)) * df["거래완료비율"] +
        (m / (df["총매물수"] + m)) * C
    )
    
    # 4. 신뢰도 가중치 (LCB 유사 개념 적용 - 여기서는 베이지안 점수 자체를 활용하거나 추가 페널티 적용 가능)
    # 간단하게 베이지안 점수를 0~100점 환산
    df["신뢰도점수"] = df["베이지안_보정점수"] * 100
    
    # 5. 타겟 생성 (3등급 분류)
    # qcut을 사용하여 균등 분포로 나눔 (0: 하위 33%, 1: 중위 33%, 2: 상위 33%)
    try:
        df["신뢰등급"] = pd.qcut(df["신뢰도점수"], q=3, labels=[0, 1, 2])
        print("   - 타겟 생성 완료: '신뢰등급' (3등급 분할)")
        print(df["신뢰등급"].value_counts())
    except Exception as e:
        print(f"   [주의] qcut 실패, 표준편차 기반으로 분할합니다. 에러: {e}")
        # fallback: std 기반
        mean_score = df["신뢰도점수"].mean()
        std_score = df["신뢰도점수"].std()
        df["신뢰등급"] = 0
        df.loc[df["신뢰도점수"] >= mean_score - 0.5*std_score, "신뢰등급"] = 1
        df.loc[df["신뢰도점수"] >= mean_score + 0.5*std_score, "신뢰등급"] = 2
        
    return df

def preprocess_features(df: pd.DataFrame):
    """
    학습에 사용할 피처 선택 및 전처리
    """
    print("\n[피처 엔지니어링] 학습 피처 선택 중...")
    
    features = [
        "총매물수", 
        "거래완료", 
        "등록매물",
    ]
    
    # X: Features
    X = df[features].copy()
    X = X.fillna(0)
    
    # y: Target
    y = df["신뢰등급"].astype(int)
    
    return X, y, features

def main(df: pd.DataFrame):
    """
    피처 엔지니어링 메인 함수
    """
    # 1. 신뢰도 점수 및 타겟 생성
    df = trust_score(df)
    
    # 2. 피처 선택
    X, y, feature_names = preprocess_features(df)
    
    print("\n=== 피처 엔지니어링 완료 ===")
    print(f"- 피처(X) 형태: {X.shape}")
    print(f"- 타겟(y) 형태: {y.shape}")
    print(f"- 피처 이름 목록: {feature_names}")
    
    return df, X, y, feature_names

if __name__ == "__main__":
    from _00_load_data import load_processed_office_data
    
    print("=== 피처 엔지니어링 모듈 테스트 ===")
    
    # 1. 데이터 로드
    raw_df = load_processed_office_data()
    
    # 2. 피처 엔지니어링 실행
    df_processed, X, y, features = main(raw_df)
    
    # 3. 결과 검증 출력
    print("\n[검증] 생성된 컬럼 샘플 (거래완료비율, 베이지안, 신뢰도, 등급):")
    print(df_processed[["거래완료비율", "베이지안_보정점수", "신뢰도점수", "신뢰등급"]].head(10))
    
    print("\n[검증] 클래스(등급) 분포:")
    print(y.value_counts().sort_index())
    
    print("\n[검증] 최종 학습용 피처 매트릭스 샘플:")
    print(X.head())
