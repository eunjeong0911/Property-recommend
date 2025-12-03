"""
시각화 모듈
EDA 및 모델 결과 시각화를 위한 함수들을 포함합니다.
"""
import os
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import shap


def setup_matplotlib_korean():
    """
    Matplotlib에서 한글 폰트를 설정합니다.
    """
    plt.rc('font', family='Malgun Gothic')   # 한글 폰트 적용
    plt.rc('axes', unicode_minus=False)      # 마이너스 깨짐 방지


def set_matplotlib_backend(backend='Agg'):
    """
    Matplotlib backend를 설정합니다.
    'Agg'로 설정하면 화면에 표시하지 않고 파일로만 저장합니다.

    Args:
        backend: matplotlib backend ('Agg', 'TkAgg' 등)
    """
    matplotlib.use(backend, force=True)


# ==================== EDA 시각화 ====================

def plot_correlation_heatmap(df: pd.DataFrame, figsize=(18, 14), show=False):
    """
    전체 특성의 상관관계 히트맵을 그립니다.

    Args:
        df: 데이터프레임
        figsize: 그림 크기
        show: 화면에 표시할지 여부 (기본값 False)
    """
    setup_matplotlib_korean()

    plt.figure(figsize=figsize)

    corr = df.corr(numeric_only=True)

    sns.heatmap(
        corr,
        annot=False,
        cmap="coolwarm",
        linewidths=0.5,
        square=False
    )

    plt.title("특성 상관관계 히트맵", fontsize=18)
    plt.tight_layout()
    if show:
        plt.show()


def plot_top_correlation_heatmap(df: pd.DataFrame, target: str = "환산보증금",
                                  top_n: int = 20, figsize=(12, 10), show=False):
    """
    타겟과 상관관계가 높은 상위 N개 특성의 히트맵을 그립니다.

    Args:
        df: 데이터프레임
        target: 타겟 컬럼명
        top_n: 상위 N개 특성
        figsize: 그림 크기
        show: 화면에 표시할지 여부 (기본값 False)
    """
    setup_matplotlib_korean()

    # 숫자 컬럼만 상관관계 계산
    corr = df.corr(numeric_only=True)

    # 타겟과 상관관계 높은 상위 N개 선택
    top_cols = corr[target].abs().sort_values(ascending=False).head(top_n).index.tolist()

    # Top N 컬럼들만 슬라이싱해서 히트맵
    plt.figure(figsize=figsize)
    sns.heatmap(
        corr.loc[top_cols, top_cols],
        annot=True,
        cmap="coolwarm",
        linewidths=0.5
    )
    plt.title(f"'{target}'와 상관관계 상위 {top_n}개 히트맵", fontsize=16)
    plt.tight_layout()
    if show:
        plt.show()


def plot_feature_vs_target_regplot(df: pd.DataFrame, feature_list: list,
                                     target: str = "환산보증금"):
    """
    각 특성과 타겟의 관계를 회귀선 포함 산점도로 그립니다.

    Args:
        df: 데이터프레임
        feature_list: 특성 리스트
        target: 타겟 컬럼명
    """
    setup_matplotlib_korean()

    for col in feature_list:
        plt.figure(figsize=(8, 6))
        sns.regplot(
            x=df[col],
            y=df[target],
            scatter_kws={"alpha": 0.3, "s": 20},
            line_kws={"color": "red"}
        )
        plt.title(f"{col} vs {target} (선형회귀선 포함)", fontsize=14)
        plt.xlabel(col)
        plt.ylabel(target)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()


def plot_numerical_boxplots(df: pd.DataFrame, num_cols: list):
    """
    숫자형 특성들의 박스플롯을 그립니다.

    Args:
        df: 데이터프레임
        num_cols: 숫자형 컬럼 리스트
    """
    setup_matplotlib_korean()

    for col in num_cols:
        plt.figure(figsize=(10, 4))
        sns.boxplot(x=df[col], color='goldenrod')
        plt.title(f"{col} Boxplot", fontsize=15)
        plt.xlabel(col)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()


def plot_target_distribution(df: pd.DataFrame, target: str = "환산보증금",
                               bins: int = 50, show=False):
    """
    타겟 변수의 분포를 히스토그램으로 그립니다.

    Args:
        df: 데이터프레임
        target: 타겟 컬럼명
        bins: 히스토그램 bin 개수
        show: 화면에 표시할지 여부 (기본값 False)
    """
    setup_matplotlib_korean()

    plt.figure(figsize=(10, 5))
    sns.histplot(df[target], bins=bins, kde=True)
    plt.title(f"{target} 분포")
    plt.tight_layout()
    if show:
        plt.show()


