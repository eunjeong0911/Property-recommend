# 월세 가격 예측 모델 (월세_price_model)

## 프로젝트 개요

서울시 월세 매물 데이터를 기반으로 **환산보증금**(보증금 + 월세*12/0.06)을 예측하는 XGBoost 회귀 모델입니다.

## 주요 성능 지표

| 지표 | 값 |
|------|-----|
| **R²** | 0.7833 |
| **MAE** | 2,362.58 만원 |
| **RMSE** | 3,746.39 만원 |
| **MAPE** | 15.30% |

> 실험명: `clean_features_v1` (타깃 누수 제거, 유의미한 특성 2개 추가)

## 디렉토리 구조

```
월세_price_model/
├── main.py                      # 메인 파이프라인 (학습 및 평가)
├── model.py                     # 모델 생성, 학습, 평가, 실험 로깅
├── feature_engineering.py       # 특성 엔지니어링 (타깃 누수 방지)
├── data_preprocessing.py        # 데이터 로딩 및 전처리
├── visualization.py             # EDA 및 모델 결과 시각화
├── predict.py                   # 학습된 모델로 가격 예측 및 평가
├── __init__.py                  # 패키지 초기화 파일
├── models/                      # 학습된 모델 저장 디렉토리
│   └── model_YYYYMMDD_HHMMSS.pkl
├── results/                     # 실험 결과 저장 디렉토리
│   └── run_YYYYMMDD_HHMMSS/
│       ├── predictions.csv      # 예측 결과
│       ├── metrics.json         # 평가 지표
│       └── images/              # 시각화 이미지
├── experiments/                 # 실험 로그
│   └── experiment_log.csv       # 모든 실험 기록
└── notebooks/
    └── EDA.ipynb                # 탐색적 데이터 분석 노트북
```

## 주요 모듈 설명

### 1. [data_preprocessing.py](../apps/reco/models/월세_price_model/data_preprocessing.py)

데이터 로딩 및 전처리를 담당합니다.

**주요 함수:**
- `load_data(file_path)`: CSV 파일 로드
- `filter_walse_data(df)`: 월세 데이터만 필터링
- `drop_unnecessary_columns(df)`: 불필요한 컬럼 제거
- `remove_invalid_room_data(df)`: 유효하지 않은 방/욕실 데이터 제거
  - 방수 == 0
  - 욕실수 >= 3
  - 파싱 실패 데이터
- `remove_null_dong(df)`: 동 정보가 없는 데이터 제거
- `preprocess_data(file_path)`: 전체 전처리 파이프라인 실행

### 2. [feature_engineering.py](../apps/reco/models/월세_price_model/feature_engineering.py)

특성 엔지니어링을 수행하며, **타깃 누수를 방지**하는 것이 핵심입니다.

**주요 함수:**
- `extract_price_features(df)`: 보증금, 월세, 환산보증금 추출
- `extract_area_features(df)`: 전용면적(평, m²) 추출
- `extract_room_features(df)`: 방수, 욕실수 추출
- `extract_floor_features(df)`: 층 정보 추출
- `add_building_features(df)`: 건축물용도, 건물형태 추출
- `add_location_features(df)`: 구, 동 정보 추출
- `add_option_features(df)`: 옵션 및 키워드 통합
- `add_derived_features(df)`: **타깃 누수 없는 파생 특성 추가**
  - **옵션개수**: 통합옵션의 개수 (가설: 옵션이 많을수록 가격이 높음)
  - **층비율**: 해당층 / 전체층 (가설: 상대적 층 위치가 가격에 영향)
- `prepare_ml_features(df)`: ML 학습용 특성 데이터프레임 생성

**타깃 누수 방지:**
- 환산보증금 = 보증금 + (월세 * 12 / 0.06)
- 보증금, 월세를 직접 사용하는 특성은 제거함 (예: 평당보증금, 평당월세, 보증금월세합 등)

### 3. [model.py](../apps/reco/models/월세_price_model/model.py)

모델 생성, 학습, 평가 및 실험 추적을 담당합니다.

**주요 함수:**
- `split_data(df, target_col)`: 데이터 분할 (train:test = 8:2)
- `create_model(...)`: XGBoost 모델 생성
  - 하이퍼파라미터: n_estimators, learning_rate, max_depth, subsample, colsample_bytree 등
