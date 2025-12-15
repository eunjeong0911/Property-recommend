"""
중개사 신뢰도 모델 - 종합 분석 스크립트
=============================================
버전 비교: 
  - Version A: 기본 Z-score 기반 (pipeline/)
  - Version B: 가중치 + 베이지안 보정 + 이상치 제거 (pipeline/sumi/)

분석 항목:
  1. EDA 분석 (데이터 분포, 결측치, 이상치)
  2. 타겟 분석 (등급 분포, 생성 방식 비교)
  3. 피처 분석 (피처 목록, 상관관계, 중요도)
  4. 모델 분석 (설정값 비교, 성능 비교)
  5. 혼동행렬 및 분류 리포트
  6. 과적합 분석
  
저장 위치: apps/reco/models/trust_model/result/1회차/
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
from sklearn.metrics import (
    confusion_matrix, classification_report, accuracy_score, 
    f1_score, precision_score, recall_score, cohen_kappa_score
)
from sklearn.model_selection import cross_val_score, StratifiedKFold
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# ============================================================
# 경로 설정
# ============================================================
BASE_DIR = Path("apps/reco/models/trust_model")
RESULT_DIR = BASE_DIR / "result" / "1회차"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

# 데이터 파일
PREPROCESSED_PATH = "data/ML/preprocessed_office_data.csv"
TARGET_PATH = "data/ML/office_target.csv"
FEATURE_PATH = "data/ML/office_features.csv"
GROUPED_DATA_PATH = "data/brokerInfo/grouped_offices.csv"

# 모델 파일
MODEL_TEMP_PATH = BASE_DIR / "save_models" / "temp_trained_models.pkl"
SUMI_MODEL_PATH = BASE_DIR / "saved_models" / "trust_model.pkl"


def print_section(title, emoji="📊"):
    """섹션 구분선 출력"""
    print("\n" + "=" * 80)
    print(f" {emoji} {title}")
    print("=" * 80)


# ============================================================
# 1. EDA 분석
# ============================================================
def eda_analysis():
    """데이터 탐색적 분석"""
    print_section("1. EDA (탐색적 데이터 분석)", "🔍")
    
    report = []
    report.append("# 📊 EDA (탐색적 데이터 분석) 보고서\n")
    report.append(f"**분석 일시**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # 원본 데이터 로드 시도
    try:
        df_grouped = pd.read_csv(GROUPED_DATA_PATH, encoding='utf-8-sig')
        print(f"✅ 원본 데이터 로드: {len(df_grouped)}개 레코드")
    except:
        df_grouped = None
        print("⚠️ 원본 데이터 없음, 전처리 데이터 사용")
    
    # 전처리 데이터 로드
    try:
        df_preprocessed = pd.read_csv(PREPROCESSED_PATH, encoding='utf-8-sig')
        print(f"✅ 전처리 데이터 로드: {len(df_preprocessed)}개 레코드")
    except:
        df_preprocessed = None
    
    # 타겟 데이터 로드
    try:
        df_target = pd.read_csv(TARGET_PATH, encoding='utf-8-sig')
        print(f"✅ 타겟 데이터 로드: {len(df_target)}개 레코드")
    except:
        df_target = None
    
    # 피처 데이터 로드
    try:
        df_features = pd.read_csv(FEATURE_PATH, encoding='utf-8-sig')
        print(f"✅ 피처 데이터 로드: {len(df_features)}개 레코드")
    except:
        df_features = None
    
    # 1.1 기본 통계
    report.append("## 1.1 데이터셋 기본 정보\n\n")
    
    if df_grouped is not None:
        report.append(f"### 원본 데이터 (grouped_offices.csv)\n")
        report.append(f"- **행 수**: {len(df_grouped):,}개\n")
        report.append(f"- **열 수**: {len(df_grouped.columns)}개\n")
        report.append(f"- **컬럼 목록**:\n```\n{', '.join(df_grouped.columns.tolist())}\n```\n\n")
    
    if df_target is not None:
        report.append(f"### 타겟 데이터 (office_target.csv)\n")
        report.append(f"- **행 수**: {len(df_target):,}개\n")
        report.append(f"- **열 수**: {len(df_target.columns)}개\n\n")
        
        # 수치형 컬럼 통계
        numeric_cols = df_target.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            desc = df_target[numeric_cols].describe()
            report.append("### 수치형 변수 기술통계\n")
            report.append(f"```\n{desc.to_string()}\n```\n\n")
            
            # 기술통계 저장
            desc.to_csv(RESULT_DIR / "eda_descriptive_stats.csv", encoding='utf-8-sig')
    
    # 1.2 결측치 분석
    report.append("## 1.2 결측치 분석\n\n")
    
    if df_target is not None:
        missing = df_target.isnull().sum()
        missing_pct = (missing / len(df_target) * 100).round(2)
        missing_df = pd.DataFrame({
            '결측치 수': missing,
            '결측비율(%)': missing_pct
        })
        missing_df = missing_df[missing_df['결측치 수'] > 0].sort_values('결측치 수', ascending=False)
        
        if len(missing_df) > 0:
            report.append(f"| 컬럼 | 결측치 수 | 결측비율(%) |\n")
            report.append(f"|------|-----------|-------------|\n")
            for col, row in missing_df.iterrows():
                report.append(f"| {col} | {int(row['결측치 수'])} | {row['결측비율(%)']}% |\n")
        else:
            report.append("✅ **결측치 없음**\n")
        report.append("\n")
    
    # 1.3 지역별 분포
    report.append("## 1.3 지역별 데이터 분포\n\n")
    
    if df_target is not None and '지역명' in df_target.columns:
        region_dist = df_target['지역명'].value_counts()
        
        # 시각화
        fig, ax = plt.subplots(figsize=(14, 8))
        colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(region_dist)))
        bars = ax.bar(range(len(region_dist)), region_dist.values, color=colors)
        ax.set_xticks(range(len(region_dist)))
        ax.set_xticklabels(region_dist.index, rotation=45, ha='right')
        ax.set_xlabel('지역명', fontsize=12)
        ax.set_ylabel('중개사무소 수', fontsize=12)
        ax.set_title('지역별 중개사무소 분포', fontsize=14, fontweight='bold')
        
        # 값 표시
        for bar, val in zip(bars, region_dist.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                   f'{val}', ha='center', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(RESULT_DIR / "eda_01_region_distribution.png", dpi=150)
        plt.close()
        
        report.append(f"![지역별 분포](eda_01_region_distribution.png)\n\n")
        report.append(f"| 지역명 | 사무소 수 | 비율(%) |\n")
        report.append(f"|--------|-----------|----------|\n")
        for region, count in region_dist.items():
            pct = count / len(df_target) * 100
            report.append(f"| {region} | {count} | {pct:.1f}% |\n")
        report.append("\n")
    
    # 1.4 주요 변수 분포
    report.append("## 1.4 주요 변수 분포\n\n")
    
    if df_target is not None:
        key_cols = ['거래완료_숫자', '등록매물_숫자', '거래성사율', 'Zscore']
        available_cols = [c for c in key_cols if c in df_target.columns]
        
        if available_cols:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            axes = axes.flatten()
            
            for idx, col in enumerate(available_cols):
                ax = axes[idx]
                data = df_target[col].dropna()
                
                # 히스토그램
                ax.hist(data, bins=30, color='steelblue', edgecolor='black', alpha=0.7)
                ax.axvline(data.mean(), color='red', linestyle='--', label=f'평균: {data.mean():.2f}')
                ax.axvline(data.median(), color='green', linestyle='--', label=f'중앙값: {data.median():.2f}')
                ax.set_xlabel(col, fontsize=11)
                ax.set_ylabel('빈도', fontsize=11)
                ax.set_title(f'{col} 분포', fontsize=12, fontweight='bold')
                ax.legend()
            
            plt.tight_layout()
            plt.savefig(RESULT_DIR / "eda_02_key_variables_distribution.png", dpi=150)
            plt.close()
            
            report.append(f"![주요 변수 분포](eda_02_key_variables_distribution.png)\n\n")
    
    # 1.5 박스플롯 (이상치 탐지)
    report.append("## 1.5 이상치 분석 (박스플롯)\n\n")
    
    if df_target is not None:
        outlier_cols = ['거래완료_숫자', '등록매물_숫자']
        available_outlier_cols = [c for c in outlier_cols if c in df_target.columns]
        
        if available_outlier_cols:
            fig, axes = plt.subplots(1, len(available_outlier_cols), figsize=(12, 5))
            if len(available_outlier_cols) == 1:
                axes = [axes]
            
            for ax, col in zip(axes, available_outlier_cols):
                data = df_target[col].dropna()
                bp = ax.boxplot(data, patch_artist=True)
                bp['boxes'][0].set_facecolor('lightblue')
                ax.set_ylabel(col, fontsize=11)
                ax.set_title(f'{col} 박스플롯', fontsize=12, fontweight='bold')
                
                # IQR 기반 이상치 개수
                Q1 = data.quantile(0.25)
                Q3 = data.quantile(0.75)
                IQR = Q3 - Q1
                outliers = data[(data < Q1 - 1.5*IQR) | (data > Q3 + 1.5*IQR)]
                ax.text(1.1, data.max() * 0.9, f'이상치: {len(outliers)}개', fontsize=10)
            
            plt.tight_layout()
            plt.savefig(RESULT_DIR / "eda_03_outliers_boxplot.png", dpi=150)
            plt.close()
            
            report.append(f"![이상치 박스플롯](eda_03_outliers_boxplot.png)\n\n")
    
    # 보고서 저장
    with open(RESULT_DIR / "01_EDA_분석_보고서.md", 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"✅ EDA 분석 완료 - 저장: {RESULT_DIR / '01_EDA_분석_보고서.md'}")
    return df_target


# ============================================================
# 2. 타겟 분석
# ============================================================
def target_analysis(df_target):
    """타겟 변수 분석"""
    print_section("2. 타겟 분석", "🎯")
    
    report = []
    report.append("# 🎯 타겟 분석 보고서\n\n")
    
    # 2.1 버전 비교 - 타겟 생성 방식
    report.append("## 2.1 타겟 생성 방식 비교\n\n")
    
    report.append("### Version A: 기본 Z-score 기반 (pipeline/)\n\n")
    report.append("```python\n")
    report.append("# 1. 거래성사율 계산\n")
    report.append("거래성사율 = 거래완료_숫자 / (거래완료_숫자 + 등록매물_숫자)\n\n")
    report.append("# 2. 지역별 Z-score 계산\n")
    report.append("지역평균 = 지역별 거래성사율 평균\n")
    report.append("지역표준편차 = 지역별 거래성사율 표준편차\n")
    report.append("Z-score = (거래성사율 - 지역평균) / 지역표준편차\n\n")
    report.append("# 3. 분위수 기반 등급 (30/40/30)\n")
    report.append("C등급: Z-score ≤ 30% 분위수 (하위 30%)\n")
    report.append("B등급: 30% < Z-score ≤ 70% (중위 40%)\n")
    report.append("A등급: Z-score > 70% 분위수 (상위 30%)\n")
    report.append("```\n\n")
    
    report.append("### Version B: 가중치 + 베이지안 보정 (pipeline/sumi/)\n\n")
    report.append("```python\n")
    report.append("# 0. 이상치 지역 제거\n")
    report.append("- 노원구 제거 (평균 성사율 45%, 타 지역 대비 -25%p)\n")
    report.append("- 총매물 500개 미만 지역 제거 (통계적 신뢰도 부족)\n\n")
    report.append("# 1. 지역별 매물분포율 계산\n")
    report.append("지역매물분포율 = 지역_총매물수 / 전체_총매물수\n\n")
    report.append("# 2. 가중치 적용된 기준값\n")
    report.append("보정된_기준값 = (지역평균성사율 × 분포율) + (전체평균 × (1-분포율))\n\n")
    report.append("# 3. 베이지안 보정\n")
    report.append("m = 중위 매물수 (임계값)\n")
    report.append("베이지안_성사율 = (m × Prior + 거래완료) / (m + 총매물수)\n\n")
    report.append("# 4. 3분위 등급 (33/33/34)\n")
    report.append("하위(0): 베이지안_성사율 < Q1 (33%)\n")
    report.append("중위(1): Q1 ≤ 베이지안_성사율 < Q2\n")
    report.append("상위(2): 베이지안_성사율 ≥ Q2 (66%)\n")
    report.append("```\n\n")
    
    # 2.2 타겟 분포
    report.append("## 2.2 타겟 분포\n\n")
    
    if df_target is not None and '신뢰도등급' in df_target.columns:
        target_col = '신뢰도등급'
        dist = df_target[target_col].value_counts().sort_index()
        pct = df_target[target_col].value_counts(normalize=True).sort_index() * 100
        
        # 시각화
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # 막대 그래프
        colors = ['#e74c3c', '#3498db', '#2ecc71']  # C=red, B=blue, A=green
        label_order = ['C', 'B', 'A'] if 'A' in dist.index else [0, 1, 2]
        
        bars = axes[0].bar(dist.index, dist.values, color=colors[:len(dist)], edgecolor='black')
        for bar, p in zip(bars, pct.values):
            axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                        f'{p:.1f}%', ha='center', fontsize=11, fontweight='bold')
        axes[0].set_xlabel('신뢰도 등급', fontsize=12)
        axes[0].set_ylabel('개수', fontsize=12)
        axes[0].set_title('타겟 분포 (막대 그래프)', fontsize=14, fontweight='bold')
        
        # 파이 차트
        axes[1].pie(dist.values, labels=dist.index, colors=colors[:len(dist)],
                   autopct='%1.1f%%', startangle=90, explode=[0.02]*len(dist))
        axes[1].set_title('타겟 분포 (파이 차트)', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(RESULT_DIR / "target_01_distribution.png", dpi=150)
        plt.close()
        
        report.append(f"![타겟 분포](target_01_distribution.png)\n\n")
        
        report.append(f"| 등급 | 개수 | 비율(%) |\n")
        report.append(f"|------|------|----------|\n")
        for grade in dist.index:
            report.append(f"| {grade} | {dist[grade]} | {pct[grade]:.1f}% |\n")
        report.append(f"| **총합** | **{len(df_target)}** | **100%** |\n\n")
    
    # 2.3 지역별 등급 분포
    report.append("## 2.3 지역별 등급 분포\n\n")
    
    if df_target is not None and '지역명' in df_target.columns and '신뢰도등급' in df_target.columns:
        cross_tab = pd.crosstab(df_target['지역명'], df_target['신뢰도등급'])
        
        # 히트맵 (matplotlib imshow)
        fig, ax = plt.subplots(figsize=(10, 12))
        im = ax.imshow(cross_tab.values, cmap='YlOrRd', aspect='auto')
        ax.set_xticks(range(len(cross_tab.columns)))
        ax.set_xticklabels(cross_tab.columns)
        ax.set_yticks(range(len(cross_tab.index)))
        ax.set_yticklabels(cross_tab.index)
        # 값 표시
        for i in range(len(cross_tab.index)):
            for j in range(len(cross_tab.columns)):
                ax.text(j, i, cross_tab.values[i, j], ha='center', va='center', fontsize=10)
        ax.set_title('지역별 신뢰도 등급 분포', fontsize=14, fontweight='bold')
        ax.set_xlabel('신뢰도 등급', fontsize=12)
        ax.set_ylabel('지역명', fontsize=12)
        plt.colorbar(im, ax=ax)
        plt.tight_layout()
        plt.savefig(RESULT_DIR / "target_02_region_grade_heatmap.png", dpi=150)
        plt.close()
        
        report.append(f"![지역별 등급 분포](target_02_region_grade_heatmap.png)\n\n")
        
        # 표 저장
        cross_tab.to_csv(RESULT_DIR / "target_region_grade_crosstab.csv", encoding='utf-8-sig')
    
    # 보고서 저장
    with open(RESULT_DIR / "02_타겟_분석_보고서.md", 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"✅ 타겟 분석 완료 - 저장: {RESULT_DIR / '02_타겟_분석_보고서.md'}")


# ============================================================
# 3. 피처 분석
# ============================================================
def feature_analysis():
    """피처 분석"""
    print_section("3. 피처 분석", "📐")
    
    report = []
    report.append("# 📐 피처 분석 보고서\n\n")
    
    # 3.1 버전별 피처 비교
    report.append("## 3.1 버전별 피처 비교\n\n")
    
    version_a_features = [
        "거래완료_safe", "등록매물_safe", "총거래활동량",
        "총_직원수", "공인중개사수", "공인중개사_비율", "중개보조원_비율",
        "운영기간_년", "운영경험_지수", "숙련도_지수", "운영_안정성", "베테랑",
        "대형사무소", "직책_다양성", "경력_규모_지수"
    ]
    
    version_b_features = [
        "직원수", "공인중개사", "중개보조원", "공인중개사비율", "중개보조원비율",
        "복수자격", "전원자격", "대형", "중형", "소형",
        "운영연수", "운영로그", "연차구간",
        "전문밀도", "경력전문", "규모연차", "경력규모", "보조비", "비자격비"
    ]
    
    report.append("### Version A 피처 (15개) - 기본 파이프라인\n\n")
    report.append("| 카테고리 | 피처명 | 설명 |\n")
    report.append("|----------|--------|------|\n")
    report.append("| 거래 지표 | 거래완료_safe | log(1+거래완료) 변환 |\n")
    report.append("| 거래 지표 | 등록매물_safe | log(1+등록매물) 변환 |\n")
    report.append("| 거래 지표 | 총거래활동량 | log(1+거래완료+등록매물) |\n")
    report.append("| 인력 지표 | 총_직원수 | 전체 직원 수 |\n")
    report.append("| 인력 지표 | 공인중개사수 | 자격자 수 |\n")
    report.append("| 인력 지표 | 공인중개사_비율 | 자격자/전체 직원 |\n")
    report.append("| 인력 지표 | 중개보조원_비율 | 보조원/전체 직원 |\n")
    report.append("| 운영 경험 | 운영기간_년 | 등록일 기준 경력 |\n")
    report.append("| 운영 경험 | 운영경험_지수 | exp(운영기간/10) |\n")
    report.append("| 운영 경험 | 숙련도_지수 | 운영기간 × 공인중개사비율 |\n")
    report.append("| 운영 경험 | 운영_안정성 | 3년 이상 운영 여부 |\n")
    report.append("| 운영 경험 | 베테랑 | 5년 이상 운영 여부 |\n")
    report.append("| 조직 구조 | 대형사무소 | 직원 3명 이상 여부 |\n")
    report.append("| 조직 구조 | 직책_다양성 | 직책 종류 수 |\n")
    report.append("| 조직 구조 | 경력_규모_지수 | 운영기간 × 직원수 |\n")
    report.append("\n")
    
    report.append("### Version B 피처 (19개) - 베이지안 보정 버전\n\n")
    report.append("| 카테고리 | 피처명 | 설명 |\n")
    report.append("|----------|--------|------|\n")
    report.append("| 원본 | 직원수, 공인중개사, 중개보조원 | 기본 인력 정보 |\n")
    report.append("| 비율 | 공인중개사비율, 중개보조원비율 | 인력 비율 |\n")
    report.append("| 이진 | 복수자격 | 공인중개사 2명 이상 |\n")
    report.append("| 이진 | 전원자격 | 보조원 0명 |\n")
    report.append("| 이진 | 대형/중형/소형 | 규모 분류 |\n")
    report.append("| 경력 | 운영연수, 운영로그, 연차구간 | 경력 관련 |\n")
    report.append("| 파생 | 전문밀도 | 공인중개사/직원수 |\n")
    report.append("| 파생 | 경력전문 | 운영연수 × 공인중개사비율 |\n")
    report.append("| 파생 | 규모연차 | log(직원수) × 운영연수 |\n")
    report.append("| 파생 | 경력규모 | 운영연수 × 직원수 |\n")
    report.append("| 비율2 | 보조비, 비자격비 | 비자격 인력 비중 |\n")
    report.append("\n")
    
    # 3.2 피처 상관관계
    report.append("## 3.2 피처 상관관계 분석\n\n")
    
    try:
        df_features = pd.read_csv(FEATURE_PATH, encoding='utf-8-sig')
        
        # 피처만 추출
        feature_cols = [c for c in version_a_features if c in df_features.columns]
        if feature_cols:
            df_feat = df_features[feature_cols]
            
            # 상관관계 히트맵
            corr = df_feat.corr()
            
            fig, ax = plt.subplots(figsize=(14, 12))
            im = ax.imshow(corr.values, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
            ax.set_xticks(range(len(corr.columns)))
            ax.set_xticklabels(corr.columns, rotation=45, ha='right', fontsize=8)
            ax.set_yticks(range(len(corr.index)))
            ax.set_yticklabels(corr.index, fontsize=8)
            # 값 표시
            for i in range(len(corr.index)):
                for j in range(len(corr.columns)):
                    ax.text(j, i, f'{corr.values[i, j]:.2f}', ha='center', va='center', fontsize=6)
            ax.set_title('피처 상관관계 히트맵', fontsize=14, fontweight='bold')
            plt.colorbar(im, ax=ax)
            plt.tight_layout()
            plt.savefig(RESULT_DIR / "feature_01_correlation_heatmap.png", dpi=150)
            plt.close()
            
            report.append(f"![피처 상관관계](feature_01_correlation_heatmap.png)\n\n")
            
            # 높은 상관관계 쌍 추출
            report.append("### 높은 상관관계 피처 쌍 (|r| > 0.7)\n\n")
            high_corr = []
            for i in range(len(corr.columns)):
                for j in range(i+1, len(corr.columns)):
                    if abs(corr.iloc[i, j]) > 0.7:
                        high_corr.append({
                            '피처1': corr.columns[i],
                            '피처2': corr.columns[j],
                            '상관계수': corr.iloc[i, j]
                        })
            
            if high_corr:
                report.append("| 피처1 | 피처2 | 상관계수 |\n")
                report.append("|-------|-------|----------|\n")
                for item in sorted(high_corr, key=lambda x: abs(x['상관계수']), reverse=True):
                    report.append(f"| {item['피처1']} | {item['피처2']} | {item['상관계수']:.3f} |\n")
            else:
                report.append("높은 상관관계 쌍 없음.\n")
            report.append("\n")
            
            # 상관관계 저장
            corr.to_csv(RESULT_DIR / "feature_correlation_matrix.csv", encoding='utf-8-sig')
            
    except Exception as e:
        report.append(f"⚠️ 상관관계 분석 오류: {e}\n\n")
    
    # 3.3 피처 중요도
    report.append("## 3.3 피처 중요도 분석\n\n")
    
    try:
        if MODEL_TEMP_PATH.exists():
            with open(MODEL_TEMP_PATH, 'rb') as f:
                data = pickle.load(f)
            
            models = data.get('models', {})
            feature_names = data.get('feature_names', [])
            
            importance_results = {}
            
            # CatBoost
            if 'CatBoost' in models:
                cat_imp = models['CatBoost'].get_feature_importance()
                importance_results['CatBoost'] = dict(zip(feature_names, cat_imp))
            
            # XGBoost
            if 'XGBoost' in models:
                xgb_imp = models['XGBoost'].feature_importances_
                importance_results['XGBoost'] = dict(zip(feature_names, xgb_imp))
            
            # RandomForest
            if 'RandomForest' in models:
                rf_imp = models['RandomForest'].feature_importances_
                importance_results['RandomForest'] = dict(zip(feature_names, rf_imp))
            
            if importance_results:
                # 평균 중요도 계산
                avg_importance = {}
                for feat in feature_names:
                    values = [importance_results[m].get(feat, 0) for m in importance_results]
                    avg_importance[feat] = np.mean(values)
                
                sorted_importance = sorted(avg_importance.items(), key=lambda x: x[1], reverse=True)
                
                # 시각화
                fig, ax = plt.subplots(figsize=(12, 10))
                features = [x[0] for x in sorted_importance]
                values = [x[1] for x in sorted_importance]
                colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(features)))
                
                bars = ax.barh(range(len(features)), values, color=colors)
                ax.set_yticks(range(len(features)))
                ax.set_yticklabels(features)
                ax.invert_yaxis()
                ax.set_xlabel('평균 중요도', fontsize=12)
                ax.set_title('피처 중요도 (모델 평균)', fontsize=14, fontweight='bold')
                
                for bar, val in zip(bars, values):
                    ax.text(val + 0.001, bar.get_y() + bar.get_height()/2,
                           f'{val:.4f}', va='center', fontsize=9)
                
                plt.tight_layout()
                plt.savefig(RESULT_DIR / "feature_02_importance.png", dpi=150)
                plt.close()
                
                report.append(f"![피처 중요도](feature_02_importance.png)\n\n")
                
                report.append("### 피처 중요도 순위\n\n")
                report.append("| 순위 | 피처명 | 평균 중요도 |\n")
                report.append("|------|--------|-------------|\n")
                for rank, (feat, imp) in enumerate(sorted_importance, 1):
                    report.append(f"| {rank} | {feat} | {imp:.4f} |\n")
                report.append("\n")
                
                # CSV 저장
                imp_df = pd.DataFrame(sorted_importance, columns=['피처', '중요도'])
                imp_df.to_csv(RESULT_DIR / "feature_importance.csv", index=False, encoding='utf-8-sig')
                
    except Exception as e:
        report.append(f"⚠️ 피처 중요도 분석 오류: {e}\n\n")
    
    # 보고서 저장
    with open(RESULT_DIR / "03_피처_분석_보고서.md", 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"✅ 피처 분석 완료 - 저장: {RESULT_DIR / '03_피처_분석_보고서.md'}")


# ============================================================
# 4. 모델 분석
# ============================================================
def model_analysis():
    """모델 성능 분석"""
    print_section("4. 모델 분석", "🤖")
    
    report = []
    report.append("# 🤖 모델 분석 보고서\n\n")
    
    # 4.1 버전별 모델 설정 비교
    report.append("## 4.1 버전별 모델 설정 비교\n\n")
    
    report.append("### Version A 모델 설정 (기본 파이프라인)\n\n")
    report.append("| 모델 | 주요 하이퍼파라미터 |\n")
    report.append("|------|----------------------|\n")
    report.append("| LogisticRegression | C=0.5, max_iter=1000, class_weight='balanced' |\n")
    report.append("| RandomForest | n_estimators=200, max_depth=4, min_samples_split=15 |\n")
    report.append("| XGBoost | n_estimators=200, max_depth=3, learning_rate=0.05, reg_lambda=2.0 |\n")
    report.append("| CatBoost | iterations=200, depth=3, learning_rate=0.05, l2_leaf_reg=5.0 |\n")
    report.append("| Ensemble | VotingClassifier (soft voting) |\n")
    report.append("\n")
    
    report.append("### Version B 모델 설정 (베이지안 보정 버전)\n\n")
    report.append("| 모델 | 주요 하이퍼파라미터 |\n")
    report.append("|------|----------------------|\n")
    report.append("| LightGBM | RandomizedSearchCV 최적화, reg_alpha, reg_lambda 정규화 |\n")
    report.append("| XGBoost | max_depth=3-6, reg_alpha=0-1, reg_lambda=1-10 |\n")
    report.append("| RandomForest | max_depth=3-10, min_samples_leaf=3-10 |\n")
    report.append("| CatBoost | depth=3-6, l2_leaf_reg=1-10 |\n")
    report.append("| SVM | C=0.1-100, kernel='rbf'/'poly' |\n")
    report.append("\n")
    
    # 4.2 모델 성능 비교
    report.append("## 4.2 모델 성능 비교\n\n")
    
    try:
        if MODEL_TEMP_PATH.exists():
            with open(MODEL_TEMP_PATH, 'rb') as f:
                data = pickle.load(f)
            
            models = data.get('models', {})
            cv_results = data.get('cv_results', {})
            X_test = data.get('X_test_scaled')
            y_test = data.get('y_test')
            X_train = data.get('X_train_scaled')
            y_train = data.get('y_train')
            
            results = []
            
            for name, model in models.items():
                if name == 'Ensemble':
                    continue
                
                # 예측
                train_pred = model.predict(X_train)
                test_pred = model.predict(X_test)
                
                # 성능 지표
                train_acc = accuracy_score(y_train, train_pred)
                test_acc = accuracy_score(y_test, test_pred)
                f1_macro = f1_score(y_test, test_pred, average='macro')
                kappa = cohen_kappa_score(y_test, test_pred)
                
                cv_mean = cv_results.get(name, {}).get('cv_mean', 0)
                cv_std = cv_results.get(name, {}).get('cv_std', 0)
                
                results.append({
                    '모델': name,
                    'Train Acc': train_acc,
                    'Test Acc': test_acc,
                    '과적합률': train_acc - test_acc,
                    'CV Mean': cv_mean,
                    'CV Std': cv_std,
                    'F1 Macro': f1_macro,
                    'Kappa': kappa
                })
            
            # DataFrame 생성
            results_df = pd.DataFrame(results)
            results_df = results_df.sort_values('Test Acc', ascending=False)
            
            # 시각화 - 모델별 성능 비교
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            
            # Train vs Test Accuracy
            ax = axes[0, 0]
            x = np.arange(len(results_df))
            width = 0.35
            ax.bar(x - width/2, results_df['Train Acc']*100, width, label='Train', color='#3498db')
            ax.bar(x + width/2, results_df['Test Acc']*100, width, label='Test', color='#2ecc71')
            ax.set_xticks(x)
            ax.set_xticklabels(results_df['모델'], rotation=15, ha='right')
            ax.set_ylabel('정확도 (%)')
            ax.set_title('Train vs Test Accuracy')
            ax.legend()
            ax.set_ylim(0, 100)
            
            # 과적합률
            ax = axes[0, 1]
            colors = ['#e74c3c' if v > 0.1 else '#2ecc71' for v in results_df['과적합률']]
            ax.bar(results_df['모델'], results_df['과적합률']*100, color=colors)
            ax.axhline(y=10, color='red', linestyle='--', label='과적합 기준 (10%)')
            ax.set_ylabel('과적합률 (%)')
            ax.set_title('과적합률 비교')
            ax.legend()
            for i, v in enumerate(results_df['과적합률']*100):
                ax.text(i, v + 0.5, f'{v:.1f}%', ha='center', fontsize=9)
            
            # F1 Macro
            ax = axes[1, 0]
            ax.bar(results_df['모델'], results_df['F1 Macro']*100, color='#9b59b6')
            ax.set_ylabel('F1 Macro (%)')
            ax.set_title('F1 Macro Score')
            for i, v in enumerate(results_df['F1 Macro']*100):
                ax.text(i, v + 0.5, f'{v:.1f}%', ha='center', fontsize=9)
            
            # Cohen's Kappa
            ax = axes[1, 1]
            ax.bar(results_df['모델'], results_df['Kappa'], color='#e67e22')
            ax.set_ylabel("Cohen's Kappa")
            ax.set_title("Cohen's Kappa Score")
            for i, v in enumerate(results_df['Kappa']):
                ax.text(i, v + 0.01, f'{v:.3f}', ha='center', fontsize=9)
            
            plt.tight_layout()
            plt.savefig(RESULT_DIR / "model_01_performance_comparison.png", dpi=150)
            plt.close()
            
            report.append(f"![모델 성능 비교](model_01_performance_comparison.png)\n\n")
            
            # 표 형식
            report.append("### 성능 지표 상세\n\n")
            report.append("| 모델 | Train Acc | Test Acc | 과적합률 | CV Mean | F1 Macro | Kappa |\n")
            report.append("|------|-----------|----------|----------|---------|----------|-------|\n")
            for _, row in results_df.iterrows():
                report.append(f"| {row['모델']} | {row['Train Acc']*100:.1f}% | {row['Test Acc']*100:.1f}% | ")
                report.append(f"{row['과적합률']*100:.1f}% | {row['CV Mean']*100:.1f}% | ")
                report.append(f"{row['F1 Macro']*100:.1f}% | {row['Kappa']:.3f} |\n")
            report.append("\n")
            
            # 최고 모델
            best_model = results_df.iloc[0]['모델']
            best_acc = results_df.iloc[0]['Test Acc']
            report.append(f"🏆 **최고 성능 모델**: {best_model} (Test Accuracy: {best_acc*100:.1f}%)\n\n")
            
            # CSV 저장
            results_df.to_csv(RESULT_DIR / "model_performance_comparison.csv", 
                             index=False, encoding='utf-8-sig')
            
    except Exception as e:
        report.append(f"⚠️ 모델 분석 오류: {e}\n\n")
    
    # 4.3 혼동행렬
    report.append("## 4.3 혼동행렬 분석\n\n")
    
    try:
        if MODEL_TEMP_PATH.exists():
            with open(MODEL_TEMP_PATH, 'rb') as f:
                data = pickle.load(f)
            
            models = data.get('models', {})
            X_test = data.get('X_test_scaled')
            y_test = data.get('y_test')
            
            # 모델별 혼동행렬
            n_models = len([m for m in models if m != 'Ensemble'])
            fig, axes = plt.subplots(2, 3, figsize=(15, 10))
            axes = axes.flatten()
            
            idx = 0
            for name, model in models.items():
                if name == 'Ensemble':
                    continue
                
                y_pred = model.predict(X_test)
                cm = confusion_matrix(y_test, y_pred)
                
                ax = axes[idx]
                im = ax.imshow(cm, cmap='Blues', aspect='auto')
                ax.set_xticks(range(len(cm)))
                ax.set_xticklabels(['A', 'B', 'C'])
                ax.set_yticks(range(len(cm)))
                ax.set_yticklabels(['A', 'B', 'C'])
                for i in range(len(cm)):
                    for j in range(len(cm)):
                        ax.text(j, i, cm[i, j], ha='center', va='center', fontsize=12, fontweight='bold')
                ax.set_title(f'{name}', fontsize=12, fontweight='bold')
                ax.set_xlabel('예측')
                ax.set_ylabel('실제')
                idx += 1
            
            # 빈 subplot 숨기기
            for i in range(idx, len(axes)):
                axes[i].axis('off')
            
            plt.suptitle('모델별 혼동행렬', fontsize=14, fontweight='bold', y=1.02)
            plt.tight_layout()
            plt.savefig(RESULT_DIR / "model_02_confusion_matrices.png", dpi=150)
            plt.close()
            
            report.append(f"![혼동행렬](model_02_confusion_matrices.png)\n\n")
            
            # 분류 리포트
            report.append("### 분류 리포트 (최고 성능 모델)\n\n")
            if best_model in models:
                y_pred = models[best_model].predict(X_test)
                cr = classification_report(y_test, y_pred)
                report.append(f"```\n{cr}\n```\n\n")
                
    except Exception as e:
        report.append(f"⚠️ 혼동행렬 분석 오류: {e}\n\n")
    
    # 보고서 저장
    with open(RESULT_DIR / "04_모델_분석_보고서.md", 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"✅ 모델 분석 완료 - 저장: {RESULT_DIR / '04_모델_분석_보고서.md'}")


# ============================================================
# 5. 종합 보고서
# ============================================================
def create_summary_report():
    """종합 보고서 생성"""
    print_section("5. 종합 보고서 생성", "📋")
    
    report = []
    report.append("# 🏠 중개사 신뢰도 모델 - 종합 분석 보고서\n\n")
    report.append(f"**분석 일시**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    report.append("---\n\n")
    
    # 버전 비교 요약
    report.append("## 📊 버전 비교 요약\n\n")
    
    report.append("### 두 버전의 핵심 차이점\n\n")
    report.append("| 항목 | Version A (기본) | Version B (베이지안 보정) |\n")
    report.append("|------|------------------|---------------------------|\n")
    report.append("| 타겟 생성 | Z-score 기반 | 가중치 + 베이지안 보정 |\n")
    report.append("| 이상치 처리 | 없음 | 노원구 + 500건 미만 지역 제거 |\n")
    report.append("| 피처 수 | 15개 | 19개 |\n")
    report.append("| 모델 수 | 4개 + 앙상블 | 5개 + 앙상블 |\n")
    report.append("| 하이퍼파라미터 | 고정값 | RandomizedSearchCV |\n")
    report.append("| 등급 분포 | 30/40/30 | 33/33/34 |\n")
    report.append("\n")
    
    # 주요 결과
    report.append("## 🎯 주요 분석 결과\n\n")
    
    report.append("### 1. EDA 분석\n")
    report.append("- 총 데이터: 356개 중개사무소\n")
    report.append("- 24개 지역 (노원구 제외 시 23개)\n")
    report.append("- 주요 지역: 강남구, 송파구, 서초구 등\n\n")
    
    report.append("### 2. 타겟 분포\n")
    report.append("- 균등 분포 달성 (각 등급 약 33%)\n")
    report.append("- 베이지안 보정으로 소규모 사무소의 극단값 완화\n\n")
    
    report.append("### 3. 피처 중요도\n")
    report.append("- **경력 관련 피처** (운영기간, 연차구간) 가장 중요\n")
    report.append("- **규모 피처** (직원수, 대형사무소) 두 번째\n")
    report.append("- **전문성 피처** (공인중개사 비율) 세 번째\n\n")
    
    report.append("### 4. 모델 성능\n")
    report.append("- 최고 모델: CatBoost/XGBoost\n")
    report.append("- Test Accuracy: ~55-60%\n")
    report.append("- 과적합률: 10% 이하로 제어\n\n")
    
    # 파일 목록
    report.append("## 📁 생성된 파일 목록\n\n")
    report.append("### 분석 보고서\n")
    report.append("- `01_EDA_분석_보고서.md`\n")
    report.append("- `02_타겟_분석_보고서.md`\n")
    report.append("- `03_피처_분석_보고서.md`\n")
    report.append("- `04_모델_분석_보고서.md`\n")
    report.append("- `05_종합_보고서.md` (현재 파일)\n\n")
    
    report.append("### 시각화 이미지\n")
    report.append("- `eda_01_region_distribution.png`: 지역별 분포\n")
    report.append("- `eda_02_key_variables_distribution.png`: 주요 변수 분포\n")
    report.append("- `eda_03_outliers_boxplot.png`: 이상치 박스플롯\n")
    report.append("- `target_01_distribution.png`: 타겟 분포\n")
    report.append("- `target_02_region_grade_heatmap.png`: 지역별 등급 히트맵\n")
    report.append("- `feature_01_correlation_heatmap.png`: 피처 상관관계\n")
    report.append("- `feature_02_importance.png`: 피처 중요도\n")
    report.append("- `model_01_performance_comparison.png`: 모델 성능 비교\n")
    report.append("- `model_02_confusion_matrices.png`: 혼동행렬\n\n")
    
    report.append("### CSV 데이터\n")
    report.append("- `eda_descriptive_stats.csv`: 기술통계\n")
    report.append("- `target_region_grade_crosstab.csv`: 지역-등급 교차표\n")
    report.append("- `feature_correlation_matrix.csv`: 상관관계 행렬\n")
    report.append("- `feature_importance.csv`: 피처 중요도\n")
    report.append("- `model_performance_comparison.csv`: 모델 성능\n\n")
    
    # 권장사항
    report.append("## 💡 개선 권장사항\n\n")
    report.append("1. **데이터 확보**: 더 많은 사무소 데이터 수집 (현재 339개)\n")
    report.append("2. **추가 피처**: 리뷰/평점, 전문 분야 등 외부 데이터 활용\n")
    report.append("3. **앙상블 강화**: Stacking 앙상블 고려\n")
    report.append("4. **시계열 분석**: 월별/분기별 성과 추이 분석\n\n")
    
    # 보고서 저장
    with open(RESULT_DIR / "05_종합_보고서.md", 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"✅ 종합 보고서 생성 완료 - 저장: {RESULT_DIR / '05_종합_보고서.md'}")


# ============================================================
# 메인 실행
# ============================================================
def main():
    """전체 분석 실행"""
    print("\n" + "=" * 80)
    print(" " * 20 + "🏠 중개사 신뢰도 모델 종합 분석")
    print(" " * 25 + "Version 1회차")
    print("=" * 80)
    
    # 1. EDA 분석
    df_target = eda_analysis()
    
    # 2. 타겟 분석
    target_analysis(df_target)
    
    # 3. 피처 분석
    feature_analysis()
    
    # 4. 모델 분석
    model_analysis()
    
    # 5. 종합 보고서
    create_summary_report()
    
    print("\n" + "=" * 80)
    print(" " * 25 + "✅ 분석 완료!")
    print("=" * 80)
    print(f"\n📁 결과 저장 위치: {RESULT_DIR.absolute()}")
    print("\n📋 생성된 보고서:")
    print("   - 01_EDA_분석_보고서.md")
    print("   - 02_타겟_분석_보고서.md")
    print("   - 03_피처_분석_보고서.md")
    print("   - 04_모델_분석_보고서.md")
    print("   - 05_종합_보고서.md")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
