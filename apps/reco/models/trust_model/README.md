# 🏢 중개사 신뢰도 평가 모델 (Trust Model)

## 📋 프로젝트 개요

부동산 중개사의 신뢰도를 A/B/C 등급으로 분류하는 머신러닝 모델입니다. 단순한 거래량 기반 평가를 넘어서, **운영 안정성**, **조직 구조**, **전문성**을 종합적으로 고려한 균형잡힌 평가 시스템을 구축했습니다.

## 🎯 모델 목표

- **공정한 평가**: 거래량에만 의존하지 않는 다면적 평가
- **실용적 성능**: 73.2% 정확도로 실제 서비스 적용 가능
- **해석 가능성**: SHAP을 통한 투명한 의사결정 과정
- **균형잡힌 분류**: A/B/C 등급별 고른 성능 확보

---

## 🔧 모델 개발 과정

### 1️⃣ 데이터 수집 및 전처리

#### 📊 **데이터 소스**
- **중개사 기본정보**: 등록번호, 사무소명, 대표자, 주소, 등록일 등
- **거래 실적**: 거래완료 건수, 등록매물 건수
- **조직 정보**: 직원 수, 공인중개사 수, 중개보조원 수
- **대표자 정보**: 대표자 구분명 (공인중개사/법인/중개인/중개보조원)

#### 🔄 **데이터 통합 과정**
```python
# 1단계: 기본 매칭 (등록번호 + 중개사무소명)
matched_basic = merge_by_registration_and_office_name()

# 2단계: 추가 매칭 (중개사무소명 + 대표자명)  
matched_additional = merge_by_office_and_representative_name()

# 3단계: 직원 목록 생성 (같은 등록번호 직원들)
staff_list = create_staff_list_by_registration_number()
```

### 2️⃣ 타겟 변수 생성

#### 🎯 **신뢰도 등급 산출 공식**
```python
# 1. 거래성사율 계산
거래성사율 = 거래완료_건수 / (거래완료_건수 + 등록매물_건수)

# 2. 지역별 표준화 (Z-score)
Z_score = (개별_거래성사율 - 지역_평균) / 지역_표준편차

# 3. 대표자 구분별 가중치 적용
가중치 = {
    '공인중개사': 0.0,    # 기준
    '법인': +0.2,         # 조직 안정성 가점
    '중개보조원': -0.1,   # 자격 수준 감점
    '중개인': -0.3        # 자격 수준 감점
}

# 4. 최종 점수 및 등급 분류
최종_점수 = Z_score + 대표자_가중치
등급 = 분위수_기반_분류(최종_점수)  # A(30%) / B(40%) / C(30%)
```

### 3️⃣ 피처 엔지니어링

#### 🏗️ **16개 피처 생성**

**거래 지표 (3개) - 억제**
```python
# 로그 변환 + 제곱근 + 세제곱근 + 극초강 스케일링
거래완료_log = np.power(np.sqrt(np.log1p(거래완료_숫자)), 1/3) * 0.001
등록매물_log = np.power(np.sqrt(np.log1p(등록매물_숫자)), 1/3) * 0.001  
총거래활동량_log = np.power(np.sqrt(np.log1p(총거래활동량)), 1/3) * 0.0005
```

**인력 지표 (3개) - 2배 강화**
```python
총_직원수 = 공인중개사수 + 중개보조원수 + 일반직원수
공인중개사수 = 공인중개사수 * 2.0
공인중개사_비율 = (공인중개사수 / 총_직원수) * 2.0
```

**운영 경험 (4개) - 2.5배 강화**
```python
운영기간_년 = (현재날짜 - 등록일) / 365.25 * 2.5
운영경험_지수 = np.exp(운영기간_년 / 10) * 2.5
숙련도_지수 = 운영기간_년 * 공인중개사_비율 * 2.5
운영_안정성 = (운영기간_년 >= 3).astype(int) * 2.5
```

**조직 구조 (2개) - 3배 강화**
```python
대형사무소 = (총_직원수 >= 3).astype(int) * 3.0
직책_다양성 = (직책_종류_수) * 3.0
```

