"""
SHAP 분석 예시 스크립트
"""
from pathlib import Path

from data_loader import DataLoader
from preprocessor import PriceDataPreprocessor
from model import get_models
from trainer import ModelTrainer
import matplotlib.pyplot as plt
import matplotlib as mpl

# 1) 폰트 설정 (Windows: 맑은 고딕)
plt.rcParams['font.family'] = 'Malgun Gothic'

# 2) 마이너스(-) 깨짐 방지
mpl.rcParams['axes.unicode_minus'] = False

ML_ROOT = Path(__file__).resolve().parent.parent
PLOTS_DIR = ML_ROOT / "shap_plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def example_shap_analysis():
    """전체 파이프라인을 통해 SHAP 분석을 수행하는 예시"""

    print("\n" + "=" * 70)
    print(">> SHAP 분석 예시 실행")
    print("=" * 70)

    # 1. 데이터 로딩
    print("\n[Step 1] 데이터 로딩")
    data_dir = "C:/dev/SKN18-FINAL-1TEAM/data/actual_transaction_price"
    loader = DataLoader(data_dir)
    train_df, test_df = loader.load_train_test(
        train_filename="월세_train(24.08~25.08).csv",
        test_filename="월세_test(25.09~25.10).csv",
    )

    # 2. 전처리 및 피처 생성
    print("\n[Step 2] 타깃 생성 및 고급 피처 엔지니어링")
    preprocessor = PriceDataPreprocessor()

    # 타깃 생성 (Train: 전체 통계 사용, Test: Train 통계 사용)
    train_df = preprocessor.create_target(train_df)
    test_df = preprocessor.create_target(
        test_df,
        train_stats={"gu_quantiles": preprocessor.train_gu_quantiles}
    )

    train_df, test_df = preprocessor.advanced_feature_engineering(train_df, test_df)

    # 3. Train/Val 분할
    print("\n[Step 3] Train/Val 분할")
    X_train, y_train, X_val, y_val = preprocessor.prepare_train_test_split(
        train_df, split_date="2025-06"
    )

    # 테스트용 특성/타깃
    X_test = test_df[preprocessor.candidate_features]
    y_test = test_df[preprocessor.target_name]

    # 4. Tree 모델용 피처 변환 (Label Encoding, No Scaling)
    print("\n[Step 4] Tree 모델용 피처 변환")
    X_train_t, X_val_t, X_test_t = preprocessor.prepare_tree_features(
        X_train, X_val, X_test
    )
    pipeline = None  # Tree 모델은 별도 파이프라인을 사용하지 않음

    # 5. LightGBM 학습
    print("\n[Step 5] LightGBM 학습")
    models = get_models()
    lgb_model = {"LightGBM": models["LightGBM"]}

    trainer = ModelTrainer()
    results_df = trainer.train_models(
        models=lgb_model,
        X_train=X_train_t.values if hasattr(X_train_t, "values") else X_train_t,
        y_train=y_train.values,
        X_val=X_val_t.values if hasattr(X_val_t, "values") else X_val_t,
        y_val=y_val.values,
        X_test=X_test_t.values if hasattr(X_test_t, "values") else X_test_t,
        y_test=y_test.values,
        feature_names=preprocessor.candidate_features,
    )

    # 6. SHAP 분석 수행 (Test 데이터만)
    print("\n[Step 6] SHAP 분석 수행 (Test 데이터)")
    print("\n>> Test 데이터에 대한 SHAP 분석...")
    explainer_test = trainer.analyze_shap(
        model_name="LightGBM",
        data_type="test",
        max_samples=1000,
        output_dir=str(PLOTS_DIR),  # shap_plots/ 폴더에만 저장
        save_plots=False,           # 기본 플롯은 저장하지 않고, 아래에서 필요한 것만 생성
    )

    # 7. 필요한 SHAP 플롯만 생성 (Summary + Bar)
    print("\n[Step 7] SHAP 플롯 생성 (Summary + Bar)")

    # 플롯용 배열 (numpy)로 변환
    X_test_plot = X_test_t.values if hasattr(X_test_t, "values") else X_test_t

    # 7-1. Summary Plot (dot)
    print("\n>> Summary Plot 생성...")
    explainer_test.plot_summary(
        X=X_test_plot[:1000],
        plot_type="dot",
        max_display=20,
        save_path=str(PLOTS_DIR / "summary_test.png"),
        show=False,
    )

    # 7-2. Bar Plot (Feature Importance)
    print("\n>> Bar Plot 생성...")
    explainer_test.plot_bar(
        X=X_test_plot[:1000],
        max_display=20,
        save_path=str(PLOTS_DIR / "bar_test.png"),
        show=False,
    )

    # 8. 피처 중요도 추출
    print("\n[Step 8] 피처 중요도 계산 및 출력")
    importance_df = explainer_test.get_feature_importance(top_n=15)

    print("\n" + "=" * 70)
    print(">> SHAP 분석 예시 종료!")
    print("=" * 70)
    print("\n생성된 플롯 경로:")
    print("   - ./shap_plots/summary_test.png")
    print("   - ./shap_plots/bar_test.png")
    print("\n상위 중요 피처:")
    print(importance_df.head(10))

    return explainer_test, importance_df


if __name__ == "__main__":
    # 메뉴 없이 바로 전체 예시 실행
    explainer, importance_df = example_shap_analysis()

    print("\n" + "=" * 70)
    print("SHAP 플롯 사용 가이드:")
    print("=" * 70)
    print(
        """
    1. Summary Plot (summary_test.png):
    - Test 데이터 전체에 대한 피처별 SHAP 분포

    2. Bar Plot (bar_test.png):
    - Test 기준 피처 중요도 순위 (평균 |SHAP| 기준)
    """
    )
