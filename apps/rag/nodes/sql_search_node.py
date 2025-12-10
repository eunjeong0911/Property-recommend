import os
import re
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


def extract_price_conditions(question: str) -> dict:
    """
    사용자 질문에서 가격 조건 추출
    Returns: {
        'deposit_max': int or None (보증금 이하, 만원 단위),
        'deposit_min': int or None (보증금 이상, 만원 단위),
        'rent_max': int or None (월세 이하, 만원 단위),
        'rent_min': int or None (월세 이상, 만원 단위),
        'jeonse_max': int or None (전세가 이하, 만원 단위),
        'jeonse_min': int or None (전세가 이상, 만원 단위),
        'sale_max': int or None (매매가 이하, 만원 단위),
        'sale_min': int or None (매매가 이상, 만원 단위),
        'include_short_term': bool (단기임대 포함 여부),
        'trade_type_filter': str or None (특정 거래유형만 필터: '매매', '전세', '월세' 등),
    }
    """
    conditions = {}
    q = question.replace(',', '').replace(' ', '')
    
    # 사용자가 단기 거주 의도를 표현했는지 확인
    # "단기임대", "잠깐 살 방", "짧게 살 집", "단기간", "몇달만" 등
    short_term_keywords = ['단기임대', '단기', '잠깐', '짧게', '단기간', '임시', '몇달', '몇개월', '일시적']
    if any(kw in question for kw in short_term_keywords):
        conditions['include_short_term'] = True
        print(f"[SQL Search] 📋 사용자가 단기 거주 의도 감지 - 단기임대 포함")
    else:
        conditions['include_short_term'] = False
    
    # 매매/구매 의도 감지 (집을 산다, 매매, 구매, 분양, 사고싶다 등)
    sale_keywords = ['매매', '구매', '산다', '사고싶', '분양', '매수', '집사', '아파트사']
    if any(kw in question for kw in sale_keywords):
        conditions['trade_type_filter'] = '매매'
        print(f"[SQL Search] 🏠 사용자가 매매(구매) 의도 감지 - 매매 매물만 필터링")
    
    # 보증금 패턴 (만원 단위로 저장)
    deposit_patterns = [
        (r'보증금?(\d+)(?:만원?)?이하', 'deposit_max', 1),  # 5000만원 이하 → 5000
        (r'보증금?(\d+)(?:만원?)?이상', 'deposit_min', 1),
        (r'보증금?(\d+)천(?:만원?)?이하', 'deposit_max', 1000),  # 5천만원 이하 → 5000
        (r'보증금?(\d+)천(?:만원?)?이상', 'deposit_min', 1000),
        (r'보증금?(\d+)억(?:만원?)?이하', 'deposit_max', 10000),  # 1억 이하 → 10000
        (r'보증금?(\d+)억(?:만원?)?이상', 'deposit_min', 10000),
    ]
    
    # 월세 패턴 (만원 단위로 저장)
    rent_patterns = [
        (r'월세(\d+)(?:만원?)?이하', 'rent_max', 1),  # 월세 50만원 이하 → 50
        (r'월세(\d+)(?:만원?)?이상', 'rent_min', 1),
    ]
    
    # 전세 패턴 (만원 단위로 저장)
    jeonse_patterns = [
        (r'전세(?:가)?(\d+)(?:만원?)?이하', 'jeonse_max', 1),
        (r'전세(?:가)?(\d+)(?:만원?)?이상', 'jeonse_min', 1),
        (r'전세(?:가)?(\d+)천(?:만원?)?이하', 'jeonse_max', 1000),
        (r'전세(?:가)?(\d+)천(?:만원?)?이상', 'jeonse_min', 1000),
        (r'전세(?:가)?(\d+)억(?:만원?)?이하', 'jeonse_max', 10000),
        (r'전세(?:가)?(\d+)억(?:만원?)?이상', 'jeonse_min', 10000),
    ]
    
    # 매매가 패턴 (만원 단위로 저장) - "3억 이하 집 사고싶다", "매매 5억 이하" 등
    sale_patterns = [
        (r'매매(?:가)?(\d+)(?:만원?)?이하', 'sale_max', 1),
        (r'매매(?:가)?(\d+)(?:만원?)?이상', 'sale_min', 1),
        (r'매매(?:가)?(\d+)천(?:만원?)?이하', 'sale_max', 1000),
        (r'매매(?:가)?(\d+)천(?:만원?)?이상', 'sale_min', 1000),
        (r'매매(?:가)?(\d+)억(?:만원?)?이하', 'sale_max', 10000),
        (r'매매(?:가)?(\d+)억(?:만원?)?이상', 'sale_min', 10000),
    ]
    
    # 매매 의도가 있을 때 일반 가격 패턴도 매매가로 해석 (예: "3억 이하 집 사고싶다")
    if conditions.get('trade_type_filter') == '매매':
        general_price_patterns = [
            (r'(\d+)억(?:\d+)?(?:만원?)?이하', 'sale_max', 10000),
            (r'(\d+)억(?:\d+)?(?:만원?)?이상', 'sale_min', 10000),
            (r'(\d+)천(?:만원?)?이하', 'sale_max', 1000),
            (r'(\d+)천(?:만원?)?이상', 'sale_min', 1000),
        ]
        for pattern, key, multiplier in general_price_patterns:
            match = re.search(pattern, q)
            if match and key not in conditions:
                value = int(match.group(1)) * multiplier
                conditions[key] = value
    
    for pattern, key, multiplier in deposit_patterns:
        match = re.search(pattern, q)
        if match:
            value = int(match.group(1)) * multiplier
            conditions[key] = value
    
    for pattern, key, multiplier in rent_patterns:
        match = re.search(pattern, q)
        if match:
            value = int(match.group(1)) * multiplier
            conditions[key] = value
    
    for pattern, key, multiplier in jeonse_patterns:
        match = re.search(pattern, q)
        if match:
            value = int(match.group(1)) * multiplier
            conditions[key] = value
    
    for pattern, key, multiplier in sale_patterns:
        match = re.search(pattern, q)
        if match:
            value = int(match.group(1)) * multiplier
            conditions[key] = value
    
    if conditions:
        print(f"[SQL Search] 💰 Extracted price conditions (만원 단위): {conditions}")
    
    return conditions


