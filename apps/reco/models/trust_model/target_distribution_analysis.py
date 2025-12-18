"""
Target Distribution Analysis
=============================
타겟 생성 과정 및 분포 시각화
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
output_dir = Path("apps/reco/models/trust_model/results/presentation")
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 100)
print("타겟 분포 분석")
print("=" * 100)

# 데이터 로드
train_target = pd.read_csv('data/ML/trust/train_target.csv', encoding='utf-8-sig')
test_target = pd.read_csv('data/ML/trust/test_target.csv', encoding='utf-8-sig')

# 전체 타겟 데이터
all_target = pd.concat([train_target, test_target], ignore_index=True)

print(f"\n전체 데이터: {len(all_target)}개")
print(f"Train: {len(train_target)}개")
print(f"Test: {len(test_target)}개")

# ============================================================================
# 타겟 생성 과정 시각화
# ============================================================================

fig = plt.figure(figsize=(20, 16))
gs = fig.add_gridspec(4, 3, hspace=0.35, wspace=0.3)

# ============================================================================
# 1단계: 원본 데이터 분포
# ============================================================================

# 1-1. 자격점수 분포
ax1 = fig.add_subplot(gs[0, 0])
ax1.hist(all_target['자격점수'], bins=30, edgecolor='black', color='lightblue', alpha=0.7)
ax1.set_title('1-1. 자격점수 분포', fontsize=12, fontweight='bold')
ax1.set_xlabel('자격점수')
ax1.set_ylabel('빈도')
ax1.grid(axis='y', alpha=0.3)
ax1.axvline(all_target['자격점수'].mean(), color='red', linestyle='--', 
            label=f'평균: {all_target["자격점수"].mean():.2f}')
ax1.legend()

# 1-2. 지역별 성사율 Z-Score 분포
ax2 = fig.add_subplot(gs[0, 1])
ax2.hist(all_target['지역별_성사율_Z'], bins=30, edgecolor='black', color='lightcoral', alpha=0.7)
ax2.set_title('1-2. 지역별 성사율 Z-Score 분포', fontsize=12, fontweight='bold')
ax2.set_xlabel('성사율 Z-Score')
ax2.set_ylabel('빈도')
ax2.grid(axis='y', alpha=0.3)
ax2.axvline(all_target['지역별_성사율_Z'].mean(), color='red', linestyle='--', 
            label=f'평균: {all_target["지역별_성사율_Z"].mean():.3f}')
ax2.legend()

# 1-3. 가중치 설명
ax3 = fig.add_subplot(gs[0, 2])
ax3.axis('off')
formula_text = """
타겟 계산 공식

신뢰도점수 = 
  (지역별_성사율_Z × 0.7) 
  + (자격점수_Z × 0.3)

가중치:
• 성사율 (실력): 70%
• 자격점수 (신뢰): 30%

