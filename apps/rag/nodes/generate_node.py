from common.state import RAGState
import json

def generate(state: RAGState) -> RAGState:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    question = state["question"]
    graph_results = state.get("graph_results", [])
    sql_results = state.get("sql_results", [])
    search_context = state.get("search_context")
    use_cache = state.get("use_cache", False)
    
    print(f"\n{'='*60}")
    print(f"[Generate] 🚀 Starting answer generation...")
    print(f"[Generate] 📝 Question: {question}")
    print(f"[Generate] 📊 Graph results count: {len(graph_results) if isinstance(graph_results, list) else 1}")
    print(f"[Generate] 🗄️  SQL results count: {len(sql_results)}")
    print(f"{'='*60}\n")
    
    # Extract context list if nested
    if isinstance(graph_results, dict) and 'context' in graph_results:
        graph_results = graph_results['context']
    
    # Index PostgreSQL results
    print(f"[Generate] 🔗 Indexing PostgreSQL results...")
    sql_details = {}
    for item in sql_results:
        land_num = item.get('land_num')
        if land_num:
            sql_details[str(land_num)] = item
    print(f"[Generate] ✓ Indexed {len(sql_details)} SQL records")
    
    # helper to format detail list
    def format_details(details_list):
        if not details_list: return ""
        
        # Handle single dict (from head(collect(...)))
        if isinstance(details_list, dict):
            details_list = [details_list]
        
        # Ensure it's a list
        if not isinstance(details_list, list):
            return ""
        
        # details_list is list of dicts: {'name': '...', 'dist': 123.0, 'time': 1.5}
        formatted = []
        for d in details_list:
            if not isinstance(d, dict):
                continue
            name = d.get('name', 'Facility') or 'Facility'
            dist = d.get('dist') or 0
            time = d.get('time') or 0
            # Format: 'OOO (123m, 2분)'
            formatted.append(f"{name} ({int(dist)}m, {int(time)}분)")
        return ", ".join(formatted)

    # Process and Merge Results
    unique_results = []
    seen_ids = set()
    
    # Flatten if list of lists
    raw_items = []
    if isinstance(graph_results, list):
         for item in graph_results:
             if isinstance(item, list): raw_items.extend(item)
             else: raw_items.append(item)
    else:
        raw_items = [graph_results]

    for result in raw_items:
        if not isinstance(result, dict): continue
        
        prop_id = result.get('p.id') or result.get('id')
        address = result.get('p.address') or result.get('address')
        
        unique_key = prop_id if prop_id else address
        if unique_key and unique_key not in seen_ids:
            seen_ids.add(unique_key)
            merged = {**result}
            
            # Merge SQL details
            if prop_id and str(prop_id) in sql_details:
                merged['postgres_details'] = sql_details[str(prop_id)]
            else:
                # Exclude properties that failed SQL filtering or have no details
                continue

            # --- PRE-PROCESS DETAILS FOR LLM ---
            # Extract and format the specific detail lists returned by neo4j_search_node
            
            # 1. POI (Train Stations, Key Locations)
            poi_info = format_details(result.get('poi_details', []))
            
            # Helper to deduplicate POI from Infrastructure
            # If a station is already in "poi_info" (Anchor), exclude it from "trans_details" (Infra)
            poi_names = {d.get('name') for d in result.get('poi_details', [])}
            
            def filter_poi(details_list):
                 if not details_list: return []
                 return [d for d in details_list if d.get('name') not in poi_names]

            # 2. General Facilities (Convenience, Hospital, Park, Education, Pharmacy)
            fac_summary = []
            if result.get('med_details'): fac_summary.append(f"의료(병원): {format_details(result['med_details'])}")
            if result.get('pharm_details'): fac_summary.append(f"약국: {format_details(result['pharm_details'])}")
            if result.get('gen_hosp_details'): fac_summary.append(f"의료(종합/대학병원): {format_details(result['gen_hosp_details'])}")
            if result.get('conv_details'): fac_summary.append(f"편의: {format_details(result['conv_details'])}")
            if result.get('park_details'): fac_summary.append(f"공원: {format_details(result['park_details'])}")
            if result.get('edu_details'): fac_summary.append(f"교육: {format_details(result['edu_details'])}")
            
            # [Fix]: Filter out transportation items that match the Anchor (POI) to avoid duplication
            filtered_trans = filter_poi(result.get('trans_details'))
            if filtered_trans: fac_summary.append(f"교통: {format_details(filtered_trans)}")
            
            merged['formatted_infrastructure'] = " | ".join(fac_summary)
            
            # 3. Safety Facilities (Dual Display)
            # - CCTV/Bell: Count only
            # - Police/Fire: Distance and time
            safe_summary = []
            
            # Count-based facilities
            cctv_count = result.get('cctv_count', 0)
            bell_count = result.get('bell_count', 0)
            if cctv_count > 0:
                safe_summary.append(f"CCTV {cctv_count}개")
            if bell_count > 0:
                safe_summary.append(f"비상벨 {bell_count}개")
            
            # Distance-based facilities
            police_details = result.get('police_details', [])
            fire_details = result.get('fire_details', [])
            if police_details:
                safe_summary.append(f"경찰서: {format_details(police_details)}")
            if fire_details:
                safe_summary.append(f"소방서: {format_details(fire_details)}")
            
            merged['formatted_safety'] = " | ".join(safe_summary) if safe_summary else ""
            
            # 4. Station Info
            merged['formatted_poi'] = poi_info

            unique_results.append(merged)
    
    context = unique_results
    print(f"\n[Generate] ✅ Context merging complete!")
    print(f"[Generate] 📝 Prepared {len(context)} unique properties for answer generation")
    
    # Check for zero results - return immediately without LLM call
    if not context or len(context) == 0:
        print(f"[Generate] ⚠️ No results found - returning 'no match' message")
        state["answer"] = "죄송합니다. 해당 조건을 만족하는 매물이 없습니다."
        state["full_results"] = []
        return state
    
    # Store full results for Redis caching
    full_results = context
    
    # Sort by price if available (Prioritize cheaper options to ensure diversity)
    # This addresses user feedback where only the most expensive options (e.g. at the limit) were shown.
    def price_sort_key(item):
        details = item.get('postgres_details', {})
        deposit = details.get('parsed_deposit') # 만원 단위
        rent = details.get('parsed_rent', 0)    # 만원 단위
        
        if deposit is not None:
            return (deposit, rent)
        return (float('inf'), float('inf'))
        
    # Check if we have price data to sort by
    has_price_data = any(item.get('postgres_details', {}).get('parsed_deposit') is not None for item in context)
    
    if has_price_data:
        print("[Generate] 💰 Sorting results by price (low to high)...")
        context.sort(key=price_sort_key)
    
    # Select top 3 for display
    context_for_display = context[:3]
    print(f"[Generate] 📊 Showing top 3 out of {len(full_results)} total results")
    print(f"[Generate] 🤖 Sending to LLM...\n")

    # 검색 컨텍스트 정보
    context_info = ""
    if search_context:
        context_info = f"""
📌 이전 검색 조건:
- 위치: {search_context.get('location', '')}
- 적용된 필터: {', '.join(search_context.get('criteria', []))}

현재 질문은 위 조건을 기반으로 {'추가 필터링' if use_cache else '새 검색'}입니다.
"""

    # Simple generation using LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompt = ChatPromptTemplate.from_template(
        """
        당신은 유용한 부동산 AI 비서입니다. 검색 결과를 바탕으로 사용자의 질문에 친절하게 답변해 주세요.
        
        **중요: 예시 생성 금지**
        검색 결과(Context)에 포함된 매물만 소개하세요. 절대로 임의로 예시를 만들거나 가상의 매물을 생성하지 마세요.

        {context_info}

        검색 결과 (Context):
        {context}
        
        **중요: 데이터 해석 및 표기**
        Context에는 이미 포맷팅된 인프라 및 안전 정보가 포함되어 있습니다. 이를 그대로 활용하세요.
        
        - **formatted_poi**: 주요 위치/지하철역 정보 (예: "홍대입구역 (200m, 3분)")
        - **formatted_infrastructure**: 주변 편의시설 (병원, 공원, 편의점 등) 상세 정보 (이름, 거리, 시간 포함)
        - **formatted_safety**: 안전 시설 (CCTV, 경찰서 등) 정보
        
        **답변 작성 가이드라인:**
        1. **형식 유지**: 아래 형식을 정확히 지켜주세요.
        2. **정확한 정보 전달**:
           - **'주변 인프라'** 항목 작성 시, `formatted_infrastructure`에 있는 내용을 사용하여 **구체적인 이름과 거리/시간**을 명시하세요.
           - 예: "세브란스병원 (350m, 5분), 연세내과 (100m, 1분)"
           - 뭉뚱그려 "병원과 가깝습니다"라고 하지 마세요.
        3. **'역 접근성'** 항목에는 `formatted_poi` 정보를 사용하세요.

        **답변 포맷 (상위 3개 매물):**
        
        **1순위 (옵션 A)**
        - **주소**: [주소]
        - **타입**: [건물형태]
        - **가격**: [보증금/월세 또는 전세가]
        - **관리비**: [관리비 정보] (없으면 생략)
        - **면적/구조**: [전용면적], [방/욕실 개수]
        - **역 접근성**: [formatted_poi 내용 위주로 작성]
        - **주변 인프라**: [formatted_infrastructure의 모든 내용을 표시 - 편의점, 병원, 공원 등 이전 검색에서 누적된 모든 시설 정보 포함]
        - **안전 시설**: [formatted_safety 내용] (정보가 있으면 작성)
        - **한줄 요약**: [이 매물의 장점 요약]


        **2순위 (옵션 B)**
        - **주소**: [주소]
        - **타입**: [건물형태]
        - **가격**: [보증금/월세 또는 전세가]
        - **관리비**: [관리비 정보] (없으면 생략)
        - **면적/구조**: [전용면적], [방/욕실 개수]
        - **역 접근성**: [formatted_poi 내용 위주로 작성]
        - **주변 인프라**: [formatted_infrastructure 내용 중 질문과 관련된 것 위주로 작성]
        - **안전 시설**: [formatted_safety 내용] (정보가 있으면 작성)
        - **한줄 요약**: [이 매물의 장점 요약]

        **3순위 (옵션 C)**
        - **주소**: [주소]
        - **타입**: [건물형태]
        - **가격**: [보증금/월세 또는 전세가]
        - **관리비**: [관리비 정보] (없으면 생략)
        - **면적/구조**: [전용면적], [방/욕실 개수]
        - **역 접근성**: [formatted_poi 내용 위주로 작성]
        - **주변 인프라**: [formatted_infrastructure 내용 중 질문과 관련된 것 위주로 작성]
        - **안전 시설**: [formatted_safety 내용] (정보가 있으면 작성)
        - **한줄 요약**: [이 매물의 장점 요약]

        **후속 질문 생성 (매물 소개 후):**
        답변 끝에 자연스럽게 2-3개의 후속 질문을 추가하세요.
        
        사용 가능한 필터 옵션:
        - 가격: 보증금, 월세, 전세가, 매매가
        - 구조: 방/욕실 개수, 전용/공급면적, 층수
        - 시설: 엘리베이터, 주차, 난방방식
        - 입주: 입주가능일
        - 위치 세부: 병원, 편의점, 공원, 안전시설 근접성
        
        이미 적용된 조건은 다시 묻지 마세요. 자연스러운 대화 톤으로 물어보세요.
        
        **예시**:
        "... (매물 결과)
        
        💬 추가로 도와드릴까요?
        - 원하시는 가격대가 있으신가요? (예: 보증금 5000만원 이하)
        - 층수나 방 구조에 선호사항이 있으신가요?"

        질문: {question}
        """
    )
    
    chain = prompt | llm | StrOutputParser()
    
    print("[Generate] 🤖 Generating final answer with GPT-4o...")
    answer = chain.invoke({
        "question": question, 
        "context": context_for_display,  # Only send top 3 to LLM
        "context_info": context_info
    })
    print(f"[Generate] ✅ Answer generated:\n{answer}")
    
    state["answer"] = answer
    state["full_results"] = full_results  # Store all results for Redis caching
    return state
