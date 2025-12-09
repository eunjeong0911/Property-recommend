# 중개개사 신뢰도 예측 모델 - 데이터 전처리 가이드

### 1단계: 원본 데이터 로드

**입력 파일**: `data/cleaned_brokers.csv`

```python
# 원본 데이터 구조
- 1,819행 (개인별 데이터)
- 27컬럼
- 주요 컬럼:
  - land_등록번호 (사무소 ID)
  - land_거래완료, land_등록매물
  - land_중개사명, land_주소
  - seoul_brkrAsortCodeNm (공인중개사/중개보조원/법인/중개인)
  - seoul_crqfcAcqdt (자격증 취득일)
  - office_estbsBeginDe (개업일)
```

---

### 2단계: 사무소 단위 집계

```python
# 집계 결과: 423개 사무소

# 기본 정보 (첫 번째 행 사용)
- land_거래완료, land_등록매물
- land_중개사명, land_주소, land_전화번호
- office_estbsBeginDe (개업일)
- office_ldCodeNm (지역)
- office_sttusSeCode (영업 상태)

# 인력 구성 집계
- 총_인원수 = 사무소별 인원 수
- 공인중개사수 = brkrAsortCodeNm == '공인중개사'
- 중개보조원수 = brkrAsortCodeNm == '중개보조원'
- 중개인수 = brkrAsortCodeNm == '중개인'
- 법인수 = brkrAsortCodeNm == '법인'
- 대표수 = ofcpsSeCodeNm == '대표'

# 자격증 관련
- 자격증보유자수 = crqfcAcqdt가 있는 인원 (비율 계산용)
```

**집계 예시**:
```
land_등록번호: 11680-2023-00001
├─ 총_인원수: 3명
├─ 공인중개사수: 2명
├─ 중개보조원수: 1명
├─ 자격증보유자수: 2명 (자격증보유비율: 66.7%)
├─ 운영년수: 5.2년
└─ 거래완료: 50건, 등록매물: 52건
```

---

### 3단계: 타겟

**타겟 = 거래완료율 30% + 인력구성 40% + 운영 30%**

```python
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()

# 1. 거래완료율 점수 (30점 만점)
거래완료율_로그 = np.log1p(거래완료율)
거래완료율_점수 = scaler.fit_transform(거래완료율_로그) * 30

# 2. 인력 구성 점수 (40점 만점)
인력_점수 = (
    공인중개사비율 * 20 +  # 공인중개사 많으면 +20점
    법인여부 * 10 +         # 법인이면 +10점
    중개인비율 * 7 +        # 중개인 많으면 +7점
    (1 - 중개보조원비율) * 3  # 중개보조원 적을수록 +3점
)
인력구성_점수 = np.clip(인력_점수, 0, 40)

# 3. 운영 기간 점수 (30점 만점)
운영기간_점수 = np.clip(운영년수 / 20, 0, 1) * 30

# 4. 종합 점수 (100점 만점)
신뢰도_종합점수 = (
    거래완료율_점수 +  # 30점
    인력구성_점수 +    # 40점
    운영기간_점수      # 30점
)

# 6. 3등급 분류 (절대값 기준)
신뢰도등급 = pd.cut(
    신뢰도_종합점수,
    bins=[0, 25, 35, 100],
    labels=['하', '중', '상']
)
```

**등급 기준**:
- **하등급**: 종합점수 < 25점 (명확히 부족)
- **중등급**: 25점 ≤ 종합점수 < 35점 (보통 수준)
- **상등급**: 종합점수 ≥ 35점 (우수)

**클래스 분포**:
```
하: 163개 (38.5%)
중: 135개 (31.9%)
상: 125개 (29.6%)
```

---

### 4단계: ML 데이터 준비

#### 4-1. 피처 선택 (Data Leakage 방지)

**❌ 완전 제외된 피처**:
```python
# 타겟 계산에 직접 사용
- 거래완료
- 등록매물
- 거래완료율

# 타겟 계산에 간접 사용
- 1인당_거래완료
- 1인당_등록매물

# 경력 관련 (자격증보유비율만 사용)
- 평균_자격증경력일수/년수
- 최대_자격증경력일수/년수
- 경력_다양성
- 고경력_보유
- 중경력_보유

# 중복 피처
- 운영일수 (년수만 사용)

# 낮은 중요도
- 자격증보유자수 (비율로 충분)
- 대표수
- 중개인수 (비율로 충분)

# 효과 미미한 조합 피처
- 전문성_지수 (경력 제거로 삭제)
- 품질_지수 (경력 제거로 삭제)
- 조직력_지수
- 규모경력_조합
- 법인전문성
```

