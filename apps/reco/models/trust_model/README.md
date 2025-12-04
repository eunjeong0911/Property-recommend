# 중개사 신뢰도 모델 - 다중 분류 버전

중개사의 신뢰도를 S/A/B/C/D 등급으로 직접 예측하는 머신러닝 분류 모델입니다.

## 개요

- **목적**: 서울시 중개사의 신뢰도를 5단계 등급(S/A/B/C/D)으로 분류
- **방식**: 규칙 기반 등급을 타겟으로 머신러닝 분류 모델 학습
- **데이터**: `seoul_broker_clean.csv` (서울시 중개사 데이터)
- **모델**: Logistic Regression, Random Forest, Gradient Boosting 비교 후 최고 성능 모델 선택

## 등급 체계

| 등급 | 백분위 | 설명 |
|------|--------|------|
| S | 상위 10% | 최우수 중개사 |
| A | 10~30% | 우수 중개사 |
| B | 30~60% | 보통 중개사 |
| C | 60~90% | 평균 이하 |
| D | 하위 10% | 개선 필요 |

## 지역권 분류

서울시 25개 구를 5개 지역권으로 분류:

- **강남권**: 강남구, 서초구, 송파구, 강동구
- **강북권**: 강북구, 노원구, 도봉구, 성북구
- **서남권**: 양천구, 강서구, 구로구, 금천구, 영등포구, 동작구, 관악구
- **동북권**: 광진구, 중랑구, 동대문구, 성동구
- **도심권**: 종로구, 중구, 용산구, 마포구, 서대문구, 은평구

## 주요 피처 (총 17개)

### 원본 데이터 (4개)
- `거래완료`: 완료된 거래 건수
- `등록매물`: 현재 등록된 매물 수
- `총매물수`: 총 매물 수
- `영업년수`: 영업 기간 (년)

### 파생 피처 (2개)
- `log_일평균거래`: 일평균 거래량 (로그 변환)
- `보증보험유효`: 보증보험 유효 여부 (0/1)

### 지역 통계 (4개)
- `지역권평균성사율`: 지역권 평균 거래 성사율
- `지역권평균매물수`: 지역권 평균 매물 수
- `구평균성사율`: 구 평균 거래 성사율
- `구평균매물수`: 구 평균 매물 수

### 지역 특성 (5개 + α)
- `지역권_강남권`, `지역권_강북권`, `지역권_서남권`, `지역권_동북권`, `지역권_도심권`: 지역권 원핫 인코딩 (0/1)

## 모델 학습 과정

### STEP 1: 규칙 기반 등급 생성 (타겟 y)
종합 점수를 계산하여 백분위 기반으로 등급 부여:

```python
rule_score = (
    거래성사율 * 0.30 +
    (100 - 재고율) * 0.20 +
    지역권대비성과 * 10 +
    구대비성과 * 10 +
    log_일평균거래 * 5 +
    보증보험유효 * 5 +
    성장잠재력 * 0.05 +
    지역권내_성과순위 * 5 +
    구내_성과순위 * 5
)
```

**등급 생성 방식:**
- rule_score를 백분위로 변환
- 백분위 구간에 따라 등급 부여 (D: 0-10%, C: 10-30%, B: 30-60%, A: 60-90%, S: 90-100%)

### STEP 2: 피처 선택 (누수 피처 제거)
- **누수(leakage) 피처 제거**: 타겟과 직접 연관된 피처 제외
- **지역권 원핫 인코딩**: 5개 지역권을 0/1로 변환
- **총 17개 피처 사용**: 원본(4) + 파생(2) + 지역통계(4) + 지역특성(5+)

### STEP 3: Train/Test 분리
- **분리 비율**: 80% Train / 20% Test
- **Stratified Split**: 등급별 비율 유지
- **스케일링**: RobustScaler 사용 (이상치에 강함)

### STEP 4: 모델 학습 및 비교
3가지 분류 모델 학습 및 성능 비교:

1. **Logistic Regression**
   - 다중 분류 (multinomial)
   - 스케일링된 데이터 사용
   
2. **Random Forest**
   - 100개 트리, 최대 깊이 10
   - 병렬 처리 (n_jobs=-1)
   
3. **Gradient Boosting**
   - 100개 트리, 최대 깊이 5
   - 순차적 학습

**최고 성능 모델 자동 선택**: Test Accuracy 기준

