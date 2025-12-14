from pathlib import Path

from data_loader import DataLoader
from preprocessor import PriceDataPreprocessor
from trainer import ModelTrainer
import matplotlib.pyplot as plt
import matplotlib as mpl

# 1) 폰트 설정
plt.rcParams["font.family"] = "Malgun Gothic" 

# 2) 마이너스(-) 깨짐 방지
mpl.rcParams["axes.unicode_minus"] = False

# 경로 설정
ML_ROOT = Path(__file__).resolve().parent.parent
PLOTS_DIR = ML_ROOT / "shap_plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# 저장된 모델 경로
MODEL_DIR = ML_ROOT / "model"
MODEL_PATH = MODEL_DIR / "price_model_lightgbm.pkl"


def example_shap_analysis():
    """저장된 모델을 이용해 Test 데이터 기준 SHAP 분석"""

    print("\n" + "=" * 70)
    print(">> 저장된 모델 기반 SHAP 분석 예시 실행")
    print("=" * 70)

    # 1. 데이터 로딩
    print("\n[Step 1] 데이터 로딩")
    data_dir = "C:/dev/SKN18-FINAL-1TEAM/data/actual_transaction_price"
    loader = DataLoader(data_dir)
    train_df, test_df = loader.load_train_test(
        train_filename="월세_train(24.08~25.08).csv",
        test_filename="월세_test(25.09~25.10).csv",
    )

    # 2. 타깃 생성 및 고급 피처 엔지니어링
    print("\n[Step 2] 타깃 생성 및 고급 피처 엔지니어링")
    preprocessor = PriceDataPreprocessor()

    # 타깃 생성 (Train: 전체 통계 사용, Test: Train 통계 사용)
    train_df = preprocessor.create_target(train_df)
    test_df = preprocessor.create_target(
        test_df,
        train_stats={"gu_quantiles": preprocessor.train_gu_quantiles},
    )

    train_df, test_df = preprocessor.advanced_feature_engineering(train_df, test_df)

    # 3. Train/Val 분할
    print("\n[Step 3] Train/Val 분할")
    X_train, y_train, X_val, y_val = preprocessor.prepare_train_test_split(
        train_df, split_date="2025-06"
    )

    # 4. Test 피처 준비
    print("\n[Step 4] Test 피처 준비")
    X_test = test_df[preprocessor.candidate_features]
    y_test = test_df[preprocessor.target_name]

    # 5. Tree 모델용 피처 변환 (Label Encoding, No Scaling)
    print("\n[Step 5] Tree 모델용 피처 변환")
    X_train_t, X_val_t, X_test_t = preprocessor.prepare_tree_features(
        X_train, X_val, X_test
    )

    # 6. 저장된 모델 로드
    print("\n[Step 6] 저장된 모델 로드")
    trainer = ModelTrainer()
    model_bundle = trainer.load_model(str(MODEL_PATH))

    # trainer에 SHAP용 상태 세팅
    trainer.best_model = model_bundle["model"]
    trainer.best_model_name = model_bundle["model_name"]

    trainer.X_train = (
        X_train_t.values if hasattr(X_train_t, "values") else X_train_t
    )
    trainer.X_val = X_val_t.values if hasattr(X_val_t, "values") else X_val_t
    trainer.X_test = X_test_t.values if hasattr(X_test_t, "values") else X_test_t
    trainer.feature_names = preprocessor.candidate_features

    # 7. SHAP 분석 수행 (Test 데이터만, 기본 플롯 저장은 끔)
    print("\n[Step 7] SHAP 값 계산 (Test 데이터)")
    explainer_test = trainer.analyze_shap(
        model_name=None,        # best_model 사용
        data_type="test",
        max_samples=1000,
        output_dir=str(PLOTS_DIR),
        save_plots=False,       # 기본 save_all_plots 비활성화
    )

    # 8. 필요한 SHAP 플롯만 생성 (Summary + Bar)
    print("\n[Step 8] SHAP 플롯 생성 (Summary + Bar)")

    # 플롯용 배열 (numpy)로 변환
    X_test_plot = X_test_t.values if hasattr(X_test_t, "values") else X_test_t

    # 8-1. Summary Plot (dot)
    print("\n>> Summary Plot 생성...")
    explainer_test.plot_summary(
        X=X_test_plot[:1000],
        plot_type="dot",
        max_display=20,
        save_path=str(PLOTS_DIR / "summary_test.png"),
        show=False,
    )

    # 8-2. Bar Plot (Feature Importance)
    print("\n>> Bar Plot 생성...")
    explainer_test.plot_bar(
        X=X_test_plot[:1000],
        max_display=20,
        save_path=str(PLOTS_DIR / "bar_test.png"),
        show=False,
    )

    # 9. 피처 중요도 추출
    print("\n[Step 9] 피처 중요도 계산 및 출력")
    importance_df = explainer_test.get_feature_importance(top_n=15)

    print("\n" + "=" * 70)
    print(">> 저장된 모델 기반 SHAP 분석 예시 종료!")
    print("=" * 70)
    print("\n생성된 플롯 경로:")
    print("   - ./shap_plots/summary_test.png")
    print("   - ./shap_plots/bar_test.png")
    print("\n상위 중요 피처:")
    print(importance_df.head(10))

    return explainer_test, importance_df


if __name__ == "__main__":
    # 메뉴 없이 바로 예시 실행
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
