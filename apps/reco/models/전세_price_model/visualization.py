"""
전세 가격 예측 모델 시각화 모듈
"""
import os
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns


def setup_matplotlib_korean():
    """
    Matplotlib에서 한글 폰트를 설정합니다.
    """
    plt.rc('font', family='Malgun Gothic')
    plt.rc('axes', unicode_minus=False)


def set_matplotlib_backend(backend='Agg'):
    """
    Matplotlib backend를 설정합니다.
    'Agg'로 설정하면 화면에 표시하지 않고 파일로만 저장합니다.

    Args:
        backend: matplotlib backend ('Agg', 'TkAgg' 등)
    """
    matplotlib.use(backend, force=True)


# ==================== EDA 시각화 ====================

def plot_target_distribution(df: pd.DataFrame, target: str = "평당가",
                               bins: int = 50, output_path: str = None, show: bool = False):
    """
    타겟 변수의 분포를 히스토그램으로 그립니다.

    Args:
        df: 데이터프레임
        target: 타겟 컬럼명
        bins: 히스토그램 구간 수
        output_path: 저장할 파일 경로
        show: 화면에 표시할지 여부
    """
    setup_matplotlib_korean()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 원본 분포
    axes[0].hist(df[target], bins=bins, edgecolor='black', alpha=0.7)
    axes[0].set_title("평당가 분포")
    axes[0].set_xlabel("평당가 (만원)")
    axes[0].set_ylabel("빈도")
    axes[0].grid(True, alpha=0.3)

    # 로그 변환된 분포
    axes[1].hist(np.log1p(df[target]), bins=bins, edgecolor='black', alpha=0.7)
    axes[1].set_title("로그 변환된 평당가 분포")
    axes[1].set_xlabel("log(평당가 + 1)")
    axes[1].set_ylabel("빈도")
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
    if show:
        plt.show()
    else:
        plt.close()


def plot_gu_average_price(df: pd.DataFrame, target: str = "평당가",
                          top_n: int = 10, output_path: str = None, show: bool = False):
    """
    구별 평균 평당가를 막대 그래프로 그립니다.

    Args:
        df: 데이터프레임
        target: 타겟 컬럼명
        top_n: 상위 N개 구 표시
        output_path: 저장할 파일 경로
        show: 화면에 표시할지 여부
    """
    setup_matplotlib_korean()

    # 구별 평균 평당가 계산
    gu_avg = df.groupby("구")[target].mean().sort_values(ascending=False).head(top_n)

    plt.figure(figsize=(10, 6))
    gu_avg.plot(kind='barh', color='skyblue', edgecolor='black')
    plt.title(f"구별 평균 평당가 TOP {top_n}")
    plt.xlabel("평균 평당가 (만원)")
    plt.ylabel("구")
    plt.gca().invert_yaxis()
    plt.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
    if show:
        plt.show()
    else:
        plt.close()


def plot_correlation_heatmap(X: pd.DataFrame, output_path: str = None, show: bool = False):
    """
    피처 간 상관관계 히트맵을 그립니다.

    Args:
        X: 특성 데이터프레임
        output_path: 저장할 파일 경로
        show: 화면에 표시할지 여부
    """
    setup_matplotlib_korean()

    correlation_matrix = X.corr()

    plt.figure(figsize=(14, 12))
    mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
    sns.heatmap(
        correlation_matrix,
        mask=mask,
        annot=True,
        fmt='.2f',
        cmap='coolwarm',
        center=0,
        square=True,
        linewidths=1,
        cbar_kws={"shrink": 0.8},
        vmin=-1,
        vmax=1
    )
    plt.title("피처 간 상관관계 히트맵", fontsize=16, pad=20)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
    if show:
        plt.show()
    else:
        plt.close()


# ==================== 모델 결과 시각화 ====================

def plot_actual_vs_predicted(y_test, y_pred, output_path: str = None, show: bool = False):
    """
    실제값 vs 예측값 산점도를 그립니다.

    Args:
        y_test: 실제값
        y_pred: 예측값
        output_path: 저장할 파일 경로
        show: 화면에 표시할지 여부
    """
    setup_matplotlib_korean()

    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred, alpha=0.5, s=30)

    max_val = max(y_test.max(), y_pred.max())
    min_val = min(y_test.min(), y_pred.min())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='y = x')

    plt.xlabel("실제 평당가 (만원)")
    plt.ylabel("예측 평당가 (만원)")
    plt.title("실제값 vs 예측값")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
    if show:
        plt.show()
    else:
        plt.close()


def plot_error_distribution(y_test, y_pred, output_path: str = None, show: bool = False):
    """
    오차율 분포를 히스토그램으로 그립니다.

    Args:
        y_test: 실제값
        y_pred: 예측값
        output_path: 저장할 파일 경로
        show: 화면에 표시할지 여부
    """
    setup_matplotlib_korean()

    error_rate = np.abs((y_test - y_pred) / y_test) * 100
    mape = np.mean(error_rate)

    plt.figure(figsize=(10, 6))
    plt.hist(error_rate, bins=50, edgecolor='black', alpha=0.7, color='steelblue')
    plt.xlim(0, 100)
    plt.axvline(mape, color='red', linestyle='--', linewidth=2, label=f'평균 오차율: {mape:.1f}%')
    plt.title("오차율(%) 분포")
    plt.xlabel("오차율 (%)")
    plt.ylabel("빈도")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
    if show:
        plt.show()
    else:
        plt.close()


