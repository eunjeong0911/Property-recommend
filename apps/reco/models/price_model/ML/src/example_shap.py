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

# 1) 한글 폰트 설정 (Windows: 맑은 고딕)
plt.rcParams['font.family'] = 'Malgun Gothic'  # 또는 '맑은 고딕'

# 2) 마이너스(-) 깨짐 방지
mpl.rcParams['axes.unicode_minus'] = False

ML_ROOT = Path(__file__).resolve().parent.parent 
PLOTS_DIR = ML_ROOT / "shap_plots"


def example_shap_analysis():
    """전체 파이프라인을 통해 SHAP 분석을 수행하는 예시"""

    print("\n" + "=" * 70)
    print("▶ SHAP 분석 예시 실행")
    print("=" * 70)

    # 1. 데이터 로딩
    print("\n[Step 1] 데이터 로딩")
    data_dir = "C:/dev/SKN18-FINAL-1TEAM/data/actual_transaction_price"
    loader = DataLoader(data_dir)
    train_df, test_df = loader.load_train_test(
        train_filename="월세_train(24.08~25.08).csv",
        test_filename="월세_test(25.09~25.10).csv",
    )

    # 2. 전처리 및 피처 엔지니어링
    print("\n[Step 2] 타깃 생성 및 고급 피처 엔지니어링")
    preprocessor = PriceDataPreprocessor()

    train_df = preprocessor.create_target(train_df)
    test_df = preprocessor.create_target(test_df)

    train_df, test_df = preprocessor.advanced_feature_engineering(train_df, test_df)

    # 3. Train/Val 분할
    print("\n[Step 3] Train/Val 분할")
    X_train, y_train, X_val, y_val = preprocessor.prepare_train_test_split(
        train_df, split_date="2025-06"
    )

    # 테스트용 피처/타깃 분리
    X_test = test_df[preprocessor.candidate_features]
    y_test = test_df[preprocessor.target_log]

    # 4. Tree 모델용 피처 변환 (Label Encoding, No Scaling)
    print("\n[Step 4] Tree 모델용 피처 변환")
    X_train_t, X_val_t, X_test_t = preprocessor.prepare_tree_features(
        X_train, X_val, X_test
    )
    pipeline = None  # Tree 모델은 별도 파이프라인 사용 안 함

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

    # 6. SHAP 분석 실행
    print("\n[Step 6] SHAP 분석 실행")

    # 6-1. Test 데이터에 대해 SHAP 분석
    print("\n▶ Test 데이터 SHAP 분석...")
    explainer_test = trainer.analyze_shap(
        model_name="LightGBM",
        data_type="test",
        max_samples=1000,
        output_dir="/shap_plots/test",
        save_plots=True,
    )

    # 6-2. Train 데이터에 대해 SHAP 분석 (옵션)
    print("\n▶ Train 데이터 SHAP 분석...")
    explainer_train = trainer.analyze_shap(
        model_name="LightGBM",
        data_type="train",
        max_samples=500,
        output_dir="./shap_plots/train",
        save_plots=True,
    )

    # 7. 개별 커스텀 플롯 생성
    print("\n[Step 7] 개별 SHAP 플롯 생성")

    # 플롯용 입력 배열 (numpy)로 변환
    X_test_plot = X_test_t.values if hasattr(X_test_t, "values") else X_test_t

    # 7-1. Summary Plot (dot)
    print("\n▶ Summary Plot 생성...")
    explainer_test.plot_summary(
        X=X_test_plot[:1000],
        plot_type="dot",
        max_display=20,
        save_path=str(PLOTS_DIR / "custom_summary.png"),
        show=False,
    )

    # 7-2. Bar Plot (Feature Importance)
    print("\n▶ Bar Plot 생성...")
    explainer_test.plot_bar(
        X=X_test_plot[:1000],
        max_display=20,
        save_path=str(PLOTS_DIR / "shap_plots/custom_bar.png"),
        show=False,
    )

    # 7-3. Waterfall Plot (개별 샘플)
    print("\n▶ Waterfall Plot 생성...")
    for idx in [0, 1, 2]:
        explainer_test.plot_waterfall(
            X=X_test_plot[:1000],
            sample_idx=idx,
            max_display=15,
            save_path=str(PLOTS_DIR / "./shap_plots/custom_waterfall_sample_{idx}.png"),
            show=False,
        )

    # 7-4. Force Plot (개별 샘플)
    print("\n▶ Force Plot 생성...")
    explainer_test.plot_force(
        X=X_test_plot[:1000],
        sample_idx=0,
        matplotlib=True,
        save_path=str(PLOTS_DIR / "./shap_plots/custom_force.png"),
        show=False,
    )

    # 8. 피처 중요도 출력
    print("\n[Step 8] 피처 중요도 계산 및 출력")
    importance_df = explainer_test.get_feature_importance(top_n=15)

    print("\n" + "=" * 70)
    print("✅ SHAP 분석 예시 완료!")
    print("=" * 70)
    print("\n생성된 플롯 경로:")
    print("   - ./shap_plots/test/")
    print("   - ./shap_plots/train/")
    print("   - ./shap_plots/custom_*.png")
    print("\n상위 중요 피처:")
    print(importance_df.head(10))

    return explainer_test, importance_df


