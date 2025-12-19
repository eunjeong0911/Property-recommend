#!/usr/bin/env python3
"""
노드별 응답 시간 벤치마크 (API 기반)

Docker에서 실행 중인 RAG 서비스의 로그를 분석하여
각 노드별 소요 시간을 측정합니다.

Usage:
    python scripts/benchmark/benchmark_node_timing.py
"""

import os
import sys
import time
import json
import requests
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from dotenv import load_dotenv

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 환경 변수 로드
load_dotenv(PROJECT_ROOT / ".env")

# RAG 서비스 URL
RAG_API_URL = "http://localhost:8001"

# 타임아웃
API_TIMEOUT = 180


@dataclass
class QuestionResult:
    """질문별 결과"""
    question: str
    question_type: str  # "simple" or "complex"
    total_time_ms: float
    success: bool
    response_length: int
    error: str = ""


# 테스트 질문들
SIMPLE_QUESTIONS = [
    "홍대입구역 근처 매물 찾아줘",
    "강남역 주변 안전한 곳",
    "신촌역 근처 편의점 가까운 매물",
]

COMPLEX_QUESTIONS = [
    "홍대입구역 근처에서 가장 좋은 매물 추천해줘",
    "강남역 주변에서 병원도 가깝고 그리고 공원도 있는 곳 찾아줘",
    "신촌역 근처 안전한 매물 있어?",
]


def check_service() -> bool:
    """RAG 서비스 헬스체크"""
    try:
        response = requests.post(
            f"{RAG_API_URL}/query",
            json={"question": "test"},
            timeout=10
        )
        return response.status_code in [200, 400, 422]
    except:
        return False


def query_with_timing(question: str, question_type: str) -> QuestionResult:
    """타이밍 측정하며 쿼리 실행"""
    try:
        start = time.time()
        
        response = requests.post(
            f"{RAG_API_URL}/query",
            json={"question": question},
            timeout=API_TIMEOUT
        )
        
        elapsed = (time.time() - start) * 1000
        
        if response.status_code == 200:
            return QuestionResult(
                question=question,
                question_type=question_type,
                total_time_ms=elapsed,
                success=True,
                response_length=len(response.text)
            )
        else:
            return QuestionResult(
                question=question,
                question_type=question_type,
                total_time_ms=elapsed,
                success=False,
                response_length=0,
                error=response.text[:100]
            )
            
    except requests.exceptions.Timeout:
        return QuestionResult(
            question=question,
            question_type=question_type,
            total_time_ms=API_TIMEOUT * 1000,
            success=False,
            response_length=0,
            error=f"Timeout ({API_TIMEOUT}s)"
        )
    except Exception as e:
        return QuestionResult(
            question=question,
            question_type=question_type,
            total_time_ms=0,
            success=False,
            response_length=0,
            error=str(e)
        )


def get_docker_logs() -> str:
    """Docker RAG 컨테이너 로그 가져오기"""
    try:
        result = subprocess.run(
            ["docker-compose", "logs", "--tail=200", "rag"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout
    except:
        return ""


def run_benchmark() -> List[QuestionResult]:
    """벤치마크 실행"""
    results = []
    
    print("\n" + "="*80)
    print("🧪 Node-Level Timing Benchmark (via Docker logs)")
    print("="*80)
    
    # 간단한 질문
    print("\n📗 SIMPLE QUESTIONS (Rule-Based Router)")
    print("-"*60)
    
    for q in SIMPLE_QUESTIONS:
        print(f"\n  ❓ {q[:45]}...")
        print(f"     Testing...", end=" ", flush=True)
        
        result = query_with_timing(q, "simple")
        results.append(result)
        
        if result.success:
            print(f"✅ {result.total_time_ms:.0f}ms")
        else:
            print(f"❌ {result.error[:30]}")
    
    # 복잡한 질문
    print("\n📕 COMPLEX QUESTIONS (LLM Agent)")
    print("-"*60)
    
    for q in COMPLEX_QUESTIONS:
        print(f"\n  ❓ {q[:45]}...")
        print(f"     Testing...", end=" ", flush=True)
        
        result = query_with_timing(q, "complex")
        results.append(result)
        
        if result.success:
            print(f"✅ {result.total_time_ms:.0f}ms")
        else:
            print(f"❌ {result.error[:30]}")
    
    return results


def print_summary(results: List[QuestionResult]):
    """결과 요약 출력"""
    print("\n" + "="*80)
    print("📊 BENCHMARK SUMMARY")
    print("="*80)
    
    simple_results = [r for r in results if r.question_type == "simple" and r.success]
    complex_results = [r for r in results if r.question_type == "complex" and r.success]
    
    print("\n📗 Simple Questions (Rule-Based Router)")
    print("-"*60)
    if simple_results:
        times = [r.total_time_ms for r in simple_results]
        print(f"Average: {sum(times)/len(times):.0f}ms")
        print(f"Min: {min(times):.0f}ms")
        print(f"Max: {max(times):.0f}ms")
        print(f"Success: {len(simple_results)}/{len([r for r in results if r.question_type == 'simple'])}")
    else:
        print("No successful results")
    
    print("\n📕 Complex Questions (LLM Agent)")
    print("-"*60)
    if complex_results:
        times = [r.total_time_ms for r in complex_results]
        print(f"Average: {sum(times)/len(times):.0f}ms")
        print(f"Min: {min(times):.0f}ms")
        print(f"Max: {max(times):.0f}ms")
        print(f"Success: {len(complex_results)}/{len([r for r in results if r.question_type == 'complex'])}")
    else:
        print("No successful results")
    
    # 비교
    if simple_results and complex_results:
        simple_avg = sum(r.total_time_ms for r in simple_results) / len(simple_results)
        complex_avg = sum(r.total_time_ms for r in complex_results) / len(complex_results)
        
        print("\n📈 Comparison")
        print("-"*60)
        print(f"Simple Avg: {simple_avg:.0f}ms")
        print(f"Complex Avg: {complex_avg:.0f}ms")
        print(f"Difference: Complex is {complex_avg/simple_avg:.1f}x slower")
        print(f"LLM Agent overhead: ~{complex_avg - simple_avg:.0f}ms")
    
    # Docker 로그에서 노드별 타이밍 확인 안내
    print("\n💡 TIP: 노드별 세부 타이밍은 Docker 로그에서 확인하세요:")
    print("   docker-compose logs --tail=100 rag | grep -E '(neo4j|sql|generate)'")


def main():
    print("\n🚀 Starting Node-Level Timing Benchmark...")
    
    if not check_service():
        print("\n❌ RAG 서비스에 연결할 수 없습니다.")
        print("docker-compose up -d 명령으로 서비스를 시작하세요.")
        sys.exit(1)
    
    print("✅ RAG service is running!")
    
    results = run_benchmark()
    
    print_summary(results)
    
    # 결과 저장
    output_file = PROJECT_ROOT / "scripts" / "benchmark" / "node_timing_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