### STEP 5: 상세 평가
- **Classification Report**: Precision, Recall, F1-Score (등급별)
- **Confusion Matrix**: 실제 vs 예측 등급 비교
- **피처 중요도**: Random Forest/Gradient Boosting의 경우

### STEP 6: 전체 데이터로 최종 학습
- 최고 성능 모델로 전체 데이터 재학습
- 모든 중개사에 대해 ML 등급 예측
- 규칙 기반 등급 vs ML 등급 비교

## 실행 방법

### 1. 필요한 라이브러리 설치
```bash
pip install pandas numpy scikit-learn seaborn matplotlib
```

### 2. 모델 학습 실행
```bash
cd apps/reco/models/trust_model
python trust_model_classification.py
```

### 3. 실행 결과
```
======================================================================
중개사 신뢰도 모델 - 다중 분류 버전
======================================================================

데이터: XXXX개 중개사

[1/6] 규칙 기반 등급 생성 (타겟 y)...
✓ 등급 생성 완료

등급별 분포:
  S등급: XXX개 (10.0%)
  A등급: XXX개 (20.0%)
  B등급: XXX개 (30.0%)
  C등급: XXX개 (30.0%)
  D등급: XXX개 (10.0%)

[2/6] 피처 선택 (누수 피처 제거)...
✅ ML 피처: 17개
✅ 타겟: 등급 (S/A/B/C/D)

[3/6] Train/Test 분리...
Train: XXXX개 (80%)
Test: XXXX개 (20%)

[4/6] 모델 학습 및 비교...
LogisticRegression 학습 중...
  Train Accuracy: X.XXX
  Test Accuracy: X.XXX

RandomForest 학습 중...
  Train Accuracy: X.XXX
  Test Accuracy: X.XXX

GradientBoosting 학습 중...
  Train Accuracy: X.XXX
  Test Accuracy: X.XXX

✅ 최고 모델: RandomForest (예시)
  Test Accuracy: X.XXX

[5/6] 상세 평가...
Classification Report:
...

[6/6] 최종 모델 학습 (전체 데이터)...
✓ ML 등급 예측 완료

등급 일치율: XX.X%
```

## 출력 파일

### 1. trust_model_classification.pkl
학습된 모델 및 메타데이터:
- `model`: 최고 성능 모델 객체
- `scaler`: RobustScaler 객체
- `feature_cols`: 피처 목록 (17개)
- `model_name`: 모델 이름 (LogisticRegression/RandomForest/GradientBoosting)
- `test_acc`: Test Accuracy
- `feature_importance`: 피처 중요도 (Random Forest/Gradient Boosting만)
- `labels`: 등급 목록 ['D', 'C', 'B', 'A', 'S']

### 2. broker_trust_grades_classification.csv
중개사별 등급 결과:
- `jurirno`: 중개사 등록번호
- `brkrNm`: 중개사명
- `bsnmCmpnm`: 회사명
- `ldCodeNm`: 주소
- `구`: 구 이름
- `지역권`: 지역권 (강남권/강북권/서남권/동북권/도심권)
- `rule_score`: 규칙 기반 종합 점수
- `등급`: 규칙 기반 등급
- `등급_ML`: ML 예측 등급
- `거래완료`, `등록매물`, `총매물수`, `영업년수`: 원본 데이터
- `거래성사율`, `재고율`, `일평균거래`: 파생 피처

### 3. confusion_matrix_classification.png
Confusion Matrix 시각화 (실제 등급 vs 예측 등급)

## 모델 사용 예시

### 기본 사용법

