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
    print(f"[LLM] 🚀 답변 생성 시작")
    print(f"{'='*60}")
    
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

            # 2. General Facilities - 요청된 시설만 표시
            requested = state.get('requested_facilities', [])
            
            # [Fallback] state에 정보가 없을 경우 질문에서 직접 추출 (TMI 방지)
            if not requested and question:
                q_temp = question.lower()
                if any(k in q_temp for k in ['편의점', '마트', 'gs25', 'cu']): requested.append('convenience')
                if any(k in q_temp for k in ['병원', '의료', '종합병원']): requested.append('hospital')
                if any(k in q_temp for k in ['약국']): requested.append('pharmacy')
                if any(k in q_temp for k in ['공원', '산책']): requested.append('park')
                if any(k in q_temp for k in ['대학', '학교', '캠퍼스']): requested.append('university')
                if any(k in q_temp for k in ['안전', '치안', 'cctv', '경찰']): requested.append('safety')
                
            fac_summary = []
            show_all = not requested
            
            if (show_all or 'hospital' in requested or 'general_hospital' in requested):
                if result.get('med_details'): fac_summary.append(f"의료(병원): {format_details(result['med_details'])}")
                if result.get('pharm_details'): fac_summary.append(f"약국: {format_details(result['pharm_details'])}")
                if result.get('gen_hosp_details'): fac_summary.append(f"의료(종합/대학병원): {format_details(result['gen_hosp_details'])}")
            if (show_all or 'convenience' in requested):
                if result.get('conv_details'): fac_summary.append(f"편의: {format_details(result['conv_details'])}")
            if (show_all or 'park' in requested):
                if result.get('park_details'): fac_summary.append(f"공원: {format_details(result['park_details'])}")
            if (show_all or 'university' in requested):
                if result.get('edu_details'): fac_summary.append(f"교육: {format_details(result['edu_details'])}")
            
            # [Fix]: Filter out transportation items that match the Anchor (POI) to avoid duplication
            filtered_trans = filter_poi(result.get('trans_details'))
            if filtered_trans: fac_summary.append(f"교통: {format_details(filtered_trans)}")
            
            merged['formatted_infrastructure'] = " | ".join(fac_summary)

            
            # 3. Safety Facilities (Dual Display)
            safe_summary = []
            
            # 안전 정보는 'safety' 요청이 있거나 show_all일 때만 표시
            if (show_all or 'safety' in requested):
                cctv_count = result.get('cctv_count', 0)
                bell_count = result.get('bell_count', 0)
                if cctv_count > 0:
                    safe_summary.append(f"CCTV {cctv_count}개")
                if bell_count > 0:
                    safe_summary.append(f"비상벨 {bell_count}개")
                
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
            
            # 6. 외부 URL 제거 (LLM이 내부 링크만 사용하도록)
            if 'url' in postgres_details:
                del postgres_details['url']

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
    
    # ------------------------------------------------------------------
    # [Input Diet] LLM 입력 데이터 최적화
    # ------------------------------------------------------------------
    slim_context = []
    
    for item in context_for_display:
        new_item = item.copy()
        
        # 1. postgres_details 경량화 (White-listing)
        details = item.get('postgres_details', {})
        slim_details = {}
        
        whitelist_keys = ['address', 'trade_info', 'listing_info', 'floor_info', 'direction']
        for k in whitelist_keys:
            if k in details:
                slim_details[k] = details[k]
        
        # 2. 가격 정보 Pre-formatting (토큰 절약)
        deposit = details.get('parsed_deposit')
        rent = details.get('parsed_rent')
        jeonse = details.get('parsed_jeonse')
        sale = details.get('parsed_sale')
        
        price_str = str(details.get('trade_info', '-'))
        try:
            trade_type = details.get('type')
            if trade_type == '월세' and deposit is not None:
                price_str = f"보증금 {deposit}/{rent}"
            elif trade_type == '전세' and jeonse is not None:
                price_str = f"전세 {jeonse}"
            elif trade_type == '매매' and sale is not None:
                price_str = f"매매 {sale}"
            elif deposit is not None and rent is not None:
                 price_str = f"{deposit}/{rent}"
        except:
            pass
            
        slim_details['formatted_price'] = price_str
        new_item['postgres_details'] = slim_details
        
        # 3. 불필요한 중간 데이터 삭제
        for key in ['poi_details', 'med_details', 'pharm_details', 'conv_details', 'park_details', 'edu_details', 'trans_details', 'police_details', 'fire_details']:
             if key in new_item:
                 del new_item[key]
                 
        slim_context.append(new_item)

    # Input Size 로깅
    import json
    input_str = json.dumps(slim_context, ensure_ascii=False)
    print(f"[Generate] 📉 Optimized Context Size: {len(str(context_for_display))} -> {len(input_str)} chars")
    print(f"[Generate] 🤖 Sending to LLM (Parallel Batch)...\n")

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
    
    # ------------------------------------------------------------------
    # [Parallel Generation] 병렬 생성 (분신술 전략)
    # ------------------------------------------------------------------
    # 1. 배치 입력 준비
    batch_inputs = []
    for i, item in enumerate(slim_context):
        # 마지막 항목인지 확인
        is_last = (i == len(slim_context) - 1)
        
        # 추가 질문 섹션 준비 (마지막 항목에만 포함)
        followup_section = ""
        if is_last:
            followup_section = f"\n💬 추가질문 2개 제안\n질문: {question}"
            
        batch_inputs.append({
            "rank": f"{i+1}순위",
            "context_info": context_info if i == 0 else "", # 컨텍스트는 첫 번째만 줘도 충분하지만 다 줘도 무방
            # LLM에게는 매물 하나만 리스트로 전달 (그래야 기존 포맷 유지 쉬움)
            "context": [item], 
            "followup_section": followup_section
        })
        
    # 2. 단일 매물용 프롬프트 정의
    single_prompt = ChatPromptTemplate.from_template(
        """부동산 AI. 매물 1개 요약.
{context_info}
**매물**: {context}

**포맷**:
**{rank}**
- 주소: [postgres_details.address]
- 가격: [postgres_details.formatted_price]
- 면적: [postgres_details.listing_info]
- 역: [formatted_poi]
- 시설: [formatted_infrastructure]
- 안전: [formatted_safety] (있으면)
👉 [detail_link]
{followup_section}"""
    )
    
    chain = single_prompt | llm | StrOutputParser()
    
    print(f"[Generate] 🚀 Executing parallel batch generation (Workers: {len(batch_inputs)})...")
    
    # 3. 병렬 실행 (Batch)
    
    # batch 호출로 병렬 처리 (속도 3배 향상)
    results = chain.batch(batch_inputs)
    
    # 4. 결과 합치기
    answer = "\n\n".join(results)



    
    llm_elapsed = int((time.time() - start_time) * 1000)
    print(f"[LLM] ✅ 완료: {len(context)}개 매물 답변 | 시간: {llm_elapsed}ms")
    
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
