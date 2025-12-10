"""
_03_train.py
중개사 신뢰도 모델 - 학습 단계
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold, GridSearchCV
from sklearn.preprocessing import RobustScaler, PowerTransformer, QuantileTransformer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
from pathlib import Path
import pickle
import numpy as np

FEATURE_PATH = "data/office_features.csv"
MODEL_TEMP_PATH = "apps/reco/models/trust_model/save_models/temp_trained_models.pkl"


def load_data():
    df = pd.read_csv(FEATURE_PATH, encoding="utf-8-sig")

    # === (중요) 실제 타겟 이름 사용 ===
    y = df["신뢰도등급"].copy()

    # === 완전한 Data Leakage만 제거 (균형 잡힌 접근) ===
    direct_leakage = [
        "지역평균", "지역표준편차", "Zscore",  # 타겟 계산 중간 변수
        "신뢰도등급", "신뢰도등급_숫자", "target"  # 타겟 자체
    ]
    
    # === 개선된 Feature 선택 ===
    # 1) 기본 사무소 정보
    basic_features = [
        "총_직원수", "공인중개사수", "중개보조원수", "대표수", "일반직원수"
    ]
    
    # 2) 비율 및 구성 정보
    ratio_features = [
        "공인중개사_비율", "중개보조원_비율", "대표_비율", "일반직원_비율",
        "복수공인중개사", "공인중개사_없음", "직원_자격증비율"
    ]
    
    # 3) 규모 분류
    size_features = [
        "대형사무소", "중형사무소", "소형사무소"
    ]
    
    # 4) 운영 기간 (중요한 신뢰도 지표)
    time_features = [
        "운영기간_일", "운영기간_년", "운영기간_일_log",
        "신규사무소", "중견사무소", "노포사무소"
    ]
    
    # 5) 개설 시기 패턴
    timing_features = [
        "개설_월", "상반기개설", "하반기개설"
    ]
    
    # 6) 실제 거래 규모 (원본 데이터, 비율 아님)
    volume_features = [
        "거래완료_숫자", "등록매물_숫자"  # 절대값은 유용한 정보
    ]
    
    # 7) 추가 Feature Engineering (더 복잡한 패턴 포착)
    # 거래 활동성 지표
    df["거래활동성"] = df["거래완료_숫자"] + df["등록매물_숫자"]
    df["거래효율성"] = np.where(df["등록매물_숫자"] > 0, 
                           df["거래완료_숫자"] / (df["등록매물_숫자"] + 1), 0)
    
    # 직원당 성과 지표
    df["직원당_거래완료"] = df["거래완료_숫자"] / df["총_직원수_safe"]
    df["직원당_등록매물"] = df["등록매물_숫자"] / df["총_직원수_safe"]
    
    # 경험 지표 (운영기간 기반)
    df["경험점수"] = np.log1p(df["운영기간_일"]) * df["총_직원수"]
    df["숙련도"] = df["운영기간_년"] * df["공인중개사수"]
    
    # 규모별 효율성
    df["대형사무소_효율성"] = df["대형사무소"] * df["거래완료_숫자"]
    df["소형사무소_집중도"] = df["소형사무소"] * df["직원당_거래완료"]
    
    engineered_features = [
        "거래활동성", "거래효율성", "직원당_거래완료", "직원당_등록매물",
        "경험점수", "숙련도", "대형사무소_효율성", "소형사무소_집중도"
    ]
    
    all_features = (basic_features + ratio_features + size_features + 
                   time_features + timing_features + volume_features + 
                   engineered_features)
    
    # 실제 존재하는 컬럼만 선택
    available_features = [col for col in all_features if col in df.columns]
    X = df[available_features].copy()
    
    # 결측치 처리
    X = X.replace([np.inf, -np.inf], 0).fillna(0)

    print(f"균형잡힌 Feature 수: {len(available_features)}")
    print(f"제거된 직접 누수 변수: {[col for col in direct_leakage if col in df.columns]}")
    print(f"포함된 Feature: {available_features[:10]}...")  # 처음 10개만 출력

    return X, y


# ===== 하이퍼파라미터 최적화 함수 (주석 처리) =====
# 이미 최적 파라미터를 찾았으므로 더 이상 그리드 서치를 실행하지 않습니다.
# 최적 파라미터: C=1, penalty='l2', solver='lbfgs', max_iter=1000, class_weight=None

# def optimize_logistic_regression(X_train_scaled, y_train):
#     """
#     LogisticRegression 하이퍼파라미터 최적화
#     """
#     print("🔍 LogisticRegression 하이퍼파라미터 최적화 중...")
#     
#     # 단계별 최적화 (더 안정적)
#     # 1단계: 기본 파라미터들
#     param_grid_1 = {
#         'C': [0.001, 0.01, 0.1, 1, 10, 100],
#         'penalty': ['l2'],  # 가장 안정적인 l2부터
#         'solver': ['lbfgs'],  # l2에 최적화된 solver
#         'class_weight': [None, 'balanced'],
#         'max_iter': [1000]
#     }
#     
#     cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
#     
#     # 1단계 최적화
#     base_model = LogisticRegression(random_state=42)
#     grid_search_1 = GridSearchCV(
#         base_model, 
#         param_grid_1,
#         cv=cv,
#         scoring='accuracy',
#         n_jobs=-1,
#         verbose=1
#     )
#     
#     grid_search_1.fit(X_train_scaled, y_train)
#     best_score_1 = grid_search_1.best_score_
#     best_params_1 = grid_search_1.best_params_
#     
#     print(f"1단계 최적 점수: {best_score_1:.4f}")
#     print(f"1단계 최적 파라미터: {best_params_1}")
#     
#     # 2단계: L1 정규화 시도
#     param_grid_2 = {
#         'C': [best_params_1['C'] * 0.1, best_params_1['C'], best_params_1['C'] * 10],
#         'penalty': ['l1'],
#         'solver': ['saga'],  # l1을 지원하는 solver
#         'class_weight': [best_params_1['class_weight']],
#         'max_iter': [2000]  # l1은 더 많은 반복이 필요할 수 있음
#     }
#     
#     grid_search_2 = GridSearchCV(
#         base_model,
#         param_grid_2,
#         cv=cv,
#         scoring='accuracy',
#         n_jobs=-1,
#         verbose=1
#     )
#     
#     grid_search_2.fit(X_train_scaled, y_train)
#     best_score_2 = grid_search_2.best_score_
#     best_params_2 = grid_search_2.best_params_
#     
#     print(f"2단계 최적 점수: {best_score_2:.4f}")
#     print(f"2단계 최적 파라미터: {best_params_2}")
#     
#     # 3단계: ElasticNet 시도
#     param_grid_3 = {
#         'C': [best_params_1['C'] * 0.1, best_params_1['C'], best_params_1['C'] * 10],
#         'penalty': ['elasticnet'],
#         'solver': ['saga'],
#         'l1_ratio': [0.1, 0.3, 0.5, 0.7, 0.9],
#         'class_weight': [best_params_1['class_weight']],
#         'max_iter': [2000]
#     }
#     
#     grid_search_3 = GridSearchCV(
#         base_model,
#         param_grid_3,
#         cv=cv,
#         scoring='accuracy',
#         n_jobs=-1,
#         verbose=1
#     )
#     
#     grid_search_3.fit(X_train_scaled, y_train)
#     best_score_3 = grid_search_3.best_score_
#     best_params_3 = grid_search_3.best_params_
#     
#     print(f"3단계 최적 점수: {best_score_3:.4f}")
#     print(f"3단계 최적 파라미터: {best_params_3}")
#     
#     # 최고 성능 선택
#     scores = [best_score_1, best_score_2, best_score_3]
#     params = [best_params_1, best_params_2, best_params_3]
#     estimators = [grid_search_1.best_estimator_, grid_search_2.best_estimator_, grid_search_3.best_estimator_]
#     
#     best_idx = np.argmax(scores)
#     final_best_score = scores[best_idx]
#     final_best_params = params[best_idx]
#     final_best_estimator = estimators[best_idx]
#     
#     print(f"\n✅ 최종 최적 하이퍼파라미터: {final_best_params}")
#     print(f"✅ 최종 최적 CV 점수: {final_best_score:.4f}")
#     
#     return final_best_estimator, final_best_params, final_best_score


