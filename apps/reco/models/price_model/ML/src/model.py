"""
머신러닝 모델 정의 모듈 - 3중 분류 (저렴/적정/비쌈)
"""
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from typing import Dict


def get_models() -> Dict[str, object]:
    """
    학습에 사용할 분류 모델들을 반환

    Returns:
        모델 딕셔너리 {모델명: 모델 객체}
    """
    models = {
        "XGBoost": XGBClassifier(
            n_estimators=3000,
            learning_rate=0.03,  # 0.05 → 0.03 (더 천천히 학습)
            max_depth=5,  # 6 → 5 (트리 깊이 줄임)
            min_child_weight=20,  # 10 → 20 (더 보수적)
            subsample=0.7,  # 0.8 → 0.7
            colsample_bytree=0.7,  # 0.8 → 0.7
            reg_alpha=2.0,  # 1.0 → 2.0 (L1 정규화 강화)
            reg_lambda=10.0,  # 5.0 → 10.0 (L2 정규화 강화)
            gamma=1.0,  # 0.5 → 1.0
            objective="multi:softprob",  # 다중 분류 + 확률 출력
            num_class=3,  # 3개 클래스
            eval_metric="mlogloss",  # Multi-class log loss
            early_stopping_rounds=50,      
            random_state=42,
            n_jobs=-1,
            scale_pos_weight=None,
        ),
        "LightGBM": LGBMClassifier(
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
            objective="multiclass",  # 다중 분류
            num_class=3,  # 3개 클래스
            metric="multi_logloss",  # Multi-class log loss
            random_state=42,
            n_jobs=-1,
            verbose=-1,
            class_weight='balanced',  # 클래스 불균형 자동 처리
            is_unbalance=True,  # 불균형 데이터 처리
        )
    }

    return models
