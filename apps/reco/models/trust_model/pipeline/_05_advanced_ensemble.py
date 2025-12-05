import os
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, classification_report
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import (
    RandomForestRegressor, 
    GradientBoostingRegressor, 
    ExtraTreesRegressor,
    VotingRegressor,
    StackingRegressor
)
from sklearn.linear_model import Ridge, Lasso
from sklearn.svm import SVR

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")


def get_feature_list():
    """
    사용할 피처 리스트 반환
    
    총 16개 피처:
    - 원본 (5개)
    - 기본 파생 (2개)
    - 지역 (3개)
    - 고급 파생 (6개)
    """
    return [
        # 원본 데이터
        "거래완료", "등록매물", "총매물수",
        "영업일수", "보증보험유효",
        # 기본 파생
        "등록비율", "규모지수",
        # 지역 피처
        "지역내백분위", "지역중개사수", "지역권평균거래",
        # 고급 파생
        "거래효율성", "매물활용도", "지역경쟁력", "상대적성과",
        # 로그 변환
        "log_거래완료", "log_총매물수"
    ]


def create_base_models():
    """
    5개의 Base 모델 생성
    
    Returns:
        list: (name, model) 튜플 리스트
    """
    models = [
        ('rf', RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1
        )),
        ('gb', GradientBoostingRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42
        )),
        ('et', ExtraTreesRegressor(
            n_estimators=200,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1
        )),
        ('ridge', Ridge(
            alpha=0.5,
            random_state=42
        )),
        ('lasso', Lasso(
            alpha=0.5,
            random_state=42,
            max_iter=10000
        ))
    ]
    return models


def evaluate_individual_models(models, X_train, X_test, y_train, y_test):
    """
    개별 모델 성능 평가
    
    Args:
        models: 모델 리스트
        X_train, X_test: 학습/테스트 데이터
        y_train, y_test: 학습/테스트 타겟
    """
    print(f"\n📊 개별 모델 성능 (Test Set):")
    
    model_names = {
        'rf': 'RandomForest',
        'gb': 'GradientBoosting',
        'et': 'ExtraTrees',
        'ridge': 'Ridge',
        'lasso': 'Lasso'
    }
    
    for name, model in models:
        model.fit(X_train, y_train)
        
        test_pred = model.predict(X_test)
        test_r2 = r2_score(y_test, test_pred)
        
        train_pred = model.predict(X_train)
        train_r2 = r2_score(y_train, train_pred)
        
        gap = train_r2 - test_r2
        
        display_name = model_names.get(name, name)
        print(f"   {display_name:20s} | Test R²: {test_r2:.3f} | Train R²: {train_r2:.3f} | Gap: {gap:.3f}")


def calculate_grade_accuracy(df, train_indices, test_indices, target):
    """
    등급 정확도 계산
    
    Args:
        df: 전체 데이터프레임
        train_indices: 학습 데이터 인덱스
        test_indices: 테스트 데이터 인덱스
        target: 타겟 컬럼명
        
    Returns:
        tuple: (train_accuracy, test_accuracy, accuracy_gap)
    """
    # 실제 타겟으로 등급 생성
    df["actual_grade"] = pd.qcut(
        df[target],
        q=5,
        labels=["D", "C", "B", "A", "S"],
        duplicates='drop'
    )
    
    # 예측 점수로 등급 생성
    df["final_temperature"] = (
        (df["predicted_score"] - df["predicted_score"].min()) / 
        (df["predicted_score"].max() - df["predicted_score"].min())
    )
    
    df["final_grade"] = pd.qcut(
        df["final_temperature"],
        q=5,
        labels=["D", "C", "B", "A", "S"],
        duplicates='drop'
    )
    
    # 정확도 계산
    train_actual = df.loc[train_indices, "actual_grade"]
    train_predicted = df.loc[train_indices, "final_grade"]
    test_actual = df.loc[test_indices, "actual_grade"]
    test_predicted = df.loc[test_indices, "final_grade"]
    
    train_acc = accuracy_score(train_actual, train_predicted)
    test_acc = accuracy_score(test_actual, test_predicted)
    acc_gap = train_acc - test_acc
    
    return train_acc, test_acc, acc_gap, test_actual, test_predicted