def train_models(X_train_scaled, y_train):
    # ===== 최적 하이퍼파라미터로 LogisticRegression 직접 생성 =====
    # 그리드 서치 결과: C=1, penalty='l2', solver='lbfgs', max_iter=1000, class_weight=None
    print("✅ 최적 하이퍼파라미터로 LogisticRegression 학습 중...")
    
    best_lr = LogisticRegression(
        C=1,
        penalty='l2',
        solver='lbfgs',
        max_iter=1000,
        class_weight=None,
        random_state=42
    )
    
    best_lr.fit(X_train_scaled, y_train)
    
    best_lr_params = {
        'C': 1,
        'penalty': 'l2',
        'solver': 'lbfgs',
        'max_iter': 1000,
        'class_weight': None
    }
    
    # CV 점수 계산
    from sklearn.model_selection import cross_val_score, StratifiedKFold
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(best_lr, X_train_scaled, y_train, cv=cv, scoring='accuracy')
    best_lr_score = cv_scores.mean()
    
    print(f"✅ 최적 하이퍼파라미터: {best_lr_params}")
    print(f"✅ CV 점수: {best_lr_score:.4f}")
    
    # ===== 다른 모델들 (주석 처리) =====
    # # 2) RandomForest
    # rf_model = RandomForestClassifier(
    #     n_estimators=150,
    #     max_depth=10,
    #     min_samples_split=3,
    #     min_samples_leaf=1,
    #     class_weight='balanced',
    #     random_state=42
    # )
    
    # # 3) GradientBoosting
    # gb_model = GradientBoostingClassifier(
    #     n_estimators=100,
    #     max_depth=4,
    #     learning_rate=0.1,
    #     min_samples_split=5,
    #     min_samples_leaf=2,
    #     random_state=42
    # )
    
    # # 4) SVM
    # svm_model = SVC(
    #     C=1.0,
    #     kernel='rbf',
    #     class_weight='balanced',
    #     probability=True,
    #     random_state=42
    # )
    
    # # 5) 앙상블 모델
    # ensemble_model = VotingClassifier(
    #     estimators=[
    #         ('lr', best_lr),
    #         ('rf', rf_model),
    #         ('gb', gb_model),
    #         ('svm', svm_model)
    #     ],
    #     voting='soft'
    # )
    
    models = {
        "LogisticRegression_Optimized": best_lr,
        # "RandomForest_Enhanced": rf_model,
        # "GradientBoosting_Enhanced": gb_model,
        # "SVM": svm_model,
        # "Ensemble_VotingClassifier": ensemble_model
    }

    trained = {}
    optimization_info = {}

    for name, model in models.items():
        print(f"▶ Train: {name}")
        trained[name] = model
        
        # 최적화 정보 저장
        if name == "LogisticRegression_Optimized":
            optimization_info[name] = {
                'best_params': best_lr_params,
                'best_cv_score': best_lr_score
            }

    return trained, optimization_info


