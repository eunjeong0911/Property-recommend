"""
Feature 중요도 분석 (LogisticRegression 계수 기반)
- 모델이 추론하는데 각 feature가 결과에 얼마나 기여했는지 분석
- 가로 막대 그래프로 feature 중요도 시각화
"""
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
plt.rcParams['axes.unicode_minus'] = False

TEMP_MODEL_PATH = "apps/reco/models/trust_model/save_models/temp_trained_models.pkl"


def load_model_and_data():
    """저장된 모델과 데이터 로드"""
    print("📂 모델 및 데이터 로드 중...")
    
    # temp 모델 로드 (테스트 데이터 포함)
    with open(TEMP_MODEL_PATH, "rb") as f:
        temp_data = pickle.load(f)
    
    # 최고 성능 모델 선택 (LogisticRegression_Optimized)
    models = temp_data["models"]
    cv_results = temp_data.get("cv_results", {})
    
    # CV 점수 기준으로 최고 모델 선택
    best_model_name = max(cv_results.keys(), key=lambda k: cv_results[k]['cv_mean'])
    model = models[best_model_name]
    
    scaler = temp_data["scaler"]
    feature_names = temp_data["feature_names"]
    
    # feature_names가 리스트인지 확인하고 변환
    if not isinstance(feature_names, list):
        feature_names = list(feature_names)
    
    X_test_scaled = temp_data["X_test_scaled"]
    y_test = temp_data["y_test"]
    
    print(f"   ✅ 모델: {best_model_name}")
    print(f"   ✅ 피처 수: {len(feature_names)}")
    print(f"   ✅ 테스트 샘플 수: {len(X_test_scaled)}")
    
    return model, X_test_scaled, feature_names, y_test


def get_feature_importance_from_coefficients(model, feature_names):
    """LogisticRegression 계수로부터 Feature 중요도 추출"""
    print("\n🔍 Feature 중요도 계산 중...")
    
    # LogisticRegression의 계수 가져오기
    coefficients = model.coef_  # shape: (n_classes, n_features)
    
    print(f"   계수 shape: {coefficients.shape}")
    print(f"   클래스 수: {len(model.classes_)}")
    print(f"   클래스: {model.classes_}")
    
    # 각 클래스별 계수의 절대값을 중요도로 사용
    importance_by_class = {}
    
    for i, class_label in enumerate(model.classes_):
        # 해당 클래스의 계수
        class_coef = coefficients[i]
        
        # 절대값을 중요도로 사용
        importance = np.abs(class_coef)
        
        importance_by_class[class_label] = importance
    
    print("   ✅ Feature 중요도 계산 완료")
    
    return importance_by_class


def plot_feature_importance(importance_by_class, feature_names):
    """Feature 중요도를 가로 막대 그래프로 시각화"""
    print("\n📊 Feature 중요도 그래프 생성 중...")
    
    # 결과 저장 디렉토리
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)
    
    # 각 클래스별로 그래프 생성
    for class_label, importance in importance_by_class.items():
        print(f"\n   처리 중: {class_label}등급")
        
        # Feature 중요도 데이터프레임 생성
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        }).sort_values('importance', ascending=True)  # 오름차순 정렬 (가로 막대)
        
        # 상위 20개만 표시
        top_n = min(20, len(importance_df))
        importance_df = importance_df.tail(top_n)
        
        # 그래프 생성
        fig_height = max(8, top_n * 0.4)
        plt.figure(figsize=(12, fig_height))
        bars = plt.barh(importance_df['feature'], importance_df['importance'], color='steelblue')
        plt.xlabel('계수 절대값 (중요도)', fontsize=13, fontweight='bold')
        plt.ylabel('Feature', fontsize=13, fontweight='bold')
        plt.title(f'Feature 중요도 - {class_label}등급 예측', fontsize=15, fontweight='bold', pad=20)
        plt.grid(axis='x', alpha=0.3, linestyle='--')
        
        # 값 표시
        for bar in bars:
            width = bar.get_width()
            plt.text(width * 1.02, bar.get_y() + bar.get_height()/2, 
                    f'{width:.3f}', ha='left', va='center', fontsize=10)
        
        plt.tight_layout()
        
        # 저장
        output_path = output_dir / f"feature_importance_{class_label}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"   ✅ 저장: {output_path}")
        plt.close()
        
        # 중요도 테이블 출력
        print(f"\n   📋 {class_label}등급 - 상위 10개 Feature:")
        top_10 = importance_df.tail(10).sort_values('importance', ascending=False)
        for idx, row in top_10.iterrows():
            print(f"      {row['feature']:30s}: {row['importance']:.4f}")


def main():
    """메인 실행"""
    print("=" * 70)
    print("🔍 Feature 중요도 분석 (LogisticRegression 계수 기반)")
    print("=" * 70)
    
    # 1. 모델 및 데이터 로드
    model, X_test_scaled, feature_names, y_test = load_model_and_data()
    
    # 2. Feature 중요도 계산
    importance_by_class = get_feature_importance_from_coefficients(model, feature_names)
    
    # 3. Feature 중요도 시각화
    plot_feature_importance(importance_by_class, feature_names)
    
    print("\n" + "=" * 70)
    print("✅ Feature 중요도 분석 완료!")
    print("=" * 70)
    print("\n📁 결과 파일:")
    print("   - apps/reco/models/trust_model/results/feature_importance_*.png")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
