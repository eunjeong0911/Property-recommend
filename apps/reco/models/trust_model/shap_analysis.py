"""
shap_analysis.py

- 다중분류 모델 (voting_ensemble.pkl)
- 이진분류 모델 (voting_ensemble_binary.pkl)

에 대해 SHAP 값 계산 + 주요 피처 중요도 확인용 스크립트.

실행 방법 (프로젝트 루트 기준):

    # 1) 가상환경 활성화
    .\.venv\Scripts\Activate.ps1

    # 2) trust_model 폴더로 이동
    cd apps/reco/models/trust_model

    # 3) SHAP 분석 실행
    python shap_analysis.py

필요:
    pip install shap
"""

import pickle
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import shap

# ✅ 한글 폰트 설정 (Windows 기준: 맑은 고딕)
from matplotlib import font_manager, rc

font_path = r"C:\Windows\Fonts\malgun.ttf"  # 윈도우 기본 한글 폰트
font_name = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font_name)

# ✅ 마이너스 깨짐 방지
matplotlib.rcParams['axes.unicode_minus'] = False

# -----------------------------------------------------------------------------
# 경로 설정
# -----------------------------------------------------------------------------
# 현재 파일: .../SKN18-FINAL-1TEAM/apps/reco/models/trust_model/shap_analysis.py
BASE_DIR = Path(__file__).resolve().parent              # trust_model
PROJECT_ROOT = BASE_DIR.parents[3]                      # SKN18-FINAL-1TEAM

# trust_model 폴더를 import path에 추가 (로컬 모듈 import용)
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# CSV 경로 (run_all 계열과 동일)
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "seoul_broker_merged.csv"

# 모델 저장 경로 (run_all.py, run_all_binary.py와 통일: trust_model/models)
MODEL_DIR = BASE_DIR / "models"


