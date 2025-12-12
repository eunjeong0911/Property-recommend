"""
[02] 피처 엔지니어링 모듈
- 순수하게 모델 학습에 필요한 Input Feature(X)를 생성하는 코드
- 타겟 변수(y) 생성 로직은 '_01_target_engineering.py'로 분리
"""
import pandas as pd
import numpy as np

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    [Feature Creation Logic]
    변수명을 직관적이고 간단하게 생성
    """
    print("\n[피처 엔지니어링] 파생 변수(Derived Features) 생성 중...")

    # 0. 전처리
    df["총매물수"] = df["총매물수"].fillna(1)
    
    # ------------------------------------------------------------
    # 1. 기본 실적 (Basic Performance)
    # ------------------------------------------------------------
    # 단순_거래성사율 -> 성사율
    df["거래성사율"] = df["거래완료"] / df["총매물수"]
    df["거래성사율"] = df["거래성사율"].fillna(0)

    # ------------------------------------------------------------
    # 2. 직원 관련 (Staff)
    # ------------------------------------------------------------
    # Raw Data 컬럼명은 그대로 두고, 파생 변수만 간단하게
    numeric_cols = ["총_직원수", "공인중개사수", "중개보조원수", "대표수"]
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 분모 안전처리
    df["총_직원수"] = df["총_직원수"].replace(0, 1)

    # 비율 (Ratio)
    df["공인중개사비율"] = df["공인중개사수"] / df["총_직원수"]
    df["중개보조원비율"] = df["중개보조원수"] / df["총_직원수"]
    
    # ------------------------------------------------------------
    # 3. 운영 기간 (History)
    # ------------------------------------------------------------
    if "등록일" in df.columns:
        df["등록일"] = pd.to_datetime(df["등록일"], errors="coerce")
        today = pd.Timestamp.now()
        
        # 운영기간_일 -> 운영일수
        df["운영일수"] = (today - df["등록일"]).dt.days.clip(lower=0)
        # 운영기간_년 -> 운영연수
        df["운영연수"] = df["운영일수"] / 365.25
        
        # Log 변환
        df["운영일수_Log"] = np.log1p(df["운영일수"]).replace([np.inf, -np.inf], 0)
        
        # 카테고리 (Category)
        # 신규사무소 -> 신규 (1년 이하)
        df["신규"] = (df["운영연수"] <= 1).astype(int)
        # 중견사무소 -> 중견 (1~5년)
        df["중견"] = ((df["운영연수"] > 1) & (df["운영연수"] <= 5)).astype(int)
        # 노포사무소 -> 노포 (5년 이상)
        df[""] = (df["운영연수"] > 5).astype(int)
        
    else:
        cols = ["운영일수", "운영연수", "운영일수_Log", "신규", "중견", "노포"]
        for c in cols:
            df[c] = 0

    # ------------------------------------------------------------
    # 4. 전문성 및 규모 (Expertise & Size)
    # ------------------------------------------------------------
    # 복수공인중개사 -> 복수자격 (2명 이상)
    df["복수자격"] = (df["공인중개사수"] >= 2).astype(int)
    # 공인중개사만 존재 -> 전원자격
    df["전원자격"] = ((df["공인중개사수"] > 0) & (df["중개보조원수"] == 0)).astype(int)
    
    # 규모 (Size)
    # 대형사무소 -> 대형 (5명 이상)
    df["대형"] = (df["총_직원수"] >= 5).astype(int)
    # 중형사무소 -> 중형 (3~4명)
    df["중형"] = ((df["총_직원수"] >= 3) & (df["총_직원수"] < 5)).astype(int)
    # 소형사무소 -> 소형 (1~2명)
    df["소형"] = (df["총_직원수"] <= 2).astype(int)
    
    return df

def select_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    [Feature Selection]
    최종 학습에 사용할 깔끔한 변수명들만 선택
    """
    print("[피처 엔지니어링] 최종 학습 피처(X) 선택 중...")
    
    # 원본 컬럼 중 학습에 쓸 것들도 간단한 이름으로 매핑해주는 것이 좋음
    # (여기서는 X 생성 시 Rename 수행)
    
    # 1. 사용할 컬럼 정의 (Source Column -> Target Name)
    # ⚠️ 주의: 타겟(베이지안_성사율) 계산에 사용된 변수는 제외! (Data Leakage 방지)
    # 제외 대상: 총매물수, 등록매물, 거래완료, 거래성사율
    feature_map = {
        # 직원 구조 (Staff Structure)
        "총_직원수": "직원수",
        "공인중개사수": "공인중개사",
        "중개보조원수": "중개보조원",
        "공인중개사비율": "공인중개사비율",
        "중개보조원비율": "중개보조원비율",
        
        # 전문성/규모 (Expertise & Size)
        "복수자격": "복수자격",
        "전원자격": "전원자격",
        "대형": "대형",
        "중형": "중형",
        "소형": "소형",
        
        # 연력 (History)
        "운영연수": "운영연수",
        "운영일수_Log": "운영로그",
        "신규": "신규",
        "중견": "중견",
        "노포": "노포"
    }
    
    # 실제 존재하는 컬럼만 선택
    available_cols = [col for col in feature_map.keys() if col in df.columns]
    
    # 데이터셋 생성
    X = df[available_cols].copy()
    
    # 이름 변경 (직관적으로)
    X = X.rename(columns=feature_map)
    
    # 결측치 처리
    X = X.select_dtypes(include=[np.number])
    X = X.fillna(0).replace([np.inf, -np.inf], 0)
    
    return X, list(X.columns)

def main(df: pd.DataFrame):
    """
    피처 엔지니어링 메인 파이프라인
    """
    # 1. 파생 변수 생성
    df_enriched = create_features(df)
    
    # 2. 학습용 피처(X) 선택 및 리네임
    X, feature_names = select_features(df_enriched)
    
    print(f"\n✅ 피처 생성 완료: {X.shape}")
    print(f"✅ 사용된 피처 목록: {feature_names}")
    
    return df_enriched, X, feature_names

if __name__ == "__main__":
    from _00_load_data import load_processed_office_data
    
    print("=== 피처 생성 모듈 독립 실행 테스트 ===")
    raw_df = load_processed_office_data()
    
    df_result, X_result, feats = main(raw_df)
    
    print("\n[Sample X Data]")
    print(X_result.head())
