"""Redis Cache for Cumulative Query Data Storage"""
import redis
import json
import os

def get_redis_client():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=0,
        decode_responses=True
    )

def save_search_context(session_id: str, property_ids: list, facility_type: str = None, graph_results: list = None, ttl: int = 7200):
    """
    검색 결과를 누적하여 저장 (Q1 + Q2 + Q3... 모든 데이터 누적)
    
    핵심 로직: 
    - 기존 accumulated_results에 새 데이터를 **병합** (덮어쓰기 X)
    - 모든 시설 필드가 누적됨
    """
    try:
        r = get_redis_client()
        key = f"search:{session_id}"
        
        # 1. 기존 데이터 로드
        existing_data = r.get(key)
        if existing_data:
            existing = json.loads(existing_data)
        else:
            existing = {"property_ids": [], "facility_types": [], "accumulated_results": {}}
        
        existing_accumulated = existing.get("accumulated_results", {})
        existing_facility_types = existing.get("facility_types", [])
        
        # 2. 새 결과를 기존에 병합 (기존 데이터 유지 + 새 필드 추가)
        for result in (graph_results or []):
            if not isinstance(result, dict):
                continue
            prop_id = str(result.get("id") or result.get("p.id") or "")
            if not prop_id:
                continue
            
            if prop_id in existing_accumulated:
                # 기존 데이터 유지, 새 값이 있으면 추가 (빈 값은 덮어쓰지 않음)
                merged = existing_accumulated[prop_id].copy()
                for key_name, value in result.items():
                    # 새 값이 유효하고, 기존에 없거나 빈 값일 때만 업데이트
                    if value and value != [] and value != 0 and value != "":
                        existing_val = merged.get(key_name)
                        if not existing_val or existing_val == [] or existing_val == 0:
                            merged[key_name] = value
                        # id, address는 항상 최신으로 유지
                        elif key_name in ["id", "address"]:
                            merged[key_name] = value
                existing_accumulated[prop_id] = merged
            else:
                existing_accumulated[prop_id] = result.copy()
        
        # 3. 시설 타입 누적
        if facility_type and facility_type not in existing_facility_types:
            existing_facility_types.append(facility_type)
        
        # 4. 저장
        data = {
            "property_ids": property_ids,
            "facility_types": existing_facility_types,
            "accumulated_results": existing_accumulated
        }
        r.setex(key, ttl, json.dumps(data))
        
        # 디버그 로그
        sample_id = next(iter(existing_accumulated.keys()), None)
        if sample_id:
            sample_fields = list(existing_accumulated[sample_id].keys())
            print(f"[RedisCache] ✓ Saved {len(property_ids)} IDs, facilities: {existing_facility_types}")
            print(f"[RedisCache] DEBUG: Sample fields: {sample_fields}")
    except Exception as e:
        print(f"[RedisCache] ✗ Save failed: {e}")

def get_search_context(session_id: str) -> dict:
    """저장된 검색 컨텍스트 조회"""
    try:
        r = get_redis_client()
        key = f"search:{session_id}"
        data = r.get(key)
        if data:
            context = json.loads(data)
            print(f"[RedisCache] ✓ Loaded {len(context.get('property_ids', []))} IDs, facilities: {context.get('facility_types', [])}")
            return context
        print(f"[RedisCache] No cached context for session")
        return {}
    except Exception as e:
        print(f"[RedisCache] ✗ Load failed: {e}")
        return {}

def get_accumulated_results(session_id: str) -> dict:
    """누적된 결과를 ID별 dict로 반환"""
    context = get_search_context(session_id)
    return context.get("accumulated_results", {})

def get_property_ids(session_id: str) -> list:
    context = get_search_context(session_id)
    return context.get("property_ids", [])

def clear_cache(session_id: str):
    """캐시 삭제"""
    try:
        r = get_redis_client()
        r.delete(f"search:{session_id}")
        print(f"[RedisCache] ✓ Cleared cache")
    except Exception as e:
        print(f"[RedisCache] ✗ Clear failed: {e}")
