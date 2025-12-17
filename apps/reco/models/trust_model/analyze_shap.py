"""
SHAP Feature 중요도 분석
- SHAP을 사용하여 모델의 feature 중요도를 분석
- 클래스별로 어떤 feature가 중요한지 시각화
"""
import pickle
import shap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
plt.rcParams['axes.unicode_minus'] = False

TEMP_MODEL_PATH = "apps/reco/models/trust_model/save_models/temp_trained_models.pkl"


def load_model_and_data():
    """저장된 모델과 데이터 로드"""
    print("📂 모델 및 데이터 로드 중...")
    
    with open(TEMP_MODEL_PATH, "rb") as f:
        temp_data = pickle.load(f)
    
    # 최고 성능 모델 선택
    models = temp_data["models"]
    cv_results = temp_data.get("cv_results", {})
    
    best_model_name = max(cv_results.keys(), key=lambda k: cv_results[k]['cv_mean'])
    model = models[best_model_name]
    
    feature_names = list(temp_data["feature_names"])
    X_test_scaled = temp_data["X_test_scaled"]
    y_test = temp_data["y_test"]
    
    print(f"   ✅ 모델: {best_model_name}")
    print(f"   ✅ 피처 수: {len(feature_names)}")
    print(f"   ✅ 테스트 샘플 수: {len(X_test_scaled)}")
    print(f"   ✅ 테스트 데이터 shape: {X_test_scaled.shape}")
    
    # 🔍 현재 사용 중인 피처명 출력 (디버깅용)
    print(f"\n🔍 현재 사용 중인 피처명:")
    for i, name in enumerate(feature_names):
        print(f"   {i+1:2d}. {name}")
    
    # 🔍 데이터 샘플 확인 (처음 5개 샘플의 처음 5개 피처)
    print(f"\n🔍 데이터 샘플 확인 (처음 5개 샘플, 처음 5개 피처):")
    for i in range(min(5, len(X_test_scaled))):
        sample_values = [f"{X_test_scaled[i][j]:.4f}" for j in range(min(5, len(feature_names)))]
        print(f"   샘플 {i+1}: {sample_values}")
    
    return model, X_test_scaled, feature_names, y_test


def get_shap_explainer(model, X_background):
    """모델 타입에 따라 적절한 SHAP Explainer 선택"""
    model_type = type(model).__name__
    print(f"   - 모델 타입: {model_type}")
    
    # Tree-based 모델 체크
    tree_models = ['RandomForestClassifier', 'GradientBoostingClassifier', 
                   'XGBClassifier', 'LGBMClassifier', 'CatBoostClassifier',
                   'DecisionTreeClassifier', 'ExtraTreesClassifier']
    
    # Linear 모델 체크
    linear_models = ['LogisticRegression', 'LinearRegression', 'Ridge', 
                     'Lasso', 'ElasticNet', 'SGDClassifier']
    
    try:
        if model_type in tree_models:
            print("   - TreeExplainer 사용")
            explainer = shap.TreeExplainer(model)
        elif model_type in linear_models:
            print("   - LinearExplainer 사용")
            explainer = shap.LinearExplainer(model, X_background)
        else:
            print("   - KernelExplainer 사용 (일반 모델)")
            # KernelExplainer는 느리므로 샘플링된 배경 데이터 사용
            background_sample = shap.sample(X_background, min(100, len(X_background)))
            explainer = shap.KernelExplainer(model.predict_proba, background_sample)
    except Exception as e:
        print(f"   ⚠️  Explainer 생성 실패, KernelExplainer로 대체: {e}")
        background_sample = shap.sample(X_background, min(100, len(X_background)))
        explainer = shap.KernelExplainer(model.predict_proba, background_sample)
    
    return explainer


def analyze_shap(model, X_test_scaled, feature_names):
    """SHAP 분석 수행"""
    print("\n🔍 SHAP 분석 시작...")
    
    # 1) SHAP Explainer 생성 (모델 타입에 맞게 자동 선택)
    print("   - SHAP Explainer 생성 중...")
    explainer = get_shap_explainer(model, X_test_scaled)
    
    # 2) SHAP 값 계산
    print("   - SHAP 값 계산 중...")
    try:
        shap_values = explainer.shap_values(X_test_scaled)
    except Exception as e:
        print(f"   ⚠️  shap_values() 실패, explainer() 사용: {e}")
        shap_values = explainer(X_test_scaled)
        if hasattr(shap_values, 'values'):
            shap_values = shap_values.values
    
    print(f"   ✅ SHAP 값 계산 완료")
    
    # SHAP 값 형태 확인 및 변환
    if isinstance(shap_values, list):
        print(f"   - 클래스 수: {len(shap_values)}")
        print(f"   - 각 클래스 SHAP shape: {shap_values[0].shape}")
    else:
        print(f"   - SHAP shape: {shap_values.shape}")
        
        # 3D 배열인 경우 (samples, features, classes) -> list of 2D arrays로 변환
        if len(shap_values.shape) == 3:
            print(f"   - 3D 배열을 list 형태로 변환 중...")
            num_classes = shap_values.shape[2]
            shap_values = [shap_values[:, :, i] for i in range(num_classes)]
            print(f"   - 변환 완료: {num_classes}개 클래스")
            print(f"   - 각 클래스 SHAP shape: {shap_values[0].shape}")
    
    return explainer, shap_values


