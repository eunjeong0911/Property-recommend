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
        'pet_details': None
    }
    
    # Neo4jMetric Name mapping to API field names
    metric_map = {
        'Safety': 'safety',
        'LivingConvenience': 'convenience',
        'Pet': 'pet',
        'Traffic': 'traffic'
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
