import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import RobustScaler, LabelEncoder
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    ExtraTreesClassifier,
    VotingClassifier
)

# XGBoost 추가
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost not installed. Install with: pip install xgboost")

# 모델 저장 경로
MODEL_DIR = Path(__file__).parent.parent / "models"


def get_feature_list():
    """
    사용할 피처 리스트 반환 (중개사 등급 분류 - 개선 버전)
    
    총 15개 피처:
    - 매물 정보 (1개): 등록매물
    - 시간 정보 (6개): 영업일수, 영업년수, 등록일_년, 등록일_월, 계절, 보증보험_남은일수
    - 지역 정보 (4개): 지역중개사수, 지역내_등록매물_순위, 지역_평균영업년수, 지역_매물밀도
    - 안전성 (1개): 보증보험유효
    - 파생 피처 (3개): 매물_규모_지수, 지역_경쟁_강도, 영업년수_매물_상호작용
    
    Target: 3등급 (A, B, C) - 거래성사율 분위수 기반
    """
    return [
        # 매물 정보
        "등록매물",
        # 시간 정보
        "영업일수",
        "영업년수",
        "등록일_년",
        "등록일_월",
        "계절",
        "보증보험_남은일수",
        # 지역 정보
        "지역중개사수",
        "지역내_등록매물_순위",
        "지역_평균영업년수",
        "지역_매물밀도",
        # 안전성
        "보증보험유효",
        # 파생 피처
        "매물_규모_지수",
        "지역_경쟁_강도",
        "영업년수_매물_상호작용"
    ]


def create_base_models():
    """
    4개의 강한 분류 모델 생성 (성능 낮은 모델 제거)
    
    제거: LogisticRegression (39.5%), SVC (52.6%)
    유지: RandomForest (57.9%), XGBoost (57.9%), ExtraTrees (56.6%), GradientBoosting (56.6%)
    
    Returns:
        list: (name, model) 튜플 리스트
    """
    models = [
        ('rf', RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_split=6,
            min_samples_leaf=3,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )),
        ('gb', GradientBoostingClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            min_samples_split=6,
            min_samples_leaf=3,
            max_features='sqrt',
            random_state=42
        )),
        ('et', ExtraTreesClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_split=6,
            min_samples_leaf=3,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        ))
    ]
    
    # XGBoost 추가 (설치되어 있는 경우)
    if XGBOOST_AVAILABLE:
        models.append(
            ('xgb', XGBClassifier(
                n_estimators=200,
                max_depth=7,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                eval_metric='mlogloss'
            ))
        )
    
    return models


def evaluate_individual_models(models, X_train, X_test, y_train, y_test):
    """
    개별 모델 성능 평가
    """
    print(f"\n📊 개별 모델 성능 (Test Set):")
    
    model_names = {
        'rf': 'RandomForest',
        'gb': 'GradientBoosting',
        'et': 'ExtraTrees',
        'lr': 'LogisticRegression',
        'svc': 'SVC',
        'xgb': 'XGBoost'
    }
    
    for name, model in models:
        model.fit(X_train, y_train)
        
        test_pred = model.predict(X_test)
        test_acc = accuracy_score(y_test, test_pred)
        
        train_pred = model.predict(X_train)
        train_acc = accuracy_score(y_train, train_pred)
        
        gap = train_acc - test_acc
        
        display_name = model_names.get(name, name)
        print(f"   {display_name:20s} | Test Acc: {test_acc:.3f} | Train Acc: {train_acc:.3f} | Gap: {gap:.3f}")


