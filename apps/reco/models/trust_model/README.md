# 중개사 신뢰도 예측 모델

**중개사 신뢰도를 A/B/C 3등급으로 분류하는 다중분류 ML 모델**


## 📊 데이터 전처리

### 원본 데이터 소스
```
파일: data/brokerInfo/grouped_offices.csv
- 중개사무소 정보 (병합된 데이터[매물데이터의 중개소 정보 + vworld 중개소 정보 + vworld 중개사 정보])
```

**주요 컬럼:**
- **거래 실적**: 거래완료, 등록매물
- **인력 구성**: 공인중개사수, 중개보조원수, 일반직원수, 대표
- **운영 정보**: 등록일, 지역명
- **기타**: 중개사명, 대표자, 주소, 전화번호 등

---

## 🎯 타겟 정의 (Z-Score 기반 신뢰도 등급)

**Target - 지역별 표준화**
```python
# 지역별 평균과 표준편차 계산
지역평균 = 지역별 거래성사율 평균
지역표준편차 = 지역별 거래성사율 표준편차

# Z-score 계산 (지역 내 상대적 성과)
Z-score = (개별 거래성사율 - 지역평균) / 지역표준편차
```


**Target - 등급 분류 (30/40/30 분포)**  
 - C등급: 109개 (30.6%)
 - B등급: 140개 (39.3%)
 - A등급: 107개 (30.1%)   
```python
# 분위수 기준
C등급: Z-score ≤ 30% 분위수  (하위 30%)
B등급: 30% < Z-score ≤ 70%   (중위 40%) 
A등급: Z-score > 70% 분위수  (상위 30%)
```

---

## 🤖 모델 학습 파이프라인

### 데이터 분할
```
Train: 80% (Stratified)
Test: 20% (Stratified)
클래스 비율 유지
```

### 전처리 최적화

**스케일러 자동 선택**
```python
# 3가지 스케일러 테스트
scalers = {
    'robust': RobustScaler(),                    # 중앙값과 IQR 사용 (이상치에 강함)
    'quantile': QuantileTransformer(),           # 균등 분포 변환 (분위수 기반으로 균등분포 변환)
    'power': PowerTransformer()                  # 정규분포 변환 (비대칭 분포를 대칭으로)
}
```

### 학습 모델

**현재 활성화: LogisticRegression (GridSearchCV 최적화)**

```python
LogisticRegression(
    C=1,
    penalty='l2',
    solver='lbfgs',
    max_iter=1000,
    class_weight=None,
    random_state=42
)
```

---

## 📊 모델 성능

### 평가 지표

**Cross Validation (5-Fold Stratified)**
- CV Mean Accuracy
- CV Standard Deviation

**Train/Test 성능**
- Train Accuracy
- Test Accuracy
- 과적합 정도 (Train - Test)

**클래스별 성능**
- Precision, Recall, F1-Score (A/B/C 등급별)
- Confusion Matrix
---

## 🚀 실행 방법

### 전체 파이프라인 실행
```bash
cd apps/reco/models/trust_model
python run_all.py
```

---

## 📁 파일 구조 및 출력

### 디렉토리 구조
```
trust_model/
├── data_preprocessing/          # 원본 데이터 전처리 스크립트
│   ├── _00_load_Landbroker.py
│   ├── _01_load_broker.py
│   ├── _02_load_brokerOffice.py
│   ├── _03_merge_all_brokers.py
│   ├── _04_clean_broker.py
│   └── _05_group_by_office.py
│
├── pipeline/                    # ML 파이프라인
│   ├── _00_load_data.py        # 데이터 로드
│   ├── _01_create_target.py    # 타겟 생성
│   ├── _02_create_features.py  # Feature 생성
│   ├── _03_train.py            # 모델 학습
│   ├── _04_eval.py             # 모델 평가
│   └── _05_save_model.py       # 최종 모델 저장
│
├── save_models/                 # 저장된 모델
│   ├── temp_trained_models.pkl
│   └── final_trust_model.pkl
│
├── results/                     # 평가 결과 (선택사항)
│
├── run_all.py                   # 전체 파이프라인 실행
├── analyze_shap.py              # SHAP 분석
└── README.md
```

### 출력 파일

**1. 중간 데이터**
```
data/ML/
├── preprocessed_office_data.csv    # 전처리된 원본 데이터
├── office_target.csv               # 타겟 포함 데이터
└── office_features.csv             # Feature 포함 데이터
```

**2. 학습된 모델**
```
apps/reco/models/trust_model/save_models/
├── temp_trained_models.pkl         # 전체 학습 결과
└── final_trust_model.pkl           # 최종 선택 모델
```

**temp_trained_models.pkl 구성:**
```python
{
    'models': {모델명: 학습된_모델},
    'scaler': 최적_스케일러,
    'X_train_scaled': 스케일된_훈련_데이터,
    'y_train': 훈련_타겟,
    'X_test_scaled': 스케일된_테스트_데이터,
    'y_test': 테스트_타겟,
    'feature_names': Feature_이름_리스트,
    'cv_results': CV_평가_결과,
    'optimization_info': 하이퍼파라미터_최적화_정보
}
```

**final_trust_model.pkl 구성:**
```python
{
    'model': 최고_성능_모델,
    'scaler': 최적_스케일러,
    'feature_names': Feature_이름_리스트,
    'model_name': 모델명
}
```