def parse_price_from_trade_info(trade_info: dict) -> dict:
    """
    거래 정보 딕셔너리에서 가격 정보 추출 (새 스키마 대응)
    
    데이터 예시:
    {
        "거래유형": "월세",
        "보증금": "3,000만원",
        "월세": "55만원",
        "매매가": "-"
    }
    
    Returns: {'deposit': int(만원), 'rent': int(만원), 'jeonse': int(만원), 'type': str}
    """
    result = {'deposit': 0, 'rent': 0, 'jeonse': 0, 'type': ''}
    
    if not trade_info:
        return result
        
    # 1. 거래 유형 확인
    trade_type = trade_info.get('거래유형', '')
    if not trade_type or trade_type == '-':
        # fallback: 거래방식 필드가 있다면 구버전 파싱 시도 (선택 사항)
        return result
        
    result['type'] = trade_type
    
    # 2. 가격 파싱
    if trade_type == '월세' or trade_type == '단기임대':
        deposit_str = trade_info.get('보증금', '-')
        rent_str = trade_info.get('월세', '-')
        result['deposit'] = _parse_korean_number(deposit_str)
        result['rent'] = _parse_korean_number(rent_str)
        
    elif trade_type == '전세':
        deposit_str = trade_info.get('보증금', '-')
        # 전세의 경우 보증금 필드에 전세금이 들어감
        jeonse_val = _parse_korean_number(deposit_str)
        result['jeonse'] = jeonse_val
        result['deposit'] = jeonse_val # 필터링 호환성을 위해 deposit에도 저장
        
    elif trade_type == '매매':
        sale_str = trade_info.get('매매가', '-')
        sale_val = _parse_korean_number(sale_str)
        # 매매가는 deposit 필드에 저장하여 기존 필터링 로직과 호환성 유지
        result['deposit'] = sale_val
        
    return result


