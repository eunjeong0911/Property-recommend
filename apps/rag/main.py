from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from graphs.listing_rag_graph import create_rag_graph
from common.redis_cache import (
    get_search_context, save_search_context, get_accumulated_results, 
    get_redis_client, save_conversation_turn,
    get_collected_conditions, save_collected_conditions, clear_collected_conditions
)
from pydantic import BaseModel
from typing import Optional
import uuid
import os
import logging
import sys
from pythonjsonlogger import jsonlogger

# =============================================================================
# JSON Logging Configuration (Requirements 5.2, 5.3)
# =============================================================================
def setup_json_logging():
    """Configure JSON-formatted logging for CloudWatch Logs compatibility."""
    log_format = os.getenv("LOG_FORMAT", "json")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create stdout handler
    handler = logging.StreamHandler(sys.stdout)
    
    if log_format == "json":
        # JSON formatter for production (CloudWatch)
        formatter = jsonlogger.JsonFormatter(
            fmt="%(timestamp)s %(level)s %(name)s %(message)s",
            rename_fields={"levelname": "level", "asctime": "timestamp"},
            timestamp=True
        )
    else:
        # Standard formatter for development
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Configure uvicorn loggers to use the same format
    for uvicorn_logger in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        uv_logger = logging.getLogger(uvicorn_logger)
        uv_logger.handlers = []
        uv_logger.addHandler(handler)
    
    return logger

# Initialize JSON logging
logger = setup_json_logging()

app = FastAPI(title="RAG System")

# =============================================================================
# CORS Configuration (Requirements 6.1)
# =============================================================================
# In production, CORS_ALLOWED_ORIGINS must be set via environment variable
# Format: comma-separated list of origins (e.g., "https://example.com,https://api.example.com")
# Default "*" is removed for security - must explicitly configure allowed origins
_cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
if _cors_origins_env:
    cors_origins = [origin.strip() for origin in _cors_origins_env.split(",") if origin.strip()]
else:
    # Development defaults only - NOT for production
    cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# =============================================================================
# Health Check Endpoints for AWS ECS/ALB
# =============================================================================

@app.get("/health")
async def health():
    """
    Liveness probe endpoint.
    Returns 200 OK with {"status": "ok"} if the service is running.
    """
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    """
    Readiness probe endpoint.
    Verifies Redis and Neo4j connectivity before returning 200 OK.
    Returns 503 Service Unavailable if any service is not connected.
    """
    status = {"status": "ok"}
    all_connected = True
    
    # Check Redis connectivity
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        status["redis"] = "connected"
    except Exception:
        status["redis"] = "disconnected"
        all_connected = False
    
    # Check Neo4j connectivity
    try:
        from langchain_community.graphs import Neo4jGraph
        graph = Neo4jGraph(
            url=os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
            username=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password")
        )
        # Simple query to verify connection
        graph.query("RETURN 1")
        status["neo4j"] = "connected"
    except Exception:
        status["neo4j"] = "disconnected"
        all_connected = False
    
    if all_connected:
        return status
    else:
        status["status"] = "error"
        return JSONResponse(status_code=503, content=status)

graph = create_rag_graph()

from fastapi import FastAPI, BackgroundTasks
import requests

# ... (imports)

def send_search_log(session_id: str, query: str, filters: dict, search_strategy: str, result_count: int):
    """Django 백엔드로 검색 로그 전송"""
    try:
        url = "http://localhost:8000/api/search/log/"
        payload = {
            "session_id": session_id,
            "query": query,
            "filters": filters,
            "search_strategy": search_strategy,
            "result_count": result_count
        }
        # 타임아웃 3초 설정 (로그 전송 실패가 메인 로직에 영향 주지 않도록)
        requests.post(url, json=payload, timeout=3)
    except Exception as e:
        logger.error(f"Failed to send search log: {str(e)}")

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