def train_classification_ensemble(df):
    """
    다중 분류 앙상블: Voting 방식으로 강한 모델만 결합
    
    목표: Accuracy 60% 이상 (3등급)
    Target: A, B, C (거래성사율 분위수 기반)
    개선: Soft Voting + 강한 모델만 (RF, XGB, ET, GB) + 가중치 적용
    """
    print("\n🤖 [4단계] Voting 앙상블 학습 (강한 모델만)")

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
    
    # Label Encoding (A, B, C → 0, 1, 2)
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    print(f"\n✅ 학습 데이터 준비 완료")
    print(f"   - 사용 피처: {len(features)}개 (10개 → 15개 개선)")
    print(f"   - 타겟: {target} (3등급: A, B, C)")
    print(f"   - 클래스: {le.classes_}")
    print(f"\n   등급 분포:")
    for grade in le.classes_:
        count = (y == grade).sum()
        print(f"   - {grade}: {count}개")

    # Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
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
    base_models = create_base_models()
    num_models = len(base_models)
    print(f"\n📦 강한 모델만 선택 ({num_models}개):")
    
    model_descriptions = {
        'rf': 'RandomForest (트리 200개, 깊이 12) ⭐',
        'gb': 'GradientBoosting (트리 200개, 깊이 6, LR 0.05)',
        'et': 'ExtraTrees (트리 200개, 랜덤 분할)',
        'xgb': 'XGBoost (트리 200개, 깊이 7, LR 0.05) ⭐'
    }
    
    for i, (name, _) in enumerate(base_models, 1):
        print(f"   {i}️⃣ {model_descriptions.get(name, name)}")

    # Voting Ensemble 생성
    print(f"\n🎯 Voting Ensemble 생성")
    print(f"   - Base Models: {num_models}개 (강한 모델만)")
    print(f"   - Voting: Soft (확률 평균)")
    
    # 가중치 설정 (RF와 XGB에 더 높은 가중치)
    if XGBOOST_AVAILABLE:
        weights = [2, 1, 1, 2]  # RF, GB, ET, XGB
        print(f"   - 가중치: RF=2, GB=1, ET=1, XGB=2")
        print(f"   ⭐ XGBoost 포함!")
    else:
        weights = [2, 1, 1]  # RF, GB, ET
        print(f"   - 가중치: RF=2, GB=1, ET=1")
    
    voting = VotingClassifier(
        estimators=base_models,
        voting='soft',
        weights=weights,
        n_jobs=-1
    )

    # 교차 검증
    print(f"\n🔄 교차 검증 (5-Fold CV):")
    model_names = {
        'rf': 'RandomForest',
        'gb': 'GradientBoosting',
        'et': 'ExtraTrees',
        'lr': 'LogisticRegression',
        'svc': 'SVC',
        'xgb': 'XGBoost'
    }
    
    for name, model in base_models:
        cv_scores = cross_val_score(
            model, X_train_s, y_train, 
            cv=5, scoring='accuracy', n_jobs=-1
        )
        display_name = model_names[name]
        print(f"   {display_name:20s} | Acc CV: {cv_scores.mean():.3f} (±{cv_scores.std():.3f})")

    # Voting 학습
    print(f"\n⏳ Voting 앙상블 학습 중...")
    voting.fit(X_train_s, y_train)
    print(f"   ✅ 학습 완료!")

    # 개별 모델 성능 평가
    evaluate_individual_models(base_models, X_train_s, X_test_s, y_train, y_test)

    # Voting 성능 평가
    print(f"\n🎯 Voting 앙상블 성능 (Test Set):")
    voting_test_pred = voting.predict(X_test_s)
    voting_train_pred = voting.predict(X_train_s)
    
    test_acc = accuracy_score(y_test, voting_test_pred)
    train_acc = accuracy_score(y_train, voting_train_pred)
    gap = train_acc - test_acc

    print(f"   {'Voting Ensemble':20s} | Test Acc: {test_acc:.3f} | Train Acc: {train_acc:.3f} | Gap: {gap:.3f}")

    # 전체 데이터 예측
    X_all_s = scaler.transform(X)
    y_pred_encoded = voting.predict(X_all_s)
    y_pred = le.inverse_transform(y_pred_encoded)
    y_pred_proba = voting.predict_proba(X_all_s)
    
    df["predicted_grade"] = y_pred
    df["predicted_grade_encoded"] = y_pred_encoded
    
    # 각 등급별 확률 저장
    for i, grade in enumerate(le.classes_):
        df[f"prob_{grade}"] = y_pred_proba[:, i]

    # 분류 리포트
    print(f"\n📋 분류 리포트 (Test Set):")
    y_test_labels = le.inverse_transform(y_test)
    y_pred_labels = le.inverse_transform(voting_test_pred)
    print(classification_report(y_test_labels, y_pred_labels, zero_division=0))

    # Confusion Matrix
    print(f"\n📊 Confusion Matrix (Test Set):")
    cm = confusion_matrix(y_test_labels, y_pred_labels, labels=le.classes_)
    cm_df = pd.DataFrame(cm, index=le.classes_, columns=le.classes_)
    print(cm_df)
    
    # 등급별 정확도
    print(f"\n📈 등급별 정확도:")
    for grade in le.classes_:
        mask = y_test_labels == grade
        if mask.sum() > 0:
            acc = (y_pred_labels[mask] == grade).mean()
            print(f"   - {grade}등급: {acc:.1%} ({(y_pred_labels[mask] == grade).sum()}/{mask.sum()})")

    # 모델 저장
    MODEL_DIR.mkdir(exist_ok=True)

    base_model_names = ['RandomForest', 'GradientBoosting', 'ExtraTrees']
    if XGBOOST_AVAILABLE:
        base_model_names.append('XGBoost')
    
    model_package = {
        'ensemble': voting,
        'scaler': scaler,
        'label_encoder': le,
        'features': features,
        'target': target,
        'metadata': {
            'model_type': 'voting_classification',
            'base_models': base_model_names,
            'voting_type': 'soft',
            'weights': weights,
            'test_accuracy': test_acc,
            'train_accuracy': train_acc,
            'overfit_gap': gap,
            'num_classes': 3,
            'num_features': len(features),
            'classes': le.classes_.tolist(),
            'xgboost_included': XGBOOST_AVAILABLE
        }
    }
    
    model_path = MODEL_DIR / "voting_ensemble.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model_package, f)

    print(f"\n💾 모델 저장: voting_ensemble.pkl")
    print(f"   - {num_models}개 강한 모델 + Soft Voting")
    print(f"   - Scaler + LabelEncoder + Features + Metadata")
    print(f"   - 3등급 분류: A, B, C (거래성사율 분위수 기반)")
    print(f"   - 15개 피처 + 가중치 적용")

    return df


if __name__ == "__main__":
    from _00_load_data import load_data
    from _01_create_target import create_regression_target
    from _02_feature_engineering import add_features
    
    df = load_data()
    df = create_regression_target(df)
    df = add_features(df)
    df = train_classification_ensemble(df)
    print(f"\n✅ Voting 앙상블 테스트 완료!")