등급 분류:
• A등급: 상위 30%
• B등급: 중위 40%
• C등급: 하위 30%
"""
ax3.text(0.1, 0.5, formula_text, fontsize=11, verticalalignment='center',
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8),
         family='monospace')

# ============================================================================
# 2단계: 신뢰도점수 (가중 합산)
# ============================================================================

# 2-1. 신뢰도점수 분포 (연속형)
신뢰도_ax = fig.add_subplot(gs[1, :])
신뢰도_ax.hist(all_target['신뢰도점수'], bins=50, edgecolor='black', color='skyblue', alpha=0.7)
신뢰도_ax.set_title('2단계: 신뢰도점수 분포 (가중 합산 결과)', fontsize=14, fontweight='bold')
신뢰도_ax.set_xlabel('신뢰도점수')
신뢰도_ax.set_ylabel('빈도')
신뢰도_ax.grid(axis='y', alpha=0.3)

# 통계 정보
mean_score = all_target['신뢰도점수'].mean()
std_score = all_target['신뢰도점수'].std()
median_score = all_target['신뢰도점수'].median()

신뢰도_ax.axvline(mean_score, color='red', linestyle='--', linewidth=2, label=f'평균: {mean_score:.3f}')
신뢰도_ax.axvline(median_score, color='green', linestyle='--', linewidth=2, label=f'중앙값: {median_score:.3f}')
신뢰도_ax.legend(fontsize=11)

# 통계 텍스트
stats_text = f'평균: {mean_score:.3f}\n표준편차: {std_score:.3f}\n최소: {all_target["신뢰도점수"].min():.3f}\n최대: {all_target["신뢰도점수"].max():.3f}'
신뢰도_ax.text(0.02, 0.98, stats_text, transform=신뢰도_ax.transAxes, 
         fontsize=10, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# ============================================================================
# 3단계: 등급 분류 기준
# ============================================================================

# 2. 등급 분류 기준 시각화
ax2 = fig.add_subplot(gs[2, :])

# 신뢰도점수를 정렬하여 누적 분포 그리기
sorted_z = np.sort(all_target['신뢰도점수'])
cumulative = np.arange(1, len(sorted_z) + 1) / len(sorted_z) * 100

ax2.plot(sorted_z, cumulative, linewidth=2, color='steelblue')
ax2.set_title('3단계: 등급 분류 기준 (누적 분포)', fontsize=14, fontweight='bold')
ax2.set_xlabel('신뢰도점수')
ax2.set_ylabel('누적 비율 (%)')
ax2.grid(alpha=0.3)

# 분류 기준선 표시
# C등급: 하위 30% (신뢰도점수 < 30th percentile)
# B등급: 중위 40% (30th ~ 70th percentile)
# A등급: 상위 30% (신뢰도점수 >= 70th percentile)

p30 = np.percentile(all_target['신뢰도점수'], 30)
p70 = np.percentile(all_target['신뢰도점수'], 70)

ax2.axhline(30, color='red', linestyle='--', linewidth=2, alpha=0.7)
ax2.axhline(70, color='green', linestyle='--', linewidth=2, alpha=0.7)
ax2.axvline(p30, color='red', linestyle='--', linewidth=2, alpha=0.7, 
            label=f'C/B 경계: {p30:.3f} (30%)')
ax2.axvline(p70, color='green', linestyle='--', linewidth=2, alpha=0.7, 
            label=f'B/A 경계: {p70:.3f} (70%)')

# 영역 색칠
ax2.fill_between(sorted_z, 0, cumulative, where=(sorted_z < p30), 
                  alpha=0.2, color='red', label='C등급 (하위 30%)')
ax2.fill_between(sorted_z, 0, cumulative, where=((sorted_z >= p30) & (sorted_z < p70)), 
                  alpha=0.2, color='yellow', label='B등급 (중위 40%)')
ax2.fill_between(sorted_z, 0, cumulative, where=(sorted_z >= p70), 
                  alpha=0.2, color='green', label='A등급 (상위 30%)')

ax2.legend(fontsize=11, loc='lower right')
ax2.set_ylim([0, 105])

# 3. 최종 등급 분포 (Train)
ax3 = fig.add_subplot(gs[3, 0])

train_dist = train_target['Target'].value_counts().sort_index()
colors = ['lightcoral', 'lightyellow', 'lightgreen']
labels = ['C등급 (0)', 'B등급 (1)', 'A등급 (2)']

ax3.bar(labels, train_dist.values, color=colors, edgecolor='black')
ax3.set_title('4단계: Train 등급 분포', fontsize=12, fontweight='bold')
ax3.set_ylabel('샘플 수')
ax3.grid(axis='y', alpha=0.3)

for i, v in enumerate(train_dist.values):
    percentage = v / len(train_target) * 100
    ax3.text(i, v + 2, f'{v}개\n({percentage:.1f}%)', ha='center', fontweight='bold')

# 4. 최종 등급 분포 (Test)
ax4 = fig.add_subplot(gs[3, 1])

test_dist = test_target['Target'].value_counts().sort_index()

ax4.bar(labels, test_dist.values, color=colors, edgecolor='black')
ax4.set_title('4단계: Test 등급 분포', fontsize=12, fontweight='bold')
ax4.set_ylabel('샘플 수')
ax4.grid(axis='y', alpha=0.3)

for i, v in enumerate(test_dist.values):
    percentage = v / len(test_target) * 100
    ax4.text(i, v + 1, f'{v}개\n({percentage:.1f}%)', ha='center', fontweight='bold')

# 5. 전체 등급 분포 (Pie Chart)
ax5 = fig.add_subplot(gs[3, 2])

all_dist = all_target['Target'].value_counts().sort_index()
explode = (0.05, 0, 0.05)  # A, B, C 강조

ax5.pie(all_dist.values, labels=labels, autopct='%1.1f%%', 
        colors=colors, explode=explode, startangle=90,
        textprops={'fontsize': 11, 'fontweight': 'bold'})
ax5.set_title('전체 등급 분포', fontsize=12, fontweight='bold')

plt.savefig(output_dir / '00_target_distribution.png', dpi=300, bbox_inches='tight')
print(f"\n✅ 저장: {output_dir / '00_target_distribution.png'}")
plt.close()

# ============================================================================
# 등급별 Z-Score 분포 비교
# ============================================================================

fig, axes = plt.subplots(1, 2, figsize=(15, 5))

# 1. Boxplot
box_data = [all_target[all_target['Target'] == i]['신뢰도점수'].dropna() for i in range(3)]
bp = axes[0].boxplot(box_data, tick_labels=labels, patch_artist=True)
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)

axes[0].set_title('등급별 신뢰도점수 분포 (Boxplot)', fontsize=14, fontweight='bold')
axes[0].set_ylabel('신뢰도점수')
axes[0].grid(axis='y', alpha=0.3)

# 평균값 표시
for i in range(3):
    mean_val = all_target[all_target['Target'] == i]['신뢰도점수'].mean()
    axes[0].plot(i+1, mean_val, 'r*', markersize=15, label='평균' if i == 0 else '')
    axes[0].text(i+1, mean_val, f'{mean_val:.3f}', ha='center', va='bottom', fontweight='bold')

axes[0].legend()

# 2. Violin Plot
parts = axes[1].violinplot(box_data, positions=range(3), showmeans=True, showmedians=True)
for i, pc in enumerate(parts['bodies']):
    pc.set_facecolor(colors[i])
    pc.set_alpha(0.7)

axes[1].set_xticks(range(3))
axes[1].set_xticklabels(labels)
axes[1].set_title('등급별 신뢰도점수 분포 (Violin Plot)', fontsize=14, fontweight='bold')
axes[1].set_ylabel('신뢰도점수')
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / '00_target_zscore_comparison.png', dpi=300, bbox_inches='tight')
print(f"✅ 저장: {output_dir / '00_target_zscore_comparison.png'}")
plt.close()

# ============================================================================
# 요약 통계
# ============================================================================

print("\n" + "=" * 100)
print("타겟 분포 요약")
print("=" * 100)

print(f"\n📊 전체 데이터 ({len(all_target)}개)")
print(f"  - C등급 (0): {all_dist[0]}개 ({all_dist[0]/len(all_target)*100:.1f}%)")
print(f"  - B등급 (1): {all_dist[1]}개 ({all_dist[1]/len(all_target)*100:.1f}%)")
print(f"  - A등급 (2): {all_dist[2]}개 ({all_dist[2]/len(all_target)*100:.1f}%)")

print(f"\n📊 신뢰도점수 통계")
print(f"  - 평균: {mean_score:.3f}")
print(f"  - 표준편차: {std_score:.3f}")
print(f"  - 최소: {all_target['신뢰도점수'].min():.3f}")
print(f"  - 최대: {all_target['신뢰도점수'].max():.3f}")

print(f"\n📊 등급 분류 기준")
print(f"  - C등급: 신뢰도점수 < {p30:.3f} (하위 30%)")
print(f"  - B등급: {p30:.3f} <= 신뢰도점수 < {p70:.3f} (중위 40%)")
print(f"  - A등급: 신뢰도점수 >= {p70:.3f} (상위 30%)")

print(f"\n📊 등급별 평균 신뢰도점수")
for i in range(3):
    grade_mean = all_target[all_target['Target'] == i]['신뢰도점수'].mean()
    grade_std = all_target[all_target['Target'] == i]['신뢰도점수'].std()
    print(f"  - {labels[i]}: {grade_mean:.3f} (±{grade_std:.3f})")

print("\n" + "=" * 100)
print("타겟 분포 분석 완료!")
print("=" * 100)
print(f"\n📁 결과 저장 위치: {output_dir}")
print(f"\n생성된 파일:")
print(f"  1. 00_target_distribution.png - 타겟 생성 과정 및 분포")
print(f"  2. 00_target_zscore_comparison.png - 등급별 Z-Score 비교")
print("\n" + "=" * 100)
