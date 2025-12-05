# 중개사 신뢰도 평가 모델 (Trust Model)


## 📂 프로젝트 구조

```
trust_model/
├── pipeline/                         # 4단계 파이프라인
│   ├── _00_load_data.py              # 1단계: 데이터 로드
│   ├── _01_create_target.py          # 2단계: 회귀 타겟 생성 (실제 데이터)
│   ├── _02_feature_engineering.py    # 3단계: 피처 생성
│   └── _05_advanced_ensemble.py      # 4단계: Stacking 앙상블 (5개 모델)
├── models/                           # 학습된 모델 저장 (자동 생성)
│   └── advanced_ensemble.pkl         # 5개 모델 + Stacking + 스케일러
├── results/                          # 최종 결과 (자동 생성)
│   └── advanced_results.csv          # 380개 중개사 신뢰도 데이터
└── run_all.py                        # 전체 파이프라인 실행 스크립트
```

---

## 🔄 파이프라인 상세 설명

### 1단계: 데이터 로드 (`_00_load_data.py`)

**목적:** 서울시 중개사 데이터 불러오기

```python
df = load_data("data/seoul_broker_clean.csv")
```

**입력 데이터:**
- 380개 중개사 정보
- 주요 컬럼: `거래완료`, `등록매물`, `총매물수`, `registDe`(등록일), `estbsEndDe`(보증보험 만료일), `ldCodeNm`(지역명) 등

---

### 2단계: 회귀 타겟 생성 (`_01_create_target.py`)

**목적:** 실제 데이터 기반의 신뢰도 점수 생성
- 모델이 예측해야 할 "정답"
- 중개사가 얼마나 신뢰할 만한지를 0~100점 사이의 점수로 표현한 것
#### 생성되는 기본 지표

| 변수명 | 계산 방법 | 의미 |
|--------|-----------|------|
| `영업일수` | 등록일 ~ 현재 | 중개사 운영 기간 | 
| `일평균거래` | 거래완료 ÷ 영업일수 | 하루 평균 거래 건수 |
| `보증보험유효` | 만료일 >= 현재 | 보증보험 유효 여부 (0 or 1) |
| `거래성사율` | 거래완료 ÷ 총매물수 | 매물 대비 실제 거래 비율 |
| `지역권평균거래` | 지역별 평균 거래 | 해당 지역의 평균 거래 건수 |

#### 회귀 타겟 계산 (연속형 점수)

```python
trust_target = (
    거래완료 × 0.4 +           # 실제로 거래를 많이 성사시켰나? (40%)
    거래성사율 × 100 × 0.3 +   # 매물 대비 실제 거래 비율이 높나? (30%)
    일평균거래 × 50 × 0.2 +    # 매일 활발하게 활동하나? (20%)
    보증보험유효 × 10 × 0.1    # 보증보험이 유효한가? (10%)
)
```

---

### 3단계: 피처 엔지니어링 (`_02_feature_engineering.py` + 추가 피처)

**목적:** 머신러닝 모델을 위한 다양한 피처 생성

#### 기본 피처 (2개)

| 피처명 | 계산 방법 | 의미 |
|--------|-----------|------|
| `등록비율` | 등록매물 ÷ 총매물수 | 활발한 매물 등록 비율 |
| `규모지수` | log(총매물수 + 1) | 중개사 규모 (로그 스케일) |

#### 지역 기반 피처 (3개)

| 피처명 | 계산 방법 | 의미 |
|--------|-----------|------|
| `지역내백분위` | 지역별 거래완료 백분위 | 지역 내 상위 몇 % (0~1) |
| `지역중개사수` | 지역별 중개사 개수 | 경쟁 강도 |
| `지역권평균거래` | 지역별 평균 거래 | 지역 평균 거래 건수 |

#### 추가 파생 피처 (6개)

| 피처명 | 계산 방법 | 의미 |
|--------|-----------|------|
| `거래효율성` | 거래완료 ÷ 등록매물 | 등록 대비 거래 효율 |
| `매물활용도` | 거래완료 ÷ 총매물수 | 전체 매물 활용도 |
| `지역경쟁력` | 거래완료 ÷ 지역중개사수 | 지역 내 경쟁력 |
| `상대적성과` | 거래완료 ÷ 지역평균 | 지역 평균 대비 성과 |
| `log_거래완료` | log(거래완료 + 1) | 이상치 완화 |
| `log_총매물수` | log(총매물수 + 1) | 이상치 완화 |

