# 전세 평당 전세금 예측 노트북 가이드

본 README는 `apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb`을 기반으로 서울 전세 매물의 평당 전세금을 예측/비교하는 워크플로를 자세히 설명합니다. 실험 재현, 추가 피처 개발, 모델 로깅까지 한 번에 이해할 수 있도록 노트북 셀의 주요 위치를 함께 명시했습니다.

---

## 1. 개요

- **목적**: 전세금/전용면적(평) 기반의 평당 전세금(만원)을 정확히 예측하고, 다양한 트리 기반 모델을 비교해 최적 모델을 추천합니다.
- **핵심 기능**
  1. CSV 데이터 로드 및 정제 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:115`)
  2. 풍부한 특성 엔지니어링과 타깃/피처 분리 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:325`, `661`)
  3. XGBoost 단일 모델 학습 → 평가 → SHAP 해석 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:801`–`1045`)
  4. XGBoost/LightGBM/CatBoost/RandomForest/GradientBoosting 동시 학습·비교 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:1400`)
  5. 실험 로그(CSV/JSON) 저장 및 모델 추천 로직 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:1611`, `1650`)

---

## 2. 데이터 요구사항

| 항목 | 설명 | 참고 코드 |
| --- | --- | --- |
| 원본 경로 | `data/통합.csv` (UTF-8) | `apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:115` |
| 주요 컬럼 | `추가_옵션`, `주소_정보.전체주소`, `거래_정보.*`, `매물_정보.*` | `apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:29` |
| 필터링 | `거래_정보.거래방식`에 “전세” 포함 행만 사용 | `apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:122` |
| 타깃 | `평당가 = 전세금 / 전용면적(평)` | `apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:235` |
| 이상치 제거 | IQR 기반 평당가 범위 필터링 | `apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:275` |

추가적으로 `data/landData/*.json`, `data/국토교통부_*`, `data/서울시 지하철_*` 등을 조인하면 입지·교통·노후 피처 확장이 가능합니다 (README 끝부분 참고).

---

## 3. 실행 환경 및 준비

1. **Python 패키지**  
   `pandas`, `numpy`, `re`, `time`, `json`, `datetime`, `matplotlib`, `seaborn`, `scikit-learn`, `xgboost`, `lightgbm`, `catboost`, `shap` 등 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:29`).

2. **환경 설정**  
   - 한글 그래프 깨짐 방지를 위해 맑은고딕 폰트 설정 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:4`).
   - 경로 상수 `data_path`는 로컬에 맞게 수정 가능 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:115`).

3. **실행 방법**  
   - `jupyter notebook apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb`
   - 상단 셀부터 순차 실행 → 데이터 준비 → 피처 생성 → 학습/비교 → 로그 저장.

---

## 4. 피처 엔지니어링 세부 설명

| 구분 | 주요 피처 | 설명 및 참고 셀 |
| --- | --- | --- |
| 기본 | `전용면적_평`, `관리비`, `욕실수`, `층`, `방수` 등 | 면적/옵션/층 정보 추출 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:325`–`343`) |
| 위치 | `구`, `동` | 주소 파싱 후 결측 제거 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:356`–`362`) |
| 파생 | `평당_방수`, `평당_관리비` | 면적 대비 방/관리비 효율 지표 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:595`–`611`) |
| 층/방향 | `전체층수`, `층비율`, `is_남향계열`, `난방_개별` | 층/방향/난방 특성 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:517`, `521`, `533`, `543`) |
| ML 입력 | `feature_cols` 총 13개 | 타깃 제외 최종 피처 목록 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:661`) |

> README 제안대로 `건축연차`, `리모델링여부`, `옵션_주차가능` 등 추가 피처를 만들려면 해당 셀 아래에 로직을 삽입하고 `feature_cols`를 업데이트하세요.

---

## 5. 학습/평가 파이프라인

1. **인코딩 및 데이터 분할**  
   - `LabelEncoder`로 `구`, `동` 인코딩 후 80:20 분할 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:688`).

2. **타깃 로그 변환**  
   - `np.log1p`로 타깃을 정규화하고 학습/테스트에 각각 저장 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:26`).

3. **XGBoost 학습**  
   - 튜닝된 하이퍼파라미터(`n_estimators=1800`, `learning_rate=0.018` 등)를 사용 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:801`).
   - 학습 완료 후 원 스케일로 예측 복원, MAE/RMSE/R²/MAPE 출력 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:29`).

4. **시각화**  
   - 실제 vs 예측 산점도, 오차율 히스토그램, 특성 중요도 바 차트, SHAP 바/도트 플롯/워터폴 등 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:31`–`40`).

---

## 6. 다중 모델 비교 및 추천

- **모델 구성**: XGBoost, LightGBM, CatBoost, RandomForest, GradientBoosting (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:1400`).
- **평가 루프**: 모델별 학습 시간, MAE, RMSE, R², MAPE 계산 후 리스트에 append (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:1422`).
- **결과 테이블 & 그래프**: `df_results` 정렬 출력 및 성능 지표 바 차트 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:1444`, `1493`).
- **레이더 차트**: 정규화된 R²/MAE/RMSE/MAPE/학습시간을 한 번에 비교 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:1529`).
- **상황별 추천**: 성능/속도/균형/프로덕션 기준으로 최적 모델 선택 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:1650`).
- **현재 최고 성능**: CatBoost R² ≈ 0.7562, MAE ≈ 367.48만원 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:1425`).

---

## 7. 실험 로그와 재학습

- **로그 함수**: `save_experiment_log`가 결과 리스트, 사용 피처, 모델 파라미터를 받아 CSV/JSON 저장 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:1611`).
- **저장 위치**: 기본 `../experiments` (노트북 경로 기준). 파일명은 `experiment_YYYYMMDD_HHMMSS.*`.
- **추가 셀**: 마지막 “15-5. 실험 결과 저장” 셀(현재 비어 있음)에 README에서 안내한 코드(실험 로그 + 최적 모델 재학습)를 입력하면 전체 데이터로 재학습하며 로그까지 남길 수 있습니다.
- **재현성**: 모든 모델이 `random_state=42`를 사용하므로 결과 재현이 용이 (`apps/reco/models/price_model/jeonse/notebooks/imporved_model.ipynb:801` 등).

---

## 8. 디렉터리 구조 & 산출물
apps/
└─ reco/models/price_model/jeonse/
├─ notebooks/
│ ├─ imporved_model.ipynb # 본 노트북
│ └─ (README.md를 이 위치에 생성 가능)
└─ experiments/
├─ experiment_<timestamp>.csv
└─ experiment_<timestamp>.json
data/
├─ 통합.csv # 필수 원본 데이터
├─ 서울시 지하철 호선별 ... csv # 교통 피처 확장용
├─ 국토교통부_전국 버스정류장 ... # 버스 접근성 확장용
└─ landData/00_통합_*.json # 건축연차·단지 정보