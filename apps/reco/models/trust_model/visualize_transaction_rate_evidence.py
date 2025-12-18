"""
거래성사율과 허위 매물 관계 시각화
- 등록 매물 vs 거래 완료 vs 거래성사율 관계 분석
- 실제 데이터로 "등록 많음 + 거래 적음 = 낮은 성사율" 패턴 증명
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
    # Train 데이터 로드 (Target이 이미 계산된 데이터)
    train_path = "data/ML/trust/train_target.csv"
    test_path = "data/ML/trust/test_target.csv"
    
    train_df = pd.read_csv(train_path, encoding="utf-8-sig")
    test_df = pd.read_csv(test_path, encoding="utf-8-sig")
    
    # 전체 데이터 합치기
    df = pd.concat([train_df, test_df], ignore_index=True)
    
    print(f"📊 전체 데이터: {len(df):,}개 중개사무소")
    print(f"   - Train: {len(train_df):,}개")
    print(f"   - Test:  {len(test_df):,}개")
    
    return df

def create_scatter_plot(df):
    """
    산점도: 등록매물 vs 거래완료 (색상: 거래성사율)
    핵심 메시지: 등록 많고 거래 적으면 성사율 낮음
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 산점도 그리기
    scatter = ax.scatter(
        df['등록매물'], 
        df['거래완료'],
        c=df['거래성사율'],
        s=100,
        alpha=0.6,
        cmap='RdYlGn',  # 빨강(낮음) → 노랑(중간) → 초록(높음)
        edgecolors='black',
        linewidth=0.5
    )
    
    # 컬러바
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('거래성사율 (Transaction Success Rate)', fontsize=12, fontweight='bold')
    
    # 대각선 (등록매물 = 거래완료)
    max_val = max(df['등록매물'].max(), df['거래완료'].max())
    ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.3, linewidth=2, label='등록 = 거래 (이상적)')
    
    # 영역 표시
    # 1. 허위 매물 의심 영역 (등록 많음, 거래 적음)
    ax.fill_between([50, max_val], 0, 20, alpha=0.1, color='red', label='허위 매물 의심 영역')
    
    # 2. 우수 중개사 영역 (거래 많음)
    ax.fill_between([0, max_val], 50, max_val, alpha=0.1, color='green', label='우수 중개사 영역')
    
    ax.set_xlabel('등록 매물 수 (Registered Listings)', fontsize=14, fontweight='bold')
    ax.set_ylabel('거래 완료 수 (Completed Transactions)', fontsize=14, fontweight='bold')
    ax.set_title('등록 매물 vs 거래 완료 vs 거래성사율\n(색상: 초록=높은 성사율, 빨강=낮은 성사율)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    # 주요 패턴 텍스트 추가
    ax.text(0.98, 0.02, 
            '📌 패턴:\n'
            '• 대각선 위쪽 = 거래 > 등록 (우수)\n'
            '• 대각선 아래쪽 = 등록 > 거래 (의심)\n'
            '• 빨간 점 = 낮은 성사율',
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='bottom',
            horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    
    # 저장
    output_dir = Path("results/evidence")
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / "01_scatter_listings_vs_transactions.png", dpi=300, bbox_inches='tight')
    print(f"✅ 저장: {output_dir / '01_scatter_listings_vs_transactions.png'}")
    
    plt.close()

def create_grade_comparison(df):
    """
    등급별 비교: 등록매물 vs 거래완료 vs 거래성사율
    """
    # 등급 매핑
    grade_map = {2: 'A등급\n(상위 30%)', 1: 'B등급\n(중위 40%)', 0: 'C등급\n(하위 30%)'}
    df['등급명'] = df['Target'].map(grade_map)
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    colors = {
        'A등급\n(상위 30%)': '#2ecc71',  # 초록
        'B등급\n(중위 40%)': '#f39c12',  # 주황
        'C등급\n(하위 30%)': '#e74c3c'   # 빨강
    }
    
    # 1. 등록 매물 평균
    grade_stats = df.groupby('등급명').agg({
        '등록매물': 'mean',
        '거래완료': 'mean',
        '거래성사율': 'mean'
    }).reindex(['A등급\n(상위 30%)', 'B등급\n(중위 40%)', 'C등급\n(하위 30%)'])
    
    # 그래프 1: 등록 매물
    bars1 = axes[0].bar(grade_stats.index, grade_stats['등록매물'], 
                        color=[colors[g] for g in grade_stats.index],
                        edgecolor='black', linewidth=1.5)
    axes[0].set_ylabel('평균 등록 매물 수', fontsize=12, fontweight='bold')
    axes[0].set_title('등급별 평균 등록 매물', fontsize=14, fontweight='bold')
    axes[0].grid(axis='y', alpha=0.3)
    
    # 값 표시
    for bar in bars1:
        height = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontweight='bold')
    
    # 그래프 2: 거래 완료
    bars2 = axes[1].bar(grade_stats.index, grade_stats['거래완료'], 
                        color=[colors[g] for g in grade_stats.index],
                        edgecolor='black', linewidth=1.5)
    axes[1].set_ylabel('평균 거래 완료 수', fontsize=12, fontweight='bold')
    axes[1].set_title('등급별 평균 거래 완료', fontsize=14, fontweight='bold')
    axes[1].grid(axis='y', alpha=0.3)
    
    for bar in bars2:
        height = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontweight='bold')
    
    # 그래프 3: 거래성사율
    bars3 = axes[2].bar(grade_stats.index, grade_stats['거래성사율'] * 100, 
                        color=[colors[g] for g in grade_stats.index],
                        edgecolor='black', linewidth=1.5)
    axes[2].set_ylabel('평균 거래성사율 (%)', fontsize=12, fontweight='bold')
    axes[2].set_title('등급별 평균 거래성사율', fontsize=14, fontweight='bold')
    axes[2].grid(axis='y', alpha=0.3)
    
    for bar in bars3:
        height = bar.get_height()
        axes[2].text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontweight='bold')
    
    plt.suptitle('등급별 비교: 등록 매물 vs 거래 완료 vs 거래성사율', 
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    # 저장
    output_dir = Path("results/evidence")
    plt.savefig(output_dir / "02_grade_comparison.png", dpi=300, bbox_inches='tight')
    print(f"✅ 저장: {output_dir / '02_grade_comparison.png'}")
    
    plt.close()
    
    # 통계 출력
    print("\n📊 등급별 통계:")
    print(grade_stats.round(2))

def create_pattern_visualization(df):
    """
    패턴 시각화: 4개 사분면으로 나누어 분석
    """
    # 중앙값 기준으로 사분면 나누기
    median_listings = df['등록매물'].median()
    median_transactions = df['거래완료'].median()
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # 사분면별 데이터 분류
    df['사분면'] = 'Unknown'
    df.loc[(df['등록매물'] >= median_listings) & (df['거래완료'] >= median_transactions), '사분면'] = '1. 높은 활동\n(등록↑, 거래↑)'
    df.loc[(df['등록매물'] < median_listings) & (df['거래완료'] >= median_transactions), '사분면'] = '2. 효율적\n(등록↓, 거래↑)'
    df.loc[(df['등록매물'] < median_listings) & (df['거래완료'] < median_transactions), '사분면'] = '3. 낮은 활동\n(등록↓, 거래↓)'
    df.loc[(df['등록매물'] >= median_listings) & (df['거래완료'] < median_transactions), '사분면'] = '4. 허위 의심\n(등록↑, 거래↓)'
    
    # 사분면별 색상
    quadrant_colors = {
        '1. 높은 활동\n(등록↑, 거래↑)': '#3498db',    # 파랑
        '2. 효율적\n(등록↓, 거래↑)': '#2ecc71',      # 초록
        '3. 낮은 활동\n(등록↓, 거래↓)': '#95a5a6',    # 회색
        '4. 허위 의심\n(등록↑, 거래↓)': '#e74c3c'     # 빨강
    }
    
    # 산점도
    for quadrant, color in quadrant_colors.items():
        mask = df['사분면'] == quadrant
        ax.scatter(
            df.loc[mask, '등록매물'],
            df.loc[mask, '거래완료'],
            c=color,
            s=80,
            alpha=0.6,
            label=f"{quadrant} ({mask.sum()}개)",
            edgecolors='black',
            linewidth=0.5
        )
    
    # 중앙값 선
    ax.axvline(median_listings, color='black', linestyle='--', linewidth=2, alpha=0.5, label=f'등록 중앙값: {median_listings:.0f}')
    ax.axhline(median_transactions, color='black', linestyle='--', linewidth=2, alpha=0.5, label=f'거래 중앙값: {median_transactions:.0f}')
    
    # 사분면별 평균 성사율 계산
    quadrant_stats = df.groupby('사분면')['거래성사율'].mean().sort_index()
    
    # 사분면별 텍스트 추가
    positions = {
        '1. 높은 활동\n(등록↑, 거래↑)': (0.75, 0.75),
        '2. 효율적\n(등록↓, 거래↑)': (0.25, 0.75),
        '3. 낮은 활동\n(등록↓, 거래↓)': (0.25, 0.25),
        '4. 허위 의심\n(등록↑, 거래↓)': (0.75, 0.25)
    }
    
    for quadrant, (x_pos, y_pos) in positions.items():
        if quadrant in quadrant_stats.index:
            avg_rate = quadrant_stats[quadrant] * 100
            ax.text(x_pos, y_pos,
                   f'평균 성사율:\n{avg_rate:.1f}%',
                   transform=ax.transAxes,
                   fontsize=11,
                   fontweight='bold',
                   ha='center',
                   va='center',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='black'))
    
    ax.set_xlabel('등록 매물 수 (Registered Listings)', fontsize=14, fontweight='bold')
    ax.set_ylabel('거래 완료 수 (Completed Transactions)', fontsize=14, fontweight='bold')
    ax.set_title('사분면 분석: 등록 매물 vs 거래 완료\n(4사분면 = 허위 매물 의심 영역)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 저장
    output_dir = Path("results/evidence")
    plt.savefig(output_dir / "03_quadrant_analysis.png", dpi=300, bbox_inches='tight')
    print(f"✅ 저장: {output_dir / '03_quadrant_analysis.png'}")
    
    plt.close()
    
    # 사분면별 통계 출력
    print("\n📊 사분면별 평균 거래성사율:")
    for quadrant in sorted(quadrant_stats.index):
        count = (df['사분면'] == quadrant).sum()
        rate = quadrant_stats[quadrant] * 100
        print(f"   {quadrant}: {rate:.1f}% ({count}개 중개사)")

def create_correlation_heatmap(df):
    """
    상관관계 히트맵: 등록매물, 거래완료, 거래성사율, Target
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 상관관계 계산
    corr_cols = ['등록매물', '거래완료', '거래성사율', 'Target']
    corr_matrix = df[corr_cols].corr()
    
    # 히트맵
    sns.heatmap(corr_matrix, 
                annot=True, 
                fmt='.3f',
                cmap='coolwarm',
                center=0,
                square=True,
                linewidths=1,
                cbar_kws={"shrink": 0.8},
                ax=ax,
                vmin=-1, vmax=1)
    
    ax.set_title('상관관계 분석: 등록매물 vs 거래완료 vs 거래성사율 vs 신뢰도등급', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # 레이블 회전
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    
    plt.tight_layout()
    
    # 저장
    output_dir = Path("results/evidence")
    plt.savefig(output_dir / "04_correlation_heatmap.png", dpi=300, bbox_inches='tight')
    print(f"✅ 저장: {output_dir / '04_correlation_heatmap.png'}")
    
    plt.close()
    
    print("\n📊 상관관계 매트릭스:")
    print(corr_matrix.round(3))

def main():
    print("=" * 60)
    print("🎯 거래성사율 근거 시각화")
    print("=" * 60)
    
    # 데이터 로드
    df = load_data()
    
    print("\n📈 시각화 생성 중...")
    
    # 1. 산점도: 등록매물 vs 거래완료 (색상: 거래성사율)
    create_scatter_plot(df)
    
    # 2. 등급별 비교
    create_grade_comparison(df)
    
    # 3. 사분면 분석
    create_pattern_visualization(df)
    
    # 4. 상관관계 히트맵
    create_correlation_heatmap(df)
    
    print("\n" + "=" * 60)
    print("✅ 모든 시각화 완료!")
    print("📁 저장 위치: results/evidence/")
    print("=" * 60)

if __name__ == "__main__":
    main()