def plot_log_target_distribution(df: pd.DataFrame, target: str = "환산보증금",
                                   bins: int = 50, show=False):
    """
    로그 변환된 타겟 변수의 분포를 히스토그램으로 그립니다.

    Args:
        df: 데이터프레임
        target: 타겟 컬럼명
        bins: 히스토그램 bin 개수
        show: 화면에 표시할지 여부 (기본값 False)
    """
    setup_matplotlib_korean()

    plt.figure(figsize=(10, 5))
    sns.histplot(np.log1p(df[target]), bins=bins, kde=True)
    plt.title(f"로그 변환된 {target} 분포")
    plt.tight_layout()
    if show:
        plt.show()


def plot_area_vs_target_by_floor(df: pd.DataFrame, area_col: str = "전용면적_평",
                                   target: str = "환산보증금",
                                   floor_col: str = "층"):
    """
    평수와 타겟의 관계를 층별로 색상을 다르게 하여 산점도로 그립니다.

    Args:
        df: 데이터프레임
        area_col: 면적 컬럼명
        target: 타겟 컬럼명
        floor_col: 층 컬럼명
    """
    setup_matplotlib_korean()

    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=df,
        x=area_col,
        y=target,
        hue=floor_col,
        palette="viridis",
        alpha=0.5
    )
    plt.title(f"{area_col} vs {target} ({floor_col}에 따라 색상)")
    plt.tight_layout()
    plt.show()


def plot_price_per_pyeong_vs_target(df: pd.DataFrame,
                                      price_per_pyeong_col: str = "평당가",
                                      target: str = "환산보증금"):
    """
    평당가와 타겟의 관계를 로그 스케일로 산점도를 그립니다.

    Args:
        df: 데이터프레임
        price_per_pyeong_col: 평당가 컬럼명
        target: 타겟 컬럼명
    """
    setup_matplotlib_korean()

    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x=price_per_pyeong_col, y=target, alpha=0.4)
    plt.xscale("log")
    plt.yscale("log")
    plt.title(f"{price_per_pyeong_col} vs {target} (로그 스케일)")
    plt.tight_layout()
    plt.show()


def plot_rooms_vs_target_boxplot(df: pd.DataFrame, rooms_col: str = "방수",
                                   target: str = "환산보증금"):
    """
    방수별 타겟의 분포를 박스플롯으로 그립니다.

    Args:
        df: 데이터프레임
        rooms_col: 방수 컬럼명
        target: 타겟 컬럼명
    """
    setup_matplotlib_korean()

    plt.figure(figsize=(10, 5))
    sns.boxplot(data=df, x=rooms_col, y=target)
    plt.title(f"{rooms_col}별 {target} 분포")
    plt.tight_layout()
    plt.show()


# ==================== 모델 결과 시각화 ====================

def plot_error_rate_histogram(df_compare: pd.DataFrame, bins=None, show=True):
    """
    오차율 분포를 히스토그램으로 그립니다.

    Args:
        df_compare: 실제값, 예측값, 오차율이 포함된 데이터프레임
        bins: 히스토그램 bins (기본값: 0~100%, 5% 간격)
        show: 그래프를 화면에 표시할지 여부 (기본값: True)
    """
    setup_matplotlib_korean()

    if bins is None:
        bins = np.arange(0, 105, 5)

    plt.figure(figsize=(10, 6))
    sns.histplot(
        df_compare["오차율(%)"],
        bins=bins,
        kde=True,
        color='steelblue',
        edgecolor='black'
    )

    plt.xlim(0, 100)
    plt.xticks(bins)

    plt.title("오차율(%) 분포 히스토그램 (5% 단위, Max 100%)", fontsize=16)
    plt.xlabel("오차율(%)")
    plt.ylabel("빈도")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    if show:
        plt.show()


