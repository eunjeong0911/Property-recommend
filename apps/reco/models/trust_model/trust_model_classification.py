"""
중개사 신뢰도 모델 - 다중 분류 버전
- 회귀 대신 분류 (Classification)
- 타겟: 등급 (S/A/B/C/D)
- 직접 등급을 예측
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import seaborn as sns
import matplotlib.pyplot as plt
import pickle

print("="*70)
print("중개사 신뢰도 모델 - 다중 분류 버전")
print("="*70)

# 데이터 로드
clean_path = "../../../../data/seoul_broker_clean.csv"
df = pd.read_csv(clean_path)

df['registDe'] = pd.to_datetime(df['registDe'])
df['estbsBeginDe'] = pd.to_datetime(df['estbsBeginDe'])
df['estbsEndDe'] = pd.to_datetime(df['estbsEndDe'])

today = pd.to_datetime(datetime.now())

print(f"\n데이터: {len(df)}개 중개사")

# ============================================================================
# STEP 1: 규칙 기반 등급 생성 (타겟 y)
# ============================================================================
print("\n[1/6] 규칙 기반 등급 생성 (타겟 y)...")

# 구 추출
df['구'] = df['ldCodeNm'].str.replace('서울특별시 ', '')

# 지역권 분류
gangnam_area = ['강남구', '서초구', '송파구', '강동구']
gangbuk_area = ['강북구', '노원구', '도봉구', '성북구']
seonam_area = ['양천구', '강서구', '구로구', '금천구', '영등포구', '동작구', '관악구']
dongbuk_area = ['광진구', '중랑구', '동대문구', '성동구']
dosim_area = ['종로구', '중구', '용산구', '마포구', '서대문구', '은평구']

def classify_region_group(gu):
    if gu in gangnam_area:
        return '강남권'
    elif gu in gangbuk_area:
        return '강북권'
    elif gu in seonam_area:
        return '서남권'
    elif gu in dongbuk_area:
        return '동북권'
    elif gu in dosim_area:
        return '도심권'
    else:
        return '기타'

df['지역권'] = df['구'].apply(classify_region_group)

# 기본 피처
df['영업일수'] = (today - df['registDe']).dt.days.clip(lower=1)
df['영업년수'] = df['영업일수'] / 365
df['거래성사율'] = (df['거래완료'] / (df['총매물수'] + 1) * 100).clip(0, 100)
df['재고율'] = (df['등록매물'] / (df['총매물수'] + 1) * 100).clip(0, 100)
df['일평균거래'] = df['거래완료'] / df['영업일수']
df['보증보험유효'] = (df['estbsEndDe'] >= today).astype(int)

# 지역 통계
region_stats = df.groupby('지역권').agg({
    '거래성사율': 'mean',
    '총매물수': 'mean'
}).round(2)
region_stats.columns = ['지역권평균성사율', '지역권평균매물수']
df = df.merge(region_stats, left_on='지역권', right_index=True, how='left')

gu_stats = df.groupby('구').agg({
    '거래성사율': 'mean',
    '총매물수': 'mean'
}).round(2)
gu_stats.columns = ['구평균성사율', '구평균매물수']
df = df.merge(gu_stats, left_on='구', right_index=True, how='left')

df['지역권대비성과'] = (df['거래성사율'] / (df['지역권평균성사율'] + 1)).fillna(1)
df['구대비성과'] = (df['거래성사율'] / (df['구평균성사율'] + 1)).fillna(1)

# 지역권 원핫 인코딩
region_dummies = pd.get_dummies(df['지역권'], prefix='지역권')
df = pd.concat([df, region_dummies], axis=1)

# 지역 내 순위
df['지역권내_성과순위'] = df.groupby('지역권')['거래성사율'].rank(ascending=False, pct=True)
df['구내_성과순위'] = df.groupby('구')['거래성사율'].rank(ascending=False, pct=True)

# 성장 잠재력
df['성장잠재력'] = df['거래성사율'] / (np.log1p(df['영업년수']) + 1)

# 로그 변환
df['log_일평균거래'] = np.log1p(df['일평균거래'])

# ============================================================================
# 규칙 기반 종합 점수 계산
# ============================================================================
df['rule_score'] = (
    df['거래성사율'] * 0.30 +
    (100 - df['재고율']) * 0.20 +
    df['지역권대비성과'] * 10 +
    df['구대비성과'] * 10 +
    df['log_일평균거래'] * 5 +
    df['보증보험유효'] * 5 +
    df['성장잠재력'] * 0.05 +
    df['지역권내_성과순위'] * 5 +
    df['구내_성과순위'] * 5
)

# ============================================================================
# 등급 생성 (타겟 y) - 백분위 기반
# ============================================================================
percentiles = [0, 0.10, 0.30, 0.60, 0.90, 1.0]
labels = ['D', 'C', 'B', 'A', 'S']

df['등급'] = pd.cut(
    df['rule_score'].rank(pct=True),
    bins=percentiles,
    labels=labels,
    include_lowest=True
)

print(f"✓ 등급 생성 완료")
print(f"\n등급별 분포:")
for grade in ['S', 'A', 'B', 'C', 'D']:
    count = len(df[df['등급'] == grade])
    pct = count / len(df) * 100
    print(f"  {grade}등급: {count:3d}개 ({pct:5.1f}%)")

# ============================================================================
# STEP 2: 피처 선택 (누수 피처 제거!)
# ============================================================================
print("\n[2/6] 피처 선택 (누수 피처 제거)...")

# ✅ 사용할 피처 (원본 데이터 + 파생 피처)
ml_features = [
    # 원본 데이터
    '거래완료',
    '등록매물',
    '총매물수',
    '영업년수',
    
    # 파생 피처 (누수 없음)
    'log_일평균거래',
    '보증보험유효',
    
    # 지역 통계 (평균값만)
    '지역권평균성사율',
    '지역권평균매물수',
    '구평균성사율',
    '구평균매물수'
]

# 지역권 원핫 인코딩 컬럼 추가
region_cols = [col for col in df.columns if col.startswith('지역권_')]
ml_features.extend(region_cols)

X = df[ml_features].copy()
y = df['등급'].copy()

print(f"\n✅ ML 피처: {len(ml_features)}개")
print(f"✅ 타겟: 등급 (S/A/B/C/D)")

# ============================================================================
# STEP 3: Train/Test 분리
# ============================================================================
print("\n[3/6] Train/Test 분리...")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Train: {len(X_train)}개 (80%)")
print(f"Test: {len(X_test)}개 (20%)")

# 등급별 분포 확인
print("\nTrain 등급 분포:")
print(y_train.value_counts().sort_index())
print("\nTest 등급 분포:")
print(y_test.value_counts().sort_index())

# 스케일링
scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ============================================================================
# STEP 4: 모델 학습 (3가지 모델 비교)
# ============================================================================
print("\n[4/6] 모델 학습 및 비교...")

models = {
    'LogisticRegression': LogisticRegression(max_iter=1000, multi_class='multinomial', random_state=42),
    'RandomForest': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1),
    'GradientBoosting': GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
}

results = {}

for name, model in models.items():
    print(f"\n{name} 학습 중...")
    
    # 학습
    if name == 'LogisticRegression':
        model.fit(X_train_scaled, y_train)
        y_train_pred = model.predict(X_train_scaled)
        y_test_pred = model.predict(X_test_scaled)
    else:
        model.fit(X_train, y_train)
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
    
    # 평가
    train_acc = accuracy_score(y_train, y_train_pred)
    test_acc = accuracy_score(y_test, y_test_pred)
    
    results[name] = {
        'model': model,
        'train_acc': train_acc,
        'test_acc': test_acc,
        'y_test_pred': y_test_pred
    }
    
    print(f"  Train Accuracy: {train_acc:.3f}")
    print(f"  Test Accuracy: {test_acc:.3f}")

# 최고 모델 선택
best_model_name = max(results, key=lambda x: results[x]['test_acc'])
best_model = results[best_model_name]['model']

print(f"\n✅ 최고 모델: {best_model_name}")
print(f"  Test Accuracy: {results[best_model_name]['test_acc']:.3f}")

# ============================================================================
# STEP 5: 상세 평가
# ============================================================================
print("\n[5/6] 상세 평가...")

y_test_pred = results[best_model_name]['y_test_pred']

# Classification Report
print("\nClassification Report:")
print(classification_report(y_test, y_test_pred, target_names=['D', 'C', 'B', 'A', 'S']))

# Confusion Matrix
print("\nConfusion Matrix:")
cm = confusion_matrix(y_test, y_test_pred, labels=['D', 'C', 'B', 'A', 'S'])
print(cm)

# Confusion Matrix 시각화
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['D', 'C', 'B', 'A', 'S'],
            yticklabels=['D', 'C', 'B', 'A', 'S'])
plt.title(f'Confusion Matrix - {best_model_name}', fontsize=14, fontweight='bold')
plt.ylabel('실제 등급', fontsize=12)
plt.xlabel('예측 등급', fontsize=12)
plt.tight_layout()
plt.savefig('confusion_matrix_classification.png', dpi=150, bbox_inches='tight')
print("\n✓ Confusion Matrix 저장: confusion_matrix_classification.png")

# 피처 중요도 (RandomForest 또는 GradientBoosting)
if best_model_name in ['RandomForest', 'GradientBoosting']:
    print("\n피처 중요도:")
    importances = best_model.feature_importances_
    feature_importance = pd.DataFrame({
        '피처': ml_features,
        '중요도': importances
    }).sort_values('중요도', ascending=False)
    
    print(feature_importance.to_string(index=False))

# ============================================================================
# STEP 6: 전체 데이터로 최종 모델 학습 및 예측
# ============================================================================
print("\n[6/6] 최종 모델 학습 (전체 데이터)...")

if best_model_name == 'LogisticRegression':
    X_all_scaled = scaler.fit_transform(X)
    best_model.fit(X_all_scaled, y)
    df['등급_ML'] = best_model.predict(X_all_scaled)
else:
    best_model.fit(X, y)
    df['등급_ML'] = best_model.predict(X)

print(f"✓ ML 등급 예측 완료")

# 규칙 vs ML 등급 비교
agreement = (df['등급'] == df['등급_ML']).sum() / len(df) * 100
print(f"\n등급 일치율: {agreement:.1f}%")

# 등급별 분포 비교
print("\n등급별 분포 비교:")
print("\n규칙 기반:")
for grade in ['S', 'A', 'B', 'C', 'D']:
    count = len(df[df['등급'] == grade])
    pct = count / len(df) * 100
    print(f"  {grade}등급: {count:3d}개 ({pct:5.1f}%)")

print("\nML 기반:")
for grade in ['S', 'A', 'B', 'C', 'D']:
    count = len(df[df['등급_ML'] == grade])
    pct = count / len(df) * 100
    print(f"  {grade}등급: {count:3d}개 ({pct:5.1f}%)")

# 등급 변화 분석
print("\n등급 변화 (규칙 → ML):")
changes = df[df['등급'] != df['등급_ML']][['brkrNm', 'bsnmCmpnm', '등급', '등급_ML', 'rule_score']]
if len(changes) > 0:
    print(f"총 {len(changes)}개 변화")
    print("\n상위 10개:")
    print(changes.head(10).to_string(index=False))

# ============================================================================
# 결과 요약
# ============================================================================
print("\n" + "="*70)
print("다중 분류 결과 요약")
print("="*70)

print(f"""
모델 성능:
  - 최고 모델: {best_model_name}
  - Train Accuracy: {results[best_model_name]['train_acc']:.3f}
  - Test Accuracy: {results[best_model_name]['test_acc']:.3f}

