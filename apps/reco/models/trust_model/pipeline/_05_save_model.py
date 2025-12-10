"""
_05_save_model.py
중개사 신뢰도 모델 - 최종 저장 단계
"""

import pickle
from pathlib import Path
import pandas as pd

TEMP_MODEL_PATH = "apps/reco/models/trust_model/save_models/temp_trained_models.pkl"
FINAL_MODEL_PATH = "apps/reco/models/trust_model/save_models/final_trust_model.pkl"
EVAL_RESULTS_PATH = "apps/reco/models/trust_model/results/model_eval_results.csv"


def select_best_model(temp_data):
    """
    temp 모델 데이터에서 직접 최고 성능 모델 선택
    """
    models = temp_data["models"]
    cv_results = temp_data.get("cv_results", {})
    
    if not cv_results:
        # CV 결과가 없으면 첫 번째 모델 선택
        first_model = list(models.keys())[0]
        print(f"⚠️ CV 결과가 없습니다. 첫 번째 모델을 선택합니다: {first_model}")
        return first_model
    
    # CV 결과가 있으면 CV 기준으로 최고 모델 선택
    best_model = None
    best_cv_score = 0
    
    print("📊 모델별 CV 성능:")
    for model_name, results in cv_results.items():
        cv_mean = results['cv_mean']
        cv_std = results['cv_std']
        test_acc = results['test_acc']
        
        print(f"  {model_name}:")
        print(f"    - CV Mean: {cv_mean:.4f} (±{cv_std:.4f})")
        print(f"    - Test Accuracy: {test_acc:.4f}")
        
        if cv_mean > best_cv_score:
            best_cv_score = cv_mean
            best_model = model_name
    
    print(f"\n🏆 최고 성능 모델 (CV 기준): {best_model}")
    print(f"   - CV Mean: {best_cv_score:.4f}")
    
    return best_model


def main():
    print("=== SAVE MODEL STEP ===")

    # 1) temp 모델 파일 확인
    if not Path(TEMP_MODEL_PATH).exists():
        raise FileNotFoundError(f"[ERROR] {TEMP_MODEL_PATH} 파일이 없습니다. 먼저 03_train.py를 실행하세요.")

    # 2) temp 모델 로드
    with open(TEMP_MODEL_PATH, "rb") as f:
        temp_data = pickle.load(f)

    # 3) 최고 성능 모델 선택
    best_model_name = select_best_model(temp_data)

    # 4) 최고 성능 모델만 추출하여 최종 저장
    Path("apps/reco/models/trust_model/save_models").mkdir(parents=True, exist_ok=True)
    
    final_model_data = {
        "model": temp_data["models"][best_model_name],
        "scaler": temp_data["scaler"],
        "feature_names": temp_data["feature_names"],
        "model_name": best_model_name
    }

    with open(FINAL_MODEL_PATH, "wb") as f:
        pickle.dump(final_model_data, f)

    print(f"✓ 최종 모델 저장 완료: {FINAL_MODEL_PATH}")
    print(f"✓ 선택된 모델: {best_model_name}")


if __name__ == "__main__":
    main()