def plot_manual_shap_importance(shap_values, feature_names, model):
    """수동으로 SHAP 중요도 시각화 (SHAP 라이브러리 시각화 문제 회피)"""
    print("\n📊 SHAP 중요도 시각화 생성 중...")
    
    # 결과 저장 디렉토리
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)
    
    class_names = model.classes_
    
    # 각 클래스별로 처리
    for i, class_name in enumerate(class_names):
        print(f"\n   처리 중: {class_name}등급")
        
        # 평균 절대 SHAP 값 계산
        mean_abs_shap = np.abs(shap_values[i]).mean(axis=0)
        
        # DataFrame 생성
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': mean_abs_shap
        }).sort_values('importance', ascending=True)
        
        # 전체 피처 표시
        top_n = len(importance_df)
        importance_df_top = importance_df
        
        # 1) Bar Plot 생성
        fig_height = max(8, top_n * 0.4)
        plt.figure(figsize=(12, fig_height))
        bars = plt.barh(importance_df_top['feature'], importance_df_top['importance'], color='steelblue')
        plt.xlabel('평균 |SHAP 값| (중요도)', fontsize=13, fontweight='bold')
        plt.ylabel('Feature', fontsize=13, fontweight='bold')
        plt.title(f'SHAP Feature 중요도 - {class_name}등급', fontsize=15, fontweight='bold', pad=20)
        plt.grid(axis='x', alpha=0.3, linestyle='--')
        
        # 값 표시
        for bar in bars:
            width = bar.get_width()
            plt.text(width * 1.02, bar.get_y() + bar.get_height()/2, 
                    f'{width:.4f}', ha='left', va='center', fontsize=10)
        
        plt.tight_layout()
        
        output_path = output_dir / f"shap_importance_{class_name}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"   ✅ 저장: {output_path}")
        plt.close()
        
        # 2) 전체 Feature 출력
        top_all = importance_df.sort_values('importance', ascending=False)
        print(f"\n   📋 {class_name}등급 - 전체 {len(top_all)}개 Feature:")
        
        for idx, row in top_all.iterrows():
            feature_name = row['feature']
            importance = row['importance']
            print(f"      {feature_name:30s}: {importance:.4f}")


def plot_shap_scatter(shap_values, X_test_scaled, feature_names, model):
    """각 Feature별 SHAP 값 분포 시각화"""
    print("\n📊 Feature별 SHAP 분포 시각화 생성 중...")
    
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)
    
    class_names = model.classes_
    
    for i, class_name in enumerate(class_names):
        print(f"\n   처리 중: {class_name}등급 - Scatter Plot")
        
        # 평균 절대 SHAP 값으로 상위 10개 feature 선택
        mean_abs_shap = np.abs(shap_values[i]).mean(axis=0)
        top_10_indices = np.argsort(mean_abs_shap)[-10:][::-1]
        
        # 2x5 그리드로 상위 10개 feature 시각화
        fig, axes = plt.subplots(2, 5, figsize=(20, 8))
        axes = axes.flatten()
        
        for plot_idx, feature_idx in enumerate(top_10_indices):
            ax = axes[plot_idx]
            
            # Scatter plot
            scatter = ax.scatter(
                X_test_scaled[:, feature_idx],
                shap_values[i][:, feature_idx],
                c=shap_values[i][:, feature_idx],
                cmap='RdBu_r',
                alpha=0.6,
                s=50
            )
            
            ax.set_xlabel(f'{feature_names[feature_idx]}', fontsize=10, fontweight='bold')
            ax.set_ylabel('SHAP 값', fontsize=10)
            ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
            ax.grid(alpha=0.3)
            
            # Colorbar
            plt.colorbar(scatter, ax=ax, label='SHAP 값')
        
        plt.suptitle(f'상위 10개 Feature의 SHAP 값 분포 - {class_name}등급', 
                     fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        
        output_path = output_dir / f"shap_scatter_{class_name}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"   ✅ 저장: {output_path}")
        plt.close()


def plot_shap_summary(shap_values, X_test_scaled, feature_names, model):
    """SHAP Summary Plot (Beeswarm) - 전체적인 Feature 중요도와 영향도"""
    print("\n📊 SHAP Summary Plot 생성 중...")
    
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)
    
    class_names = model.classes_
    
    # 각 클래스별로 Summary Plot 생성
    for i, class_name in enumerate(class_names):
        print(f"   처리 중: {class_name}등급 - Summary Plot")
        
        try:
            plt.figure(figsize=(12, 10))
            
            # SHAP Summary Plot (Beeswarm)
            shap.summary_plot(
                shap_values[i] if isinstance(shap_values, list) else shap_values,
                X_test_scaled,
                feature_names=feature_names,
                show=False,
                max_display=20
            )
            
            plt.title(f'SHAP Summary Plot - {class_name}등급', 
                     fontsize=15, fontweight='bold', pad=20)
            plt.tight_layout()
            
            output_path = output_dir / f"shap_summary_{class_name}.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"   ✅ 저장: {output_path}")
            plt.close()
        except Exception as e:
            print(f"   ⚠️  Summary Plot 생성 실패: {e}")
            plt.close()


