"""
Operating Period Statistics
============================
운영기간 전체 통계 및 분포 분석
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 결과 저장 디렉토리
output_dir = Path("apps/reco/models/trust_model/analysis/results")
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 100)
print("운영기간 전체 통계 분석")
print("=" * 100)

# 데이터 로드
df = pd.read_csv('data/ML/preprocessed_office_data.csv', encoding='utf-8-sig')
train_target = pd.read_csv('data/ML/trust/train_target.csv', encoding='utf-8-sig')

# Target 병합
df_with_target = df.merge(train_target[['등록번호', 'Target']], on='등록번호', how='inner')

# 운영기간 계산
df_with_target['등록일'] = pd.to_datetime(df_with_target['등록일'], errors='coerce')
today = pd.Timestamp.now()
df_with_target['운영기간_년'] = ((today - df_with_target['등록일']).dt.days / 365.25).fillna(0)

print(f"\n데이터 로드 완료: {len(df_with_target)}개")

# 통계 계산
mean_period = df_with_target['운영기간_년'].mean()
median_period = df_with_target['운영기간_년'].median()
std_period = df_with_target['운영기간_년'].std()
min_period = df_with_target['운영기간_년'].min()
max_period = df_with_target['운영기간_년'].max()
q25 = df_with_target['운영기간_년'].quantile(0.25)
q75 = df_with_target['운영기간_년'].quantile(0.75)

# ============================================================================
# 시각화
# ============================================================================

fig = plt.figure(figsize=(20, 12))
gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)

# 1. 히스토그램
ax1 = fig.add_subplot(gs[0, :2])

n, bins, patches = ax1.hist(df_with_target['운영기간_년'], bins=50, 
                             edgecolor='black', color='skyblue', alpha=0.7)

# 평균, 중앙값 표시
ax1.axvline(mean_period, color='red', linestyle='--', linewidth=2, label=f'평균: {mean_period:.2f}년')
ax1.axvline(median_period, color='green', linestyle='--', linewidth=2, label=f'중앙값: {median_period:.2f}년')
ax1.axvline(q25, color='orange', linestyle=':', linewidth=2, label=f'25%: {q25:.2f}년')
ax1.axvline(q75, color='purple', linestyle=':', linewidth=2, label=f'75%: {q75:.2f}년')

ax1.set_title('운영기간 분포', fontsize=14, fontweight='bold')
ax1.set_xlabel('운영기간 (년)')
ax1.set_ylabel('빈도')
ax1.legend(fontsize=11)
ax1.grid(axis='y', alpha=0.3)

# 2. 통계 요약
ax2 = fig.add_subplot(gs[0, 2])
ax2.axis('off')

stats_text = f"""
운영기간 통계

평균: {mean_period:.2f}년
중앙값: {median_period:.2f}년
표준편차: {std_period:.2f}년

최소: {min_period:.2f}년
최대: {max_period:.2f}년

25% 분위: {q25:.2f}년
75% 분위: {q75:.2f}년