def main():
    print("=== TRAIN STEP ===")

    # 1) 데이터 로드
    X, y = load_data()

    # 2) Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 3) 개선된 전처리
    from sklearn.preprocessing import PowerTransformer, QuantileTransformer
    
    # 여러 스케일러 시도
    scalers = {
        'robust': RobustScaler(),
        'quantile': QuantileTransformer(n_quantiles=100, random_state=42),
        'power': PowerTransformer(method='yeo-johnson', standardize=True)
    }
    
    # 각 스케일러로 CV 성능 테스트
    best_scaler_name = 'robust'
    best_scaler_score = 0
    
    print("🔍 최적 스케일러 선택 중...")
    for scaler_name, scaler in scalers.items():
        X_train_temp = scaler.fit_transform(X_train)
        
        # 간단한 LogisticRegression으로 빠른 테스트
        temp_model = LogisticRegression(random_state=42, max_iter=1000)
        cv_scores = cross_val_score(temp_model, X_train_temp, y_train, 
                                  cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=42))
        avg_score = cv_scores.mean()
        
        print(f"  {scaler_name}: {avg_score:.4f}")
        
        if avg_score > best_scaler_score:
            best_scaler_score = avg_score
            best_scaler_name = scaler_name
    
    print(f"✅ 선택된 스케일러: {best_scaler_name} ({best_scaler_score:.4f})")
    
    # 최적 스케일러 사용
    scaler = scalers[best_scaler_name]
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 4) 모델 학습 (하이퍼파라미터 최적화 포함)
    models, optimization_info = train_models(X_train_scaled, y_train)

    # 5) Test 세트 분석
    print("\n🔍 Test 세트 특성 분석:")
    test_target_dist = pd.Series(y_test).value_counts(normalize=True).sort_index()
    train_target_dist = pd.Series(y_train).value_counts(normalize=True).sort_index()
    
    print("클래스 분포 비교:")
    for cls in ['A', 'B', 'C']:
        train_pct = train_target_dist.get(cls, 0) * 100
        test_pct = test_target_dist.get(cls, 0) * 100
        print(f"  {cls}등급: Train {train_pct:.1f}% vs Test {test_pct:.1f}%")

    # 6) Cross Validation 평가 (Test 세트 고려)
    print("\n🔄 Cross Validation 평가 (5-Fold + Test 특화):")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    cv_results = {}
    for name, model in models.items():
        # 전체 데이터에 대한 CV 점수
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
        
        # 단일 train/test 점수
        train_pred = model.predict(X_train_scaled)
        test_pred = model.predict(X_test_scaled)
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        
        # Test 세트에서 클래스별 성능
        from sklearn.metrics import classification_report
        test_report = classification_report(y_test, test_pred, output_dict=True)
        
        cv_results[name] = {
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'train_acc': train_acc,
            'test_acc': test_acc,
            'test_report': test_report
        }
        
        print(f"  {name}:")
        print(f"    - CV Mean:        {cv_scores.mean():.4f} (±{cv_scores.std():.4f})")
        print(f"    - Train Accuracy: {train_acc:.4f}")
        print(f"    - Test Accuracy:  {test_acc:.4f}")
        print(f"    - 과적합 정도:     {train_acc - test_acc:.4f}")
        print(f"    - CV vs Test:     {cv_scores.mean() - test_acc:.4f}")
        
        # 클래스별 F1 점수 출력
        for cls in ['A', 'B', 'C']:
            if cls in test_report:
                f1 = test_report[cls]['f1-score']
                print(f"    - {cls}등급 F1:      {f1:.4f}")
        print()

    # 6) 최적화 정보 출력
    print("\n🎯 하이퍼파라미터 최적화 결과:")
    for model_name, info in optimization_info.items():
        print(f"  {model_name}:")
        print(f"    - 최적 파라미터: {info['best_params']}")
        print(f"    - 최적 CV 점수: {info['best_cv_score']:.4f}")

    # 7) 모델 + 스케일러 저장
    Path("apps/reco/models/trust_model/save_models").mkdir(parents=True, exist_ok=True)
    with open(MODEL_TEMP_PATH, "wb") as f:
        pickle.dump(
            {
                "models": models,
                "scaler": scaler,
                "X_train_scaled": X_train_scaled,  # 훈련 데이터도 저장
                "y_train": y_train,
                "X_test_scaled": X_test_scaled,
                "y_test": y_test,
                "feature_names": list(X.columns),
                "cv_results": cv_results,  # CV 결과도 저장
                "optimization_info": optimization_info,  # 최적화 정보도 저장
            },
            f,
        )

    print("\n✓ 학습 완료, temp 모델 저장:", MODEL_TEMP_PATH)
    
    # 8) 최고 CV 성능 모델 출력
    best_cv_model = max(cv_results.keys(), key=lambda k: cv_results[k]['cv_mean'])
    print(f"🏆 최고 CV 성능 모델: {best_cv_model} ({cv_results[best_cv_model]['cv_mean']:.4f})")


if __name__ == "__main__":
    main()
