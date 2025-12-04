# pipeline/_04_regression_model.py

import os
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import RandomForestRegressor

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")


def train_regression(df):
    print("\n" + "="*60)
    print("🤖 [5단계] 회귀 모델 학습")
    print("="*60)

    df = df.copy()

    # ----------------------
    # 1. 사용 feature
    # ----------------------
    features = [
        "거래완료", "등록매물", "총매물수",
        "일평균거래", "거래성사율",
        "cluster_temp"
    ]

    # feature 존재 여부 확인
    missing = [col for col in features if col not in df.columns]
    if missing:
        raise ValueError(f"❌ 누락된 피처: {missing}")

    X = df[features]
    y = df["rule_score"]

    print(f"✅ 학습 데이터 준비 완료")
    print(f"   - 사용 피처: {len(features)}개")
    print(f"   - 타겟: rule_score")

    # ----------------------
    # 2. Train/Test split
    # ----------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"\n✅ 데이터 분할 완료")
    print(f"   - 학습 데이터: {len(X_train)}개 (80%)")
    print(f"   - 테스트 데이터: {len(X_test)}개 (20%)")

    # ----------------------
    # 3. 모델 학습
    # ----------------------
    model = RandomForestRegressor(n_estimators=300, random_state=42)
    model.fit(X_train, y_train)

    print(f"\n✅ RandomForest 회귀 모델 학습 완료")
    print(f"   - 트리 개수: 300개")

    # ----------------------
    # 4. 평가
    # ----------------------
    pred = model.predict(X_test)
    rmse = (mean_squared_error(y_test, pred)) ** 0.5
    r2 = model.score(X_test, y_test)
    
    print(f"\n📊 모델 성능 평가")
    print(f"   - RMSE: {rmse:.4f}")
    print(f"   - R² Score: {r2:.4f}")

    # 피처 중요도
    feature_importance = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n📈 피처 중요도 (Top 3)")
    for idx, row in feature_importance.head(3).iterrows():
        print(f"   - {row['feature']}: {row['importance']:.4f}")

    # ----------------------
    # 5. 전체 데이터 예측값 생성
    # ----------------------
    df["reg_pred"] = model.predict(X)

    print(f"\n✅ 회귀 예측값(reg_pred) 생성 완료")
    print(f"   - 평균: {df['reg_pred'].mean():.2f}")
    print(f"   - 범위: {df['reg_pred'].min():.2f} ~ {df['reg_pred'].max():.2f}")

    # ----------------------
    # 6. 모델 저장
    # ----------------------
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, "regression_model.pkl")

    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    print(f"\n💾 모델 저장 완료: {model_path}")

    return df
