"""
중개사 신뢰도 다중분류 모델 - 앙상블 학습
- 모델: LightGBM, XGBoost, RandomForest
- 최적화: RandomizedSearchCV → 정규화 파라미터 적용
- SHAP 분석 포함
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold, RandomizedSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix, 
    accuracy_score, f1_score, precision_score, recall_score, 
    roc_auc_score, log_loss
)
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
import warnings
warnings.filterwarnings("ignore")

# 모듈 임포트
from _00_load_data import load_processed_office_data as load_data
import _01_targer_engineering as target_engineering
from _02_feature_engineering import main as feature_engineering


def prepare_data(filepath=None):
    """데이터 준비: 로드 → 타겟 생성 → 피처 생성"""
    print("=" * 70)
    print("🏠 중개사 신뢰도 모델 - 앙상블 분류 파이프라인")
    print("=" * 70)
    
    if filepath:
        raw_df = load_data(filepath)
    else:
        raw_df = load_data()
    df_with_target = target_engineering.main(raw_df)
    df_final, X, feature_names = feature_engineering(df_with_target)
    y = df_final["신뢰등급"].astype(int)
    
    print(f"\n✅ 데이터 준비 완료: X={X.shape}, y={y.shape}")
    print(f"   등급 분포: {dict(y.value_counts().sort_index())}")
    
    return X, y, feature_names


def train_lightgbm(X_train, y_train, cv):
    """LightGBM 학습 (정규화 파라미터 포함)"""
    from lightgbm import LGBMClassifier
    
    print("\n🌲 [LightGBM] 하이퍼파라미터 탐색 중...")
    
    param_dist = {
        "num_leaves": [15, 31, 50, 80],
        "max_depth": [3, 4, 5, 6],
        "learning_rate": [0.01, 0.03, 0.05],
        "n_estimators": [200, 300, 500],
        "min_child_samples": [30, 50, 80],
        "subsample": [0.6, 0.7, 0.8],
        "colsample_bytree": [0.5, 0.6, 0.7],
        "reg_alpha": [0.0, 0.1, 0.5, 1.0],     # L1 정규화
        "reg_lambda": [0.0, 1.0, 5.0, 10.0],   # L2 정규화
    }
    
    model = LGBMClassifier(
        objective="multiclass",
        num_class=3,
        class_weight="balanced",
        random_state=42,
        verbose=-1
    )
    
    search = RandomizedSearchCV(
        model, param_dist, n_iter=30, cv=cv, scoring="f1_macro",
        n_jobs=-1, random_state=42, verbose=0
    )
    search.fit(X_train, y_train)
    
    print(f"   Best F1: {search.best_score_:.4f}")
    return search.best_estimator_, search.best_params_, search.best_score_


def train_xgboost(X_train, y_train, cv):
    """XGBoost 학습 (정규화 파라미터 포함)"""
    try:
        from xgboost import XGBClassifier
    except ImportError:
        print("   ⚠️ XGBoost 미설치. 건너뜀.")
        return None, None, 0
    
    print("\n🚀 [XGBoost] 하이퍼파라미터 탐색 중...")
    
    param_dist = {
        "max_depth": [3, 4, 5, 6],
        "learning_rate": [0.01, 0.03, 0.05],
        "n_estimators": [200, 300, 500],
        "min_child_weight": [3, 5, 7],
        "subsample": [0.6, 0.7, 0.8],
        "colsample_bytree": [0.5, 0.6, 0.7],
        "reg_alpha": [0.0, 0.1, 0.5, 1.0],     # L1 정규화
        "reg_lambda": [1.0, 5.0, 10.0],        # L2 정규화
    }
    
    model = XGBClassifier(
        objective="multi:softmax",
        num_class=3,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=42,
        verbosity=0
    )
    
    search = RandomizedSearchCV(
        model, param_dist, n_iter=30, cv=cv, scoring="f1_macro",
        n_jobs=-1, random_state=42, verbose=0
    )
    search.fit(X_train, y_train)
    
    print(f"   Best F1: {search.best_score_:.4f}")
    return search.best_estimator_, search.best_params_, search.best_score_


def train_random_forest(X_train, y_train, cv):
    """RandomForest 학습"""
    print("\n🌳 [RandomForest] 하이퍼파라미터 탐색 중...")
    
    param_dist = {
        "n_estimators": [100, 200, 300],
        "max_depth": [3, 5, 7, 10],
        "min_samples_split": [5, 10, 20],
        "min_samples_leaf": [3, 5, 10],
        "max_features": ["sqrt", "log2", 0.5],
    }
    
    model = RandomForestClassifier(
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    
    search = RandomizedSearchCV(
        model, param_dist, n_iter=30, cv=cv, scoring="f1_macro",
        n_jobs=-1, random_state=42, verbose=0
    )
    search.fit(X_train, y_train)
    
    print(f"   Best F1: {search.best_score_:.4f}")
    return search.best_estimator_, search.best_params_, search.best_score_


def train_catboost(X_train, y_train, cv):
    """CatBoost 학습"""
    try:
        from catboost import CatBoostClassifier
    except ImportError:
        print("\n🐱 [CatBoost] ⚠️ 미설치. 건너뜀. (pip install catboost)")
        return None, None, 0
    
    print("\n🐱 [CatBoost] 하이퍼파라미터 탐색 중...")
    
    param_dist = {
        "depth": [3, 4, 5, 6],
        "learning_rate": [0.01, 0.03, 0.05],
        "iterations": [200, 300, 500],
        "l2_leaf_reg": [1.0, 3.0, 5.0, 10.0],   # L2 정규화
        "border_count": [32, 64, 128],
    }
    
    model = CatBoostClassifier(
        loss_function="MultiClass",
        auto_class_weights="Balanced",
        random_state=42,
        verbose=False
    )
    
    search = RandomizedSearchCV(
        model, param_dist, n_iter=30, cv=cv, scoring="f1_macro",
        n_jobs=-1, random_state=42, verbose=0
    )
    search.fit(X_train, y_train)
    
    print(f"   Best F1: {search.best_score_:.4f}")
    return search.best_estimator_, search.best_params_, search.best_score_


def train_svm(X_train, y_train, cv):
    """SVM 학습"""
    from sklearn.svm import SVC
    
    print("\n🎯 [SVM] 하이퍼파라미터 탐색 중...")
    
    param_dist = {
        "C": [0.1, 1.0, 10.0, 100.0],
        "gamma": ["scale", "auto", 0.01, 0.1],
        "kernel": ["rbf", "poly"],
        "degree": [2, 3],  # poly 커널용
    }
    
    model = SVC(
        class_weight="balanced",
        probability=True,  # Soft voting을 위해 필요
        random_state=42
    )
    
    search = RandomizedSearchCV(
        model, param_dist, n_iter=20, cv=cv, scoring="f1_macro",
        n_jobs=-1, random_state=42, verbose=0
    )
    search.fit(X_train, y_train)
    
    print(f"   Best F1: {search.best_score_:.4f}")
    return search.best_estimator_, search.best_params_, search.best_score_


def train_ensemble(models_dict, X_train, y_train, X_test, y_test, cv):
    """앙상블 모델 (Voting Classifier)"""
    print("\n" + "=" * 70)
    print("🏆 앙상블 모델 (Voting Classifier)")
    print("=" * 70)
    
    # 유효한 모델만 선택
    estimators = [(name, model) for name, model in models_dict.items() if model is not None]
    
    if len(estimators) < 2:
        print("   ⚠️ 앙상블에 필요한 모델 부족 (최소 2개)")
        return None
    
    # Soft Voting (확률 기반)
    ensemble = VotingClassifier(estimators=estimators, voting='soft')
    ensemble.fit(X_train, y_train)
    
    # 성능 평가
    # 성능 평가
    y_train_pred = ensemble.predict(X_train)
    y_test_pred = ensemble.predict(X_test)
    y_test_proba = ensemble.predict_proba(X_test)
    
    train_f1 = f1_score(y_train, y_train_pred, average='macro')
    
    test_acc = accuracy_score(y_test, y_test_pred)
    test_f1 = f1_score(y_test, y_test_pred, average='macro')
    test_prec = precision_score(y_test, y_test_pred, average='macro')
    test_rec = recall_score(y_test, y_test_pred, average='macro')
    test_auc = roc_auc_score(y_test, y_test_proba, multi_class='ovr')
    test_logloss = log_loss(y_test, y_test_proba)
    
    print(f"\n📊 앙상블 성능 상세:")
    print(f"   Train F1 : {train_f1:.4f}")
    print(f"   Test F1  : {test_f1:.4f}  | Acc  : {test_acc:.4f}")
    print(f"   Prec     : {test_prec:.4f}  | Rec  : {test_rec:.4f}")
    print(f"   ROC AUC  : {test_auc:.4f}  | Loss : {test_logloss:.4f}")
    
    # Classification Report
    class_names = ["하위", "중위", "상위"]
    print(f"\n📋 Classification Report:")
    print(classification_report(y_test, y_test_pred, target_names=class_names))
    
    # Confusion Matrix
    print(f"🔢 Confusion Matrix:")
    print(confusion_matrix(y_test, y_test_pred))
    
    return ensemble, test_f1


def analyze_shap(model, X_test, feature_names, output_dir="apps/reco/models/trust_model/saved_models"):
    """SHAP 분석"""
    print("\n" + "=" * 70)
    print("🔍 SHAP 분석")
    print("=" * 70)
    
    try:
        import shap
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        X_test_df = pd.DataFrame(X_test, columns=feature_names)
        
        print("   📊 SHAP 값 계산 중...")
        explainer = shap.TreeExplainer(model)
        shap_values = explainer(X_test_df)
        
        # Summary Plot (클래스별)
        class_names = ["하위", "중위", "상위"]
        for i, name in enumerate(class_names):
            plt.figure(figsize=(10, 8))
            shap.summary_plot(shap_values[:, :, i], X_test_df, show=False, max_display=15)
            plt.title(f"SHAP - {name} 등급")
            plt.tight_layout()
            plt.savefig(output_path / f"shap_{name}.png", dpi=150)
            plt.close()
            print(f"      ✅ 저장: shap_{name}.png")
        
        # Feature Importance Bar
        mean_shap = np.abs(shap_values.values).mean(axis=0).mean(axis=1)
        sorted_idx = np.argsort(mean_shap)[::-1]
        
        plt.figure(figsize=(10, 8))
        top_n = min(15, len(feature_names))
        plt.barh(range(top_n), mean_shap[sorted_idx[:top_n]][::-1], color='steelblue')
        plt.yticks(range(top_n), [feature_names[i] for i in sorted_idx[:top_n]][::-1])
        plt.xlabel('Mean |SHAP Value|')
        plt.title('SHAP Feature Importance')
        plt.tight_layout()
        plt.savefig(output_path / "shap_importance.png", dpi=150)
        plt.close()
        print(f"      ✅ 저장: shap_importance.png")
        
        print("\n   📋 SHAP Top 10 피처:")
        for rank, idx in enumerate(sorted_idx[:10], 1):
            print(f"      {rank:2d}. {feature_names[idx]:<12}: {mean_shap[idx]:.4f}")
        
    except Exception as e:
        print(f"   ❌ SHAP 오류: {e}")


def save_models(best_model, models_dict, scaler, feature_names, output_dir="apps/reco/models/trust_model/saved_models"):
    """모델 저장"""
    print("\n💾 모델 저장 중...")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    with open(output_path / "trust_model.pkl", "wb") as f:
        pickle.dump(best_model, f)
    with open(output_path / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    with open(output_path / "feature_names.pkl", "wb") as f:
        pickle.dump(feature_names, f)
    with open(output_path / "all_models.pkl", "wb") as f:
        pickle.dump(models_dict, f)
    
    print(f"   ✅ 저장 완료: {output_path}")


def main():
    """메인 실행"""
    # 1. 데이터 준비
    X, y, feature_names = prepare_data()
    
    # 2. Train/Test 분리
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n📊 데이터 분리: Train {len(X_train)} / Test {len(X_test)}")
    
    # 3. 스케일링
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 4. CV 설정
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # 5. 개별 모델 학습
    print("\n" + "=" * 70)
    print("🎯 개별 모델 학습")
    print("=" * 70)
    
    lgb_model, lgb_params, lgb_score = train_lightgbm(X_train_scaled, y_train, cv)
    xgb_model, xgb_params, xgb_score = train_xgboost(X_train_scaled, y_train, cv)
    rf_model, rf_params, rf_score = train_random_forest(X_train_scaled, y_train, cv)
    cat_model, cat_params, cat_score = train_catboost(X_train_scaled, y_train, cv)
    svm_model, svm_params, svm_score = train_svm(X_train_scaled, y_train, cv)
    
    # 6. 모델 비교
    print("\n" + "=" * 70)
    print("📊 모델 성능 비교")
    print("=" * 70)
    
    results = []
    if lgb_model:
        results.append(("LightGBM", lgb_model, lgb_score))
    if xgb_model:
        results.append(("XGBoost", xgb_model, xgb_score))
    if rf_model:
        results.append(("RandomForest", rf_model, rf_score))
    if cat_model:
        results.append(("CatBoost", cat_model, cat_score))
    if svm_model:
        results.append(("SVM", svm_model, svm_score))
    
    print(f"\n   {'Model':<12} | {'CV F1':<7} | {'Test F1':<7} | {'Acc':<6} | {'Prec':<6} | {'Rec':<6} | {'AUC':<6}")
    print("   " + "-" * 75)
    
    for name, model, score in sorted(results, key=lambda x: x[2], reverse=True):
        test_pred = model.predict(X_test_scaled)
        
        # 확률 계산 (가능한 경우)
        if hasattr(model, "predict_proba"):
            test_proba = model.predict_proba(X_test_scaled)
            auc = roc_auc_score(y_test, test_proba, multi_class='ovr')
        else:
            auc = 0.0
            
        test_f1 = f1_score(y_test, test_pred, average='macro')
        acc = accuracy_score(y_test, test_pred)
        prec = precision_score(y_test, test_pred, average='macro')
        rec = recall_score(y_test, test_pred, average='macro')
        
        print(f"   {name:<12} | {score:.4f}  | {test_f1:.4f}  | {acc:.4f} | {prec:.4f} | {rec:.4f} | {auc:.4f}")
    
    # 7. 최고 모델 선택
    best_name, best_model, best_cv_score = max(results, key=lambda x: x[2])
    print(f"\n   🏆 최고 모델: {best_name} (CV F1={best_cv_score:.4f})")
    
    # 8. 앙상블 모델
    models_dict = {"lgb": lgb_model, "xgb": xgb_model, "rf": rf_model, "cat": cat_model, "svm": svm_model}
    ensemble, ensemble_f1 = train_ensemble(
        {k: v for k, v in models_dict.items() if v is not None},
        X_train_scaled, y_train, X_test_scaled, y_test, cv
    )
    
    # 9. 최종 모델 결정 (앙상블 vs 개별 최고)
    if ensemble and ensemble_f1 > f1_score(y_test, best_model.predict(X_test_scaled), average='macro'):
        final_model = ensemble
        print(f"\n   🎉 최종 선택: Ensemble (F1={ensemble_f1:.4f})")
    else:
        final_model = best_model
        print(f"\n   🎉 최종 선택: {best_name}")
    
    # 10. SHAP 분석 (개별 최고 모델로)
    analyze_shap(best_model, X_test_scaled, feature_names)
    
    # 11. 모델 저장
    save_models(final_model, models_dict, scaler, feature_names)
    
    print("\n" + "=" * 70)
    print("✅ 앙상블 학습 완료!")
    print("=" * 70)
    
    return final_model, scaler, feature_names


if __name__ == "__main__":
    main()
