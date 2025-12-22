#!/usr/bin/env python3
"""
전체 RAG API 다중 모델 벤치마크 스크립트

neo4j_search_node의 모델을 변경하면서 전체 RAG API 응답 시간을 측정합니다.
각 모델별로 Docker 컨테이너를 재빌드하고 테스트합니다.

테스트 모델:
- gpt-4o-mini
- gpt-5-mini  
- gpt-5-nano
- gpt-5

Usage:
    python scripts/benchmark_rag_multi_model.py
    
전제 조건:
    - Docker 실행 중
    - OPENAI_API_KEY 환경변수 설정
"""

import os
import sys
import subprocess
import time
import json
import requests
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from pathlib import Path

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
NEO4J_SEARCH_NODE = PROJECT_ROOT / "apps" / "rag" / "nodes" / "neo4j_search_node.py"

# RAG 서비스 URL
RAG_API_URL = "http://localhost:8001"

# 테스트할 모델 목록
MODELS_TO_TEST = [
    "gpt-4o-mini",
    "gpt-5-mini",
    "gpt-5-nano", 
    "gpt-5",
]

# 테스트 질문 (단순한 질문만 - 타임아웃 방지)
TEST_QUESTIONS = [
    "홍대입구역 근처 치안 좋은 매물 찾아줘",
]

# 타임아웃 설정 (초)
API_TIMEOUT = 180  # 3분

@dataclass
class ModelBenchmarkResult:
    model: str
    question: str
    total_time_ms: float
    success: bool
    error: str = ""


def update_model_in_code(model_name: str) -> bool:
    """neo4j_search_node.py에서 모델명 변경"""
    try:
        content = NEO4J_SEARCH_NODE.read_text(encoding='utf-8')
        
        # search_with_agent 함수에서 모델 변경
        # 기존: llm = ChatOpenAI(model="gpt-5-mini")
        import re
        pattern = r'(llm = ChatOpenAI\(model=")[^"]+(")'
        
        # gpt-5 시리즈는 temperature 미지원
        if model_name.startswith("gpt-5"):
            replacement = f'\\1{model_name}\\2'
        else:
            replacement = f'\\1{model_name}\\2'
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content == content:
            print(f"  ⚠️ No model pattern found to replace")
            return False
        
        NEO4J_SEARCH_NODE.write_text(new_content, encoding='utf-8')
        print(f"  ✅ Model updated to: {model_name}")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to update model: {e}")
        return False


