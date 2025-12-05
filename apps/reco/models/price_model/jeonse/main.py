"""
전세 가격 예측 모델 메인 파이프라인
전체 데이터 처리, 특성 엔지니어링, 모델 학습 및 평가를 실행합니다.
"""
import os
from datetime import datetime

# 모듈 import
# 패키지로 사용될 때와 직접 실행될 때 모두 지원
try:
    # 패키지로 import될 때 (상대 import)
    from .data_preprocessing import preprocess_data
    from .feature_engineering import create_all_features, prepare_ml_features
    from .model import (
        full_train_and_evaluate,
        save_model,
        save_predictions,
        save_metrics,
        log_experiment
    )
    from .visualization import (
        save_all_eda_plots,
        save_model_result_plots,
        save_shap_plots,
        plot_feature_importance,
        plot_correlation_heatmap
    )
except ImportError:
    # 직접 실행될 때 (절대 import)
    from data_preprocessing import preprocess_data
    from feature_engineering import create_all_features, prepare_ml_features
    from model import (
        full_train_and_evaluate,
        save_model,
        save_predictions,
        save_metrics,
        log_experiment
    )
    from visualization import (
        save_all_eda_plots,
        save_model_result_plots,
        save_shap_plots,
        plot_feature_importance,
        plot_correlation_heatmap
    )


