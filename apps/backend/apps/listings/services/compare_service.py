"""
매물 비교 서비스
"""
import os
from openai import OpenAI
from typing import List, Dict
from .comparison_prompt import create_comparison_prompt


class PropertyComparisonService:
    """매물 비교 LLM 서비스"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"
        self.temperature = 0.3  # 일관성 있는 분석을 위해 낮게 설정
    
    def compare_properties(self, land_ids: List[int]) -> Dict:
        """
        2-3개 매물을 비교 분석
        
        Args:
            land_ids: 비교할 매물 ID 리스트 (2-3개)
            
        Returns:
            {
                "summary": "LLM 생성 비교 요약 (마크다운)",
                "properties": [...],  # 매물 상세 정보
                "count": 2 or 3
            }
        """
        from apps.listings.models import Land, PriceClassificationResult
        
        # 유효성 검증
        if not land_ids or len(land_ids) < 2:
            raise ValueError("최소 2개의 매물을 선택해주세요.")
        
        if len(land_ids) > 3:
            raise ValueError("최대 3개까지만 비교할 수 있습니다.")
        
        # 1. DB에서 매물 정보 조회
        properties_queryset = Land.objects.filter(land_id__in=land_ids).select_related('landbroker')
        
        # land_id를 키로 하는 딕셔너리로 변환
        properties_dict = {prop.land_id: prop for prop in properties_queryset}
        
        if len(properties_dict) != len(land_ids):
            raise ValueError("일부 매물을 찾을 수 없습니다.")
        
        # Frontend에서 전달한 순서대로 정렬 (매물1, 매물2 순서 유지)
        properties_ordered = [properties_dict[land_id] for land_id in land_ids]
        
        # 2. 매물 데이터 포맷팅 (순서 유지)
        properties_data = []
        for idx, prop in enumerate(properties_ordered, 1):
            # 기본 정보
            prop_data = {
                'property_number': idx,  # 매물 번호 (1, 2, 3)
                'land_id': prop.land_id,
                'land_num': prop.land_num,
                'address': prop.address,
                'building_type': prop.building_type,
                'deal_type': prop.deal_type or '월세',
                'deposit': prop.deposit or 0,
                'monthly_rent': prop.monthly_rent or 0,
                'jeonse_price': prop.jeonse_price or 0,
                'sale_price': prop.sale_price or 0,
            }
            
            # listing_info에서 추가 정보 추출
            if prop.listing_info and isinstance(prop.listing_info, dict):
                prop_data['area_exclusive'] = prop.listing_info.get('전용/공급면적', '-')
                prop_data['area_supply'] = prop.listing_info.get('전용/공급면적', '-')
                prop_data['floor'] = prop.listing_info.get('해당층/전체층', '-')
                prop_data['room_count'] = prop.listing_info.get('방/욕실개수', '-')
                prop_data['direction'] = prop.listing_info.get('주실기준/방향', '-')
                prop_data['parking'] = prop.listing_info.get('주차', '-')
                prop_data['heating_method'] = prop.listing_info.get('난방방식', '-')
            
            # ML 가격 예측 정보
            try:
                price_class = PriceClassificationResult.objects.filter(land_num=prop.land_num).first()
                if price_class:
                    prop_data['price_prediction'] = {
                        'prediction_class': price_class.prediction_class,
                        'prediction_label': price_class.prediction_label,
                        'prediction_label_korean': price_class.prediction_label_korean,
                        'probability_underpriced': price_class.probability_underpriced,
                        'probability_fair': price_class.probability_fair,
                        'probability_overpriced': price_class.probability_overpriced,
                    }
            except Exception as e:
                print(f"가격 예측 정보 조회 실패: {e}")
                prop_data['price_prediction'] = {}
            
            # 중개사 신뢰도 정보
            if prop.landbroker:
                prop_data['broker'] = {
                    'office_name': prop.landbroker.office_name,
                    'trust_score': prop.landbroker.trust_score or '-',
                    'trust_grade': prop.landbroker.trust_grade_display,
                }
            else:
                prop_data['broker'] = {
                    'office_name': '-',
                    'trust_score': '-',
                    'trust_grade': '-',
                }
            
            properties_data.append(prop_data)
        
        # 3. LLM 프롬프트 생성
        prompts = create_comparison_prompt(properties_data)
        
        # 4. OpenAI API 호출
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": prompts["system"]},
                    {"role": "user", "content": prompts["user"]}
                ]
            )
            
            comparison_summary = response.choices[0].message.content
            
        except Exception as e:
            print(f"OpenAI API 호출 실패: {e}")
            # 폴백: 기본 비교 메시지
            comparison_summary = self._generate_fallback_comparison(properties_data)
        
        # 5. 결과 반환
        return {
            "summary": comparison_summary,
            "properties": properties_data,
            "count": len(properties_data)
        }
    
    def _generate_fallback_comparison(self, properties: List[Dict]) -> str:
        """
        LLM 호출 실패 시 기본 비교 메시지 생성
        """
        fallback = f"""
## 📊 매물 비교

총 {len(properties)}개의 매물을 비교합니다.

"""
        for i, prop in enumerate(properties, 1):
            deposit = prop.get('deposit', 0)
            monthly_rent = prop.get('monthly_rent', 0)
            ml_pred = prop.get('price_prediction', {})
            ml_label = ml_pred.get('prediction_label_korean', '-')
            
            fallback += f"""
### 매물 {i}
- 주소: {prop.get('address', '-')}
- 가격: 보증금 {deposit:,}만원 / 월세 {monthly_rent:,}만원
- ML 예측: {ml_label}
- 중개사 신뢰도: {prop.get('broker', {}).get('trust_score', '-')}등급

"""
        
        fallback += """
**참고**: 상세 비교 분석을 생성하는 중 오류가 발생했습니다. 위의 기본 정보를 참고해주세요.
"""
        
        return fallback
