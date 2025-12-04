"""Run 월세 price prediction with a saved model and raw JSON inputs."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure the parent directory (which contains the package) is on sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PACKAGE_PARENT = CURRENT_DIR.parent
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))

from 월세_price_model.data_preprocessing import preprocess_data
from 월세_price_model.feature_engineering import create_all_features, prepare_ml_features
from 월세_price_model.model import load_model
from 월세_price_model.predict import evaluate_price_difference


DATA_FILES = [
    Path("data/landData/00_통합_빌라주택.json"),
    Path("data/landData/00_통합_아파트.json"),
    Path("data/landData/00_통합_오피스텔.json"),
    Path("data/landData/00_통합_원투룸.json"),
]
DEFAULT_MODEL = Path("apps/reco/models/월세_price_model/models/model_20251204_162936.pkl")

COL_ADDRESS = "주소_정보.전체주소"
COL_DEAL = "거래_정보.거래방식"
TARGET_COL = "환산보증금"


def align_features(features: pd.DataFrame, model) -> pd.DataFrame:
    """Align feature columns to match what the trained model expects."""
    booster = getattr(model, "get_booster", lambda: None)()
    feature_names = getattr(booster, "feature_names", None)
    if not feature_names:
        return features

    for col in feature_names:
        if col not in features:
            features[col] = 0

    extra_cols = [col for col in features.columns if col not in feature_names]
    if extra_cols:
        features = features.drop(columns=extra_cols)

    return features[feature_names]


def predict(properties: pd.DataFrame, model_path: Path) -> pd.DataFrame:
    """Load the saved model and return prediction/evaluation dataframe."""
    model = load_model(str(model_path))

    features = properties.drop(columns=[TARGET_COL])
    target = properties[TARGET_COL]
    features_aligned = align_features(features.copy(), model)

    y_pred_log = model.predict(features_aligned)
    y_pred = np.expm1(y_pred_log)

    results = pd.DataFrame(
        {
            "주소": properties.get(COL_ADDRESS, ""),
            "거래방식": properties.get(COL_DEAL, ""),
            "실제값(만원)": target.values,
            "예측값(만원)": y_pred,
        }
    )

    evaluations = results.apply(
        lambda row: evaluate_price_difference(row["실제값(만원)"], row["예측값(만원)"]),
        axis=1,
    )
    results["분류"] = [ev[0] for ev in evaluations]
    results["차이금액(만원)"] = [ev[1] for ev in evaluations]
    results["차이비율(%)"] = [ev[2] for ev in evaluations]
    return results


def main():
    print("1) 데이터 적재 및 전처리")
    df = preprocess_data([str(path) for path in DATA_FILES])
    df = create_all_features(df)
    df_ml = prepare_ml_features(df)

    print("2) 모델 예측")
    results = predict(df_ml, DEFAULT_MODEL)

    print("3) 결과 요약 (상위 5건)")
    print(
        results[["주소", "거래방식", "실제값(만원)", "예측값(만원)", "차이비율(%)", "분류"]]
        .head()
        .to_string(index=False)
    )

    print("\n4) 분류별 개수/비율")
    counts = results["분류"].value_counts().rename_axis("분류").reset_index(name="개수")
    counts["비율(%)"] = (counts["개수"] / len(results) * 100).round(2)
    print(counts.to_string(index=False))

    output_dir = CURRENT_DIR / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "walse_prediction_result.csv"
    results.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"완료: {output_path.resolve()}")


if __name__ == "__main__":
    main()