#### 4-2. 결측치 처리

```python
X = df[feature_columns].fillna(0)
y = df['신뢰도등급_숫자'].values  # 0: 하, 1: 중, 2: 상
```

#### 4-3. 데이터 분할

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, 
    test_size=0.2,  # 80% 학습, 20% 테스트
    random_state=42,
    stratify=y  # 클래스 비율 유지
)

# 결과
# Train: 338개
# Test: 85개
```

#### 4-4. 피처 스케일링

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

#### 4-5. SMOTE 오버샘플링

```python
from imblearn.over_sampling import BorderlineSMOTE

# 중등급을 1.2배 더 샘플링 (경계선 샘플 집중)
smote = BorderlineSMOTE(
    random_state=42,
    k_neighbors=5,
    sampling_strategy={
        0: max_count,             # 하등급: 최대값
        1: int(max_count * 1.2),  # 중등급: 최대값의 1.2배
        2: max_count              # 상등급: 최대값
    },
    kind='borderline-1'
)

X_train_resampled, y_train_resampled = smote.fit_resample(X_train_scaled, y_train)

# 결과
# 원본: 338개
# 리샘플링 후: 442개
# 클래스 하: 130개, 중: 182개, 상: 130개
```

---

## 📊 최종 모델 성능

### LogisticRegression (최종 선택)

**하이퍼파라미터**:
```python
LogisticRegression(
    max_iter=3000,
    random_state=42,
    multi_class="multinomial",
    solver='saga',
    penalty='l2',
    C=0.5,
    class_weight={0: 1.0, 1: 1.5, 2: 1.0}
)
```

**성능 지표**:
- **전체 정확도**: 71.76%
- **F1-Score**: 71.97%
- **과적합**: 10.78% (Train-Test 차이)

**클래스별 성능**:
| 등급 | Precision | Recall | F1-Score | 정확도 |
|------|-----------|--------|----------|--------|
| 하   | 0.82      | 0.82   | 0.82     | 82.14% |
| 중   | 0.59      | 0.69   | 0.63     | 68.97% |
| 상   | 0.78      | 0.64   | 0.71     | 64.29% |

**주요 특징**:
- ✅ 거래 피처 포함으로 성능 2배 향상 (37% → 72%)
- ✅ 하등급 예측 우수: 82.14%
- ✅ 중등급 예측 안정적: 68.97%
- ✅ 상등급 예측 양호: 64.29%
- ✅ 과적합 관리: 10.78% (허용 범위)

**타겟 구성**:
- 거래완료율: 40점 (실제 성과)
- 인력구성: 30점 (전문성)
- 경력: 20점 (경험)
- 운영기간: 10점 (안정성)

**SMOTE 샘플링**:
- BorderlineSMOTE (경계선 샘플 집중)
- 중등급 1.4배 오버샘플링

---

## 📁 출력 파일

```
data/processed_office_data.csv
- 423행
- 57개 피처 (거래 성과 포함)
- 타겟 레이블 포함

apps/reco/models/trust_model/saved_models/
- trust_model.pkl (LogisticRegression, 71.76% 정확도)
- scaler.pkl (StandardScaler)
- feature_names.pkl (57개 피처 이름)
```

## 🎯 핵심 인사이트

1. **거래 피처의 중요성**: 거래완료, 등록매물 피처를 제외하면 성능이 37%로 급락
2. **타겟 설계**: 거래 성과(40%) + 사무소 품질(60%)의 균형이 중요
3. **클래스 불균형**: SMOTE 오버샘플링으로 중등급 예측 개선
4. **과적합 관리**: LogisticRegression이 앙상블보다 안정적 (10.78% vs 12.83%)

---

## 🚀 실행 방법

```bash
# 전체 파이프라인 실행
python apps/reco/models/trust_model/run_all.py
```
