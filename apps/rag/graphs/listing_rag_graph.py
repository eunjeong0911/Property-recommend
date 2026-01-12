from typing import List
from langgraph.graph import StateGraph, END
from common.state import RAGState
from nodes import sql_search_node, vector_search_node, generate_node, neo4j_search_node, es_search_node, query_analyzer_node, soft_filter_rerank_node

def create_rag_graph():
    """
    RAG 그래프 생성 (순차적 파이프라인 + 검색 전략 분기 + 멀티턴 인터럽트)
    
    검색 전략:
    1. neo4j_only: Neo4j → SQL (위치/시설 기반)
    2. keyword_only: ES Keyword → SQL (가격/타입 기반)
    3. neo4j_keyword: Neo4j → ES Keyword → SQL (위치 + 가격)
    4. keyword_vector: ES Keyword → Vector Rerank → SQL (가격 + 소프트 필터)
    5. full: Neo4j → ES Keyword → Vector Rerank → SQL (복합 조건)
    
    흐름:
    query_analyzer → [조건 완성?] → Yes: [전략별 파이프라인] → sql_search → generate
                       ↓ No
                    interrupt_response → END (후속 질문 반환)
    """
    workflow = StateGraph(RAGState)
    
    # ==================================================================
    # 노드 등록
    # ==================================================================
    workflow.add_node("query_analyzer", query_analyzer_node.analyze)
    
    # 멀티턴 인터럽트 응답 노드
    workflow.add_node("interrupt_response", interrupt_response_node)
    
    # 검색 노드들 (순차 실행)
    workflow.add_node("neo4j_search", neo4j_search_node.search)
    workflow.add_node("es_keyword_search", es_keyword_search_node)
    workflow.add_node("vector_rerank", soft_filter_rerank_node.rerank)  # 벡터 재정렬
    
    # 최종 처리 노드들
    workflow.add_node("sql_search", sql_search_node.search)
    workflow.add_node("generate", generate_node.generate)
    
    # ==================================================================
    # 엣지 정의
    # ==================================================================
    
    # 진입점
    workflow.set_entry_point("query_analyzer")
    
    # query_analyzer → 조건 완성 여부 체크 → 검색 전략 분기 OR 인터럽트
    def route_after_analyzer(state: RAGState) -> str:
        """
        조건 완성 여부에 따른 분기:
        - 에러 발생: interrupt_response → 에러 메시지 반환
        - 조건 미완성: interrupt_response → 후속 질문 반환
        - 조건 완성: 검색 전략에 따라 분기
        """
        # ★★★ 에러 타입 체크 (관련 없는 질문, 서울 외 지역 등) ★★★
        error_type = state.get("error_type")
        if error_type:
            print(f"[Router] 🚫 에러 감지: {error_type} → 인터럽트 응답")
            return "interrupt"
        
        conversation_complete = state.get("conversation_complete", False)
        
        if not conversation_complete:
            # 조건 미완성 → 인터럽트
            print(f"[Router] ❓ 조건 미완성 → 인터럽트 응답")
            return "interrupt"
        
        # 조건 완성 → 검색 전략 분기
        strategy = state.get("search_strategy", "neo4j_keyword")
        print(f"[Router] 🎯 조건 완성, 검색 전략: {strategy}")
        
        if strategy == "neo4j_only":
            return "neo4j_only"
        elif strategy == "keyword_only":
            return "keyword_only"
        elif strategy == "neo4j_keyword":
            return "neo4j_keyword"
        elif strategy == "keyword_vector":
            return "keyword_vector"
        elif strategy == "full":
            return "full"
        else:
            return "neo4j_keyword"
    
    workflow.add_conditional_edges(
        "query_analyzer",
        route_after_analyzer,
        {
            "interrupt": "interrupt_response",
            "neo4j_only": "neo4j_search",
            "keyword_only": "es_keyword_search",
            "neo4j_keyword": "neo4j_search",
            "keyword_vector": "es_keyword_search",
            "full": "neo4j_search"
        }
    )
    
    # interrupt_response → END (후속 질문 반환하고 종료)
    workflow.add_edge("interrupt_response", END)
    
    # 각 전략별 후속 라우팅
    def route_after_neo4j(state: RAGState) -> str:
        """Neo4j 검색 후 라우팅"""
        strategy = state.get("search_strategy", "neo4j_keyword")
        
        if strategy == "neo4j_only":
            return "sql_search"
        elif strategy in ["neo4j_keyword", "full"]:
            return "es_keyword_search"
        else:
            return "sql_search"
    
    workflow.add_conditional_edges(
        "neo4j_search",
        route_after_neo4j,
        {
            "sql_search": "sql_search",
            "es_keyword_search": "es_keyword_search"
        }
    )
    
    def route_after_keyword(state: RAGState) -> str:
        """ES Keyword 검색 후 라우팅"""
        strategy = state.get("search_strategy", "neo4j_keyword")
        
        if strategy in ["keyword_vector", "full"]:
            return "vector_rerank"
        else:
            return "sql_search"
    
    workflow.add_conditional_edges(
        "es_keyword_search",
        route_after_keyword,
        {
            "sql_search": "sql_search",
            "vector_rerank": "vector_rerank"
        }
    )
    
    # vector_rerank → sql_search
    workflow.add_edge("vector_rerank", "sql_search")
    
    # sql_search → generate
    workflow.add_edge("sql_search", "generate")
    
    return workflow.compile()