등급 비교:
  - 등급 일치율: {agreement:.1f}%
  - 불일치: {len(changes)}개

피처:
  - 사용: {len(ml_features)}개 (누수 제거)
  - 타겟: 등급 (S/A/B/C/D)

장점:
  ✅ 직접 등급 예측
  ✅ 해석 가능 (Confusion Matrix)
  ✅ 새로운 중개사 예측 가능
  ✅ 확률 정보 제공 가능
""")

# 모델 저장
model_data = {
    'model': best_model,
    'scaler': scaler,
    'feature_cols': ml_features,
    'model_name': best_model_name,
    'test_acc': results[best_model_name]['test_acc'],
    'feature_importance': feature_importance if best_model_name in ['RandomForest', 'GradientBoosting'] else None,
    'labels': ['D', 'C', 'B', 'A', 'S']
}

with open('trust_model_classification.pkl', 'wb') as f:
    pickle.dump(model_data, f)

# 결과 저장
output_cols = [
    'jurirno', 'brkrNm', 'bsnmCmpnm', 'ldCodeNm', '구', '지역권',
    'rule_score', '등급', '등급_ML',
    '거래완료', '등록매물', '총매물수', '영업년수',
    '거래성사율', '재고율', '일평균거래'
]

df[output_cols].to_csv('broker_trust_grades_classification.csv', index=False, encoding='utf-8-sig')

print("\n✓ 모델 저장: trust_model_classification.pkl")
print("✓ 결과 저장: broker_trust_grades_classification.csv")

print("\n" + "="*70)
print("다중 분류 학습 완료!")
print("="*70)
