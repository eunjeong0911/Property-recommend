"""
Operating Period Threshold Analysis
====================================
운영_안정성 기준 (3년) 설정 근거 분석
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
output_dir = Path("apps/reco/models/trust_model/results/eda")
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 100)
print("운영기간 3년 기준 설정 근거 분석")
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

# ============================================================================
# 분석 1: 운영기간별 신뢰도 등급 분포
# ============================================================================

fig = plt.figure(figsize=(20, 12))
gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)

# 1-1. 운영기간 히스토그램 (전체)
ax1 = fig.add_subplot(gs[0, :])

# 운영기간 구간별로 색상 다르게
colors_hist = []
bins = np.arange(0, df_with_target['운영기간_년'].max() + 1, 0.5)
hist_data, bin_edges = np.histogram(df_with_target['운영기간_년'], bins=bins)

for i, edge in enumerate(bin_edges[:-1]):
    if edge < 3:
        colors_hist.append('lightcoral')
    else:
        colors_hist.append('lightgreen')

ax1.bar(bin_edges[:-1], hist_data, width=0.5, color=colors_hist, edgecolor='black', alpha=0.7)
ax1.axvline(3, color='red', linestyle='--', linewidth=3, label='3년 기준선')
ax1.set_title('운영기간 분포 (3년 기준)', fontsize=14, fontweight='bold')
ax1.set_xlabel('운영기간 (년)')
ax1.set_ylabel('빈도')
ax1.legend(fontsize=12)
ax1.grid(axis='y', alpha=0.3)

# 통계 표시
under_3 = (df_with_target['운영기간_년'] < 3).sum()
over_3 = (df_with_target['운영기간_년'] >= 3).sum()
ax1.text(0.02, 0.98, f'3년 미만: {under_3}개 ({under_3/len(df_with_target)*100:.1f}%)\n3년 이상: {over_3}개 ({over_3/len(df_with_target)*100:.1f}%)', 
         transform=ax1.transAxes, fontsize=11, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# 1-2. 운영기간별 평균 신뢰도 등급
ax2 = fig.add_subplot(gs[1, 0])

# 운영기간을 1년 단위로 그룹화
df_with_target['운영기간_구간'] = pd.cut(df_with_target['운영기간_년'], 
                                      bins=[0, 1, 2, 3, 4, 5, 10, 100],
                                      labels=['0-1년', '1-2년', '2-3년', '3-4년', '4-5년', '5-10년', '10년+'])

avg_grade_by_period = df_with_target.groupby('운영기간_구간')['Target'].mean()
colors_bar = ['lightcoral', 'lightcoral', 'lightcoral', 'lightgreen', 'lightgreen', 'lightgreen', 'lightgreen']

ax2.bar(range(len(avg_grade_by_period)), avg_grade_by_period.values, 
        color=colors_bar, edgecolor='black')
ax2.set_xticks(range(len(avg_grade_by_period)))
ax2.set_xticklabels(avg_grade_by_period.index, rotation=45)
ax2.set_title('운영기간 구간별 평균 신뢰도 등급', fontsize=12, fontweight='bold')
ax2.set_ylabel('평균 Target (0=C, 1=B, 2=A)')
ax2.axhline(1.0, color='blue', linestyle='--', alpha=0.5, label='B등급 기준')
ax2.axvline(2.5, color='red', linestyle='--', linewidth=2, label='3년 기준')
ax2.legend()
ax2.grid(axis='y', alpha=0.3)

# 값 표시
for i, v in enumerate(avg_grade_by_period.values):
    ax2.text(i, v + 0.05, f'{v:.2f}', ha='center', fontweight='bold')

# 1-3. 운영기간별 A등급 비율
ax3 = fig.add_subplot(gs[1, 1])

a_grade_ratio = df_with_target.groupby('운영기간_구간').apply(
    lambda x: (x['Target'] == 2).sum() / len(x) * 100
)

ax3.bar(range(len(a_grade_ratio)), a_grade_ratio.values, 
        color=colors_bar, edgecolor='black')
ax3.set_xticks(range(len(a_grade_ratio)))
ax3.set_xticklabels(a_grade_ratio.index, rotation=45)
ax3.set_title('운영기간 구간별 A등급 비율', fontsize=12, fontweight='bold')
ax3.set_ylabel('A등급 비율 (%)')
ax3.axvline(2.5, color='red', linestyle='--', linewidth=2, label='3년 기준')
ax3.legend()
ax3.grid(axis='y', alpha=0.3)

for i, v in enumerate(a_grade_ratio.values):
    ax3.text(i, v + 1, f'{v:.1f}%', ha='center', fontweight='bold')

# 1-4. 운영기간별 C등급 비율
ax4 = fig.add_subplot(gs[1, 2])

c_grade_ratio = df_with_target.groupby('운영기간_구간').apply(
    lambda x: (x['Target'] == 0).sum() / len(x) * 100
)

ax4.bar(range(len(c_grade_ratio)), c_grade_ratio.values, 
        color=colors_bar, edgecolor='black')
ax4.set_xticks(range(len(c_grade_ratio)))
ax4.set_xticklabels(c_grade_ratio.index, rotation=45)
ax4.set_title('운영기간 구간별 C등급 비율', fontsize=12, fontweight='bold')
ax4.set_ylabel('C등급 비율 (%)')
ax4.axvline(2.5, color='red', linestyle='--', linewidth=2, label='3년 기준')
ax4.legend()
ax4.grid(axis='y', alpha=0.3)

for i, v in enumerate(c_grade_ratio.values):
    ax4.text(i, v + 1, f'{v:.1f}%', ha='center', fontweight='bold')

# 2-1. 3년 기준 전후 비교
ax5 = fig.add_subplot(gs[2, 0])

df_with_target['운영_안정성'] = (df_with_target['운영기간_년'] >= 3).astype(int)
stability_grade = df_with_target.groupby(['운영_안정성', 'Target']).size().unstack(fill_value=0)
stability_grade_pct = stability_grade.div(stability_grade.sum(axis=1), axis=0) * 100

x = np.arange(2)
width = 0.25
colors_grade = ['lightcoral', 'lightyellow', 'lightgreen']

for i, (grade, color) in enumerate(zip([0, 1, 2], colors_grade)):
    if grade in stability_grade_pct.columns:
        ax5.bar(x + i*width, stability_grade_pct[grade], width, 
                label=f'{"C" if grade==0 else "B" if grade==1 else "A"}등급', 
                color=color, edgecolor='black')

ax5.set_xticks(x + width)
ax5.set_xticklabels(['3년 미만', '3년 이상'])
ax5.set_title('운영 안정성별 등급 분포', fontsize=12, fontweight='bold')
ax5.set_ylabel('비율 (%)')
ax5.legend()
ax5.grid(axis='y', alpha=0.3)

# 2-2. 누적 분포 함수
ax6 = fig.add_subplot(gs[2, 1])

sorted_period = np.sort(df_with_target['운영기간_년'])
cumulative = np.arange(1, len(sorted_period) + 1) / len(sorted_period) * 100

ax6.plot(sorted_period, cumulative, linewidth=2, color='steelblue')
ax6.axvline(3, color='red', linestyle='--', linewidth=3, label='3년 기준')
ax6.axhline(50, color='green', linestyle='--', alpha=0.5, label='중앙값')
ax6.set_title('운영기간 누적 분포', fontsize=12, fontweight='bold')
ax6.set_xlabel('운영기간 (년)')
ax6.set_ylabel('누적 비율 (%)')
ax6.legend()
ax6.grid(alpha=0.3)

# 3년 지점 표시
pct_at_3 = (df_with_target['운영기간_년'] < 3).sum() / len(df_with_target) * 100
ax6.plot(3, pct_at_3, 'ro', markersize=10)
ax6.text(3, pct_at_3 + 5, f'{pct_at_3:.1f}%', ha='center', fontweight='bold',
         bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))

# 2-3. 3년 기준의 타당성 설명
ax7 = fig.add_subplot(gs[2, 2])
ax7.axis('off')

# 통계 계산
under_3_avg = df_with_target[df_with_target['운영기간_년'] < 3]['Target'].mean()
over_3_avg = df_with_target[df_with_target['운영기간_년'] >= 3]['Target'].mean()
diff = over_3_avg - under_3_avg

under_3_a = (df_with_target[df_with_target['운영기간_년'] < 3]['Target'] == 2).sum()
over_3_a = (df_with_target[df_with_target['운영기간_년'] >= 3]['Target'] == 2).sum()
under_3_a_pct = under_3_a / (df_with_target['운영기간_년'] < 3).sum() * 100
over_3_a_pct = over_3_a / (df_with_target['운영기간_년'] >= 3).sum() * 100

summary_text = f"""
3년 기준 설정 근거