def rebuild_rag_container() -> bool:
    """RAG Docker 컨테이너 재빌드"""
    try:
        print("  🔨 Rebuilding RAG container...")
        
        # 컨테이너 중지
        subprocess.run(
            ["docker-compose", "stop", "rag"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=30
        )
        
        # 컨테이너 재빌드
        result = subprocess.run(
            ["docker-compose", "build", "rag"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=300
        )
        
        if result.returncode != 0:
            print(f"  ❌ Build failed: {result.stderr.decode()[:200]}")
            return False
        
        # 컨테이너 시작
        result = subprocess.run(
            ["docker-compose", "up", "-d", "rag"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"  ❌ Start failed: {result.stderr.decode()[:200]}")
            return False
        
        # 서비스 준비 대기
        print("  ⏳ Waiting for service to be ready...")
        for i in range(30):  # 최대 30초 대기
            time.sleep(1)
            try:
                response = requests.post(
                    f"{RAG_API_URL}/query",
                    json={"question": "test"},
                    timeout=5
                )
                if response.status_code in [200, 400, 422]:
                    print("  ✅ RAG service is ready!")
                    return True
            except:
                pass
        
        print("  ❌ Service did not become ready in time")
        return False
        
    except Exception as e:
        print(f"  ❌ Container rebuild failed: {e}")
        return False


def benchmark_api_call(question: str) -> tuple:
    """API 호출 벤치마크"""
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{RAG_API_URL}/query",
            json={"question": question},
            timeout=API_TIMEOUT
        )
        
        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000
        
        return (
            total_time_ms,
            response.status_code == 200,
            "" if response.status_code == 200 else response.text[:100]
        )
        
    except requests.exceptions.Timeout:
        return (API_TIMEOUT * 1000, False, f"Timeout ({API_TIMEOUT}s)")
    except Exception as e:
        return (0, False, str(e))


def run_full_benchmark() -> List[ModelBenchmarkResult]:
    """모든 모델에 대해 벤치마크 실행"""
    all_results = []
    
    print("\n" + "="*80)
    print("🚀 Full RAG API Multi-Model Benchmark")
    print("="*80)
    print(f"📊 Models to test: {MODELS_TO_TEST}")
    print(f"❓ Questions: {len(TEST_QUESTIONS)}")
    print("="*80)
    
    for model in MODELS_TO_TEST:
        print(f"\n{'='*60}")
        print(f"📦 Testing model: {model}")
        print("="*60)
        
        # 1. 모델 코드 변경
        if not update_model_in_code(model):
            print(f"  ⚠️ Skipping {model} - code update failed")
            continue
        
        # 2. Docker 재빌드
        if not rebuild_rag_container():
            print(f"  ⚠️ Skipping {model} - container rebuild failed")
            continue
        
        # 3. 벤치마크 실행
        for question in TEST_QUESTIONS:
            print(f"\n  ❓ {question[:40]}...", end=" ", flush=True)
            
            time_ms, success, error = benchmark_api_call(question)
            
            result = ModelBenchmarkResult(
                model=model,
                question=question,
                total_time_ms=time_ms,
                success=success,
                error=error
            )
            all_results.append(result)
            
            if success:
                print(f"✅ {time_ms:.0f}ms")
            else:
                print(f"❌ {error[:30]}")
    
    return all_results


def print_comparison_table(results: List[ModelBenchmarkResult]):
    """모델별 비교 표 출력"""
    print("\n" + "="*80)
    print("📊 MULTI-MODEL RAG API BENCHMARK RESULTS")
    print("="*80)
    
    # 모델별 평균 계산
    model_stats = {}
    for result in results:
        if result.model not in model_stats:
            model_stats[result.model] = {"times": [], "success": 0, "total": 0}
        
        model_stats[result.model]["total"] += 1
        if result.success:
            model_stats[result.model]["times"].append(result.total_time_ms)
            model_stats[result.model]["success"] += 1
    
    # 표 출력
    print("\n" + "-"*80)
    print(f"{'Model':<15} {'Avg Time (ms)':<15} {'Min (ms)':<12} {'Max (ms)':<12} {'Success Rate':<15}")
    print("-"*80)
    
    for model in MODELS_TO_TEST:
        if model in model_stats:
            stats = model_stats[model]
            times = stats["times"]
            success_rate = stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0
            
            if times:
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                print(f"{model:<15} {avg_time:<15.0f} {min_time:<12.0f} {max_time:<12.0f} {success_rate:<15.1f}%")
            else:
                print(f"{model:<15} {'N/A':<15} {'N/A':<12} {'N/A':<12} {success_rate:<15.1f}%")
    
    print("-"*80)
    
    # 최고 성능 모델 표시
    best_model = None
    best_time = float('inf')
    for model, stats in model_stats.items():
        if stats["times"]:
            avg = sum(stats["times"]) / len(stats["times"])
            if avg < best_time:
                best_time = avg
                best_model = model
    
    if best_model:
        print(f"\n🏆 Best Model: {best_model} ({best_time:.0f}ms average)")


def main():
    print("\n🔍 Starting Multi-Model RAG API Benchmark...")
    
    # 벤치마크 실행
    results = run_full_benchmark()
    
    # 결과 표시
    print_comparison_table(results)
    
    # 결과 저장
    output_file = PROJECT_ROOT / "scripts" / "benchmark_rag_multi_model_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # 원래 모델로 복구 (gpt-5-mini)
    print("\n🔄 Restoring original model (gpt-5-mini)...")
    update_model_in_code("gpt-5-mini")
    rebuild_rag_container()


if __name__ == "__main__":
    main()
