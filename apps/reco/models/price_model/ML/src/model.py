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
    n_estimators=1500,        # 3000 → 1500 (조금 줄이기)
    learning_rate=0.03,
    max_depth=7,             # -1 → 7 (트리 깊이 제한)
    num_leaves=63,           # 255 → 63 (리프 개수 줄이기)
    min_child_samples=80,    # 20 → 80 (리프 최소 샘플 수 증가)
    subsample=0.7,           # 0.8 → 0.7
    colsample_bytree=0.7,    # 0.8 → 0.7
    reg_alpha=0.5,           # 0.05 → 0.5 (L1 규제 강화)
    reg_lambda=3.0,          # 1.5 → 3.0 (L2 규제 강화)
    min_split_gain=0.01,     # 0.005 → 0.01
    objective="multiclass",
    num_class=3,
    metric="multi_logloss",
    random_state=42,
    n_jobs=-1,
    verbose=-1,
    class_weight='balanced',
    is_unbalance=True,
)
    }

    return models
