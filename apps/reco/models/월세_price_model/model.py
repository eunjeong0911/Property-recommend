"""
모델 학습 및 평가 모듈
"""
import os
import warnings
import pickle
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.utils.validation import check_is_fitted
from xgboost import XGBRegressor


def split_data(df: pd.DataFrame, target_col: str = "환산보증금",
               test_size: float = 0.2, random_state: int = 42):
    """
    데이터를 학습/테스트 세트로 분할합니다.

    Args:
        df: 특성 데이터프레임
        target_col: 타깃 컬럼명
        test_size: 테스트 세트 비율
        random_state: 랜덤 시드

    Returns:
        tuple: (X_train, X_test, y_train, y_test)
    """
    X = df.drop(columns=[target_col])
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state
    )

    return X_train, X_test, y_train, y_test


def create_model(n_estimators: int = 1000, learning_rate: float = 0.05,
                 max_depth: int = 6, subsample: float = 0.8,
                 colsample_bytree: float = 0.8, min_child_weight: int = 1,
                 gamma: float = 0, reg_alpha: float = 0, reg_lambda: float = 1,
                 random_state: int = 42, n_jobs: int = -1, tree_method: str = 'hist'):

    # XGBoost 모델 생성
    model = XGBRegressor(
        n_estimators=n_estimators,          # 부스팅 라운드 수
        learning_rate=learning_rate,        # 학습률
        max_depth=max_depth,                # 트리 최대 깊이
        subsample=subsample,                # 샘플 서브샘플링 비율
        colsample_bytree=colsample_bytree,  # 특성 서브샘플링 비율
        min_child_weight=min_child_weight,  # 최소 자식 가중치
        gamma=gamma,                        # 노드 분할 최소 손실 감소
        reg_alpha=reg_alpha,                # L1 정규화 계수
        reg_lambda=reg_lambda,              # L2 정규화 계수
        random_state=random_state,          # 랜덤 시드
        n_jobs=n_jobs,                      # 병렬 처리 코어 수
        tree_method=tree_method             # 트리 생성 방법
    )

    return model


def tune_hyperparameters(X_train, y_train, n_iter: int = 50, cv: int = 5, random_state: int = 42):
    """
    RandomizedSearchCV로 하이퍼파라미터를 튜닝합니다.

    Args:
        X_train: 학습 특성
        y_train: 학습 타깃
        n_iter: 탐색할 조합 수
        cv: 교차 검증 폴드 수
        random_state: 랜덤 시드

    Returns:
        dict: 최적 파라미터
    """
    print("\n하이퍼파라미터 튜닝 시작...")
    print(f"탐색 횟수: {n_iter}, 교차 검증: {cv}-fold")

    # 로그 변환
    y_train_log = np.log1p(y_train)

    # 탐색할 파라미터 범위
    param_distributions = {
        'n_estimators': [1500, 2000, 2500, 3000],
        'learning_rate': [0.01, 0.02, 0.03, 0.05, 0.07, 0.1],
        'max_depth': [8, 10, 12, 15, 20],
        'min_child_weight': [1, 2, 3, 5, 7],
        'subsample': [0.6, 0.7, 0.8, 0.85, 0.9, 0.95],
        'colsample_bytree': [0.6, 0.7, 0.8, 0.85, 0.9, 0.95],
        'gamma': [0, 0.05, 0.1, 0.2, 0.3],
        'reg_alpha': [0, 0.01, 0.1, 0.5, 1, 2],
        'reg_lambda': [0.5, 1, 1.5, 2, 3, 5]
    }

    # 기본 모델 생성
    base_model = XGBRegressor(
        random_state=random_state,
        n_jobs=-1,
        tree_method='hist'
    )

    # RandomizedSearchCV 실행
    random_search = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=param_distributions,
        n_iter=n_iter,
        cv=cv,
        scoring='r2',
        n_jobs=-1,
        random_state=random_state,
        verbose=2
    )

    random_search.fit(X_train, y_train_log)

    print(f"\n최적 파라미터: {random_search.best_params_}")
    print(f"최적 R² 점수 (CV): {random_search.best_score_:.4f}")

    return random_search.best_params_


