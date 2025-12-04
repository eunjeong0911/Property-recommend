from common.state import RAGState

def generate(state: RAGState) -> RAGState:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    question = state["question"]
    graph_results = state.get("graph_results", [])
    sql_results = state.get("sql_results", [])
    
    print(f"[Generate] graph_results type: {type(graph_results)}")
    print(f"[Generate] sql_results count: {len(sql_results) if sql_results else 0}")
    
    # graph_results가 딕셔너리이고 'context' 키가 있는 경우 처리
    if isinstance(graph_results, dict) and 'context' in graph_results:
        graph_results = graph_results['context']
        print(f"[Generate] Extracted context, new length: {len(graph_results)}")
    
    # PostgreSQL 결과를 매물번호로 인덱싱
    sql_details = {}
    for item in sql_results:
        land_num = item.get('land_num')
        if land_num:
            sql_details[str(land_num)] = item
            print(f"[Generate] Indexed SQL detail for land_num: {land_num}")
    
    # Filter out duplicate property IDs and merge with PostgreSQL details
    unique_results = []
    seen_ids = set()
    
    for result in graph_results:
        # Check if result is a list (from Neo4j search)
        if isinstance(result, list):
            for item in result:
                prop_id = item.get('p.id') or item.get('id')
                if prop_id and prop_id not in seen_ids:
                    seen_ids.add(prop_id)
                    # PostgreSQL 상세 정보 병합
                    merged = {**item}
                    if str(prop_id) in sql_details:
                        merged['postgres_details'] = sql_details[str(prop_id)]
                        print(f"[Generate] Merged postgres_details for {prop_id}")
                    unique_results.append(merged)
                elif not prop_id:
                    address = item.get('p.address') or item.get('address')
                    if address and address not in seen_ids:
                        seen_ids.add(address)
                        unique_results.append(item)
        # Check if result is a dict (single item)
        elif isinstance(result, dict):
            prop_id = result.get('p.id') or result.get('id')
            if prop_id and prop_id not in seen_ids:
                seen_ids.add(prop_id)
                merged = {**result}
                if str(prop_id) in sql_details:
                    merged['postgres_details'] = sql_details[str(prop_id)]
                    print(f"[Generate] Merged postgres_details for {prop_id}")
                unique_results.append(merged)
            elif not prop_id:
                address = result.get('p.address') or result.get('address')
                if address and address not in seen_ids:
                    seen_ids.add(address)
                    unique_results.append(result)
    
    # Use unique results for context
    context = unique_results if unique_results else graph_results
    print(f"[Generate] Final context count: {len(context)}")

    # Simple generation using LLM
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
    
    prompt = ChatPromptTemplate.from_template(
        """
        다음 검색 결과를 바탕으로 사용자의 질문에 답변해 주세요.
        
        검색 결과 (Neo4j 위치 기반 + PostgreSQL 상세 정보):
        {context}

        데이터 구조 설명:
        - Neo4j 결과: p.id, p.address, p.bldg_type, subway_station_name, subway_station_dist 등 위치/거리 정보
        - postgres_details: 매물의 상세 정보 (PostgreSQL Land 테이블)
          - building_type: 건물 유형 (빌라주택, 아파트, 오피스텔, 원투룸)
          - trade_info: 거래 정보 (거래방식, 관리비, 융자금, 입주가능일 등)
          - listing_info: 매물 상세 (전용면적, 층수, 방/욕실 개수, 옵션 등)
          - additional_options: 추가 옵션 (풀옵션, 엘리베이터, 주차가능 등)
          - description: 상세 설명
          - agent_info: 중개사 정보
          - url: 매물 상세 페이지 URL

        핵심 원칙 (Core Principles):
        1. **PostgreSQL 상세 정보 적극 활용**
           - postgres_details가 있으면 listing_info의 옵션, 시설, 면적 등을 답변에 포함하세요
           - trade_info에서 정확한 가격, 관리비, 입주가능일 정보를 추출하세요
           - additional_options에서 풀옵션, 엘리베이터, 주차 등 편의시설 정보를 표시하세요
           
        2. **정확성 최우선 - Hallucination 금지**
           - 검색 결과에 없는 정보는 절대 만들어내지 마세요
           - 확실하게 확인된 데이터만 제공하세요
           
        3. **CCTV/비상벨은 개수로만 표시**
           - "반경 내 CCTV [cctv_count]대, 비상벨 [bell_count]개" 형식
           
        4. **시설 정보는 거리+시간 필수**
           - "[시설명] (거리 약 [dist]m / 도보 약 [time]분)"

        지침:
        1. **검색 결과가 없거나 비어있는 경우**:
           - "죄송합니다. 요청하신 조건을 만족하는 매물을 찾지 못했습니다."
           - "조건을 조금 완화하거나 다른 지역으로 검색해 보시겠어요?"

        2. **검색 결과가 있는 경우**:
           - 상위 3개 매물을 1순위, 2순위, 3순위로 제시
           - 각 옵션 형식:
           
           **1순위 (옵션 A)**
           - **주소**: [주소]
           - **타입**: [건물형태] (postgres_details.building_type 활용)
           - **가격**: [거래방식 + 가격] (postgres_details.trade_info.거래방식 활용)
           - **관리비**: [관리비 정보] (postgres_details.trade_info.관리비 활용)
           - **면적/구조**: [전용면적, 방/욕실 개수] (postgres_details.listing_info 활용)
           - **역 접근성**: [역 이름]까지 도보 약 [time]분 ([dist]m)
           - **옵션/시설**: [풀옵션, 엘리베이터, 주차 등] (postgres_details.additional_options + listing_info.생활시설 활용)
           - **입주가능일**: [입주가능일] (postgres_details.trade_info.입주가능일 활용)
           - **매물 링크**: [url] (postgres_details.url 활용)
           - **한줄 요약**: [이 매물의 장점]

        3. **데이터 누락 처리**:
           - postgres_details가 없는 매물은 Neo4j 정보만으로 표시
           - 없는 항목은 생략

        4. **추천** 섹션 작성:
           - 종합 추천과 상황별 추천

        5. **추가 제안**: 다른 조건 검색 제안
        
        6. 톤앤매너: 전문적이면서도 친절하게
        
        질문: {question}
        """
    )
    
    chain = prompt | llm | StrOutputParser()
    
    # context (병합된 결과)를 전달
    answer = chain.invoke({"question": question, "context": context})
    
    state["answer"] = answer
    return state
