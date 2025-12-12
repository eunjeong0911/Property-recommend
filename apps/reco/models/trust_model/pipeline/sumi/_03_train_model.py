"""
중개사 신뢰도 모델 학습 파이프라인 (Regression)
- 타겟: 베이지안_성사율 (지역가중치 + 베이지안 조정된 거래성사율)
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings

warnings.filterwarnings("ignore")

# 데이터 로드 및 피처/타겟 엔지니어링 모듈 import
from _00_load_data import load_processed_office_data as load_data
import _01_targer_engineering as target_engineering
from _02_feature_engineering import main as feature_engineering


def split_data(X, y, test_size=0.2, random_state=42):
    """학습/테스트 데이터 분리"""
    print(f"\n📊 데이터 분리 (Train: {int((1-test_size)*100)}%, Test: {int(test_size*100)}%)")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    print(f"   ✅ Train: {len(X_train)}개 / Test: {len(X_test)}개")
    return X_train, X_test, y_train, y_test


def scale_features(X_train, X_test):
    """피처 스케일링"""
    print("\n⚖️ 피처 스케일링 (StandardScaler)")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    return X_train_scaled, X_test_scaled, scaler


def train_models(X_train, y_train, X_test, y_test):
    """
    회귀 모델 학습 및 비교
    """
    print("\n🤖 모델 학습 (Regression)")
    
    models = {
        "RandomForest": RandomForestRegressor(
            n_estimators=300,      # 트리 수 증가
            max_depth=3,           # 깊이 얕게
            min_samples_split=10,
            max_samples=0.8,       # subsample 효과
            random_state=42, n_jobs=-1
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=300,      # 트리 수 증가
            max_depth=3,           # 깊이 얕게
            learning_rate=0.01,    # 낮은 학습률
            subsample=0.8,         # 랜덤 샘플링
            random_state=42
        ),
        "Ridge": Ridge(alpha=1.0)
    }
    
    results = {}
    
    for name, model in models.items():
        print(f"\n   🔹 {name} 학습 중...")
        model.fit(X_train, y_train)
        
        # 예측
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        
        # 평가 지표
        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
        test_mae = mean_absolute_error(y_test, y_test_pred)
        test_r2 = r2_score(y_test, y_test_pred)
        
        # CV Score
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
        
        results[name] = {
            "model": model,
            "train_rmse": train_rmse,
            "test_rmse": test_rmse,
            "test_mae": test_mae,
            "test_r2": test_r2,
            "cv_r2_mean": cv_scores.mean(),
            "y_pred": y_test_pred,
        }
        
        print(f"      Train RMSE: {train_rmse:.4f} / Test RMSE: {test_rmse:.4f}")
        print(f"      Test MAE: {test_mae:.4f}")
        print(f"      Test R²: {test_r2:.4f}")
        print(f"      CV R² (5-fold): {cv_scores.mean():.4f}")
    
    return models, results


def evaluate_model(model, X_test, y_test, feature_names):
    """모델 상세 평가"""
    print("\n📈 최종 모델 평가")
    
    y_pred = model.predict(X_test)
    
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"   RMSE: {rmse:.4f}")
    print(f"   MAE:  {mae:.4f}")
    print(f"   R²:   {r2:.4f}")
    
    # 피처 중요도
    if hasattr(model, "feature_importances_"):
        print("\n🔍 피처 중요도 (Top 10)")
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]
        for i in range(min(10, len(feature_names))):
            idx = indices[i]
            print(f"      {i+1}. {feature_names[idx]}: {importances[idx]:.4f}")


def save_model(model, scaler, feature_names, output_dir="apps/reco/models/trust_model/saved_models"):
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
    
    print(f"   ✅ 저장 완료: {output_path}")


def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("🏠 중개사 신뢰도 모델 - 학습 파이프라인 (Regression)")
    print("=" * 70)
    
    # 1. 데이터 로드
    raw_df = load_data()
    
    # 2. 타겟 생성 (베이지안_성사율)
    df_with_target = target_engineering.main(raw_df)
    
    # 3. 피처 생성 (X)
    df_final, X, feature_names = feature_engineering(df_with_target)
    
    # 4. 타겟 추출 (y = 베이지안_성사율)
    TARGET_COL = "베이지안_성사율"
    if TARGET_COL not in df_final.columns:
        raise ValueError(f"❌ '{TARGET_COL}' 컬럼이 없습니다. _01_targer_engineering.py를 확인하세요.")
    
    y = df_final[TARGET_COL]
    
    print(f"\n✅ 데이터 준비 완료")
    print(f"   - Feature(X): {X.shape}")
    print(f"   - Target(y): {y.shape} (Mean: {y.mean():.4f}, Std: {y.std():.4f})")
    
    # 5. 데이터 분리
    X_train, X_test, y_train, y_test = split_data(X, y)
    
    # 6. 스케일링
    X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)
    
    # 7. 모델 학습
    models, results = train_models(X_train_scaled, y_train, X_test_scaled, y_test)
    
    # 8. 최종 모델 선택 (R2 기준)
    best_name = max(results, key=lambda k: results[k]["test_r2"])
    best_model = results[best_name]["model"]
    print(f"\n🏆 최종 모델 선택: {best_name} (R²: {results[best_name]['test_r2']:.4f})")
    
    # 9. 평가 및 저장
    evaluate_model(best_model, X_test_scaled, y_test, feature_names)
    save_model(best_model, scaler, feature_names)
    
    print("\n" + "=" * 70)
    print("✅ 모델 학습 완료!")
    print("=" * 70)
    
    return best_model, scaler, feature_names, results


if __name__ == "__main__":
    main()
