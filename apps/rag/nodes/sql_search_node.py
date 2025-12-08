import os
import psycopg2
from psycopg2.extras import RealDictCursor
from common.state import RAGState


def get_postgres_connection():
    """PostgreSQL 연결 생성"""
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )


def search(state: RAGState) -> RAGState:
    """
    Neo4j 검색 결과에서 매물 ID를 추출하여
    PostgreSQL Land 테이블에서 상세 정보를 조회
    """
    import re
    
    graph_results = state.get("graph_results", [])
    
    print(f"[SQL Search] graph_results type: {type(graph_results)}")
    print(f"[SQL Search] graph_results: {graph_results[:500] if isinstance(graph_results, str) else graph_results}")
    
    if not graph_results:
        state["sql_results"] = []
        return state
    
    # Neo4j 결과에서 매물 ID 추출
    land_nums = set()
    
    # graph_results가 딕셔너리이고 'context' 키가 있는 경우 처리
    if isinstance(graph_results, dict) and 'context' in graph_results:
        graph_results = graph_results['context']
        print(f"[SQL Search] Extracted context from dict, new type: {type(graph_results)}")
    
    for result in graph_results:
        print(f"[SQL Search] Processing result type: {type(result)}")
        
        # 문자열인 경우 정규식으로 p.id 추출
        if isinstance(result, str):
            # 'p.id': '18287419' 패턴 매칭
            ids = re.findall(r"'p\.id':\s*'(\d+)'", result)
            for id_val in ids:
                land_nums.add(id_val)
                print(f"[SQL Search] Extracted ID from string: {id_val}")
        elif isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    land_num = item.get('p.id') or item.get('id')
                    if land_num:
                        land_nums.add(str(land_num))
                        print(f"[SQL Search] Extracted ID from list item: {land_num}")
        elif isinstance(result, dict):
            # 딕셔너리에서 직접 p.id 추출
            land_num = result.get('p.id') or result.get('id')
            if land_num:
                land_nums.add(str(land_num))
                print(f"[SQL Search] Extracted ID from dict: {land_num}")
            # context 키가 있는 경우 재귀적으로 처리
            if 'context' in result:
                for item in result['context']:
                    if isinstance(item, dict):
                        land_num = item.get('p.id') or item.get('id')
                        if land_num:
                            land_nums.add(str(land_num))
                            print(f"[SQL Search] Extracted ID from context: {land_num}")
    
    print(f"[SQL Search] Extracted land_nums: {land_nums}")
    
    if not land_nums:
        print("[SQL Search] No land_nums found, returning empty")
        state["sql_results"] = []
        return state
    
    try:
        print(f"[SQL Search] Connecting to PostgreSQL...")
        conn = get_postgres_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Land 테이블에서 상세 정보 조회
        query = """
            SELECT 
                land_num,
                building_type,
                address,
                deal_type,
                url,
                images,
                trade_info,
                listing_info,
                additional_options,
                description,
                agent_info,
                like_count,
                view_count,
                'm' as distance_unit
            FROM land
            WHERE land_num = ANY(%s)
        """
        
        cur.execute(query, (list(land_nums),))
        rows = cur.fetchall()
        
        # dict로 변환하여 저장
        sql_results = []
        for row in rows:
            sql_results.append(dict(row))
        
        cur.close()
        conn.close()
        
        state["sql_results"] = sql_results
        print(f"✓ PostgreSQL에서 {len(sql_results)}개 매물 상세정보 조회 완료")
        
    except Exception as e:
        print(f"✗ PostgreSQL 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        state["sql_results"] = []
    
    return state
