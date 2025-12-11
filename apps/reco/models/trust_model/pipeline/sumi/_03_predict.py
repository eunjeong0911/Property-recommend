"""
학습된 모델을 사용한 예측 파이프라인
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path


def load_saved_model(model_dir="apps/reco/models/trust_model/saved_models"):
    """
    저장된 모델, 스케일러, 피처 이름 로드
    
    Args:
        model_dir: 모델 저장 디렉토리
        
    Returns:
        model, scaler, feature_names
    """
    model_path = Path(model_dir)
    
    # 모델 로드
    with open(model_path / "trust_model.pkl", "rb") as f:
        model = pickle.load(f)
    
    # 스케일러 로드
    with open(model_path / "scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    
    # 피처 이름 로드
    with open(model_path / "feature_names.pkl", "rb") as f:
        feature_names = pickle.load(f)
    
    print("✅ 모델 로드 완료")
    return model, scaler, feature_names


def predict_trust_level(office_data, model, scaler, feature_names):
    """
    사무소 신뢰도 등급 예측
    
    Args:
        office_data: 사무소 데이터 (DataFrame 또는 dict)
        model: 학습된 모델
        scaler: 스케일러
        feature_names: 피처 이름 리스트
        
    Returns:
        예측 등급, 예측 확률
    """
    # DataFrame으로 변환
    if isinstance(office_data, dict):
        office_data = pd.DataFrame([office_data])
    
    # 피처 추출
    X = office_data[feature_names]
    
    # 스케일링
    X_scaled = scaler.transform(X)
    
    # 예측
    prediction = model.predict(X_scaled)[0]
    probabilities = model.predict_proba(X_scaled)[0]
    
    # 등급 매핑
    class_names = ["하", "중", "상"]
    predicted_class = class_names[prediction]
    
    return predicted_class, probabilities


def predict_batch(office_df, model, scaler, feature_names):
    """
    여러 사무소에 대한 일괄 예측
    
    Args:
        office_df: 사무소 데이터 DataFrame
        model: 학습된 모델
        scaler: 스케일러
        feature_names: 피처 이름 리스트
        
    Returns:
        예측 결과가 추가된 DataFrame
    """
    # 피처 추출
    X = office_df[feature_names]
    
    # 스케일링
    X_scaled = scaler.transform(X)
    
    # 예측
    predictions = model.predict(X_scaled)
    probabilities = model.predict_proba(X_scaled)
    
    # 등급 매핑
    class_names = ["하", "중", "상"]
    office_df["예측_신뢰도등급"] = [class_names[p] for p in predictions]
    office_df["예측_확률_하"] = probabilities[:, 0]
    office_df["예측_확률_중"] = probabilities[:, 1]
    office_df["예측_확률_상"] = probabilities[:, 2]
    
    return office_df


def main():
    """메인 실행 함수 - 예측 예시"""
    print("=" * 70)
    print("🔮 중개사 신뢰도 예측")
    print("=" * 70)
    
    # 모델 로드
    model, scaler, feature_names = load_saved_model()
    
    # 전처리된 데이터 로드
    current_file = Path(__file__)
    data_dir = current_file.parent.parent.parent.parent.parent.parent / "data"
    office_df = pd.read_csv(data_dir / "processed_office_data.csv")
    
    print(f"\n📊 {len(office_df)}개 사무소 예측 중...")
    
    # 일괄 예측
    result_df = predict_batch(office_df, model, scaler, feature_names)
    
    # 결과 출력
    print("\n✅ 예측 완료!")
    print("\n📈 예측 결과 샘플 (상위 10개):")
    print(
        result_df[
            [
                "land_중개사명",
                "거래완료",
                "등록매물",
                "신뢰도등급",
                "예측_신뢰도등급",
                "예측_확률_상",
            ]
        ]
        .sort_values("예측_확률_상", ascending=False)
        .head(10)
    )
    
    # 예측 정확도
    if "신뢰도등급_숫자" in result_df.columns:
        accuracy = (
            result_df["신뢰도등급"] == result_df["예측_신뢰도등급"]
        ).mean()
        print(f"\n🎯 전체 예측 정확도: {accuracy:.4f}")
    
    return result_df


if __name__ == "__main__":
    result_df = main()