```python
import pickle
import pandas as pd
import numpy as np
from datetime import datetime

# 1. 모델 로드
with open('trust_model_classification.pkl', 'rb') as f:
    model_data = pickle.load(f)

model = model_data['model']
scaler = model_data['scaler']
feature_cols = model_data['feature_cols']
model_name = model_data['model_name']

# 2. 새로운 중개사 데이터 준비
# 필요한 최소 정보:
# - 거래완료, 등록매물, 총매물수
# - registDe (등록일), estbsEndDe (보증보험 만료일)
# - 구 또는 지역권

# 예시: 강남구 중개사
today = pd.to_datetime(datetime.now())
registDe = pd.to_datetime('2020-01-01')
estbsEndDe = pd.to_datetime('2025-12-31')

# 기본 데이터
거래완료 = 50
등록매물 = 10
총매물수 = 100
영업일수 = (today - registDe).days
영업년수 = 영업일수 / 365
일평균거래 = 거래완료 / 영업일수
log_일평균거래 = np.log1p(일평균거래)
보증보험유효 = 1 if estbsEndDe >= today else 0

# 지역 정보 (학습 데이터의 통계값 사용)
지역권 = '강남권'
지역권평균성사율 = 45.0  # 학습 데이터에서 계산된 값
지역권평균매물수 = 80.0
구평균성사율 = 48.0
구평균매물수 = 85.0

# 지역권 원핫 인코딩
지역권_강남권 = 1 if 지역권 == '강남권' else 0
지역권_강북권 = 1 if 지역권 == '강북권' else 0
지역권_서남권 = 1 if 지역권 == '서남권' else 0
지역권_동북권 = 1 if 지역권 == '동북권' else 0
지역권_도심권 = 1 if 지역권 == '도심권' else 0

# 3. 데이터프레임 생성
new_broker = pd.DataFrame({
    '거래완료': [거래완료],
    '등록매물': [등록매물],
    '총매물수': [총매물수],
    '영업년수': [영업년수],
    'log_일평균거래': [log_일평균거래],
    '보증보험유효': [보증보험유효],
    '지역권평균성사율': [지역권평균성사율],
    '지역권평균매물수': [지역권평균매물수],
    '구평균성사율': [구평균성사율],
    '구평균매물수': [구평균매물수],
    '지역권_강남권': [지역권_강남권],
    '지역권_강북권': [지역권_강북권],
    '지역권_서남권': [지역권_서남권],
    '지역권_동북권': [지역권_동북권],
    '지역권_도심권': [지역권_도심권]
})

# 4. 예측
if model_name == 'LogisticRegression':
    X_scaled = scaler.transform(new_broker[feature_cols])
    grade = model.predict(X_scaled)[0]
    proba = model.predict_proba(X_scaled)[0]
else:
    grade = model.predict(new_broker[feature_cols])[0]
    proba = model.predict_proba(new_broker[feature_cols])[0]

# 5. 결과 출력
print(f"예측 등급: {grade}")
print(f"등급별 확률:")
for label, prob in zip(['D', 'C', 'B', 'A', 'S'], proba):
    print(f"  {label}등급: {prob:.1%}")
```

### 출력 예시
```
예측 등급: A
등급별 확률:
  D등급: 2.3%
  C등급: 8.5%
  B등급: 25.7%
  A등급: 58.2%
  S등급: 5.3%
```

## 모델 특징

### 장점
- ✅ **직접 등급 예측**: 회귀 후 변환 불필요, 바로 S/A/B/C/D 등급 출력
- ✅ **해석 가능**: Confusion Matrix, 피처 중요도로 모델 동작 이해 가능
- ✅ **새로운 중개사 예측**: 학습 데이터에 없는 중개사도 예측 가능
- ✅ **확률 정보 제공**: 각 등급별 확률로 예측 신뢰도 확인 가능
- ✅ **누수 피처 제거**: 타겟과 직접 연관된 피처 제외로 일반화 성능 향상
- ✅ **자동 모델 선택**: 3가지 모델 비교 후 최고 성능 모델 자동 선택
- ✅ **지역 특성 반영**: 지역권별 특성을 원핫 인코딩으로 반영

### 주의사항
- 새로운 중개사 예측 시 **지역 통계값**(지역권평균성사율 등)은 학습 데이터의 값을 사용해야 함
- 지역권이 '기타'인 경우 원핫 인코딩에서 모두 0으로 처리됨
- 보증보험 만료일이 과거인 경우 `보증보험유효=0`으로 처리

## 의존성

```bash
pip install pandas numpy scikit-learn seaborn matplotlib
```

또는

```bash
pip install -r requirements.txt
```

## 파일 구조

```
trust_model/
├── trust_model_classification.py          # 모델 학습 스크립트
├── trust_model_classification.pkl         # 학습된 모델 (생성됨)
├── broker_trust_grades_classification.csv # 등급 결과 (생성됨)
├── confusion_matrix_classification.png    # Confusion Matrix (생성됨)
└── README.md                              # 이 문서
```

## 참고사항

- **데이터 경로**: `../../../../data/seoul_broker_clean.csv`
- **지역권 분류**: 강남권, 강북권, 서남권, 동북권, 도심권 (총 5개)
- **등급 분포**: S(10%), A(20%), B(30%), C(30%), D(10%)
- **Train/Test 비율**: 80% / 20%
- **스케일러**: RobustScaler (이상치에 강함)
