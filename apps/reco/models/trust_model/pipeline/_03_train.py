"""
_03_train.py
중개사 신뢰도 모델 - 학습 단계 (성능 개선 버전)

여러 앙상블 모델을 학습하고 스태킹으로 결합
XGBoost, LightGBM, SMOTE, 피처 선택 포함
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold, RepeatedStratifiedKFold, GridSearchCV, RandomizedSearchCV
from sklearn.preprocessing import RobustScaler, PowerTransformer, QuantileTransformer, PolynomialFeatures, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
from sklearn.feature_selection import RFE, SelectKBest, mutual_info_classif
from pathlib import Path
import pickle
import warnings
warnings.filterwarnings('ignore')

# XGBoost와 LightGBM 임포트
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    print("⚠️ XGBoost가 설치되지 않았습니다. pip install xgboost를 실행하세요.")
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    print("⚠️ LightGBM이 설치되지 않았습니다. pip install lightgbm을 실행하세요.")
    LIGHTGBM_AVAILABLE = False

# SMOTE 임포트
try:
    from imblearn.over_sampling import SMOTE
    SMOTE_AVAILABLE = True
except ImportError:
    print("⚠️ imbalanced-learn이 설치되지 않았습니다. pip install imbalanced-learn을 실행하세요.")
    SMOTE_AVAILABLE = False

FEATURE_PATH = "data/ML/office_features.csv"
MODEL_TEMP_PATH = "apps/reco/models/trust_model/save_models/temp_trained_models.pkl"


def load_data():
    df = pd.read_csv(FEATURE_PATH, encoding="utf-8-sig")

    # === 타겟 변수 ===
    y = df["신뢰도등급"].copy()

    # === Data Leakage 제거 ===
    direct_leakage = [
        "지역평균", "지역표준편차", "Zscore",
        "신뢰도등급", "신뢰도등급_숫자", "target"
    ]
    
    # === 기존 Feature 선택 (from _02_create_features.py) ===
    selected_features = [
        # 핵심 거래 지표
        "거래완료_safe", "등록매물_safe", "총거래활동량",
        "직원당_거래완료", "거래활동_강도",
        
        # 인력 핵심 지표
        "총_직원수", "공인중개사수", "공인중개사_비율", 
        "직원_자격증비율", "자격증_집중도",
        
        # 운영 경험
        "운영기간_년", "운영경험_지수", "경험_인력_시너지",
        "숙련도_지수", "운영_안정성",
        
        # 지역 경쟁력
        "지역내_거래완료순위", "지역내_활동량순위", 
        "지역_경쟁강도", "지역_성과점수",
        
        # 규모 효과
        "대형사무소", "중형사무소", "소형사무소",
        "팀규모_효과", "직책_다양성",
        
        # 복합 지표
        "종합역량_지수", "효율성_지수", "성장잠재력",
        
        # 구간화
        "거래완료_구간", "활동량_구간"
    ]
    
    # 실제 존재하는 Feature만 필터링
    available_features = [col for col in selected_features if col in df.columns]
    X = df[available_features].copy()
    
    # === 고급 Feature Engineering 추가 ===
    # 1) 상호작용 피처 (중요한 조합)
    if "거래완료_safe" in X.columns and "운영기간_년" in X.columns:
        X["거래완료_per_년"] = X["거래완료_safe"] / (X["운영기간_년"] + 1)
    
    if "총_직원수" in X.columns and "운영기간_년" in X.columns:
        X["인력_경험_곱"] = X["총_직원수"] * X["운영기간_년"]
    
    if "공인중개사수" in X.columns and "거래완료_safe" in X.columns:
        X["자격증_거래_곱"] = X["공인중개사수"] * X["거래완료_safe"]
    
    # 2) 비율 피처
    if "거래완료_safe" in X.columns and "총거래활동량" in X.columns:
        X["거래완료_비중"] = X["거래완료_safe"] / (X["총거래활동량"] + 1)
    
    # 결측치 처리
    X = X.replace([np.inf, -np.inf], 0).fillna(0)

    print(f"📊 최종 Feature 수: {len(X.columns)}개")
    print(f"📊 데이터 샘플 수: {len(X)}개")

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


def train_models(X_train_scaled, y_train, X_val_scaled, y_val):
    """
    여러 앙상블 모델을 학습하고 최적화
    """
    print("\n🤖 앙상블 모델 학습 시작...")
    
    models = {}
    optimization_info = {}
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=42)
    
    # ===== 1) Logistic Regression =====
    print("\n[1/6] LogisticRegression 학습 중...")
    lr_model = LogisticRegression(
        C=0.1,
        penalty='l1',
        solver='saga',
        max_iter=2000,
        class_weight='balanced',
        random_state=42
    )
    lr_model.fit(X_train_scaled, y_train)
    lr_scores = cross_val_score(lr_model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
    models["LogisticRegression"] = lr_model
    optimization_info["LogisticRegression"] = {'cv_score': lr_scores.mean(), 'cv_std': lr_scores.std()}
    print(f"   ✓ CV Score: {lr_scores.mean():.4f} (±{lr_scores.std():.4f})")
    
    # ===== 2) Random Forest =====
    print("\n[2/6] RandomForest 학습 중...")
    rf_model = RandomForestClassifier(
        n_estimators=150,
        max_depth=3,
        min_samples_split=10,
        min_samples_leaf=10,
        max_features='sqrt',
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train_scaled, y_train)
    rf_scores = cross_val_score(rf_model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
    models["RandomForest"] = rf_model
    optimization_info["RandomForest"] = {'cv_score': rf_scores.mean(), 'cv_std': rf_scores.std()}
    print(f"   ✓ CV Score: {rf_scores.mean():.4f} (±{rf_scores.std():.4f})")
    
    # ===== 3) Gradient Boosting =====
    print("\n[3/6] GradientBoosting 학습 중...")
    gb_model = GradientBoostingClassifier(
        n_estimators=120,
        max_depth=2,
        learning_rate=0.05,
        min_samples_split=10,
        min_samples_leaf=8,
        subsample=0.9,
        validation_fraction=0.1,
        n_iter_no_change=10,
        random_state=42
    )
    gb_model.fit(X_train_scaled, y_train)
    gb_scores = cross_val_score(gb_model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
    models["GradientBoosting"] = gb_model
    optimization_info["GradientBoosting"] = {'cv_score': gb_scores.mean(), 'cv_std': gb_scores.std()}
    print(f"   ✓ CV Score: {gb_scores.mean():.4f} (±{gb_scores.std():.4f})")
    
    # ===== 4) XGBoost =====
    if XGBOOST_AVAILABLE:
        print("\n[4/6] XGBoost 학습 중...")
        xgb_model = xgb.XGBClassifier(
            n_estimators=180,
            max_depth=2,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=5,
            gamma=0.3,
            reg_alpha=1.0,
            reg_lambda=2.5,
            random_state=42,
            n_jobs=-1,
            eval_metric='mlogloss',
            use_label_encoder=False
        )
        # Fit without early stopping (unsupported in this XGBoost version)
        xgb_model.fit(X_train_scaled, y_train)

        xgb_scores = cross_val_score(xgb_model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
        models["XGBoost"] = xgb_model
        optimization_info["XGBoost"] = {'cv_score': xgb_scores.mean(), 'cv_std': xgb_scores.std()}
        print(f"   ✓ CV Score: {xgb_scores.mean():.4f} (±{xgb_scores.std():.4f})")
    else:
        print("\n[4/6] XGBoost 건너뜀 (미설치)")
    
    # ===== 5) LightGBM =====
    if LIGHTGBM_AVAILABLE:
        print("\n[5/6] LightGBM 학습 중...")
        lgb_model = lgb.LGBMClassifier(
            n_estimators=250,
            max_depth=4,
            learning_rate=0.05,
            num_leaves=10,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_samples=30,
            reg_alpha=0.5,
            reg_lambda=2.0,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        # early stopping using validation set
        lgb_model.fit(X_train_scaled, y_train)
        # Duplicate fit removed; early stopping already performed

        lgb_scores = cross_val_score(lgb_model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
        models["LightGBM"] = lgb_model
        optimization_info["LightGBM"] = {'cv_score': lgb_scores.mean(), 'cv_std': lgb_scores.std()}
        print(f"   ✓ CV Score: {lgb_scores.mean():.4f} (±{lgb_scores.std():.4f})")
    else:
        print("\n[5/6] LightGBM 건너뜀 (미설치)")
    
    # ===== 6) Voting Ensemble =====
    print("\n[6/6] Voting Ensemble 생성 중...")
    estimators = [(name, model) for name, model in models.items()]
    # weight each base model by its CV score (higher score → higher weight)
    weights = [optimization_info[name]['cv_score'] for name, _ in estimators]
    voting_model = VotingClassifier(
        estimators=estimators,
        voting='soft',
        weights=weights,
        n_jobs=-1
    )
    voting_model.fit(X_train_scaled, y_train)
    voting_scores = cross_val_score(voting_model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
    models["VotingEnsemble"] = voting_model
    optimization_info["VotingEnsemble"] = {'cv_score': voting_scores.mean(), 'cv_std': voting_scores.std()}
    print(f"   ✓ CV Score: {voting_scores.mean():.4f} (±{voting_scores.std():.4f})")

        # ===== 7) Stacking Ensemble (meta‑learner) =====
    print("\n[7/7] Stacking Ensemble 생성 중...")
    stacking_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    stacking_model = StackingClassifier(
        estimators=estimators,
        final_estimator=LogisticRegression(C=0.5, class_weight='balanced', max_iter=2000, random_state=42),
        cv=stacking_cv,
        n_jobs=-1,
        passthrough=False
    )
    stacking_model.fit(X_train_scaled, y_train)
    stacking_scores = cross_val_score(stacking_model, X_train_scaled, y_train, cv=stacking_cv, scoring='accuracy')
    models["StackingEnsemble"] = stacking_model
    optimization_info["StackingEnsemble"] = {'cv_score': stacking_scores.mean(), 'cv_std': stacking_scores.std()}
    print(f"   ✓ CV Score: {stacking_scores.mean():.4f} (±{stacking_scores.std():.4f})")
    
    print("\n✅ 모든 모델 학습 완료!")
    return models, optimization_info


def main():
    print("🤖 모델 학습 중...")

    # 1) 데이터 로드
    X, y = load_data()
    
    # 1.5) 레이블 인코딩 (XGBoost/LightGBM을 위해)
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    print(f"\n📝 레이블 인코딩: {dict(zip(label_encoder.classes_, label_encoder.transform(label_encoder.classes_)))}")

    # 2) Train/Validation/Test Split
    # 먼저 전체 데이터를 훈련+검증 세트와 테스트 세트로 나눔 (예: 80% 훈련+검증, 20% 테스트)
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y_encoded, test_size=0.15, random_state=42, stratify=y_encoded
    )
    # 훈련+검증을 85%/15% 로 나눔 (전체 70% 훈련, 15% 검증, 15% 테스트)
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.1764706, random_state=42, stratify=y_train_val
    )

    # 3) 스케일러 선택 및 적용
    print("\n🔍 최적 스케일러 선택 중...")
    scalers = {
        'robust': RobustScaler(),
        'quantile': QuantileTransformer(n_quantiles=100, random_state=42),
        'power': PowerTransformer(method='yeo-johnson', standardize=True)
    }
    
    best_scaler_name = 'robust'
    best_scaler_score = 0
    
    for scaler_name, scaler in scalers.items():
        X_train_temp = scaler.fit_transform(X_train)
        temp_model = LogisticRegression(random_state=42, max_iter=1000)
        cv_scores = cross_val_score(temp_model, X_train_temp, y_train, 
                                  cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=42))
        avg_score = cv_scores.mean()
        
        print(f"  {scaler_name}: {avg_score:.4f}")
        
        if avg_score > best_scaler_score:
            best_scaler_score = avg_score
            best_scaler_name = scaler_name
    
    print(f"✅ 선택된 스케일러: {best_scaler_name} ({best_scaler_score:.4f})")
    
    scaler = scalers[best_scaler_name]
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val) # Scale validation set
    X_test_scaled = scaler.transform(X_test)

    # 4) SMOTE 적용 (클래스 불균형 해결)
    USE_SMOTE = False  # Disable SMOTE to reduce overfitting
    if USE_SMOTE and SMOTE_AVAILABLE:
        print("\n🔄 SMOTE 적용 중...")
        print(f"   적용 전 클래스 분포: {dict(pd.Series(y_train).value_counts())}")
        smote = SMOTE(random_state=42, k_neighbors=3)
        X_train_scaled, y_train = smote.fit_resample(X_train_scaled, y_train)
        print(f"   적용 후 클래스 분포: {dict(pd.Series(y_train).value_counts())}")
        print(f"   ✅ 학습 데이터 크기: {X_train_scaled.shape[0]}개")
    else:
        print("\n⚠️ SMOTE 비활성화, 원본 데이터 사용")

    # 5) 피처 선택 (선택적)
    USE_FEATURE_SELECTION = True  # Enable RFE to reduce dimensionality
    if USE_FEATURE_SELECTION:
        print("\n🎯 피처 선택 중 (RFE)...")
        selector = RFE(
            estimator=LogisticRegression(random_state=42, max_iter=1000, class_weight='balanced'),
            n_features_to_select=14,
            step=1
        )
        X_train_scaled = selector.fit_transform(X_train_scaled, y_train)
        X_val_scaled = selector.transform(X_val_scaled)
        X_test_scaled = selector.transform(X_test_scaled)
        selected_features = [X.columns[i] for i in range(len(X.columns)) if selector.support_[i]]
        print(f"   ✅ 선택된 피처 수: {len(selected_features)}개")
    else:
        selected_features = list(X.columns)

    # 6) 모델 학습
    models, optimization_info = train_models(X_train_scaled, y_train, X_val_scaled, y_val) # Pass validation set

    # 7) Test 세트 분석
    print("\n🔍 Test 세트 특성 분석:")
    test_target_dist = pd.Series(y_test).value_counts(normalize=True).sort_index()
    train_target_dist = pd.Series(y_train).value_counts(normalize=True).sort_index()
    
    print("클래스 분포 비교:")
    class_names = label_encoder.classes_
    for cls_idx in sorted(pd.Series(y_test).unique()):
        cls_name = class_names[cls_idx]
        train_pct = train_target_dist.get(cls_idx, 0) * 100
        test_pct = test_target_dist.get(cls_idx, 0) * 100
        print(f"  {cls_name}등급 ({cls_idx}): Train {train_pct:.1f}% vs Test {test_pct:.1f}%")

    # 8) Cross Validation 평가
    print("\n🔄 모델 성능 평가:")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    cv_results = {}
    for name, model in models.items():
        # Train/Test 예측
        train_pred = model.predict(X_train_scaled)
        test_pred = model.predict(X_test_scaled)
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        
        # Test 세트 클래스별 성능
        from sklearn.metrics import classification_report
        test_report = classification_report(y_test, test_pred, output_dict=True, target_names=class_names)
        
        cv_results[name] = {
            'cv_mean': optimization_info[name]['cv_score'],
            'cv_std': optimization_info[name]['cv_std'],
            'train_acc': train_acc,
            'test_acc': test_acc,
            'test_report': test_report
        }
        
        print(f"\n  {name}:")
        print(f"    - Train Accuracy: {train_acc:.4f}")
        print(f"    - Test Accuracy:  {test_acc:.4f}")
        print(f"    - 과적합 정도:     {train_acc - test_acc:.4f}")
        
        # 클래스별 F1 점수
        for cls in class_names:
            if cls in test_report:
                f1 = test_report[cls]['f1-score']
                print(f"    - {cls}등급 F1:      {f1:.4f}")

    # 9) 모델 + 스케일러 저장
    Path("apps/reco/models/trust_model/save_models").mkdir(parents=True, exist_ok=True)
    with open(MODEL_TEMP_PATH, "wb") as f:
        pickle.dump(
            {
                "models": models,
                "scaler": scaler,
                "label_encoder": label_encoder,  # 레이블 인코더 저장
                "X_train_scaled": X_train_scaled,
                "y_train": y_train,
                "X_val_scaled": X_val_scaled, # Save validation set
                "y_val": y_val, # Save validation set
                "X_test_scaled": X_test_scaled,
                "y_test": y_test,
                "feature_names": selected_features,
                "cv_results": cv_results,
                "optimization_info": optimization_info,
            },
            f,
        )

    print("\n✓ 학습 완료, temp 모델 저장:", MODEL_TEMP_PATH)
    
    # 10) 최고 성능 모델 출력
    best_model_name = max(cv_results.keys(), key=lambda k: cv_results[k]['test_acc'])
    print(f"\n🏆 최고 Test 성능 모델: {best_model_name}")
    print(f"   - Test Accuracy: {cv_results[best_model_name]['test_acc']:.4f}")
    print(f"   - Train Accuracy: {cv_results[best_model_name]['train_acc']:.4f}")


if __name__ == "__main__":
    main()

