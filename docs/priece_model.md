# 가격 예측 모델

전국 주요 지역의 전월세 매물을 대상으로 환산보증금을 예측하는 XGBoost 회귀 모델입니다. `apps/reco/models/price_model` 디렉터리 안의 스크립트가 데이터 전처리 → 특성 엔지니어링 → 학습/추론 → 시각화를 모두 담당합니다.

## 구성 요소
- `data_preprocessing.py`: CSV 로딩, 전세/월세 필터링, 필요 컬럼 제거, 방 정보/행정동 누락치 제거 등 기초 정제 로직
- `feature_engineering.py`: 금액·면적·건물·방 상태·방향/주차/위반 여부·구/동 위치·옵션 키워드 등의 파생 특성 생성
- `model.py`: XGBoost 회귀 모델 정의/학습/평가 및 결과 저장
- `visualization.py`: EDA/결과 플롯/SHAP 분석과 이미지 저장 유틸리티
- `predict.py`: 학습된 모델을 활용해 전체 매물의 적정가를 평가하고 `싸다/적정/비쌈`을 분류
- `outputs/`: 학습 과정에서 생성된 CSV, JSON, PNG 자산 보관 경로

## 데이터 파이프라인
1. **전처리 (`preprocess_data`)**
   - `load_data`로 CSV 로딩 후 `filter_walse_data`가 거래 방식에 ‘전세/월세’가 포함된 행만 남깁니다.
   - `drop_unnecessary_columns`로 지도/중개사 등 학습에 쓰지 않을 수십 개 컬럼을 제거합니다.
   - `remove_invalid_room_data`는 “방/욕실=0” 혹은 누락된 매물을 삭제하고, `remove_null_dong`은 행정동 정보가 빠진 행을 제거합니다.

2. **특성 엔지니어링 (`create_all_features`)**
   - `calculate_converted_deposit`: “보증금/월세” 문자열을 분리하고, 월세×12÷0.06으로 환산보증금을 계산합니다.
   - `add_management_fee`: 관리비 텍스트에서 금액만 추출해 숫자 컬럼 생성.
   - `add_area_features`: 전용면적(㎡)과 평단위(`전용면적_m2`, `전용면적_평`)를 추가합니다.
   - `add_building_features`/`add_floor_feature`: 건축물 용도·형태를 점수화하고 층수/층 타입을 정규화합니다.
   - `add_room_features`/`add_room_living_feature`: 방수·욕실수·거실유무·방 형태를 정리합니다.
   - `add_direction_feature`, `add_parking_feature`, `add_violation_feature`: 방향, 주차 가능, 불법 여부 등을 정규화된 수치로 변환합니다.
   - `add_location_features`: 주소 문자열에서 구/동을 추출해 Label Encoding에 사용할 텍스트 컬럼을 만듭니다.
   - `add_option_features`: 상세 설명·생활시설·추가 옵션·기타 시설에서 키워드를 파싱하여 `통합옵션` 리스트를 구성합니다.

3. **모델 입력 구성 (`prepare_ml_features`)**
   - 모델 학습에 필요한 컬럼만 선택(`환산보증금`, `전용면적_평`, `층`, `구` 등) 후 MultiLabelBinarizer로 옵션을 one-hot 인코딩합니다.
   - `구`, `동`은 LabelEncoder로 숫자화해 XGBoost에 전달합니다.

## 모델 학습 및 평가
- `create_model`은 `xgboost.XGBRegressor`를 `n_estimators=1000`, `learning_rate=0.05`, `max_depth=6`, `subsample=0.8`, `colsample_bytree=0.8`, `tree_method='hist'`로 초기화합니다.
- `train_model`에서는 `log1p` 변환된 타깃(`환산보증금`)을 사용해 안정적으로 학습하며, `predict_model` 단계에서 `expm1`로 원 스케일을 복원합니다.
- `evaluate_model`은 MAE, RMSE, R², MAPE를 계산하고 `print_evaluation_results`가 콘솔로 출력합니다.
- `main.main`이 전체 파이프라인을 묶어 실행하며, `save_results=True`인 경우 다음 항목을 저장합니다.
  - `models/model_YYYYMMDD_HHMMSS.pkl`: 학습된 모델
  - `outputs/predictions_YYYYMMDD_HHMMSS.csv`: 실제/예측/오차율
  - `outputs/metrics_YYYYMMDD_HHMMSS.json`: 성능 지표와 타임스탬프
  - `outputs/results/*.png`: 오차율 히스토그램, 박스플롯, 실제 vs 예측 산점도

## 시각화와 설명가능성
- `plot_all_eda`는 상관행렬, 분포, 면적-층별 산점 등 9가지 EDA 차트를 생성합니다. `save_all_eda_plots`를 호출하면 `outputs/eda`에 PNG를 저장합니다.
- `save_model_result_plots`는 저장용 호출에 대해 `plt.show()`를 차단(`show=False`)하므로 GUI 백엔드가 없는 서버에서도 `01_error_rate_histogram.png` 같은 결과물을 안정적으로 생성합니다.
- `plot_shap_analysis`는 `shap.TreeExplainer`로 전역/Top-N 기여도를 시각화합니다.

## 실행 방법
1. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```
2. **학습 및 예측 파이프라인 실행**
   ```bash
   python -m apps.reco.models.changes
   python -m apps.reco.models.price_model.main
   python -m apps.reco.models.predict
   ```


## 산출물 구조
```
apps/reco/models/price_model/
├─ models/                 # 최신 모델(.pkl)
├─ outputs/
│  ├─ predictions_*.csv    # 예측 결과
│  ├─ metrics_*.json       # 성능 지표
│  ├─ results/             # 모델 결과 플롯 (01~03)
│  └─ eda/ (선택)          # run_eda=True일 때 저장
└─ notebooks/              # 실험용 EDA/모델링 노트
```