"""
다중 분류 모델 비교 및 평가
- Logistic Regression, Random Forest, Gradient Boosting, SVM 비교
- 교차검증을 통한 안정성 평가
- 성능 지표 시각화 및 분석
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from pathlib import Path

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def load_data():
    """데이터 로드"""
    filepath = "data/ML/office_features.csv"
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    
    # 실제 데이터의 컬럼명 확인
    print(f"📋 데이터 컬럼 확인:")
    print(f"   전체 컬럼 수: {len(df.columns)}")
    print(f"   컬럼 목록: {list(df.columns)}")
    
    # 사용 가능한 피처들만 선택 (실제 존재하는 컬럼들)
    all_features = [
        "거래완료_log","등록매물_log", "총거래활동량_log",
        "총_직원수","공인중개사수","공인중개사_비율",
        "운영기간_년","운영경험_지수","숙련도_지수","운영_안정성",
        "대형사무소", "직책_다양성",
        "대표_공인중개사","대표_법인","대표_중개인","대표_중개보조원"
    ]
    
    # 실제 존재하는 피처들만 필터링
    features = [f for f in all_features if f in df.columns]
    missing_features = [f for f in all_features if f not in df.columns]
    
    if missing_features:
        print(f"⚠️ 누락된 피처들: {missing_features}")
    
    print(f"✅ 사용할 피처들 ({len(features)}개): {features}")
    
    X = df[features]
    y = df['신뢰도등급']
    
    return X, y, features

def prepare_models():
    """분류 모델들 정의"""
    models = {
        'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'Gradient Boosting': GradientBoostingClassifier(random_state=42),
        'SVM': SVC(random_state=42, probability=True)
    }
    return models

def evaluate_models(X, y):
    """모델들 평가 및 비교"""
    # 데이터 분할
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # 스케일링 (SVM을 위해)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 모델들 준비
    models = prepare_models()
    
    # 결과 저장용
    results = {}
    predictions = {}
    
    print("🔄 모델 학습 및 평가 중...")
    print("="*60)
    
    for name, model in models.items():
        print(f"\n📊 {name} 평가 중...")
        
        # SVM은 스케일된 데이터 사용, 나머지는 원본 데이터
        if name == 'SVM':
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            cv_scores = cross_val_score(model, X_train, y_train, cv=5)
        
        # 성능 지표 계산
        accuracy = accuracy_score(y_test, y_pred)
        cv_mean = cv_scores.mean()
        cv_std = cv_scores.std()
        
        results[name] = {
            'accuracy': accuracy,
            'cv_mean': cv_mean,
            'cv_std': cv_std,
            'cv_scores': cv_scores,
            'model': model
        }
        predictions[name] = y_pred
        
        print(f"테스트 정확도: {accuracy:.4f}")
        print(f"교차검증 평균: {cv_mean:.4f} (±{cv_std:.4f})")
    
    return results, predictions, y_test, scaler

def visualize_results(results, predictions, y_test):
    """결과 시각화"""
    plt.figure(figsize=(15, 5))
    
    # 1. 정확도 비교
    plt.subplot(1, 3, 1)
    model_names = list(results.keys())
    accuracies = [results[name]['accuracy'] for name in model_names]
    cv_means = [results[name]['cv_mean'] for name in model_names]
    
    x = np.arange(len(model_names))
    width = 0.35
    
    plt.bar(x - width/2, accuracies, width, label='Test Accuracy', alpha=0.8)
    plt.bar(x + width/2, cv_means, width, label='CV Mean', alpha=0.8)
    
    plt.xlabel('Models')
    plt.ylabel('Accuracy')
    plt.title('모델별 정확도 비교')
    plt.xticks(x, model_names, rotation=45)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    # 2. 교차검증 점수 분포
    plt.subplot(1, 3, 2)
    cv_data = [results[name]['cv_scores'] for name in model_names]
    
    plt.boxplot(cv_data, labels=model_names)
    plt.ylabel('CV Accuracy')
    plt.title('교차검증 점수 분포')
    plt.xticks(rotation=45)
    plt.grid(axis='y', alpha=0.3)
    
    # 3. 최고 성능 모델의 혼동행렬
    best_model_name = max(results.keys(), key=lambda x: results[x]['cv_mean'])
    best_predictions = predictions[best_model_name]
    
    plt.subplot(1, 3, 3)
    cm = confusion_matrix(y_test, best_predictions)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['A', 'B', 'C'], yticklabels=['A', 'B', 'C'])
    plt.title(f'{best_model_name}\n혼동행렬')
    plt.ylabel('실제')
    plt.xlabel('예측')
    
    plt.tight_layout()
    
    # 이미지 저장
    save_path = Path("../image/model_comparison.png")
    save_path.parent.mkdir(exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()
    
    return best_model_name

def print_detailed_results(results, predictions, y_test, best_model_name):
    """상세 결과 출력"""
    model_names = list(results.keys())
    
    print("\n" + "="*60)
    print("📈 최종 모델 성능 비교")
    print("="*60)
    
    results_df = pd.DataFrame({
        'Model': model_names,
        'Test_Accuracy': [results[name]['accuracy'] for name in model_names],
        'CV_Mean': [results[name]['cv_mean'] for name in model_names],
        'CV_Std': [results[name]['cv_std'] for name in model_names]
    }).sort_values('CV_Mean', ascending=False)
    
    print(results_df.to_string(index=False, float_format='%.4f'))
    
    print(f"\n🏆 최고 성능 모델: {best_model_name}")
    print(f"   교차검증 평균: {results[best_model_name]['cv_mean']:.4f}")
    print(f"   테스트 정확도: {results[best_model_name]['accuracy']:.4f}")
    
    # 최고 성능 모델의 분류 리포트
    best_predictions = predictions[best_model_name]
    print(f"\n📋 {best_model_name} 상세 분류 리포트:")
    print(classification_report(y_test, best_predictions))
    
    return results_df

def save_best_model(results, scaler, features, best_model_name):
    """최고 성능 모델 저장"""
    best_model = results[best_model_name]['model']
    
    save_dir = Path("../save_models")
    save_dir.mkdir(exist_ok=True)
    
    # 모델 저장
    model_path = save_dir / f"best_model_{best_model_name.lower().replace(' ', '_')}.pkl"
    joblib.dump(best_model, model_path)
    
    # 스케일러 저장 (SVM인 경우)
    if best_model_name == 'SVM':
        scaler_path = save_dir / "scaler.pkl"
        joblib.dump(scaler, scaler_path)
    
    # 피처 정보 저장
    feature_info = {
        'features': features,
        'model_type': best_model_name,
        'use_scaler': best_model_name == 'SVM'
    }
    
    import json
    info_path = save_dir / "model_info.json"
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(feature_info, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 최고 성능 모델 저장 완료:")
    print(f"   모델: {model_path}")
    if best_model_name == 'SVM':
        print(f"   스케일러: {scaler_path}")
    print(f"   정보: {info_path}")

def main():
    """메인 실행 함수"""
    print("🚀 다중 분류 모델 비교 시작")
    
    # 데이터 로드
    X, y, features = load_data()
    print(f"📊 데이터 로드 완료: {X.shape[0]}개 샘플, {X.shape[1]}개 피처")
    
    # 모델 평가
    results, predictions, y_test, scaler = evaluate_models(X, y)
    
    # 결과 시각화
    best_model_name = visualize_results(results, predictions, y_test)
    
    # 상세 결과 출력
    results_df = print_detailed_results(results, predictions, y_test, best_model_name)
    
    # 최고 성능 모델 저장
    save_best_model(results, scaler, features, best_model_name)
    
    # 결과 CSV 저장
    results_path = Path("../results/model_comparison_results.csv")
    results_path.parent.mkdir(exist_ok=True)
    results_df.to_csv(results_path, index=False, encoding='utf-8-sig')
    print(f"\n📄 결과 저장: {results_path}")
    
    print("\n✅ 모델 비교 완료!")
    return results, best_model_name

if __name__ == "__main__":
    results, best_model_name = main()