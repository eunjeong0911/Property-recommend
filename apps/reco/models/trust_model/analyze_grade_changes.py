"""
자격점수 적용 전후 등급 변화 분석
- 성사율 Z-Score만 사용한 등급
- 성사율 Z-Score + 자격점수 사용한 등급
- 자격별 등급 변화 분석
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

def calculate_grade_without_qualification(df):
    """
    자격점수 없이 성사율 Z-Score만으로 등급 계산
    """
    # 성사율 Z-Score만 사용
    score_without_qual = df["지역별_성사율_Z"] * 1.0  # 가중치 100%
    
    # Train 데이터 기준으로 분위수 계산 (원래 방식과 동일)
    # 실제로는 전체 데이터로 계산하지만, 비교를 위해 동일한 방식 사용
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
    
    return grade_without_qual, score_without_qual

def analyze_grade_changes(df):
    """
    등급 변화 분석
    """
    # 1. 자격점수 없이 계산한 등급
    grade_without_qual, score_without_qual = calculate_grade_without_qualification(df)
    
    # 2. 자격점수 포함한 등급 (현재 Target)
    grade_with_qual = df["Target"]
    
    # 3. 데이터프레임에 추가
    df_analysis = df.copy()
    df_analysis["등급_성사율만"] = grade_without_qual
    df_analysis["등급_자격포함"] = grade_with_qual
    df_analysis["점수_성사율만"] = score_without_qual
    df_analysis["점수_자격포함"] = df["신뢰도점수"]
    
    # 4. 등급 변화 계산
    df_analysis["등급변화"] = df_analysis["등급_자격포함"] - df_analysis["등급_성사율만"]
    
    # 등급 변화 레이블
    def get_change_label(change):
        if change > 0:
            return f"+{change} (상승)"
        elif change < 0:
            return f"{change} (하락)"
        else:
            return "0 (유지)"
    
    df_analysis["등급변화_레이블"] = df_analysis["등급변화"].apply(get_change_label)
    
    return df_analysis

def print_summary_statistics(df_analysis):
    """
    요약 통계 출력
    """
    print("\n" + "=" * 80)
    print("📊 자격점수 적용 전후 등급 변화 분석")
    print("=" * 80)
    
    # 전체 등급 변화 분포
    print("\n1️⃣ 전체 등급 변화 분포")
    print("-" * 80)
    change_dist = df_analysis["등급변화"].value_counts().sort_index()
    for change, count in change_dist.items():
        if change > 0:
            label = f"+{change} (상승)"
            emoji = "⬆️"
        elif change < 0:
            label = f"{change} (하락)"
            emoji = "⬇️"
        else:
            label = "0 (유지)"
            emoji = "➡️"
        print(f"   {emoji} {label:15s}: {count:3d}개 ({count/len(df_analysis)*100:5.1f}%)")
    
    # 자격별 등급 변화
    print("\n2️⃣ 자격별 등급 변화")
    print("-" * 80)
    
    qualifications = ["법인", "공인중개사", "중개보조원", "중개인"]
    
    for qual in qualifications:
        mask = df_analysis["대표자구분명"] == qual
        if mask.sum() == 0:
            continue
        
        print(f"\n   📌 {qual} ({mask.sum()}개)")
        
        # 등급 변화 분포
        qual_changes = df_analysis.loc[mask, "등급변화"].value_counts().sort_index()
        for change, count in qual_changes.items():
            if change > 0:
                label = f"+{change} (상승)"
                emoji = "⬆️"
            elif change < 0:
                label = f"{change} (하락)"
                emoji = "⬇️"
            else:
                label = "0 (유지)"
                emoji = "➡️"
            print(f"      {emoji} {label:15s}: {count:3d}개 ({count/mask.sum()*100:5.1f}%)")
        
        # 평균 변화
        avg_change = df_analysis.loc[mask, "등급변화"].mean()
        if avg_change > 0:
            print(f"      💡 평균 변화: +{avg_change:.3f} (상승 경향)")
        elif avg_change < 0:
            print(f"      💡 평균 변화: {avg_change:.3f} (하락 경향)")
        else:
            print(f"      💡 평균 변화: {avg_change:.3f} (변화 없음)")
    
    # 등급별 자격 분포 (자격포함 기준)
    print("\n3️⃣ 최종 등급별 자격 분포")
    print("-" * 80)
    
    grade_map = {0: "C등급", 1: "B등급", 2: "A등급"}
    
    for grade, grade_name in grade_map.items():
        mask = df_analysis["등급_자격포함"] == grade
        if mask.sum() == 0:
            continue
        
        print(f"\n   🏆 {grade_name} ({mask.sum()}개)")
        
        qual_dist = df_analysis.loc[mask, "대표자구분명"].value_counts()
        for qual, count in qual_dist.items():
            print(f"      - {qual:10s}: {count:3d}개 ({count/mask.sum()*100:5.1f}%)")

def create_grade_change_matrix(df_analysis):
    """
    등급 변화 매트릭스 시각화
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    fig.suptitle('자격점수 적용 전후 등급 변화 분석', fontsize=16, fontweight='bold')
    
    qualifications = ["법인", "공인중개사", "중개보조원", "중개인"]
    grade_map = {0: "C", 1: "B", 2: "A"}
    
    for idx, qual in enumerate(qualifications):
        row = idx // 2
        col = idx % 2
        ax = axes[row, col]
        
        mask = df_analysis["대표자구분명"] == qual
        
        if mask.sum() == 0:
            ax.text(0.5, 0.5, f'{qual}\n데이터 없음', 
                   ha='center', va='center', fontsize=14)
            ax.set_title(f'{qual} (0개)', fontweight='bold')
            continue
        
        # 혼동 행렬 생성
        from sklearn.metrics import confusion_matrix
        
        cm = confusion_matrix(
            df_analysis.loc[mask, "등급_성사율만"],
            df_analysis.loc[mask, "등급_자격포함"],
            labels=[0, 1, 2]
        )
        
        # 히트맵
        sns.heatmap(cm, annot=True, fmt='d', cmap='RdYlGn', 
                   xticklabels=['C', 'B', 'A'],
                   yticklabels=['C', 'B', 'A'],
                   cbar_kws={'label': '중개사 수'},
                   ax=ax, vmin=0, vmax=cm.max())
        
        ax.set_xlabel('자격포함 등급', fontsize=11, fontweight='bold')
        ax.set_ylabel('성사율만 등급', fontsize=11, fontweight='bold')
        ax.set_title(f'{qual} ({mask.sum()}개 중개사)', fontsize=12, fontweight='bold')
        
        # 대각선 강조 (등급 유지)
        for i in range(3):
            ax.add_patch(plt.Rectangle((i, i), 1, 1, fill=False, 
                                      edgecolor='blue', lw=3))
        
        # 통계 추가
        total = mask.sum()
        upgraded = (df_analysis.loc[mask, "등급변화"] > 0).sum()
        downgraded = (df_analysis.loc[mask, "등급변화"] < 0).sum()
        maintained = (df_analysis.loc[mask, "등급변화"] == 0).sum()
        
        stats_text = f"상승: {upgraded}개 ({upgraded/total*100:.1f}%)\n"
        stats_text += f"유지: {maintained}개 ({maintained/total*100:.1f}%)\n"
        stats_text += f"하락: {downgraded}개 ({downgraded/total*100:.1f}%)"
        
        ax.text(0.02, 0.98, stats_text,
               transform=ax.transAxes,
               fontsize=9,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    
    # 저장
    output_dir = Path("results/evidence")
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / "09_grade_change_matrix_by_qualification.png", dpi=300, bbox_inches='tight')
    print(f"\n✅ 저장: {output_dir / '09_grade_change_matrix_by_qualification.png'}")
    
    plt.close()