def is_fitted_model(m):
    """
    모델이 학습되었는지 확인합니다.

    Args:
        m: 모델 객체

    Returns:
        bool: 학습 여부
    """
    try:
        check_is_fitted(m)
        return True
    except Exception:
        return False


def train_model(model, X_train, y_train, X_val=None, y_val=None,
                early_stopping_rounds: int = 50, verbose: int = 50):
    """
    모델을 학습시킵니다.

    Args:
        model: XGBoost 모델
        X_train: 학습 특성
        y_train: 학습 타깃
        X_val: 검증 특성 
        y_val: 검증 타깃
        early_stopping_rounds: 조기 종료 라운드
        verbose: 로그 출력 주기

    Returns:
        model: 학습된 모델
    """
    # 모델이 이미 학습되었는지 확인
    if is_fitted_model(model):
        warnings.warn("모델이 이미 학습되어 있습니다. 재학습을 진행합니다.")

    # 로그 변환
    y_train_log = np.log1p(y_train)

    # 검증 세트가 있으면 조기 종료 포함 학습
    if X_val is not None and y_val is not None:
        y_val_log = np.log1p(y_val)
        try:
            model.fit(
                X_train,
                y_train_log,
                eval_set=[(X_val, y_val_log)],
                verbose=verbose,
            )
        except Exception as e:
            warnings.warn(f"검증 세트로 학습 중 오류 발생: {e}. 전체 학습 데이터로 재시도합니다.")
            model.fit(X_train, y_train_log)
    else:
        # 검증 세트가 없으면 전체 학습 데이터로 학습
        model.fit(X_train, y_train_log)

    return model


def predict_model(model, X_test):
    """
    모델로 예측을 수행합니다.

    Args:
        model: 학습된 XGBoost 모델
        X_test: 테스트 특성

    Returns:
        np.ndarray: 예측값
    """
    if not is_fitted_model(model):
        raise RuntimeError("모델이 학습되지 않았습니다. 먼저 train_model을 호출하세요.")

    # 예측 (가능하면 best_iteration 사용)
    y_pred_log = None
    try:
        if hasattr(model, 'get_booster'):
            try:
                booster = model.get_booster()
                best_it = getattr(booster, 'best_iteration', None)
                if best_it is not None and best_it > 0:
                    try:
                        y_pred_log = model.predict(X_test, iteration_range=(0, best_it+1))
                    except Exception:
                        y_pred_log = model.predict(X_test)
                else:
                    y_pred_log = model.predict(X_test)
            except Exception:
                y_pred_log = model.predict(X_test)
        else:
            y_pred_log = model.predict(X_test)
    except Exception as e:
        raise RuntimeError(f"모델 예측 실패: {e}")

    # 역변환
    y_pred = np.expm1(y_pred_log)

    return y_pred


def evaluate_model(y_test, y_pred):
    """
    모델 성능을 평가합니다.

    Args:
        y_test: 실제 타깃값
        y_pred: 예측값

    Returns:
        dict: 평가 지표 딕셔너리
    """
    # 테스트 타깃 역변환 (로그 역변환)
    y_test_orig = np.expm1(y_test) if np.any(y_test < 0) == False and np.all(y_test < 100) else y_test

    mae = mean_absolute_error(y_test_orig, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test_orig, y_pred))
    r2 = r2_score(y_test_orig, y_pred)
    mape = np.mean(np.abs((y_test_orig - y_pred) / y_test_orig)) * 100

    metrics = {
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2,
        "MAPE": mape
    }

    return metrics


def print_evaluation_results(metrics: dict):
    """
    평가 결과를 출력합니다.

    Args:
        metrics: 평가 지표 딕셔너리
    """
    print("=== XGBoost 모델 성능 ===")
    print(f"MAE  : {metrics['MAE']:,.2f}")
    print(f"RMSE : {metrics['RMSE']:,.2f}")
    print(f"R^2  : {metrics['R2']:.4f}")
    print(f"MAPE : {metrics['MAPE']:.2f}%")