def plot_error_rate_boxplot(df_compare: pd.DataFrame, show=True):
    """
    오차율의 박스플롯을 그립니다.

    Args:
        df_compare: 실제값, 예측값, 오차율이 포함된 데이터프레임
        show: 그래프를 화면에 표시할지 여부 (기본값: True)
    """
    setup_matplotlib_korean()

    plt.figure(figsize=(8, 4))
    sns.boxplot(x=df_compare["오차율(%)"], color='orange')

    plt.title("오차율(%) Boxplot", fontsize=15)
    plt.xlabel("오차율(%)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    if show:
        plt.show()


def plot_actual_vs_predicted(y_test, y_pred, show=True):
    """
    실제값과 예측값의 산점도를 그립니다.

    Args:
        y_test: 실제값
        y_pred: 예측값
        show: 그래프를 화면에 표시할지 여부 (기본값 True)
    """
    setup_matplotlib_korean()

    plt.figure(figsize=(8, 8))
    sns.scatterplot(x=y_test, y=y_pred, alpha=0.4, s=30)

    max_val = max(max(y_test), max(y_pred))
    min_val = min(min(y_test), min(y_pred))
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='y = x')

    plt.xlabel("실제값")
    plt.ylabel("예측값")
    plt.title("실제값 vs 예측값 산점도 (전체 테스트셋)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    if show:
        plt.show()


# ==================== SHAP 시각화 ====================

def initialize_shap():
    """
    SHAP을 초기화합니다.
    """
    shap.initjs()


def create_shap_explainer(model, X_test):
    """
    SHAP explainer를 생성하고 SHAP 값을 계산합니다.

    Args:
        model: 학습된 모델
        X_test: 테스트 데이터

    Returns:
        tuple: (explainer, shap_values)
    """
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    return explainer, shap_values


def plot_shap_summary_bar(shap_values, X_test, max_display: int = 20):
    """
    SHAP 중요도를 막대 그래프로 표시합니다.

    Args:
        shap_values: SHAP 값
        X_test: 테스트 데이터
        max_display: 표시할 최대 특성 개수
    """
    shap.summary_plot(shap_values, X_test, plot_type="bar", max_display=max_display)


def plot_shap_summary(shap_values, X_test, max_display: int = 20):
    """
    SHAP 요약 플롯을 표시합니다.

    Args:
        shap_values: SHAP 값
        X_test: 테스트 데이터
        max_display: 표시할 최대 특성 개수
    """
    shap.summary_plot(shap_values, X_test, max_display=max_display)


def plot_shap_force(explainer, shap_values, X_test, sample_idx: int = 0):
    """
    개별 샘플의 SHAP force plot을 표시합니다.

    Args:
        explainer: SHAP explainer
        shap_values: SHAP 값
        X_test: 테스트 데이터
        sample_idx: 샘플 인덱스
    """
    idx = X_test.index[sample_idx]
    shap.force_plot(
        explainer.expected_value,
        shap_values[X_test.index.get_loc(idx)],
        X_test.loc[idx],
        matplotlib=True
    )


# ==================== 편의 함수 ====================

def plot_all_eda(df_ml: pd.DataFrame):
    """
    모든 EDA 시각화를 수행합니다.

    Args:
        df_ml: 머신러닝용 데이터프레임
    """
    target = "환산보증금"

    feature_list = [
        "전용면적_평",
        "전용면적_m2",
        "평당가",
        "관리비",
        "건축물용도",
        "건물형태",
        "층",
        "방수",
        "욕실수",
        "방형태",
        "구",
        "동"
    ]

    num_cols = [
        "환산보증금",
        "전용면적_평",
        "전용면적_m2",
        "평당가",
        "관리비",
        "층",
        "방수",
        "욕실수"
    ]

    print("=== 1. 전체 상관관계 히트맵 ===")
    plot_correlation_heatmap(df_ml, show=False)

    print("\n=== 2. Top 20 상관관계 히트맵 ===")
    plot_top_correlation_heatmap(df_ml, target, show=False)

    print("\n=== 3. 특성별 회귀선 포함 산점도 ===")
    plot_feature_vs_target_regplot(df_ml, feature_list, target)

    print("\n=== 4. 숫자형 특성 박스플롯 ===")
    plot_numerical_boxplots(df_ml, num_cols)

    print("\n=== 5. 타겟 분포 ===")
    plot_target_distribution(df_ml, target, show=False)

    print("\n=== 6. 로그 변환된 타겟 분포 ===")
    plot_log_target_distribution(df_ml, target, show=False)

    print("\n=== 7. 평수 vs 타겟 (층별) ===")
    plot_area_vs_target_by_floor(df_ml)

    print("\n=== 8. 평당가 vs 타겟 (로그 스케일) ===")
    plot_price_per_pyeong_vs_target(df_ml)

    print("\n=== 9. 방수별 타겟 박스플롯 ===")
    plot_rooms_vs_target_boxplot(df_ml)


def plot_model_results(y_test, y_pred, df_compare: pd.DataFrame, show=True):
    """
    모델 결과 시각화를 수행합니다.

    Args:
        y_test: 실제값
        y_pred: 예측값
        df_compare: 비교 데이터프레임
        show: 그래프를 화면에 표시할지 여부 (기본값 True)
    """
    print("=== 1. 오차율 히스토그램 ===")
    plot_error_rate_histogram(df_compare, show=show)

    print("\n=== 2. 오차율 박스플롯 ===")
    plot_error_rate_boxplot(df_compare, show=show)

    print("\n=== 3. 실제값 vs 예측값 산점도 ===")
    plot_actual_vs_predicted(y_test, y_pred, show=show)


def plot_shap_analysis(model, X_test):
    """
    SHAP 분석 시각화를 수행합니다.

    Args:
        model: 학습된 모델
        X_test: 테스트 데이터
    """
    print("=== SHAP 분석 시작 ===")
    initialize_shap()

    print("\nSHAP explainer 생성 중...")
    explainer, shap_values = create_shap_explainer(model, X_test)

    print("\n=== 1. SHAP 중요도 막대 그래프 ===")
    plot_shap_summary_bar(shap_values, X_test)

    print("\n=== 2. SHAP 요약 플롯 ===")
    plot_shap_summary(shap_values, X_test)

    print("\n=== 3. SHAP Force Plot (첫 번째 샘플) ===")
    plot_shap_force(explainer, shap_values, X_test, sample_idx=0)


def save_shap_plots(model, X_test, output_dir: str = None):
    """
    SHAP 분석 시각화를 수행하고 저장합니다.

    Args:
        model: 학습된 모델
        X_test: 테스트 데이터
        output_dir: 저장 디렉토리 (기본값: 현재 파일의 outputs/ 폴더)

    Returns:
        list: 저장된 파일 경로 리스트
    """
    # 이미지가 화면에 표시되지 않도록 설정
    original_backend = matplotlib.get_backend()
    set_matplotlib_backend('Agg')  # GUI 없이 파일로만 저장
    plt.ioff()

    if output_dir is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, "outputs", "shap")

    os.makedirs(output_dir, exist_ok=True)
    saved_files = []

    print("=== SHAP 분석 시작 ===")
    initialize_shap()

    print("\nSHAP explainer 생성 중...")
    explainer, shap_values = create_shap_explainer(model, X_test)

    # 1. SHAP 중요도 막대 그래프
    print("\n=== 1. SHAP 중요도 막대 그래프 저장 중 ===")
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_test, plot_type="bar", max_display=20, show=False)
    filepath = save_figure(output_dir=output_dir, filename="01_shap_importance_bar.png")
    saved_files.append(filepath)
    plt.close()

    # 2. SHAP 요약 플롯
    print("\n=== 2. SHAP 요약 플롯 저장 중 ===")
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_test, max_display=20, show=False)
    filepath = save_figure(output_dir=output_dir, filename="02_shap_summary.png")
    saved_files.append(filepath)
    plt.close()

    # backend 및 interactive mode 복원
    matplotlib.use(original_backend, force=True)
    plt.ion()

    print(f"\n✓ 총 {len(saved_files)}개의 SHAP 그래프 저장 완료")
    return saved_files