def train_advanced_ensemble(df):
    """
    앙상블: Stacking 방식으로 5개 모델 결합
    
    목표: Accuracy 80% 이상
    
    전략:
    1. 16개 피처 사용 (이미 생성됨)
    2. 5개 Base 모델 (RF, GB, ET, Ridge, Lasso)
    3. Stacking 앙상블 (Meta Model: Ridge)
    4. 교차 검증으로 안정성 확인
    """
    print("\n🤖 [4단계] 앙상블 학습 (Stacking)")

    df = df.copy()

    # 피처 리스트 가져오기
    features = get_feature_list()
    
    target = "trust_target"

    # 컬럼 존재 여부 확인
    missing = [col for col in features if col not in df.columns]
    if missing:
        raise ValueError(f"❌ 누락된 피처: {missing}")

    X = df[features]
    y = df[target]

    print(f"\n✅ 학습 데이터 준비 완료")
    print(f"   - 사용 피처: {len(features)}개 (10개 → 16개)")
    print(f"   - 타겟: {target} (연속형 점수)")

    # Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"\n✅ 데이터 분할 완료")
    print(f"   - 학습 데이터: {len(X_train)}개 (80%)")
    print(f"   - 테스트 데이터: {len(X_test)}개 (20%)")

    # RobustScaler
    scaler = RobustScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    print(f"\n✅ RobustScaler 적용 완료")

    # Base 모델 생성
    print(f"\n📦 Base 모델 생성 (5개):")
    base_models = create_base_models()
    
    model_descriptions = {
        'rf': 'RandomForest (트리 200개, 깊이 12)',
        'gb': 'GradientBoosting (트리 200개, 깊이 6)',
        'et': 'ExtraTrees (트리 200개, 랜덤 분할)',
        'ridge': 'Ridge (alpha=0.5)',
        'lasso': 'Lasso (L1 정규화)'
    }
    
    for i, (name, _) in enumerate(base_models, 1):
        print(f"   {i}️⃣ {model_descriptions[name]}")

    # Stacking Ensemble 생성
    print(f"\n🎯 Stacking Ensemble 생성")
    print(f"   - Base Models: 5개")
    print(f"   - Meta Model: Ridge (alpha=1.0)")
    print(f"   - CV: 5-Fold")
    
    stacking = StackingRegressor(
        estimators=base_models,
        final_estimator=Ridge(alpha=1.0),
        cv=5,
        n_jobs=-1
    )

    # 교차 검증
    print(f"\n🔄 교차 검증 (5-Fold CV):")
    model_names = {
        'rf': 'RandomForest',
        'gb': 'GradientBoosting',
        'et': 'ExtraTrees',
        'ridge': 'Ridge',
        'lasso': 'Lasso'
    }
    
    for name, model in base_models:
        cv_scores = cross_val_score(
            model, X_train_s, y_train, 
            cv=5, scoring='r2', n_jobs=-1
        )
        display_name = model_names[name]
        print(f"   {display_name:20s} | R² CV: {cv_scores.mean():.3f} (±{cv_scores.std():.3f})")

    # Stacking 학습
    print(f"\n⏳ Stacking 앙상블 학습 중...")
    stacking.fit(X_train_s, y_train)
    print(f"   ✅ 학습 완료!")

    # 개별 모델 성능 평가
    evaluate_individual_models(base_models, X_train_s, X_test_s, y_train, y_test)

    # Stacking 성능 평가
    print(f"\n🎯 Stacking 앙상블 성능 (Test Set):")
    stacking_test_pred = stacking.predict(X_test_s)
    stacking_train_pred = stacking.predict(X_train_s)
    
    test_r2 = r2_score(y_test, stacking_test_pred)
    train_r2 = r2_score(y_train, stacking_train_pred)
    test_mae = mean_absolute_error(y_test, stacking_test_pred)
    test_rmse = np.sqrt(mean_squared_error(y_test, stacking_test_pred))
    gap = train_r2 - test_r2

    print(f"   {'Stacking Ensemble':20s} | Test R²: {test_r2:.3f} | Train R²: {train_r2:.3f} | Gap: {gap:.3f}")
    print(f"   MAE: {test_mae:.2f} | RMSE: {test_rmse:.2f}")

    # 전체 데이터 예측
    X_all_s = scaler.transform(X)
    df["predicted_score"] = stacking.predict(X_all_s)
    
    # 등급 정확도 계산
    train_accuracy, test_accuracy, accuracy_gap, test_actual, test_predicted = calculate_grade_accuracy(
        df, X_train.index, X_test.index, target
    )

    # 결과 통계 출력
    print(f"\n📊 예측 결과 통계:")
    print(f"   - 예측 점수 평균: {df['predicted_score'].mean():.2f}")
    print(f"   - 실제 점수 평균: {df[target].mean():.2f}")
    print(f"   - 상관계수: {df['predicted_score'].corr(df[target]):.3f}")
    
    print(f"\n🎯 등급 정확도:")
    print(f"   - Train Accuracy: {train_accuracy:.2%}")
    print(f"   - Test Accuracy: {test_accuracy:.2%}")
    print(f"   - 과적합 차이: {accuracy_gap:.2%}")
    
    print(f"\n📋 등급 분류 리포트 (Test Set):")
    print(classification_report(test_actual, test_predicted, zero_division=0))

    # 모델 저장
    os.makedirs(MODEL_DIR, exist_ok=True)

    model_package = {
        'ensemble': stacking,
        'scaler': scaler,
        'features': features,
        'target': target,
        'metadata': {
            'model_type': 'stacking_regression',
            'base_models': ['RandomForest', 'GradientBoosting', 'ExtraTrees', 'Ridge', 'Lasso'],
            'meta_model': 'Ridge',
            'test_r2': test_r2,
            'test_mae': test_mae,
            'test_rmse': test_rmse,
            'train_r2': train_r2,
            'overfit_gap_r2': gap,
            'test_accuracy': test_accuracy,
            'train_accuracy': train_accuracy,
            'overfit_gap_accuracy': accuracy_gap
        }
    }
    
    model_path = os.path.join(MODEL_DIR, "advanced_ensemble.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model_package, f)

    print(f"\n💾 모델 저장: advanced_ensemble.pkl")
    print(f"   - 5개 Base Models + Stacking")
    print(f"   - Scaler + Features + Metadata")

    return df


if __name__ == "__main__":
    from _00_load_data import load_data
    from _01_create_target import create_regression_target
    from _02_feature_engineering import add_features
    
    df = load_data()
    df = create_regression_target(df)
    df = add_features(df)
    df = train_advanced_ensemble(df)
    print(f"\n✅ 앙상블 테스트 완료!")