**총 16개 피처 사용** (10개 → 16개로 확장)

---

### 4단계: Stacking 앙상블 학습 (`_05_advanced_ensemble.py`)

**목적:** 5개의 독립적인 ML 모델을 Stacking 방식으로 앙상블 (Accuracy 80% 이상 달성)

#### 앙상블 구성

**5개의 Base 모델 (성능 최적화):**

1. **RandomForest** (비선형 패턴)
```python
RandomForestRegressor(
    n_estimators=200,        # 트리 200개
    max_depth=12,            # 깊이 12
    min_samples_split=5,
    min_samples_leaf=2
)
```
- Test R²: 0.881
- 비선형 관계 포착

2. **GradientBoosting** (순차 학습)
```python
GradientBoostingRegressor(
    n_estimators=200,        # 트리 200개
    max_depth=6,             # 깊이 6
    learning_rate=0.1
)
```
- Test R²: 0.980
- 복잡한 패턴 학습

3. **ExtraTrees** (랜덤 분할)
```python
ExtraTreesRegressor(
    n_estimators=200,
    max_depth=12
)
```
- Test R²: 0.916
- 다양성 확보

4. **Ridge** (L2 정규화)
```python
Ridge(alpha=0.5)
```
- Test R²: 0.996
- 선형 관계 + 정규화

5. **Lasso** (L1 정규화)
```python
Lasso(alpha=0.5)
```
- Test R²: 0.996
- 피처 선택 효과

#### Stacking Ensemble

```python
StackingRegressor(
    estimators=[rf, gb, et, ridge, lasso],
    final_estimator=Ridge(alpha=1.0),
    cv=5
)
```

**Stacking 방식:**
- 5개 Base 모델이 각자 예측
- Meta 모델(Ridge)이 Base 모델들의 예측을 학습
- 최적의 조합 자동 발견
- **Test R²: 0.994**

#### 사용 피처 (16개)

**원본 데이터 (5개):**
- `거래완료`, `등록매물`, `총매물수`, `영업일수`, `보증보험유효`

**기본 파생 (2개):**
- `등록비율`, `규모지수`

**지역 피처 (3개):**
- `지역내백분위`, `지역중개사수`, `지역권평균거래`

**추가 파생 (6개):**
- `거래효율성`, `매물활용도`, `지역경쟁력`, `상대적성과`
- `log_거래완료`, `log_총매물수`

#### 데이터 전처리

```python
# RobustScaler 사용 (이상치에 강함)
scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train)
```

**Train/Test Split:**
- 80% 학습 (304개) / 20% 테스트 (76개)
- Stratified 방식 (각 등급 비율 유지)

#### 출력 결과

| 컬럼명 | 설명 |
|--------|------|
| `ensemble_pred` | 앙상블이 예측한 등급 (D, C, B, A, S) |
| `ensemble_score` | S등급일 확률 (0~1) |
| `final_temperature` | 최종 신뢰도 온도 (= ensemble_score) |
| `final_grade` | 최종 등급 (온도 기반 Quantile 분류) |

#### 앙상블 성능

**개별 모델 성능 (Test Set):**
```
모델                  | Test R²  | Train R²  | 과적합 차이
─────────────────────────────────────────────────────────
RandomForest        | 0.881    | 0.885     | 0.004 ✅
GradientBoosting    | 0.980    | 1.000     | 0.020 ✅
ExtraTrees          | 0.916    | 0.930     | 0.014 ✅
Ridge               | 0.996    | 0.999     | 0.004 ✅
Lasso               | 0.996    | 0.999     | 0.004 ✅
─────────────────────────────────────────────────────────
Stacking Ensemble   | 0.994    | 0.999     | 0.005 ✅
```

**등급 정확도:**
```
Train Accuracy: 78.62%
Test Accuracy:  81.58%
과적합 차이:     -2.96%
```

**등급별 성능 (Test Set):**
```
등급  | Precision | Recall | F1-score
─────────────────────────────────────
S     | 1.00      | 1.00   | 1.00    
A     | 0.81      | 1.00   | 0.90     
D     | 0.73      | 0.85   | 0.79     
C     | 0.72      | 0.68   | 0.70     
B     | 0.83      | 0.62   | 0.71     
```

**교차 검증 (5-Fold CV):**
```
RandomForest         | R² CV: 0.859 (±0.140)
GradientBoosting     | R² CV: 0.765 (±0.235)
ExtraTrees           | R² CV: 0.850 (±0.101)
Ridge                | R² CV: 0.995 (±0.002)
Lasso                | R² CV: 0.995 (±0.002)
```

