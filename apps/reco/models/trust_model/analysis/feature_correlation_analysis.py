"""
Feature Correlation Analysis
=============================
피처 간 상관관계 분석
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 결과 저장 디렉토리
output_dir = Path("apps/reco/models/trust_model/analysis/results")
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 100)
print("피처 상관관계 분석")
print("=" * 100)

# 데이터 로드
X_train = pd.read_csv('data/ML/trust/X_train.csv', encoding='utf-8-sig')
y_train = pd.read_csv('data/ML/trust/y_train.csv', encoding='utf-8-sig')['Target']

print(f"\n데이터 로드 완료")
print(f"  - Train: {len(X_train)}개")
print(f"  - 피처 수: {len(X_train.columns)}개")

# Target 추가
X_train_with_target = X_train.copy()
X_train_with_target['Target'] = y_train

# ============================================================================
# 1. 전체 피처 상관관계 히트맵
# ============================================================================

print("\n" + "=" * 100)
print("1. 전체 피처 상관관계 히트맵 생성")
print("=" * 100)

# 상관관계 계산
corr_matrix = X_train_with_target.corr()

# 히트맵 생성
fig, ax = plt.subplots(figsize=(16, 14))

# 마스크 생성 (상삼각 제거)
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))

# 히트맵 그리기
sns.heatmap(corr_matrix, 
            mask=mask,
            annot=True, 
            fmt='.2f', 
            cmap='coolwarm', 
            center=0,
            square=True,
            linewidths=0.5,
            cbar_kws={"shrink": 0.8},
            ax=ax,
            vmin=-1, vmax=1)

ax.set_title('피처 간 상관관계 히트맵', fontsize=16, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig(output_dir / 'feature_correlation_heatmap.png', dpi=300, bbox_inches='tight')
print(f"✅ 저장: {output_dir / 'feature_correlation_heatmap.png'}")
plt.close()

# ============================================================================
# 2. 높은 상관관계 피처 쌍 찾기
# ============================================================================

print("\n" + "=" * 100)
print("2. 높은 상관관계 피처 쌍 분석")
print("=" * 100)

# Target 제외
corr_matrix_no_target = X_train.corr()

# 상삼각 행렬만 추출
upper_triangle = corr_matrix_no_target.where(
    np.triu(np.ones(corr_matrix_no_target.shape), k=1).astype(bool)
)

# 높은 상관관계 찾기 (절대값 0.5 이상)
high_corr_pairs = []
for column in upper_triangle.columns:
    for index in upper_triangle.index:
        value = upper_triangle.loc[index, column]
        if pd.notna(value) and abs(value) >= 0.5:
            high_corr_pairs.append({
                'Feature 1': index,
                'Feature 2': column,
                'Correlation': value
            })

# 정렬
high_corr_df = pd.DataFrame(high_corr_pairs)
if len(high_corr_df) > 0:
    high_corr_df = high_corr_df.sort_values('Correlation', key=abs, ascending=False)
    
    print(f"\n높은 상관관계 피처 쌍 (|r| >= 0.5): {len(high_corr_df)}개")
    print("\n" + "-" * 80)
    for idx, row in high_corr_df.iterrows():
        print(f"{row['Feature 1']:25s} ↔ {row['Feature 2']:25s} : {row['Correlation']:+.3f}")
    print("-" * 80)
else:
    print("\n높은 상관관계 피처 쌍이 없습니다 (|r| >= 0.5)")

# ============================================================================
# 3. Target과의 상관관계
# ============================================================================

print("\n" + "=" * 100)
print("3. Target과의 상관관계 분석")
print("=" * 100)

# Target과의 상관관계
target_corr = corr_matrix['Target'].drop('Target').sort_values(ascending=False)

# 시각화
fig, ax = plt.subplots(figsize=(12, 8))

colors = ['green' if x > 0 else 'red' for x in target_corr.values]
bars = ax.barh(range(len(target_corr)), target_corr.values, color=colors, alpha=0.7)

ax.set_yticks(range(len(target_corr)))
ax.set_yticklabels(target_corr.index)
ax.set_xlabel('상관계수', fontsize=12)
ax.set_title('피처-Target 상관관계', fontsize=14, fontweight='bold')
ax.axvline(0, color='black', linewidth=0.8)
ax.grid(axis='x', alpha=0.3)

# 값 표시
for i, (v, bar) in enumerate(zip(target_corr.values, bars)):
    ax.text(v, i, f' {v:+.3f}', va='center', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / 'target_correlation.png', dpi=300, bbox_inches='tight')
print(f"✅ 저장: {output_dir / 'target_correlation.png'}")
plt.close()

print(f"\nTarget과의 상관관계 (상위 5개):")
for feat, corr in target_corr.head(5).items():
    print(f"  {feat:25s}: {corr:+.3f}")

print(f"\nTarget과의 상관관계 (하위 5개):")
for feat, corr in target_corr.tail(5).items():
    print(f"  {feat:25s}: {corr:+.3f}")

# ============================================================================
# 4. 피처 그룹별 상관관계
# ============================================================================

print("\n" + "=" * 100)
print("4. 피처 그룹별 상관관계")
print("=" * 100)

# 피처 그룹 정의
feature_groups = {
    '실적': ['등록매물_log', '총거래활동량_log', '1인당_거래량_log'],
    '인력': ['총_직원수', '중개보조원_비율', '자격증_보유비율'],
    '경험': ['운영기간_년', '숙련도_지수', '운영_안정성'],
    '구조': ['대형사무소'],
    '대표자': ['대표_공인중개사', '대표_법인'],
    '지역': ['지역_경쟁강도', '1층_여부']
}

fig, axes = plt.subplots(2, 3, figsize=(18, 12))
axes = axes.flatten()

for idx, (group_name, features) in enumerate(feature_groups.items()):
    # 해당 그룹 피처만 선택
    available_features = [f for f in features if f in X_train.columns]
    
    if len(available_features) > 1:
        group_corr = X_train[available_features].corr()
        
        # 히트맵
        sns.heatmap(group_corr, 
                    annot=True, 
                    fmt='.2f', 
                    cmap='coolwarm', 
                    center=0,
                    square=True,
                    linewidths=1,
                    cbar_kws={"shrink": 0.8},
                    ax=axes[idx],
                    vmin=-1, vmax=1)
        
        axes[idx].set_title(f'{group_name} 그룹 상관관계', fontsize=12, fontweight='bold')
    else:
        axes[idx].text(0.5, 0.5, f'{group_name}\n(피처 1개)', 
                      ha='center', va='center', fontsize=12)
        axes[idx].axis('off')

# 마지막 subplot 제거
if len(feature_groups) < 6:
    axes[-1].remove()

plt.tight_layout()
plt.savefig(output_dir / 'group_correlation.png', dpi=300, bbox_inches='tight')
print(f"✅ 저장: {output_dir / 'group_correlation.png'}")
plt.close()

# ============================================================================
# 요약
# ============================================================================

print("\n" + "=" * 100)
print("피처 상관관계 분석 완료!")
print("=" * 100)
print(f"\n📁 결과 저장 위치: {output_dir}")
print(f"\n생성된 파일:")
print(f"  1. feature_correlation_heatmap.png - 전체 피처 상관관계")
print(f"  2. target_correlation.png - Target과의 상관관계")
print(f"  3. group_correlation.png - 그룹별 상관관계")

print("\n📊 주요 발견:")
print(f"  - 전체 피처 수: {len(X_train.columns)}개")
print(f"  - 높은 상관관계 쌍: {len(high_corr_df) if len(high_corr_df) > 0 else 0}개")
print(f"  - Target과 가장 높은 상관: {target_corr.index[0]} ({target_corr.values[0]:+.3f})")

print("\n" + "=" * 100)
