"""
model_analysis.py
모델 분석 도구 - SHAP, 피처 중요도, 타겟 분포, 모델 비교 + 시각화
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 시각화 저장 경로
SAVE_DIR = Path("apps/reco/models/trust_model/analysisㅈ_plots")
SAVE_DIR.mkdir(parents=True, exist_ok=True)


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
    """타겟 분포 출력 + 시각화"""
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
        
        # 시각화
        fig, ax = plt.subplots(figsize=(8, 5))
        colors = ['#2ecc71', '#3498db', '#e74c3c']  # A=green, B=blue, C=red
        bars = ax.bar(dist.index, dist.values, color=colors, edgecolor='black')
        
        for bar, p in zip(bars, pct.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                   f'{p:.1f}%', ha='center', fontsize=12, fontweight='bold')
        
        ax.set_xlabel('신뢰도 등급', fontsize=12)
        ax.set_ylabel('개수', fontsize=12)
        ax.set_title('타겟 분포 (A/B/C 등급)', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(SAVE_DIR / '1_target_distribution.png', dpi=150)
        plt.close()
        print(f"\n📊 그래프 저장: {SAVE_DIR / '1_target_distribution.png'}")


def show_model_comparison():
    """모델별 성능 비교 + 추가 지표 + 시각화"""
    from sklearn.metrics import f1_score, cohen_kappa_score
    
    print("\n" + "=" * 60)
    print(" " * 15 + "🏆 모델 성능 비교")
    print("=" * 60)
    
    data = load_model_data()
    cv_results = data.get('cv_results', {})
    models = data['models']
    X_test = data['X_test_scaled']
    y_test = data['y_test']
    
    results = []
    for name, metrics in cv_results.items():
        # 추가 지표 계산
        if name in models:
            y_pred = models[name].predict(X_test)
            f1_macro = f1_score(y_test, y_pred, average='macro')
            kappa = cohen_kappa_score(y_test, y_pred)
        else:
            f1_macro = 0
            kappa = 0
        
        results.append({
            '모델': name,
            'Test Acc': f"{metrics['test_acc']*100:.1f}%",
            'F1 Macro': f"{f1_macro*100:.1f}%",
            'Kappa': f"{kappa:.3f}",
            '과적합률': f"{(metrics['train_acc'] - metrics['test_acc'])*100:.1f}%",
        })
    
    df = pd.DataFrame(results)
    df = df.sort_values('Test Acc', ascending=False)
    print(f"\n{df.to_string(index=False)}")
    
    # 최고 모델 하이라이트
    best = max(cv_results.items(), key=lambda x: x[1]['test_acc'])
    print(f"\n🏆 최고 Test 성능: {best[0]} ({best[1]['test_acc']*100:.1f}%)")
    
    # 시각화
    fig, ax = plt.subplots(figsize=(10, 6))
    model_names = [r['모델'] for r in results]
    test_accs = [float(r['Test Acc'].replace('%', '')) for r in results]
    f1_scores_val = [float(r['F1 Macro'].replace('%', '')) for r in results]
    
    x = np.arange(len(model_names))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, test_accs, width, label='Test Accuracy', color='#3498db')
    bars2 = ax.bar(x + width/2, f1_scores_val, width, label='F1 Macro', color='#2ecc71')
    
    ax.set_xlabel('모델', fontsize=12)
    ax.set_ylabel('점수 (%)', fontsize=12)
    ax.set_title('모델별 성능 비교', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(model_names, rotation=15, ha='right')
    ax.legend()
    ax.set_ylim(0, 100)
    
    # 값 표시
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
               f'{bar.get_height():.1f}', ha='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(SAVE_DIR / '2_model_comparison.png', dpi=150)
    plt.close()
    print(f"\n📊 그래프 저장: {SAVE_DIR / '2_model_comparison.png'}")


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
        
        # 시각화 (CatBoost만)
        if model_name == 'CatBoost':
            fig, ax = plt.subplots(figsize=(10, 8))
            colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(df)))
            bars = ax.barh(df['Feature'], df['Importance'], color=colors)
            ax.set_xlabel('중요도', fontsize=12)
            ax.set_title(f'{model_name} 피처 중요도', fontsize=14, fontweight='bold')
            ax.invert_yaxis()
            plt.tight_layout()
            plt.savefig(SAVE_DIR / '3_feature_importance.png', dpi=150)
            plt.close()
            print(f"\n📊 그래프 저장: {SAVE_DIR / '3_feature_importance.png'}")
        
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
        
        try:
            explainer = shap.TreeExplainer(cat_model)
            shap_values = explainer.shap_values(X_test)
            
            # 평균 절대 SHAP 값 계산
            shap_values = np.array(shap_values)
            
            # 다중 클래스 처리
            if shap_values.ndim == 3:
                # (n_classes, n_samples, n_features) -> (n_features,)
                mean_shap = np.abs(shap_values).mean(axis=0).mean(axis=0)
            elif shap_values.ndim == 2:
                mean_shap = np.abs(shap_values).mean(axis=0)
            else:
                raise ValueError("Unexpected SHAP shape")
            
            mean_shap = np.array(mean_shap).flatten()
            
            # 피처 수와 맞는지 확인
            if len(mean_shap) == len(feature_names):
                result_data = []
                for i, feat in enumerate(feature_names):
                    result_data.append({'Feature': feat, 'Mean |SHAP|': mean_shap[i]})
                
                df = pd.DataFrame(result_data)
                df = df.sort_values('Mean |SHAP|', ascending=False)
                df['Mean |SHAP|'] = df['Mean |SHAP|'].apply(lambda x: f"{x:.4f}")
                print(df.to_string(index=False))
            else:
                raise ValueError(f"Shape mismatch: {len(mean_shap)} vs {len(feature_names)}")
                
        except Exception as e:
            print(f"   ⚠️ SHAP 계산 실패: {e}")
            print("   → 피처 중요도 대체 사용")
            importance = cat_model.get_feature_importance()
            df = pd.DataFrame({'Feature': feature_names, 'Importance': importance})
            df = df.sort_values('Importance', ascending=False)
            df['Importance'] = df['Importance'].apply(lambda x: f"{x:.4f}")
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
    import seaborn as sns
    
    # CatBoost 혼동 행렬 시각화
    if 'CatBoost' in models:
        y_pred = models['CatBoost'].predict(X_test)
        cm = confusion_matrix(y_test, y_pred)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=['A', 'B', 'C'], yticklabels=['A', 'B', 'C'],
                   annot_kws={'size': 16})
        ax.set_xlabel('예측 등급', fontsize=12)
        ax.set_ylabel('실제 등급', fontsize=12)
        ax.set_title('CatBoost 혼동 행렬', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(SAVE_DIR / '4_confusion_matrix.png', dpi=150)
        plt.close()
        print(f"\n📊 그래프 저장: {SAVE_DIR / '4_confusion_matrix.png'}")
    
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
    print(f"\n📁 저장된 그래프 위치: {SAVE_DIR}")
    print("   - 1_target_distribution.png")
    print("   - 2_model_comparison.png")
    print("   - 3_feature_importance.png")
    print("   - 4_confusion_matrix.png")


if __name__ == "__main__":
    run_all_analysis()
