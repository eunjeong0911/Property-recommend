# Trust Model Pipeline

중개사 신뢰도 평가 모델 파이프라인입니다. 룰 기반 스코어링과 RandomForest 분류 모델을 결합한 앙상블 방식으로 최종 신뢰도 온도(temperature)를 산출합니다.

## 📂 디렉토리 구조

```
trust_model/
├── pipeline/
│   ├── _00_load_data.py              # 데이터 로드
│   ├── _01_rule_score.py             # 룰 기반 스코어링
│   ├── _02_feature_engineering.py    # 피처 엔지니어링
│   ├── _05_classification_model.py   # RandomForest 분류 모델 학습
│   └── _06_ensemble.py               # 앙상블 최종 온도 계산
├── models/                           # 학습된 모델 저장 (자동 생성)
├── results/                          # 최종 결과 저장 (자동 생성)
└── run_all.py                        # 전체 파이프라인 실행
```

## 🔄 파이프라인 흐름

### 1️⃣ 데이터 로드 (`_00_load_data.py`)
```python
df = load_data("data/seoul_broker_clean.csv")
```
- 서울 중개사 데이터 로드 (380개)
- 기본 데이터 shape 및 메모리 사용량 확인

### 2️⃣ 룰 기반 스코어링 (`_01_rule_score.py`)
```python
df = apply_rule_score(df)
```
**생성되는 컬럼:**
- `영업일수`: 등록일부터 현재까지 영업 기간
- `일평균거래`: 거래완료 / 영업일수
- `보증보험유효`: 보증보험 만료일 체크 (0 or 1)
- `거래성사율`: 거래완료 / 총매물수
- `지역권평균성사율`: 지역별 평균 성사율
- `rule_score`: 룰 기반 종합 점수
  - 거래성사율 × 40
  - 일평균거래 × 30
  - 보증보험유효 × 20
  - 지역권평균성사율 × 10
- `grade`: **rule_score 기반 등급** (D, C, B, A, S)
  - Quantile 기반으로 각 20%씩 균등 분포

### 3️⃣ 피처 엔지니어링 (`_02_feature_engineering.py`)
```python
df = add_features(df)
```
**기본 피처:**
- `등록비율`: 등록매물 / 총매물수
- `규모지수`: log(총매물수 + 1)

**지역 기반 피처:**
- `지역내순위`: 해당 지역에서 거래완료 기준 순위
- `지역내백분위`: 지역 내 상위 몇 %인지 (0~1)
- `지역중개사수`: 해당 지역의 중개사 총 개수
- `지역평균대비거래비율`: 지역 평균 대비 거래 비율

### 4️⃣ 분류 모델 (`_05_classification_model.py`)
```python
df = train_classification(df)
```
**모델 설정:**
- RandomForestClassifier
  - n_estimators: 50
  - max_depth: 6
  - min_samples_split: 20
  - min_samples_leaf: 10
  - class_weight: 'balanced'
- Target: `grade` (D, C, B, A, S)
- RobustScaler로 스케일링

**사용 피처 (10개):**
- 원본: `거래완료`, `등록매물`, `총매물수`, `영업일수`, `보증보험유효`
- 파생: `등록비율`, `규모지수`
- 지역: `지역권평균성사율`, `지역내백분위`, `지역중개사수`

**생성 컬럼:**
- `clf_pred`: 등급 예측 (D, C, B, A, S)
- `clf_score`: S등급 확률 (0~1)

**성능:**
- Test Accuracy: 84.21%
- F1-score: 83.84%
- 과적합 차이: 2.30% (건강)

**모델 저장:**
- `models/classification_model.pkl`
- `models/classification_scaler.pkl`

### 5️⃣ 앙상블 (`_06_ensemble.py`)
```python
df = ensemble(df)
```
**최종 신뢰도 온도 계산:**
```
final_temperature = rule_score(정규화) × 0.5 + clf_score × 0.5
```
- 룰 기반 스코어 50%
- ML 분류 확률 50%
- 모든 값이 0~1로 정규화됨

**최종 등급:**
- Quantile 기반으로 D, C, B, A, S 각 20%씩 분류

## 🚀 실행 방법

### 전체 파이프라인 실행
```bash
cd apps/reco/models/trust_model
python run_all.py
```

### 개별 단계 실행 (테스트용)
```bash
python pipeline/_00_load_data.py
python pipeline/_01_rule_score.py
# ... 등등
```

## 📊 출력 결과

### 생성되는 파일
- `results/final_temperature.csv`: 최종 신뢰도 온도가 포함된 전체 데이터 (380개 중개사)
- `models/classification_model.pkl`: RandomForest 분류 모델
- `models/classification_scaler.pkl`: RobustScaler

### 최종 데이터 컬럼
- 원본 데이터 컬럼 (20개)
- `rule_score`: 룰 기반 종합 점수
- `grade`: 등급 (D, C, B, A, S) - rule_score 기반
- `clf_pred`: ML 예측 등급
- `clf_score`: ML 분류 확률 (S등급 확률)
- `final_temperature`: 최종 신뢰도 온도 (0~1) ⭐
- `final_grade`: 최종 등급 (D, C, B, A, S)

## 📝 주요 특징

1. **단순하고 효율적**: 5단계로 구성된 명확한 파이프라인
2. **균형잡힌 성능**: 84% 정확도, 과적합 2.3%
3. **지역 특성 반영**: 지역별 경쟁 환경 및 평균 고려
4. **데이터 누수 방지**: 타겟과 직접 관련된 피처 제외
5. **클래스 균형**: 각 등급이 20%씩 균등 분포
6. **재현 가능성**: 모든 모델 저장 및 재사용 가능

## 🎯 모델 성능

### 분류 모델
- **Test Accuracy**: 84.21%
- **F1-score (macro)**: 83.84%
- **Train Accuracy**: 86.51%
- **과적합 차이**: 2.30% ✅

### 피처 중요도 (Top 3)
1. 거래완료: 20.93%
2. 등록비율: 20.71%
3. 지역평균대비거래비율: 14.86%

### 앙상블 구성
- rule_score: 50%
- ML 분류 확률: 50%

## 🔧 의존성

```python
pandas
numpy
scikit-learn
scipy
```

## 💡 설계 원칙

1. **과적합 방지**
   - 트리 깊이 제한 (max_depth=6)
   - 분할 조건 강화 (min_samples_split=20)
   - 클래스 가중치 균형 (class_weight='balanced')

2. **데이터 누수 방지**
   - 거래성사율, 거래완료비율, 거래밀도 제외
   - 일평균거래 제외 (간접적 누수)

3. **일반화 성능**
   - 학습/테스트 차이 2.3%
   - 새로운 데이터에도 잘 작동

