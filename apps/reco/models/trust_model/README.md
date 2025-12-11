# 중개사 신뢰도 예측 모델

- **중개사 신뢰도를 A/B/C 3등급으로 분류하는 다중분류 ML**



## 📊 원본 데이터

### 입력 데이터
```
파일: data/preprocessed_office_data.csv
- 356개 중개사무소
- 25개 컬럼 (기본 정보 + 거래 실적)
```

**주요 컬럼:**
- **거래 실적**: 거래완료, 등록매물
- **인력 구성**: 총_직원수, 공인중개사수, 중개보조원수, 대표수, 일반직원수
- **운영 정보**: 개설시작일, 지역명
- **기타**: 중개사명, 대표자, 주소, 전화번호 등

---

## 🎯 타겟 정의

### Z-Score 기반 신뢰도 등급

**1단계: 거래성사율 계산**
```python
거래성사율 = 거래완료 / (등록매물 + 거래완료)
```

**2단계: 지역별 표준화**
```python
# 지역별 평균과 표준편차 계산
지역평균 = 지역별 거래성사율 평균
지역표준편차 = 지역별 거래성사율 표준편차

# Z-score 계산 (지역 내 상대적 성과)
Z-score = (개별_거래성사율 - 지역평균) / 지역표준편차
```

**3단계: 등급 분류 (30/40/30 분포)**
```python
# 분위수 기준
C등급: Z-score ≤ 30% 분위수  (하위 30%)
B등급: 30% < Z-score ≤ 70%   (중위 40%) 
A등급: Z-score > 70% 분위수  (상위 30%)
```

### 타겟 선택 이유
1. **지역별 공정성**: 같은 지역 내에서 상대적 성과 평가
2. **거래성사율 중심**: 중개사의 역량 지표
3. **균형잡힌 분포**: 30/40/30으로 분류


## 🤖 모델 학습

### 데이터 분할
```
전체: 356개
Train: 284개 (80%)
Test: 72개 (20%)
Stratified Split (클래스 비율 유지)
```

### 전처리 최적화

**스케일러 자동 선택**
```python
# 3가지 스케일러 CV 테스트
scalers = {
    'robust': RobustScaler(),           # 이상치에 강함
    'quantile': QuantileTransformer(),  # 균등 분포 변환
    'power': PowerTransformer()         # 정규분포 변환
}
# → 최적 스케일러 자동 선택
```

### 모델 비교 (5개)

**1. LogisticRegression (하이퍼파라미터 최적화)**
```python
# 3단계 GridSearchCV
1단계: L2 정규화 (기본)
2단계: L1 정규화 (특성 선택)
3단계: ElasticNet (L1+L2 조합)

# 최적 파라미터
penalty='elasticnet', C=1, l1_ratio=0.1, solver='saga'
```

**2. RandomForest Enhanced**
```python
RandomForestClassifier(
    n_estimators=150,
    max_depth=10,
    min_samples_split=3,
    min_samples_leaf=1,
    class_weight='balanced'
)
```

**3. GradientBoosting Enhanced**
```python
GradientBoostingClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    min_samples_split=5,
    min_samples_leaf=2
)
```

**4. SVM**
```python
SVC(
    C=1.0,
    kernel='rbf',
    class_weight='balanced',
    probability=True
)
```

**5. Ensemble VotingClassifier**
```python
# 4개 모델의 소프트 투표
VotingClassifier(
    estimators=[LR, RF, GB, SVM],
    voting='soft'
)
```

---

## 📊 모델 성능

### 최종 성능 비교

| 모델 | CV Mean | Test Acc | 과적합 |
|------|---------|----------|--------|
| **LogisticRegression_Optimized** | **70.09%** | 62.50% | 0.118 |
| GradientBoosting_Enhanced | 62.32% | 61.11% | 0.361 |
| RandomForest_Enhanced | 61.28% | 62.50% | 0.269 |
| SVM | - | - | - |
| Ensemble_VotingClassifier | - | - | - |

### 최고 성능 모델: LogisticRegression_Optimized

**하이퍼파라미터:**
```python
penalty='elasticnet'     # L1+L2 조합
C=1                      # 정규화 강도
l1_ratio=0.1            # L2 위주 (90%), L1 소량 (10%)
solver='saga'           # ElasticNet 지원
max_iter=2000          # 충분한 반복
```

**성능 지표:**
- **CV Mean**: 73.26% (±3.96%)
- **Test Accuracy**: 69.44%
- **과적합 정도**: 6.96% (매우 낮음)

### 클래스별 성능 (Test 기준)

| 등급 | Precision | Recall | F1-Score | 샘플 수 |
|------|-----------|--------|----------|---------|
| A (상) | 0.91 | 0.91 | 0.91 | 22 |
| B (중) | 0.62 | 0.57 | 0.59 | 28 |
| C (하) | 0.58 | 0.64 | 0.61 | 22 |



## 🚀 실행 방법

### 전체 파이프라인 실행
```bash
cd apps/reco/models/trust_model
python run_all.py
```

## 📁 출력 파일

```
apps/reco/models/trust_model/save_models/
├── temp_trained_models.pkl     # 전체 모델 + 결과
└── final_trust_model.pkl       # 최고 성능 모델만

data/
├── office_target.csv           # 타겟 포함 데이터
└── office_features.csv         # Feature 포함 데이터
```

**final_trust_model.pkl 구성:**
```python
{
    'model': LogisticRegression_Optimized,
    'scaler': 최적_스케일러,
    'feature_names': 34개_Feature_이름,
    'model_name': 'LogisticRegression_Optimized'
}
```




