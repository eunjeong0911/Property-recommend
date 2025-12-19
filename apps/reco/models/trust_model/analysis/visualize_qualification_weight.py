"""
자격점수 가중치 적용 전후 비교 시각화
- 성사율 Z-Score만 사용한 경우
- 성사율 Z-Score + 자격점수 원본 사용한 경우
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def load_data():
    """데이터 로드"""
    train_path = "data/ML/trust/train_target.csv"
    test_path = "data/ML/trust/test_target.csv"
    
    train_df = pd.read_csv(train_path, encoding="utf-8-sig")
    test_df = pd.read_csv(test_path, encoding="utf-8-sig")
    
    df = pd.concat([train_df, test_df], ignore_index=True)
    
    print(f"📊 전체 데이터: {len(df):,}개 중개사무소")
    return df

def calculate_scores_without_qualification(df):
    """
    자격점수 없이 성사율 Z-Score만 사용한 신뢰도 점수 계산
    """
    # 성사율 Z-Score만 사용 (가중치 100%)
    score_without_qual = df["지역별_성사율_Z"] * 1.0
    
    return score_without_qual

def calculate_scores_with_qualification(df):
    """
    자격점수 포함한 신뢰도 점수 (현재 방식)
    """
    # 이미 계산된 신뢰도점수 사용
    return df["신뢰도점수"]

def create_comparison_plot(df):
    """
    1. 자격점수 적용 전후 비교 그래프
    """
    # 점수 계산
    score_without_qual = calculate_scores_without_qualification(df)
    score_with_qual = calculate_scores_with_qualification(df)
    
    # 자격별로 분류
    qualifications = ["법인", "공인중개사", "중개보조원", "중개인"]
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('자격점수 가중치 적용 전후 비교\n(같은 성사율 Z-Score에서 자격에 따른 신뢰도 점수 차이)', 
                 fontsize=16, fontweight='bold', y=0.995)
    
    colors_without = '#e74c3c'  # 빨강 (자격 미반영)
    colors_with = '#2ecc71'     # 초록 (자격 반영)
    
    for idx, qual in enumerate(qualifications):
        row = idx // 2
        col = idx % 2
        ax = axes[row, col]
        
        # 해당 자격의 데이터만 필터링
        mask = df["대표자구분명"] == qual
        
        if mask.sum() == 0:
            ax.text(0.5, 0.5, f'{qual}\n데이터 없음', 
                   ha='center', va='center', fontsize=14)
            ax.set_title(f'{qual} (0개)', fontweight='bold')
            continue
        
        x = df.loc[mask, "지역별_성사율_Z"]
        y_without = score_without_qual[mask]
        y_with = score_with_qual[mask]
        
        # 산점도
        ax.scatter(x, y_without, alpha=0.5, s=50, c=colors_without, 
                  label='자격 미반영', edgecolors='black', linewidth=0.5)
        ax.scatter(x, y_with, alpha=0.5, s=50, c=colors_with, 
                  label='자격 반영', edgecolors='black', linewidth=0.5)
        
        # 추세선
        if len(x) > 1:
            z = np.polyfit(x, y_without, 1)
            p = np.poly1d(z)
            x_line = np.linspace(x.min(), x.max(), 100)
            ax.plot(x_line, p(x_line), '--', color=colors_without, alpha=0.7, linewidth=2)
            
            z2 = np.polyfit(x, y_with, 1)
            p2 = np.poly1d(z2)
            ax.plot(x_line, p2(x_line), '--', color=colors_with, alpha=0.7, linewidth=2)
        
        # 평균 차이 표시
        mean_diff = y_with.mean() - y_without.mean()
        qual_score = df.loc[mask, "자격점수"].iloc[0]
        
        ax.text(0.05, 0.95, 
               f'자격점수: {qual_score:+.1f}\n'
               f'평균 차이: {mean_diff:+.3f}\n'
               f'미반영: {y_without.mean():.3f}\n'
               f'반영: {y_with.mean():.3f}',
               transform=ax.transAxes,
               fontsize=10,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        ax.set_xlabel('지역별 성사율 Z-Score', fontsize=11, fontweight='bold')
        ax.set_ylabel('신뢰도 점수', fontsize=11, fontweight='bold')
        ax.set_title(f'{qual} ({mask.sum()}개 중개사)', fontsize=12, fontweight='bold')
        ax.legend(loc='lower right', fontsize=10)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 저장
    output_dir = Path("apps/reco/models/trust_model/analysis/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / "05_qualification_weight_comparison.png", dpi=300, bbox_inches='tight')
    print(f"✅ 저장: {output_dir / '05_qualification_weight_comparison.png'}")
    
    plt.close()

def create_overall_comparison_plot(df):
    """
    2. 전체 비교 - 히스토그램 + 박스플롯
    """
    score_without_qual = calculate_scores_without_qualification(df)
    score_with_qual = calculate_scores_with_qualification(df)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('자격점수 가중치 적용 전후 전체 비교', fontsize=16, fontweight='bold')
    
    # 1. 히스토그램 (자격 미반영)
    axes[0, 0].hist(score_without_qual, bins=50, alpha=0.7, color='#e74c3c', edgecolor='black')
    axes[0, 0].axvline(score_without_qual.mean(), color='red', linestyle='--', linewidth=2, 
                       label=f'평균: {score_without_qual.mean():.3f}')
    axes[0, 0].axvline(score_without_qual.median(), color='orange', linestyle='--', linewidth=2, 
                       label=f'중앙값: {score_without_qual.median():.3f}')
    axes[0, 0].set_xlabel('신뢰도 점수', fontsize=12, fontweight='bold')
    axes[0, 0].set_ylabel('빈도', fontsize=12, fontweight='bold')
    axes[0, 0].set_title('자격 미반영 (성사율 Z-Score만)', fontsize=13, fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(axis='y', alpha=0.3)
    
    # 2. 히스토그램 (자격 반영)
    axes[0, 1].hist(score_with_qual, bins=50, alpha=0.7, color='#2ecc71', edgecolor='black')
    axes[0, 1].axvline(score_with_qual.mean(), color='green', linestyle='--', linewidth=2, 
                       label=f'평균: {score_with_qual.mean():.3f}')
    axes[0, 1].axvline(score_with_qual.median(), color='lime', linestyle='--', linewidth=2, 
                       label=f'중앙값: {score_with_qual.median():.3f}')
    axes[0, 1].set_xlabel('신뢰도 점수', fontsize=12, fontweight='bold')
    axes[0, 1].set_ylabel('빈도', fontsize=12, fontweight='bold')
    axes[0, 1].set_title('자격 반영 (성사율 70% + 자격 30%)', fontsize=13, fontweight='bold')
    axes[0, 1].legend()
    axes[0, 1].grid(axis='y', alpha=0.3)
    
    # 3. 박스플롯 비교
    box_data = [score_without_qual, score_with_qual]
    bp = axes[1, 0].boxplot(box_data, labels=['자격 미반영', '자격 반영'],
                            patch_artist=True, widths=0.6)
    bp['boxes'][0].set_facecolor('#e74c3c')
    bp['boxes'][1].set_facecolor('#2ecc71')
    axes[1, 0].set_ylabel('신뢰도 점수', fontsize=12, fontweight='bold')
    axes[1, 0].set_title('분포 비교 (박스플롯)', fontsize=13, fontweight='bold')
    axes[1, 0].grid(axis='y', alpha=0.3)
    
    # 통계 정보 추가
    stats_text = f"자격 미반영:\n  평균: {score_without_qual.mean():.3f}\n  표준편차: {score_without_qual.std():.3f}\n  범위: [{score_without_qual.min():.3f}, {score_without_qual.max():.3f}]\n\n"
    stats_text += f"자격 반영:\n  평균: {score_with_qual.mean():.3f}\n  표준편차: {score_with_qual.std():.3f}\n  범위: [{score_with_qual.min():.3f}, {score_with_qual.max():.3f}]"
    axes[1, 0].text(0.5, 0.02, stats_text, transform=axes[1, 0].transAxes,
                   fontsize=9, verticalalignment='bottom', horizontalalignment='center',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # 4. 산점도 (전후 비교)
    axes[1, 1].scatter(score_without_qual, score_with_qual, alpha=0.5, s=30, 
                      c=df["Target"], cmap='RdYlGn', edgecolors='black', linewidth=0.5)
    
    # 대각선 (y=x)
    min_val = min(score_without_qual.min(), score_with_qual.min())
    max_val = max(score_without_qual.max(), score_with_qual.max())
    axes[1, 1].plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, linewidth=2, label='y=x')
    
    axes[1, 1].set_xlabel('자격 미반영', fontsize=12, fontweight='bold')
    axes[1, 1].set_ylabel('자격 반영', fontsize=12, fontweight='bold')
    axes[1, 1].set_title('점수 변화 (색상: 등급)', fontsize=13, fontweight='bold')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    # 상관계수
    corr = np.corrcoef(score_without_qual, score_with_qual)[0, 1]
    axes[1, 1].text(0.05, 0.95, f'상관계수: {corr:.4f}',
                   transform=axes[1, 1].transAxes,
                   fontsize=11, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    
    # 저장
    output_dir = Path("apps/reco/models/trust_model/analysis/results")
    plt.savefig(output_dir / "06_overall_qualification_comparison.png", dpi=300, bbox_inches='tight')
    print(f"✅ 저장: {output_dir / '06_overall_qualification_comparison.png'}")
    
    plt.close()

def create_qualification_distribution(df):
    """
    3. 자격점수 분포 시각화
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('자격점수 분포 및 가중치 적용', fontsize=16, fontweight='bold')
    
    # 1. 자격점수 분포
    ax1 = axes[0]
    
    qualifications = ["법인", "공인중개사", "중개보조원", "중개인"]
    qual_values = [2.0, 0.0, -1.0, -3.0]
    qual_colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c']
    
    for qual, val, color in zip(qualifications, qual_values, qual_colors):
        count = (df["대표자구분명"] == qual).sum()
        ax1.bar(qual, val, color=color, edgecolor='black', linewidth=1.5, alpha=0.7)
        ax1.text(qual, val + 0.1 if val >= 0 else val - 0.3, 
                f'{count}개\n({count/len(df)*100:.1f}%)',
                ha='center', fontsize=10, fontweight='bold')
    
    ax1.axhline(0, color='black', linestyle='-', linewidth=1)
    ax1.set_ylabel('자격점수', fontsize=12, fontweight='bold')
    ax1.set_title('자격별 점수 분포', fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    ax1.set_ylim(-4, 3)
    
    # 2. 가중치 적용 후 기여도
    ax2 = axes[1]
    
    # 각 자격의 평균 기여도 계산
    contributions = []
    for qual in qualifications:
        mask = df["대표자구분명"] == qual
        if mask.sum() > 0:
            # 자격점수 기여도 = 자격점수 × 0.3
            qual_score = df.loc[mask, "자격점수"].iloc[0]
            contribution = qual_score * 0.3
            contributions.append(contribution)
        else:
            contributions.append(0)
    
    for qual, contrib, color in zip(qualifications, contributions, qual_colors):
        count = (df["대표자구분명"] == qual).sum()
        ax2.bar(qual, contrib, color=color, edgecolor='black', linewidth=1.5, alpha=0.7)
        ax2.text(qual, contrib + 0.05 if contrib >= 0 else contrib - 0.1, 
                f'{contrib:+.2f}\n({count}개)',
                ha='center', fontsize=10, fontweight='bold')
    
    ax2.axhline(0, color='black', linestyle='-', linewidth=1)
    ax2.set_ylabel('신뢰도 점수 기여도', fontsize=12, fontweight='bold')
    ax2.set_title('자격점수 기여도 (가중치 30% 적용)', fontsize=13, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    # 공식 표시
    formula_text = "신뢰도점수 = (성사율_Z × 0.7) + (자격점수 × 0.3)\n\n"
    formula_text += "자격점수:\n"
    formula_text += "  법인: +2.0 → 기여도: +0.6\n"
    formula_text += "  공인중개사: 0.0 → 기여도: 0.0\n"
    formula_text += "  중개보조원: -1.0 → 기여도: -0.3\n"
    formula_text += "  중개인: -3.0 → 기여도: -0.9"
    
    ax2.text(0.5, 0.02, formula_text,
            transform=ax2.transAxes,
            fontsize=9, verticalalignment='bottom', horizontalalignment='center',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
            family='monospace')
    
    plt.tight_layout()
    
    # 저장
    output_dir = Path("apps/reco/models/trust_model/analysis/results")
    plt.savefig(output_dir / "07_qualification_score_distribution.png", dpi=300, bbox_inches='tight')
    print(f"✅ 저장: {output_dir / '07_qualification_score_distribution.png'}")
    
    plt.close()

def calculate_grade_changes(df):
    """
    등급 변화 계산
    """
    # 성사율만 사용한 점수
    score_without_qual = df["지역별_성사율_Z"] * 1.0
    
    # 등급 분위수 계산
    threshold_high = score_without_qual.quantile(0.70)
    threshold_low = score_without_qual.quantile(0.30)
    
    def get_grade(score):
        if score >= threshold_high:
            return 2  # A
        elif score >= threshold_low:
            return 1  # B
        else:
            return 0  # C
    
    grade_without_qual = score_without_qual.apply(get_grade)
    grade_with_qual = df["Target"]
    
    # 등급 변화
    grade_change = grade_with_qual - grade_without_qual
    
    return grade_without_qual, grade_with_qual, grade_change

def create_grade_change_table(df):
    """
    4. 자격별 등급 변화 표 시각화
    """
    # 등급 변화 계산
    grade_without, grade_with, grade_change = calculate_grade_changes(df)
    
    df_temp = df.copy()
    df_temp["등급_성사율만"] = grade_without
    df_temp["등급_자격포함"] = grade_with
    df_temp["등급변화"] = grade_change
    
    # 자격별 통계 계산
    qualifications = ["법인", "공인중개사", "중개보조원", "중개인"]
    
    table_data = []
    for qual in qualifications:
        mask = df_temp["대표자구분명"] == qual
        if mask.sum() == 0:
            continue
        
        total = mask.sum()
        upgraded = (df_temp.loc[mask, "등급변화"] > 0).sum()
        maintained = (df_temp.loc[mask, "등급변화"] == 0).sum()
        downgraded = (df_temp.loc[mask, "등급변화"] < 0).sum()
        avg_change = df_temp.loc[mask, "등급변화"].mean()
        
        table_data.append({
            "자격": qual,
            "총 개수": total,
            "상승": upgraded,
            "상승%": f"{upgraded/total*100:.1f}%",
            "유지": maintained,
            "유지%": f"{maintained/total*100:.1f}%",
            "하락": downgraded,
            "하락%": f"{downgraded/total*100:.1f}%",
            "평균변화": f"{avg_change:+.3f}"
        })
    
    # 표 생성
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.suptitle('자격별 등급 변화 통계', fontsize=16, fontweight='bold')
    
    ax.axis('tight')
    ax.axis('off')
    
    # 데이터프레임 생성
    df_table = pd.DataFrame(table_data)
    
    # 표 생성
    table = ax.table(cellText=df_table.values,
                    colLabels=df_table.columns,
                    cellLoc='center',
                    loc='center',
                    bbox=[0, 0, 1, 1])
    
    # 스타일링
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.5)
    
    # 헤더 스타일
    for i in range(len(df_table.columns)):
        cell = table[(0, i)]
        cell.set_facecolor('#3498db')
        cell.set_text_props(weight='bold', color='white', fontsize=12)
    
    # 데이터 셀 스타일
    for i in range(1, len(df_table) + 1):
        # 자격 컬럼
        table[(i, 0)].set_facecolor('#ecf0f1')
        table[(i, 0)].set_text_props(weight='bold')
        
        # 상승 컬럼 (초록)
        table[(i, 2)].set_facecolor('#d5f4e6')
        table[(i, 3)].set_facecolor('#d5f4e6')
        
        # 유지 컬럼 (회색)
        table[(i, 4)].set_facecolor('#f0f0f0')
        table[(i, 5)].set_facecolor('#f0f0f0')
        
        # 하락 컬럼 (빨강)
        table[(i, 6)].set_facecolor('#fadbd8')
        table[(i, 7)].set_facecolor('#fadbd8')
        
        # 평균변화 컬럼
        avg_val = float(df_table.iloc[i-1]["평균변화"])
        if avg_val > 0:
            table[(i, 8)].set_facecolor('#d5f4e6')
            table[(i, 8)].set_text_props(color='#27ae60', weight='bold')
        elif avg_val < 0:
            table[(i, 8)].set_facecolor('#fadbd8')
            table[(i, 8)].set_text_props(color='#c0392b', weight='bold')
        else:
            table[(i, 8)].set_facecolor('#f0f0f0')
    
    # 설명 추가
    explanation = (
        "📊 등급 변화 분석\n"
        "• 성사율만: 지역별 성사율 Z-Score만 사용 (자격 미반영)\n"
        "• 자격포함: 성사율 70% + 자격점수 30% (현재 방식)\n"
        "• 상승: 자격점수 반영으로 등급이 올라간 중개사\n"
        "• 하락: 자격점수 반영으로 등급이 내려간 중개사\n"
        "• 평균변화: 양수(+)는 상승 경향, 음수(-)는 하락 경향"
    )
    
    ax.text(0.5, -0.15, explanation,
           transform=ax.transAxes,
           fontsize=10,
           verticalalignment='top',
           horizontalalignment='center',
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    plt.tight_layout()
    
    # 저장
    output_dir = Path("apps/reco/models/trust_model/analysis/results")
    plt.savefig(output_dir / "08_grade_change_table_by_qualification.png", dpi=300, bbox_inches='tight')
    print(f"✅ 저장: {output_dir / '08_grade_change_table_by_qualification.png'}")
    
    plt.close()


def main():
    print("=" * 60)
    print("🎯 자격점수 가중치 적용 효과 시각화")
    print("=" * 60)
    
    # 데이터 로드
    df = load_data()
    
    print("\n📈 시각화 생성 중...")
    
    # 1. 자격별 비교
    create_comparison_plot(df)
    
    # 2. 전체 비교
    create_overall_comparison_plot(df)
    
    # 3. 자격점수 분포
    create_qualification_distribution(df)
    
    # 4. 등급 변화 표
    create_grade_change_table(df)
    
    print("\n" + "=" * 60)
    print("✅ 모든 시각화 완료!")
    print("📁 저장 위치: results/evidence/")
    print("   - 05_qualification_weight_comparison.png")
    print("   - 06_overall_qualification_comparison.png")
    print("   - 07_qualification_score_distribution.png")
    print("   - 08_grade_change_table_by_qualification.png")
    print("=" * 60)

if __name__ == "__main__":
    main()