# ==================== 그래프 저장 ====================

def save_figure(fig=None, output_dir: str = None, filename: str = None, dpi: int = 300):
    """
    현재 그래프를 파일로 저장합니다.

    Args:
        fig: matplotlib figure 객체 (None이면 현재 figure 사용)
        output_dir: 저장 디렉토리 (기본값: 현재 파일의 outputs/ 폴더)
        filename: 저장할 파일명
        dpi: 해상도

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
        filename = f"plot_{timestamp}.png"

    # 전체 경로
    filepath = os.path.join(output_dir, filename)

    # 그래프 저장
    if fig is None:
        plt.savefig(filepath, dpi=dpi, bbox_inches='tight')
    else:
        fig.savefig(filepath, dpi=dpi, bbox_inches='tight')

    print(f"✓ 그래프 저장 완료: {filepath}")
    return filepath


def save_all_eda_plots(df_ml: pd.DataFrame, output_dir: str = None):
    """
    모든 EDA 시각화를 수행하고 저장합니다.

    Args:
        df_ml: 머신러닝용 데이터프레임
        output_dir: 저장 디렉토리 (기본값: 현재 파일의 outputs/ 폴더)

    Returns:
        list: 저장된 파일 경로 리스트
    """
    # 이미지가 화면에 표시되지 않도록 설정
    original_backend = matplotlib.get_backend()
    set_matplotlib_backend('Agg')  # GUI 없이 파일로만 저장
    plt.ioff() 

    if output_dir is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, "outputs", "eda")

    os.makedirs(output_dir, exist_ok=True)
    saved_files = []

    target = "환산보증금"
    feature_list = [
        "전용면적_평",
        "전용면적_m2",
        "평당가",
        "관리비",
        "건축물용도",
        "건물형태",
        "층",
        "방수",
        "욕실수",
        "방형태",
        "구",
        "동"
    ]

    # 1. 전체 상관관계 히트맵
    print("=== 1. 전체 상관관계 히트맵 저장 중 ===")
    plot_correlation_heatmap(df_ml, show=False)
    filepath = save_figure(output_dir=output_dir, filename="01_correlation_heatmap.png")
    saved_files.append(filepath)
    plt.close()

    # 2. Top 20 상관관계 히트맵
    print("\n=== 2. Top 20 상관관계 히트맵 저장 중 ===")
    plot_top_correlation_heatmap(df_ml, target, show=False)
    filepath = save_figure(output_dir=output_dir, filename="02_top_correlation_heatmap.png")
    saved_files.append(filepath)
    plt.close()

    # 3. 타겟 분포
    print("\n=== 3. 타겟 분포 저장 중 ===")
    plot_target_distribution(df_ml, target, show=False)
    filepath = save_figure(output_dir=output_dir, filename="03_target_distribution.png")
    saved_files.append(filepath)
    plt.close()

    # 4. 로그 변환된 타겟 분포
    print("\n=== 4. 로그 변환된 타겟 분포 저장 중 ===")
    plot_log_target_distribution(df_ml, target, show=False)
    filepath = save_figure(output_dir=output_dir, filename="04_log_target_distribution.png")
    saved_files.append(filepath)
    plt.close()

    # backend 및 interactive mode 복원
    matplotlib.use(original_backend, force=True)
    plt.ion()

    print(f"\n✓ 총 {len(saved_files)}개의 EDA 그래프 저장 완료")
    return saved_files


def save_model_result_plots(y_test, y_pred, df_compare: pd.DataFrame, output_dir: str = None):
    """
    모델 결과 시각화를 수행하고 저장합니다.

    Args:
        y_test: 실제값
        y_pred: 예측값
        df_compare: 비교 데이터프레임
        output_dir: 저장 디렉토리 (기본값: 현재 파일의 outputs/ 폴더)

    Returns:
        list: 저장된 파일 경로 리스트
    """
    # 이미지가 화면에 표시되지 않도록 설정
    original_backend = matplotlib.get_backend()
    set_matplotlib_backend('Agg')  # GUI 없이 파일로만 저장
    plt.ioff()  # interactive mode off

    if output_dir is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, "outputs", "results")

    os.makedirs(output_dir, exist_ok=True)
    saved_files = []

    # 1. 오차율 히스토그램
    print("=== 1. 오차율 히스토그램 저장 중 ===")
    plot_error_rate_histogram(df_compare, show=False)
    filepath = save_figure(output_dir=output_dir, filename="01_error_rate_histogram.png")
    saved_files.append(filepath)
    plt.close()

    # 2. 오차율 박스플롯
    print("\n=== 2. 오차율 박스플롯 저장 중 ===")
    plot_error_rate_boxplot(df_compare, show=False)
    filepath = save_figure(output_dir=output_dir, filename="02_error_rate_boxplot.png")
    saved_files.append(filepath)
    plt.close()

    # 3. 실제값 vs 예측값 산점도
    print("\n=== 3. 실제값 vs 예측값 산점도 저장 중 ===")
    plot_actual_vs_predicted(y_test, y_pred, show=False)
    filepath = save_figure(output_dir=output_dir, filename="03_actual_vs_predicted.png")
    saved_files.append(filepath)
    plt.close()

    # backend 및 interactive mode 복원
    matplotlib.use(original_backend, force=True)
    plt.ion()

    print(f"\n✓ 총 {len(saved_files)}개의 결과 그래프 저장 완료")
    return saved_files
