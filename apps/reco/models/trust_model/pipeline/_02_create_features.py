"""
02_create_features.py
Feature Engineering
- 01_create_target.py에서 생성된 데이터 로드
- 모델 학습용 Feature 생성 (파생변수, 로그변환, 비율 등)
- 최종 X, y 데이터셋 저장
"""

import pandas as pd
import numpy as np
from pathlib import Path

def load_target_data(train_path="data/ML/trust/train_target.csv", test_path="data/ML/trust/test_target.csv"):
    """01단계에서 생성된 데이터 로드"""
    print(f"📂 [1단계] 데이터 로드")
    if not Path(train_path).exists() or not Path(test_path).exists():
        raise FileNotFoundError("이전 단계의 결과 파일이 없습니다. _01_create_target.py를 먼저 실행하세요.")
        
    train_df = pd.read_csv(train_path, encoding="utf-8-sig")
    test_df = pd.read_csv(test_path, encoding="utf-8-sig")
    print(f"   - Train: {len(train_df):,}개")
    print(f"   - Test:  {len(test_df):,}개")
    return train_df, test_df

def feature_engineering(df: pd.DataFrame):
    """
    Feature 생성 로직 (Train/Test 공통 적용)
    """
    # 0. 데이터 타입 변환 
    numeric_cols = ["공인중개사수", "중개보조원수", "중개인수", "법인수"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # ------------------------------------
    # 1. 거래 및 실적 지표 (Log 변환)
    # ------------------------------------
    # 왜도(Skewness)가 심한 데이터는 로그 변환이 모델 성능에 도움됨
    df["등록매물_log"] = np.log1p(df["등록매물"])
    df["총거래활동량_log"] = np.log1p(df["거래완료"] + df["등록매물"])

    # ------------------------------------
    # 2. 인력 및 전문성 지표
    # ------------------------------------
    # Division by Zero 방지
    df["공인중개사_비율"] = np.where(df["총_직원수"] > 0, df["공인중개사수"] / df["총_직원수"], 0)
    df["중개보조원_비율"] = np.where(df["총_직원수"] > 0, df["중개보조원수"] / df["총_직원수"], 0)
    df["중개인_비율"] = np.where(df["총_직원수"] > 0, df["중개인수"] / df["총_직원수"], 0)
    df["법인_비율"] = np.where(df["총_직원수"] > 0, df["법인수"] / df["총_직원수"], 0)

    # ------------------------------------
    # 3. 운영 경험 및 숙련도
    # ------------------------------------
    df["등록일"] = pd.to_datetime(df["등록일"], errors="coerce")
    today = pd.Timestamp.now()
    
    # 운영기간 (년 단위)
    df["운영기간_일"] = (today - df["등록일"]).dt.days.clip(lower=0)
    df["운영기간_년"] = (df["운영기간_일"] / 365.25).fillna(0)
    
    # 파생 변수
    df["숙련도_지수"] = df["운영기간_년"] * df["공인중개사_비율"] # 경력과 전문성 결합
    df["운영_안정성"] = (df["운영기간_년"] >= 3).astype(int) # 3년 이상 생존 여부

    # ------------------------------------
    # 4. 조직 구조
    # ------------------------------------
    df["대형사무소"] = (df["총_직원수"] >= 2).astype(int) # 기준: 2명 이상
    
    # 직책 다양성: 구성원이 다양한가?
    df["직책_다양성"] = (
        (df["공인중개사수"] > 0).astype(int) +
        (df["중개보조원수"] > 0).astype(int) +
        (df.get("법인수", 0) > 0).astype(int) +
        (df.get("중개인수", 0) > 0).astype(int)
    )

    # ------------------------------------
    # 5. 대표자 자격 (원-핫 인코딩)
    # ------------------------------------
    df["대표_공인중개사"] = (df["대표자구분명"] == "공인중개사").astype(int)
    df["대표_법인"] = (df["대표자구분명"] == "법인").astype(int)
    df["대표_중개인"] = (df["대표자구분명"] == "중개인").astype(int)
    df["대표_중개보조원"] = (df["대표자구분명"] == "중개보조원").astype(int)

    # ------------------------------------
    # 6. 상호작용 피처 (Interaction Features)
    # ------------------------------------
    # 활동량과 다른 피처들의 결합으로 더 정교한 평가
    df["활동량_경력_지수"] = df["총거래활동량_log"] * df["운영기간_년"]
    df["활동량_전문성_지수"] = df["총거래활동량_log"] * df["공인중개사_비율"]

    return df

def select_features(df: pd.DataFrame):
    """모델 학습에 사용할 최종 Feature 선택"""
    
    final_features = [
        # 1. 실적
        "등록매물_log", 
        "총거래활동량_log",
        
        # 2. 인력
        "총_직원수",
        # "공인중개사_비율",  # 제거: VIF 53.85, 중개보조원_비율과 -0.97 상관
        "중개보조원_비율",
        # "중개인_비율",      # 제거: 분산 0.000936, 99.1%가 0
        # "법인_비율",        # 제거: 분산 0.003681, 97.4%가 0
        
        # 3. 경험
        "운영기간_년",
        "숙련도_지수",
        "운영_안정성",
        
        # 4. 구조
        "대형사무소", 
        # "직책_다양성",      # 제거: VIF 5.88, 다른 피처와 중복
        
        # 5. 대표자
        "대표_공인중개사",
        "대표_법인",
        # "대표_중개인",      # 제거: 분산 0.008498, 99.1%가 0
        # "대표_중개보조원",  # 제거: 분산 0.002849, 99.7%가 0
        
        # 6. 상호작용 피처
        # "활동량_경력_지수",    # 제거: VIF 12.71, 운영기간_년과 0.91 상관
        # "활동량_전문성_지수"   # 제거: VIF 14.07, 공인중개사_비율과 0.80 상관
    ]
    
    # Feature Matrix (X)
    X = df[final_features].copy()
    
    # 결측치 최종 처리 (머신러닝 입력용)
    X = X.replace([np.inf, -np.inf], 0).fillna(0)
    
    return X, final_features

def main():
    print(f"\n🔧 [2단계] Feature Engineering 수행")
    
    # 1. 로드
    train_df, test_df = load_target_data()
    
    # 2. Feature 생성
    train_processed = feature_engineering(train_df)
    test_processed = feature_engineering(test_df)
    
    # 3. X, y 분리
    X_train, feature_cols = select_features(train_processed)
    y_train = train_processed["Target"] # 01단계에서 생성된 Target (0, 1, 2)
    
    X_test, _ = select_features(test_processed)
    y_test = test_processed["Target"]
    
    # 4. 저장
    save_dir = Path("data/ML/trust")
    save_dir.mkdir(parents=True, exist_ok=True)
    
    X_train.to_csv(save_dir / "X_train.csv", index=False, encoding="utf-8-sig")
    y_train.to_csv(save_dir / "y_train.csv", index=False, encoding="utf-8-sig")
    X_test.to_csv(save_dir / "X_test.csv", index=False, encoding="utf-8-sig")
    y_test.to_csv(save_dir / "y_test.csv", index=False, encoding="utf-8-sig")
    
    # Feature 이름도 저장 (나중에 중요도 시각화 등에 사용)
    pd.DataFrame({"feature": feature_cols}).to_csv(save_dir / "feature_names.csv", index=False, encoding="utf-8-sig")
    
    print(f"\n💾 [3단계] 저장 완료 ({save_dir})")
    print(f"   - Feature 수: {len(feature_cols)}개")
    print(f"   - Train X: {X_train.shape}, y: {y_train.shape}")
    print(f"   - Test  X: {X_test.shape},  y: {y_test.shape}")
    
    # 미리보기
    print("\n   [생성된 Feature 목록]")
    print(f"   {feature_cols}")

if __name__ == "__main__":
    main()