def create_detailed_comparison(df_analysis):
    """
    상세 비교 시각화
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('자격점수 적용 효과 상세 분석', fontsize=16, fontweight='bold')
    
    # 1. 전체 등급 변화 분포
    ax1 = axes[0, 0]
    
    change_counts = df_analysis["등급변화"].value_counts().sort_index()
    colors = ['#e74c3c' if x < 0 else '#95a5a6' if x == 0 else '#2ecc71' 
             for x in change_counts.index]
    
    bars = ax1.bar(change_counts.index, change_counts.values, color=colors, 
                   edgecolor='black', linewidth=1.5)
    
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}개',
                ha='center', va='bottom', fontweight='bold')
    
    ax1.set_xlabel('등급 변화', fontsize=12, fontweight='bold')
    ax1.set_ylabel('중개사 수', fontsize=12, fontweight='bold')
    ax1.set_title('전체 등급 변화 분포', fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    ax1.set_xticks(change_counts.index)
    ax1.set_xticklabels([f'{int(x):+d}' if x != 0 else '0' for x in change_counts.index])
    
    # 2. 자격별 평균 등급 변화
    ax2 = axes[0, 1]
    
    qualifications = ["법인", "공인중개사", "중개보조원", "중개인"]
    avg_changes = []
    qual_labels = []
    
    for qual in qualifications:
        mask = df_analysis["대표자구분명"] == qual
        if mask.sum() > 0:
            avg_change = df_analysis.loc[mask, "등급변화"].mean()
            avg_changes.append(avg_change)
            qual_labels.append(f"{qual}\n({mask.sum()}개)")
    
    colors = ['#2ecc71' if x > 0 else '#e74c3c' if x < 0 else '#95a5a6' 
             for x in avg_changes]
    
    bars = ax2.bar(range(len(avg_changes)), avg_changes, color=colors, 
                   edgecolor='black', linewidth=1.5)
    
    for i, (bar, val) in enumerate(zip(bars, avg_changes)):
        ax2.text(bar.get_x() + bar.get_width()/2., val + (0.05 if val >= 0 else -0.05),
                f'{val:+.3f}',
                ha='center', va='bottom' if val >= 0 else 'top', 
                fontweight='bold', fontsize=10)
    
    ax2.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax2.set_ylabel('평균 등급 변화', fontsize=12, fontweight='bold')
    ax2.set_title('자격별 평균 등급 변화', fontsize=13, fontweight='bold')
    ax2.set_xticks(range(len(qual_labels)))
    ax2.set_xticklabels(qual_labels, fontsize=10)
    ax2.grid(axis='y', alpha=0.3)
    
    # 3. 자격별 등급 변화 비율 (스택 바)
    ax3 = axes[1, 0]
    
    qual_data = []
    for qual in qualifications:
        mask = df_analysis["대표자구분명"] == qual
        if mask.sum() > 0:
            total = mask.sum()
            upgraded = (df_analysis.loc[mask, "등급변화"] > 0).sum() / total * 100
            maintained = (df_analysis.loc[mask, "등급변화"] == 0).sum() / total * 100
            downgraded = (df_analysis.loc[mask, "등급변화"] < 0).sum() / total * 100
            qual_data.append([downgraded, maintained, upgraded])
        else:
            qual_data.append([0, 0, 0])
    
    qual_data = np.array(qual_data).T
    
    x = np.arange(len(qualifications))
    width = 0.6
    
    p1 = ax3.bar(x, qual_data[0], width, label='하락', color='#e74c3c', edgecolor='black')
    p2 = ax3.bar(x, qual_data[1], width, bottom=qual_data[0], 
                label='유지', color='#95a5a6', edgecolor='black')
    p3 = ax3.bar(x, qual_data[2], width, bottom=qual_data[0]+qual_data[1], 
                label='상승', color='#2ecc71', edgecolor='black')
    
    # 값 표시
    for i in range(len(qualifications)):
        if qual_data[0][i] > 5:
            ax3.text(i, qual_data[0][i]/2, f'{qual_data[0][i]:.1f}%', 
                    ha='center', va='center', fontweight='bold', fontsize=9)
        if qual_data[1][i] > 5:
            ax3.text(i, qual_data[0][i] + qual_data[1][i]/2, f'{qual_data[1][i]:.1f}%', 
                    ha='center', va='center', fontweight='bold', fontsize=9)
        if qual_data[2][i] > 5:
            ax3.text(i, qual_data[0][i] + qual_data[1][i] + qual_data[2][i]/2, 
                    f'{qual_data[2][i]:.1f}%', 
                    ha='center', va='center', fontweight='bold', fontsize=9)
    
    ax3.set_ylabel('비율 (%)', fontsize=12, fontweight='bold')
    ax3.set_title('자격별 등급 변화 비율', fontsize=13, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(qualifications)
    ax3.legend(loc='upper right')
    ax3.grid(axis='y', alpha=0.3)
    
    # 4. 산점도: 점수 변화
    ax4 = axes[1, 1]
    
    qual_colors = {
        "법인": '#2ecc71',
        "공인중개사": '#3498db',
        "중개보조원": '#f39c12',
        "중개인": '#e74c3c'
    }
    
    for qual, color in qual_colors.items():
        mask = df_analysis["대표자구분명"] == qual
        if mask.sum() > 0:
            ax4.scatter(df_analysis.loc[mask, "점수_성사율만"],
                       df_analysis.loc[mask, "점수_자격포함"],
                       c=color, label=f'{qual} ({mask.sum()}개)',
                       alpha=0.6, s=80, edgecolors='black', linewidth=0.5)
    
    # 대각선 (y=x)
    min_val = min(df_analysis["점수_성사율만"].min(), df_analysis["점수_자격포함"].min())
    max_val = max(df_analysis["점수_성사율만"].max(), df_analysis["점수_자격포함"].max())
    ax4.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, linewidth=2, label='y=x (변화없음)')
    
    ax4.set_xlabel('성사율만 점수', fontsize=12, fontweight='bold')
    ax4.set_ylabel('자격포함 점수', fontsize=12, fontweight='bold')
    ax4.set_title('점수 변화 (대각선 위=상승, 아래=하락)', fontsize=13, fontweight='bold')
    ax4.legend(loc='upper left', fontsize=9)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 저장
    output_dir = Path("results/evidence")
    plt.savefig(output_dir / "10_detailed_grade_change_analysis.png", dpi=300, bbox_inches='tight')
    print(f"✅ 저장: {output_dir / '10_detailed_grade_change_analysis.png'}")
    
    plt.close()

def export_detailed_table(df_analysis):
    """
    상세 변화 테이블 저장
    """
    # 등급 변화가 있는 중개사만 필터링
    df_changed = df_analysis[df_analysis["등급변화"] != 0].copy()
    
    # 필요한 컬럼만 선택
    columns = [
        "중개사무소명", "대표자구분명", "지역명",
        "거래성사율", "지역별_성사율_Z", "자격점수",
        "점수_성사율만", "점수_자격포함",
        "등급_성사율만", "등급_자격포함", "등급변화", "등급변화_레이블"
    ]
    
    df_export = df_changed[columns].copy()
    
    # 등급 레이블 추가
    grade_map = {0: "C", 1: "B", 2: "A"}
    df_export["등급_성사율만_레이블"] = df_export["등급_성사율만"].map(grade_map)
    df_export["등급_자격포함_레이블"] = df_export["등급_자격포함"].map(grade_map)
    
    # 정렬 (등급 변화 큰 순)
    df_export = df_export.sort_values("등급변화", ascending=False)
    
    # 저장
    output_dir = Path("results/evidence")
    output_path = output_dir / "grade_change_details.csv"
    df_export.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    print(f"✅ 저장: {output_path}")
    print(f"   - 등급 변화 중개사: {len(df_export)}개")

def main():
    print("=" * 60)
    print("🎯 자격점수 적용 전후 등급 변화 분석")
    print("=" * 60)
    
    # 데이터 로드
    df = load_data()
    
    # 등급 변화 분석
    df_analysis = analyze_grade_changes(df)
    
    # 요약 통계 출력
    print_summary_statistics(df_analysis)
    
    print("\n📈 시각화 생성 중...")
    
    # 시각화
    create_grade_change_matrix(df_analysis)
    create_detailed_comparison(df_analysis)
    
    # 상세 테이블 저장
    export_detailed_table(df_analysis)
    
    print("\n" + "=" * 60)
    print("✅ 분석 완료!")
    print("📁 저장 위치: results/evidence/")
    print("   - 09_grade_change_matrix_by_qualification.png")
    print("   - 10_detailed_grade_change_analysis.png")
    print("   - grade_change_details.csv")
    print("=" * 60)

if __name__ == "__main__":
    main()
