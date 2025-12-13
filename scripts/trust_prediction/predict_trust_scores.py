"""
학습된 모델로 Trust Score 예측
"""
import os
import sys
import pickle
import django
from datetime import datetime

# Django 설정
backend_path = '/app/apps/backend' if os.path.exists('/app/apps/backend') else 'apps/backend'
if backend_path not in sys.path:
    sys.path.append(backend_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.listings.models import LandBroker


def load_model():
    """모델 로드"""
    model_path = '/app/apps/reco/models/trust_model/save_models/final_trust_model.pkl'
    if not os.path.exists(model_path):
        model_path = 'apps/reco/models/trust_model/save_models/final_trust_model.pkl'
    
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    return model_data['model'], model_data['scaler'], model_data['feature_names']


def create_features(broker):
    """Feature 생성"""
    properties_count = broker.properties.count()
    총_직원수 = (broker.brokers_count or 0) + (broker.assistants_count or 0) + (broker.staff_count or 0)
    총_직원수_safe = max(총_직원수, 1)
    
    거래완료 = broker.completed_deals or 0
    등록매물 = broker.registered_properties or 0
    총거래활동량 = 거래완료 + 등록매물
    
    features = [
        거래완료,
        등록매물,
        총거래활동량,
        broker.brokers_count or 0,
        broker.assistants_count or 0,
        총_직원수,
        총거래활동량 / 총_직원수_safe,
        properties_count
    ]
    
    return features


def predict():
    """예측 실행"""
    print("\n" + "=" * 70)
    print(" " * 15 + "Trust Score 예측 시작")
    print("=" * 70 + "\n")
    
    # 1. 모델 로드
    print("1. 모델 로드 중...")
    model, scaler, feature_names = load_model()
    print(f"  ✓ Feature: {feature_names}")
    
    # 2. Broker 조회
    print("\n2. Broker 데이터 조회 중...")
    brokers = LandBroker.objects.all()
    total = brokers.count()
    print(f"  ✓ {total}개 broker")
    
    # 3. 예측
    print("\n3. 예측 실행 중...")
    updated = 0
    grade_dist = {'A': 0, 'B': 0, 'C': 0}
    
    for i, broker in enumerate(brokers, 1):
        try:
            # Feature 생성
            features = create_features(broker)
            
            # 스케일링
            features_scaled = scaler.transform([features])
            
            # 예측
            pred = model.predict(features_scaled)[0]
            
            # 0, 1, 2 → A, B, C
            grade_map = {0: 'A', 1: 'B', 2: 'C'}
            trust_score = grade_map[pred]
            
            # 저장
            broker.trust_score = trust_score
            broker.trust_score_updated_at = datetime.now()
            broker.save(update_fields=['trust_score', 'trust_score_updated_at'])
            
            updated += 1
            grade_dist[trust_score] += 1
            
            if i % max(total // 10, 1) == 0:
                print(f"  진행: {i}/{total} ({i/total*100:.1f}%)")
        
        except Exception as e:
            print(f"  ✗ 예측 실패 ({broker.office_name}): {e}")
    
    # 4. 결과
    print("\n" + "=" * 70)
    print(" " * 20 + "예측 완료")
    print("=" * 70)
    print(f"\n  성공: {updated}개")
    print(f"\n  등급 분포:")
    print(f"    A등급: {grade_dist['A']}개 ({grade_dist['A']/max(total,1)*100:.1f}%)")
    print(f"    B등급: {grade_dist['B']}개 ({grade_dist['B']/max(total,1)*100:.1f}%)")
    print(f"    C등급: {grade_dist['C']}개 ({grade_dist['C']/max(total,1)*100:.1f}%)")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        predict()
    except Exception as e:
        print(f"\n✗ 오류: {e}")
        import traceback
        traceback.print_exc()
