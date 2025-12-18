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



def create_detailed_comparison(df_analysis):
    """
    자격별 등급 변화 비율 시각화
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    qualifications = ["법인", "공인중개사", "중개보조원", "중개인"]
    
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
    
    p1 = ax.bar(x, qual_data[0], width, label='하락', color='#e74c3c', edgecolor='black')
    p2 = ax.bar(x, qual_data[1], width, bottom=qual_data[0], 
                label='유지', color='#95a5a6', edgecolor='black')
    p3 = ax.bar(x, qual_data[2], width, bottom=qual_data[0]+qual_data[1], 
                label='상승', color='#2ecc71', edgecolor='black')
    
    # 값 표시
    for i in range(len(qualifications)):
        if qual_data[0][i] > 5:
            ax.text(i, qual_data[0][i]/2, f'{qual_data[0][i]:.1f}%', 
                    ha='center', va='center', fontweight='bold', fontsize=9)
        if qual_data[1][i] > 5:
            ax.text(i, qual_data[0][i] + qual_data[1][i]/2, f'{qual_data[1][i]:.1f}%', 
                    ha='center', va='center', fontweight='bold', fontsize=9)
        if qual_data[2][i] > 5:
            ax.text(i, qual_data[0][i] + qual_data[1][i] + qual_data[2][i]/2, 
                    f'{qual_data[2][i]:.1f}%', 
                    ha='center', va='center', fontweight='bold', fontsize=9)
    
    ax.set_ylabel('비율 (%)', fontsize=12, fontweight='bold')
    ax.set_title('자격별 등급 변화 비율', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(qualifications)
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # 저장
    script_dir = Path(__file__).parent
    output_dir = script_dir / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
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
    script_dir = Path(__file__).parent
    output_dir = script_dir / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
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
    create_detailed_comparison(df_analysis)
    
    # 상세 테이블 저장
    export_detailed_table(df_analysis)
    
    print("\n" + "=" * 60)
    print("✅ 분석 완료!")
    print("📁 저장 위치: analysis/results/")
    print("   - 10_detailed_grade_change_analysis.png")
    print("   - grade_change_details.csv")
    print("=" * 60)

if __name__ == "__main__":
    main()
