"""
Trust Model Presentation Materials
===================================
발표용 추가 데이터 분석 자료

목차:
1. 모델 성능 분석
2. 피처 중요도 분석
3. 등급별 특성 비교
4. 예측 오류 분석
5. 비즈니스 인사이트
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pickle

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 결과 저장 디렉토리
output_dir = Path("apps/reco/models/trust_model/analysis/results")
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 100)
print("발표용 데이터 분석 자료 생성")
print("=" * 100)

# 데이터 로드
df = pd.read_csv('data/ML/preprocessed_office_data.csv', encoding='utf-8-sig')
X_train = pd.read_csv('data/ML/trust/X_train.csv', encoding='utf-8-sig')
X_test = pd.read_csv('data/ML/trust/X_test.csv', encoding='utf-8-sig')
y_train = pd.read_csv('data/ML/trust/y_train.csv', encoding='utf-8-sig')['Target']
y_test = pd.read_csv('data/ML/trust/y_test.csv', encoding='utf-8-sig')['Target']

# 모델 로드
with open("apps/reco/models/trust_model/save_models/final_trust_model.pkl", "rb") as f:
    model_data = pickle.load(f)
    model = model_data["model"]
    scaler = model_data["scaler"]

print(f"데이터 로드 완료")
print(f"  - Train: {len(X_train)}개")
print(f"  - Test: {len(X_test)}개")
print(f"  - 피처 수: {len(X_train.columns)}개")

# ============================================================================
# 1. 모델 성능 종합 분석
# ============================================================================
print("\n" + "=" * 100)
print("1. 모델 성능 종합 분석")
print("=" * 100)

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# 예측
X_train_scaled = scaler.transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 총거래활동량_log 가중치 조정
feature_names = X_train.columns.tolist()
if "총거래활동량_log" in feature_names:
    feature_idx = feature_names.index("총거래활동량_log")
    X_train_scaled[:, feature_idx] *= 0.5
    X_test_scaled[:, feature_idx] *= 0.5

y_train_pred = model.predict(X_train_scaled)
y_test_pred = model.predict(X_test_scaled)

train_acc = accuracy_score(y_train, y_train_pred)
test_acc = accuracy_score(y_test, y_test_pred)

# 성능 지표 시각화
fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# 1-1. Train vs Test 정확도
axes[0, 0].bar(['Train', 'Test'], [train_acc * 100, test_acc * 100], 
               color=['steelblue', 'coral'])
axes[0, 0].set_title('Train vs Test 정확도', fontsize=14, fontweight='bold')
axes[0, 0].set_ylabel('정확도 (%)')
axes[0, 0].set_ylim([0, 100])
axes[0, 0].grid(axis='y', alpha=0.3)
for i, v in enumerate([train_acc * 100, test_acc * 100]):
    axes[0, 0].text(i, v + 2, f'{v:.2f}%', ha='center', fontweight='bold', fontsize=12)

# 과적합 표시
overfitting = (train_acc - test_acc) * 100
axes[0, 0].text(0.5, 50, f'과적합: {overfitting:.2f}%', 
                ha='center', fontsize=11, 
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

# 1-2. 등급별 정확도 (Test)
from sklearn.metrics import precision_score, recall_score, f1_score

grade_labels = ['C등급 (0)', 'B등급 (1)', 'A등급 (2)']
precision = precision_score(y_test, y_test_pred, average=None)
recall = recall_score(y_test, y_test_pred, average=None)
f1 = f1_score(y_test, y_test_pred, average=None)

x = np.arange(len(grade_labels))
width = 0.25

axes[0, 1].bar(x - width, precision, width, label='Precision', color='skyblue')
axes[0, 1].bar(x, recall, width, label='Recall', color='lightgreen')
axes[0, 1].bar(x + width, f1, width, label='F1-Score', color='salmon')

axes[0, 1].set_title('등급별 성능 지표 (Test)', fontsize=14, fontweight='bold')
axes[0, 1].set_ylabel('점수')
axes[0, 1].set_xticks(x)
axes[0, 1].set_xticklabels(grade_labels)
axes[0, 1].legend()
axes[0, 1].grid(axis='y', alpha=0.3)
axes[0, 1].set_ylim([0, 1.1])

# 1-3. Confusion Matrix (Test)
cm = confusion_matrix(y_test, y_test_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[1, 0],
            xticklabels=grade_labels, yticklabels=grade_labels)
axes[1, 0].set_title('혼동 행렬 (Test)', fontsize=14, fontweight='bold')
axes[1, 0].set_ylabel('실제')
axes[1, 0].set_xlabel('예측')

# 1-4. 등급별 샘플 수
train_dist = y_train.value_counts().sort_index()
test_dist = y_test.value_counts().sort_index()

x = np.arange(len(grade_labels))
width = 0.35

axes[1, 1].bar(x - width/2, train_dist.values, width, label='Train', color='steelblue')
axes[1, 1].bar(x + width/2, test_dist.values, width, label='Test', color='coral')

axes[1, 1].set_title('등급별 데이터 분포', fontsize=14, fontweight='bold')
axes[1, 1].set_ylabel('샘플 수')
axes[1, 1].set_xticks(x)
axes[1, 1].set_xticklabels(grade_labels)
axes[1, 1].legend()
axes[1, 1].grid(axis='y', alpha=0.3)

for i, (train_v, test_v) in enumerate(zip(train_dist.values, test_dist.values)):
    axes[1, 1].text(i - width/2, train_v + 2, str(train_v), ha='center', fontweight='bold')
    axes[1, 1].text(i + width/2, test_v + 2, str(test_v), ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / '01_model_performance.png', dpi=300, bbox_inches='tight')
print(f"✅ 저장: {output_dir / '01_model_performance.png'}")
plt.close()

# ============================================================================
# 2. 피처 중요도 분석
# ============================================================================
print("\n" + "=" * 100)
print("2. 피처 중요도 분석")
print("=" * 100)

# 모델 계수 추출
coef = model.coef_  # shape: (3, n_features)

fig, axes = plt.subplots(1, 3, figsize=(20, 6))

for class_idx, (ax, grade) in enumerate(zip(axes, grade_labels)):
    # 계수 절대값 기준 정렬
    coef_abs = np.abs(coef[class_idx])
    sorted_indices = np.argsort(coef_abs)[::-1][:10]  # 상위 10개
    
    top_features = [feature_names[i] for i in sorted_indices]
    top_coefs = [coef[class_idx][i] for i in sorted_indices]
    
    colors = ['green' if c > 0 else 'red' for c in top_coefs]
    
    ax.barh(range(len(top_features)), top_coefs, color=colors, alpha=0.7)
    ax.set_yticks(range(len(top_features)))
    ax.set_yticklabels(top_features)
    ax.set_xlabel('계수 값')
    ax.set_title(f'{grade} 예측 중요 피처 (Top 10)', fontsize=12, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    ax.axvline(0, color='black', linewidth=0.8)
    
    # 값 표시
    for i, v in enumerate(top_coefs):
        ax.text(v, i, f' {v:+.3f}', va='center', fontsize=9)

plt.tight_layout()
plt.savefig(output_dir / '02_feature_importance.png', dpi=300, bbox_inches='tight')
print(f"✅ 저장: {output_dir / '02_feature_importance.png'}")
plt.close()

# ============================================================================
# 3. 등급별 특성 비교
# ============================================================================
print("\n" + "=" * 100)
print("3. 등급별 특성 비교")
print("=" * 100)

# Train 데이터에 Target 추가
X_train_with_target = X_train.copy()
X_train_with_target['Target'] = y_train

# 주요 피처 선택
key_features = ['총거래활동량_log', '운영기간_년', '자격증_보유비율', '총_직원수', '지역_경쟁강도']

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
axes = axes.flatten()

for idx, feature in enumerate(key_features):
    if feature in X_train_with_target.columns:
        box_data = [X_train_with_target[X_train_with_target['Target'] == i][feature].dropna() 
                    for i in range(3)]
        
        bp = axes[idx].boxplot(box_data, tick_labels=grade_labels, patch_artist=True)
        for patch, color in zip(bp['boxes'], ['lightcoral', 'lightyellow', 'lightgreen']):
            patch.set_facecolor(color)
        
        axes[idx].set_title(f'{feature} 분포', fontsize=12, fontweight='bold')
        axes[idx].set_ylabel(feature)
        axes[idx].grid(axis='y', alpha=0.3)
        
        # 평균값 표시
        means = [X_train_with_target[X_train_with_target['Target'] == i][feature].mean() 
                for i in range(3)]
        for i, mean in enumerate(means):
            axes[idx].text(i+1, mean, f'{mean:.2f}', ha='center', 
                          bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                          fontsize=9)

# 마지막 subplot 제거
axes[-1].remove()

plt.tight_layout()
plt.savefig(output_dir / '03_grade_comparison.png', dpi=300, bbox_inches='tight')
print(f"✅ 저장: {output_dir / '03_grade_comparison.png'}")
plt.close()

# ============================================================================
# 4. 예측 오류 분석
# ============================================================================
print("\n" + "=" * 100)
print("4. 예측 오류 분석")
print("=" * 100)

# 오분류 케이스 찾기
X_test_with_pred = X_test.copy()
X_test_with_pred['실제'] = y_test.values
X_test_with_pred['예측'] = y_test_pred

misclassified = X_test_with_pred[X_test_with_pred['실제'] != X_test_with_pred['예측']]

fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# 4-1. 오분류 패턴
error_patterns = {}
for _, row in misclassified.iterrows():
    pattern = f"{int(row['실제'])} → {int(row['예측'])}"
    error_patterns[pattern] = error_patterns.get(pattern, 0) + 1

if error_patterns:
    patterns = list(error_patterns.keys())
    counts = list(error_patterns.values())
    
    axes[0, 0].bar(patterns, counts, color='salmon')
    axes[0, 0].set_title('오분류 패턴 분포', fontsize=14, fontweight='bold')
    axes[0, 0].set_xlabel('실제 → 예측')
    axes[0, 0].set_ylabel('빈도')
    axes[0, 0].grid(axis='y', alpha=0.3)
    
    for i, v in enumerate(counts):
        axes[0, 0].text(i, v + 0.5, str(v), ha='center', fontweight='bold')

# 4-2. 정확도 vs 오류율
correct = len(X_test_with_pred) - len(misclassified)
incorrect = len(misclassified)

axes[0, 1].pie([correct, incorrect], 
               labels=['정확한 예측', '오분류'], 
               autopct='%1.1f%%',
               colors=['lightgreen', 'salmon'],
               startangle=90)
axes[0, 1].set_title(f'Test 예측 결과\n(정확도: {test_acc*100:.2f}%)', 
                     fontsize=14, fontweight='bold')

# 4-3. 오분류 케이스의 총거래활동량 분포
if len(misclassified) > 0:
    axes[1, 0].hist(misclassified['총거래활동량_log'], bins=20, 
                    edgecolor='black', color='salmon', alpha=0.7, label='오분류')
    axes[1, 0].hist(X_test_with_pred[X_test_with_pred['실제'] == X_test_with_pred['예측']]['총거래활동량_log'], 
                    bins=20, edgecolor='black', color='lightgreen', alpha=0.5, label='정확한 예측')
    axes[1, 0].set_title('오분류 vs 정확한 예측 (총거래활동량)', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('총거래활동량_log')
    axes[1, 0].set_ylabel('빈도')
    axes[1, 0].legend()
    axes[1, 0].grid(axis='y', alpha=0.3)

# 4-4. 신뢰도 점수 분포
y_test_proba = model.predict_proba(X_test_scaled)
max_proba = np.max(y_test_proba, axis=1)

axes[1, 1].hist(max_proba, bins=20, edgecolor='black', color='skyblue')
axes[1, 1].set_title('예측 신뢰도 분포', fontsize=14, fontweight='bold')
axes[1, 1].set_xlabel('최대 확률')
axes[1, 1].set_ylabel('빈도')
axes[1, 1].axvline(max_proba.mean(), color='red', linestyle='--', 
                   label=f'평균: {max_proba.mean():.3f}')
axes[1, 1].legend()
axes[1, 1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / '04_error_analysis.png', dpi=300, bbox_inches='tight')
print(f"✅ 저장: {output_dir / '04_error_analysis.png'}")
plt.close()

# ============================================================================
# 5. 비즈니스 인사이트
# ============================================================================
print("\n" + "=" * 100)
print("5. 비즈니스 인사이트")
print("=" * 100)

fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# 5-1. 신뢰도 등급별 평균 거래량
grade_transaction = X_train_with_target.groupby('Target')['총거래활동량_log'].mean()
axes[0, 0].bar(grade_labels, np.exp(grade_transaction.values) - 1, 
               color=['lightcoral', 'lightyellow', 'lightgreen'])
axes[0, 0].set_title('신뢰도 등급별 평균 거래량', fontsize=14, fontweight='bold')
axes[0, 0].set_ylabel('평균 거래량 (건)')
axes[0, 0].grid(axis='y', alpha=0.3)
for i, v in enumerate(np.exp(grade_transaction.values) - 1):
    axes[0, 0].text(i, v + 5, f'{v:.0f}건', ha='center', fontweight='bold')

# 5-2. 운영기간과 신뢰도의 관계
grade_period = X_train_with_target.groupby('Target')['운영기간_년'].mean()
axes[0, 1].bar(grade_labels, grade_period.values, 
               color=['lightcoral', 'lightyellow', 'lightgreen'])
axes[0, 1].set_title('신뢰도 등급별 평균 운영기간', fontsize=14, fontweight='bold')
axes[0, 1].set_ylabel('평균 운영기간 (년)')
axes[0, 1].grid(axis='y', alpha=0.3)
for i, v in enumerate(grade_period.values):
    axes[0, 1].text(i, v + 0.2, f'{v:.1f}년', ha='center', fontweight='bold')

# 5-3. 자격증 보유율과 신뢰도
if '자격증_보유비율' in X_train_with_target.columns:
    grade_cert = X_train_with_target.groupby('Target')['자격증_보유비율'].mean()
    axes[1, 0].bar(grade_labels, grade_cert.values * 100, 
                   color=['lightcoral', 'lightyellow', 'lightgreen'])
    axes[1, 0].set_title('신뢰도 등급별 평균 자격증 보유율', fontsize=14, fontweight='bold')
    axes[1, 0].set_ylabel('평균 자격증 보유율 (%)')
    axes[1, 0].grid(axis='y', alpha=0.3)
    for i, v in enumerate(grade_cert.values * 100):
        axes[1, 0].text(i, v + 1, f'{v:.1f}%', ha='center', fontweight='bold')

# 5-4. 1층 여부와 신뢰도
if '1층_여부' in X_train_with_target.columns:
    grade_floor = X_train_with_target.groupby('Target')['1층_여부'].mean()
    axes[1, 1].bar(grade_labels, grade_floor.values * 100, 
                   color=['lightcoral', 'lightyellow', 'lightgreen'])
    axes[1, 1].set_title('신뢰도 등급별 1층 사무소 비율', fontsize=14, fontweight='bold')
    axes[1, 1].set_ylabel('1층 비율 (%)')
    axes[1, 1].grid(axis='y', alpha=0.3)
    for i, v in enumerate(grade_floor.values * 100):
        axes[1, 1].text(i, v + 1, f'{v:.1f}%', ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / '05_business_insights.png', dpi=300, bbox_inches='tight')
print(f"✅ 저장: {output_dir / '05_business_insights.png'}")
plt.close()

# ============================================================================
# 최종 요약
# ============================================================================
print("\n" + "=" * 100)
print("발표 자료 생성 완료!")
print("=" * 100)
print(f"\n📁 결과 저장 위치: {output_dir}")
print(f"\n생성된 파일:")
print(f"  1. 01_model_performance.png - 모델 성능 종합 분석")
print(f"  2. 02_feature_importance.png - 피처 중요도 분석")
print(f"  3. 03_grade_comparison.png - 등급별 특성 비교")
print(f"  4. 04_error_analysis.png - 예측 오류 분석")
print(f"  5. 05_business_insights.png - 비즈니스 인사이트")

print("\n📊 주요 지표:")
print(f"  - Test 정확도: {test_acc*100:.2f}%")
print(f"  - Train 정확도: {train_acc*100:.2f}%")
print(f"  - 과적합: {overfitting:.2f}%")
print(f"  - 오분류 케이스: {len(misclassified)}개 / {len(X_test)}개")

print("\n" + "=" * 100)