def plot_feature_importance(model, X: pd.DataFrame, output_path: str = None, show: bool = False):
    """
    특성 중요도를 막대 그래프로 그립니다.

    Args:
        model: 학습된 모델
        X: 특성 데이터프레임
        output_path: 저장할 파일 경로
        show: 화면에 표시할지 여부
    """
    setup_matplotlib_korean()

    feature_importance = pd.DataFrame({
        '특성': X.columns,
        '중요도': model.feature_importances_
    }).sort_values('중요도', ascending=False)

    plt.figure(figsize=(10, 6))
    sns.barplot(data=feature_importance, x='중요도', y='특성', hue='특성', palette='viridis', legend=False)
    plt.title("특성 중요도")
    plt.xlabel("중요도")
    plt.ylabel("특성")
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
    if show:
        plt.show()
    else:
        plt.close()

    return feature_importance


def plot_shap_analysis(model, X_test, output_dir: str = None, max_samples: int = 100):
    """
    SHAP 분석을 수행하고 결과를 시각화합니다.

    Args:
        model: 학습된 모델
        X_test: 테스트 특성
        output_dir: 저장할 디렉토리
        max_samples: 최대 샘플 수

    Returns:
        list: 저장된 파일 경로 리스트
    """
    try:
        import shap
    except ImportError:
        print("SHAP 라이브러리가 설치되지 않았습니다. pip install shap")
        return []

    setup_matplotlib_korean()
    saved_files = []

    # 샘플링하여 계산 속도 향상
    X_test_sample = X_test.sample(min(max_samples, len(X_test)), random_state=42)

    # TreeExplainer 사용 (XGBoost용)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test_sample)

    # SHAP 요약 플롯 (bar)
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values, X_test_sample, plot_type="bar", show=False)
    plt.title("SHAP Feature Importance", fontsize=16, pad=20)
    plt.tight_layout()

    if output_dir:
        filepath = os.path.join(output_dir, "01_shap_importance_bar.png")
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        saved_files.append(filepath)
    plt.close()

    # SHAP 상세 플롯 (dot)
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values, X_test_sample, plot_type="dot", max_display=10, show=False)
    plt.title("SHAP Summary Plot (Top 10 Features)", fontsize=16, pad=20)
    plt.tight_layout()

    if output_dir:
        filepath = os.path.join(output_dir, "02_shap_summary.png")
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        saved_files.append(filepath)
    plt.close()

    return saved_files


def plot_permutation_importance(perm_importance, feature_names, output_path: str = None, show: bool = False):
    """
    Permutation Importance를 막대 그래프로 그립니다.

    Args:
        perm_importance: permutation_importance 결과
        feature_names: 특성 이름 리스트
        output_path: 저장할 파일 경로
        show: 화면에 표시할지 여부
    """
    setup_matplotlib_korean()

    perm_df = pd.DataFrame({
        'feature': feature_names,
        'importance_mean': perm_importance.importances_mean,
        'importance_std': perm_importance.importances_std
    }).sort_values('importance_mean', ascending=False)

    plt.figure(figsize=(10, 6))
    sns.barplot(data=perm_df, x='importance_mean', y='feature', palette='viridis', legend=False)
    plt.title("Permutation Feature Importance", fontsize=16, pad=20)
    plt.xlabel("Importance (R² decrease)")
    plt.ylabel("Feature")
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
    if show:
        plt.show()
    else:
        plt.close()

    return perm_df


# ==================== 결과 저장 함수 ====================

def save_all_eda_plots(df: pd.DataFrame, target: str = "평당가", output_dir: str = None):
    """
    모든 EDA 플롯을 저장합니다.

    Args:
        df: 데이터프레임
        target: 타겟 컬럼명
        output_dir: 저장할 디렉토리

    Returns:
        list: 저장된 파일 경로 리스트
    """
    if output_dir is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, "results", "images")
    os.makedirs(output_dir, exist_ok=True)

    saved_files = []

    # 평당가 분포
    filepath = os.path.join(output_dir, "01_평당가_분포.png")
    plot_target_distribution(df, target, output_path=filepath)
    saved_files.append(filepath)

    # 구별 평균 평당가
    filepath = os.path.join(output_dir, "02_구별_평균_평당가.png")
    plot_gu_average_price(df, target, output_path=filepath)
    saved_files.append(filepath)

    return saved_files


def save_model_result_plots(y_test, y_pred, output_dir: str = None):
    """
    모델 결과 플롯을 저장합니다.

    Args:
        y_test: 실제값
        y_pred: 예측값
        output_dir: 저장할 디렉토리

    Returns:
        list: 저장된 파일 경로 리스트
    """
    if output_dir is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, "results", "images")
    os.makedirs(output_dir, exist_ok=True)

    saved_files = []

    # 실제값 vs 예측값
    filepath = os.path.join(output_dir, "03_실제값_vs_예측값.png")
    plot_actual_vs_predicted(y_test, y_pred, output_path=filepath)
    saved_files.append(filepath)

    # 오차율 분포
    filepath = os.path.join(output_dir, "04_오차율_분포.png")
    plot_error_distribution(y_test, y_pred, output_path=filepath)
    saved_files.append(filepath)

    return saved_files


def save_shap_plots(model, X_test, output_dir: str = None):
    """
    SHAP 분석 플롯을 저장합니다.

    Args:
        model: 학습된 모델
        X_test: 테스트 특성
        output_dir: 저장할 디렉토리

    Returns:
        list: 저장된 파일 경로 리스트
    """
    if output_dir is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, "results", "images")
    os.makedirs(output_dir, exist_ok=True)

    return plot_shap_analysis(model, X_test, output_dir)