def create_comparison_dataframe(y_test, y_pred, num_samples: int = 10):
    """
    실제값과 예측값을 비교하는 데이터프레임을 생성합니다.

    Args:
        y_test: 실제 타깃값
        y_pred: 예측값
        num_samples: 샘플 개수

    Returns:
        pd.DataFrame: 비교 데이터프레임
    """
    y_test_orig = np.expm1(y_test) if np.any(y_test < 0) == False and np.all(y_test < 100) else y_test

    df_compare = pd.DataFrame({
        "실제값": y_test_orig.values[:num_samples],
        "예측값": y_pred[:num_samples]
    })

    df_compare["오차율(%)"] = np.abs((df_compare["실제값"] - df_compare["예측값"]) / df_compare["실제값"]) * 100

    return df_compare


def full_train_and_evaluate(df_ml: pd.DataFrame, target_col: str = "환산보증금",
                           tune_params: bool = False, n_iter: int = 20):
    """
    전체 학습 및 평가 파이프라인을 실행합니다.

    Args:
        df_ml: 머신러닝용 특성 데이터프레임
        target_col: 타깃 컬럼명
        tune_params: 하이퍼파라미터 튜닝 실행 여부
        n_iter: 튜닝 시 탐색할 조합 수

    Returns:
        tuple: (model, X_train, X_test, y_train, y_test, y_pred, metrics)
    """
    # 1. 데이터 분할
    X_train, X_test, y_train, y_test = split_data(df_ml, target_col)

    # 2. 하이퍼파라미터 튜닝 (옵션)
    if tune_params:
        best_params = tune_hyperparameters(X_train, y_train, n_iter=n_iter)
        model = create_model(**best_params)
    else:
        # 기본 모델 생성
        model = create_model()

    # 3. 모델 학습
    model = train_model(model, X_train, y_train)

    # 4. 예측
    y_pred = predict_model(model, X_test)

    # 5. 평가
    # y_test를 로그 변환된 상태로 전달
    y_test_log = np.log1p(y_test)
    metrics = evaluate_model(y_test_log, y_pred)

    # 6. 결과 출력
    print_evaluation_results(metrics)

    return model, X_train, X_test, y_train, y_test, y_pred, metrics


def save_model(model, model_dir: str = None, filename: str = None):
    """
    학습된 모델을 저장합니다.

    Args:
        model: 학습된 모델
        model_dir: 모델 저장 디렉토리 (기본값: 현재 파일의 models/ 폴더)
        filename: 저장할 파일명 (기본값: model_YYYYMMDD_HHMMSS.pkl)

    Returns:
        str: 저장된 파일 경로
    """
    # 기본 저장 디렉토리 설정
    if model_dir is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(current_dir, "models")

    # 디렉토리 생성
    os.makedirs(model_dir, exist_ok=True)

    # 파일명 생성
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"model_{timestamp}.pkl"

    # 전체 경로
    filepath = os.path.join(model_dir, filename)

    # 모델 저장
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)

    print(f"✓ 모델 저장 완료: {filepath}")
    return filepath


