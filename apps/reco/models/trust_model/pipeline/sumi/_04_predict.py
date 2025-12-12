"""
학습된 모델을 사용한 예측 파이프라인 (Regression)
- 타겟: 베이지안_성사율 (연속형)
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path

# 피처 엔지니어링 모듈 import
from _02_feature_engineering import main as feature_engineering


def load_saved_model(model_dir="apps/reco/models/trust_model/saved_models"):
    """
    저장된 모델, 스케일러, 피처 이름 로드
    """
    model_path = Path(model_dir)
    
    with open(model_path / "trust_model.pkl", "rb") as f:
        model = pickle.load(f)
    
    with open(model_path / "scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    
    with open(model_path / "feature_names.pkl", "rb") as f:
        feature_names = pickle.load(f)
    
    print("✅ 모델 로드 완료")
    return model, scaler, feature_names


def predict_trust_score(X, model, scaler):
    """
    신뢰도 점수 예측 (Regression)
    
    Args:
        X: 피처 데이터 (DataFrame)
        model: 학습된 Regressor
        scaler: StandardScaler
        
    Returns:
        예측된 신뢰도 점수 (array)
    """
    X_scaled = scaler.transform(X)
    predictions = model.predict(X_scaled)
    return predictions


def predict_batch(office_df, model, scaler, feature_names):
    """
    여러 사무소에 대한 일괄 예측
    
    Args:
        office_df: 사무소 데이터 DataFrame (피처 엔지니어링 완료된 상태)
        model: 학습된 모델
        scaler: 스케일러
        feature_names: 피처 이름 리스트
        
    Returns:
        예측 결과가 추가된 DataFrame
    """
    # 피처 추출 (이미 생성된 피처에서 선택)
    X = office_df[feature_names].copy()
    X = X.fillna(0).replace([np.inf, -np.inf], 0)
    
    # 스케일링 및 예측
    X_scaled = scaler.transform(X)
    predictions = model.predict(X_scaled)
    
    # 결과 추가
    office_df = office_df.copy()
    office_df["예측_신뢰도점수"] = predictions
    
    # 등급 부여 (Mean ± 1 Std 기준)
    mean_score = predictions.mean()
    std_score = predictions.std()
    
    def assign_grade(score):
        if score >= mean_score + std_score:
            return "S"
        elif score >= mean_score:
            return "A"
        elif score >= mean_score - std_score:
            return "B"
        else:
            return "C"
    
    office_df["예측_등급"] = office_df["예측_신뢰도점수"].apply(assign_grade)
    
    return office_df


def main():
    """메인 실행 함수 - 예측 예시"""
    print("=" * 70)
    print("🔮 중개사 신뢰도 예측 (Regression)")
    print("=" * 70)
    
    # 1. 모델 로드
    model, scaler, feature_names = load_saved_model()
    
    # 2. 데이터 로드
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent.parent.parent.parent
    data_dir = project_root / "data"
    office_df = pd.read_csv(data_dir / "processed_office_data_nn.csv")
    
    print(f"\n📊 {len(office_df)}개 사무소 데이터 로드")
    
    # 3. 피처 엔지니어링 수행
    print("\n[피처 엔지니어링 수행 중...]")
    df_enriched, X, _ = feature_engineering(office_df)
    
    # 4. 예측 수행 (X는 이미 올바른 컬럼명을 가지고 있음)
    print("\n[예측 수행 중...]")
    X_scaled = scaler.transform(X)
    predictions = model.predict(X_scaled)
    
    # 5. 결과 추가
    result_df = df_enriched.copy()
    result_df["예측_신뢰도점수"] = predictions
    
    # 등급 부여 (Mean ± 1 Std 기준)
    mean_score = predictions.mean()
    std_score = predictions.std()
    
    def assign_grade(score):
        if score >= mean_score + std_score:
            return "S"
        elif score >= mean_score:
            return "A"
        elif score >= mean_score - std_score:
            return "B"
        else:
            return "C"
    
    result_df["예측_등급"] = result_df["예측_신뢰도점수"].apply(assign_grade)
    
    # 5. 결과 출력
    print("\n" + "=" * 70)
    print("✅ 예측 완료!")
    print("=" * 70)
    
    print("\n📈 예측 결과 샘플 (상위 10개):")
    display_cols = ["ldCodeNm", "총매물수", "거래완료", "예측_신뢰도점수", "예측_등급"]
    available_cols = [c for c in display_cols if c in result_df.columns]
    print(result_df[available_cols].head(10).to_string())
    
    # 등급별 분포
    print("\n📊 예측 등급 분포:")
    print(result_df["예측_등급"].value_counts().sort_index())
    
    # 결과 저장
    output_path = data_dir / "predicted_trust_scores.csv"
    result_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n💾 예측 결과 저장: {output_path}")
    
    return result_df


if __name__ == "__main__":
    result_df = main()