@app.post("/query")
async def query(request: QueryRequest, background_tasks: BackgroundTasks):
    # session_id 생성 또는 사용
    session_id = request.session_id or str(uuid.uuid4())
    
    # 1. 캐시된 검색 컨텍스트 로드
    search_context = get_search_context(session_id)
    cached_ids = search_context.get("property_ids", [])
    accumulated_results = search_context.get("accumulated_results", {})  # 누적된 모든 결과
    facility_types = search_context.get("facility_types", [])
    
    # 2. 멀티턴: 이전에 수집된 조건 로드
    collected_conditions = get_collected_conditions(session_id)
    
    logger.info("RAG query received", extra={
        "question": request.question,
        "session_id": session_id[:8] + "...",
        "cached_ids_count": len(cached_ids),
        "accumulated_facilities": facility_types,
        "collected_conditions": list(collected_conditions.keys())
    })
    
    # 3. RAG 그래프 호출 - 누적된 결과 + 수집된 조건 전달
    result = await graph.ainvoke({
        "question": request.question,
        "session_id": session_id,
        "cached_property_ids": cached_ids,
        "accumulated_results": accumulated_results,  # 누적된 모든 Q1+Q2+... 데이터
        "collected_conditions": collected_conditions  # 멀티턴에서 수집된 조건
    })
    
    # 4. 멀티턴: 인터럽트 응답 처리
    conversation_complete = result.get("conversation_complete", True)
    pending_question = result.get("pending_question")
    
    if not conversation_complete and pending_question:
        # 조건 수집 중 - 수집된 조건 저장하고 인터럽트 응답 반환
        new_collected = result.get("collected_conditions", {})
        save_collected_conditions(session_id, new_collected)
        
        logger.info("Multi-turn interrupt", extra={
            "missing_conditions": result.get("missing_conditions", []),
            "collected_so_far": list(new_collected.keys())
        })
        
        # 현재까지 수집된 조건을 한국어로 표시
        filter_info = _format_filter_info(new_collected)
        
        # ★ 중간 검색 결과도 함께 반환 (실시간 LandList 업데이트용)
        intermediate_results = result.get("graph_results", [])
        
        return {
            "answer": pending_question,
            "session_id": session_id,
            "awaiting_input": True,
            "collected_conditions": new_collected,
            "filter_info": filter_info,
            "properties": intermediate_results[:20]  # 실시간 매물 표시용
        }
    
    # 5. 조건 완성 → 검색 실행됨
    # ★★★ 핵심 수정: 필터 제거 제안 상태에서는 collected_conditions 유지 ★★★
    suggest_filter_removal = result.get("suggest_filter_removal", False)
    final_collected = result.get("collected_conditions", {})
    
    # ★★★ removed_filters 저장 (무한 루프 방지) ★★★
    removed_filters = result.get("removed_filters", [])
    if removed_filters:
        final_collected["removed_filters"] = removed_filters
    
    if suggest_filter_removal and final_collected.get("pending_filter_removal"):
        # 필터 제거 제안 중 → collected_conditions 저장 (초기화하지 않음!)
        save_collected_conditions(session_id, final_collected)
        logger.info("Filter removal suggestion active - keeping collected_conditions", extra={
            "pending_filter": final_collected.get("pending_filter_removal")
        })
    else:
        # 일반 검색 완료 → 수집된 조건 초기화
        clear_collected_conditions(session_id)
    
    # 필터링 정보 생성 (검색에 사용된 조건들)
    hard_filters = result.get("hard_filters", {})
    soft_filters = result.get("soft_filters", [])
    search_strategy = result.get("search_strategy", "")
    
    filter_info = _format_filter_info(final_collected, hard_filters, soft_filters, search_strategy)
    
    # 6. 결과 저장 (새 검색이든 캐시 사용이든 항상 누적)
    graph_results = result.get("graph_results", [])
    if graph_results:
        # ID 추출
        new_ids = []
        for r in graph_results:
            if isinstance(r, dict):
                prop_id = r.get("id") or r.get("p.id")
                if prop_id:
                    new_ids.append(str(prop_id))
        
        # 시설 타입 감지
        facility_type = detect_facility_type(request.question)
        
        # [DEBUG] 저장 전 필드 확인
        if graph_results:
            sample = graph_results[0] if isinstance(graph_results[0], dict) else {}
            sample_fields = [k for k in sample.keys() if sample.get(k)]
            logger.debug("Saving fields", extra={"fields": sample_fields[:10]})
        
        # 후속 질문이면 cache_filter에서 AND 필터링된 ID 사용
        filtered_ids = result.get("cached_property_ids", [])
        if filtered_ids:
            ids_to_save = filtered_ids[:20]  # cache_filter에서 AND 필터링된 결과
        elif cached_ids:
            ids_to_save = new_ids[:20] if new_ids else cached_ids[:20]
        else:
            ids_to_save = new_ids[:20]  # 첫 검색
        
        save_search_context(session_id, ids_to_save, facility_type, graph_results[:20])
        logger.info("Saved to cumulative cache", extra={"facility_type": facility_type})
    
    # 7. 대화 턴 저장 (최근 5개 유지)
    answer = result.get("answer", "")
    save_conversation_turn(session_id, request.question, answer)
    
    # [LOGGING] 검색 로그 전송 (백그라운드)
    background_tasks.add_task(
        send_search_log,
        session_id=session_id,
        query=request.question,
        filters=filter_info.get("details", {}),
        search_strategy=search_strategy,
        result_count=len(graph_results)
    )

    # =====================================================================
    # Low Result Fallback: 필터 제거 제안
    # =====================================================================
    suggest_filter_removal = result.get("suggest_filter_removal", False)
    low_result_filters = result.get("low_result_filters", [])
    
    if suggest_filter_removal and low_result_filters:
        # 필터 이름 한국어로 변환
        filter_names_kr = {
            "direction": "방향",
            "excluded_floors": "층수 제외",
            "max_rent": "월세 상한",
            "max_deposit": "보증금 상한",
            "style": "스타일",
            "options": "옵션"
        }
        
        # 첫 번째 제거 가능한 필터로 제안
        first_filter = low_result_filters[0]
        filter_key, filter_value, filter_kr = first_filter
        
        suggestion_msg = f"검색 결과가 {len(graph_results)}개로 적습니다. 😢\n\n" \
                         f"'{filter_value}' ({filter_kr}) 조건을 제외하고 다시 검색해볼까요?\n\n" \
                         f"👉 \"응\", \"네\", \"제외해줘\" 라고 답해주세요!"
        
        # ★★★ 중요: 현재 필터 상태 스냅샷 저장 (재검색 시 복원용) ★★★
        collected_conditions = result.get("collected_conditions", {})
        collected_conditions["pending_filter_removal"] = filter_key
        collected_conditions["saved_hard_filters"] = hard_filters  # 모든 필터 저장!
        collected_conditions["saved_soft_filters"] = soft_filters
        save_collected_conditions(session_id, collected_conditions)
        
        return {
            "answer": suggestion_msg,
            "session_id": session_id,
            "awaiting_input": True,
            "filter_info": filter_info,
            "result_count": len(graph_results),
            "properties": graph_results[:20]  # 현재 결과도 함께 반환
        }

    return {
        "answer": answer,
        "session_id": session_id,
        "awaiting_input": False,
        "filter_info": filter_info,
        "result_count": len(graph_results),
        "properties": graph_results[:20]
    }


