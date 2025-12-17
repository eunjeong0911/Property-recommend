"""
학습된 모델로 Trust Score 예측 (12개 feature)
"""
import os
import sys
import pickle
import django

# Django 설정
backend_path = '/app/apps/backend' if os.path.exists('/app/apps/backend') else 'apps/backend'
if backend_path not in sys.path:
    sys.path.append(backend_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.utils import timezone
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
    """
    Feature 생성 (학습 시와 동일한 12개)
    """
    from datetime import datetime
    import numpy as np
    
    # 기본 값 추출
    거래완료 = broker.completed_deals or 0
    등록매물 = broker.registered_properties or 0
    공인중개사수 = broker.brokers_count or 0
    중개보조원수 = broker.assistants_count or 0
    일반직원수 = broker.staff_count or 0
    
    # 1-3. 거래 지표
    거래완료_safe = 거래완료
    등록매물_safe = 등록매물
    총거래활동량 = 거래완료 + 등록매물
    
    # 4-6. 인력 지표
    총_직원수 = 공인중개사수 + 중개보조원수 + 일반직원수
    총_직원수_safe = max(총_직원수, 1)
    공인중개사_비율 = 공인중개사수 / 총_직원수_safe
    
    # 7-10. 운영 경험
    if broker.registration_date:
        try:
            등록일 = broker.registration_date
            today = datetime.now().date()
            if isinstance(등록일, str):
                from dateutil import parser
                등록일 = parser.parse(등록일).date()
            영업일수 = (today - 등록일).days
            운영기간_년 = 영업일수 / 365.25
        except:
            운영기간_년 = 0
    else:
        운영기간_년 = 0
    
    운영경험_지수 = np.exp(운영기간_년 / 10)
    숙련도_지수 = 운영기간_년 * 공인중개사_비율
    운영_안정성 = 1 if 운영기간_년 >= 3 else 0
    
    # 11-12. 조직 구조
    대형사무소 = 1 if 총_직원수 >= 3 else 0
    직책_다양성 = (
        (1 if 공인중개사수 > 0 else 0) +
        (1 if 중개보조원수 > 0 else 0) +
        1 +  # 대표수 (항상 1)
        (1 if 일반직원수 > 0 else 0)
    )
    
    # 12개 Feature (학습 시와 동일한 순서)
    features = [
        거래완료_safe,
        등록매물_safe,
        총거래활동량,
        총_직원수,
        공인중개사수,
        공인중개사_비율,
        운영기간_년,
        운영경험_지수,
        숙련도_지수,
        운영_안정성,
        대형사무소,
        직책_다양성
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
            
            # pandas DataFrame으로 변환
            import pandas as pd
            features_df = pd.DataFrame([features], columns=feature_names)
            
            # 스케일링
            features_scaled = scaler.transform(features_df)
            
            # 예측
            pred = model.predict(features_scaled)[0]
            
            # 예측값이 문자열인 경우 (A, B, C) 그대로 사용
            # 예측값이 숫자인 경우 (0, 1, 2) 매핑
            if isinstance(pred, str):
                trust_score = pred
            else:
                grade_map = {0: 'A', 1: 'B', 2: 'C'}
                trust_score = grade_map.get(pred, 'C')
            
            # 저장
            broker.trust_score = trust_score
            broker.trust_score_updated_at = timezone.now()
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
