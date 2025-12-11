from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from graphs.listing_rag_graph import create_rag_graph
from common.redis_cache import get_search_context, save_search_context, get_accumulated_results
from pydantic import BaseModel
from typing import Optional
import uuid

app = FastAPI(title="RAG System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = create_rag_graph()

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

@app.post("/query")
async def query(request: QueryRequest):
    # session_id 생성 또는 사용
    session_id = request.session_id or str(uuid.uuid4())
    
    # 1. 캐시된 검색 컨텍스트 로드
    search_context = get_search_context(session_id)
    cached_ids = search_context.get("property_ids", [])
    accumulated_results = search_context.get("accumulated_results", {})  # 누적된 모든 결과
    facility_types = search_context.get("facility_types", [])
    
    print(f"\n{'='*60}")
    print(f"[Main] 📝 Question: {request.question}")
    print(f"[Main] 🔑 Session: {session_id[:8]}...")
    print(f"[Main] 💾 Cached IDs: {len(cached_ids)}")
    print(f"[Main] 🏷️  Accumulated facilities: {facility_types}")
    print(f"{'='*60}\n")
    
    # 2. RAG 그래프 호출 - 누적된 결과 전달
    result = await graph.ainvoke({
        "question": request.question,
        "session_id": session_id,
        "cached_property_ids": cached_ids,
        "accumulated_results": accumulated_results  # 누적된 모든 Q1+Q2+... 데이터
    })
    
    # 3. 결과 저장 (새 검색이든 캐시 사용이든 항상 누적)
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
            print(f"[Main] DEBUG: Saving fields: {sample_fields[:10]}...")
        
        # 후속 질문이면 cache_filter에서 AND 필터링된 ID 사용
        filtered_ids = result.get("cached_property_ids", [])
        if filtered_ids:
            ids_to_save = filtered_ids[:20]  # cache_filter에서 AND 필터링된 결과
        elif cached_ids:
            ids_to_save = new_ids[:20] if new_ids else cached_ids[:20]
        else:
            ids_to_save = new_ids[:20]  # 첫 검색
        
        save_search_context(session_id, ids_to_save, facility_type, graph_results[:20])
        print(f"[Main] ✓ Saved {facility_type} to cumulative cache")
    
    return {
        "answer": result.get("answer"),
        "session_id": session_id
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
