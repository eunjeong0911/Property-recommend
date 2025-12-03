from common.state import RAGState

def generate(state: RAGState) -> RAGState:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    question = state["question"]
    graph_results = state.get("graph_results", [])
    
    # Filter out duplicate property IDs (not addresses - same address can have multiple properties)
    unique_results = []
    seen_ids = set()
    
    for result in graph_results:
        # Check if result is a list (from Neo4j search)
        if isinstance(result, list):
            for item in result:
                prop_id = item.get('p.id') or item.get('id')
                if prop_id and prop_id not in seen_ids:
                    seen_ids.add(prop_id)
                    unique_results.append(item)
                elif not prop_id:
                    # If no ID, fall back to address to avoid truly identical entries
                    address = item.get('p.address') or item.get('address')
                    if address and address not in seen_ids:
                        seen_ids.add(address)
                        unique_results.append(item)
        # Check if result is a dict (single item)
        elif isinstance(result, dict):
            prop_id = result.get('p.id') or result.get('id')
            if prop_id and prop_id not in seen_ids:
                seen_ids.add(prop_id)
                unique_results.append(result)
            elif not prop_id:
                address = result.get('p.address') or result.get('address')
                if address and address not in seen_ids:
                    seen_ids.add(address)
                    unique_results.append(result)
    
    # Use unique results for context
    context = unique_results if unique_results else graph_results

    # Simple generation using LLM
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
    
    prompt = ChatPromptTemplate.from_template(
        """
        다음 검색 결과를 바탕으로 사용자의 질문에 답변해 주세요.
        
        검색 결과:
        {context}

        핵심 원칙 (Core Principles):
        1. **사용자 질문 내용 최대한 반영**
           - 사용자가 질문에서 언급한 시설/조건(예: 편의점, CCTV, 병원, 역 등)은 검색 결과에 있으면 최대한 답변에 포함하세요
           
        2. **정확성 최우선 - Hallucination 금지**
           - 검색 결과에 없는 정보는 절대 만들어내지 마세요
           - 확실하게 확인된 데이터만 제공하고, 불확실한 정보는 "정보 없음" 또는 생략하세요
           
        3. **CCTV/비상벨은 개수로만 표시**
           - "반경 내 CCTV [cctv_count]대, 비상벨 [bell_count]개" 형식
           - 거리나 시간이 아닌 개수만 표시하세요
           
        4. **시설 정보는 거리+시간 필수**
           - 시설(병원, 편의점 등)을 언급할 때는 반드시: "[시설명] (거리 약 [dist]m / 도보 약 [time]분)"
           - 이름만 쓰고 거리/시간을 생략하지 마세요

        지침:
        1. **검색 결과가 없거나 비어있는 경우**:
           - "죄송합니다. 요청하신 모든 조건을 만족하는 매물을 찾지 못했습니다."라고 정중하게 답변해 주세요.
           - "조건을 조금 완화하거나 다른 지역으로 검색해 보시겠어요?"라고 제안해 주세요.

        2. **검색 결과가 있는 경우 (Result Generation)**:
           - **선별 로직 (Selection Logic)**: 검색 결과는 관련성 순으로 정렬되어 있습니다. 리스트에서 **상위 3개 매물을 선정하여 1순위(옵션 A), 2순위(옵션 B), 3순위(옵션 C)로 제시**하세요.
           - **매물 부족 시 처리**: 만약 적합한 매물이 3개 미만이라면, **억지로 채우지 말고 찾은 만큼만(예: 1순위만, 또는 1-2순위만) 표시**하세요.
           - **절대 시설을 매물로 둔갑시키지 마세요**: 검색 결과의 `convenience_name`, `hospital_name` 등은 주변 시설일 뿐, 추천할 매물이 아닙니다. **반드시 `p.address`와 `p.bldg_type`이 명확한 데이터만 매물로 추천하세요.**
           - **사용자 질문 내용 최대한 반영**: 사용자가 질문에서 언급한 시설/조건(예: 편의점, CCTV, 병원 등)은 검색 결과에 있으면 최대한 답변에 포함하세요. 검색 결과에 없으면 "해당 정보 없음"으로 명시하세요.
           - **정확성 최우선 (절대 금지: Hallucination)**: 검색 결과에 없는 정보는 절대 만들어내거나 추측하지 마세요. 확실하게 확인된 데이터만 제공하고, 불확실한 정보는 "정보 없음" 또는 생략하세요.
           - **가격 정보 표시 (Price Info)**:
             - `trade_type_raw`가 있으면 그대로 표시 (예: "월세 1,000만원/70만원")
             - `trade_type_raw`가 없으면:
               - `monthly_rent` > 0 이면: "월세 [deposit] / [monthly_rent]"
               - `monthly_rent` == 0 이면: "전세 [deposit]"
               - `trade_type`이 매매이면: "매매 [price]"
             - (단위는 '만원' 또는 '억' 등을 적절히 사용하세요)
           - 각 옵션은 다음 형식을 반드시 지켜주세요:
           
           **1순위 (옵션 A)**
           - **주소**: [주소]
           - **타입**: [건물형태]
           - **가격**: [가격 정보 (예: 전세 1억 2000 / 관리비 5만)]
           - **역 접근성**: [가장 가까운 역 이름]까지 도보 약 [subway_station_time]분 ([subway_station_dist]m)
             *(필수: 검색 결과에 `subway_station_name`, `subway_station_dist`, `subway_station_time`이 있으면 반드시 표시하세요. 없으면 "정보 없음"으로 표시)*
           - **안전 시설**: 반경 내 CCTV [cctv_count]대, 비상벨 [bell_count]개
             *(조건부 표시: 사용자가 질문에서 CCTV나 비상벨을 언급했을 때만 이 섹션을 표시하세요. 언급 안 했으면 이 줄 전체를 생략하세요.)*
           - **가까운 시설**:
             - [시설명1] (거리 약 [facility1_dist]m / 도보 약 [facility1_time]분)
             - [시설명2] (거리 약 [facility2_dist]m / 도보 약 [facility2_time]분)
             - [시설명2] (거리 약 [facility2_dist]m / 도보 약 [facility2_time]분)
             *(주의: `subway_station_dist`와 `subway_station_time`은 위에서 이미 언급했으므로 여기서는 제외하세요. 
             **CCTV와 비상벨은 "안전 시설" 섹션에 개수로 표시하므로 여기서는 절대 포함하지 마세요.**
             그 외 검색 결과에 포함된 시설(병원, 약국, 편의점 등)을 표시하세요. **단, 같은 거리와 시간을 가진 중복 시설은 하나만 표시하세요.**)*
           - **한줄 요약**: [이 매물의 장점 요약]

        3. **데이터 정확성 및 누락 처리**:
           - `OPTIONAL MATCH`로 인해 일부 시설 정보가 없을 수 있습니다. 이 경우 "정보 없음"이라고 표기하기보다 해당 항목을 아예 생략하는 것이 깔끔합니다.
           - 30m 거리에 29분이 걸린다는 식의 비상식적인 데이터가 있다면, 데이터 그대로 표시하되 "(데이터 확인 필요)"라고 덧붙여 주세요.
           - 서로 다른 시설의 거리와 시간을 섞어 쓰지 마세요.

        4. 옵션 나열 후, **추천** 섹션을 작성해 주세요.
           - **종합 추천**: 가장 추천하는 옵션과 그 이유를 설명하세요.
           - **상황별 추천**: 특정 조건(예: 병원 접근성, 역 접근성 등)을 중시하는 경우에 대한 추천을 덧붙이세요.

        5. 마지막으로 **추가 제안**을 해주세요.
           - 비교 표 제공이나 다른 조건 검색 제안 등을 포함하세요.
        
        6. 톤앤매너: 전문적이면서도 친절하게 답변해 주세요.
        
        질문: {question}
        """
    )
    
    chain = prompt | llm | StrOutputParser()
    
    answer = chain.invoke({"question": question, "context": graph_results})
    
    state["answer"] = answer
    return state
