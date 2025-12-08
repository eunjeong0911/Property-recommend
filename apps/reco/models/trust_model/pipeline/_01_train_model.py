"""
중개사 신뢰도 다중분류 모델 학습 파이프라인
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    f1_score,
)
import warnings

warnings.filterwarnings("ignore")

# 데이터 로드 모듈 import
from _00_load_data import main as load_data


def split_data(X, y, test_size=0.2, random_state=42):
    """
    학습/테스트 데이터 분리
    
    Args:
        X: 피처 데이터
        y: 타겟 데이터
        test_size: 테스트 데이터 비율
        random_state: 랜덤 시드
        
    Returns:
        X_train, X_test, y_train, y_test
    """
    print(f"\n📊 [6단계] 데이터 분리 (Train: {int((1-test_size)*100)}%, Test: {int(test_size*100)}%)")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    print(f"   ✅ Train: {len(X_train)}개")
    print(f"   ✅ Test: {len(X_test)}개")
    
    return X_train, X_test, y_train, y_test


def scale_features(X_train, X_test):
    """
    피처 스케일링
    
    Args:
        X_train: 학습 데이터
        X_test: 테스트 데이터
        
    Returns:
        X_train_scaled, X_test_scaled, scaler
    """
    print("\n⚖️  [7단계] 피처 스케일링")
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("   ✅ StandardScaler 적용 완료")
    
    return X_train_scaled, X_test_scaled, scaler


def train_models(X_train, y_train, X_test, y_test, tune_hyperparams=True, use_class_weight=True):
    """
    여러 모델 학습 및 비교 (개선된 하이퍼파라미터)
    
    Args:
        X_train: 학습 피처
        y_train: 학습 타겟
        X_test: 테스트 피처
        y_test: 테스트 타겟
        tune_hyperparams: 하이퍼파라미터 튜닝 여부
        
    Returns:
        models: 학습된 모델 딕셔너리
        results: 성능 결과 딕셔너리
    """
    print("\n🤖 [8단계] 모델 학습")
    
    if tune_hyperparams:
        print("   ⚙️  하이퍼파라미터 튜닝 활성화")
        
        # RandomForest 튜닝 (더 넓은 범위)
        rf_params = {
            'n_estimators': [200, 300, 500],
            'max_depth': [10, 15, 20, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2', None]
        }
        
        rf_grid = GridSearchCV(
            RandomForestClassifier(random_state=42, n_jobs=-1, class_weight='balanced'),
            rf_params,
            cv=5,
            scoring='f1_weighted',
            n_jobs=-1,
            verbose=1
        )
        
        print("\n   🔹 RandomForest 튜닝 중...")
        rf_grid.fit(X_train, y_train)
        rf_model = rf_grid.best_estimator_
        print(f"      Best params: {rf_grid.best_params_}")
        print(f"      Best CV score: {rf_grid.best_score_:.4f}")
        
        # GradientBoosting 튜닝 (더 넓은 범위)
        gb_params = {
            'n_estimators': [200, 300, 500],
            'max_depth': [3, 5, 7, 10],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'min_samples_split': [2, 5, 10],
            'subsample': [0.8, 0.9, 1.0]
        }
        
        gb_grid = GridSearchCV(
            GradientBoostingClassifier(random_state=42),
            gb_params,
            cv=5,
            scoring='f1_weighted',
            n_jobs=-1,
            verbose=1
        )
        
        print("\n   🔹 GradientBoosting 튜닝 중...")
        gb_grid.fit(X_train, y_train)
        gb_model = gb_grid.best_estimator_
        print(f"      Best params: {gb_grid.best_params_}")
        print(f"      Best CV score: {gb_grid.best_score_:.4f}")
        
        # XGBoost 추가
        try:
            from xgboost import XGBClassifier
            
            xgb_params = {
                'n_estimators': [200, 300, 500],
                'max_depth': [3, 5, 7, 10],
                'learning_rate': [0.01, 0.05, 0.1],
                'subsample': [0.8, 0.9, 1.0],
                'colsample_bytree': [0.8, 0.9, 1.0]
            }
            
            xgb_grid = GridSearchCV(
                XGBClassifier(random_state=42, n_jobs=-1, eval_metric='mlogloss'),
                xgb_params,
                cv=5,
                scoring='f1_weighted',
                n_jobs=-1,
                verbose=1
            )
            
            print("\n   🔹 XGBoost 튜닝 중...")
            xgb_grid.fit(X_train, y_train)
            xgb_model = xgb_grid.best_estimator_
            print(f"      Best params: {xgb_grid.best_params_}")
            print(f"      Best CV score: {xgb_grid.best_score_:.4f}")
            
            models = {
                "RandomForest": rf_model,
                "GradientBoosting": gb_model,
                "XGBoost": xgb_model,
                "LogisticRegression": LogisticRegression(
                    max_iter=2000, random_state=42, multi_class="multinomial", 
                    C=1.0, class_weight='balanced'
                ),
            }
        except ImportError:
            print("   ⚠️  XGBoost 미설치 - RandomForest, GradientBoosting만 사용")
            models = {
                "RandomForest": rf_model,
                "GradientBoosting": gb_model,
                "LogisticRegression": LogisticRegression(
                    max_iter=2000, random_state=42, multi_class="multinomial", 
                    C=1.0, class_weight='balanced'
                ),
            }
    else:
        # 클래스 가중치 설정
        class_weight_param = 'balanced' if use_class_weight else None
        
        models = {
            "RandomForest": RandomForestClassifier(
                n_estimators=300, max_depth=20, min_samples_split=2, 
                min_samples_leaf=1, max_features='sqrt', random_state=42, n_jobs=-1,
                class_weight=class_weight_param
            ),
            "GradientBoosting": GradientBoostingClassifier(
                n_estimators=300, max_depth=7, learning_rate=0.1, 
                subsample=0.9, random_state=42
            ),
            "LogisticRegression": LogisticRegression(
                max_iter=2000, random_state=42, multi_class="multinomial", 
                C=1.0, class_weight=class_weight_param
            ),
        }
        
        # XGBoost 추가 시도
        try:
            from xgboost import XGBClassifier
            models["XGBoost"] = XGBClassifier(
                n_estimators=300, max_depth=7, learning_rate=0.1,
                subsample=0.9, colsample_bytree=0.9,
                random_state=42, n_jobs=-1, eval_metric='mlogloss'
            )
        except ImportError:
            pass
    
    results = {}
    
    for name, model in models.items():
        # 튜닝하지 않은 모델은 학습 필요
        if not tune_hyperparams or name == "LogisticRegression":
            print(f"\n   🔹 {name} 학습 중...")
            model.fit(X_train, y_train)
        
        # 예측
        y_pred = model.predict(X_test)
        
        # 평가
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="weighted")
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="accuracy")
        
        results[name] = {
            "model": model,
            "accuracy": accuracy,
            "f1_score": f1,
            "cv_mean": cv_scores.mean(),
            "cv_std": cv_scores.std(),
            "y_pred": y_pred,
        }
        
        print(f"      Accuracy: {accuracy:.4f}")
        print(f"      F1-Score: {f1:.4f}")
        print(f"      CV Score: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    
    return models, results


def select_best_model(results):
    """
    최고 성능 모델 선택
    
    Args:
        results: 모델 결과 딕셔너리
        
    Returns:
        best_model_name, best_model
    """
    print("\n🏆 [9단계] 최고 성능 모델 선택")
    
    # F1-Score 기준으로 선택
    best_name = max(results, key=lambda x: results[x]["f1_score"])
    best_model = results[best_name]["model"]
    
    print(f"\n   ✅ 선택된 모델: {best_name}")
    print(f"      Accuracy: {results[best_name]['accuracy']:.4f}")
    print(f"      F1-Score: {results[best_name]['f1_score']:.4f}")
    
    return best_name, best_model


def evaluate_model(model, X_test, y_test, class_names=None):
    """
    모델 상세 평가
    
    Args:
        model: 학습된 모델
        X_test: 테스트 피처
        y_test: 테스트 타겟
        class_names: 클래스 이름 리스트
    """
    print("\n📈 [10단계] 모델 평가")
    
    y_pred = model.predict(X_test)
    
    # 실제 존재하는 클래스만 사용
    unique_classes = sorted(set(y_test) | set(y_pred))
    if class_names is None:
        class_names = ["하", "중", "상"]
    actual_class_names = [class_names[i] for i in unique_classes]
    
    # Classification Report
    print("\n   📊 Classification Report:")
    print(classification_report(y_test, y_pred, labels=unique_classes, target_names=actual_class_names))
    
    # Confusion Matrix
    print("\n   🔢 Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    
    # 클래스별 정확도
    print("\n   🎯 클래스별 정확도:")
    for i, class_name in enumerate(class_names):
        class_acc = cm[i, i] / cm[i].sum() if cm[i].sum() > 0 else 0
        print(f"      {class_name}: {class_acc:.4f}")


def get_feature_importance(model, feature_names):
    """
    피처 중요도 출력
    
    Args:
        model: 학습된 모델
        feature_names: 피처 이름 리스트
    """
    print("\n🔍 [11단계] 피처 중요도")
    
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        print("\n   Top 10 중요 피처:")
        for i in range(min(10, len(feature_names))):
            idx = indices[i]
            print(f"      {i+1}. {feature_names[idx]}: {importances[idx]:.4f}")
    else:
        print("   ⚠️  이 모델은 feature_importances_를 지원하지 않습니다.")


def save_model(model, scaler, feature_names, output_dir="apps/reco/models/trust_model/saved_models"):
    """
    모델 저장
    
    Args:
        model: 학습된 모델
        scaler: 스케일러
        feature_names: 피처 이름 리스트
        output_dir: 저장 디렉토리
    """
    print("\n💾 [12단계] 모델 저장")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 모델 저장
    model_path = output_path / "trust_model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"   ✅ 모델 저장: {model_path}")
    
    # 스케일러 저장
    scaler_path = output_path / "scaler.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    print(f"   ✅ 스케일러 저장: {scaler_path}")
    
    # 피처 이름 저장
    features_path = output_path / "feature_names.pkl"
    with open(features_path, "wb") as f:
        pickle.dump(feature_names, f)
    print(f"   ✅ 피처 이름 저장: {features_path}")


def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("🏠 중개사 신뢰도 모델 - 학습 파이프라인")
    print("=" * 70)
    
    # 1-5단계: 데이터 로드 및 전처리
    office_df, X, y, feature_names = load_data()
    
    # 6단계: 데이터 분리
    X_train, X_test, y_train, y_test = split_data(X, y)
    
    # 7단계: 피처 스케일링
    X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)
    
    # 8단계: 모델 학습 (하이퍼파라미터 튜닝 비활성화, 개선된 기본값 사용)
    models, results = train_models(X_train_scaled, y_train, X_test_scaled, y_test, tune_hyperparams=False, use_class_weight=True)
    
    # 9단계: 최고 모델 선택
    best_name, best_model = select_best_model(results)
    
    # 10단계: 모델 평가
    evaluate_model(best_model, X_test_scaled, y_test)
    
    # 11단계: 피처 중요도
    get_feature_importance(best_model, feature_names)
    
    # 12단계: 모델 저장
    save_model(best_model, scaler, feature_names)
    
    print("\n" + "=" * 70)
    print("✅ 모델 학습 완료!")
    print("=" * 70)
    
    return best_model, scaler, feature_names, results


if __name__ == "__main__":
    best_model, scaler, feature_names, results = main()
