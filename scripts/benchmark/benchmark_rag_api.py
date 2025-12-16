#!/usr/bin/env python3
"""
전체 RAG API 벤치마크 스크립트

RAG 서비스 API 엔드포인트를 통해 전체 응답 시간을 측정합니다.
- neo4j_search_node (LLM Agent)
- sql_search_node (PostgreSQL)
- generate_node (답변 생성)
- 네트워크 전송

Usage:
    python scripts/benchmark_rag_api.py
    
전제 조건:
    - Docker 컨테이너 실행 중 (docker-compose up -d)
    - RAG 서비스가 http://localhost:8001에서 실행 중
"""

import requests
import time
import json
import sys
from dataclasses import dataclass
from typing import List, Dict, Any

# RAG 서비스 URL
RAG_API_URL = "http://localhost:8001"

# 테스트 질문들 (neo4j_search_node 벤치마크와 동일)
TEST_QUESTIONS = [
    "홍대입구역 근처 치안 좋은 매물 찾아줘",
    "강남역 주변 병원과 편의점 가까운 곳",
    "신촌역 근처 공원이 있는 안전한 곳",
]

@dataclass
class APIBenchmarkResult:
    question: str
    total_time_ms: float
    success: bool
    status_code: int
    response_length: int
    error: str = ""


def check_health() -> bool:
    """RAG 서비스 헬스체크 - /query 엔드포인트로 간단한 테스트"""
    try:
        # /health가 없으므로 빈 쿼리로 테스트
        response = requests.post(
            f"{RAG_API_URL}/query",
            json={"question": "test"},
            timeout=10
        )
        # 200 또는 다른 응답이라도 서버가 응답하면 OK
        return response.status_code in [200, 400, 422]
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {RAG_API_URL}")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def benchmark_api_call(question: str) -> APIBenchmarkResult:
    """
    단일 API 호출에 대해 벤치마크 실행
    """
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{RAG_API_URL}/query",
            json={"question": question},
            timeout=120  # 2분 타임아웃
        )
        
        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000
        
        return APIBenchmarkResult(
            question=question,
            total_time_ms=total_time_ms,
            success=response.status_code == 200,
            status_code=response.status_code,
            response_length=len(response.text),
            error="" if response.status_code == 200 else response.text[:100]
        )
        
    except requests.exceptions.Timeout:
        return APIBenchmarkResult(
            question=question,
            total_time_ms=120000,
            success=False,
            status_code=0,
            response_length=0,
            error="Timeout (120s)"
        )
    except Exception as e:
        return APIBenchmarkResult(
            question=question,
            total_time_ms=0,
            success=False,
            status_code=0,
            response_length=0,
            error=str(e)
        )


def run_benchmark(iterations: int = 1) -> List[APIBenchmarkResult]:
    """
    전체 벤치마크 실행
    """
    results = []
    
    print("\n" + "="*80)
    print("🚀 Full RAG API Benchmark")
    print("="*80)
    print(f"📍 API URL: {RAG_API_URL}")
    print(f"📊 Questions: {len(TEST_QUESTIONS)}")
    print(f"🔄 Iterations: {iterations}")
    print("="*80)
    
    for i in range(iterations):
        if iterations > 1:
            print(f"\n--- Iteration {i+1}/{iterations} ---")
        
        for question in TEST_QUESTIONS:
            print(f"\n❓ {question[:50]}...", end=" ", flush=True)
            
            result = benchmark_api_call(question)
            results.append(result)
            
            if result.success:
                print(f"✅ {result.total_time_ms:.0f}ms ({result.response_length} chars)")
            else:
                print(f"❌ Failed: {result.error[:50]}")
    
    return results


def print_summary(results: List[APIBenchmarkResult]):
    """
    벤치마크 결과 요약 출력
    """
    print("\n" + "="*80)
    print("📈 FULL RAG API BENCHMARK RESULTS")
    print("="*80)
    
    successful = [r for r in results if r.success]
    
    if not successful:
        print("❌ No successful API calls!")
        return
    
    times = [r.total_time_ms for r in successful]
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n📊 Summary (from {len(successful)} successful calls):")
    print("-"*50)
    print(f"{'Metric':<25} {'Value':<20}")
    print("-"*50)
    print(f"{'Average Response Time':<25} {avg_time:.0f}ms")
    print(f"{'Minimum Response Time':<25} {min_time:.0f}ms")
    print(f"{'Maximum Response Time':<25} {max_time:.0f}ms")
    print(f"{'Success Rate':<25} {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
    print("-"*50)
    
    # 질문별 결과
    print("\n📋 Results by Question:")
    print("-"*80)
    
    for question in TEST_QUESTIONS:
        q_results = [r for r in successful if r.question == question]
        if q_results:
            q_avg = sum(r.total_time_ms for r in q_results) / len(q_results)
            print(f"❓ {question[:45]}...")
            print(f"   ⏱️ {q_avg:.0f}ms (avg of {len(q_results)} calls)")
    
    # Neo4j 모델 벤치마크와 비교
    estimated_improved = avg_time - 13177  # gpt-5-mini → gpt-4o-mini 차이
    
    print("\n" + "="*80)
    print("🔍 COMPARISON WITH NEO4J MODEL BENCHMARK")
    print("="*80)
    print(f"""
현재 RAG 파이프라인 구성 (neo4j_search_node에서 gpt-5-mini 사용 중):

┌─────────────────────────────────────────────────────────────────┐
│  Stage                    │  Estimated Time                     │
├─────────────────────────────────────────────────────────────────┤
│  1. neo4j_search (gpt-5)  │  ~17,916ms (벤치마크 결과)          │
│  2. sql_search (Postgres) │  ~100-500ms                         │
│  3. generate (gpt-4o-mini)│  ~2,000-5,000ms                     │
│  4. Network overhead      │  ~50-200ms                          │
├─────────────────────────────────────────────────────────────────┤
│  Total Expected           │  ~20,000-23,000ms                   │
│  Actual Measured          │  {avg_time:.0f}ms                             │
└─────────────────────────────────────────────────────────────────┘

💡 gpt-4o-mini로 변경 시 예상 개선:
   neo4j_search: 17,916ms → 4,739ms (3.8배 빠름)
   Total: {avg_time:.0f}ms → ~{estimated_improved:.0f}ms (예상)
""")


def main():
    """
    메인 함수
    """
    print("\n🔍 Checking RAG service health...")
    
    if not check_health():
        print("\n❌ RAG 서비스에 연결할 수 없습니다.")
        print("다음 명령어로 서비스를 시작하세요:")
        print("  docker-compose up -d")
        sys.exit(1)
    
    print("✅ RAG service is healthy!")
    
    # 벤치마크 실행
    results = run_benchmark(iterations=1)
    
    # 결과 요약
    print_summary(results)
    
    # 결과 JSON 저장
    import os
    output_file = os.path.join(os.path.dirname(__file__), "benchmark_rag_api_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([{
            "question": r.question,
            "total_time_ms": r.total_time_ms,
            "success": r.success,
            "status_code": r.status_code,
            "response_length": r.response_length,
            "error": r.error
        } for r in results], f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