def quick_shap_analysis():
    """
    모델을 빠르게 학습하고 SHAP 분석만 수행하는 간단 예시
    """
    print("\n" + "=" * 70)
    print("🚀 빠른 SHAP 분석 (LightGBM 단일 모델)")
    print("=" * 70)

    # 1. 데이터 로딩 및 전처리
    data_dir = "C:/dev/SKN18-FINAL-1TEAM/data/actual_transaction_price"
    loader = DataLoader(data_dir)
    train_df, test_df = loader.load_train_test(
        train_filename="월세_train(24.08~25.08).csv",
        test_filename="월세_test(25.09~25.10).csv",
    )

    preprocessor = PriceDataPreprocessor()
    train_df = preprocessor.create_target(train_df)
    test_df = preprocessor.create_target(test_df)
    train_df, test_df = preprocessor.advanced_feature_engineering(train_df, test_df)

    X_train, y_train, X_val, y_val = preprocessor.prepare_train_test_split(
        train_df, split_date="2025-06"
    )
    X_test = test_df[preprocessor.candidate_features]
    y_test = test_df[preprocessor.target_log]

    # Tree 모델용 피처 변환
    X_train_t, X_val_t, X_test_t = preprocessor.prepare_tree_features(
        X_train, X_val, X_test
    )

    # 2. LightGBM 학습
    print("\n모델 학습 중...")
    models = get_models()
    trainer = ModelTrainer()

    lgb_model = {"LightGBM": models["LightGBM"]}

    trainer.train_models(
        models=lgb_model,
        X_train=X_train_t.values if hasattr(X_train_t, "values") else X_train_t,
        y_train=y_train.values,
        X_val=X_val_t.values if hasattr(X_val_t, "values") else X_val_t,
        y_val=y_val.values,
        X_test=X_test_t.values if hasattr(X_test_t, "values") else X_test_t,
        y_test=y_test.values,
        feature_names=preprocessor.candidate_features,
    )

    # 3. SHAP 분석
    print("\n▶ SHAP 분석 실행...")
    explainer = trainer.analyze_shap(
        data_type="test",
        max_samples=1000,
        output_dir="./shap_plots_quick",
        save_plots=True,
    )

    print("\n✅ 완료! 결과는 ./shap_plots_quick/ 에 저장되었습니다.")

    return explainer


if __name__ == "__main__":
    # 간단한 CLI 선택
    print("=" * 70)
    print("SHAP 분석 예시를 실행합니다.")
    print("=" * 70)
    print("\n1. 전체 예시 (학습 + 다양한 플롯)")
    print("2. 빠른 예시 (간단 학습 + SHAP)")

    choice = input("\n선택하세요 (1 또는 2, 기본값 1): ").strip()

    if choice == "2":
        explainer = quick_shap_analysis()
    else:
        explainer, importance_df = example_shap_analysis()

    print("\n" + "=" * 70)
    print("SHAP 플롯 사용 가이드:")
    print("=" * 70)
    print(
        """
    1. Summary Plot (dot):
       - 모든 피처의 SHAP 분포 시각화
       - 색상: 피처 값의 크기(높음=빨강, 낮음=파랑)
       - x축: SHAP 값(모델 예측에 미치는 영향)

    2. Bar Plot:
       - 피처 중요도 순위
       - 절대값 기준 평균 SHAP 값 막대 그래프

    3. Waterfall Plot:
       - 개별 샘플에 대한 예측 분해
       - 어떤 피처가 예측을 얼마나 올리고/내리는지 확인

    4. Force Plot:
       - 개별 샘플의 예측을 직관적으로 표현
       - 빨간색: 예측을 키우는 방향의 피처
       - 파란색: 예측을 줄이는 방향의 피처
    """
    )
