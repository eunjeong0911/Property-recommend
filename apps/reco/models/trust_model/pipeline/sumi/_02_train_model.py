"""
중개사 신뢰도 다중분류 모델 학습 파이프라인
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    f1_score,
)
import warnings

warnings.filterwarnings("ignore")

# 데이터 로드 및 피처 엔지니어링 모듈 import
from _00_load_data import load_processed_office_data as load_data
from _01_feature_engineering import main as feature_engineering


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


def train_models(X_train, y_train, X_test, y_test, tune_hyperparams=True, use_class_weight=True, use_smote=True):
    """
    여러 모델 학습 및 비교 (개선된 하이퍼파라미터)
    
    Args:
        X_train: 학습 피처
        y_train: 학습 타겟
        X_test: 테스트 피처
        y_test: 테스트 타겟
        tune_hyperparams: 하이퍼파라미터 튜닝 여부
        use_smote: SMOTE 오버샘플링 사용 여부
        
    Returns:
        models: 학습된 모델 딕셔너리
        results: 성능 결과 딕셔너리
    """
    print("\n🤖 [8단계] 모델 학습")
    
    # BorderlineSMOTE 적용 (클래스 불균형 해결 - 경계선 샘플 집중)
    if use_smote:
        try:
            from imblearn.over_sampling import BorderlineSMOTE
            print("   🔄 BorderlineSMOTE 오버샘플링 적용 중...")
            print("      (경계선 근처 샘플 집중 생성 - 중등급 예측 강화)")
            
            # 중등급(클래스 1)을 더 많이 샘플링
            # 원본 분포 확인
            unique_orig, counts_orig = np.unique(y_train, return_counts=True)
            max_count = counts_orig.max()
            
            # 샘플링 전략: 중등급을 1.2배만 생성 (과적합 방지)
            sampling_strategy = {
                0: max_count,      # 하등급: 최대값
                1: int(max_count * 1.2),  # 중등급: 최대값의 1.2배
                2: max_count       # 상등급: 최대값
            }
            
            smote = BorderlineSMOTE(
                random_state=42, 
                k_neighbors=5,
                sampling_strategy=sampling_strategy,
                kind='borderline-1'  # 경계선 샘플만 사용
            )
            X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
            
            print(f"      원본: {len(X_train)}개")
            print(f"      리샘플링 후: {len(X_train_resampled)}개")
            
            # 클래스별 분포 확인
            unique, counts = np.unique(y_train_resampled, return_counts=True)
            class_names = ['하', '중', '상']
            for cls, cnt in zip(unique, counts):
                print(f"      클래스 {class_names[cls]}: {cnt}개")
            
            X_train = X_train_resampled
            y_train = y_train_resampled
            
        except ImportError:
            print("   ⚠️  imbalanced-learn 미설치 - SMOTE 스킵")
            print("   💡 설치: pip install imbalanced-learn")
    
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
                    C=0.1, class_weight='balanced'  # C=1.0 → 0.1 (정규화 강화)
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
                n_estimators=80,            # GridSearchCV 최적값
                max_depth=5,                # GridSearchCV 최적값
                min_samples_split=12,       # GridSearchCV 최적값
                min_samples_leaf=8,         # GridSearchCV 최적값
                max_samples=0.9,            # GridSearchCV 최적값
                max_features='sqrt',        # GridSearchCV 최적값
                random_state=42,
                n_jobs=-1,
                class_weight=class_weight_param
            ),
        }
    
    results = {}
    
    for name, model in models.items():
        print(f"\n   🔹 {name} 학습 중...")
        model.fit(X_train, y_train)
        
        # GridSearchCV인 경우 최적 파라미터 출력
        if hasattr(model, 'best_params_'):
            print(f"      ✅ 최적 파라미터: {model.best_params_}")
            print(f"      ✅ 최적 CV 점수: {model.best_score_:.4f}")
        
        # Train 예측
        y_train_pred = model.predict(X_train)
        train_accuracy = accuracy_score(y_train, y_train_pred)
        
        # Test 예측
        y_pred = model.predict(X_test)
        test_accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="weighted")
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="accuracy")
        
        results[name] = {
            "model": model,
            "train_accuracy": train_accuracy,
            "accuracy": test_accuracy,
            "f1_score": f1,
            "cv_mean": cv_scores.mean(),
            "cv_std": cv_scores.std(),
            "y_pred": y_pred,
        }
        
        print(f"      Train Accuracy: {train_accuracy:.4f}")
        print(f"      Test Accuracy:  {test_accuracy:.4f}")
        print(f"      차이: {abs(train_accuracy - test_accuracy):.4f}")
        if abs(train_accuracy - test_accuracy) > 0.1:
            print(f"      ⚠️  과적합")
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
    print("\n🏆 [9단계] 최종 모델 선택")
    
    # RandomForest 고정 선택
    best_name = "RandomForest"
    best_model = results[best_name]["model"]
    
    # 과적합 정도 계산
    overfitting = abs(results[best_name]['train_accuracy'] - results[best_name]['accuracy'])
    
    print(f"\n   ✅ 선택된 모델: {best_name}")
    print(f"      Accuracy: {results[best_name]['accuracy']:.4f}")
    print(f"      F1-Score: {results[best_name]['f1_score']:.4f}")
    print(f"      과적합: {overfitting:.4f}")
    
    return best_name, best_model


def evaluate_model(model, X_train, y_train, X_test, y_test, class_names=None):
    """
    모델 상세 평가 (Train/Test 비교)
    
    Args:
        model: 학습된 모델
        X_train: 학습 피처
        y_train: 학습 타겟
        X_test: 테스트 피처
        y_test: 테스트 타겟
        class_names: 클래스 이름 리스트
    """
    print("\n📈 [10단계] 모델 평가")
    
    # Train 성능
    y_train_pred = model.predict(X_train)
    train_accuracy = accuracy_score(y_train, y_train_pred)
    train_f1 = f1_score(y_train, y_train_pred, average="weighted")
    
    # Test 성능
    y_pred = model.predict(X_test)
    test_accuracy = accuracy_score(y_test, y_pred)
    test_f1 = f1_score(y_test, y_pred, average="weighted")
    
    # 과적합 확인
    print(f"\n   🔍 과적합 확인:")
    print(f"      Train Accuracy: {train_accuracy:.4f}")
    print(f"      Test Accuracy:  {test_accuracy:.4f}")
    print(f"      차이: {abs(train_accuracy - test_accuracy):.4f}")
    
    if abs(train_accuracy - test_accuracy) > 0.1:
        print(f"      ⚠️  과적합 의심 (차이 > 10%)")
    elif abs(train_accuracy - test_accuracy) > 0.05:
        print(f"      ⚡ 약간의 과적합 (차이 5-10%)")
    else:
        print(f"      ✅ 과적합 없음 (차이 < 5%)")
    
    print(f"\n      Train F1-Score: {train_f1:.4f}")
    print(f"      Test F1-Score:  {test_f1:.4f}")
    print(f"      차이: {abs(train_f1 - test_f1):.4f}")
    
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
    raw_df = load_data()
    office_df, X, y, feature_names = feature_engineering(raw_df)
    
    # 6단계: 데이터 분리
    X_train, X_test, y_train, y_test = split_data(X, y)
    
    # 7단계: 피처 스케일링
    X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)
    
    # 8단계: 모델 학습 (하이퍼파라미터 튜닝 비활성화, 개선된 기본값 사용, SMOTE 적용)
    models, results = train_models(X_train_scaled, y_train, X_test_scaled, y_test, tune_hyperparams=False, use_class_weight=True, use_smote=True)
    
    # 9단계: RandomForest 사용 (최적 하이퍼파라미터)
    best_name = "RandomForest"
    best_model = results[best_name]["model"]
    
    print("\n🏆 [9단계] 최종 모델 선택")
    print(f"   ✅ 선택된 모델: {best_name}")
    print(f"      Accuracy: {results[best_name]['accuracy']:.4f}")
    print(f"      F1-Score: {results[best_name]['f1_score']:.4f}")
    print(f"      과적합: {abs(results[best_name]['train_accuracy'] - results[best_name]['accuracy']):.4f}")
    
    # 10단계: 모델 평가 (Train/Test 비교)
    evaluate_model(best_model, X_train_scaled, y_train, X_test_scaled, y_test)
    
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
