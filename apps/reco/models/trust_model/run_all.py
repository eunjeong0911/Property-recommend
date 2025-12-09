"""
중개사 신뢰도 모델 - 전체 파이프라인 실행
"""
from pathlib import Path
import sys

# pipeline 폴더를 sys.path에 추가
pipeline_dir = Path(__file__).parent / "pipeline"
sys.path.insert(0, str(pipeline_dir))

# import
from _01_train_model import main as train_model

# 경로 설정
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def run_pipeline():
    """전체 파이프라인 실행"""
    print("\n" + "="*70)
    print("🚀 중개사 신뢰도 모델 - 전체 파이프라인 실행")
    print("="*70)
    
    # 1. 데이터 로드 및 전처리 (이미 main에서 실행됨)
    print("\n[Step 1/2] 데이터 전처리 및 모델 학습 시작...")
    
    # 2. 모델 학습 (데이터 로드 포함)
    best_model, scaler, feature_names, results = train_model()
    
    print("\n" + "="*70)
    print("✅ 전체 파이프라인 완료!")
    print("="*70)
    print("\n📊 최종 결과:")
    print(f"   - 최고 모델: {max(results, key=lambda x: results[x]['f1_score'])}")
    print(f"   - 정확도: {max(r['accuracy'] for r in results.values()):.4f}")
    print(f"   - F1-Score: {max(r['f1_score'] for r in results.values()):.4f}")
    print(f"   - 피처 수: {len(feature_names)}")
    print(f"   - 타겟: 하이브리드 (거래완료율 30% + 인력 40% + 경력 20% + 운영 10%)")
    print("\n💾 저장된 파일:")
    print(f"   - 모델: apps/reco/models/trust_model/saved_models/trust_model.pkl")
    print(f"   - 스케일러: apps/reco/models/trust_model/saved_models/scaler.pkl")
    print(f"   - 피처: apps/reco/models/trust_model/saved_models/feature_names.pkl")
    print(f"   - 데이터: data/processed_office_data.csv")
    print("="*70 + "\n")
    
    return best_model, scaler, feature_names, results


if __name__ == "__main__":
    best_model, scaler, feature_names, results = run_pipeline()