**Stacking 효과:**
- 개별 모델보다 높은 성능
- 과적합 거의 없음 (0.5%)
- 상관계수 0.999 (거의 완벽)
- MAE 371.19 (매우 낮음)

**저장되는 파일:**
- `models/advanced_ensemble.pkl`: 5개 모델 + Stacking + 스케일러 + 메타데이터

#### 최종 등급 분류

```python
final_grade = pd.qcut(final_temperature, q=5, labels=["D", "C", "B", "A", "S"])
```

- Quantile 방식으로 각 등급 20%씩 균등 분포

---

## 🚀 실행 방법

### 전체 파이프라인 실행

```bash
cd apps/reco/models/trust_model
py run_all.py
```

**실행 순서:**
1. 데이터 로드
2. 회귀 타겟 생성 (실제 데이터)
3. 피처 생성 (16개)
4. Stacking 앙상블 학습 (5개 모델)
5. 결과 저장 (`results/advanced_results.csv`)

**성능:**
- Test Accuracy: 81.58%
- Test R²: 0.994
- 상관계수: 0.999

### 개별 단계 실행 (디버깅용)

```bash
py pipeline/_00_load_data.py
py pipeline/_01_create_target.py
python pipeline/_02_feature_engineering.py
python pipeline/_05_advanced_ensemble.py
```

---

## 📊 최종 결과물

### 생성되는 파일

1. **`results/advanced_results.csv`**
   - 380개 중개사의 최종 신뢰도 데이터
   - 원본 컬럼 + 16개 피처 + Stacking 결과 포함

2. **`models/advanced_ensemble.pkl`**
   - 5개 Base 모델 (RandomForest, GradientBoosting, ExtraTrees, Ridge, Lasso)
   - StackingRegressor + Meta Model (Ridge)
   - RobustScaler
   - 피처 리스트 (16개)
   - 메타데이터 (R², Accuracy, MAE 등)

### 최종 데이터 컬럼 구조

| 컬럼 그룹 | 주요 컬럼 |
|-----------|-----------|
| **원본 데이터** | `거래완료`, `등록매물`, `총매물수`, `ldCodeNm` 등 |
| **회귀 타겟** | `trust_target` (연속형 점수) - 실제 데이터 조합 |
| **기본 피처** | `등록비율`, `규모지수`, `지역내백분위` 등 |
| **추가 피처** | `거래효율성`, `매물활용도`, `지역경쟁력`, `상대적성과` 등 |
| **예측 결과** | `predicted_score` (예측 점수), `actual_grade` (실제 등급) |
| **최종 결과** | `final_temperature` (0~1), `final_grade` (D~S) |

---

## 🎯 모델 설계 철학

### 1. 진짜 ML (Real Machine Learning)

**실제 데이터 기반:**
- 규칙이 아닌 실제 데이터 조합 (거래 + 성사율 + 활동성 + 안전성)
- 연속형 타겟 (0 ~ 173631)
- ML이 데이터에서 패턴 발견 ✅

**회귀 문제:**
- 분류가 아닌 회귀로 접근
- 더 세밀한 점수 예측
- 등급 경계 문제 해결

### 2. Stacking 앙상블

**5개의 독립적인 모델:**
- RandomForest: 비선형 패턴
- GradientBoosting: 순차 학습
- ExtraTrees: 랜덤 분할
- Ridge: L2 정규화
- Lasso: L1 정규화

**Meta Model:**
- Ridge가 Base 모델들의 예측을 학습
- 최적의 조합 자동 발견
- 개별 모델보다 높은 성능

### 3. 피처 엔지니어링

**16개 피처 사용:**
- 원본 데이터 (5개)
- 기본 파생 (2개)
- 지역 피처 (3개)
- 추가 파생 (6개) ⭐ 성능 향상의 핵심!

**추가 피처의 효과:**
- 거래효율성, 매물활용도, 지역경쟁력, 상대적성과
- 로그 변환으로 이상치 완화
- Accuracy 72% → 81% (+9%)

### 4. 성능 최적화

**모델 복잡도 증가:**
- 트리 수: 100 → 200
- 깊이: 10 → 12 (RF), 5 → 6 (GB)
- 더 많은 패턴 학습

**과적합 방지:**
- 교차 검증 (5-Fold CV)
- 정규화 (Ridge, Lasso)
- 과적합 0.5% 달성 ✅
---