- `tune_hyperparameters(X_train, y_train, n_iter, cv)`: RandomizedSearchCV로 하이퍼파라미터 튜닝
- `train_model(model, X_train, y_train)`: 모델 학습 (로그 변환 적용)
- `predict_model(model, X_test)`: 예측 (로그 역변환 적용)
- `evaluate_model(y_test_log, y_pred)`: 평가 지표 계산 (MAE, RMSE, R², MAPE)
- `full_train_and_evaluate(df_ml, tune_params, n_iter)`: 전체 학습 및 평가 파이프라인
- `save_model(model, model_dir, filename)`: 모델 저장
- `load_model(model_path)`: 모델 로드
- `save_predictions(y_test, y_pred, output_dir, filename)`: 예측 결과 저장
- `save_metrics(metrics, output_dir, filename)`: 평가 지표 저장
- `log_experiment(model, metrics, experiment_name, notes)`: 실험 결과를 CSV에 로깅
- `compare_experiments(top_n)`: 실험 결과 비교 (R² 기준 정렬)

### 4. [main.py](../apps/reco/models/월세_price_model/main.py)

전체 파이프라인을 실행하는 메인 스크립트입니다.

**파이프라인 단계:**
1. 데이터 전처리 (`preprocess_data`)
2. 특성 엔지니어링 (`create_all_features`)
3. 데이터 정제 (`remove_invalid_room_data`, `remove_null_dong`)
4. ML 특성 준비 (`prepare_ml_features`)
5. EDA (옵션)
6. 모델 학습 및 평가 (`full_train_and_evaluate`)
7. 결과 시각화
8. SHAP 분석 (옵션)
9. 결과 저장 (모델, 예측, 지표, 그래프)

**실행 예시:**
```python
python main.py
```

### 5. [visualization.py](../apps/reco/models/월세_price_model/visualization.py)

EDA 및 모델 결과 시각화를 담당합니다.

**주요 함수:**

**EDA 시각화:**
- `plot_correlation_heatmap(df)`: 전체 특성 상관관계 히트맵
- `plot_top_correlation_heatmap(df, target, top_n)`: 타겟과 상관관계 높은 상위 N개 히트맵
- `plot_target_distribution(df, target)`: 타겟 분포 히스토그램
- `plot_log_target_distribution(df, target)`: 로그 변환된 타겟 분포

**모델 결과 시각화:**
- `plot_error_rate_histogram(df_compare)`: 오차율 분포 히스토그램
- `plot_error_rate_boxplot(df_compare)`: 오차율 박스플롯
- `plot_actual_vs_predicted(y_test, y_pred)`: 실제값 vs 예측값 산점도

**SHAP 분석:**
- `create_shap_explainer(model, X_test)`: SHAP explainer 생성
- `plot_shap_summary_bar(shap_values, X_test)`: SHAP 중요도 막대 그래프
- `plot_shap_summary(shap_values, X_test)`: SHAP 요약 플롯

**편의 함수:**
- `plot_all_eda(df_ml)`: 모든 EDA 시각화 수행
- `plot_model_results(y_test, y_pred, df_compare)`: 모델 결과 시각화
- `plot_shap_analysis(model, X_test)`: SHAP 분석 시각화
- `save_all_eda_plots(df_ml, output_dir)`: EDA 그래프 저장
- `save_model_result_plots(y_test, y_pred, df_compare, output_dir)`: 결과 그래프 저장
- `save_shap_plots(model, X_test, output_dir)`: SHAP 그래프 저장

### 6. [predict.py](../apps/reco/models/월세_price_model/predict.py)

학습된 모델을 사용하여 매물 가격을 예측하고 평가합니다.

**주요 함수:**
- `predict_single_property(model, property_features)`: 단일 매물 가격 예측
- `evaluate_price_difference(actual_price, predicted_price, threshold_cheap, threshold_expensive)`: 가격 차이 평가
  - "싸다": 실제가격이 예상가격보다 10% 이상 낮음
  - "적정": 실제가격이 예상가격 ±10% 범위 내
  - "비싸다": 실제가격이 예상가격보다 10% 이상 높음
- `predict_and_evaluate_properties(model, df_processed, original_df)`: 전체 매물 예측 및 평가
- `analyze_price_distribution(results_df)`: 가격 평가 분포 분석
- `get_cheap_properties(results_df, top_n)`: 가장 저렴한 매물 TOP N
- `get_expensive_properties(results_df, top_n)`: 가장 비싼 매물 TOP N
- `save_prediction_results(results_df, output_dir, filename)`: 예측 결과 CSV 저장

**실행 예시:**
```python
python predict.py
```

## 사용 방법

### 1. 모델 학습 및 평가

```bash
cd apps/reco/models/월세_price_model
python main.py
```

**결과:**
- `models/` 폴더에 학습된 모델 저장
- `results/run_YYYYMMDD_HHMMSS/` 폴더에 예측 결과, 평가 지표, 시각화 이미지 저장
- `experiments/experiment_log.csv`에 실험 결과 로깅

### 2. 가격 예측 및 평가

```bash
python predict.py
```

**결과:**
- 전체 매물에 대한 가격 예측
- 가격 평가 분포 (싸다/적정/비싸다)
- 가장 저렴한/비싼 매물 TOP 10
- 예측 결과 CSV 저장