def plot_shap_waterfall(explainer, shap_values, X_test_scaled, feature_names, model, num_samples=5):
    """SHAP Waterfall Plot - 개별 예측에 대한 설명"""
    print("\n📊 SHAP Waterfall Plot 생성 중...")
    
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)
    
    class_names = model.classes_
    
    # 각 클래스별로 샘플 선택하여 Waterfall Plot 생성
    for i, class_name in enumerate(class_names):
        print(f"   처리 중: {class_name}등급 - Waterfall Plot")
        
        # 랜덤하게 샘플 선택
        sample_indices = np.random.choice(len(X_test_scaled), 
                                         min(num_samples, len(X_test_scaled)), 
                                         replace=False)
        
        for idx, sample_idx in enumerate(sample_indices):
            try:
                plt.figure(figsize=(12, 8))
                
                # SHAP Explanation 객체 생성
                if isinstance(shap_values, list):
                    shap_val = shap_values[i][sample_idx]
                else:
                    shap_val = shap_values[sample_idx]
                
                # Waterfall plot용 Explanation 객체 생성
                explanation = shap.Explanation(
                    values=shap_val,
                    base_values=explainer.expected_value[i] if isinstance(explainer.expected_value, np.ndarray) else explainer.expected_value,
                    data=X_test_scaled[sample_idx],
                    feature_names=feature_names
                )
                
                shap.waterfall_plot(explanation, show=False, max_display=15)
                
                plt.title(f'SHAP Waterfall Plot - {class_name}등급 (샘플 {idx+1})', 
                         fontsize=15, fontweight='bold', pad=20)
                plt.tight_layout()
                
                output_path = output_dir / f"shap_waterfall_{class_name}_sample{idx+1}.png"
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                print(f"   ✅ 저장: {output_path}")
                plt.close()
            except Exception as e:
                print(f"   ⚠️  Waterfall Plot 생성 실패 (샘플 {idx+1}): {e}")
                plt.close()


def plot_shap_dependence(shap_values, X_test_scaled, feature_names, model, top_n=5):
    """SHAP Dependence Plot - Feature 간 상호작용 분석"""
    print("\n📊 SHAP Dependence Plot 생성 중...")
    
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)
    
    class_names = model.classes_
    
    for i, class_name in enumerate(class_names):
        print(f"   처리 중: {class_name}등급 - Dependence Plot")
        
        # 평균 절대 SHAP 값으로 상위 feature 선택
        mean_abs_shap = np.abs(shap_values[i] if isinstance(shap_values, list) else shap_values).mean(axis=0)
        top_features_idx = np.argsort(mean_abs_shap)[-top_n:][::-1]
        
        for feature_idx in top_features_idx:
            feature_name = feature_names[feature_idx]
            
            try:
                plt.figure(figsize=(10, 6))
                
                # Dependence plot
                shap.dependence_plot(
                    feature_idx,
                    shap_values[i] if isinstance(shap_values, list) else shap_values,
                    X_test_scaled,
                    feature_names=feature_names,
                    show=False
                )
                
                plt.title(f'SHAP Dependence Plot - {class_name}등급: {feature_name}', 
                         fontsize=14, fontweight='bold', pad=15)
                plt.tight_layout()
                
                # 파일명에 사용할 수 있도록 feature 이름 정리
                safe_feature_name = feature_name.replace('/', '_').replace('\\', '_').replace(' ', '_')
                output_path = output_dir / f"shap_dependence_{class_name}_{safe_feature_name}.png"
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                print(f"   ✅ 저장: {output_path}")
                plt.close()
            except Exception as e:
                print(f"   ⚠️  Dependence Plot 생성 실패 ({feature_name}): {e}")
                plt.close()


def main():
    """메인 실행"""
    print("=" * 70)
    print("🔍 SHAP Feature 중요도 분석")
    print("=" * 70)
    
    # 1. 모델 및 데이터 로드
    model, X_test_scaled, feature_names, y_test = load_model_and_data()
    
    # 2. SHAP 분석
    explainer, shap_values = analyze_shap(model, X_test_scaled, feature_names)
    
    # 3. SHAP 중요도 Bar Chart (가로 막대그래프)
    plot_manual_shap_importance(shap_values, feature_names, model)
    
    print("\n" + "=" * 70)
    print("✅ SHAP 분석 완료!")
    print("=" * 70)
    print("\n📁 결과 파일:")
    print("   - shap_importance_*.png : Feature 중요도 가로 막대그래프")
    print(f"\n   📂 저장 위치: apps/reco/models/trust_model/results/")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