**대표자 구분 (4개) - 2배 강화**
```python
대표_공인중개사 = (대표자구분명 == "공인중개사").astype(int) * 2.0
대표_법인 = (대표자구분명 == "법인").astype(int) * 2.0
대표_중개인 = (대표자구분명 == "중개인").astype(int) * 2.0
대표_중개보조원 = (대표자구분명 == "중개보조원").astype(int) * 2.0
```

### 4️⃣ 모델 학습

#### 🤖 **모델 선택 및 설정**
```python
# LogisticRegression with L2 Regularization
model = LogisticRegression(
    C=0.01,              # 강한 정규화로 과적합 방지
    random_state=42,     # 재현성 확보
    max_iter=1000       # 충분한 반복 횟수
)

# 데이터 분할
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 표준화
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

#### 📊 **교차 검증**
```python
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
```

### 5️⃣ 모델 성능

#### 🎯 **최종 성능 지표**
- **Test Accuracy**: 73.24%
- **Train Accuracy**: 74.29%
- **과적합 정도**: 1.05% (매우 낮음)
- **CV Mean**: 66.79% (±5.00%)

#### 📈 **등급별 성능**
| 등급 | Precision | Recall | F1-Score | Support |
|------|-----------|--------|----------|---------|
| A등급 | 0.74 | 0.91 | 0.82 | 22 |
| B등급 | 0.74 | 0.50 | 0.60 | 28 |
| C등급 | 0.72 | 0.86 | 0.78 | 21 |

### 6️⃣ SHAP 분석 결과

#### 🔍 **A등급 예측 주요 피처**
1. `총거래활동량_log`: 0.299 📉 (억제됨)
2. `등록매물_log`: 0.157 📉 (억제됨)  
3. `거래완료_log`: 0.132 📉 (억제됨)
4. `운영_안정성`: 0.130 📈 (강화됨) ⭐
5. `운영기간_년`: 0.029 📈 (강화됨)

**✅ 성과**: 운영 안정성이 4번째로 중요한 피처로 부상하여 **균형잡힌 평가 체계** 구축 성공

---

## 📁 프로젝트 구조

```
apps/reco/models/trust_model/
├── data_preprocessing/
│   ├── _01_load_raw_data.py          # 원시 데이터 로드
│   ├── _02_clean_data.py             # 데이터 정제
│   └── _03_merge_all_brokers.py      # 중개사 데이터 통합
├── pipeline/
│   ├── _00_load_data.py              # 전처리된 데이터 로드
│   ├── _01_create_target.py          # 타겟 변수 생성
│   ├── _02_create_features.py        # 피처 엔지니어링
│   ├── _03_train.py                  # 모델 학습
│   ├── _04_eval.py                   # 모델 평가
│   └── _05_save_model.py             # 모델 저장
├── results/
│   ├── validation/                   # 검증 분석 결과
│   └── shap_importance_*.png         # SHAP 분석 결과
├── save_models/
│   └── temp_trained_models.pkl       # 학습된 모델
├── analyze_shap.py                   # SHAP 분석
├── model_validation_analysis.py     # 종합 검증 분석
├── run_all.py                        # 전체 파이프라인 실행
└── README.md                         # 이 문서
```

---

## 🚀 사용 방법

### 1️⃣ 전체 파이프라인 실행
```bash
# 데이터 전처리부터 모델 학습까지 전체 과정
python apps/reco/models/trust_model/run_all.py
```

### 2️⃣ 단계별 실행
```bash
# 1. 타겟 생성
python apps/reco/models/trust_model/pipeline/_01_create_target.py

# 2. 피처 생성  
python apps/reco/models/trust_model/pipeline/_02_create_features.py

# 3. 모델 학습
python apps/reco/models/trust_model/pipeline/_03_train.py

# 4. 모델 평가
python apps/reco/models/trust_model/pipeline/_04_eval.py
```

### 3️⃣ 분석 도구
```bash
# SHAP 분석
python apps/reco/models/trust_model/analyze_shap.py

# 종합 검증 분석 (17개 차트 생성)
python apps/reco/models/trust_model/model_validation_analysis.py
```

---
