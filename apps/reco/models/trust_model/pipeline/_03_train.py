"""
_03_train.py
중개사 신뢰도 모델 - 학습 단계 (LogisticRegression)
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from pathlib import Path
import pickle
import warnings
warnings.filterwarnings('ignore')

FEATURE_PATH = "data/ML/office_features.csv"
MODEL_TEMP_PATH = "apps/reco/models/trust_model/save_models/temp_trained_models.pkl"


def load_data():
    """데이터 로드"""
    df = pd.read_csv(FEATURE_PATH, encoding="utf-8-sig")
    
    # 타겟 변수
    y = df["신뢰도등급"].copy()
    
    # Feature 선택 (12개)
    selected_features = [
        "거래완료_safe", "등록매물_safe", "총거래활동량",
        "총_직원수", "공인중개사수", "공인중개사_비율",
        "운영기간_년", "운영경험_지수", "숙련도_지수", "운영_안정성",
        "대형사무소", "직책_다양성"
    ]
    
    # 실제 존재하는 Feature만 필터링
    available_features = [col for col in selected_features if col in df.columns]
    X = df[available_features].copy()
    
    # 모든 컬럼을 숫자형으로 강제 변환
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')
    
    # 결측치 처리
    X = X.replace([np.inf, -np.inf], 0).fillna(0)
    
    print(f"📊 최종 Feature 수: {len(X.columns)}개")
    print(f"📊 데이터 샘플 수: {len(X)}개")
    print(f"\n📋 사용된 Feature:")
    for i, feature in enumerate(X.columns, 1):
        print(f"   {i:2d}. {feature}")
    
    return X, y


def train_models(X_train_scaled, y_train, X_test_scaled, y_test):
    """
    LogisticRegression 모델 학습
    """
    print("\n🤖 모델 학습 시작...")
    
    models = {}
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # LogisticRegression
    print("\n[1/1] LogisticRegression 학습 중...")
    lr_model = LogisticRegression(
        C=1.0,
        max_iter=1000,
        class_weight='balanced',
        random_state=42
    )
    lr_model.fit(X_train_scaled, y_train)
    lr_scores = cross_val_score(lr_model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
    models["LogisticRegression"] = lr_model
    print(f"   ✓ CV Score: {lr_scores.mean():.4f} (±{lr_scores.std():.4f})")
    
    print("\n✅ 모델 학습 완료!")
    return models


def main():
    print("=" * 70)
    print(" " * 20 + "모델 학습 (12개 Feature)")
    print("=" * 70)

    # 1) 데이터 로드
    X, y = load_data()
    
    # 2) Train/Test Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\n📊 데이터 분할:")
    print(f"   - Train: {len(X_train)}개")
    print(f"   - Test: {len(X_test)}개")
    
    # 3) 스케일링
    print("\n🔍 데이터 스케일링 중...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print("   ✅ StandardScaler 적용 완료")
    
    # 4) 모델 학습
    models = train_models(X_train_scaled, y_train, X_test_scaled, y_test)
    
    # 5) Test 세트 평가
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
    
    # 6) 모델 + 스케일러 저장
    Path("apps/reco/models/trust_model/save_models").mkdir(parents=True, exist_ok=True)
    with open(MODEL_TEMP_PATH, "wb") as f:
        pickle.dump(
            {
                "models": models,
                "scaler": scaler,
                "X_train_scaled": X_train_scaled,
                "y_train": y_train,
                "X_test_scaled": X_test_scaled,
                "y_test": y_test,
                "feature_names": list(X.columns),
                "cv_results": cv_results,
            },
            f,
        )
    
    print(f"\n✓ 학습 완료, temp 모델 저장: {MODEL_TEMP_PATH}")
    
    # 7) 최고 성능 모델 출력
    best_model_name = max(cv_results.keys(), key=lambda k: cv_results[k]['test_acc'])
    print(f"\n🏆 최고 Test 성능 모델: {best_model_name}")
    print(f"   - Test Accuracy: {cv_results[best_model_name]['test_acc']:.4f}")
    print(f"   - Train Accuracy: {cv_results[best_model_name]['train_acc']:.4f}")
    
    print("\n" + "=" * 70)
    print(" " * 25 + "완료!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