## 📈 모델 성능 요약

### 최종 성능 (Stacking Ensemble)

```
✅ Test Accuracy: 81.58% (목표 80% 달성!)
✅ Test R²: 0.994 
✅ 상관계수: 0.999 
✅ MAE: 371.19 
✅ RMSE: 1630.08
✅ 과적합: 0.5% 
```

### 개별 모델 성능 (Test Set)

| 모델 | Test R² | Train R² | 과적합 차이 |
|------|---------|----------|-------------|
| RandomForest | 0.881 | 0.885 | 0.004 ✅ |
| GradientBoosting | 0.980 | 1.000 | 0.020 ✅ |
| ExtraTrees | 0.916 | 0.930 | 0.014 ✅ |
| Ridge | 0.996 | 0.999 | 0.004 ✅ |
| Lasso | 0.996 | 0.999 | 0.004 ✅ |
| **Stacking** | **0.994** | **0.999** | **0.005** ✅ |

### 등급별 성능 (Test Set)

| 등급 | Precision | Recall | F1-score |
|------|-----------|--------|----------|
| S | 1.00 | 1.00 | 1.00 |  
| A | 0.81 | 1.00 | 0.90 | 
| D | 0.73 | 0.85 | 0.79 | 
| C | 0.72 | 0.68 | 0.70 | 
| B | 0.83 | 0.62 | 0.71 | 
| **평균** | **0.82** | **0.82** | **0.82** | ⭐ 우수! |

### 성능 향상 과정

| 버전 | Accuracy | R² | 주요 변경 |
|------|----------|-----|-----------|
| 1차 | 63.16% | 0.746 | 기본 회귀 |
| 2차 | 72.37% | 0.899 | 피처 추가 (거래완료) |
| **3차** | **81.58%** | **0.994** | **Stacking + 추가 피처** ⭐ |

**총 향상: +18.42%** 🚀

---

## 🔧 의존성

```bash
pip install pandas numpy scikit-learn scipy
```

---

## 💡 사용 예시

### 신규 중개사 신뢰도 예측

```python
import pickle
import pandas as pd

# 앙상블 모델 로드
with open("models/ensemble_model.pkl", "rb") as f:
    package = pickle.load(f)

ensemble = package['ensemble']
scaler = package['scaler']
features = package['features']

# 신규 데이터 준비 (10개 피처 필요)
new_data = pd.DataFrame({
    '거래완료': [15],
    '등록매물': [30],
    '총매물수': [50],
    '영업일수': [365],
    '보증보험유효': [1],
    '등록비율': [0.6],
    '규모지수': [3.93],
    '지역권평균성사율': [0.25],
    '지역내백분위': [0.7],
    '지역중개사수': [25]
})

# 예측
X_scaled = scaler.transform(new_data[features])
pred_grade = ensemble.predict(X_scaled)[0]
pred_proba = ensemble.predict_proba(X_scaled)[0]

print(f"예측 등급: {pred_grade}")
print(f"S등급 확률: {pred_proba[-1]:.2%}")
```


## 📝 버전 히스토리

| 버전 | Accuracy | R² | 방식 | 상태 |
|------|----------|-----|------|------|
| v1.0 | 63.16% | 0.746 | 기본 회귀 | ~~삭제됨~~ |
| v2.0 | 72.37% | 0.899 | 피처 추가 (거래완료) | ~~삭제됨~~ |
| **v3.0** | **81.58%** | **0.994** | **Stacking + 추가 피처** | **현재 버전** ✅ |

**총 성능 향상: +18.42%** 🚀

---

## 🗑️ 정리된 구버전 파일

### 삭제된 Pipeline 파일
- ~~`_01_rule_score.py`~~ (규칙 기반 라벨링)
- ~~`_05_classification_model.py`~~ (단일 분류 모델)
- ~~`_05_ensemble_models.py`~~ (Voting 앙상블)

### 삭제된 실행 파일
- ~~`run_all.py`~~ (구버전)

### 삭제된 모델 파일
- ~~`ensemble_model.pkl`~~ (Voting 앙상블)
- ~~`trust_model.pkl`~~ (단일 모델)
- ~~`regression_ensemble.pkl`~~ (중간 버전)

### 삭제된 기타 파일
- ~~`analyze_shap_simple.py`~~ (분석용)
- ~~`model.py`~~ (미사용)

**결과: 깔끔한 구조, 최고 성능, 유지보수 용이** ✅

---
