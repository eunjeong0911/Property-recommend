"""
이진 분류 예측 파이프라인 (Binary Classification)
- 2등급: 상위(1), 하위(0)
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path

from _02_feature_engineering import main as feature_engineering



def load_saved_model(model_dir="apps/reco/models/trust_model/saved_models_binary"):
    """저장된 모델 로드"""
    model_path = Path(model_dir)
    
    with open(model_path / "trust_model.pkl", "rb") as f:
        model = pickle.load(f)
    
    with open(model_path / "scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    
    with open(model_path / "feature_names.pkl", "rb") as f:
        feature_names = pickle.load(f)
    
    print("✅ 모델 로드 완료")
    return model, scaler, feature_names


def predict_batch(office_df, model, scaler, feature_names):
    """일괄 예측"""
    X = office_df[feature_names].copy()
    X = X.fillna(0).replace([np.inf, -np.inf], 0)
    
    X_scaled = scaler.transform(X)
    predictions = model.predict(X_scaled)
    
    # 확률 예측 (가능한 경우)
    try:
        probabilities = model.predict_proba(X_scaled)[:, 1]
    except:
        probabilities = predictions
    
    office_df = office_df.copy()
    office_df["예측_등급"] = predictions
    office_df["예측_확률"] = probabilities
    
    # 등급 라벨 변환
    def grade_label(pred):
        return "상위" if pred == 1 else "하위"
    
    office_df["등급_라벨"] = office_df["예측_등급"].apply(grade_label)
    
    return office_df


def main():
    """메인 실행"""
    print("=" * 70)
    print("🔮 중개사 신뢰도 예측 (Binary Classification)")
    print("=" * 70)
    
    # 1. 모델 로드
    model, scaler, feature_names = load_saved_model()
    
    # 2. 데이터 로드
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent.parent.parent.parent
    data_dir = project_root / "data"
    office_df = pd.read_csv(data_dir / "processed_office_data_nn.csv")
    
    print(f"\n📊 {len(office_df)}개 사무소 데이터 로드")
    
    # 3. 피처 엔지니어링
    print("\n[피처 엔지니어링 수행 중...]")
    df_enriched, X, _ = feature_engineering(office_df)
    
    # 4. 예측 수행
    print("\n[예측 수행 중...]")
    X_scaled = scaler.transform(X)
    predictions = model.predict(X_scaled)
    
    # 확률 예측
    try:
        probabilities = model.predict_proba(X_scaled)[:, 1]
    except:
        probabilities = predictions
    
    # 5. 결과 추가
    result_df = df_enriched.copy()
    result_df["예측_등급"] = predictions
    result_df["예측_확률"] = probabilities
    result_df["등급_라벨"] = result_df["예측_등급"].apply(lambda x: "상위" if x == 1 else "하위")
    
    # 6. 결과 출력
    print("\n" + "=" * 70)
    print("✅ 예측 완료!")
    print("=" * 70)
    
    print("\n📈 예측 결과 샘플 (상위 10개):")
    display_cols = ["총매물수", "거래완료", "예측_확률", "등급_라벨"]
    available_cols = [c for c in display_cols if c in result_df.columns]
    print(result_df[available_cols].head(10).to_string())
    
    # 등급별 분포
    print("\n📊 예측 등급 분포:")
    print(result_df["등급_라벨"].value_counts())
    
    # 결과 저장
    output_path = data_dir / "predicted_trust_scores_binary.csv"
    result_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n💾 예측 결과 저장: {output_path}")
    
    return result_df


if __name__ == "__main__":
    result_df = main()
