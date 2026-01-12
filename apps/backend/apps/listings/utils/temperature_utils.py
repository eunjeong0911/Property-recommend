import logging
from typing import Dict, Any, Optional
from ..neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

def get_land_temperatures(land_num: str) -> Dict[str, Any]:
    """
    Neo4j에서 매물의 온도 지표를 가져옵니다.
    
    Args:
        land_num: 매물 번호 (Neo4j Property 노드의 id)
        
    Returns:
        4가지 온도 지표와 세부 정보를 포함하는 딕셔너리.
    """
    # 기본값 설정
    temperatures = {
        'safety': 36.5,
        'convenience': 36.5,
        'pet': 36.5,
        'traffic': 36.5,
        'culture': 36.5,
        'pet_details': None
    }
    
    # Neo4jMetric Name mapping to API field names
    metric_map = {
        'Safety': 'safety',
        'LivingConvenience': 'convenience',
        'Pet': 'pet',
        'Traffic': 'traffic',
        'Culture': 'culture'
    }
    
    try:
        driver = Neo4jClient.get_driver()
        with driver.session() as session:
            # 매물과 연결된 모든 온도 지표(Metric) 조회
            query = """
            MATCH (p:Property {id: $land_num})-[r:HAS_TEMPERATURE]->(m:Metric)
            RETURN m.name as name, r.temperature as score, properties(r) as props
            """
            result = session.run(query, land_num=str(land_num))
            
            found_data = False
            for record in result:
                neo4j_metric_name = record['name']
                score = record['score']
                props = record['props']
                
                # 매핑된 필드명이 있으면 업데이트
                if neo4j_metric_name in metric_map:
                    api_key = metric_map[neo4j_metric_name]
                    temperatures[api_key] = float(score)
                    found_data = True
                    
                    # 반려동물 세부 정보가 있으면 추가
                    if neo4j_metric_name == 'Pet':
                        temperatures['pet_details'] = {
                            'playground': props.get('playground_count', 0),
                            'hospital': props.get('hospital_count', 0),
                            'park': props.get('park_count', 0),
                            'etc': props.get('etc_count', 0)
                        }
            
            if not found_data:
                logger.debug(f"Neo4j에서 매물 {land_num}에 대한 온도 데이터를 찾을 수 없습니다. 기본값을 사용합니다.")
                
    except Exception as e:
        logger.error(f"Neo4j 온도 데이터 조회 중 오류 발생 (land_num={land_num}): {e}")
        
    return temperatures


def get_bulk_land_temperatures(land_nums: list) -> Dict[str, Dict[str, Any]]:
    """
    여러 매물의 온도 지표를 한 번에 조회
    유사 매물 추천에 사용
    여러번 쿼리 실행 방지
    
    Returns: {land_num: {온도 정보}} 형태의 딕셔너리
    """
    if not land_nums:
        return {}
        
    land_nums = [str(num) for num in land_nums]
    results = {}
    
    # 기본값 템플릿
    default_temps = {
        'safety': 36.5,
        'convenience': 36.5,
        'pet': 36.5,
        'traffic': 36.5,
        'culture': 36.5,
        'pet_details': None
    }
    
    metric_map = {
        'Safety': 'safety',
        'LivingConvenience': 'convenience',
        'Pet': 'pet',
        'Traffic': 'traffic',
        'Culture': 'culture'
    }
    
    try:
        driver = Neo4jClient.get_driver()
        with driver.session() as session:
            query = """
            MATCH (p:Property)-[r:HAS_TEMPERATURE]->(m:Metric)
            WHERE p.id IN $land_nums
            RETURN p.id as land_id, m.name as name, r.temperature as score, properties(r) as props
            """
            
            result = session.run(query, land_nums=land_nums)
            
            for record in result:
                land_id = record['land_id']
                neo4j_metric_name = record['name']
                score = record['score']
                props = record['props']
                
                if land_id not in results:
                    results[land_id] = default_temps.copy()
                
                if neo4j_metric_name in metric_map:
                    api_key = metric_map[neo4j_metric_name]
                    results[land_id][api_key] = float(score)
                    
                    if neo4j_metric_name == 'Pet':
                        results[land_id]['pet_details'] = {
                            'playground': props.get('playground_count', 0),
                            'hospital': props.get('hospital_count', 0),
                            'park': props.get('park_count', 0),
                            'etc': props.get('etc_count', 0)
                        }
                        
    except Exception as e:
        logger.error(f"Neo4j 대량 온도 데이터 조회 중 오류 발생: {e}")
        
    # 조회되지 않은 매물에 대해서도 기본값 반환
    for land_num in land_nums:
        if land_num not in results:
            results[land_num] = default_temps.copy()
            
    return results
