"""
SHAP을 이용한 모델 해석
"""
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
plt.rcParams['axes.unicode_minus'] = False


def load_model_and_data():
    """저장된 모델과 데이터 로드"""
    print("📂 모델 및 데이터 로드 중...")
    
    model_dir = Path(__file__).parent / "saved_models"
    
    # 모델 로드
    with open(model_dir / "trust_model.pkl", "rb") as f:
        model = pickle.load(f)
    
    # 스케일러 로드
    with open(model_dir / "scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    
    # 피처 이름 로드
    with open(model_dir / "feature_names.pkl", "rb") as f:
        feature_names = pickle.load(f)
    
    # 데이터 전처리 파이프라인 실행
    print("   데이터 전처리 중...")
    import sys
    pipeline_dir = Path(__file__).parent / "pipeline"
    sys.path.insert(0, str(pipeline_dir))
    
    from _00_load_data import main as load_data
    
    # 전체 파이프라인 실행
    office_df, X, y, _ = load_data()
    
    # 스케일링
    X_scaled = scaler.transform(X)
    
    print(f"   ✅ 모델: {type(model).__name__}")
    print(f"   ✅ 피처 수: {len(feature_names)}")
    print(f"   ✅ 샘플 수: {len(X)}")
    
    return model, X_scaled, X, feature_names, y


def analyze_shap(model, X_scaled, X, feature_names, sample_size=100):
    """SHAP 분석"""
    print("\n🔍 SHAP 분석 중...")
    
    try:
        import shap
    except ImportError:
        print("❌ SHAP 미설치")
        print("💡 설치: pip install shap")
        return
    
    # 샘플링 (전체 데이터는 시간이 오래 걸림)
    if len(X) > sample_size:
        indices = np.random.choice(len(X), sample_size, replace=False)
        X_sample = X_scaled[indices]
        X_original = X.iloc[indices]
    else:
        X_sample = X_scaled
        X_original = X
    
    print(f"   샘플 크기: {len(X_sample)}개")
    
    # SHAP Explainer 생성
    print("   Explainer 생성 중...")
    
    model_type = type(model).__name__
    
    if model_type in ['RandomForestClassifier', 'GradientBoostingClassifier', 'XGBClassifier']:
        # Tree 기반 모델
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample)
    elif model_type == 'LogisticRegression':
        # Linear 모델
        explainer = shap.LinearExplainer(model, X_sample)
        shap_values = explainer.shap_values(X_sample)
    else:
        # 기타 모델 (KernelExplainer - 느림)
        explainer = shap.KernelExplainer(model.predict_proba, X_sample)
        shap_values = explainer.shap_values(X_sample)
    
    print("   ✅ SHAP 값 계산 완료")
    
    return explainer, shap_values, X_sample, X_original, feature_names


def plot_shap_summary(shap_values, X_original, feature_names, class_names=['하', '중', '상']):
    """SHAP Summary Plot"""
    print("\n📊 SHAP Summary Plot 생성 중...")
    
    import shap
    
    # 다중 클래스인 경우
    if isinstance(shap_values, list):
        for i, class_name in enumerate(class_names):
            plt.figure(figsize=(12, 8))
            shap.summary_plot(
                shap_values[i], 
                X_original, 
                feature_names=feature_names,
                show=False,
                max_display=15
            )
            plt.title(f'SHAP Summary Plot - {class_name}등급', fontsize=16, pad=20)
            plt.tight_layout()
            
            output_path = Path(__file__).parent / "results" / f"shap_summary_{class_name}.png"
            output_path.parent.mkdir(exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"   ✅ 저장: {output_path}")
            plt.close()
    else:
        # 이진 분류
        plt.figure(figsize=(12, 8))
        shap.summary_plot(
            shap_values, 
            X_original, 
            feature_names=feature_names,
            show=False,
            max_display=15
        )
        plt.title('SHAP Summary Plot', fontsize=16, pad=20)
        plt.tight_layout()
        
        output_path = Path(__file__).parent / "results" / "shap_summary.png"
        output_path.parent.mkdir(exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"   ✅ 저장: {output_path}")
        plt.close()


def plot_shap_bar(shap_values, feature_names, class_names=['하', '중', '상']):
    """SHAP Bar Plot (평균 절대값)"""
    print("\n📊 SHAP Bar Plot 생성 중...")
    
    import shap
    
    # 다중 클래스인 경우
    if isinstance(shap_values, list):
        for i, class_name in enumerate(class_names):
            plt.figure(figsize=(10, 8))
            shap.summary_plot(
                shap_values[i], 
                feature_names=feature_names,
                plot_type="bar",
                show=False,
                max_display=15
            )
            plt.title(f'SHAP Feature Importance - {class_name}등급', fontsize=16, pad=20)
            plt.tight_layout()
            
            output_path = Path(__file__).parent / "results" / f"shap_bar_{class_name}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"   ✅ 저장: {output_path}")
            plt.close()
    else:
        plt.figure(figsize=(10, 8))
        shap.summary_plot(
            shap_values, 
            feature_names=feature_names,
            plot_type="bar",
            show=False,
            max_display=15
        )
        plt.title('SHAP Feature Importance', fontsize=16, pad=20)
        plt.tight_layout()
        
        output_path = Path(__file__).parent / "results" / "shap_bar.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"   ✅ 저장: {output_path}")
        plt.close()


def main():
    """메인 실행"""
    print("=" * 70)
    print("🔍 SHAP 분석 - 모델 해석")
    print("=" * 70)
    
    # 1. 모델 및 데이터 로드
    model, X_scaled, X, feature_names, y = load_model_and_data()
    
    # 2. SHAP 분석
    explainer, shap_values, X_sample, X_original, feature_names = analyze_shap(
        model, X_scaled, X, feature_names, sample_size=100
    )
    
    # 3. SHAP Summary Plot
    plot_shap_summary(shap_values, X_original, feature_names)
    
    # 4. SHAP Bar Plot
    plot_shap_bar(shap_values, feature_names)
    
    print("\n" + "=" * 70)
    print("✅ SHAP 분석 완료!")
    print("=" * 70)
    print("\n📁 결과 파일:")
    print("   - apps/reco/models/trust_model/results/shap_summary_*.png")
    print("   - apps/reco/models/trust_model/results/shap_bar_*.png")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
