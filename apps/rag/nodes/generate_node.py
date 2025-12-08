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
    print(f"[Generate] 📝 Context prepared with {len(context)} items.")
    if len(context) > 0:
        print(f"[Generate]    First item preview: {str(context[0])[:200]}...")

    # Simple generation using LLM
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
    
    prompt = ChatPromptTemplate.from_template(
        """
        다음 검색 결과를 바탕으로 사용자의 질문에 답변해 주세요.
        
        검색 결과 (Neo4j 위치 기반 + PostgreSQL 상세 정보):
        {context}

        데이터 구조 설명 (참고용):
        - Neo4j 결과: 위치/거리 정보 (p.address, subway_info 등)
          - **subway_info**: 인접한 모든 지하철역 정보 리스트
          - **facilities**: 주변 주요 시설 정보 (병원, 대학교, 편의점 등 - `{{'General Hospitals': [...], 'Universities': [...]}}`)
          - **surroundings**: 안전 시설 정보 (`{{'safety': {{'cctv_count': ..., 'bell_count': ...}}}}`)
        - postgres_details: 매물 상세 정보 (가격, 관리비, 옵션 등)

        핵심 원칙 (Core Principles):
        1. **자연스러운 답변 작성**
           - **절대** 답변에 "(Neo4j ...)", "(postgres_details ...)", "(postgres trade_info 표기)", "[위치 정보: Neo4j]" 와 같은 **시스템 내부 출처나 디버그 정보를 포함하지 마세요.**
           - 사용자는 데이터가 어디서 왔는지 알 필요가 없습니다. 그냥 정보만 제공하세요.
           - 예: "가격: 월세 1,000만원/110만원 (postgres trade_info)" -> "가격: 월세 1,000만원/110만원"

        2. **데이터 통합 및 거리 표기**
           - 위치/거리 정보는 Neo4j 결과를 사용하고, 상세 정보는 postgres_details를 사용하여 하나의 완성된 매물 정보로 만드세요.
           - **거리 표기**: Neo4j의 숫자 거리 값(distance) 뒤에 postgres_details에 있는 `distance_unit` 값을 붙여서 표현하세요.
             - 예: Neo4j `distance: 500` + RDB `distance_unit: 'm'` -> **"500m"**
           - **시설 정보 통합**: `facilities` 정보를 활용하여 이 매물이 어떤 시설(종합병원, 대학교 등)과 가까운지 설명에 포함하세요.

        3. **정확성 최우선**
           - 없는 정보를 지어내지 마세요.

        지침:
        1. **검색 결과가 없거나 비어있는 경우**:
           - "죄송합니다. 요청하신 조건을 만족하는 매물을 찾지 못했습니다."
           - "조건을 조금 완화하거나 다른 지역으로 검색해 보시겠어요?"

        2. **검색 결과가 있는 경우**:
           - 상위 3개 매물을 1순위, 2순위, 3순위로 제시
           - 각 옵션 형식:
           
           **1순위 (옵션 A)**
           - **주소**: [주소]
           - **타입**: [건물형태]
           - **가격**: [거래방식 + 가격]
           - **관리비**: [관리비 정보]
           - **면적/구조**: [전용면적, 방/욕실 개수]
           - **역 접근성**: [역1 이름](도보 [time1]분, [dist1]m), [역2 이름](도보 [time2]분, [dist2]m)
           - **주변 인프라**: [종합병원/대학교/공원 등 주요 시설 이름과 거리] (facilities 정보 활용)
           - **안전 시설**: [CCTV n대, 비상벨 n개] (surroundings 정보 활용, 없으면 생략)
           - **옵션/시설**: [풀옵션, 엘리베이터, 주차 등]
           - **입주가능일**: [입주가능일]
           - **매물 링크**: [url]
           - **한줄 요약**: [이 매물의 장점 - 특히 요청한 조건(예: 대학교 근처)과의 연관성 강조]

        3. **데이터 누락 처리**:
           - 상세 정보가 없으면 "상세 정보 없음"으로 표시

        4. **추천** 섹션 작성:
           - 종합 추천과 상황별 추천

        5. **추가 제안**: 다른 조건 검색 제안
        
        6. 톤앤매너: 전문적이면서도 친절하게. **불필요한 괄호 설명이나 출처 표기 금지.**
        
        질문: {question}
        """
    )
    
    chain = prompt | llm | StrOutputParser()
    
    # context (병합된 결과)를 전달
    print("[Generate] 🤖 Generating final answer with GPT-5-mini...")
    answer = chain.invoke({"question": question, "context": context})
    print(f"[Generate] ✅ Answer generated:\n{answer}")
    
    state["answer"] = answer
    return state
