"""
_03_train.py
중개사 신뢰도 모델 - 학습 단계 (LogisticRegression)
이미 분할된 Train/Test 데이터 사용
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from pathlib import Path
import pickle
import warnings
warnings.filterwarnings('ignore')

# XGBoost와 LightGBM import (없으면 설치 필요)
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost가 설치되지 않았습니다. pip install xgboost")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("⚠️  LightGBM이 설치되지 않았습니다. pip install lightgbm")

# Docker 환경에서는 /data로 마운트됨
if Path("/data/ML/trust").exists():
    TRAIN_PATH = "/data/ML/trust/X_train.csv"
    TEST_PATH = "/data/ML/trust/X_test.csv"
    TRAIN_TARGET_PATH = "/data/ML/trust/y_train.csv"
    TEST_TARGET_PATH = "/data/ML/trust/y_test.csv"
    MODEL_DIR = Path("/data/ML/trust/models")
    MODEL_TEMP_PATH = "/data/ML/trust/temp_trained_models.pkl"
else:
    TRAIN_PATH = "data/ML/trust/X_train.csv"
    TEST_PATH = "data/ML/trust/X_test.csv"
    TRAIN_TARGET_PATH = "data/ML/trust/y_train.csv"
    TEST_TARGET_PATH = "data/ML/trust/y_test.csv"
    MODEL_DIR = Path("data/ML/trust/models")
    MODEL_TEMP_PATH = "data/ML/trust/temp_trained_models.pkl"


def load_processed_data():
    """이미 처리된 Train/Test 데이터 로드"""
    
    if not Path(TRAIN_PATH).exists():
        raise FileNotFoundError(f"[ERROR] Train 파일이 존재하지 않음: {TRAIN_PATH}")
    if not Path(TRAIN_TARGET_PATH).exists():
        raise FileNotFoundError(f"[ERROR] Train Target 파일이 존재하지 않음: {TRAIN_TARGET_PATH}")
    
    print(f"📂 [1단계] 처리된 데이터 로드")
    X_train = pd.read_csv(TRAIN_PATH, encoding="utf-8-sig")
    X_test = pd.read_csv(TEST_PATH, encoding="utf-8-sig")
    y_train = pd.read_csv(TRAIN_TARGET_PATH, encoding="utf-8-sig").squeeze()
    y_test = pd.read_csv(TEST_TARGET_PATH, encoding="utf-8-sig").squeeze()
    
    print(f"   - Train: {len(X_train):,}개")
    print(f"   - Test: {len(X_test):,}개")
    
    # Feature는 이미 _02_create_features.py에서 선택되어 있음
    # X_train, X_test는 그대로 사용

    
    print(f"\n📊 최종 Feature 수: {len(X_train.columns)}개")
    print(f"📋 사용된 Feature:")
    for i, feature in enumerate(X_train.columns, 1):
        print(f"   {i:2d}. {feature}")
    
    # 등급 분포 확인
    print(f"\n📊 Train 등급 분포:")
    train_dist = y_train.value_counts().sort_index()
    for grade, count in train_dist.items():
        print(f"   {grade}: {count}개 ({count/len(y_train)*100:.1f}%)")
    
    print(f"\n📊 Test 등급 분포:")
    test_dist = y_test.value_counts().sort_index()
    for grade, count in test_dist.items():
        print(f"   {grade}: {count}개 ({count/len(y_test)*100:.1f}%)")
    
    return X_train, X_test, y_train, y_test


def tune_logistic_regression(X_train_scaled, y_train):
    """
    LogisticRegression 하이퍼파라미터 튜닝 (GridSearchCV)
    
    탐색 파라미터:
    - C: 정규화 강도 (작을수록 강한 정규화)
    - penalty: L1, L2 정규화
    - solver: 최적화 알고리즘
    """
    print("\n🔍 LogisticRegression 하이퍼파라미터 튜닝 시작...")
    print("   - GridSearchCV (5-Fold Cross Validation)")
    
    # 파라미터 그리드 정의
    param_grid = {
        'C': [0.01, 0.1, 1, 10, 100],  # 정규화 강도
        'penalty': ['l1', 'l2'],  # 정규화 타입
        'solver': ['saga'],  # L1/L2 모두 지원하는 solver
        'max_iter': [1000],
        'class_weight': ['balanced'],
        'random_state': [42]
    }
    
    # GridSearchCV 설정
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    grid_search = GridSearchCV(
        LogisticRegression(),
        param_grid,
        cv=cv,
        scoring='accuracy',
        n_jobs=-1,
        verbose=1
    )
    
    # 튜닝 실행
    print(f"\n   탐색 조합 수: {len(param_grid['C']) * len(param_grid['penalty'])} = {len(param_grid['C']) * len(param_grid['penalty'])}개")
    grid_search.fit(X_train_scaled, y_train)
    
    # 결과 출력
    print(f"\n✅ 튜닝 완료!")
    print(f"   최적 파라미터: {grid_search.best_params_}")
    print(f"   최적 CV Score: {grid_search.best_score_:.4f}")
    
    # 상위 5개 결과 출력
    results_df = pd.DataFrame(grid_search.cv_results_)
    results_df = results_df.sort_values('rank_test_score')
    
    print(f"\n📊 상위 5개 파라미터 조합:")
    for idx, row in results_df.head(5).iterrows():
        print(f"   {row['rank_test_score']}위: C={row['param_C']}, penalty={row['param_penalty']} "
              f"→ CV={row['mean_test_score']:.4f} (±{row['std_test_score']:.4f})")
    
    return grid_search.best_estimator_, grid_search.best_params_


def train_models(X_train_scaled, y_train, X_test_scaled, y_test):

    """
    4개 모델 학습 및 비교 (기본 하이퍼파라미터 사용)
    - LogisticRegression
    - RandomForest
    - XGBoost
    - LightGBM
    
    공정한 비교를 위해 모든 모델에 기본값 사용
    (class_weight='balanced'만 공통 적용)
    """
    print("\n🤖 모델 학습 시작 (기본 하이퍼파라미터 사용)...")
    
    models = {}
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # 1) LogisticRegression (기본값)
    print("\n[1/4] LogisticRegression 학습 중...")
    print("   - 기본 하이퍼파라미터 + class_weight=balanced")
    lr_model = LogisticRegression(
        class_weight='balanced',
        random_state=42,
        max_iter=1000  # 수렴을 위해 필요
    )
    lr_model.fit(X_train_scaled, y_train)
    lr_scores = cross_val_score(lr_model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
    models["LogisticRegression"] = lr_model
    print(f"   ✓ CV Score: {lr_scores.mean():.4f} (±{lr_scores.std():.4f})")
    
    # 2) RandomForest (기본값)
    print("\n[2/4] RandomForest 학습 중...")
    print("   - 기본 하이퍼파라미터 + class_weight=balanced")
    rf_model = RandomForestClassifier(
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train_scaled, y_train)
    rf_scores = cross_val_score(rf_model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
    models["RandomForest"] = rf_model
    print(f"   ✓ CV Score: {rf_scores.mean():.4f} (±{rf_scores.std():.4f})")
    
    # 3) XGBoost (기본값)
    if XGBOOST_AVAILABLE:
        print("\n[3/4] XGBoost 학습 중...")
        print("   - 기본 하이퍼파라미터")
        # XGBoost는 class_weight 대신 scale_pos_weight 사용
        # 클래스 비율 계산
        from collections import Counter
        class_counts = Counter(y_train)
        scale_pos_weight = class_counts[0] / class_counts[1] if len(class_counts) > 1 else 1.0
        
        xgb_model = xgb.XGBClassifier(
            random_state=42,
            n_jobs=-1,
            eval_metric='mlogloss'
        )
        xgb_model.fit(X_train_scaled, y_train)
        xgb_scores = cross_val_score(xgb_model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
        models["XGBoost"] = xgb_model
        print(f"   ✓ CV Score: {xgb_scores.mean():.4f} (±{xgb_scores.std():.4f})")
    else:
        print("\n[3/4] XGBoost 건너뛰기 (설치 필요)")
    
    # 4) LightGBM (기본값)
    if LIGHTGBM_AVAILABLE:
        print("\n[4/4] LightGBM 학습 중...")
        print("   - 기본 하이퍼파라미터 + class_weight=balanced")
        lgb_model = lgb.LGBMClassifier(
            class_weight='balanced',
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        lgb_model.fit(X_train_scaled, y_train)
        lgb_scores = cross_val_score(lgb_model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
        models["LightGBM"] = lgb_model
        print(f"   ✓ CV Score: {lgb_scores.mean():.4f} (±{lgb_scores.std():.4f})")
    else:
        print("\n[4/4] LightGBM 건너뛰기 (설치 필요)")
    
    print(f"\n✅ 모델 학습 완료! (총 {len(models)}개 모델)")
    return models


def main():
    print("=" * 70)
    print(" " * 20 + "모델 학습")
    print("=" * 70)

    # 1) 이미 분할된 데이터 로드
    X_train, X_test, y_train, y_test = load_processed_data()
    
    # 2) 스케일링 (Train 기준으로 fit, Test에 transform)
    print("\n🔍 [2단계] 데이터 스케일링")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print("   ✅ StandardScaler 적용 완료 (Train 기준)")
    
    # 총거래활동량_log 피처의 가중치를 0.5배로 축소
    feature_names = X_train.columns.tolist()
    if "총거래활동량_log" in feature_names:
        feature_idx = feature_names.index("총거래활동량_log")
        X_train_scaled[:, feature_idx] *= 0.5
        X_test_scaled[:, feature_idx] *= 0.5
        print("   ✅ 총거래활동량_log 가중치 0.5배로 축소")
    
    
    # 3) LogisticRegression 하이퍼파라미터 튜닝
    best_lr_model, best_params = tune_logistic_regression(X_train_scaled, y_train)
    
    # 4) 기본값 모델들과 비교를 위해 모든 모델 학습
    models = train_models(X_train_scaled, y_train, X_test_scaled, y_test)
    
    # 5) 튜닝된 LogisticRegression을 모델 딕셔너리에 추가
    models["LogisticRegression_Tuned"] = best_lr_model
    print(f"\n✅ 튜닝된 LogisticRegression 추가 완료!")
    print(f"   최적 파라미터: {best_params}")

    
    # 4) Test 세트 평가
    print("\n" + "=" * 70)
    print(" " * 20 + "모델 성능 평가")
    print("=" * 70)
    
    cv_results = {}
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    for name, model in models.items():
        # Train/Test 예측
        train_pred = model.predict(X_train_scaled)
        test_pred = model.predict(X_test_scaled)
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        
        # CV 점수
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
        
        cv_results[name] = {
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'train_acc': train_acc,
            'test_acc': test_acc
        }
        
        print(f"\n  {name}:")
        print(f"    - Train Accuracy: {train_acc:.4f}")
        print(f"    - Test Accuracy:  {test_acc:.4f}")
        print(f"    - 과적합 정도:     {train_acc - test_acc:.4f}")
        print(f"    - CV Mean:        {cv_scores.mean():.4f} (±{cv_scores.std():.4f})")
    
    # 5) 모델 + 스케일러 저장
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_TEMP_PATH, "wb") as f:
        pickle.dump(
            {
                "models": models,
                "scaler": scaler,
                "X_train_scaled": X_train_scaled,
                "y_train": y_train,
                "X_test_scaled": X_test_scaled,
                "y_test": y_test,
                "feature_names": list(X_train.columns),
                "cv_results": cv_results,
            },
            f,
        )
    
    print(f"\n✓ Temp 모델 저장: {MODEL_TEMP_PATH}")
    
    print("\n" + "=" * 70)
    print(" " * 25 + "완료!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
