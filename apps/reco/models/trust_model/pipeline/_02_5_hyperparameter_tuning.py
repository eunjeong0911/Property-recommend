"""
하이퍼파라미터 튜닝
GridSearchCV를 사용하여 LogisticRegression의 최적 하이퍼파라미터 탐색
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import pickle
from pathlib import Path

FEATURE_PATH = "data/ML/office_features.csv"


def load_data():
    """데이터 로드"""
    print("📂 데이터 로드 중...")
    df = pd.read_csv(FEATURE_PATH, encoding="utf-8-sig")
    
    # 타겟 변수
    y = df["신뢰도등급"].copy()
    
    # Feature 선택 (15개)
    selected_features = [
        "등록매물_log", "총거래활동량_log",
        "총_직원수", "공인중개사수", "공인중개사_비율",
        "운영기간_년", "운영경험_지수", "숙련도_지수", "운영_안정성",
        "대형사무소", "직책_다양성",
        "대표_공인중개사", "대표_법인", "대표_중개인", "대표_중개보조원"
    ]
    
    # 실제 존재하는 Feature만 필터링
    available_features = [col for col in selected_features if col in df.columns]
    X = df[available_features].copy()
    
    # 모든 컬럼을 숫자형으로 강제 변환
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')
    
    # 결측치 처리
    X = X.replace([np.inf, -np.inf], 0).fillna(0)
    
    print(f"   ✅ 피처 수: {len(X.columns)}개")
    print(f"   ✅ 데이터 수: {len(X)}개")
    
    return X, y


def hyperparameter_tuning(X, y):
    """하이퍼파라미터 튜닝"""
    print("\n" + "=" * 70)
    print("🔍 하이퍼파라미터 튜닝 시작")
    print("=" * 70)
    
    # 스케일링
    print("\n📊 데이터 스케일링 중...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 하이퍼파라미터 그리드 정의
    param_grid = {
        'C': [0.001, 0.01, 0.1, 1, 10, 100],  # 정규화 강도
        'penalty': ['l1', 'l2'],  # 정규화 타입
        'solver': ['liblinear', 'saga'],  # l1을 지원하는 solver
        'class_weight': [None, 'balanced'],  # 클래스 가중치
        'max_iter': [1000, 2000]  # 최대 반복 횟수
    }
    
    print(f"\n🔧 탐색할 하이퍼파라미터 조합: {len(param_grid['C']) * len(param_grid['penalty']) * len(param_grid['solver']) * len(param_grid['class_weight']) * len(param_grid['max_iter'])}개")
    print("\n📋 탐색 범위:")
    for param, values in param_grid.items():
        print(f"   - {param}: {values}")
    
    # GridSearchCV 설정
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    grid_search = GridSearchCV(
        estimator=LogisticRegression(random_state=42),
        param_grid=param_grid,
        cv=cv,
        scoring='accuracy',
        n_jobs=-1,  # 모든 CPU 코어 사용
        verbose=2,
        return_train_score=True
    )
    
    # 그리드 서치 실행
    print("\n🚀 그리드 서치 실행 중... (시간이 걸릴 수 있습니다)")
    grid_search.fit(X_scaled, y)
    
    # 결과 출력
    print("\n" + "=" * 70)
    print("✅ 하이퍼파라미터 튜닝 완료!")
    print("=" * 70)
    
    print(f"\n🏆 최고 CV 정확도: {grid_search.best_score_:.4f}")
    print(f"\n📌 최적 하이퍼파라미터:")
    for param, value in grid_search.best_params_.items():
        print(f"   - {param}: {value}")
    
    # 상위 10개 결과 출력
    results_df = pd.DataFrame(grid_search.cv_results_)
    results_df = results_df.sort_values('rank_test_score')
    
    print(f"\n📊 상위 10개 하이퍼파라미터 조합:")
    print("-" * 100)
    
    top_10 = results_df.head(10)
    for idx, row in top_10.iterrows():
        print(f"\n순위 {int(row['rank_test_score'])}: CV 정확도 = {row['mean_test_score']:.4f} (±{row['std_test_score']:.4f})")
        print(f"   C={row['param_C']}, penalty={row['param_penalty']}, solver={row['param_solver']}, "
              f"class_weight={row['param_class_weight']}, max_iter={row['param_max_iter']}")
    
    # 결과 저장
    results_dir = Path("apps/reco/models/trust_model/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    results_path = results_dir / "hyperparameter_tuning_results.csv"
    results_df.to_csv(results_path, index=False, encoding='utf-8-sig')
    print(f"\n💾 전체 결과 저장: {results_path}")
    
    # 최적 모델 저장
    best_model = grid_search.best_estimator_
    best_model_path = Path("apps/reco/models/trust_model/save_models/best_hyperparameter_model.pkl")
    
    with open(best_model_path, 'wb') as f:
        pickle.dump({
            'model': best_model,
            'scaler': scaler,
            'best_params': grid_search.best_params_,
            'best_score': grid_search.best_score_,
            'feature_names': list(X.columns)
        }, f)
    
    print(f"💾 최적 모델 저장: {best_model_path}")
    
    return grid_search.best_estimator_, grid_search.best_params_, grid_search.best_score_


def evaluate_best_model(model, X, y):
    """최적 모델 평가"""
    print("\n" + "=" * 70)
    print("📊 최적 모델 성능 평가")
    print("=" * 70)
    
    # 스케일링
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 예측
    y_pred = model.predict(X_scaled)
    accuracy = accuracy_score(y, y_pred)
    
    print(f"\n전체 데이터 정확도: {accuracy:.4f}")
    print("\n분류 리포트:")
    print(classification_report(y, y_pred))


def main():
    """메인 실행 함수"""
    # 데이터 로드
    X, y = load_data()
    
    # 하이퍼파라미터 튜닝
    best_model, best_params, best_score = hyperparameter_tuning(X, y)
    
    # 최적 모델 평가
    evaluate_best_model(best_model, X, y)
    
    print("\n" + "=" * 70)
    print("🎉 하이퍼파라미터 튜닝 완료!")
    print("=" * 70)
    print("\n💡 다음 단계:")
    print("   1. 최적 하이퍼파라미터를 _03_train.py에 적용")
    print("   2. run_all.py 실행하여 최종 모델 학습")
    print("\n📌 권장 하이퍼파라미터:")
    for param, value in best_params.items():
        print(f"   {param}={value}")


if __name__ == "__main__":
    main()
