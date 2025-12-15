"""
model_analysis.py
모델 분석 도구 - SHAP, 피처 중요도, 타겟 분포, 모델 비교
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


# ============================================================
# 경로 설정
# ============================================================
MODEL_PATH = "apps/reco/models/trust_model/save_models/temp_trained_models.pkl"
FEATURE_PATH = "data/ML/office_features.csv"
TARGET_PATH = "data/ML/office_target.csv"


def load_model_data():
    """저장된 모델 데이터 로드"""
    with open(MODEL_PATH, 'rb') as f:
        data = pickle.load(f)
    return data


def show_target_distribution():
    """타겟 분포 출력"""
    print("\n" + "=" * 60)
    print(" " * 15 + "📊 타겟 분포 분석")
    print("=" * 60)
    
    df = pd.read_csv(TARGET_PATH, encoding='utf-8-sig')
    target_col = '신뢰도등급'
    
    if target_col in df.columns:
        dist = df[target_col].value_counts().sort_index()
        pct = df[target_col].value_counts(normalize=True).sort_index() * 100
        
        print(f"\n{'등급':<10} {'개수':<10} {'비율':<10}")
        print("-" * 30)
        for grade in dist.index:
            print(f"{grade:<10} {dist[grade]:<10} {pct[grade]:.1f}%")
        print(f"\n총 샘플 수: {len(df)}개")


def show_model_comparison():
    """모델별 성능 비교"""
    print("\n" + "=" * 60)
    print(" " * 15 + "🏆 모델 성능 비교")
    print("=" * 60)
    
    data = load_model_data()
    cv_results = data.get('cv_results', {})
    
    results = []
    for name, metrics in cv_results.items():
        results.append({
            '모델': name,
            'Test Acc': f"{metrics['test_acc']*100:.1f}%",
            'Train Acc': f"{metrics['train_acc']*100:.1f}%",
            '과적합률': f"{(metrics['train_acc'] - metrics['test_acc'])*100:.1f}%",
            'CV Mean': f"{metrics['cv_mean']*100:.1f}%",
        })
    
    df = pd.DataFrame(results)
    df = df.sort_values('Test Acc', ascending=False)
    print(f"\n{df.to_string(index=False)}")
    
    # 최고 모델 하이라이트
    best = max(cv_results.items(), key=lambda x: x[1]['test_acc'])
    print(f"\n🏆 최고 Test 성능: {best[0]} ({best[1]['test_acc']*100:.1f}%)")


def show_feature_importance():
    """피처 중요도 분석 (여러 모델)"""
    print("\n" + "=" * 60)
    print(" " * 15 + "📈 피처 중요도 분석")
    print("=" * 60)
    
    data = load_model_data()
    models = data['models']
    feature_names = data['feature_names']
    
    importance_data = {}
    
    # CatBoost
    if 'CatBoost' in models:
        cat_model = models['CatBoost']
        importance_data['CatBoost'] = cat_model.get_feature_importance()
    
    # XGBoost
    if 'XGBoost' in models:
        xgb_model = models['XGBoost']
        importance_data['XGBoost'] = xgb_model.feature_importances_
    
    # RandomForest
    if 'RandomForest' in models:
        rf_model = models['RandomForest']
        importance_data['RandomForest'] = rf_model.feature_importances_
    
    for model_name, importance in importance_data.items():
        print(f"\n--- {model_name} 피처 중요도 ---")
        df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': importance
        })
        df = df.sort_values('Importance', ascending=False)
        df['Importance'] = df['Importance'].apply(lambda x: f"{x:.4f}")
        print(df.to_string(index=False))


def show_shap_analysis():
    """SHAP 분석 (CatBoost 기준)"""
    print("\n" + "=" * 60)
    print(" " * 15 + "🔍 SHAP 분석")
    print("=" * 60)
    
    try:
        import shap
    except ImportError:
        print("\n⚠️ SHAP 라이브러리가 설치되지 않았습니다.")
        print("   설치: pip install shap")
        return
    
    data = load_model_data()
    models = data['models']
    feature_names = data['feature_names']
    X_test = data['X_test_scaled']
    
    # CatBoost SHAP
    if 'CatBoost' in models:
        print("\n--- CatBoost SHAP 분석 ---")
        cat_model = models['CatBoost']
        
        explainer = shap.TreeExplainer(cat_model)
        shap_values = explainer.shap_values(X_test)
        
        # 평균 절대 SHAP 값
        if isinstance(shap_values, list):
            # 다중 클래스: 모든 클래스의 평균
            mean_shap = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
        else:
            mean_shap = np.abs(shap_values).mean(axis=0)
        
        df = pd.DataFrame({
            'Feature': feature_names,
            'Mean |SHAP|': mean_shap
        })
        df = df.sort_values('Mean |SHAP|', ascending=False)
        df['Mean |SHAP|'] = df['Mean |SHAP|'].apply(lambda x: f"{x:.4f}")
        print(df.to_string(index=False))
        
        print("\n📊 SHAP 요약:")
        top3 = df.head(3)['Feature'].tolist()
        print(f"   가장 중요한 피처: {', '.join(top3)}")


def show_confusion_matrix_summary():
    """혼동 행렬 요약"""
    print("\n" + "=" * 60)
    print(" " * 15 + "📋 혼동 행렬 요약")
    print("=" * 60)
    
    data = load_model_data()
    models = data['models']
    X_test = data['X_test_scaled']
    y_test = data['y_test']
    
    from sklearn.metrics import confusion_matrix
    
    for name, model in models.items():
        if name == 'Ensemble':
            continue
        y_pred = model.predict(X_test)
        cm = confusion_matrix(y_test, y_pred)
        
        print(f"\n--- {name} ---")
        print(f"     예측A  예측B  예측C")
        labels = ['A', 'B', 'C']
        for i, row in enumerate(cm):
            print(f"실제{labels[i]}  {row[0]:>4}  {row[1]:>4}  {row[2]:>4}")


def run_all_analysis():
    """전체 분석 실행"""
    print("\n" + "=" * 60)
    print(" " * 10 + "🔬 중개사 신뢰도 모델 분석 리포트")
    print("=" * 60)
    
    show_target_distribution()
    show_model_comparison()
    show_feature_importance()
    show_confusion_matrix_summary()
    show_shap_analysis()
    
    print("\n" + "=" * 60)
    print(" " * 15 + "✅ 분석 완료!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_analysis()
