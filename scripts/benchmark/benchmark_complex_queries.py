#!/usr/bin/env python3
"""
복잡한 질문 전용 벤치마크

LLM Agent(search_with_agent)를 사용하는 복잡한 질문에 대해
gpt-4o-mini vs gpt-5-mini 성능 비교

복잡한 질문 조건:
- 비교 표현 (가장, 더, 제일)
- 조건부 표현 (만약, 경우)
- 복합 조건 (그리고, 또는)
- 100자 초과 질문
- 대화형 질문 (뭐야?, 어때?)

Usage:
    python scripts/benchmark/benchmark_complex_queries.py
"""

import os
import sys
import subprocess
import time
import json
import requests
from dataclasses import dataclass, asdict
from typing import List
from pathlib import Path

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent
NEO4J_SEARCH_NODE = PROJECT_ROOT / "apps" / "rag" / "nodes" / "neo4j_search_node.py"

# RAG 서비스 URL
RAG_API_URL = "http://localhost:8001"

# 테스트할 모델
MODELS_TO_TEST = ["gpt-4o-mini", "gpt-5-mini"]

# 복잡한 질문들 (LLM Agent 경로를 타도록 설계)
COMPLEX_QUESTIONS = [
    # 비교 표현 - "가장", "더", "제일"
    "홍대입구역 근처에서 가장 좋은 매물 추천해줘",
    
    # 복합 조건 - "그리고", "또는"
    "강남역 주변에서 병원도 가깝고 그리고 공원도 있는 곳 찾아줘",
    
    # 대화형/질문형 - "어때?", "있어?"
    "신촌역 근처 안전한 매물 있어?",
]

# 타임아웃
API_TIMEOUT = 180

@dataclass
class ComplexBenchmarkResult:
    model: str
    question: str
    response_time_ms: float
    success: bool
    is_complex_route: bool  # Agent 경로 사용 여부
    answer_length: int
    error: str = ""


def update_model_in_code(model_name: str) -> bool:
    """neo4j_search_node.py에서 모델명 변경"""
    try:
        content = NEO4J_SEARCH_NODE.read_text(encoding='utf-8')
        
        import re
        pattern = r'(llm = ChatOpenAI\(model=")[^"]+(")'
        replacement = f'\\1{model_name}\\2'
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content == content:
            print(f"  ⚠️ 모델 패턴 없음")
            return False
        
        NEO4J_SEARCH_NODE.write_text(new_content, encoding='utf-8')
        print(f"  ✅ 모델 변경: {model_name}")
        return True
        
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        return False


