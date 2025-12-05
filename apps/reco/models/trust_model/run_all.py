from pathlib import Path

# 상대 import와 절대 import 모두 지원
try:
    from .pipeline._00_load_data import load_data
    from .pipeline._01_create_target import create_regression_target
    from .pipeline._02_feature_engineering import add_features
    from .pipeline._03_train_model import train_classification_ensemble
except ImportError:
    from pipeline._00_load_data import load_data
    from pipeline._01_create_target import create_regression_target
    from pipeline._02_feature_engineering import add_features
    from pipeline._03_train_model import train_classification_ensemble

# 경로 설정
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

print("\n" + "="*60)
print("🚀 중개사 신뢰도 모델 - Voting 앙상블")
print("   (Soft Voting: 강한 모델만 결합)")
print("   (Target: 3등급 A, B, C)")
print("   (기준: 거래성사율 분위수)")
print("="*60)

df = load_data()
df = create_regression_target(df)
df = add_features(df)
df = train_classification_ensemble(df)

output_path = RESULTS_DIR / "classification_results.csv"
df.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"\n💾 결과 저장: {output_path}")
print("="*60)
print("✅ Voting 앙상블 파이프라인 완료!")
print("   - 4개 강한 모델 (RF, GB, ET, XGB)")
print("   - Soft Voting + 가중치 (RF=2, XGB=2)")
print("   - 15개 피처")
print("   - 3등급 분류 (A, B, C)")
print("   - 기준: 거래성사율 분위수 (각 33%)")
print("="*60 + "\n")
