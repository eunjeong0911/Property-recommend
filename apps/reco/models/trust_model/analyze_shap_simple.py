# 간단한 SHAP 분석 - 피처 중요도만 확인

import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import shap
import os

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

print("\n📊 SHAP 피처 중요도 분석\n")

# 경로 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, "models", "trust_model.pkl")
DATA_PATH = os.path.join(SCRIPT_DIR, "results", "final_temperature.csv")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "results")

# 1. 모델 로드
print("1️⃣ 모델 로드...")
with open(MODEL_PATH, "rb") as f:
    package = pickle.load(f)

model = package['model']
scaler = package['scaler']
features = package['features']
print(f"   ✅ 완료 (피처: {len(features)}개)\n")

# 2. 데이터 로드
print("2️⃣ 데이터 로드...")
df = pd.read_csv(DATA_PATH)
X = df[features]
X_scaled = scaler.transform(X)
print(f"   ✅ 완료 ({len(df)}개)\n")

# 3. SHAP 값 계산
print("3️⃣ SHAP 값 계산 중...")
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_scaled)

# S등급(최고 등급) 기준
if isinstance(shap_values, list):
    shap_values_s = shap_values[-1]  # S등급
else:
    shap_values_s = shap_values

print("   ✅ 완료\n")

# 4. 피처 중요도 계산
print("4️⃣ 피처 중요도 분석\n")
print("="*60)

# 평균 절대 SHAP 값
mean_abs_shap = np.abs(shap_values_s).mean(axis=0)

# 디버깅
print(f"DEBUG: mean_abs_shap shape = {mean_abs_shap.shape}")
print(f"DEBUG: features length = {len(features)}")

# 2D인 경우 1D로 변환
if len(mean_abs_shap.shape) > 1:
    print(f"DEBUG: 2D 배열 감지, flatten 수행")
    mean_abs_shap = mean_abs_shap.flatten()
    print(f"DEBUG: flatten 후 shape = {mean_abs_shap.shape}")

# 피처 개수만큼만 사용
mean_abs_shap = mean_abs_shap[:len(features)]
print(f"DEBUG: 최종 shape = {mean_abs_shap.shape}")

# 리스트로 변환
importance_list = mean_abs_shap.tolist()
print(f"DEBUG: list length = {len(importance_list)}")

# 정렬
feature_importance = pd.DataFrame({
    'feature': features,
    'importance': importance_list
}).sort_values('importance', ascending=False)

print("📊 피처 중요도 순위 (S등급 기준)\n")
for idx, row in feature_importance.iterrows():
    bar = '█' * int(row['importance'] * 50)
    print(f"{row['feature']:20s} {row['importance']:.4f} {bar}")

print("\n" + "="*60)

# 5. 간단한 시각화 2개만
print("\n5️⃣ 시각화 생성 중...\n")

# 5-1. Bar Plot (피처 중요도)
plt.figure(figsize=(10, 6))
shap.summary_plot(
    shap_values_s, 
    X_scaled, 
    feature_names=features,
    plot_type="bar",
    show=False
)
plt.title("피처 중요도 (평균 |SHAP 값|)", fontsize=14, pad=15)
plt.tight_layout()
output_path = os.path.join(OUTPUT_DIR, "shap_importance.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"   ✅ 저장: {output_path}")

# 5-2. Summary Plot (피처별 영향)
plt.figure(figsize=(10, 8))
shap.summary_plot(
    shap_values_s, 
    X_scaled, 
    feature_names=features,
    show=False
)
plt.title("피처별 SHAP 값 분포 (S등급 기준)", fontsize=14, pad=15)
plt.tight_layout()
output_path = os.path.join(OUTPUT_DIR, "shap_summary.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"   ✅ 저장: {output_path}")

# 6. CSV 저장
output_path = os.path.join(OUTPUT_DIR, "shap_feature_importance.csv")
feature_importance.to_csv(output_path, index=False, encoding='utf-8-sig')
print(f"   ✅ 저장: {output_path}")

print("\n" + "="*60)
print("✅ 분석 완료!")
print("="*60)

print("\n💡 해석:")
print(f"   - 가장 중요한 피처: {feature_importance.iloc[0]['feature']}")
print(f"   - 상위 3개: {', '.join(feature_importance.head(3)['feature'].tolist())}")
print(f"   - 이 피처들이 S등급 예측에 가장 큰 영향을 미칩니다.\n")
