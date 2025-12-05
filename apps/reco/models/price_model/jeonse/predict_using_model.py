"""Predict jeonse prices and classify listings as 저렴/적정/비쌈."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable, List

import numpy as np
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PACKAGE_PARENT = CURRENT_DIR.parent
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))

from jeonse.model import load_model, predict_model
from jeonse.predict_using_model import (
    normalize_json_data,
    preprocess_from_dataframe,
    build_features,
)


PROJECT_ROOT = CURRENT_DIR.parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "landData"
DATA_FILES = [
    DATA_DIR / "00_통합_빌라주택.json",
    DATA_DIR / "00_통합_아파트.json",
    DATA_DIR / "00_통합_오피스텔.json",
    DATA_DIR / "00_통합_원투룸.json",
]
MODEL_PATH = CURRENT_DIR / "models" / "model_20251204_151829.pkl"
OUTPUT_DIR = CURRENT_DIR / "outputs"
OUTPUT_CSV = OUTPUT_DIR / "jeonse_prediction_result.csv"

COL_ADDRESS = "주소_정보.전체주소"
COL_DEAL = "거래_정보.거래방식"
TARGET_COL = "평당가"


def load_json_as_dataframe(paths: Iterable[Path]) -> pd.DataFrame:
    """Load multiple JSON files and flatten nested dicts."""
    frames: List[pd.DataFrame] = []
    for path in paths:
        if not path.exists():
            print(f"[WARN] 파일을 찾을 수 없습니다: {path}")
            continue
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        df_raw = pd.DataFrame(data)
        frames.append(normalize_json_data(df_raw))

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def align_features(df_features: pd.DataFrame, model) -> pd.DataFrame:
    """Align feature columns with the trained model."""
    booster = getattr(model, "get_booster", lambda: None)()
    feature_names = getattr(booster, "feature_names", None)
    if not feature_names:
        return df_features

    for name in feature_names:
        if name not in df_features:
            df_features[name] = 0

    extra_cols = [col for col in df_features.columns if col not in feature_names]
    if extra_cols:
        df_features = df_features.drop(columns=extra_cols)

    return df_features[feature_names]


def evaluate_price_difference(
    actual: float,
    predicted: float,
    threshold_ratio: float = 0.1,
) -> tuple[str, float, float]:
    """Return (label, diff, diff_percent) comparing actual vs predicted."""
    diff = actual - predicted
    diff_ratio = (diff / predicted) * 100 if predicted != 0 else 0

    if diff_ratio < -threshold_ratio * 100:
        label = "저렴"
    elif diff_ratio > threshold_ratio * 100:
        label = "비쌈"
    else:
        label = "적정"
    return label, diff, diff_ratio


def main():
    print("1) 데이터 적재 및 전처리")
    df_raw = load_json_as_dataframe(DATA_FILES)
    if df_raw.empty:
        print("   로드된 데이터가 없습니다.")
        return

    df_preprocessed = preprocess_from_dataframe(df_raw)
    if df_preprocessed.empty:
        print("   전처리 결과 데이터가 없습니다.")
        return

    df_ml = build_features(df_preprocessed)
    if df_ml.empty:
        print("   특성 생성 결과 데이터가 없습니다.")
        return

    print("2) 모델 로드 및 예측")
    model = load_model(str(MODEL_PATH))
    X = df_ml.drop(columns=[TARGET_COL])
    y_actual = df_ml[TARGET_COL]
    X_aligned = align_features(X.copy(), model)
    y_pred = predict_model(model, X_aligned)

    results = pd.DataFrame(
        {
            "주소": df_preprocessed.loc[y_actual.index, COL_ADDRESS].values,
            "거래방식": df_preprocessed.loc[y_actual.index, COL_DEAL].values,
            "실제값(만원/평)": y_actual.values,
            "예측값(만원/평)": y_pred,
        }
    )

    evaluations = results.apply(
        lambda row: evaluate_price_difference(row["실제값(만원/평)"], row["예측값(만원/평)"]),
        axis=1,
    )
    results["분류"] = [ev[0] for ev in evaluations]
    results["차이금액(만원/평)"] = [ev[1] for ev in evaluations]
    results["차이비율(%)"] = [ev[2] for ev in evaluations]

    print("3) 결과 요약 (상위 5건)")
    print(
        results[
            ["주소", "거래방식", "실제값(만원/평)", "예측값(만원/평)", "차이비율(%)", "분류"]
        ]
        .head()
        .to_string(index=False)
    )

    counts = results["분류"].value_counts().rename_axis("분류").reset_index(name="개수")
    counts["비율(%)"] = (counts["개수"] / len(results) * 100).round(2)
    print("\n4) 분류별 개수/비율")
    print(counts.to_string(index=False))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n완료: {OUTPUT_CSV.resolve()}")


if __name__ == "__main__":
    main()