def main(data_path: str, run_eda: bool = False, run_shap: bool = False,
         save_results: bool = True, tune_params: bool = False, n_iter: int = 20,
         use_oof_target_encoding: bool = False,
         experiment_name: str = None, experiment_notes: str = ""):
    """
    전체 파이프라인을 실행합니다.

    Args:
        data_path: CSV 파일 경로
        run_eda: EDA 시각화 실행 여부
        run_shap: SHAP 분석 실행 여부
        save_results: 결과물 저장 여부 (모델, 예측결과, 그래프 등)
        tune_params: 하이퍼파라미터 튜닝 실행 여부
        n_iter: 튜닝 시 탐색할 조합 수
        use_oof_target_encoding: Out-of-Fold Target Encoding 사용 여부
        experiment_name: 실험 이름 (로깅용)
        experiment_notes: 실험 노트 (로깅용)

    Returns:
        tuple: (model, df_ml, X_train, X_test, y_train, y_test, y_pred, metrics)
    """
    print("=" * 80)
    print("전세 가격 예측 모델 파이프라인 시작")
    print("=" * 80)

    # ==================== 1. 데이터 전처리 ====================
    print("\n[1/6] 데이터 전처리 중...")
    df_jeonse = preprocess_data(data_path)
    print(f"✓ 전세 데이터 로드 완료: {len(df_jeonse)}행")

    # ==================== 2. 특성 엔지니어링 ====================
    print("\n[2/6] 특성 엔지니어링 중...")
    df_jeonse = create_all_features(df_jeonse, use_oof_target_encoding=use_oof_target_encoding)
    print("✓ 특성 엔지니어링 완료")

    # ==================== 3. ML 특성 준비 ====================
    print("\n[3/6] ML 특성 준비 중...")
    df_ml = prepare_ml_features(df_jeonse)
    print(f"✓ ML 특성 준비 완료: {df_ml.shape[1]}개 특성, {len(df_ml)}행")

    # ==================== 4. EDA ====================
    if run_eda:
        print("\n[EDA] 탐색적 데이터 분석 시각화 중...")
        # EDA 플롯은 결과 저장 시 함께 저장

    # ==================== 5. 모델 학습 및 평가 ====================
    print("\n[4/6] 모델 학습 및 평가 중...")
    model, X_train, X_test, y_train, y_test, y_pred, metrics = full_train_and_evaluate(
        df_ml,
        target_col="평당가",
        tune_params=tune_params,
        n_iter=n_iter
    )
    print("✓ 모델 학습 및 평가 완료")

    # 실험 결과 로깅
    log_experiment(model, metrics, experiment_name=experiment_name, notes=experiment_notes)

    # ==================== 6. 결과 저장 ====================
    saved_files = {}
    if save_results:
        print("\n[결과 저장] 모델 및 결과물 저장 중...")

        # 타임스탬프로 결과 폴더 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        results_dir = os.path.join(current_dir, "results", f"run_{timestamp}")
        images_dir = os.path.join(results_dir, "images")
        os.makedirs(results_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)

        # 모델 저장 (models 폴더에 저장)
        models_dir = os.path.join(current_dir, "models")
        model_path = save_model(model, model_dir=models_dir, filename=f"model_{timestamp}.pkl")
        saved_files['model'] = model_path

        # 예측 결과 저장
        pred_path = save_predictions(y_test, y_pred, output_dir=results_dir, filename="predictions.csv")
        saved_files['predictions'] = pred_path

        # 평가 지표 저장 (JSON)
        metrics_path = save_metrics(metrics, output_dir=results_dir, filename="metrics.json")
        saved_files['metrics'] = metrics_path

        # EDA 그래프 저장
        if run_eda:
            eda_plots = save_all_eda_plots(df_jeonse, target="평당가", output_dir=images_dir)
            saved_files['eda_plots'] = eda_plots

            # 피처 상관관계 히트맵
            X = df_ml.drop(columns=["평당가"])
            corr_path = os.path.join(images_dir, "05_피처_상관관계.png")
            plot_correlation_heatmap(X, output_path=corr_path)
            saved_files['correlation_plot'] = corr_path

        # 모델 결과 그래프 저장
        result_plots = save_model_result_plots(y_test, y_pred, output_dir=images_dir)
        saved_files['result_plots'] = result_plots

        # 특성 중요도 그래프 저장
        X = df_ml.drop(columns=["평당가"])
        importance_path = os.path.join(images_dir, "05_특성_중요도.png")
        plot_feature_importance(model, X, output_path=importance_path)
        saved_files['importance_plot'] = importance_path

        # SHAP 그래프 저장
        if run_shap:
            print("\n[SHAP 분석] SHAP 그래프 저장 중...")
            shap_plots = save_shap_plots(model, X_test, output_dir=images_dir)
            saved_files['shap_plots'] = shap_plots

        print(f"\n✓ 결과 저장 완료: {results_dir}")

    # ==================== 최종 요약 ====================
    print("\n" + "=" * 80)
    print("파이프라인 실행 완료!")
    print("=" * 80)
    print("\n최종 모델 성능:")
    print(f"  - MAE  : {metrics['MAE']:,.2f} 만원")
    print(f"  - RMSE : {metrics['RMSE']:,.2f} 만원")
    print(f"  - R^2  : {metrics['R2']:.4f}")
    print(f"  - MAPE : {metrics['MAPE']:.2f}%")

    if save_results:
        print("\n저장된 파일:")
        print(f"  - 모델: {saved_files.get('model', 'N/A')}")
        print(f"  - 결과 폴더: {results_dir}")
        print(f"    ∟ predictions.csv")
        print(f"    ∟ metrics.json")
        print(f"    ∟ images/")
        print(f"      ├─ 결과 그래프: {len(saved_files.get('result_plots', []))}개")
        if run_shap:
            print(f"      ├─ SHAP 그래프: {len(saved_files.get('shap_plots', []))}개")
        if run_eda:
            print(f"      └─ EDA 그래프: {len(saved_files.get('eda_plots', []))}개")

    print("=" * 80)

    return model, df_ml, X_train, X_test, y_train, y_test, y_pred, metrics


if __name__ == "__main__":
    # 데이터 파일 경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "..",".."))
    data_path = os.path.join(project_root, "data", "통합.csv")

    # 파이프라인 실행
    model, df_ml, X_train, X_test, y_train, y_test, y_pred, metrics = main(
        data_path=data_path,
        run_eda=True,          # EDA 시각화 실행
        run_shap=True,         # SHAP 분석 실행
        save_results=True,     # 결과 저장
        tune_params=False,     # 하이퍼파라미터 튜닝 실행 여부
        use_oof_target_encoding=False,  # Out-of-Fold Target Encoding 사용 여부
        experiment_name="baseline",
        experiment_notes="기본 설정으로 실행"
    )