def _format_price_kr(val):
    """만원 단위 숫자를 한국어 금액 표현으로 변환 (예: 10000 -> 1억)"""
    if val is None: return ""
    try:
        # 숫자가 아닌 경우 (이미 '1억' 등으로 들어온 경우) 처리
        if isinstance(val, str) and not val.isdigit():
            return val
            
        val_int = int(val)
        if val_int >= 10000:
            eok = val_int // 10000
            man = val_int % 10000
            if man > 0:
                return f"{eok}억 {man}만원"
            return f"{eok}억"
        return f"{val_int}만원"
    except Exception:
        return str(val)


def _format_filter_info(collected: dict = None, hard_filters: dict = None, 
                        soft_filters: list = None, search_strategy: str = None) -> dict:
    """
    필터링 과정을 한국어로 포맷팅하여 사용자에게 표시
    
    Returns:
        {
            "summary": "홍대역 | 월세 | 풀옵션",  # 한 줄 요약
            "details": {
                "location": "홍대역",
                "deal_type": "월세",
                "style": ["풀옵션", "채광좋음"],
                ...
            },
            "search_strategy": "neo4j_keyword"
        }
    """
    collected = collected or {}
    hard_filters = hard_filters or {}
    
    details = {}
    summary_parts = []
    
    # 위치 조건
    location = collected.get("location") or hard_filters.get("location")
    if location:
        details["location"] = location
        summary_parts.append(f"📍 {location}")
    
    # 시설 조건
    facilities = collected.get("facilities") or hard_filters.get("facilities", [])
    if facilities:
        facility_names = {
            "subway": "역세권",
            "convenience": "편세권",
            "safety": "치안좋음",
            "hospital": "병원가까움",
            "park": "공원가까움",
            "university": "대학가"
        }
        details["facilities"] = [facility_names.get(f, f) for f in facilities]
    
    # 거래 유형
    deal_type = collected.get("deal_type") or hard_filters.get("deal_type")
    if deal_type:
        details["deal_type"] = deal_type
        summary_parts.append(f"🏠 {deal_type}")
    
    # 건물 타입
    building_type = collected.get("building_type") or hard_filters.get("building_type")
    if building_type:
        details["building_type"] = building_type
        summary_parts.append(f"🏢 {building_type}")
    
    # 가격 조건
    price_info = collected.get("price_info", {})
    max_deposit = price_info.get("max_deposit") or hard_filters.get("max_deposit")
    max_rent = price_info.get("max_rent") or hard_filters.get("max_rent")
    if max_deposit:
        deposit_str = _format_price_kr(max_deposit)
        details["max_deposit"] = f"{deposit_str} 이하"
        summary_parts.append(f"💰 보증금 {deposit_str}↓")
    if max_rent:
        rent_str = _format_price_kr(max_rent)
        details["max_rent"] = f"{rent_str} 이하"
        summary_parts.append(f"💵 월세 {rent_str}↓")
    
    # 스타일/선호도
    styles = collected.get("style") or soft_filters or []
    if styles:
        details["style"] = styles if isinstance(styles, list) else [styles]
        style_str = ", ".join(details["style"][:3])  # 최대 3개만 표시
        if len(details["style"]) > 3:
            style_str += f" 외 {len(details['style'])-3}개"
        summary_parts.append(f"✨ {style_str}")
    
    # 제외 조건 (층, 방향 등)
    excluded_floors = collected.get("excluded_floors") or hard_filters.get("excluded_floors", [])
    if excluded_floors:
        details["excluded_floors"] = excluded_floors if isinstance(excluded_floors, list) else [excluded_floors]
        summary_parts.append(f"🚫 {', '.join(details['excluded_floors'])} 제외")
    
    # 선호 방향
    direction = collected.get("direction") or hard_filters.get("direction")
    if direction:
        details["direction"] = direction
        summary_parts.append(f"☀️ {direction}")
    
    # 옵션 (세탁기, 에어컨 등)
    options = collected.get("options") or hard_filters.get("options", [])
    if options:
        details["options"] = options if isinstance(options, list) else [options]
        # ★★★ 핵심 수정: 스타일(✨)과 중복되는 옵션은 요약에서 제외 (예: 풀옵션) ★★★
        unique_options = [opt for opt in details["options"] if opt not in (details.get("style", []))]
        if unique_options:
            summary_parts.append(f"🔧 {', '.join(unique_options[:2])}")

    
    # 검색 전략 (개발자용)
    strategy_names = {
        "neo4j_only": "위치 기반",
        "keyword_only": "조건 기반",
        "neo4j_keyword": "위치+조건",
        "keyword_vector": "조건+스타일",
        "full": "복합 검색"
    }
    
    return {
        "summary": " | ".join(summary_parts) if summary_parts else "조건 수집 중...",
        "details": details,
        "search_strategy": strategy_names.get(search_strategy, search_strategy) if search_strategy else None
    }


def detect_facility_type(question: str) -> str:
    """질문에서 시설 타입 감지"""
    q = question.lower()
    facility_map = {
        "convenience": ["편의점", "마트", "gs25", "cu"],
        "hospital": ["병원", "의료", "종합병원"],
        "pharmacy": ["약국"],
        "park": ["공원", "산책"],
        "university": ["대학", "학교"],
        "subway": ["역", "지하철", "교통"],
        "safety": ["안전", "치안", "cctv", "경찰"]
    }
    for facility, keywords in facility_map.items():
        if any(kw in q for kw in keywords):
            return facility
    return "general"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