# -----------------------------------------------------------------------------
# 데이터 로드 & 피처 엔지니어링
# -----------------------------------------------------------------------------
def load_data() -> pd.DataFrame:
    """원본 CSV 로드"""
    print(f"📂 CSV 직접 로드: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    return df


# add_features 가져오기 (run_all.py와 동일한 방식)
try:
    from _02_feature_engineering import add_features
except ImportError:
    # 혹시 pipeline 폴더에 있을 경우 대비
    from pipeline._02_feature_engineering import add_features

# binary target 생성 함수는 있으면 쓰고, 없으면 패스 (SHAP에는 꼭 필요는 X)
try:
    from _0A_create_target import create_binary_target
    HAS_BINARY_TARGET = True
except ImportError:
    HAS_BINARY_TARGET = False
    print("⚠️ _0A_create_target 모듈을 찾을 수 없습니다. "
          "이진 타겟 생성 없이 피처 만 사용합니다.")


def prepare_feature_data() -> pd.DataFrame:
    """
    SHAP 계산용 데이터 준비:
    - 원본 CSV 로드
    - 날짜 컬럼 dtype 변환
    - 보증보험유효 생성 (학습 파이프라인과 동일 의미)
    - add_features(df) 호출로 17개 피처 생성
    """
    df = load_data().copy()

    # 1) 날짜 컬럼을 datetime으로 변환 (add_features 내부 계산 대비)
    date_cols = ["registDe", "estbsBeginDe", "estbsEndDe", "lastUpdtDt"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # 2) 보증보험유효 생성 (estbsEndDe 기준)
    if "estbsEndDe" in df.columns:
        today = pd.Timestamp.today().normalize()
        df["보증보험유효"] = (df["estbsEndDe"] >= today).astype(int)
    else:
        df["보증보험유효"] = 0

    # 3) (선택) 이진 타겟 생성 함수가 있으면 한 번 태워줘도 됨
    if HAS_BINARY_TARGET:
        try:
            df = create_binary_target(df)
        except Exception as e:
            print(f"⚠️ create_binary_target 실행 중 오류 (무시하고 진행): {e}")

    # 4) 피처 엔지니어링 (영업년수, 지역 피처, 파생 피처 등 17개 생성)
    df = add_features(df)

    return df


# -----------------------------------------------------------------------------
# 1) 다중분류 SHAP (voting_ensemble.pkl)
# -----------------------------------------------------------------------------
def shap_multiclass(sample_size: int = 300, target_label: str = "A") -> None:
    """
    다중분류(voting_ensemble.pkl)에 대해 SHAP 값 계산.

    Parameters
    ----------
    sample_size : int
        SHAP 계산에 사용할 샘플 수 (너무 크면 느려짐).
    target_label : str
        'A', 'B', 'C' 중 SHAP을 보고 싶은 클래스 라벨.
    """
    model_path = MODEL_DIR / "voting_ensemble.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"❌ 다중분류 모델 파일이 없습니다: {model_path}")

    print(f"\n📦 다중분류 모델 로드: {model_path}")
    with open(model_path, "rb") as f:
        model_package = pickle.load(f)

    ensemble = model_package["ensemble"]
    scaler = model_package["scaler"]
    features = model_package["features"]
    metadata = model_package.get("metadata", {})
    label_encoder = model_package.get("label_encoder", None)

    print(f"   - 사용 피처 수: {len(features)}개")
    print(f"   - 메타데이터: classes = {metadata.get('classes')}")

    # 데이터 준비
    df = prepare_feature_data()

    # 🔐 방어: 누락된 피처 있으면 0으로 채워서라도 맞춰줌
    missing = [col for col in features if col not in df.columns]
    if missing:
        print(f"⚠️ SHAP용 피처 누락: {missing} → 0으로 채워서 사용")
        for col in missing:
            df[col] = 0

    X = df[features]
    X_s = scaler.transform(X)

    # 샘플링
    n = len(X_s)
    if sample_size is not None and sample_size < n:
        idx = np.random.choice(n, size=sample_size, replace=False)
        X_sample = X_s[idx]
        print(f"   - SHAP 계산용 샘플: {sample_size}/{n}")
    else:
        X_sample = X_s
        print(f"   - SHAP 계산용 샘플: 전체 {n}개 사용")

    X_df_sample = pd.DataFrame(X_sample, columns=features)

    # base 모델 선택 (xgb 우선 → rf)
    if hasattr(ensemble, "named_estimators_"):
        estimators = ensemble.named_estimators_
    else:
        raise RuntimeError("VotingClassifier에 named_estimators_ 속성이 없습니다.")

    if "xgb" in estimators:
        base_model = estimators["xgb"]
        base_name = "XGBoost"
    elif "rf" in estimators:
        base_model = estimators["rf"]
        base_name = "RandomForest"
    else:
        name0, base_model = list(estimators.items())[0]
        base_name = name0

    print(f"\n🌳 SHAP 기준 모델: {base_name} (multi-class)")

    explainer = shap.TreeExplainer(base_model)
    shap_values = explainer.shap_values(X_sample)

    # 다중분류: shap_values는 클래스별 리스트
    if label_encoder is not None:
        class_index = int(label_encoder.transform([target_label])[0])
        class_names = list(label_encoder.classes_)
    else:
        class_names = list(ensemble.classes_)
        class_index = class_names.index(target_label)

    print(f"   - 대상 클래스 라벨: {target_label} (index={class_index})")
    print(f"   - 전체 클래스: {class_names}")

    shap_class = shap_values[class_index]

    # 1) 요약(bar) 플롯
    plt.figure(figsize=(10, 6))
    shap.summary_plot(
        shap_class,
        X_df_sample,
        plot_type="bar",
        show=False,
    )
    plt.title(f"SHAP Feature Importance (Multi-class, class={target_label})")
    plt.tight_layout()
    plt.show()

    # 2) 비즈웜 플롯
    plt.figure(figsize=(10, 6))
    shap.summary_plot(
        shap_class,
        X_df_sample,
        show=False,
    )
    plt.title(f"SHAP Summary Plot (Multi-class, class={target_label})")
    plt.tight_layout()
    plt.show()


# -----------------------------------------------------------------------------
# 2) 이진분류 SHAP (voting_ensemble_binary.pkl)
# -----------------------------------------------------------------------------
def shap_binary(sample_size: int = 300, positive_class: int = 1) -> None:
    """
    이진분류(voting_ensemble_binary.pkl)에 대해 SHAP 값 계산.

    Parameters
    ----------
    sample_size : int
        SHAP 계산에 사용할 샘플 수.
    positive_class : int
        양성 클래스 (기본 1 = 고수/A).
    """
    model_path = MODEL_DIR / "voting_ensemble_binary.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"❌ 이진분류 모델 파일이 없습니다: {model_path}")

    print(f"\n📦 이진분류 모델 로드: {model_path}")
    with open(model_path, "rb") as f:
        model_package = pickle.load(f)

    ensemble = model_package["ensemble"]
    scaler = model_package["scaler"]
    features = model_package["features"]
    metadata = model_package.get("metadata", {})

    print(f"   - 사용 피처 수: {len(features)}개")
    print(f"   - 메타데이터: {metadata}")

    # 데이터 준비
    df = prepare_feature_data()

    # 🔐 방어: 누락된 피처 있으면 0으로 채워서라도 맞춰줌
    missing = [col for col in features if col not in df.columns]
    if missing:
        print(f"⚠️ SHAP용 피처 누락: {missing} → 0으로 채워서 사용")
        for col in missing:
            df[col] = 0

    X = df[features]
    X_s = scaler.transform(X)

    # 샘플링
    n = len(X_s)
    if sample_size is not None and sample_size < n:
        idx = np.random.choice(n, size=sample_size, replace=False)
        X_sample = X_s[idx]
        print(f"   - SHAP 계산용 샘플: {sample_size}/{n}")
    else:
        X_sample = X_s
        print(f"   - SHAP 계산용 샘플: 전체 {n}개 사용")

    X_df_sample = pd.DataFrame(X_sample, columns=features)

    # base 모델 선택 (xgb 우선 → rf)
    if hasattr(ensemble, "named_estimators_"):
        estimators = ensemble.named_estimators_
    else:
        raise RuntimeError("VotingClassifier에 named_estimators_ 속성이 없습니다.")

    if "xgb" in estimators:
        base_model = estimators["xgb"]
        base_name = "XGBoost"
    elif "rf" in estimators:
        base_model = estimators["rf"]
        base_name = "RandomForest"
    else:
        name0, base_model = list(estimators.items())[0]
        base_name = name0

    print(f"\n🌳 SHAP 기준 모델: {base_name} (binary)")

    explainer = shap.TreeExplainer(base_model)
    shap_values = explainer.shap_values(X_sample)

    # 이진 분류일 때 shap_values 형식 방어
    if isinstance(shap_values, list):
        shap_bin = shap_values[positive_class]
    else:
        shap_bin = shap_values

    # 1) 요약(bar) 플롯
    plt.figure(figsize=(10, 6))
    shap.summary_plot(
        shap_bin,
        X_df_sample,
        plot_type="bar",
        show=False,
    )
    plt.title("SHAP Feature Importance (Binary, positive=1: 고수/A)")
    plt.tight_layout()
    plt.show()

    # 2) 비즈웜 플롯
    plt.figure(figsize=(10, 6))
    shap.summary_plot(
        shap_bin,
        X_df_sample,
        show=False,
    )
    plt.title("SHAP Summary Plot (Binary, positive=1: 고수/A)")
    plt.tight_layout()
    plt.show()


# -----------------------------------------------------------------------------
# 메인 실행
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n================= SHAP 분석 시작 =================")

    # 1) 다중분류 – A 등급 기준
    try:
        print("\n[1] 다중분류 SHAP (class = 'A')")
        shap_multiclass(sample_size=300, target_label="A")
    except Exception as e:
        print(f"❌ 다중분류 SHAP 계산 중 오류: {e}")

    # 2) 이진분류 – positive_class=1 (고수/A)
    try:
        print("\n[2] 이진분류 SHAP (positive_class=1)")
        shap_binary(sample_size=300, positive_class=1)
    except Exception as e:
        print(f"❌ 이진분류 SHAP 계산 중 오류: {e}")

    print("\n================= SHAP 분석 종료 =================\n")