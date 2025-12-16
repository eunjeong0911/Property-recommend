"""
모델 신뢰성 검증을 위한 종합 분석
- 모델 성능 검증
- 피처 중요도 검증  
- 등급별 특성 분석
- 지역별 공정성 검증
- 비즈니스 타당성 검증
- 예측 안정성 검증
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
from pathlib import Path
from sklearn.metrics import (
    confusion_matrix, classification_report, roc_curve, auc,
    precision_recall_curve, average_precision_score
)
from sklearn.model_selection import cross_val_score, validation_curve, learning_curve
from sklearn.preprocessing import label_binarize
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 파일 경로
TEMP_MODEL_PATH = "apps/reco/models/trust_model/save_models/temp_trained_models.pkl"
FEATURE_DATA_PATH = "data/ML/office_features.csv"
TARGET_DATA_PATH = "data/ML/office_target.csv"

class ModelValidationAnalyzer:
    def __init__(self):
        self.results_dir = Path("apps/reco/models/trust_model/results/validation")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # 데이터 로드
        self.load_data()
        
    def load_data(self):
        """모델과 데이터 로드"""
        print("📂 데이터 로드 중...")
        
        # 모델 데이터 로드
        with open(TEMP_MODEL_PATH, "rb") as f:
            temp_data = pickle.load(f)
        
        self.models = temp_data["models"]
        self.cv_results = temp_data.get("cv_results", {})
        self.X_train_scaled = temp_data["X_train_scaled"]
        self.X_test_scaled = temp_data["X_test_scaled"]
        self.y_train = temp_data["y_train"]
        self.y_test = temp_data["y_test"]
        self.feature_names = temp_data["feature_names"]
        
        # 최고 성능 모델 선택
        best_model_name = max(self.cv_results.keys(), key=lambda k: self.cv_results[k]['cv_mean'])
        self.model = self.models[best_model_name]
        self.model_name = best_model_name
        
        # 원본 데이터 로드
        self.df_features = pd.read_csv(FEATURE_DATA_PATH, encoding='utf-8-sig')
        self.df_target = pd.read_csv(TARGET_DATA_PATH, encoding='utf-8-sig')
        
        print(f"✅ 모델: {self.model_name}")
        print(f"✅ 피처 수: {len(self.feature_names)}")
        print(f"✅ 훈련 데이터: {len(self.X_train_scaled)}")
        print(f"✅ 테스트 데이터: {len(self.X_test_scaled)}")
        
    def analyze_1_model_performance(self):
        """1. 모델 성능 검증 분석"""
        print("\n" + "="*70)
        print("📊 1. 모델 성능 검증 분석")
        print("="*70)
        
        # 예측 수행
        y_train_pred = self.model.predict(self.X_train_scaled)
        y_test_pred = self.model.predict(self.X_test_scaled)
        y_test_proba = self.model.predict_proba(self.X_test_scaled)
        
        # 1-1. Confusion Matrix
        self._plot_confusion_matrix(y_test_pred)
        
        # 1-2. Classification Report
        self._plot_classification_report(y_test_pred)
        
        # 1-3. ROC Curve
        self._plot_roc_curves(y_test_proba)
        
        # 1-4. Precision-Recall Curve
        self._plot_precision_recall_curves(y_test_proba)
        
    def _plot_confusion_matrix(self, y_pred):
        """혼동 행렬 시각화"""
        plt.figure(figsize=(10, 8))
        
        cm = confusion_matrix(self.y_test, y_pred)
        classes = ['A등급', 'B등급', 'C등급']
        
        # 혼동 행렬 히트맵
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=classes, yticklabels=classes,
                   cbar_kws={'label': '예측 건수'})
        
        plt.title('혼동 행렬 (Confusion Matrix)', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('예측 등급', fontsize=14, fontweight='bold')
        plt.ylabel('실제 등급', fontsize=14, fontweight='bold')
        
        # 정확도 계산
        accuracy = np.trace(cm) / np.sum(cm)
        plt.figtext(0.02, 0.02, f'전체 정확도: {accuracy:.3f}', fontsize=12, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))
        
        plt.tight_layout()
        plt.savefig(self.results_dir / "1_confusion_matrix.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("   ✅ 혼동 행렬 저장 완료")
        
    def _plot_classification_report(self, y_pred):
        """분류 성능 리포트 시각화"""
        from sklearn.metrics import precision_recall_fscore_support
        
        # 클래스별 성능 계산
        precision, recall, f1, support = precision_recall_fscore_support(
            self.y_test, y_pred, average=None, labels=['A', 'B', 'C']
        )
        
        # 데이터프레임 생성
        metrics_df = pd.DataFrame({
            '등급': ['A등급', 'B등급', 'C등급'],
            'Precision': precision,
            'Recall': recall,
            'F1-Score': f1,
            'Support': support
        })
        
        # 시각화
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        metrics = ['Precision', 'Recall', 'F1-Score']
        colors = ['skyblue', 'lightgreen', 'lightcoral']
        
        for i, metric in enumerate(metrics):
            bars = axes[i].bar(metrics_df['등급'], metrics_df[metric], 
                              color=colors[i], alpha=0.8, edgecolor='black')
            axes[i].set_title(f'{metric} by 등급', fontsize=14, fontweight='bold')
            axes[i].set_ylabel(metric, fontsize=12)
            axes[i].set_ylim(0, 1.1)
            
            # 값 표시
            for bar in bars:
                height = bar.get_height()
                axes[i].text(bar.get_x() + bar.get_width()/2., height + 0.02,
                           f'{height:.3f}', ha='center', va='bottom', fontweight='bold')
        
        plt.suptitle('등급별 분류 성능 지표', fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(self.results_dir / "2_classification_report.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("   ✅ 분류 성능 리포트 저장 완료")
        
    def _plot_roc_curves(self, y_proba):
        """ROC 곡선 시각화"""
        plt.figure(figsize=(12, 8))
        
        # 클래스 이진화
        y_test_bin = label_binarize(self.y_test, classes=['A', 'B', 'C'])
        n_classes = y_test_bin.shape[1]
        
        colors = ['blue', 'red', 'green']
        class_names = ['A등급', 'B등급', 'C등급']
        
        # 각 클래스별 ROC 곡선
        for i in range(n_classes):
            fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_proba[:, i])
            roc_auc = auc(fpr, tpr)
            
            plt.plot(fpr, tpr, color=colors[i], lw=2,
                    label=f'{class_names[i]} (AUC = {roc_auc:.3f})')
        
        # 대각선 (랜덤 분류기)
        plt.plot([0, 1], [0, 1], 'k--', lw=2, label='랜덤 분류기 (AUC = 0.500)')
        
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate', fontsize=14, fontweight='bold')
        plt.ylabel('True Positive Rate', fontsize=14, fontweight='bold')
        plt.title('ROC 곡선 (Receiver Operating Characteristic)', fontsize=16, fontweight='bold', pad=20)
        plt.legend(loc="lower right", fontsize=12)
        plt.grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.results_dir / "3_roc_curves.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("   ✅ ROC 곡선 저장 완료")
        
    def _plot_precision_recall_curves(self, y_proba):
        """Precision-Recall 곡선 시각화"""
        plt.figure(figsize=(12, 8))
        
        # 클래스 이진화
        y_test_bin = label_binarize(self.y_test, classes=['A', 'B', 'C'])
        n_classes = y_test_bin.shape[1]
        
        colors = ['blue', 'red', 'green']
        class_names = ['A등급', 'B등급', 'C등급']
        
        # 각 클래스별 PR 곡선
        for i in range(n_classes):
            precision, recall, _ = precision_recall_curve(y_test_bin[:, i], y_proba[:, i])
            avg_precision = average_precision_score(y_test_bin[:, i], y_proba[:, i])
            
            plt.plot(recall, precision, color=colors[i], lw=2,
                    label=f'{class_names[i]} (AP = {avg_precision:.3f})')
        
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('Recall', fontsize=14, fontweight='bold')
        plt.ylabel('Precision', fontsize=14, fontweight='bold')
        plt.title('Precision-Recall 곡선', fontsize=16, fontweight='bold', pad=20)
        plt.legend(loc="lower left", fontsize=12)
        plt.grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.results_dir / "4_precision_recall_curves.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("   ✅ Precision-Recall 곡선 저장 완료")

    def analyze_2_feature_importance(self):
        """2. 피처 중요도 검증 분석"""
        print("\n" + "="*70)
        print("📊 2. 피처 중요도 검증 분석")
        print("="*70)
        
        # 2-1. Feature Correlation Heatmap
        self._plot_feature_correlation()
        
        # 2-2. Feature Importance (Logistic Regression Coefficients)
        self._plot_feature_coefficients()

    def analyze_3_grade_characteristics(self):
        """3. 등급별 특성 분석"""
        print("\n" + "="*70)
        print("📊 3. 등급별 특성 분석")
        print("="*70)
        
        # 3-1. Grade Distribution
        self._plot_grade_distribution()
        
        # 3-2. Feature Distribution by Grade
        self._plot_feature_distribution_by_grade()
        
        # 3-3. Grade Transition Analysis
        self._plot_grade_characteristics_radar()

    def analyze_4_regional_fairness(self):
        """4. 지역별 공정성 검증"""
        print("\n" + "="*70)
        print("📊 4. 지역별 공정성 검증")
        print("="*70)
        
        # 4-1. Regional Grade Distribution
        self._plot_regional_grade_distribution()
        
        # 4-2. Regional Performance Consistency
        self._plot_regional_performance_consistency()

    def analyze_5_business_validity(self):
        """5. 비즈니스 타당성 검증"""
        print("\n" + "="*70)
        print("📊 5. 비즈니스 타당성 검증")
        print("="*70)
        
        # 5-1. Representative Type Impact
        self._plot_representative_type_impact()
        
        # 5-2. Operational Period Trends
        self._plot_operational_period_trends()
        
        # 5-3. Staff Size Impact
        self._plot_staff_size_impact()

    def analyze_6_prediction_stability(self):
        """6. 예측 안정성 검증"""
        print("\n" + "="*70)
        print("📊 6. 예측 안정성 검증")
        print("="*70)
        
        # 6-1. Cross-Validation Analysis
        self._plot_cross_validation_analysis()
        
        # 6-2. Learning Curve
        self._plot_learning_curve()
        
        # 6-3. Prediction Confidence Distribution
        self._plot_prediction_confidence()
        
    def _plot_feature_correlation(self):
        """피처 상관관계 히트맵"""
        plt.figure(figsize=(14, 12))
        
        # 선택된 피처들만 추출
        selected_features_df = self.df_features[self.feature_names]
        
        # 상관관계 계산
        correlation_matrix = selected_features_df.corr()
        
        # 히트맵 생성
        mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
        sns.heatmap(correlation_matrix, mask=mask, annot=True, fmt='.2f', 
                   cmap='RdBu_r', center=0, square=True, cbar_kws={'label': '상관계수'})
        
        plt.title('피처 간 상관관계 히트맵', fontsize=16, fontweight='bold', pad=20)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        plt.tight_layout()
        plt.savefig(self.results_dir / "5_feature_correlation.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("   ✅ 피처 상관관계 히트맵 저장 완료")
        
    def _plot_feature_coefficients(self):
        """로지스틱 회귀 계수 시각화"""
        fig, axes = plt.subplots(1, 3, figsize=(20, 8))
        
        classes = ['A등급', 'B등급', 'C등급']
        colors = ['blue', 'red', 'green']
        
        # 각 클래스별 계수
        for i, (class_name, color) in enumerate(zip(classes, colors)):
            coefficients = self.model.coef_[i]
            
            # 절댓값 기준으로 정렬
            coef_df = pd.DataFrame({
                'feature': self.feature_names,
                'coefficient': coefficients,
                'abs_coefficient': np.abs(coefficients)
            }).sort_values('abs_coefficient', ascending=True)
            
            # 상위 10개만 표시
            top_features = coef_df.tail(10)
            
            bars = axes[i].barh(range(len(top_features)), top_features['coefficient'], 
                               color=color, alpha=0.7)
            axes[i].set_yticks(range(len(top_features)))
            axes[i].set_yticklabels(top_features['feature'])
            axes[i].set_xlabel('계수 값', fontsize=12)
            axes[i].set_title(f'{class_name} 예측 계수', fontsize=14, fontweight='bold')
            axes[i].axvline(x=0, color='black', linestyle='--', alpha=0.5)
            axes[i].grid(axis='x', alpha=0.3)
            
            # 값 표시
            for j, bar in enumerate(bars):
                width = bar.get_width()
                axes[i].text(width + (0.01 if width >= 0 else -0.01), bar.get_y() + bar.get_height()/2,
                           f'{width:.3f}', ha='left' if width >= 0 else 'right', va='center', fontsize=10)
        
        plt.suptitle('로지스틱 회귀 계수 (피처 중요도)', fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(self.results_dir / "6_feature_coefficients.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("   ✅ 피처 계수 시각화 저장 완료")

    def _plot_grade_distribution(self):
        """등급 분포 시각화"""
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # 전체 데이터 등급 분포
        grade_counts = self.df_target['신뢰도등급'].value_counts().sort_index()
        grade_labels = [f'{grade}등급' for grade in grade_counts.index]
        
        # 파이 차트
        colors = ['#ff9999', '#66b3ff', '#99ff99']
        wedges, texts, autotexts = axes[0].pie(grade_counts.values, labels=grade_labels, 
                                              autopct='%1.1f%%', colors=colors, startangle=90)
        axes[0].set_title('전체 등급 분포', fontsize=14, fontweight='bold')
        
        # 막대 그래프
        bars = axes[1].bar(grade_labels, grade_counts.values, color=colors, alpha=0.8, edgecolor='black')
        axes[1].set_title('등급별 중개사 수', fontsize=14, fontweight='bold')
        axes[1].set_ylabel('중개사 수', fontsize=12)
        
        # 값 표시
        for bar in bars:
            height = bar.get_height()
            axes[1].text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{int(height):,}', ha='center', va='bottom', fontweight='bold')
        
        plt.suptitle('신뢰도 등급 분포 분석', fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(self.results_dir / "7_grade_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("   ✅ 등급 분포 시각화 저장 완료")

    def _plot_feature_distribution_by_grade(self):
        """등급별 주요 피처 분포 시각화"""
        # 주요 피처 선택 (거래 관련 + 운영 관련)
        key_features = ['거래완료_숫자', '등록매물_숫자', '총_직원수', '운영기간_년', '공인중개사_비율']
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes = axes.flatten()
        
        # 원본 데이터에서 등급별 분포 분석
        # features 데이터에 이미 신뢰도등급이 포함되어 있음
        merged_data = self.df_features.copy()
        
        for i, feature in enumerate(key_features):
            if i < len(axes):
                ax = axes[i]
                
                # 등급별 박스플롯
                grade_data = []
                grade_labels = []
                for grade in ['A', 'B', 'C']:
                    data = merged_data[merged_data['신뢰도등급'] == grade][feature].dropna()
                    if len(data) > 0:
                        grade_data.append(data)
                        grade_labels.append(f'{grade}등급')
                
                if grade_data:
                    bp = ax.boxplot(grade_data, labels=grade_labels, patch_artist=True)
                    colors = ['#ff9999', '#66b3ff', '#99ff99']
                    for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
                        patch.set_facecolor(color)
                        patch.set_alpha(0.7)
                
                ax.set_title(f'{feature} 등급별 분포', fontsize=12, fontweight='bold')
                ax.set_ylabel(feature, fontsize=10)
                ax.grid(alpha=0.3)
        
        # 빈 subplot 제거
        for i in range(len(key_features), len(axes)):
            fig.delaxes(axes[i])
        
        plt.suptitle('등급별 주요 피처 분포 분석', fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(self.results_dir / "8_feature_distribution_by_grade.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("   ✅ 등급별 피처 분포 시각화 저장 완료")

    def _plot_grade_characteristics_radar(self):
        """등급별 특성 레이더 차트"""
        # 주요 특성 지표 계산
        merged_data = self.df_features.copy()
        
        # 정규화된 특성 지표
        characteristics = {
            '거래활동': '거래완료_숫자',
            '매물등록': '등록매물_숫자', 
            '직원규모': '총_직원수',
            '운영경험': '운영기간_년',
            '전문성': '공인중개사_비율',
            '조직안정성': '운영_안정성'
        }
        
        # 등급별 평균 계산 및 정규화
        grade_profiles = {}
        for grade in ['A', 'B', 'C']:
            grade_data = merged_data[merged_data['신뢰도등급'] == grade]
            profile = []
            for char_name, feature_name in characteristics.items():
                if feature_name in grade_data.columns:
                    mean_val = grade_data[feature_name].mean()
                    # 0-1 정규화
                    max_val = merged_data[feature_name].max()
                    min_val = merged_data[feature_name].min()
                    if max_val > min_val:
                        normalized = (mean_val - min_val) / (max_val - min_val)
                    else:
                        normalized = 0.5
                    profile.append(normalized)
                else:
                    profile.append(0.5)
            grade_profiles[grade] = profile
        
        # 레이더 차트 생성
        angles = np.linspace(0, 2 * np.pi, len(characteristics), endpoint=False).tolist()
        angles += angles[:1]  # 원형으로 만들기
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        colors = ['#ff9999', '#66b3ff', '#99ff99']
        for i, (grade, profile) in enumerate(grade_profiles.items()):
            profile += profile[:1]  # 원형으로 만들기
            ax.plot(angles, profile, 'o-', linewidth=2, label=f'{grade}등급', color=colors[i])
            ax.fill(angles, profile, alpha=0.25, color=colors[i])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(list(characteristics.keys()), fontsize=12)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=10)
        ax.grid(True)
        
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0), fontsize=12)
        plt.title('등급별 특성 프로필 (레이더 차트)', fontsize=16, fontweight='bold', pad=30)
        
        plt.tight_layout()
        plt.savefig(self.results_dir / "9_grade_characteristics_radar.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("   ✅ 등급별 특성 레이더 차트 저장 완료")

    def _plot_regional_grade_distribution(self):
        """지역별 등급 분포 시각화"""
        # 지역 정보가 있는 경우에만 실행
        if '지역' in self.df_target.columns or '시도' in self.df_target.columns:
            region_col = '지역' if '지역' in self.df_target.columns else '시도'
            
            # 지역별 등급 분포 계산
            region_grade = pd.crosstab(self.df_target[region_col], self.df_target['신뢰도등급'])
            
            # 상위 10개 지역만 표시
            top_regions = region_grade.sum(axis=1).nlargest(10).index
            region_grade_top = region_grade.loc[top_regions]
            
            # 비율로 변환
            region_grade_pct = region_grade_top.div(region_grade_top.sum(axis=1), axis=0) * 100
            
            fig, axes = plt.subplots(1, 2, figsize=(20, 8))
            
            # 절대 수치
            region_grade_top.plot(kind='bar', ax=axes[0], color=['#ff9999', '#66b3ff', '#99ff99'])
            axes[0].set_title('지역별 등급 분포 (절대 수치)', fontsize=14, fontweight='bold')
            axes[0].set_ylabel('중개사 수', fontsize=12)
            axes[0].legend(title='등급', labels=['A등급', 'B등급', 'C등급'])
            axes[0].tick_params(axis='x', rotation=45)
            
            # 비율
            region_grade_pct.plot(kind='bar', ax=axes[1], color=['#ff9999', '#66b3ff', '#99ff99'])
            axes[1].set_title('지역별 등급 분포 (비율)', fontsize=14, fontweight='bold')
            axes[1].set_ylabel('비율 (%)', fontsize=12)
            axes[1].legend(title='등급', labels=['A등급', 'B등급', 'C등급'])
            axes[1].tick_params(axis='x', rotation=45)
            
            plt.suptitle('지역별 신뢰도 등급 분포 분석', fontsize=16, fontweight='bold', y=1.02)
            plt.tight_layout()
            plt.savefig(self.results_dir / "10_regional_grade_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()
            print("   ✅ 지역별 등급 분포 시각화 저장 완료")
        else:
            print("   ⚠️  지역 정보가 없어 지역별 분석을 건너뜁니다.")

    def _plot_regional_performance_consistency(self):
        """지역별 모델 성능 일관성 분석"""
        if '지역' in self.df_target.columns or '시도' in self.df_target.columns:
            region_col = '지역' if '지역' in self.df_target.columns else '시도'
            
            # 테스트 데이터에 지역 정보 추가
            test_indices = self.df_target.index[self.df_target.index.isin(range(len(self.y_test)))]
            if len(test_indices) > 0:
                y_pred = self.model.predict(self.X_test_scaled)
                
                # 지역별 정확도 계산
                regional_accuracy = {}
                for region in self.df_target[region_col].unique():
                    region_mask = self.df_target[region_col] == region
                    region_indices = self.df_target[region_mask].index
                    
                    # 테스트 데이터와 교집합
                    test_region_indices = [i for i, idx in enumerate(test_indices) if idx in region_indices]
                    
                    if len(test_region_indices) > 5:  # 최소 5개 이상인 지역만
                        region_y_true = [self.y_test[i] for i in test_region_indices]
                        region_y_pred = [y_pred[i] for i in test_region_indices]
                        accuracy = sum(1 for t, p in zip(region_y_true, region_y_pred) if t == p) / len(region_y_true)
                        regional_accuracy[region] = accuracy
                
                if regional_accuracy:
                    # 시각화
                    regions = list(regional_accuracy.keys())
                    accuracies = list(regional_accuracy.values())
                    
                    plt.figure(figsize=(14, 8))
                    bars = plt.bar(regions, accuracies, color='steelblue', alpha=0.7, edgecolor='black')
                    plt.axhline(y=np.mean(accuracies), color='red', linestyle='--', 
                               label=f'전체 평균: {np.mean(accuracies):.3f}')
                    
                    plt.title('지역별 모델 예측 정확도', fontsize=16, fontweight='bold', pad=20)
                    plt.xlabel('지역', fontsize=12)
                    plt.ylabel('정확도', fontsize=12)
                    plt.xticks(rotation=45, ha='right')
                    plt.legend()
                    plt.grid(axis='y', alpha=0.3)
                    
                    # 값 표시
                    for bar, acc in zip(bars, accuracies):
                        plt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                                f'{acc:.3f}', ha='center', va='bottom', fontweight='bold')
                    
                    plt.tight_layout()
                    plt.savefig(self.results_dir / "11_regional_performance_consistency.png", dpi=300, bbox_inches='tight')
                    plt.close()
                    print("   ✅ 지역별 성능 일관성 분석 저장 완료")
                else:
                    print("   ⚠️  충분한 지역별 테스트 데이터가 없습니다.")
            else:
                print("   ⚠️  테스트 데이터와 지역 정보를 매칭할 수 없습니다.")
        else:
            print("   ⚠️  지역 정보가 없어 지역별 성능 분석을 건너뜁니다.")

    def _plot_representative_type_impact(self):
        """대표자 유형별 영향 분석"""
        merged_data = self.df_features.copy()
        
        if '대표자구분명' in merged_data.columns:
            # 대표자 유형별 등급 분포
            rep_grade = pd.crosstab(merged_data['대표자구분명'], merged_data['신뢰도등급'])
            rep_grade_pct = rep_grade.div(rep_grade.sum(axis=1), axis=0) * 100
            
            fig, axes = plt.subplots(1, 2, figsize=(16, 6))
            
            # 절대 수치
            rep_grade.plot(kind='bar', ax=axes[0], color=['#ff9999', '#66b3ff', '#99ff99'])
            axes[0].set_title('대표자 유형별 등급 분포 (절대 수치)', fontsize=14, fontweight='bold')
            axes[0].set_ylabel('중개사 수', fontsize=12)
            axes[0].legend(title='등급', labels=['A등급', 'B등급', 'C등급'])
            axes[0].tick_params(axis='x', rotation=45)
            
            # 비율
            rep_grade_pct.plot(kind='bar', ax=axes[1], color=['#ff9999', '#66b3ff', '#99ff99'])
            axes[1].set_title('대표자 유형별 등급 분포 (비율)', fontsize=14, fontweight='bold')
            axes[1].set_ylabel('비율 (%)', fontsize=12)
            axes[1].legend(title='등급', labels=['A등급', 'B등급', 'C등급'])
            axes[1].tick_params(axis='x', rotation=45)
            
            plt.suptitle('대표자 유형별 신뢰도 등급 영향 분석', fontsize=16, fontweight='bold', y=1.02)
            plt.tight_layout()
            plt.savefig(self.results_dir / "12_representative_type_impact.png", dpi=300, bbox_inches='tight')
            plt.close()
            print("   ✅ 대표자 유형별 영향 분석 저장 완료")
        else:
            print("   ⚠️  대표자구분명 정보가 없습니다.")

    def _plot_operational_period_trends(self):
        """운영 기간별 신뢰도 트렌드 분석"""
        merged_data = self.df_features.copy()
        
        if '운영기간_년' in merged_data.columns:
            # 운영 기간을 구간으로 나누기
            merged_data['운영기간_구간'] = pd.cut(merged_data['운영기간_년'], 
                                           bins=[0, 1, 3, 5, 10, float('inf')],
                                           labels=['1년 미만', '1-3년', '3-5년', '5-10년', '10년 이상'])
            
            # 구간별 등급 분포
            period_grade = pd.crosstab(merged_data['운영기간_구간'], merged_data['신뢰도등급'])
            period_grade_pct = period_grade.div(period_grade.sum(axis=1), axis=0) * 100
            
            fig, axes = plt.subplots(1, 2, figsize=(16, 6))
            
            # 절대 수치
            period_grade.plot(kind='bar', ax=axes[0], color=['#ff9999', '#66b3ff', '#99ff99'])
            axes[0].set_title('운영 기간별 등급 분포 (절대 수치)', fontsize=14, fontweight='bold')
            axes[0].set_ylabel('중개사 수', fontsize=12)
            axes[0].legend(title='등급', labels=['A등급', 'B등급', 'C등급'])
            axes[0].tick_params(axis='x', rotation=45)
            
            # 비율
            period_grade_pct.plot(kind='bar', ax=axes[1], color=['#ff9999', '#66b3ff', '#99ff99'])
            axes[1].set_title('운영 기간별 등급 분포 (비율)', fontsize=14, fontweight='bold')
            axes[1].set_ylabel('비율 (%)', fontsize=12)
            axes[1].legend(title='등급', labels=['A등급', 'B등급', 'C등급'])
            axes[1].tick_params(axis='x', rotation=45)
            
            plt.suptitle('운영 기간별 신뢰도 트렌드 분석', fontsize=16, fontweight='bold', y=1.02)
            plt.tight_layout()
            plt.savefig(self.results_dir / "13_operational_period_trends.png", dpi=300, bbox_inches='tight')
            plt.close()
            print("   ✅ 운영 기간별 트렌드 분석 저장 완료")
        else:
            print("   ⚠️  운영기간_년 정보가 없습니다.")

    def _plot_staff_size_impact(self):
        """직원 규모별 영향 분석"""
        merged_data = self.df_features.copy()
        
        if '총_직원수' in merged_data.columns:
            # 직원 수를 구간으로 나누기
            merged_data['직원규모_구간'] = pd.cut(merged_data['총_직원수'], 
                                           bins=[0, 1, 2, 3, 5, float('inf')],
                                           labels=['1명', '2명', '3명', '4-5명', '6명 이상'])
            
            # 구간별 등급 분포
            staff_grade = pd.crosstab(merged_data['직원규모_구간'], merged_data['신뢰도등급'])
            staff_grade_pct = staff_grade.div(staff_grade.sum(axis=1), axis=0) * 100
            
            fig, axes = plt.subplots(1, 2, figsize=(16, 6))
            
            # 절대 수치
            staff_grade.plot(kind='bar', ax=axes[0], color=['#ff9999', '#66b3ff', '#99ff99'])
            axes[0].set_title('직원 규모별 등급 분포 (절대 수치)', fontsize=14, fontweight='bold')
            axes[0].set_ylabel('중개사 수', fontsize=12)
            axes[0].legend(title='등급', labels=['A등급', 'B등급', 'C등급'])
            axes[0].tick_params(axis='x', rotation=45)
            
            # 비율
            staff_grade_pct.plot(kind='bar', ax=axes[1], color=['#ff9999', '#66b3ff', '#99ff99'])
            axes[1].set_title('직원 규모별 등급 분포 (비율)', fontsize=14, fontweight='bold')
            axes[1].set_ylabel('비율 (%)', fontsize=12)
            axes[1].legend(title='등급', labels=['A등급', 'B등급', 'C등급'])
            axes[1].tick_params(axis='x', rotation=45)
            
            plt.suptitle('직원 규모별 신뢰도 영향 분석', fontsize=16, fontweight='bold', y=1.02)
            plt.tight_layout()
            plt.savefig(self.results_dir / "14_staff_size_impact.png", dpi=300, bbox_inches='tight')
            plt.close()
            print("   ✅ 직원 규모별 영향 분석 저장 완료")
        else:
            print("   ⚠️  총_직원수 정보가 없습니다.")

    def _plot_cross_validation_analysis(self):
        """교차 검증 분석"""
        if self.cv_results:
            models = list(self.cv_results.keys())
            cv_means = [self.cv_results[model]['cv_mean'] for model in models]
            cv_stds = [self.cv_results[model]['cv_std'] for model in models]
            
            plt.figure(figsize=(12, 8))
            
            # 에러바가 있는 막대 그래프
            bars = plt.bar(models, cv_means, yerr=cv_stds, capsize=5, 
                          color='steelblue', alpha=0.7, edgecolor='black')
            
            plt.title('모델별 교차 검증 성능 비교', fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('모델', fontsize=12)
            plt.ylabel('교차 검증 정확도', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.grid(axis='y', alpha=0.3)
            
            # 값 표시
            for bar, mean, std in zip(bars, cv_means, cv_stds):
                plt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + std + 0.005,
                        f'{mean:.3f}±{std:.3f}', ha='center', va='bottom', fontweight='bold')
            
            plt.tight_layout()
            plt.savefig(self.results_dir / "15_cross_validation_analysis.png", dpi=300, bbox_inches='tight')
            plt.close()
            print("   ✅ 교차 검증 분석 저장 완료")
        else:
            print("   ⚠️  교차 검증 결과가 없습니다.")

    def _plot_learning_curve(self):
        """학습 곡선 분석"""
        from sklearn.model_selection import learning_curve
        
        print("   - 학습 곡선 계산 중... (시간이 걸릴 수 있습니다)")
        
        # 학습 곡선 계산
        train_sizes, train_scores, val_scores = learning_curve(
            self.model, self.X_train_scaled, self.y_train,
            train_sizes=np.linspace(0.1, 1.0, 10),
            cv=5, scoring='accuracy', n_jobs=-1
        )
        
        # 평균과 표준편차 계산
        train_mean = np.mean(train_scores, axis=1)
        train_std = np.std(train_scores, axis=1)
        val_mean = np.mean(val_scores, axis=1)
        val_std = np.std(val_scores, axis=1)
        
        plt.figure(figsize=(12, 8))
        
        # 학습 곡선 그리기
        plt.plot(train_sizes, train_mean, 'o-', color='blue', label='훈련 정확도')
        plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.1, color='blue')
        
        plt.plot(train_sizes, val_mean, 'o-', color='red', label='검증 정확도')
        plt.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.1, color='red')
        
        plt.title('학습 곡선 (Learning Curve)', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('훈련 데이터 크기', fontsize=12)
        plt.ylabel('정확도', fontsize=12)
        plt.legend(fontsize=12)
        plt.grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.results_dir / "16_learning_curve.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("   ✅ 학습 곡선 분석 저장 완료")

    def _plot_prediction_confidence(self):
        """예측 신뢰도 분포 분석"""
        y_proba = self.model.predict_proba(self.X_test_scaled)
        y_pred = self.model.predict(self.X_test_scaled)
        
        # 최대 확률값 (신뢰도)
        max_probas = np.max(y_proba, axis=1)
        
        # 정답/오답별 신뢰도 분포
        correct_mask = (y_pred == self.y_test)
        correct_probas = max_probas[correct_mask]
        incorrect_probas = max_probas[~correct_mask]
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # 히스토그램
        axes[0].hist(correct_probas, bins=20, alpha=0.7, label='정답', color='green', density=True)
        axes[0].hist(incorrect_probas, bins=20, alpha=0.7, label='오답', color='red', density=True)
        axes[0].set_title('예측 신뢰도 분포', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('예측 신뢰도 (최대 확률)', fontsize=12)
        axes[0].set_ylabel('밀도', fontsize=12)
        axes[0].legend()
        axes[0].grid(alpha=0.3)
        
        # 박스플롯
        axes[1].boxplot([correct_probas, incorrect_probas], labels=['정답', '오답'])
        axes[1].set_title('예측 신뢰도 박스플롯', fontsize=14, fontweight='bold')
        axes[1].set_ylabel('예측 신뢰도 (최대 확률)', fontsize=12)
        axes[1].grid(alpha=0.3)
        
        plt.suptitle('모델 예측 신뢰도 분석', fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(self.results_dir / "17_prediction_confidence.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("   ✅ 예측 신뢰도 분석 저장 완료")

def main():
    """메인 실행 함수"""
    print("="*70)
    print("🔍 모델 신뢰성 검증 종합 분석")
    print("="*70)
    
    analyzer = ModelValidationAnalyzer()
    
    # 1. 모델 성능 검증
    analyzer.analyze_1_model_performance()
    
    # 2. 피처 중요도 검증
    analyzer.analyze_2_feature_importance()
    
    # 3. 등급별 특성 분석
    analyzer.analyze_3_grade_characteristics()
    
    # 4. 지역별 공정성 검증
    analyzer.analyze_4_regional_fairness()
    
    # 5. 비즈니스 타당성 검증
    analyzer.analyze_5_business_validity()
    
    # 6. 예측 안정성 검증
    analyzer.analyze_6_prediction_stability()
    
    print("\n" + "="*70)
    print("✅ 전체 6단계 분석 완료!")
    print(f"📂 결과 저장 위치: {analyzer.results_dir}")
    print("\n📊 생성된 분석 결과:")
    print("   1. 모델 성능 검증 (4개 차트)")
    print("   2. 피처 중요도 검증 (2개 차트)")
    print("   3. 등급별 특성 분석 (3개 차트)")
    print("   4. 지역별 공정성 검증 (2개 차트)")
    print("   5. 비즈니스 타당성 검증 (3개 차트)")
    print("   6. 예측 안정성 검증 (3개 차트)")
    print("   📈 총 17개 분석 차트 생성")
    print("="*70)

if __name__ == "__main__":
    main()