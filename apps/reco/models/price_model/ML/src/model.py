"""
머신러닝 모델 정의 모듈
"""
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from typing import Dict


def get_models() -> Dict[str, object]:
    """
    학습에 사용할 모델들을 반환

    Returns:
        모델 딕셔너리 {모델명: 모델 객체}
    """
    models = {
        "XGBoost": XGBRegressor(
            n_estimators=3000,
            learning_rate=0.05,
            max_depth=6,
            min_child_weight=10,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=1.0,
            reg_lambda=5.0,
            gamma=0.5,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=-1,
        ),
        "LightGBM": LGBMRegressor(
            n_estimators=3000,
            learning_rate=0.03,
            max_depth=-1,
            num_leaves=255,
            min_child_samples=20,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.05,
            reg_lambda=1.5,
            min_split_gain=0.005,
            random_state=42,
            n_jobs=-1,
            verbose=-1,
        )
    }

    return models
