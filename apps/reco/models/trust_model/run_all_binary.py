from pathlib import Path

# 상대 import와 절대 import 모두 지원 (이진 분류 버전)
try:
    from .pipeline._00_load_data import load_data
    from .pipeline._0A_create_target import create_binary_target
    from .pipeline._02_feature_engineering import add_features
    from .pipeline._0B_train_model import train_binary_ensemble
except ImportError:
    from pipeline._00_load_data import load_data
    from pipeline._0A_create_target import create_binary_target
    from pipeline._02_feature_engineering import add_features
    from pipeline._0B_train_model import train_binary_ensemble

# 경로 설정
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

print("\n" + "="*60)
print("🚀 중개사 신뢰도 모델 - Voting 앙상블 (이진 분류)")
print("   (Soft Voting: 강한 모델만 결합)")
print("   (Target: trust_binary 0/1)")
print("   (기준: 거래성사율 상위 33% = A(고수))")
print("="*60)

# 1) 데이터 로드
df = load_data()

# 2) 이진 타겟 생성 (A vs B)
df = create_binary_target(df)

# 3) 피처 엔지니어링
df = add_features(df)

# 4) 이진 분류 Voting 앙상블 학습
df = train_binary_ensemble(df)

# 5) 결과 저장
output_path = RESULTS_DIR / "binary_classification_results.csv"
df.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"\n💾 결과 저장: {output_path}")
print("="*60)
print("✅ Voting 앙상블 파이프라인 완료! (이진 분류)")
print("   - 4개 강한 모델 (RF, GB, ET, XGB)")
print("   - Soft Voting + 가중치 (RF=2, XGB=2)")
print("   - 17개 피처")
print("   - 타겟: trust_binary (0=B, 1=A)")
print("   - 기준: 거래성사율 {high_threshold:.2f}% 이상 = A(고수)")
print("="*60 + "\n")