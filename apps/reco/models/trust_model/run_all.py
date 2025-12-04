import os
import pandas as pd

from pipeline._00_load_data import load_data
from pipeline._01_rule_score import apply_rule_score
from pipeline._02_feature_engineering import add_features
from pipeline._05_classification_model import train_classification
from pipeline._06_ensemble import ensemble

BASE_DIR = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

print("\n" + "="*60)
print("🚀 중개사 신뢰도 모델 파이프라인 시작")
print("="*60)

df = load_data()
df = apply_rule_score(df)
df = add_features(df)
df = train_classification(df)
df = ensemble(df)

output_path = os.path.join(RESULTS_DIR, "final_temperature.csv")
df.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"\n💾 결과 저장: {output_path}")
print("="*60)
print("✅ 파이프라인 완료!\n")