def rebuild_rag_container() -> bool:
    """RAG Docker 컨테이너 재빌드"""
    try:
        print("  🔨 Docker 재빌드...")
        
        subprocess.run(
            ["docker-compose", "stop", "rag"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=30
        )
        
        result = subprocess.run(
            ["docker-compose", "build", "rag"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=300
        )
        
        if result.returncode != 0:
            return False
        
        subprocess.run(
            ["docker-compose", "up", "-d", "rag"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=60
        )
        
        print("  ⏳ 서비스 대기...")
        for i in range(30):
            time.sleep(1)
            try:
                response = requests.post(
                    f"{RAG_API_URL}/query",
                    json={"question": "test"},
                    timeout=5
                )
                if response.status_code in [200, 400, 422]:
                    print("  ✅ 준비 완료!")
                    return True
            except:
                pass
        
        return False
        
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        return False


def test_question(question: str) -> tuple:
    """단일 질문 테스트"""
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{RAG_API_URL}/query",
            json={"question": question},
            timeout=API_TIMEOUT
        )
        
        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('response', str(data))
            return (total_time_ms, True, len(answer), "")
        else:
            return (total_time_ms, False, 0, response.text[:100])
            
    except requests.exceptions.Timeout:
        return (API_TIMEOUT * 1000, False, 0, f"Timeout ({API_TIMEOUT}s)")
    except Exception as e:
        return (0, False, 0, str(e))


def check_is_complex_route(question: str) -> bool:
    """질문이 복잡한 경로(Agent)를 타는지 확인"""
    import re
    
    # 복잡한 패턴들
    complex_patterns = [
        r'(보다|더|가장|최고|덜|제일)',  # 비교
        r'(만약|경우|때문에|그래서)',      # 조건부
        r'(그리고|또는|이면서|동시에)',    # 복합
        r'(뭐야\?|어때\?|있어\?|될까\?)',  # 대화형
    ]
    
    for pattern in complex_patterns:
        if re.search(pattern, question):
            return True
    
    return len(question) > 100


def run_complex_benchmark() -> List[ComplexBenchmarkResult]:
    """복잡한 질문 벤치마크 실행"""
    results = []
    
    print("\n" + "="*80)
    print("🧠 Complex Query Benchmark (LLM Agent Path)")
    print("="*80)
    print(f"❓ Questions: {len(COMPLEX_QUESTIONS)}")
    print(f"📦 Models: {MODELS_TO_TEST}")
    print("="*80)
    
    for model in MODELS_TO_TEST:
        print(f"\n{'='*60}")
        print(f"📦 Testing: {model}")
        print("="*60)
        
        if not update_model_in_code(model):
            continue
        
        if not rebuild_rag_container():
            continue
        
        for question in COMPLEX_QUESTIONS:
            is_complex = check_is_complex_route(question)
            print(f"\n  ❓ {question[:40]}...")
            print(f"     📌 Complex route: {'✓' if is_complex else '✗'}")
            print(f"     🧪 Testing...", end=" ", flush=True)
            
            time_ms, success, answer_len, error = test_question(question)
            
            result = ComplexBenchmarkResult(
                model=model,
                question=question,
                response_time_ms=time_ms,
                success=success,
                is_complex_route=is_complex,
                answer_length=answer_len,
                error=error
            )
            results.append(result)
            
            if success:
                print(f"✅ {time_ms:.0f}ms")
            else:
                print(f"❌ {error[:30]}")
    
    return results


def print_comparison(results: List[ComplexBenchmarkResult]):
    """결과 비교 출력"""
    print("\n" + "="*80)
    print("📊 COMPLEX QUERY BENCHMARK RESULTS")
    print("="*80)
    
    # 모델별 통계
    model_stats = {}
    for r in results:
        if r.model not in model_stats:
            model_stats[r.model] = {"times": [], "success": 0, "total": 0}
        model_stats[r.model]["total"] += 1
        if r.success:
            model_stats[r.model]["times"].append(r.response_time_ms)
            model_stats[r.model]["success"] += 1
    
    # 비교 표
    print("\n📈 Model Comparison:")
    print("-"*70)
    print(f"{'Model':<15} {'Avg Time':<12} {'Min':<10} {'Max':<10} {'Success':<10}")
    print("-"*70)
    
    for model in MODELS_TO_TEST:
        if model in model_stats:
            stats = model_stats[model]
            times = stats["times"]
            if times:
                avg = sum(times) / len(times)
                print(f"{model:<15} {avg:<12.0f}ms {min(times):<10.0f}ms {max(times):<10.0f}ms {stats['success']}/{stats['total']}")
    
    print("-"*70)
    
    # 질문별 비교
    print("\n📋 Question-by-Question Comparison:")
    print("-"*80)
    
    for question in COMPLEX_QUESTIONS:
        print(f"\n❓ {question[:50]}...")
        for model in MODELS_TO_TEST:
            q_results = [r for r in results if r.model == model and r.question == question]
            if q_results:
                r = q_results[0]
                status = "✅" if r.success else "❌"
                time_str = f"{r.response_time_ms:.0f}ms" if r.success else r.error[:20]
                print(f"   {model:<15}: {status} {time_str}")
    
    # 속도 비교
    if all(model in model_stats for model in MODELS_TO_TEST):
        times_4o = model_stats["gpt-4o-mini"]["times"]
        times_5 = model_stats["gpt-5-mini"]["times"]
        
        if times_4o and times_5:
            avg_4o = sum(times_4o) / len(times_4o)
            avg_5 = sum(times_5) / len(times_5)
            speedup = avg_5 / avg_4o if avg_4o > 0 else 0
            
            print("\n" + "="*80)
            print("🏆 CONCLUSION")
            print("="*80)
            print(f"\n   gpt-4o-mini: {avg_4o:.0f}ms (평균)")
            print(f"   gpt-5-mini:  {avg_5:.0f}ms (평균)")
            print(f"\n   ⚡ gpt-4o-mini가 {speedup:.1f}x 빠름!")
            print("="*80)


def main():
    print("\n🚀 Starting Complex Query Benchmark...")
    
    results = run_complex_benchmark()
    
    print_comparison(results)
    
    # 결과 저장
    output_file = PROJECT_ROOT / "scripts" / "benchmark" / "complex_query_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # 원래 모델 복구
    print("\n🔄 Restoring original model (gpt-5-mini)...")
    update_model_in_code("gpt-5-mini")
    rebuild_rag_container()


if __name__ == "__main__":
    main()