def es_keyword_search_node(state: RAGState) -> RAGState:
    """
    ES 키워드 기반 검색/재정렬 노드
    
    - 이전 단계 결과가 있으면: 가격/타입 조건으로 재정렬 (결과 유지)
    - 이전 단계 결과가 없으면: 새 검색
    
    ★ 스타일 태그 검색 지원 (Requirements 1.2, 8.4):
    - soft_filters: style_tags 필드에서 검색
    - unmapped_styles: search_text 필드에서 검색
    """
    hard_filters = state.get("hard_filters", {})
    existing_results = state.get("graph_results", [])
    
    # ★ 스타일 필터 추출 (Requirements 1.2, 8.4)
    soft_filters = state.get("soft_filters", [])  # 매핑된 스타일 태그
    unmapped_styles = state.get("unmapped_styles", [])  # 매핑되지 않은 스타일 키워드
    
    print(f"\n{'='*60}")
    print(f"[ES Keyword] 🔍 가격/타입/스타일 기반 검색")
    print(f"[ES Keyword] 📋 하드 필터: {hard_filters}")
    print(f"[ES Keyword] 🎨 소프트 필터 (스타일 태그): {soft_filters}")
    print(f"[ES Keyword] 🔤 매핑되지 않은 스타일: {unmapped_styles}")
    print(f"[ES Keyword] 📊 기존 결과: {len(existing_results)}개")
    print(f"{'='*60}\n")
    
    # 기존 결과가 있고, 가격/타입/스타일 필터가 없으면 스킵
    has_price_filter = hard_filters.get("max_deposit") or hard_filters.get("max_rent") or hard_filters.get("min_deposit")
    has_type_filter = hard_filters.get("building_type") or hard_filters.get("deal_type")
    has_style_filter = bool(soft_filters) or bool(unmapped_styles)
    
    if existing_results and not has_price_filter and not has_type_filter and not has_style_filter:
        print(f"[ES Keyword] ⏭️ 가격/타입/스타일 필터 없음 - 기존 결과 유지")
        return state
    
    try:
        from elasticsearch import Elasticsearch
        import os
        
        es_host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
        es_port = os.getenv("ELASTICSEARCH_PORT", "9200")
        es_url = f"http://{es_host}:{es_port}"
        es_index = os.getenv("ES_INDEX_NAME", "realestate_listings")
        
        es = Elasticsearch(hosts=[es_url], request_timeout=30)
        
        # bool 쿼리 빌드
        must_clauses = []
        filter_clauses = []
        must_not_clauses = []
        
        # 기존 결과가 있으면 해당 ID들만 필터링
        if existing_results:
            existing_ids = [str(r.get("id", "")) for r in existing_results if r.get("id")]
            if existing_ids:
                filter_clauses.append({"terms": {"land_num": existing_ids}})
        
        # 가격/타입 필터 적용 (기존 결과가 있으면 더 관대하게)
        building_type = hard_filters.get("building_type")
        if building_type and not existing_results:  # 새 검색일 때만 building_type 필터
            filter_clauses.append({"term": {"building_type.keyword": building_type}})
        
        # ★★★ 거래 유형은 항상 적용 (사용자가 명시적으로 선택한 조건) ★★★
        deal_type = hard_filters.get("deal_type")
        if deal_type:
            filter_clauses.append({"term": {"deal_type.keyword": deal_type}})
            print(f"[ES Keyword] 🏠 거래유형 필터 적용: {deal_type}")
        
        # 보증금 범위 (항상 적용)
        max_deposit = hard_filters.get("max_deposit")
        min_deposit = hard_filters.get("min_deposit")
        if max_deposit or min_deposit:
            deposit_range = {"range": {"deposit": {}}}
            if max_deposit:
                deposit_range["range"]["deposit"]["lte"] = max_deposit
            if min_deposit:
                deposit_range["range"]["deposit"]["gte"] = min_deposit
            filter_clauses.append(deposit_range)
        
        # 월세 범위 (항상 적용)
        max_rent = hard_filters.get("max_rent")
        if max_rent:
            filter_clauses.append({"range": {"monthly_rent": {"lte": max_rent}}})

        # 방향 필터 (남향 등)
        direction = hard_filters.get("direction")
        if direction:
            # search_text에서 방향 키워드 검색
            must_clauses.append({
                "match": {
                    "search_text": direction
                }
            })
            print(f"[ES Keyword] 🧭 방향 필터 적용: {direction}")

        # 기피 층수 필터 (1층, 반지하)
        excluded_floors = hard_filters.get("excluded_floors", [])
        for ef in excluded_floors:
            if ef == "1층":
                # '1층'이 포함된 매물 제외 (search_text 기준)
                must_not_clauses.append({
                    "match_phrase": {
                        "search_text": "1층"
                    }
                })
            elif ef == "반지하":
                 must_not_clauses.append({
                    "match_phrase": {
                        "search_text": "반지하"
                    }
                })
            elif ef == "탑층":
                 must_not_clauses.append({
                    "match_phrase": {
                        "search_text": "탑층"
                    }
                })
        if excluded_floors:
            print(f"[ES Keyword] 🚫 층수 제외 필터 적용: {excluded_floors}")
        
        # 키워드 검색 (위치 등) - 기존 결과가 없을 때만
        if not existing_results:
            location = hard_filters.get("location")
            if location:
                must_clauses.append({
                    "multi_match": {
                        "query": location,
                        "fields": ["address^3", "search_text^2"],
                        "type": "best_fields"
                    }
                })
        
        # ★★★ 스타일 태그 검색 (Requirements 1.2, 8.4) ★★★
        # 매핑된 스타일 태그는 style_tags 필드에서 검색
        if soft_filters:
            filter_clauses.append({
                "terms": {"style_tags.keyword": soft_filters}
            })
            print(f"[ES Keyword] 🎨 스타일 태그 필터 적용: {soft_filters}")
        
        # 매핑되지 않은 스타일 키워드는 search_text 필드에서 검색
        if unmapped_styles:
            for style in unmapped_styles:
                must_clauses.append({
                    "match": {
                        "search_text": {
                            "query": style,
                            "boost": 1.5
                        }
                    }
                })
            print(f"[ES Keyword] 🔤 매핑되지 않은 스타일 검색: {unmapped_styles}")
        
        # 쿼리 빌드
        query = {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}],
                "filter": filter_clauses if filter_clauses else [],
                "must_not": must_not_clauses if must_not_clauses else []
            }
        }
        
        response = es.search(
            index=es_index,
            query=query,
            size=50,
            _source=["land_num", "address", "search_text", "deposit", "monthly_rent", "building_type", "deal_type"]
        )
        
        # 결과 파싱
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            results.append({
                "id": source.get("land_num", hit["_id"]),
                "address": source.get("address", ""),
                "search_text": source.get("search_text", ""),
                "deposit": source.get("deposit", 0),
                "monthly_rent": source.get("monthly_rent", 0),
                "total_score": hit["_score"],
                "source": "es_keyword"
            })
        
        print(f"[ES Keyword] ✅ {len(results)}개 매물 발견")
        
        # ★★★ 역 정보 보강 (Enrichment) ★★★
        # ES 결과에는 역 정보(poi_details)가 없으므로 Neo4j에서 가져옴
        if results:
            from nodes.neo4j_search_node import enrich_properties_with_stations
            prop_ids = [str(r['id']) for r in results]
            enriched_data = enrich_properties_with_stations(prop_ids)
            
            # ID별로 매핑
            station_map = {str(e['id']): e['poi_details'] for e in enriched_data}
            for r in results:
                r['poi_details'] = station_map.get(str(r['id']), [])
            
            print(f"[ES Keyword] 🚇 {len(results)}개 매물 역 정보 보강 완료")
        
        # =====================================================================
        # ★★★ 자동 폴백 메커니즘 (Requirements 1.3) ★★★
        # 결과가 0개이고 스타일 필터가 적용된 경우, 스타일 필터 제외 후 재검색
        # =====================================================================
        if len(results) == 0 and has_style_filter and not state.get("style_filter_removed", False):
            print(f"[ES Keyword] ⚠️ 스타일 필터로 결과 0개 → 스타일 제외 재검색 시도")
            
            # 스타일 필터 제외하고 재검색
            state["style_filter_removed"] = True
            state["original_soft_filters"] = soft_filters.copy() if soft_filters else []
            state["original_unmapped_styles"] = unmapped_styles.copy() if unmapped_styles else []
            
            # 스타일 필터 제거
            state["soft_filters"] = []
            state["unmapped_styles"] = []
            
            # 스타일 필터 없이 쿼리 재빌드
            fallback_must_clauses = []
            fallback_filter_clauses = []
            fallback_must_not_clauses = []
            
            # 기존 결과가 있으면 해당 ID들만 필터링
            if existing_results:
                existing_ids = [str(r.get("id", "")) for r in existing_results if r.get("id")]
                if existing_ids:
                    fallback_filter_clauses.append({"terms": {"land_num": existing_ids}})
            
            # 거래 유형 필터
            if deal_type:
                fallback_filter_clauses.append({"term": {"deal_type.keyword": deal_type}})
            
            # 건물 타입 필터
            if building_type:
                fallback_filter_clauses.append({"term": {"building_type.keyword": building_type}})
            
            # 보증금 범위
            if max_deposit or min_deposit:
                deposit_range = {"range": {"deposit": {}}}
                if max_deposit:
                    deposit_range["range"]["deposit"]["lte"] = max_deposit
                if min_deposit:
                    deposit_range["range"]["deposit"]["gte"] = min_deposit
                fallback_filter_clauses.append(deposit_range)
            
            # 월세 범위
            if max_rent:
                fallback_filter_clauses.append({"range": {"monthly_rent": {"lte": max_rent}}})
            
            # 방향 필터
            if direction:
                fallback_must_clauses.append({"match": {"search_text": direction}})
            
            # 층수 제외 필터
            for ef in excluded_floors:
                if ef == "1층":
                    fallback_must_not_clauses.append({"match_phrase": {"search_text": "1층"}})
                elif ef == "반지하":
                    fallback_must_not_clauses.append({"match_phrase": {"search_text": "반지하"}})
                elif ef == "탑층":
                    fallback_must_not_clauses.append({"match_phrase": {"search_text": "탑층"}})
            
            # 위치 검색 (기존 결과가 없을 때만)
            if not existing_results:
                location = hard_filters.get("location")
                if location:
                    fallback_must_clauses.append({
                        "multi_match": {
                            "query": location,
                            "fields": ["address^3", "search_text^2"],
                            "type": "best_fields"
                        }
                    })
            
            # 폴백 쿼리 빌드 (스타일 필터 제외)
            fallback_query = {
                "bool": {
                    "must": fallback_must_clauses if fallback_must_clauses else [{"match_all": {}}],
                    "filter": fallback_filter_clauses if fallback_filter_clauses else [],
                    "must_not": fallback_must_not_clauses if fallback_must_not_clauses else []
                }
            }
            
            print(f"[ES Keyword] 🔄 스타일 제외 폴백 검색 실행...")
            
            fallback_response = es.search(
                index=es_index,
                query=fallback_query,
                size=50,
                _source=["land_num", "address", "search_text", "deposit", "monthly_rent", "building_type", "deal_type"]
            )
            
            # 폴백 결과 파싱
            fallback_results = []
            for hit in fallback_response["hits"]["hits"]:
                source = hit["_source"]
                fallback_results.append({
                    "id": source.get("land_num", hit["_id"]),
                    "address": source.get("address", ""),
                    "search_text": source.get("search_text", ""),
                    "deposit": source.get("deposit", 0),
                    "monthly_rent": source.get("monthly_rent", 0),
                    "total_score": hit["_score"],
                    "source": "es_keyword_fallback"
                })
            
            print(f"[ES Keyword] ✅ 스타일 제외 폴백 결과: {len(fallback_results)}개 매물 발견")
            
            # 폴백 결과로 대체
            results = fallback_results
        
        # =====================================================================
        # Low Result Fallback: 결과가 3개 이하면 필터 제거 제안 (Requirements 2.1, 7.2)
        # =====================================================================
        LOW_RESULT_THRESHOLD = 3
        applied_optional_filters = []
        
        # ★★★ 필터 이름 한글 매핑 (사용자 친화적 메시지용) ★★★
        FILTER_NAME_MAPPING = {
            "direction": "방향",
            "excluded_floors": "층수 제외",
            "max_rent": "월세 상한",
            "max_deposit": "보증금 상한",
            "min_deposit": "보증금 하한",
            "options": "옵션",
            "style": "스타일",
            "unmapped_style": "스타일 키워드",
            "building_type": "건물 유형",
        }
        
        # ★★★ 이미 제거된 필터 목록 확인 (무한 루프 방지) ★★★
        removed_filters = state.get("removed_filters", [])
        
        # 제거 가능한 필터 식별 (필수가 아닌 조건들, 이미 제거된 것 제외)
        # 우선순위: 스타일 > 방향 > 층수 > 옵션 > 가격
        
        # 1. 스타일 필터 (가장 먼저 제거 제안)
        current_soft_filters = state.get("soft_filters", [])
        if current_soft_filters and "style" not in removed_filters:
            style_str = ", ".join(current_soft_filters[:2]) if len(current_soft_filters) > 2 else ", ".join(current_soft_filters)
            applied_optional_filters.append(("style", style_str, FILTER_NAME_MAPPING["style"]))
        
        # 2. 매핑되지 않은 스타일 키워드
        current_unmapped_styles = state.get("unmapped_styles", [])
        if current_unmapped_styles and "unmapped_style" not in removed_filters:
            unmapped_str = ", ".join(current_unmapped_styles[:2]) if len(current_unmapped_styles) > 2 else ", ".join(current_unmapped_styles)
            applied_optional_filters.append(("unmapped_style", unmapped_str, FILTER_NAME_MAPPING["unmapped_style"]))
        
        # 3. 방향 필터
        if hard_filters.get("direction") and "direction" not in removed_filters:
            applied_optional_filters.append(("direction", hard_filters.get("direction"), FILTER_NAME_MAPPING["direction"]))
        
        # 4. 층수 제외 필터
        if hard_filters.get("excluded_floors") and "excluded_floors" not in removed_filters:
            floors_str = ", ".join(hard_filters.get("excluded_floors", []))
            applied_optional_filters.append(("excluded_floors", floors_str, FILTER_NAME_MAPPING["excluded_floors"]))
        
        # 5. 옵션 필터
        if hard_filters.get("options") and "options" not in removed_filters:
            options = hard_filters.get("options", [])
            if options:
                options_str = ", ".join(options[:3]) if len(options) > 3 else ", ".join(options)
                applied_optional_filters.append(("options", options_str, FILTER_NAME_MAPPING["options"]))
        
        # 6. 가격 필터 (마지막에 제거 제안)
        if hard_filters.get("max_rent") and "max_rent" not in removed_filters:
            applied_optional_filters.append(("max_rent", f"{hard_filters.get('max_rent')}만원", FILTER_NAME_MAPPING["max_rent"]))
        if hard_filters.get("max_deposit") and "max_deposit" not in removed_filters:
            applied_optional_filters.append(("max_deposit", f"{hard_filters.get('max_deposit')}만원", FILTER_NAME_MAPPING["max_deposit"]))
        
        # 결과가 적고 제거 가능한 필터가 있으면 제안
        # ★★★ 핵심 수정: ES 결과가 없어서 기존 결과(existing_results)를 사용하는 경우도 고려해야 함 ★★★
        effective_results = results if results else existing_results
        
        if len(effective_results) <= LOW_RESULT_THRESHOLD and applied_optional_filters:
            state["suggest_filter_removal"] = True
            state["low_result_filters"] = applied_optional_filters
            
            # ★★★ 제안 메시지 생성 (Requirements 7.2) ★★★
            first_filter = applied_optional_filters[0]
            filter_key, filter_value, filter_display_name = first_filter
            
            # 결과 수에 따른 메시지 차별화
            if len(results) == 0:
                suggestion_message = f"검색 결과가 0개입니다. 😢\n'{filter_value}' ({filter_display_name}) 조건을 제외하고 다시 검색해볼까요?"
            else:
                suggestion_message = f"검색 결과가 {len(results)}개로 적습니다. 😢\n'{filter_value}' ({filter_display_name}) 조건을 제외하고 다시 검색해볼까요?"
            
            state["filter_removal_message"] = suggestion_message
            
            # ★★★ 핵심 수정: collected_conditions에 pending_filter_removal 설정 ★★★
            # 이렇게 해야 query_analyzer에서 사용자의 "응", "웅" 응답을 처리할 수 있음
            collected = state.get("collected_conditions", {}) or {}
            collected["pending_filter_removal"] = filter_key
            collected["pending_filter_value"] = filter_value
            collected["pending_filter_display_name"] = filter_display_name
            
            # ★★★ 현재 필터 상태 저장 (복원용) ★★★
            collected["saved_hard_filters"] = hard_filters.copy()
            collected["saved_soft_filters"] = state.get("soft_filters", []).copy()
            collected["saved_unmapped_styles"] = state.get("unmapped_styles", []).copy()
            
            state["collected_conditions"] = collected
            print(f"[ES Keyword] 🔧 pending_filter_removal 설정: {filter_key} ('{filter_value}')")
            print(f"[ES Keyword] 💡 저결과 감지! 제거 가능 필터: {[(f[0], f[1]) for f in applied_optional_filters]}")
        else:
            state["suggest_filter_removal"] = False
            state["low_result_filters"] = []
            state["filter_removal_message"] = ""
        
        # 결과가 있으면 업데이트, 없으면 기존 결과 유지!
        if results:
            state["graph_results"] = results
        elif existing_results:
            print(f"[ES Keyword] ⚠️ ES 결과 0개 - 기존 Neo4j 결과 {len(existing_results)}개 유지")
            # 기존 결과 유지 (state["graph_results"] 변경하지 않음)
        else:
            state["graph_results"] = []
        
    except Exception as e:
        print(f"[ES Keyword] ❌ 검색 실패: {e}")
        # 실패 시 기존 결과 유지
    
    return state