def load_model(filepath: str):
    """
    저장된 모델을 로드합니다.

    Args:
        filepath: 모델 파일 경로

    Returns:
        model: 로드된 모델
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {filepath}")

    with open(filepath, 'rb') as f:
        model = pickle.load(f)

    print(f"✓ 모델 로드 완료: {filepath}")
    return model


def save_predictions(y_test, y_pred, output_dir: str = None, filename: str = None):
    """
    예측 결과를 CSV 파일로 저장합니다.

    Args:
        y_test: 실제값
        y_pred: 예측값
        output_dir: 저장 디렉토리 (기본값: 현재 파일의 outputs/ 폴더)
        filename: 저장할 파일명 (기본값: predictions_YYYYMMDD_HHMMSS.csv)

    Returns:
        str: 저장된 파일 경로
    """
    # 기본 저장 디렉토리 설정
    if output_dir is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, "outputs")

    # 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # 파일명 생성
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"predictions_{timestamp}.csv"

    # 전체 경로
    filepath = os.path.join(output_dir, filename)

    # 데이터프레임 생성
    y_test_orig = np.expm1(y_test) if np.any(y_test < 0) == False and np.all(y_test < 100) else y_test

    df_result = pd.DataFrame({
        "실제값": y_test_orig.values,
        "예측값": y_pred,
        "오차": y_test_orig.values - y_pred,
        "오차율(%)": np.abs((y_test_orig.values - y_pred) / y_test_orig.values) * 100
    })

    # CSV 저장
    df_result.to_csv(filepath, index=False, encoding='utf-8-sig')

    print(f"✓ 예측 결과 저장 완료: {filepath}")
    return filepath


def save_metrics(metrics: dict, output_dir: str = None, filename: str = None):
    """
    평가 지표를 JSON 파일로 저장합니다.

    Args:
        metrics: 평가 지표 딕셔너리
        output_dir: 저장 디렉토리 (기본값: 현재 파일의 outputs/ 폴더)
        filename: 저장할 파일명 (기본값: metrics_YYYYMMDD_HHMMSS.json)

    Returns:
        str: 저장된 파일 경로
    """
    import json

    # 기본 저장 디렉토리 설정
    if output_dir is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, "outputs")

    # 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # 파일명 생성
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"metrics_{timestamp}.json"

    # 전체 경로
    filepath = os.path.join(output_dir, filename)

    # 타임스탬프 추가
    metrics_with_timestamp = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **metrics
    }

    # JSON 저장
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(metrics_with_timestamp, f, indent=2, ensure_ascii=False)

    print(f"✓ 평가 지표 저장 완료: {filepath}")
    return filepath


def log_experiment(model, metrics: dict, experiment_name: str = None, notes: str = ""):
    """
    실험 결과를 experiment_log.csv에 기록합니다.

    Args:
        model: 학습된 XGBoost 모델
        metrics: 평가 지표 딕셔너리
        experiment_name: 실험 이름
        notes: 실험 노트

    Returns:
        str: 로그 파일 경로
    """
    # 로그 파일 경로
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(current_dir, "experiments")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "experiment_log.csv")

    # 타임스탬프
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 모델 파라미터 추출
    params = model.get_params()

    # 실험 데이터 준비
    experiment_data = {
        "timestamp": timestamp,
        "experiment_name": experiment_name or f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "n_estimators": params.get('n_estimators'),
        "learning_rate": params.get('learning_rate'),
        "max_depth": params.get('max_depth'),
        "min_child_weight": params.get('min_child_weight'),
        "subsample": params.get('subsample'),
        "colsample_bytree": params.get('colsample_bytree'),
        "gamma": params.get('gamma'),
        "reg_alpha": params.get('reg_alpha'),
        "reg_lambda": params.get('reg_lambda'),
        "MAE": metrics['MAE'],
        "RMSE": metrics['RMSE'],
        "R2": metrics['R2'],
        "MAPE": metrics['MAPE'],
        "notes": notes
    }

    # DataFrame으로 변환
    df_new = pd.DataFrame([experiment_data])

    # 기존 로그 파일이 있으면 추가, 없으면 새로 생성
    if os.path.exists(log_file):
        df_existing = pd.read_csv(log_file, encoding='utf-8-sig')
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    # CSV 저장
    df_combined.to_csv(log_file, index=False, encoding='utf-8-sig')

    print(f"✓ 실험 결과 로그 저장: {log_file}")
    return log_file


def compare_experiments(top_n: int = 10):
    """
    실험 로그를 읽어서 상위 N개의 실험을 R² 기준으로 비교합니다.

    Args:
        top_n: 상위 N개 실험 표시

    Returns:
        pd.DataFrame: 상위 실험 결과
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(current_dir, "experiments", "experiment_log.csv")

    if not os.path.exists(log_file):
        print("실험 로그 파일이 없습니다.")
        return None

    # 로그 파일 읽기
    df = pd.read_csv(log_file, encoding='utf-8-sig')

    # R² 기준으로 정렬
    df_sorted = df.sort_values('R2', ascending=False).head(top_n)

    print("\n" + "="*120)
    print(f"상위 {top_n}개 실험 결과 (R² 기준)")
    print("="*120)

    # 주요 컬럼만 표시
    display_cols = ['experiment_name', 'timestamp', 'R2', 'MAE', 'RMSE', 'MAPE',
                    'learning_rate', 'max_depth', 'n_estimators']

    # 존재하는 컬럼만 필터링
    display_cols = [col for col in display_cols if col in df_sorted.columns]

    print(df_sorted[display_cols].to_string(index=False))
    print("="*120)

    return df_sorted