def _parse_korean_number(num_str: str) -> int:
    """
    한글 숫자 문자열을 만원 단위 정수로 변환
    
    예시:
    - "1억 2,500만원" → 12500
    - "5,000만원" → 5000
    - "50만원" → 50
    - "-" → 0
    """
    if not num_str or num_str == '-':
        return 0
    
    # 공백, 콤마, '원' 제거
    s = num_str.replace(' ', '').replace(',', '').replace('원', '')
    
    # 억/만 단위 처리
    uk = 0
    man = 0
    
    if '억' in s:
        parts = s.split('억')
        uk_str = parts[0]
        if uk_str.isdigit():
            uk = int(uk_str)
        
        remain = parts[1]
    else:
        remain = s
        
    if '만' in remain:
        man_str = remain.split('만')[0]
        if man_str.isdigit():
            man = int(man_str)
    elif remain.isdigit():
        # "50" 처럼 단위 없이 숫자만 있는 경우 만원 단위로 간주
        man = int(remain)
        
    return uk * 10000 + man


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
    
    # Neo4j 결과에서 매물 ID 추출 (순서 유지)
    land_nums = []
    seen_ids = set()
    
    def add_id(id_val):
        """ID 추가 헬퍼 (중복 제거 및 순서 유지)"""
        if id_val and str(id_val) not in seen_ids:
            seen_ids.add(str(id_val))
            land_nums.append(str(id_val))
            print(f"[SQL Search] Extracted ID: {id_val}")

    # graph_results가 딕셔너리이고 'context' 키가 있는 경우 처리
    if isinstance(graph_results, dict) and 'context' in graph_results:
        graph_results = graph_results['context']
        print(f"[SQL Search] Extracted context from dict, new type: {type(graph_results)}")
    
    for result in graph_results:
        # 문자열인 경우 정규식으로 p.id 추출
        if isinstance(result, str):
            ids = re.findall(r"'p\.id':\s*'(\d+)'", result)
            for id_val in ids:
                add_id(id_val)
        elif isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    add_id(item.get('p.id') or item.get('id'))
        elif isinstance(result, dict):
            # 딕셔너리에서 직접 p.id 추출
            add_id(result.get('p.id') or result.get('id'))
            # context 키가 있는 경우 재귀적으로 처리
            if 'context' in result:
                for item in result['context']:
                    if isinstance(item, dict):
                        add_id(item.get('p.id') or item.get('id'))
    
    print(f"[SQL Search] Extracted land_nums (ordered): {land_nums}")
    
    if not land_nums:
        print("[SQL Search] No land_nums found, returning empty")
        state["sql_results"] = []
        return state
    
    try:
        print(f"[SQL Search] Connecting to PostgreSQL...")
        conn = get_postgres_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 가격 조건 추출 (사용자 질문에서 직접)
        question = state.get("question", "")
        price_conditions = extract_price_conditions(question)
        
        # 거래유형 필터 (매매 의도 시 매매만)
        trade_type_filter = price_conditions.get('trade_type_filter') if price_conditions else None
        
        # 기본 쿼리 - trade_info에서 거래방식 필드를 추출
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
        
        cur.execute(query, (land_nums,))
        rows = cur.fetchall()
        
        # dict로 변환하고 가격 조건 필터링 (Python에서 처리)
        filtered_results = []
        filtered_count = 0
        
        # 단기임대 제외 여부 확인 (사용자가 명시적으로 언급하지 않은 경우)
        include_short_term = price_conditions.get('include_short_term', True) if price_conditions else True
        
        for row in rows:
            row_dict = dict(row)
            
            # trade_info JSON에서 가격 추출
            trade_info = row_dict.get('trade_info', {})
            parsed_price = parse_price_from_trade_info(trade_info)
            trade_type = parsed_price['type']
            
            deposit = parsed_price['deposit']  # 만원 단위 (매매의 경우 매매가)
            rent = parsed_price['rent']  # 만원 단위
            jeonse = parsed_price['jeonse']  # 만원 단위
            
            # 파싱된 가격 정보 저장 (나중에 정렬에 사용)
            row_dict['parsed_deposit'] = deposit
            row_dict['parsed_rent'] = rent
            row_dict['parsed_jeonse'] = jeonse
            row_dict['parsed_trade_type'] = trade_type
            
            # 거래유형 필터링 (매매 의도 시 매매만)
            if trade_type_filter:
                if trade_type != trade_type_filter:
                    filtered_count += 1
                    print(f"[SQL Filter] ❌ Excluded {row_dict['land_num']}: 거래유형 '{trade_type}' ≠ '{trade_type_filter}'")
                    continue
            
            # 가격 조건 필터링
            if price_conditions:
                try:
                    # 디버깅
                    # print(f"[SQL Filter] DEBUG: parsed_price = {parsed_price}")
                    
                    # 단기임대 제외 로직: 사용자가 단기 거주 의도를 표현하지 않았고,
                    # 보증금 또는 월세 조건이 있으면 단기임대 제외
                    if trade_type == '단기임대' and not include_short_term:
                        has_deposit_condition = 'deposit_max' in price_conditions or 'deposit_min' in price_conditions
                        has_rent_condition = 'rent_max' in price_conditions or 'rent_min' in price_conditions
                        if has_deposit_condition or has_rent_condition:
                            filtered_count += 1
                            print(f"[SQL Filter] ❌ Excluded {row_dict['land_num']}: 단기임대 제외 (사용자가 단기 거주 의도를 표현하지 않음)")
                            continue
                    
                    # 조건 확인 (모든 값이 만원 단위)
                    passed = True
                    
                    # 보증금 조건 확인 (전세/월세/단기임대 모두 적용)
                    if 'deposit_max' in price_conditions:
                        if deposit > price_conditions['deposit_max']:
                            passed = False
                            print(f"[SQL Filter] ❌ Excluded {row_dict['land_num']}: 보증금 {deposit}만원 > {price_conditions['deposit_max']}만원")
                    
                    if 'deposit_min' in price_conditions:
                        if deposit < price_conditions['deposit_min']:
                            passed = False
                            print(f"[SQL Filter] ❌ Excluded {row_dict['land_num']}: 보증금 {deposit}만원 < {price_conditions['deposit_min']}만원")
                    
                    # 월세 조건 확인
                    if 'rent_max' in price_conditions:
                        if rent > price_conditions['rent_max']:
                            passed = False
                            print(f"[SQL Filter] ❌ Excluded {row_dict['land_num']}: 월세 {rent}만원 > {price_conditions['rent_max']}만원")
                    
                    if 'rent_min' in price_conditions:
                        if rent < price_conditions['rent_min']:
                            passed = False
                            print(f"[SQL Filter] ❌ Excluded {row_dict['land_num']}: 월세 {rent}만원 < {price_conditions['rent_min']}만원")
                    
                    # 전세 조건 확인
                    if 'jeonse_max' in price_conditions:
                        if jeonse > price_conditions['jeonse_max']:
                            passed = False
                            print(f"[SQL Filter] ❌ Excluded {row_dict['land_num']}: 전세 {jeonse}만원 > {price_conditions['jeonse_max']}만원")
                    
                    if 'jeonse_min' in price_conditions:
                        if jeonse < price_conditions['jeonse_min']:
                            passed = False
                            print(f"[SQL Filter] ❌ Excluded {row_dict['land_num']}: 전세 {jeonse}만원 < {price_conditions['jeonse_min']}만원")
                    
                    # 매매가 조건 확인 (매매의 경우 deposit에 매매가가 저장됨)
                    if 'sale_max' in price_conditions:
                        if trade_type == '매매' and deposit > price_conditions['sale_max']:
                            passed = False
                            print(f"[SQL Filter] ❌ Excluded {row_dict['land_num']}: 매매가 {deposit}만원 > {price_conditions['sale_max']}만원")
                    
                    if 'sale_min' in price_conditions:
                        if trade_type == '매매' and deposit < price_conditions['sale_min']:
                            passed = False
                            print(f"[SQL Filter] ❌ Excluded {row_dict['land_num']}: 매매가 {deposit}만원 < {price_conditions['sale_min']}만원")
                    
                    if not passed:
                        filtered_count += 1
                        continue
                    else:
                        print(f"[SQL Filter] ✅ Passed {row_dict['land_num']}: {trade_type} 보증금/매매가 {deposit}만원, 월세 {rent}만원")
                        
                except Exception as e:
                    print(f"[SQL Filter] ⚠️ Price parsing error for {row_dict.get('land_num')}: {e}")
            
            filtered_results.append(row_dict)
        
        # 조건에 따른 정렬 로직
        if price_conditions:
            has_rent_condition = 'rent_max' in price_conditions or 'rent_min' in price_conditions
            has_deposit_condition = 'deposit_max' in price_conditions or 'deposit_min' in price_conditions
            has_jeonse_condition = 'jeonse_max' in price_conditions or 'jeonse_min' in price_conditions
            has_sale_condition = 'sale_max' in price_conditions or 'sale_min' in price_conditions
            
            if has_rent_condition:
                # 월세 조건이 있으면 월세(오른쪽 금액) 기준 오름차순 정렬
                print(f"[SQL Filter] 💰 Sorting by monthly RENT (ascending)...")
                filtered_results.sort(key=lambda x: (x.get('parsed_rent', float('inf')), x.get('parsed_deposit', float('inf'))))
            elif has_sale_condition or trade_type_filter == '매매':
                # 매매 조건이 있거나 매매 필터 시 매매가(deposit) 기준 오름차순 정렬
                print(f"[SQL Filter] 💰 Sorting by SALE price (ascending)...")
                filtered_results.sort(key=lambda x: (x.get('parsed_deposit', float('inf')),))
            elif has_deposit_condition or has_jeonse_condition:
                # 보증금/전세 조건이 있으면 보증금(왼쪽 금액) 기준 오름차순 정렬  
                print(f"[SQL Filter] 💰 Sorting by DEPOSIT price (ascending)...")
                filtered_results.sort(key=lambda x: (x.get('parsed_deposit', float('inf')), x.get('parsed_rent', float('inf'))))
        else:
            # 가격 조건 없으면 기존 Neo4j 순서 유지
            land_nums_order = {str(num): i for i, num in enumerate(land_nums)}
            filtered_results.sort(key=lambda x: land_nums_order.get(str(x.get('land_num')), 999))
        
        cur.close()
        conn.close()
        
        state["sql_results"] = filtered_results
        if price_conditions:
            print(f"✓ PostgreSQL에서 {len(rows)}개 조회, 가격 필터링 후 {len(filtered_results)}개 ({filtered_count}개 제외)")
        else:
            print(f"✓ PostgreSQL에서 {len(filtered_results)}개 매물 상세정보 조회 완료")
        
    except Exception as e:
        print(f"✗ PostgreSQL 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        state["sql_results"] = []
    
    return state

