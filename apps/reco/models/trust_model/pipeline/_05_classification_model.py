import os
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import RandomForestClassifier

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")


def train_classification(df):
    print("\n🤖 [4단계] RandomForest 분류 모델 학습")

    df = df.copy()

    # 사용 Feature 지정
    # 데이터 누수 방지: 거래성사율, 거래완료비율, 거래밀도, 일평균거래 제외
    # 일평균거래 제거 이유: 거래완료/영업일수 = 간접적 누수
    features = [
        "거래완료", "등록매물", "총매물수",
        "등록비율", "규모지수",  # 기본 피처
        "지역권평균성사율",      # 지역 평균 (rule_score에서 생성)
        "지역내백분위",          # 지역 내 상대적 위치 (순위 대신 백분위만)
        "지역중개사수",          # 지역 규모
        "보증보험유효",          # 보증보험 여부
        "영업일수"               # 영업 기간
    ]

    # 컬럼 존재 여부 확인
    missing = [col for col in features if col not in df.columns]
    if missing:
        raise ValueError(f"❌ 누락된 피처: {missing}")

    X = df[features]
    y = df["grade"].astype(str)

    print(f"✅ 학습 데이터 준비 완료")
    print(f"   - 사용 피처: {len(features)}개")
    print(f"   - 타겟: grade (D, C, B, A, S)")
    print(f"   - 클래스 분포:")
    for grade, count in y.value_counts().sort_index().items():
        print(f"      {grade}: {count}개 ({count/len(y)*100:.1f}%)")

    # Train / Test Split 
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\n✅ 데이터 분할 완료 (Stratified)")
    print(f"   - 학습 데이터: {len(X_train)}개 (80%)")
    print(f"   - 테스트 데이터: {len(X_test)}개 (20%)")

    # RobustScaler - 이상치(outlier)에 덜 민감한 스케일링
    scaler = RobustScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    print(f"\n✅ RobustScaler 적용 완료")

    # 모델 학습 (단순화 & 일반화 강화)
    model = RandomForestClassifier(
        n_estimators=50,         # 100 → 50 (트리 수 대폭 감소)
        max_depth=6,             # 8 → 6 (더 얕게)
        min_samples_split=20,    # 15 → 20 (더 엄격)
        min_samples_leaf=10,     # 8 → 10 (더 엄격)
        max_features='sqrt',     # 피처 샘플링
        class_weight='balanced', # 클래스 불균형 처리
        random_state=42
    )
    model.fit(X_train_s, y_train)

    print(f"\n✅ RandomForest 분류 모델 학습 완료")
    print(f"   - 트리 개수: 50개 (단순화)")
    print(f"   - 최대 깊이: 6 (얕은 트리)")
    print(f"   - 클래스 가중치: 균형 조정")
    print(f"   - 일반화 우선 설정")

    # 평가
    pred = model.predict(X_test_s)
    acc = accuracy_score(y_test, pred)
    f1 = f1_score(y_test, pred, average="macro")
    train_pred = model.predict(X_train_s)
    train_acc = accuracy_score(y_train, train_pred)
    overfit_gap = train_acc - acc

    print(f"   ✅ 학습 완료 | Accuracy: {acc:.2%} | F1: {f1:.2%} | 과적합: {overfit_gap:.2%}")

    # 결과 저장
    df["clf_pred"] = model.predict(scaler.transform(X))
    
    clf_proba = model.predict_proba(scaler.transform(X))
    grade_labels = model.classes_
    s_idx = list(grade_labels).index('S') if 'S' in grade_labels else -1
    df["clf_score"] = clf_proba[:, s_idx] if s_idx >= 0 else clf_proba.max(axis=1)

    # 모델 저장
    os.makedirs(MODEL_DIR, exist_ok=True)

    model_package = {
        'model': model,
        'scaler': scaler,
        'features': features,
        'metadata': {
            'n_estimators': 50,
            'max_depth': 6,
            'accuracy': acc,
            'f1_score': f1
        }
    }
    
    model_path = os.path.join(MODEL_DIR, "trust_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model_package, f)

    print(f"   💾 모델 저장: trust_model.pkl")

    return df
