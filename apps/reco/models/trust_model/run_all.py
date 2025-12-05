import os
import pandas as pd

from pipeline._00_load_data import load_data
from pipeline._01_create_target import create_regression_target
from pipeline._02_feature_engineering import add_features
from pipeline._05_advanced_ensemble import train_advanced_ensemble

BASE_DIR = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

print("\n" + "="*60)
print("🚀 중개사 신뢰도 모델 - 앙상블 버전")
print("   (Stacking: 5개 모델 결합)")
print("="*60)

df = load_data()
df = create_regression_target(df)
df = add_features(df)
df = train_advanced_ensemble(df)

output_path = os.path.join(RESULTS_DIR, "advanced_results.csv")
df.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"\n💾 결과 저장: {output_path}")
print("="*60)
print("✅ 앙상블 파이프라인 완료!")
print("   - 5개 Base Models (RF, GB, ET, Ridge, Lasso)")
print("   - Stacking Ensemble")
print("   - 16개 피처")
print("="*60 + "\n")