총 사무소: {len(df_with_target)}개
"""

ax2.text(0.1, 0.5, stats_text, fontsize=12, verticalalignment='center',
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
         family='monospace')

# 3. Boxplot
ax3 = fig.add_subplot(gs[1, 0])

bp = ax3.boxplot([df_with_target['운영기간_년']], 
                  vert=True, patch_artist=True, widths=0.5)
bp['boxes'][0].set_facecolor('lightgreen')

ax3.set_title('운영기간 박스플롯', fontsize=12, fontweight='bold')
ax3.set_ylabel('운영기간 (년)')
ax3.set_xticklabels(['전체'])
ax3.grid(axis='y', alpha=0.3)

# 통계값 표시
ax3.text(1.15, median_period, f'중앙값: {median_period:.2f}', fontsize=10)
ax3.text(1.15, q25, f'Q1: {q25:.2f}', fontsize=10)
ax3.text(1.15, q75, f'Q3: {q75:.2f}', fontsize=10)

# 4. 누적 분포
ax4 = fig.add_subplot(gs[1, 1:])

sorted_period = np.sort(df_with_target['운영기간_년'])
cumulative = np.arange(1, len(sorted_period) + 1) / len(sorted_period) * 100

ax4.plot(sorted_period, cumulative, linewidth=2, color='steelblue')
ax4.axvline(mean_period, color='red', linestyle='--', linewidth=2, label=f'평균: {mean_period:.2f}년')
ax4.axvline(median_period, color='green', linestyle='--', linewidth=2, label=f'중앙값: {median_period:.2f}년')
ax4.axhline(50, color='gray', linestyle=':', alpha=0.5)
ax4.axhline(25, color='gray', linestyle=':', alpha=0.5)
ax4.axhline(75, color='gray', linestyle=':', alpha=0.5)

ax4.set_title('운영기간 누적 분포', fontsize=12, fontweight='bold')
ax4.set_xlabel('운영기간 (년)')
ax4.set_ylabel('누적 비율 (%)')
ax4.legend()
ax4.grid(alpha=0.3)

# 5. 운영기간 구간별 분포
ax5 = fig.add_subplot(gs[2, 0])

bins_custom = [0, 1, 2, 3, 5, 10, 100]
labels_custom = ['0-1년', '1-2년', '2-3년', '3-5년', '5-10년', '10년+']
df_with_target['운영기간_구간'] = pd.cut(df_with_target['운영기간_년'], 
                                      bins=bins_custom, labels=labels_custom)

period_dist = df_with_target['운영기간_구간'].value_counts().sort_index()

ax5.bar(range(len(period_dist)), period_dist.values, 
        color='lightcoral', edgecolor='black')
ax5.set_xticks(range(len(period_dist)))
ax5.set_xticklabels(period_dist.index, rotation=45)
ax5.set_title('운영기간 구간별 분포', fontsize=12, fontweight='bold')
ax5.set_ylabel('사무소 수')
ax5.grid(axis='y', alpha=0.3)

for i, v in enumerate(period_dist.values):
    pct = v / len(df_with_target) * 100
    ax5.text(i, v + 2, f'{v}개\n({pct:.1f}%)', ha='center', fontsize=9, fontweight='bold')

# 6. 운영기간별 평균 신뢰도
ax6 = fig.add_subplot(gs[2, 1])

avg_grade_by_period = df_with_target.groupby('운영기간_구간', observed=True)['Target'].mean()

ax6.bar(range(len(avg_grade_by_period)), avg_grade_by_period.values, 
        color='lightyellow', edgecolor='black')
ax6.set_xticks(range(len(avg_grade_by_period)))
ax6.set_xticklabels(avg_grade_by_period.index, rotation=45)
ax6.set_title('구간별 평균 신뢰도 등급', fontsize=12, fontweight='bold')
ax6.set_ylabel('평균 Target (0=C, 1=B, 2=A)')
ax6.axhline(1.0, color='blue', linestyle='--', alpha=0.5, label='B등급')
ax6.legend()
ax6.grid(axis='y', alpha=0.3)

for i, v in enumerate(avg_grade_by_period.values):
    ax6.text(i, v + 0.05, f'{v:.2f}', ha='center', fontweight='bold')

# 7. 등급별 평균 운영기간
ax7 = fig.add_subplot(gs[2, 2])

grade_labels = ['C등급 (0)', 'B등급 (1)', 'A등급 (2)']
colors_grade = ['lightcoral', 'lightyellow', 'lightgreen']

avg_period_by_grade = df_with_target.groupby('Target')['운영기간_년'].mean()

ax7.bar(range(len(avg_period_by_grade)), avg_period_by_grade.values, 
        color=colors_grade, edgecolor='black')
ax7.set_xticks(range(len(avg_period_by_grade)))
ax7.set_xticklabels(grade_labels)
ax7.set_title('등급별 평균 운영기간', fontsize=12, fontweight='bold')
ax7.set_ylabel('평균 운영기간 (년)')
ax7.axhline(mean_period, color='red', linestyle='--', alpha=0.5, label=f'전체 평균: {mean_period:.2f}년')
ax7.legend()
ax7.grid(axis='y', alpha=0.3)

for i, v in enumerate(avg_period_by_grade.values):
    ax7.text(i, v + 0.3, f'{v:.2f}년', ha='center', fontweight='bold')

plt.savefig(output_dir / '07_operating_period_statistics.png', dpi=300, bbox_inches='tight')
print(f"\n✅ 저장: {output_dir / '07_operating_period_statistics.png'}")
plt.close()

# ============================================================================
# 요약 출력
# ============================================================================

print("\n" + "=" * 100)
print("운영기간 통계 요약")
print("=" * 100)

print(f"\n📊 기본 통계:")
print(f"  - 평균: {mean_period:.2f}년")
print(f"  - 중앙값: {median_period:.2f}년")
print(f"  - 표준편차: {std_period:.2f}년")
print(f"  - 최소: {min_period:.2f}년")
print(f"  - 최대: {max_period:.2f}년")

print(f"\n📈 분위수:")
print(f"  - 25% 분위: {q25:.2f}년")
print(f"  - 50% 분위 (중앙값): {median_period:.2f}년")
print(f"  - 75% 분위: {q75:.2f}년")

print(f"\n🏢 구간별 분포:")
for period, count in period_dist.items():
    pct = count / len(df_with_target) * 100
    print(f"  - {period}: {count}개 ({pct:.1f}%)")

print(f"\n🎯 등급별 평균 운영기간:")
for grade, period in avg_period_by_grade.items():
    grade_name = grade_labels[grade]
    print(f"  - {grade_name}: {period:.2f}년")

print("\n" + "=" * 100)