## 실험 결과

실험 로그는 [experiments/experiment_log.csv](../apps/reco/models/월세_price_model/experiments/experiment_log.csv)에 저장됩니다.

| 실험명 | R² | MAE | RMSE | MAPE | 주요 변경사항 |
|--------|----|----|------|------|---------------|
| **clean_features_v1** | **0.7833** | **2,362.58** | **3,746.39** | **15.30%** | 타깃 누수 제거, 유의미한 특성 2개 추가 (옵션개수, 층비율) |
| baseline | 0.7771 | 2,372.64 | 3,799.77 | 15.37% | 기본 하이퍼파라미터 설정 |
| tuned_v1 | 0.7767 | 2,394.65 | 3,802.60 | 15.43% | RandomizedSearchCV로 하이퍼파라미터 튜닝 |
| tuned_v2_aggressive | 0.7726 | 2,373.11 | 3,837.89 | 15.37% | 확장된 파라미터 범위 + 50회 탐색 |
| improved_baseline | 0.7478 | 2,500.50 | 4,041.61 | 16.02% | 개선된 기본 파라미터 (n_estimators=2000, max_depth=10 등) |

### 최적 모델 (clean_features_v1)

**하이퍼파라미터:**
- n_estimators: 1000
- learning_rate: 0.05
- max_depth: 6
- subsample: 0.8
- colsample_bytree: 0.8
- min_child_weight: 1
- gamma: 0
- reg_alpha: 0
- reg_lambda: 1

**주요 개선 사항:**
- 타깃 누수를 일으키는 특성 제거 (보증금, 월세 관련 파생 특성)
- 가설 기반 유의미한 특성 2개 추가:
  - 옵션개수: 통합옵션의 개수
  - 층비율: 해당층 / 전체층

## 주요 특성 (Features)

### 기본 특성
- **환산보증금** (타겟): 보증금 + (월세 × 12 / 0.06)
- **전용면적_평**: 전용면적 (평)
- **전용면적_m2**: 전용면적 (m²)
- **관리비**: 관리비 (만원)
- **건축물용도**: 아파트, 오피스텔, 빌라 등
- **건물형태**: 복층형, 원룸형, 분리형 등
- **층**: 층수
- **방수**: 방 개수
- **욕실수**: 욕실 개수
- **방형태**: 오픈형, 분리형 등
- **방향**: 동향, 남향, 서향, 북향 등
- **구**: 서울시 구 (강남구, 서초구 등)
- **동**: 서울시 동 (역삼동, 삼성동 등)
- **통합옵션**: 옵션 및 키워드 리스트

### 파생 특성 (타깃 누수 없음)
- **옵션개수**: 통합옵션의 개수
  - 가설: 옵션이 많을수록 가격이 높을 것
- **층비율**: 해당층 / 전체층
  - 가설: 상대적 층 위치가 가격에 영향을 줄 것

## 평가 지표 설명

| 지표 | 설명 | 해석 |
|------|------|------|
| **MAE** (Mean Absolute Error) | 평균 절대 오차 | 평균적으로 2,362만원 오차 |
| **RMSE** (Root Mean Squared Error) | 평균 제곱근 오차 | 큰 오차에 더 민감, 3,746만원 |
| **R²** (R-squared) | 결정계수 | 모델이 타겟 변동의 78.33% 설명 |
| **MAPE** (Mean Absolute Percentage Error) | 평균 절대 오차율 | 평균적으로 15.30% 오차율 |

## 주요 개선 과정

### 1. 초기 시도 (baseline)
- 기본 하이퍼파라미터로 모델 학습
- R² = 0.7771

### 2. 하이퍼파라미터 튜닝 (tuned_v1, tuned_v2_aggressive)
- RandomizedSearchCV로 최적 파라미터 탐색
- 결과: 성능 개선 없음 (오히려 소폭 하락)

### 3. 타깃 누수 제거 (clean_features_v1) ⭐
- **문제 발견**: 보증금, 월세를 사용하는 파생 특성들이 타깃 누수를 일으킴
  - 환산보증금 = 보증금 + (월세 × 12 / 0.06)
  - 평당보증금, 평당월세, 보증금월세합 등의 특성이 타겟 계산에 사용됨
- **해결 방법**: 타깃 누수 특성 제거, 가설 기반 유의미한 특성 2개만 추가
- **결과**: R² = 0.7833 (최고 성능), 과적합 없음

## 참고 자료

- [EDA 노트북](../apps/reco/models/월세_price_model/notebooks/EDA.ipynb): SHAP 분석, 상관관계 히트맵 등
- [실험 로그](../apps/reco/models/월세_price_model/experiments/experiment_log.csv): 모든 실험 기록

## 라이선스

This project is part of SKN18-FINAL-1TEAM.