def interrupt_response_node(state: RAGState) -> RAGState:
    """
    멀티턴 인터럽트 응답 노드
    
    조건이 미완성일 때 호출되어, pending_question을 answer로 설정하고 종료.
    프론트엔드에서 이를 받아 사용자에게 추가 질문을 표시.
    
    ★ 위치가 있으면 미리 Neo4j 검색을 실행하여 실시간 매물 표시 지원!
    """
    # ★★★ 에러 타입이 있으면 이미 answer가 설정되어 있으므로 그대로 반환 ★★★
    error_type = state.get("error_type")
    if error_type:
        print(f"\n{'='*60}")
        print(f"[Interrupt] 🚫 에러 응답: {error_type}")
        print(f"[Interrupt] 💬 메시지: {state.get('answer', '')[:100]}...")
        print(f"{'='*60}\n")
        return state
    
    pending_question = state.get("pending_question", "")
    missing = state.get("missing_conditions", [])
    collected = state.get("collected_conditions", {})
    hard_filters = state.get("hard_filters", {})
    
    print(f"\n{'='*60}")
    print(f"[Interrupt] ❓ 조건 수집 인터럽트")
    print(f"[Interrupt] 📦 수집된 조건: {collected}")
    print(f"[Interrupt] ❌ 누락 조건: {missing}")
    print(f"{'='*60}\n")
    
    # 후속 질문을 answer로 설정
    state["answer"] = pending_question
    
    # ★★★ 위치가 있으면 미리 Neo4j + ES 검색 실행! (실시간 LandList 표시용) ★★★
    location = collected.get("location") or hard_filters.get("location")
    if location:
        print(f"[Interrupt] 🔍 위치 발견! 미리 실시간 검색 실행: {location}")
        try:
            # 1. Neo4j 검색 (함수명은 search)
            from nodes.neo4j_search_node import search as neo4j_search
            from nodes import es_search_node
            
            # 임시 State 생성
            temp_state = state.copy()
            temp_state["hard_filters"] = temp_state.get("hard_filters", {}) or {}
            temp_state["hard_filters"]["location"] = location
            
            # Neo4j 실행 (후보군 탐색)
            result_state = neo4j_search(temp_state)
            preliminary_results = result_state.get("graph_results", [])
            
            if preliminary_results:
                candidate_ids = [str(r.get('id', '')) for r in preliminary_results if r.get('id')]
                print(f"[Interrupt] ✅ 위치 기반 후보군: {len(candidate_ids)}개")
                
                # 2. ES 필터링 (건물유형, 거래유형, 가격 등)
                filters = {}
                
                # collected 조건과 hard_filters 병합 (user input 우선)
                # 건물유형
                b_type = collected.get("building_type") or hard_filters.get("building_type")
                if b_type: filters["building_type"] = b_type
                
                # 거래유형
                d_type = collected.get("deal_type") or hard_filters.get("deal_type")
                if d_type: filters["deal_type"] = d_type
                
                # 가격 조건
                price_cond = state.get("price_conditions", {})
                
                # 월세 상한 (collected에 있으면 사용, 없으면 price_conditions나 hard_filters 확인)
                max_rent = collected.get("max_rent") or hard_filters.get("max_rent")
                if not max_rent and price_cond: max_rent = price_cond.get("rent_max")
                
                # 보증금 (collected에 있으면 사용)
                max_deposit = collected.get("max_deposit") or hard_filters.get("max_deposit")
                if not max_deposit and price_cond: max_deposit = price_cond.get("deposit_max")
                
                # ES 검색 실행
                es_result = es_search_node.search_with_es(
                    candidate_ids=candidate_ids,
                    keyword=pending_question, # 질문 텍스트로 키워드 검색
                    building_type=filters.get("building_type"),
                    deal_type=filters.get("deal_type"),
                    max_rent=max_rent,
                    max_deposit=max_deposit
                )
                
                if es_result['ids']:
                    # ES 결과로 순서 재정렬 및 필터링
                    # Neo4j 점수와 ES 점수 조합은 복잡하므로, 여기선 ES 필터링 통과한 것만 Neo4j 정보 유지하여 반환
                    valid_ids = set(es_result['ids'])
                    filtered_results = [r for r in preliminary_results if str(r.get('id', '')) in valid_ids]
                    
                    print(f"[Interrupt] ✅ 최종 필터링 결과: {len(filtered_results)}개 (조건: {filters})")
                    state["graph_results"] = filtered_results
                else:
                    print(f"[Interrupt] ⚠️ 필터링 결과 0개 (위치는 맞으나 조건 불일치)")
                    # 결과가 없으면 Neo4j 결과라도 보여줄지, 아니면 빈 결과 보여줄지?
                    # 사용자는 "필터링된" 결과를 원하므로 빈 결과가 맞음
                    state["graph_results"] = []
            else:
                state["graph_results"] = []
        except Exception as e:
            print(f"[Interrupt] ❌ 예비 검색 실패: {e}")
            import traceback
            traceback.print_exc()
            state["graph_results"] = []
    else:
        # 위치 없으면 빈 결과
        state["graph_results"] = []
    
    state["sql_results"] = []
    
    return state


