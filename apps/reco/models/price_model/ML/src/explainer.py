"""
모델 해석 및 SHAP 분석 모듈
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap
from pathlib import Path
from typing import Optional, List, Dict, Any


class ModelExplainer:
    """모델 해석 및 SHAP 분석 클래스"""

    def __init__(
        self,
        model: Any,
        model_name: str,
        feature_names: Optional[List[str]] = None
    ):
        """
        Args:
            model: 학습된 모델
            model_name: 모델 이름
            feature_names: 피처 이름 리스트
        """
        self.model = model
        self.model_name = model_name
        self.feature_names = feature_names
        self.explainer = None
        self.shap_values = None

    def create_explainer(
        self,
        X_background: np.ndarray,
        background_size: int = 100
    ):
        """
        SHAP Explainer 생성

        Args:
            X_background: 배경 데이터 (학습 데이터 샘플)
            background_size: 배경 데이터 크기
        """
        print(f"\n🔍 SHAP Explainer 생성 중...")

        # Tree 모델인 경우 TreeExplainer 사용
        if self.model_name in ["XGBoost", "LightGBM"]:
            print(f"   - TreeExplainer 사용 ({self.model_name})")
            self.explainer = shap.TreeExplainer(self.model)
        else:
            # 일반 모델은 KernelExplainer 사용
            print(f"   - KernelExplainer 사용")
            # 배경 데이터 샘플링
            if len(X_background) > background_size:
                indices = np.random.choice(
                    len(X_background),
                    size=background_size,
                    replace=False
                )
                X_bg = X_background[indices]
            else:
                X_bg = X_background

            self.explainer = shap.KernelExplainer(
                self.model.predict,
                X_bg
            )

        print(f"✅ Explainer 생성 완료")

    def compute_shap_values(
        self,
        X: np.ndarray,
        max_samples: Optional[int] = None
    ):
        """
        SHAP values 계산

        Args:
            X: 분석할 데이터
            max_samples: 최대 샘플 수 (None이면 전체)
        """
        if self.explainer is None:
            raise ValueError("먼저 create_explainer()를 호출하세요.")

        print(f"\n📊 SHAP values 계산 중...")

        # 샘플링
        if max_samples is not None and len(X) > max_samples:
            print(f"   - {len(X):,}개 중 {max_samples:,}개 샘플링")
            indices = np.random.choice(
                len(X),
                size=max_samples,
                replace=False
            )
            X_sample = X[indices]
        else:
            X_sample = X

        # SHAP values 계산
        print(f"   - 계산 중... (시간이 걸릴 수 있습니다)")
        self.shap_values = self.explainer.shap_values(X_sample)

        print(f"✅ SHAP values 계산 완료: {self.shap_values.shape}")

        return self.shap_values, X_sample

    def plot_summary(
        self,
        X: np.ndarray,
        plot_type: str = "dot",
        max_display: int = 20,
        save_path: Optional[str] = None,
        show: bool = True
    ):
        """
        SHAP Summary Plot

        Args:
            X: 데이터
            plot_type: 플롯 타입 ("dot" or "bar")
            max_display: 표시할 최대 피처 수
            save_path: 저장 경로
            show: 플롯 표시 여부
        """
        if self.shap_values is None:
            raise ValueError("먼저 compute_shap_values()를 호출하세요.")

        print(f"\n📈 SHAP Summary Plot 생성 중...")

        plt.figure(figsize=(12, 8))
        shap.summary_plot(
            self.shap_values,
            X,
            feature_names=self.feature_names,
            plot_type=plot_type,
            max_display=max_display,
            show=False
        )
        plt.title(f"SHAP Summary Plot - {self.model_name}", fontsize=14, pad=20)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 저장 완료: {save_path}")

        if show:
            plt.show()
        else:
            plt.close()

    def plot_bar(
        self,
        X: np.ndarray,
        max_display: int = 20,
        save_path: Optional[str] = None,
        show: bool = True
    ):
        """
        SHAP Bar Plot (피처 중요도)

        Args:
            X: 데이터
            max_display: 표시할 최대 피처 수
            save_path: 저장 경로
            show: 플롯 표시 여부
        """
        if self.shap_values is None:
            raise ValueError("먼저 compute_shap_values()를 호출하세요.")

        print(f"\n📊 SHAP Bar Plot 생성 중...")

        plt.figure(figsize=(10, 8))
        shap.summary_plot(
            self.shap_values,
            X,
            feature_names=self.feature_names,
            plot_type="bar",
            max_display=max_display,
            show=False
        )
        plt.title(f"SHAP Feature Importance - {self.model_name}", fontsize=14, pad=20)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 저장 완료: {save_path}")

        if show:
            plt.show()
        else:
            plt.close()

    def plot_waterfall(
        self,
        X: np.ndarray,
        sample_idx: int = 0,
        max_display: int = 20,
        save_path: Optional[str] = None,
        show: bool = True
    ):
        """
        SHAP Waterfall Plot (단일 샘플 설명)

        Args:
            X: 데이터
            sample_idx: 분석할 샘플 인덱스
            max_display: 표시할 최대 피처 수
            save_path: 저장 경로
            show: 플롯 표시 여부
        """
        if self.shap_values is None:
            raise ValueError("먼저 compute_shap_values()를 호출하세요.")

        print(f"\n🌊 SHAP Waterfall Plot 생성 중 (샘플 #{sample_idx})...")

        # TreeExplainer를 사용한 경우
        if isinstance(self.explainer, shap.TreeExplainer):
            explanation = shap.Explanation(
                values=self.shap_values[sample_idx],
                base_values=self.explainer.expected_value,
                data=X[sample_idx],
                feature_names=self.feature_names
            )
        else:
            explanation = shap.Explanation(
                values=self.shap_values[sample_idx],
                base_values=self.explainer.expected_value[0] if hasattr(self.explainer.expected_value, '__len__') else self.explainer.expected_value,
                data=X[sample_idx],
                feature_names=self.feature_names
            )

        plt.figure(figsize=(10, 8))
        shap.waterfall_plot(explanation, max_display=max_display, show=False)
        plt.title(f"SHAP Waterfall Plot - {self.model_name} (Sample #{sample_idx})", fontsize=14, pad=20)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 저장 완료: {save_path}")

        if show:
            plt.show()
        else:
            plt.close()

    def plot_force(
        self,
        X: np.ndarray,
        sample_idx: int = 0,
        matplotlib: bool = True,
        save_path: Optional[str] = None,
        show: bool = True
    ):
        """
        SHAP Force Plot (단일 샘플 설명)

        Args:
            X: 데이터
            sample_idx: 분석할 샘플 인덱스
            matplotlib: matplotlib 사용 여부
            save_path: 저장 경로
            show: 플롯 표시 여부
        """
        if self.shap_values is None:
            raise ValueError("먼저 compute_shap_values()를 호출하세요.")

        print(f"\n⚡ SHAP Force Plot 생성 중 (샘플 #{sample_idx})...")

        if matplotlib:
            # TreeExplainer의 expected_value 처리
            if isinstance(self.explainer, shap.TreeExplainer):
                base_value = self.explainer.expected_value
            else:
                base_value = self.explainer.expected_value[0] if hasattr(self.explainer.expected_value, '__len__') else self.explainer.expected_value

            plt.figure(figsize=(20, 3))
            shap.force_plot(
                base_value,
                self.shap_values[sample_idx],
                X[sample_idx],
                feature_names=self.feature_names,
                matplotlib=True,
                show=False
            )
            plt.title(f"SHAP Force Plot - {self.model_name} (Sample #{sample_idx})", fontsize=12, pad=20)
            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"✅ 저장 완료: {save_path}")

            if show:
                plt.show()
            else:
                plt.close()
        else:
            # JavaScript 기반 force plot (주피터 노트북에서만 작동)
            if isinstance(self.explainer, shap.TreeExplainer):
                base_value = self.explainer.expected_value
            else:
                base_value = self.explainer.expected_value[0] if hasattr(self.explainer.expected_value, '__len__') else self.explainer.expected_value

            return shap.force_plot(
                base_value,
                self.shap_values[sample_idx],
                X[sample_idx],
                feature_names=self.feature_names
            )

    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """
        SHAP 기반 피처 중요도 데이터프레임 생성

        Args:
            top_n: 상위 N개 피처

        Returns:
            피처 중요도 데이터프레임
        """
        if self.shap_values is None:
            raise ValueError("먼저 compute_shap_values()를 호출하세요.")

        print(f"\n📊 피처 중요도 계산 중...")

        # SHAP 절대값 평균으로 중요도 계산
        importance = np.abs(self.shap_values).mean(axis=0)

        # 데이터프레임 생성
        if self.feature_names is not None:
            df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': importance
            })
        else:
            df = pd.DataFrame({
                'feature': [f'feature_{i}' for i in range(len(importance))],
                'importance': importance
            })

        # 정렬
        df = df.sort_values('importance', ascending=False).reset_index(drop=True)

        print(f"✅ 피처 중요도 계산 완료")
        print(f"\n🏆 Top {top_n} 중요 피처:")
        print(df.head(top_n).to_string(index=False))

        return df

    def save_all_plots(
        self,
        X: np.ndarray,
        output_dir: str = "./shap_plots",
        max_display: int = 20,
        sample_indices: Optional[List[int]] = None
    ):
        """
        모든 SHAP 플롯을 저장

        Args:
            X: 데이터
            output_dir: 저장 디렉토리
            max_display: 표시할 최대 피처 수
            sample_indices: waterfall/force plot에 사용할 샘플 인덱스 리스트
        """
        if self.shap_values is None:
            raise ValueError("먼저 compute_shap_values()를 호출하세요.")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\n{'=' * 60}")
        print(f"💾 모든 SHAP 플롯 저장 중: {output_dir}")
        print(f"{'=' * 60}")

        # 1. Summary Plot (dot)
        self.plot_summary(
            X,
            plot_type="dot",
            max_display=max_display,
            save_path=str(output_path / f"shap_summary_{self.model_name.lower()}.png"),
            show=False
        )

        # 2. Bar Plot
        self.plot_bar(
            X,
            max_display=max_display,
            save_path=str(output_path / f"shap_bar_{self.model_name.lower()}.png"),
            show=False
        )

        # 3. Waterfall & Force plots (샘플별)
        if sample_indices is None:
            sample_indices = [0, 1, 2]  # 기본값: 처음 3개 샘플

        for idx in sample_indices:
            if idx < len(X):
                # Waterfall plot
                self.plot_waterfall(
                    X,
                    sample_idx=idx,
                    max_display=max_display,
                    save_path=str(output_path / f"shap_waterfall_{self.model_name.lower()}_sample_{idx}.png"),
                    show=False
                )

                # Force plot
                self.plot_force(
                    X,
                    sample_idx=idx,
                    matplotlib=True,
                    save_path=str(output_path / f"shap_force_{self.model_name.lower()}_sample_{idx}.png"),
                    show=False
                )

        # 4. Feature importance CSV 저장
        importance_df = self.get_feature_importance(top_n=len(self.feature_names) if self.feature_names else 50)
        importance_path = output_path / f"shap_feature_importance_{self.model_name.lower()}.csv"
        importance_df.to_csv(importance_path, index=False, encoding='utf-8-sig')
        print(f"✅ 피처 중요도 CSV 저장: {importance_path}")

        print(f"\n{'=' * 60}")
        print(f"✅ 모든 플롯 저장 완료!")
        print(f"{'=' * 60}")
