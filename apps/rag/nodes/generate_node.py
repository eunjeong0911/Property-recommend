from common.state import RAGState
from common.search_logging import log_user_search
import json
import time

def generate(state: RAGState) -> RAGState:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    # 검색 시작 시간 기록 (로깅용)
    start_time = time.time()
    
    question = state["question"]
    session_id = state.get("session_id")
    graph_results = state.get("graph_results", [])
    sql_results = state.get("sql_results", [])
    search_context = state.get("search_context")
    use_cache = state.get("use_cache", False)
    price_conditions = state.get("price_conditions", {})
    
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
        
        unique_key = prop_id
        if unique_key and unique_key not in seen_ids:
            seen_ids.add(unique_key)
            merged = {**result}
            
            # Merge SQL details (필수! Neo4j에는 ID만 있고 주소는 PostgreSQL에 있음)
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
            
            # 5. Pre-generate detail link (확실한 링크 생성!)
            postgres_details = merged.get('postgres_details', {})
            land_id = postgres_details.get('land_id')
            if land_id:
                merged['detail_link'] = f"[📋 상세보기](/landDetail/{land_id})"
            else:
                merged['detail_link'] = ""

            unique_results.append(merged)
    
    context = unique_results
    print(f"\n[Generate] ✅ Context merging complete!")
    print(f"[Generate] 📝 Prepared {len(context)} unique properties for answer generation")
    
    # Check for zero results - return immediately without LLM call
    if not context or len(context) == 0:
        print(f"[Generate] ⚠️ No results found - returning 'no match' message")
        state["answer"] = "죄송합니다. 해당 조건을 만족하는 매물이 없습니다."
        state["full_results"] = []
        
        # 결과 없음도 로그 저장 (Requirements 1.1, 6.4)
        search_duration_ms = int((time.time() - start_time) * 1000)
        filters = {}
        if price_conditions:
            filters['price_conditions'] = price_conditions
        if use_cache:
            filters['use_cache'] = True
        
        log_user_search(
            query=question,
            result_ids=[],
            filters=filters,
            session_id=session_id,
            search_duration_ms=search_duration_ms,
            search_type='rag'
        )
        print(f"[Generate] 📝 Search log queued (no results): {search_duration_ms}ms")
        
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
    
    # [Optimized]: 프롬프트 압축 (~800 토큰 → ~400 토큰) - LLM 응답 50% 빨라짐
    prompt = ChatPromptTemplate.from_template(
        """부동산 AI. 검색된 매물만 소개 (가상 금지).
{context_info}
**검색결과**: {context}

**포맷** (상위 3개):
**1순위**
- 주소: [postgres_details.address]
- 가격: [postgres_details.trade_info]
- 면적: [postgres_details.listing_info]
- 역: [formatted_poi]
- 시설: [formatted_infrastructure]
- 안전: [formatted_safety] (있으면)
👉 [detail_link]

**2순위** / **3순위** - 동일 포맷

💬 추가질문 2개 제안
질문: {question}"""
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
    
    # ==========================================================================
    # 검색 로그 저장 (Requirements 1.1, 6.4)
    # ==========================================================================
    # 검색 소요 시간 계산
    search_duration_ms = int((time.time() - start_time) * 1000)
    
    # 결과 매물 ID 목록 추출
    result_ids = []
    for item in full_results:
        prop_id = item.get('p.id') or item.get('id')
        if prop_id:
            result_ids.append(str(prop_id))
    
    # 필터 조건 수집
    filters = {}
    if price_conditions:
        filters['price_conditions'] = price_conditions
    if use_cache:
        filters['use_cache'] = True
    if search_context:
        filters['search_context'] = {
            'location': search_context.get('location', ''),
            'criteria': search_context.get('criteria', [])
        }
    
    # 비동기 로그 저장
    log_user_search(
        query=question,
        result_ids=result_ids,
        filters=filters,
        session_id=session_id,
        search_duration_ms=search_duration_ms,
        search_type='rag'
    )
    print(f"[Generate] 📝 Search log queued: {len(result_ids)} results, {search_duration_ms}ms")
    
    return state
