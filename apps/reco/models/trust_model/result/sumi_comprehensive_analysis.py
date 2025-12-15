"""
sumi 폴더 파이프라인 - 종합 상세 분석
===========================================
베이지안 보정 + 가중치 적용 + 이상치 제거 버전

분석 항목:
1. EDA 상세 분석
2. 타겟 생성 방식 (베이지안 보정)
3. 피처 분석 (19개)
4. 모델 학습 및 성능 분석
5. 혼동행렬 및 분류 리포트
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import warnings
warnings.filterwarnings('ignore')

# 프로젝트 루트 설정
PROJECT_ROOT = Path("c:/dev/study/eunjeong/SKN18-FINAL-1TEAM")
os.chdir(PROJECT_ROOT)

# sumi 폴더 경로 추가
SUMI_DIR = PROJECT_ROOT / "apps/reco/models/trust_model/pipeline/sumi"
sys.path.insert(0, str(SUMI_DIR))

RESULT_DIR = PROJECT_ROOT / "apps/reco/models/trust_model/result/1회차"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report, cohen_kappa_score, precision_score, recall_score

# sumi 모듈 import
from _00_load_data import load_processed_office_data
import _01_targer_engineering as target_eng
from _02_feature_engineering import main as feature_eng

print("="*80)
print(" 🔬 sumi 파이프라인 종합 분석 (베이지안 보정 버전)")
print("="*80)


# ============================================================
# 1. 데이터 로드 및 전처리
# ============================================================
print("\n" + "="*60)
print(" [1단계] 데이터 로드")
print("="*60)

df_raw = load_processed_office_data()
print(f"✅ 원본 데이터 로드: {len(df_raw)}개")


# ============================================================
# 2. 타겟 생성 (베이지안 보정)
# ============================================================
print("\n" + "="*60)
print(" [2단계] 타겟 생성 (베이지안 보정)")
print("="*60)

df = target_eng.main(df_raw)
print(f"✅ 타겟 생성 완료: {len(df)}개 (이상치 제거 후)")


# ============================================================
# 3. 피처 생성
# ============================================================
print("\n" + "="*60)
print(" [3단계] 피처 생성 (19개)")
print("="*60)

df_enriched, X, feature_names = feature_eng(df)
y = df_enriched["신뢰등급"].astype(int)

print(f"✅ 피처 수: {len(feature_names)}개")
print(f"✅ 샘플 수: {len(X)}개")


# ============================================================
# 보고서 1: EDA 상세 분석
# ============================================================
print("\n" + "="*60)
print(" [분석1] EDA 상세 분석")
print("="*60)

report1 = []
report1.append("# 📊 sumi 파이프라인 - EDA 상세 분석\n\n")
report1.append(f"**분석 일시**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
report1.append("---\n\n")

# 1.1 데이터 개요
report1.append("## 1. 데이터 개요\n\n")
report1.append("### 1.1 원본 vs 전처리 데이터\n\n")
report1.append(f"| 단계 | 레코드 수 | 비고 |\n")
report1.append(f"|------|----------|------|\n")
report1.append(f"| 원본 데이터 | {len(df_raw)}개 | 전체 데이터 |\n")
report1.append(f"| 이상치 제거 후 | {len(df)}개 | 노원구 + 소규모 지역 제외 |\n")
report1.append(f"| 제거된 레코드 | {len(df_raw) - len(df)}개 | {(len(df_raw) - len(df))/len(df_raw)*100:.1f}% 감소 |\n\n")

# 1.2 이상치 제거 상세
report1.append("### 1.2 이상치 제거 기준\n\n")
report1.append("| 필터 | 제거 대상 | 제거 사유 |\n")
report1.append("|------|----------|----------|\n")
report1.append("| 필터 1 | 노원구 | 평균 성사율 45% (타 지역 70% 대비 -25%p) |\n")
report1.append("| 필터 2 | 총매물 500건 미만 지역 | 통계적 신뢰도 부족 |\n\n")

# 1.3 지역별 분포
if 'ldCodeNm' in df.columns:
    region_col = 'ldCodeNm'
elif '지역명' in df.columns:
    region_col = '지역명'
else:
    region_col = None

if region_col:
    region_dist = df[region_col].value_counts()
    report1.append("### 1.3 지역별 분포 (이상치 제거 후)\n\n")
    report1.append("| 순위 | 지역 | 사무소 수 | 비율 |\n")
    report1.append("|------|------|----------|------|\n")
    for rank, (region, count) in enumerate(region_dist.items(), 1):
        pct = count / len(df) * 100
        report1.append(f"| {rank} | {region} | {count} | {pct:.1f}% |\n")
    report1.append("\n")

# 1.4 주요 변수 기술통계
report1.append("### 1.4 주요 변수 기술통계\n\n")
key_cols = []
for col in ['거래완료', '총매물수', '베이지안_성사율', '지역평균성사율']:
    if col in df.columns:
        key_cols.append(col)

if key_cols:
    stats = df[key_cols].describe()
    report1.append("| 통계량 | " + " | ".join(key_cols) + " |\n")
    report1.append("|--------|" + "|".join(["--------"]*len(key_cols)) + "|\n")
    for stat in ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']:
        vals = [f"{stats.loc[stat, c]:.2f}" for c in key_cols]
        report1.append(f"| {stat} | " + " | ".join(vals) + " |\n")
    report1.append("\n")

# 1.5 분포 시각화
fig, axes = plt.subplots(2, 3, figsize=(16, 10))

# 거래완료 분포
if '거래완료' in df.columns:
    ax = axes[0, 0]
    data = df['거래완료'].dropna()
    ax.hist(data, bins=40, color='steelblue', edgecolor='black', alpha=0.7)
    ax.axvline(data.mean(), color='red', linestyle='--', linewidth=2, label=f'평균: {data.mean():.1f}')
    ax.axvline(data.median(), color='green', linestyle='--', linewidth=2, label=f'중앙값: {data.median():.1f}')
    ax.set_xlabel('거래완료')
    ax.set_ylabel('빈도')
    ax.set_title('거래완료 분포', fontweight='bold')
    ax.legend()

# 총매물수 분포
if '총매물수' in df.columns:
    ax = axes[0, 1]
    data = df['총매물수'].dropna()
    ax.hist(data, bins=40, color='coral', edgecolor='black', alpha=0.7)
    ax.axvline(data.mean(), color='red', linestyle='--', linewidth=2, label=f'평균: {data.mean():.1f}')
    ax.set_xlabel('총매물수')
    ax.set_ylabel('빈도')
    ax.set_title('총매물수 분포', fontweight='bold')
    ax.legend()

# 베이지안 성사율 분포
if '베이지안_성사율' in df.columns:
    ax = axes[0, 2]
    data = df['베이지안_성사율'].dropna()
    ax.hist(data, bins=30, color='seagreen', edgecolor='black', alpha=0.7)
    q1 = data.quantile(0.33)
    q2 = data.quantile(0.66)
    ax.axvline(q1, color='red', linestyle='--', linewidth=2, label=f'Q1(33%): {q1:.3f}')
    ax.axvline(q2, color='blue', linestyle='--', linewidth=2, label=f'Q2(66%): {q2:.3f}')
    ax.set_xlabel('베이지안 성사율')
    ax.set_ylabel('빈도')
    ax.set_title('베이지안 성사율 분포', fontweight='bold')
    ax.legend()

# 지역별 사무소 수
if region_col:
    ax = axes[1, 0]
    top_regions = region_dist.head(12)
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(top_regions)))
    ax.barh(range(len(top_regions)), top_regions.values, color=colors)
    ax.set_yticks(range(len(top_regions)))
    ax.set_yticklabels(top_regions.index, fontsize=8)
    ax.set_xlabel('사무소 수')
    ax.set_title('지역별 사무소 수 (Top 12)', fontweight='bold')
    ax.invert_yaxis()

# 신뢰등급 분포
ax = axes[1, 1]
grade_dist = y.value_counts().sort_index()
colors = ['#e74c3c', '#f39c12', '#27ae60']
bars = ax.bar(grade_dist.index, grade_dist.values, color=colors, edgecolor='black')
for bar, val in zip(bars, grade_dist.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
            f'{val}\n({val/len(y)*100:.1f}%)', ha='center', fontsize=10)
ax.set_xlabel('신뢰등급 (0=하위, 1=중위, 2=상위)')
ax.set_ylabel('개수')
ax.set_title('신뢰등급 분포', fontweight='bold')

# 거래완료 vs 총매물수 산점도
if '거래완료' in df.columns and '총매물수' in df.columns:
    ax = axes[1, 2]
    colors = ['#e74c3c', '#f39c12', '#27ae60']
    for grade in sorted(y.unique()):
        mask = y == grade
        ax.scatter(df.loc[mask, '총매물수'], df.loc[mask, '거래완료'], 
                  alpha=0.5, c=colors[grade], label=f'등급 {grade}', s=30)
    ax.set_xlabel('총매물수')
    ax.set_ylabel('거래완료')
    ax.set_title('거래완료 vs 총매물수 (등급별)', fontweight='bold')
    ax.legend()

plt.tight_layout()
plt.savefig(RESULT_DIR / "sumi_eda_distributions.png", dpi=150)
plt.close()

report1.append("![EDA 분포](sumi_eda_distributions.png)\n\n")

# 저장
with open(RESULT_DIR / "sumi_01_EDA_상세분석.md", 'w', encoding='utf-8') as f:
    f.write('\n'.join(report1))
print("✅ sumi_01_EDA_상세분석.md 저장 완료")


# ============================================================
# 보고서 2: 타겟 분석
# ============================================================
print("\n" + "="*60)
print(" [분석2] 타겟 분석")
print("="*60)

report2 = []
report2.append("# 🎯 sumi 파이프라인 - 타겟 분석\n\n")
report2.append(f"**분석 일시**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
report2.append("---\n\n")

# 2.1 타겟 생성 방식
report2.append("## 1. 타겟 생성 방식 (베이지안 보정)\n\n")
report2.append("### 1.1 베이지안 보정 수식\n\n")
report2.append("```\n")
report2.append("베이지안_성사율 = (m × Prior + 거래완료) / (m + 총매물수)\n\n")
report2.append("여기서:\n")
report2.append("  m = 베이지안 임계값 (중위 매물 수)\n")
report2.append("  Prior = 보정된 기준값 = (지역평균성사율 × 분포율) + (전체평균 × (1-분포율))\n")
report2.append("```\n\n")

# 베이지안 파라미터
if '총매물수' in df.columns:
    m_value = df['총매물수'].median()
    report2.append(f"### 1.2 베이지안 임계값 (m)\n\n")
    report2.append(f"- **m = {m_value:.1f}** (총매물수의 중위값)\n")
    report2.append(f"- 매물 수가 {m_value:.1f}개 미만인 경우, 지역/전체 평균값(Prior)의 영향을 더 많이 받음\n\n")

# 2.2 등급 분류 기준
report2.append("### 1.3 등급 분류 기준 (3분위)\n\n")
if '베이지안_성사율' in df.columns:
    q1 = df['베이지안_성사율'].quantile(0.33)
    q2 = df['베이지안_성사율'].quantile(0.66)
    report2.append(f"| 등급 | 숫자값 | 기준 (베이지안 성사율) | 설명 |\n")
    report2.append(f"|------|--------|----------------------|------|\n")
    report2.append(f"| 하위 | 0 | < {q1:.4f} | 하위 33% |\n")
    report2.append(f"| 중위 | 1 | {q1:.4f} ~ {q2:.4f} | 중위 33% |\n")
    report2.append(f"| 상위 | 2 | ≥ {q2:.4f} | 상위 34% |\n\n")

# 2.3 등급 분포
report2.append("## 2. 등급 분포\n\n")
grade_dist = y.value_counts().sort_index()
grade_pct = y.value_counts(normalize=True).sort_index() * 100

report2.append("| 등급 | 설명 | 개수 | 비율 |\n")
report2.append("|------|------|------|------|\n")
grade_names = {0: "하위 (Bottom)", 1: "중위 (Middle)", 2: "상위 (Top)"}
for grade in grade_dist.index:
    report2.append(f"| {grade} | {grade_names.get(grade)} | {grade_dist[grade]} | {grade_pct[grade]:.1f}% |\n")
report2.append(f"| **합계** | - | **{len(y)}** | **100%** |\n\n")

# 2.4 등급별 통계
report2.append("## 3. 등급별 상세 통계\n\n")
for grade in sorted(y.unique()):
    mask = y == grade
    subset = df[mask]
    report2.append(f"### 등급 {grade} ({grade_names.get(grade)})\n\n")
    report2.append(f"- **개수**: {len(subset)}개\n")
    if '거래완료' in df.columns:
        report2.append(f"- **평균 거래완료**: {subset['거래완료'].mean():.1f}건\n")
    if '총매물수' in df.columns:
        report2.append(f"- **평균 총매물수**: {subset['총매물수'].mean():.1f}건\n")
    if '베이지안_성사율' in df.columns:
        report2.append(f"- **평균 베이지안 성사율**: {subset['베이지안_성사율'].mean():.4f}\n")
        report2.append(f"- **베이지안 성사율 범위**: {subset['베이지안_성사율'].min():.4f} ~ {subset['베이지안_성사율'].max():.4f}\n")
    report2.append("\n")

# 시각화
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# 막대그래프
colors = ['#e74c3c', '#f39c12', '#27ae60']
bars = axes[0].bar(grade_dist.index, grade_dist.values, color=colors, edgecolor='black')
for bar, pct in zip(bars, grade_pct.values):
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                f'{pct:.1f}%', ha='center', fontweight='bold', fontsize=12)
axes[0].set_xlabel('등급')
axes[0].set_ylabel('개수')
axes[0].set_title('타겟 등급 분포', fontweight='bold', fontsize=14)
axes[0].set_xticks([0, 1, 2])
axes[0].set_xticklabels(['하위(0)', '중위(1)', '상위(2)'])

# 파이차트
axes[1].pie(grade_dist.values, labels=['하위', '중위', '상위'], colors=colors, 
           autopct='%1.1f%%', startangle=90, explode=[0.02, 0.02, 0.02])
axes[1].set_title('등급 비율', fontweight='bold', fontsize=14)

# 등급별 베이지안 성사율 박스플롯
if '베이지안_성사율' in df.columns:
    grade_data = [df[y==g]['베이지안_성사율'].dropna() for g in sorted(y.unique())]
    bp = axes[2].boxplot(grade_data, patch_artist=True, labels=['하위', '중위', '상위'])
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    axes[2].set_xlabel('등급')
    axes[2].set_ylabel('베이지안 성사율')
    axes[2].set_title('등급별 베이지안 성사율 분포', fontweight='bold', fontsize=14)

plt.tight_layout()
plt.savefig(RESULT_DIR / "sumi_target_analysis.png", dpi=150)
plt.close()

report2.append("![타겟 분석](sumi_target_analysis.png)\n\n")

# 저장
with open(RESULT_DIR / "sumi_02_타겟_분석.md", 'w', encoding='utf-8') as f:
    f.write('\n'.join(report2))
print("✅ sumi_02_타겟_분석.md 저장 완료")


# ============================================================
# 보고서 3: 피처 분석
# ============================================================
print("\n" + "="*60)
print(" [분석3] 피처 분석")
print("="*60)

report3 = []
report3.append("# 📐 sumi 파이프라인 - 피처 분석 (19개)\n\n")
report3.append(f"**분석 일시**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
report3.append("---\n\n")

# 3.1 피처 목록
report3.append("## 1. 피처 목록 (19개)\n\n")
report3.append("### 1.1 카테고리별 피처\n\n")
report3.append("| 카테고리 | 피처명 | 설명 |\n")
report3.append("|----------|--------|------|\n")
report3.append("| 원본 (3개) | 직원수, 공인중개사, 중개보조원 | 기본 인력 정보 |\n")
report3.append("| 비율 (2개) | 공인중개사비율, 중개보조원비율 | 자격자/보조원 비율 |\n")
report3.append("| 이진 (5개) | 복수자격, 전원자격, 대형, 중형, 소형 | 조건 충족 여부 |\n")
report3.append("| 경력 (3개) | 운영연수, 운영로그, 연차구간 | 등록일 기반 |\n")
report3.append("| 파생 (4개) | 전문밀도, 경력전문, 규모연차, 경력규모 | 복합 피처 |\n")
report3.append("| 비율2 (2개) | 보조비, 비자격비 | 비자격 인력 비중 |\n\n")

# 피처 상세 목록
report3.append("### 1.2 피처 상세 목록\n\n")
report3.append("| 번호 | 피처명 | 설명 |\n")
report3.append("|------|--------|------|\n")
feature_desc = {
    '직원수': '전체 직원 수', '공인중개사': '자격자 수', '중개보조원': '보조원 수',
    '공인중개사비율': '자격자/전체', '중개보조원비율': '보조원/전체',
    '복수자격': '2명 이상 자격자', '전원자격': '보조원 0명',
    '대형': '5명 이상', '중형': '3-4명', '소형': '2명 이하',
    '운영연수': '경력 (년)', '운영로그': 'log(운영일수)', '연차구간': '0-3 구간',
    '전문밀도': '공인/직원수', '경력전문': '운영연수×비율',
    '규모연차': 'log(직원)×운영연수', '경력규모': '운영연수×직원수',
    '보조비': '보조/자격', '비자격비': '비자격/전체'
}
for i, feat in enumerate(feature_names, 1):
    desc = feature_desc.get(feat, '-')
    report3.append(f"| {i} | `{feat}` | {desc} |\n")
report3.append("\n")

# 3.2 피처 통계
report3.append("## 2. 피처별 통계\n\n")
stats = X.describe()
report3.append("| 피처 | 평균 | 표준편차 | 최소 | 중앙값 | 최대 |\n")
report3.append("|------|------|----------|------|--------|------|\n")
for col in X.columns:
    report3.append(f"| {col} | {stats.loc['mean', col]:.3f} | {stats.loc['std', col]:.3f} | ")
    report3.append(f"{stats.loc['min', col]:.3f} | {stats.loc['50%', col]:.3f} | {stats.loc['max', col]:.3f} |\n")
report3.append("\n")

# 3.3 상관관계
report3.append("## 3. 피처 상관관계 분석\n\n")
corr = X.corr()

# 높은 상관관계 추출
high_corr = []
for i in range(len(corr.columns)):
    for j in range(i+1, len(corr.columns)):
        if abs(corr.iloc[i, j]) > 0.7:
            high_corr.append((corr.columns[i], corr.columns[j], corr.iloc[i, j]))

report3.append("### 3.1 높은 상관관계 피처 쌍 (|r| > 0.7)\n\n")
if high_corr:
    report3.append("| 피처1 | 피처2 | 상관계수 | 해석 |\n")
    report3.append("|-------|-------|----------|------|\n")
    for f1, f2, r in sorted(high_corr, key=lambda x: abs(x[2]), reverse=True):
        sign = "양의 상관" if r > 0 else "음의 상관"
        report3.append(f"| {f1} | {f2} | {r:.3f} | {sign} |\n")
    report3.append("\n")
else:
    report3.append("높은 상관관계 쌍 없음.\n\n")

# 히트맵
fig, ax = plt.subplots(figsize=(16, 14))
im = ax.imshow(corr.values, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
ax.set_xticks(range(len(corr.columns)))
ax.set_xticklabels(corr.columns, rotation=45, ha='right', fontsize=9)
ax.set_yticks(range(len(corr.index)))
ax.set_yticklabels(corr.index, fontsize=9)
for i in range(len(corr.index)):
    for j in range(len(corr.columns)):
        color = 'white' if abs(corr.values[i, j]) > 0.5 else 'black'
        ax.text(j, i, f'{corr.values[i, j]:.2f}', ha='center', va='center', fontsize=7, color=color)
ax.set_title('sumi 피처 상관관계 히트맵 (19개)', fontweight='bold', fontsize=14)
plt.colorbar(im, ax=ax, shrink=0.8)
plt.tight_layout()
plt.savefig(RESULT_DIR / "sumi_feature_correlation.png", dpi=150)
plt.close()

report3.append("![피처 상관관계](sumi_feature_correlation.png)\n\n")

# 저장
with open(RESULT_DIR / "sumi_03_피처_분석.md", 'w', encoding='utf-8') as f:
    f.write('\n'.join(report3))
print("✅ sumi_03_피처_분석.md 저장 완료")


# ============================================================
# 모델 학습
# ============================================================
print("\n" + "="*60)
print(" [4단계] 모델 학습")
print("="*60)

# Train/Test 분리
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"Train: {len(X_train)}개, Test: {len(X_test)}개")

# 스케일링
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# CV 설정
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# 모델 학습
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC

models = {}
all_results = []

# 1. RandomForest
print("[1/5] RandomForest 학습...")
rf = RandomForestClassifier(n_estimators=200, max_depth=5, min_samples_leaf=5,
                           class_weight='balanced', random_state=42, n_jobs=-1)
rf.fit(X_train_scaled, y_train)
models['RandomForest'] = rf

# 2. XGBoost
try:
    from xgboost import XGBClassifier
    print("[2/5] XGBoost 학습...")
    xgb = XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.05,
                       reg_lambda=5.0, reg_alpha=0.5, use_label_encoder=False,
                       eval_metric='mlogloss', random_state=42, verbosity=0)
    xgb.fit(X_train_scaled, y_train)
    models['XGBoost'] = xgb
except ImportError:
    print("   ⚠️ XGBoost 미설치")

# 3. CatBoost
try:
    from catboost import CatBoostClassifier
    print("[3/5] CatBoost 학습...")
    cat = CatBoostClassifier(iterations=200, depth=4, learning_rate=0.05,
                            l2_leaf_reg=5.0, auto_class_weights='Balanced',
                            random_state=42, verbose=False)
    cat.fit(X_train_scaled, y_train)
    models['CatBoost'] = cat
except ImportError:
    print("   ⚠️ CatBoost 미설치")

# 4. LightGBM
try:
    from lightgbm import LGBMClassifier
    print("[4/5] LightGBM 학습...")
    lgb = LGBMClassifier(n_estimators=200, max_depth=4, learning_rate=0.05,
                        reg_alpha=0.5, reg_lambda=5.0, class_weight='balanced',
                        random_state=42, verbose=-1)
    lgb.fit(X_train_scaled, y_train)
    models['LightGBM'] = lgb
except ImportError:
    print("   ⚠️ LightGBM 미설치")

# 5. SVM
print("[5/5] SVM 학습...")
svm = SVC(C=1.0, kernel='rbf', class_weight='balanced', probability=True, random_state=42)
svm.fit(X_train_scaled, y_train)
models['SVM'] = svm

print(f"\n✅ 학습 완료: {len(models)}개 모델")


# ============================================================
# 보고서 4: 모델 분석
# ============================================================
print("\n" + "="*60)
print(" [분석4] 모델 분석")
print("="*60)

report4 = []
report4.append("# 🤖 sumi 파이프라인 - 모델 분석\n\n")
report4.append(f"**분석 일시**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
report4.append("---\n\n")

# 4.1 모델 설정
report4.append("## 1. 모델 하이퍼파라미터 설정\n\n")
report4.append("| 모델 | 주요 하이퍼파라미터 |\n")
report4.append("|------|--------------------|\n")
report4.append("| RandomForest | n_estimators=200, max_depth=5, min_samples_leaf=5, class_weight='balanced' |\n")
report4.append("| XGBoost | n_estimators=200, max_depth=4, learning_rate=0.05, reg_lambda=5.0, reg_alpha=0.5 |\n")
report4.append("| CatBoost | iterations=200, depth=4, learning_rate=0.05, l2_leaf_reg=5.0, auto_class_weights='Balanced' |\n")
report4.append("| LightGBM | n_estimators=200, max_depth=4, learning_rate=0.05, reg_alpha=0.5, reg_lambda=5.0 |\n")
report4.append("| SVM | C=1.0, kernel='rbf', class_weight='balanced' |\n\n")

# 4.2 성능 평가
report4.append("## 2. 모델 성능 비교\n\n")

for name, model in models.items():
    train_pred = model.predict(X_train_scaled)
    test_pred = model.predict(X_test_scaled)
    
    train_acc = accuracy_score(y_train, train_pred)
    test_acc = accuracy_score(y_test, test_pred)
    f1 = f1_score(y_test, test_pred, average='macro')
    precision = precision_score(y_test, test_pred, average='macro')
    recall = recall_score(y_test, test_pred, average='macro')
    kappa = cohen_kappa_score(y_test, test_pred)
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
    
    all_results.append({
        '모델': name, 'Train Acc': train_acc, 'Test Acc': test_acc,
        '과적합률': train_acc - test_acc, 'CV Mean': cv_scores.mean(), 'CV Std': cv_scores.std(),
        'F1 Macro': f1, 'Precision': precision, 'Recall': recall, 'Kappa': kappa
    })

results_df = pd.DataFrame(all_results).sort_values('Test Acc', ascending=False)

report4.append("### 2.1 전체 성능 비교\n\n")
report4.append("| 모델 | Train Acc | Test Acc | 과적합률 | CV Mean | F1 Macro | Precision | Recall | Kappa |\n")
report4.append("|------|-----------|----------|----------|---------|----------|-----------|--------|-------|\n")
for _, row in results_df.iterrows():
    report4.append(f"| {row['모델']} | {row['Train Acc']*100:.1f}% | {row['Test Acc']*100:.1f}% | ")
    report4.append(f"{row['과적합률']*100:.1f}% | {row['CV Mean']*100:.1f}% | {row['F1 Macro']*100:.1f}% | ")
    report4.append(f"{row['Precision']*100:.1f}% | {row['Recall']*100:.1f}% | {row['Kappa']:.3f} |\n")
report4.append("\n")

best_model_name = results_df.iloc[0]['모델']
report4.append(f"🏆 **최고 성능 모델**: {best_model_name} (Test Acc: {results_df.iloc[0]['Test Acc']*100:.1f}%)\n\n")

# 시각화
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Train vs Test
ax = axes[0, 0]
x = np.arange(len(results_df))
width = 0.35
ax.bar(x - width/2, results_df['Train Acc']*100, width, label='Train', color='#3498db')
ax.bar(x + width/2, results_df['Test Acc']*100, width, label='Test', color='#2ecc71')
ax.set_xticks(x)
ax.set_xticklabels(results_df['모델'], rotation=15, ha='right')
ax.set_ylabel('정확도 (%)')
ax.set_title('Train vs Test Accuracy', fontweight='bold')
ax.legend()
ax.set_ylim(0, 100)

# 과적합률
ax = axes[0, 1]
colors_bar = ['#e74c3c' if v > 0.1 else '#2ecc71' for v in results_df['과적합률']]
bars = ax.bar(results_df['모델'], results_df['과적합률']*100, color=colors_bar, edgecolor='black')
ax.axhline(y=10, color='red', linestyle='--', linewidth=2, label='과적합 기준 (10%)')
ax.set_ylabel('과적합률 (%)')
ax.set_title('과적합률 비교', fontweight='bold')
ax.legend()
for bar, v in zip(bars, results_df['과적합률']*100):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'{v:.1f}%', ha='center', fontsize=9)

# F1 / Precision / Recall
ax = axes[1, 0]
x = np.arange(len(results_df))
width = 0.25
ax.bar(x - width, results_df['F1 Macro']*100, width, label='F1 Macro', color='#9b59b6')
ax.bar(x, results_df['Precision']*100, width, label='Precision', color='#3498db')
ax.bar(x + width, results_df['Recall']*100, width, label='Recall', color='#e67e22')
ax.set_xticks(x)
ax.set_xticklabels(results_df['모델'], rotation=15, ha='right')
ax.set_ylabel('점수 (%)')
ax.set_title('F1 / Precision / Recall', fontweight='bold')
ax.legend()

# Kappa
ax = axes[1, 1]
colors_kappa = plt.cm.viridis(np.linspace(0.3, 0.9, len(results_df)))
bars = ax.bar(results_df['모델'], results_df['Kappa'], color=colors_kappa, edgecolor='black')
ax.set_ylabel("Cohen's Kappa")
ax.set_title("Cohen's Kappa Score", fontweight='bold')
for bar, v in zip(bars, results_df['Kappa']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, f'{v:.3f}', ha='center', fontsize=9)

plt.tight_layout()
plt.savefig(RESULT_DIR / "sumi_model_performance.png", dpi=150)
plt.close()

report4.append("![모델 성능](sumi_model_performance.png)\n\n")

# 4.3 혼동행렬
report4.append("## 3. 혼동행렬\n\n")

n_models = len(models)
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for idx, (name, model) in enumerate(models.items()):
    y_pred = model.predict(X_test_scaled)
    cm = confusion_matrix(y_test, y_pred)
    
    ax = axes[idx]
    im = ax.imshow(cm, cmap='Blues')
    ax.set_xticks(range(3))
    ax.set_xticklabels(['하위', '중위', '상위'])
    ax.set_yticks(range(3))
    ax.set_yticklabels(['하위', '중위', '상위'])
    for i in range(3):
        for j in range(3):
            ax.text(j, i, cm[i, j], ha='center', va='center', fontsize=14, fontweight='bold')
    ax.set_title(name, fontweight='bold', fontsize=12)
    ax.set_xlabel('예측')
    ax.set_ylabel('실제')

# 빈 subplot 숨기기
for i in range(len(models), 6):
    axes[i].axis('off')

plt.suptitle('sumi 모델별 혼동행렬', fontweight='bold', fontsize=14)
plt.tight_layout()
plt.savefig(RESULT_DIR / "sumi_confusion_matrices.png", dpi=150)
plt.close()

report4.append("![혼동행렬](sumi_confusion_matrices.png)\n\n")

# 4.4 분류 리포트
report4.append("## 4. 분류 리포트 (최고 성능 모델: " + best_model_name + ")\n\n")
y_pred = models[best_model_name].predict(X_test_scaled)
cr = classification_report(y_test, y_pred, target_names=['하위', '중위', '상위'])
report4.append(f"```\n{cr}\n```\n\n")

# 4.5 피처 중요도
report4.append("## 5. 피처 중요도\n\n")

if 'CatBoost' in models:
    imp = models['CatBoost'].get_feature_importance()
    imp_model = 'CatBoost'
elif 'XGBoost' in models:
    imp = models['XGBoost'].feature_importances_
    imp_model = 'XGBoost'
else:
    imp = models['RandomForest'].feature_importances_
    imp_model = 'RandomForest'

imp_df = pd.DataFrame({'피처': feature_names, '중요도': imp})
imp_df = imp_df.sort_values('중요도', ascending=False)

report4.append(f"### {imp_model} 기준 피처 중요도\n\n")
report4.append("| 순위 | 피처 | 중요도 |\n")
report4.append("|------|------|--------|\n")
for rank, (_, row) in enumerate(imp_df.iterrows(), 1):
    report4.append(f"| {rank} | {row['피처']} | {row['중요도']:.4f} |\n")
report4.append("\n")

# 시각화
fig, ax = plt.subplots(figsize=(12, 10))
colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(imp_df)))
bars = ax.barh(range(len(imp_df)), imp_df['중요도'].values, color=colors)
ax.set_yticks(range(len(imp_df)))
ax.set_yticklabels(imp_df['피처'].values)
ax.invert_yaxis()
ax.set_xlabel('중요도')
ax.set_title(f'sumi 피처 중요도 ({imp_model})', fontweight='bold', fontsize=14)
for bar, v in zip(bars, imp_df['중요도'].values):
    ax.text(v + 0.001, bar.get_y() + bar.get_height()/2, f'{v:.3f}', va='center', fontsize=9)
plt.tight_layout()
plt.savefig(RESULT_DIR / "sumi_feature_importance.png", dpi=150)
plt.close()

report4.append("![피처 중요도](sumi_feature_importance.png)\n\n")

# 저장
with open(RESULT_DIR / "sumi_04_모델_분석.md", 'w', encoding='utf-8') as f:
    f.write('\n'.join(report4))
print("✅ sumi_04_모델_분석.md 저장 완료")

# 결과 CSV 저장
results_df.to_csv(RESULT_DIR / "sumi_model_results.csv", index=False, encoding='utf-8-sig')
imp_df.to_csv(RESULT_DIR / "sumi_feature_importance.csv", index=False, encoding='utf-8-sig')


# ============================================================
# 종합 보고서
# ============================================================
print("\n" + "="*60)
print(" [분석5] 종합 보고서")
print("="*60)

report5 = []
report5.append("# 📋 sumi 파이프라인 - 종합 분석 보고서\n\n")
report5.append(f"**분석 일시**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
report5.append("---\n\n")

report5.append("## 1. 분석 개요\n\n")
report5.append("sumi 파이프라인은 **베이지안 보정 + 가중치 적용 + 이상치 제거**를 적용한 버전입니다.\n\n")

report5.append("### 핵심 특징\n")
report5.append("1. **이상치 제거**: 노원구 + 총매물 500건 미만 지역 제외\n")
report5.append("2. **베이지안 보정**: 소규모 사무소의 극단값 완화\n")
report5.append("3. **가중치 적용**: 지역별 매물분포율 반영\n")
report5.append("4. **19개 피처**: 6개 카테고리 (원본/비율/이진/경력/파생/비율2)\n")
report5.append("5. **5개 모델 앙상블**: RF, XGB, CatBoost, LightGBM, SVM\n\n")

report5.append("## 2. 주요 결과 요약\n\n")
report5.append(f"| 항목 | 수치 |\n")
report5.append(f"|------|------|\n")
report5.append(f"| 원본 데이터 | {len(df_raw)}개 |\n")
report5.append(f"| 이상치 제거 후 | {len(df)}개 |\n")
report5.append(f"| 피처 수 | {len(feature_names)}개 |\n")
report5.append(f"| 등급 분포 | 하위:{grade_dist[0]} / 중위:{grade_dist[1]} / 상위:{grade_dist[2]} |\n")
report5.append(f"| 최고 모델 | {best_model_name} |\n")
report5.append(f"| Test Accuracy | {results_df.iloc[0]['Test Acc']*100:.1f}% |\n")
report5.append(f"| F1 Macro | {results_df.iloc[0]['F1 Macro']*100:.1f}% |\n\n")

report5.append("## 3. 생성된 파일 목록\n\n")
report5.append("### 분석 보고서\n")
report5.append("- `sumi_01_EDA_상세분석.md`\n")
report5.append("- `sumi_02_타겟_분석.md`\n")
report5.append("- `sumi_03_피처_분석.md`\n")
report5.append("- `sumi_04_모델_분석.md`\n")
report5.append("- `sumi_05_종합_보고서.md` (현재 파일)\n\n")

report5.append("### 시각화 이미지\n")
report5.append("- `sumi_eda_distributions.png`\n")
report5.append("- `sumi_target_analysis.png`\n")
report5.append("- `sumi_feature_correlation.png`\n")
report5.append("- `sumi_model_performance.png`\n")
report5.append("- `sumi_confusion_matrices.png`\n")
report5.append("- `sumi_feature_importance.png`\n\n")

report5.append("### CSV 데이터\n")
report5.append("- `sumi_model_results.csv`\n")
report5.append("- `sumi_feature_importance.csv`\n")

# 저장
with open(RESULT_DIR / "sumi_05_종합_보고서.md", 'w', encoding='utf-8') as f:
    f.write('\n'.join(report5))
print("✅ sumi_05_종합_보고서.md 저장 완료")


print("\n" + "="*80)
print(" ✅ sumi 파이프라인 분석 완료!")
print(f" 📁 저장 위치: {RESULT_DIR}")
print("="*80)