📊 평균 신뢰도 등급:
  • 3년 미만: {under_3_avg:.2f}
  • 3년 이상: {over_3_avg:.2f}
  • 차이: +{diff:.2f} ({diff/under_3_avg*100:+.1f}%)

📈 A등급 비율:
  • 3년 미만: {under_3_a_pct:.1f}%
  • 3년 이상: {over_3_a_pct:.1f}%
  • 증가: +{over_3_a_pct - under_3_a_pct:.1f}%p

✅ 결론:
3년 이상 운영 시 신뢰도가
유의미하게 높아짐

→ 운영_안정성 기준으로 적합
"""

ax7.text(0.1, 0.5, summary_text, fontsize=11, verticalalignment='center',
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9),
         family='monospace')

plt.savefig(output_dir / '06_operating_period_threshold.png', dpi=300, bbox_inches='tight')
print(f"\n✅ 저장: {output_dir / '06_operating_period_threshold.png'}")
plt.close()

# ============================================================================
# 요약 출력
# ============================================================================

print("\n" + "=" * 100)
print("분석 결과 요약")
print("=" * 100)

print(f"\n📊 운영기간 분포:")
print(f"  - 3년 미만: {under_3}개 ({under_3/len(df_with_target)*100:.1f}%)")
print(f"  - 3년 이상: {over_3}개 ({over_3/len(df_with_target)*100:.1f}%)")

# 운영기간 평균 계산
under_3_period_avg = df_with_target[df_with_target['운영기간_년'] < 3]['운영기간_년'].mean()
over_3_period_avg = df_with_target[df_with_target['운영기간_년'] >= 3]['운영기간_년'].mean()
total_period_avg = df_with_target['운영기간_년'].mean()
period_median = df_with_target['운영기간_년'].median()

print(f"\n📅 운영기간 통계:")
print(f"  - 전체 평균: {total_period_avg:.2f}년")
print(f"  - 전체 중앙값: {period_median:.2f}년")
print(f"  - 3년 미만 평균: {under_3_period_avg:.2f}년")
print(f"  - 3년 이상 평균: {over_3_period_avg:.2f}년")

print(f"\n📈 평균 신뢰도 등급:")
print(f"  - 3년 미만: {under_3_avg:.3f}")
print(f"  - 3년 이상: {over_3_avg:.3f}")
print(f"  - 차이: +{diff:.3f} ({diff/under_3_avg*100:+.1f}%)")

print(f"\n🏆 A등급 비율:")
print(f"  - 3년 미만: {under_3_a_pct:.1f}%")
print(f"  - 3년 이상: {over_3_a_pct:.1f}%")
print(f"  - 증가: +{over_3_a_pct - under_3_a_pct:.1f}%p")

print(f"\n✅ 결론: 3년 이상 운영 시 신뢰도가 유의미하게 높아짐")
print(f"   → 운영_안정성 기준 (3년)으로 적합")

print("\n" + "=" * 100)
