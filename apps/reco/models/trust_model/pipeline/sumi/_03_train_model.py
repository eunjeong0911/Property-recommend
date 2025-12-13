"""
중개사 신뢰도 다중분류 모델 학습 파이프라인
- 타겟: 신뢰등급 (0=C, 1=B, 2=A, 3=S)
- 최적화: RandomizedSearchCV → Optuna → 최종 재학습
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold, RandomizedSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score, f1_score
)
import warnings
warnings.filterwarnings("ignore")

# 데이터 로드 및 피처/타겟 엔지니어링 모듈 import
from _00_load_data import load_processed_office_data as load_data
import _01_targer_engineering as target_engineering
from _02_feature_engineering import main as feature_engineering


def prepare_data():
    """데이터 준비: 로드 → 타겟 생성 → 피처 생성"""
    print("=" * 70)
    print("🏠 중개사 신뢰도 모델 - 분류 학습 파이프라인")
    print("=" * 70)
    
    # 1. 데이터 로드
    raw_df = load_data()
    
    # 2. 타겟 생성 (베이지안_성사율 + 신뢰등급)
    df_with_target = target_engineering.main(raw_df)
    
    # 3. 피처 생성 (X)
    df_final, X, feature_names = feature_engineering(df_with_target)
    
    # 4. 타겟 추출 (y = 신뢰등급)
    y = df_final["신뢰등급"].astype(int)
    
    print(f"\n✅ 데이터 준비 완료")
    print(f"   - Feature(X): {X.shape}")
    print(f"   - Target(y): {y.shape}")
    print(f"   - 등급 분포:\n{y.value_counts().sort_index()}")
    
    return X, y, feature_names


def run_randomized_search(X_train, y_train, cv):
    """1단계: RandomizedSearchCV로 거친 영역 탐색"""
    print("\n" + "=" * 70)
    print("🔍 [1단계] RandomizedSearchCV - 거친 영역 탐색")
    print("=" * 70)
    
    try:
        from lightgbm import LGBMClassifier
        
        param_dist = {
            "num_leaves": [15, 31, 63, 127],
            "max_depth": [-1, 5, 7, 9],
            "learning_rate": [0.01, 0.03, 0.05, 0.1],
            "n_estimators": [300, 500, 800],
            "min_child_samples": [10, 20, 40],
            "subsample": [0.7, 0.8, 0.9],
            "colsample_bytree": [0.7, 0.8, 0.9],
        }
        
        model = LGBMClassifier(
            objective="multiclass",
            num_class=3,  # 하/중/상
            class_weight="balanced",
            random_state=42,
            verbose=-1
        )
        
        search = RandomizedSearchCV(
            model,
            param_distributions=param_dist,
            n_iter=30,  # 탐색 횟수
            scoring="f1_macro",
            cv=cv,
            n_jobs=-1,
            verbose=1,
            random_state=42
        )
        
        search.fit(X_train, y_train)
        
        print(f"\n✅ RandomSearch 완료!")
        print(f"   Best F1 Macro: {search.best_score_:.4f}")
        print(f"   Best Params: {search.best_params_}")
        
        return search.best_params_, search.best_score_
        
    except ImportError:
        print("⚠️ LightGBM 미설치. pip install lightgbm")
        return None, 0


def run_optuna_search(X_train, y_train, cv, initial_params):
    """2단계: Optuna로 정밀 탐색 (RandomSearch 결과 기반)"""
    print("\n" + "=" * 70)
    print("🎯 [2단계] Optuna - 정밀 탐색")
    print("=" * 70)
    
    try:
        import optuna
        from lightgbm import LGBMClassifier
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        
        # RandomSearch 결과를 기반으로 탐색 범위 설정
        base_leaves = initial_params.get("num_leaves", 31) if initial_params else 31
        base_depth = initial_params.get("max_depth", 7) if initial_params else 7
        # max_depth가 -1이면 기본값 7로 대체
        if base_depth == -1:
            base_depth = 7
        base_lr = initial_params.get("learning_rate", 0.05) if initial_params else 0.05
        
        def objective(trial):
            params = {
                "num_leaves": trial.suggest_int("num_leaves", max(10, base_leaves-20), min(150, base_leaves+30)),
                "max_depth": trial.suggest_int("max_depth", max(3, base_depth-2), max(base_depth+3, 8)),  # 최소 8 보장
                "learning_rate": trial.suggest_float("learning_rate", max(0.005, base_lr*0.5), min(0.2, base_lr*2)),
                "n_estimators": trial.suggest_int("n_estimators", 300, 1000),
                "min_child_samples": trial.suggest_int("min_child_samples", 5, 50),
                "subsample": trial.suggest_float("subsample", 0.6, 0.95),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 0.95),
            }
            
            model = LGBMClassifier(
                objective="multiclass",
                num_class=3,  # 하/중/상
                class_weight="balanced",
                random_state=42,
                verbose=-1,
                **params
            )
            
            score = cross_val_score(
                model, X_train, y_train, cv=cv, scoring="f1_macro", n_jobs=-1
            ).mean()
            
            return score
        
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=50, show_progress_bar=True)
        
        print(f"\n✅ Optuna 완료!")
        print(f"   Best F1 Macro: {study.best_value:.4f}")
        print(f"   Best Params: {study.best_params}")
        
        return study.best_params, study.best_value
        
    except ImportError:
        print("⚠️ Optuna 또는 LightGBM 미설치.")
        print("   pip install optuna lightgbm")
        return initial_params, 0


def train_final_model(X_train, X_test, y_train, y_test, best_params, cv):
    """3단계: 최종 모델 학습 및 평가"""
    print("\n" + "=" * 70)
    print("🏆 [3단계] 최종 모델 학습")
    print("=" * 70)
    
    from lightgbm import LGBMClassifier
    
    model = LGBMClassifier(
        objective="multiclass",
        num_class=3,  # 하/중/상
        class_weight="balanced",
        random_state=42,
        verbose=-1,
        **best_params
    )
    
    # 전체 Train 데이터로 학습
    model.fit(X_train, y_train)
    
    # Train/Test 예측
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # 평가 지표
    train_f1 = f1_score(y_train, y_train_pred, average="macro")
    test_f1 = f1_score(y_test, y_test_pred, average="macro")
    train_acc = accuracy_score(y_train, y_train_pred)
    test_acc = accuracy_score(y_test, y_test_pred)
    
    # CV Score
    cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="f1_macro")
    
    print(f"\n📊 성능 비교:")
    print(f"   Train F1 Macro: {train_f1:.4f} / Test F1 Macro: {test_f1:.4f}")
    print(f"   Train Accuracy: {train_acc:.4f} / Test Accuracy: {test_acc:.4f}")
    print(f"   CV F1 Macro: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    
    # 과적합 체크
    if train_f1 - test_f1 > 0.1:
        print(f"   ⚠️ 과적합 의심 (Train-Test F1 차이: {train_f1-test_f1:.4f})")
    else:
        print(f"   ✅ 과적합 없음")
    
    # Classification Report
    class_names = ["하위(Bottom)", "중위(Middle)", "상위(Top)"]
    print(f"\n� Classification Report:")
    print(classification_report(y_test, y_test_pred, target_names=class_names))
    
    # Confusion Matrix
    print(f"🔢 Confusion Matrix:")
    print(confusion_matrix(y_test, y_test_pred))
    
    # Feature Importance
    if hasattr(model, "feature_importances_"):
        print(f"\n🔍 피처 중요도 (Top 10):")
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]
        for i in range(min(10, len(indices))):
            print(f"      {i+1}. Feature_{indices[i]}: {importances[indices[i]]:.4f}")
    
    return model, {"train_f1": train_f1, "test_f1": test_f1, "train_acc": train_acc, "test_acc": test_acc}


def save_model(model, scaler, feature_names, best_params, output_dir="apps/reco/models/trust_model/saved_models"):
    """모델 저장"""
    print("\n💾 모델 저장")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    with open(output_path / "trust_model.pkl", "wb") as f:
        pickle.dump(model, f)
    with open(output_path / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    with open(output_path / "feature_names.pkl", "wb") as f:
        pickle.dump(feature_names, f)
    with open(output_path / "best_params.pkl", "wb") as f:
        pickle.dump(best_params, f)
    
    print(f"   ✅ 저장 완료: {output_path}")


def main():
    """메인 실행 함수"""
    # 1. 데이터 준비
    X, y, feature_names = prepare_data()
    
    # 2. Train/Test 분리 (Stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n📊 데이터 분리: Train {len(X_train)}개 / Test {len(X_test)}개")
    
    # 3. 스케일링
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 4. Cross-Validation 설정
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # 5. [1단계] RandomizedSearchCV
    random_params, random_score = run_randomized_search(X_train_scaled, y_train, cv)
    
    # 6. [2단계] Optuna 정밀 탐색
    best_params, best_score = run_optuna_search(X_train_scaled, y_train, cv, random_params)
    
    # 7. [3단계] 최종 모델 학습
    final_model, results = train_final_model(
        X_train_scaled, X_test_scaled, y_train, y_test, best_params, cv
    )
    
    # 8. 모델 저장
    save_model(final_model, scaler, list(X.columns), best_params)
    
    print("\n" + "=" * 70)
    print("✅ 분류 모델 학습 완료!")
    print("=" * 70)
    
    return final_model, scaler, best_params, results


if __name__ == "__main__":
    main()
