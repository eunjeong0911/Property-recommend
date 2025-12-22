#!/usr/bin/env python3
"""
Neo4j Search Node 모델 벤치마크 스크립트

동일한 질문에 대해 여러 OpenAI 모델의 응답 속도를 비교합니다.
- gpt-4o-mini
- gpt-4.1-mini (gpt-5-mini 대신)
- gpt-4.1-nano (gpt-5-nano 대신)
- gpt-4o (gpt-5 대신)

Usage:
    python scripts/benchmark_neo4j_models.py
"""

import os
import sys
import time
import json
from typing import Dict, List, Any
from dataclasses import dataclass

# .env 파일에서 환경변수 로드
from dotenv import load_dotenv
load_dotenv()

# 프로젝트 루트 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'rag'))

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

# 테스트할 모델 목록 (사용자 요청대로)
MODELS_TO_TEST = [
    "gpt-4o-mini",
    "gpt-5-mini",   # gpt-5 시리즈 경량 모델
    "gpt-5-nano",   # gpt-5 시리즈 초경량 모델
    "gpt-5",        # gpt-5 풀 모델
]

# 테스트 질문들
TEST_QUESTIONS = [
    "홍대입구역 근처 치안 좋은 매물 찾아줘",
    "강남역 주변 병원과 편의점 가까운 곳",  
    "신촌역 근처 공원이 있는 안전한 곳",
]

@dataclass
class BenchmarkResult:
    model: str
    question: str
    response_time_ms: float
    success: bool
    result_count: int
    error: str = ""


# Mock tools for benchmark (실제 Neo4j 없이 테스트)
@tool
def mock_search_properties_near_subway(location_keyword: str):
    """Find properties near a specific Subway Station."""
    return [{"id": f"mock_{location_keyword}_{i}", "name": f"Property {i}"} for i in range(5)]

@tool
def mock_search_properties_with_safety(location_keyword: str):
    """Find properties with good safety infrastructure."""
    return [{"id": f"mock_safety_{location_keyword}_{i}", "name": f"Safe Property {i}"} for i in range(3)]

@tool
def mock_search_properties_near_hospital(location_keyword: str, general_only: bool = False):
    """Find properties near Hospitals."""
    return [{"id": f"mock_hospital_{location_keyword}_{i}", "name": f"Hospital Nearby {i}"} for i in range(4)]

@tool
def mock_search_properties_near_convenience(location_keyword: str):
    """Find properties near Convenience Stores."""
    return [{"id": f"mock_conv_{location_keyword}_{i}", "name": f"Convenient {i}"} for i in range(4)]

@tool
def mock_search_properties_near_park(location_keyword: str):
    """Find properties near Parks."""
    return [{"id": f"mock_park_{location_keyword}_{i}", "name": f"Near Park {i}"} for i in range(3)]

@tool
def mock_search_properties_multi_criteria(
    location_keyword: str,
    convenience: bool = False,
    hospital: bool = False,
    pharmacy: bool = False,
    safety: bool = False,
    park: bool = False
):
    """Find properties that satisfy MULTIPLE facility requirements."""
    return [{"id": f"mock_multi_{location_keyword}_{i}", "name": f"Multi-Criteria {i}"} for i in range(5)]


def benchmark_model(model_name: str, question: str) -> BenchmarkResult:
    """
    단일 모델에 대해 벤치마크 실행
    """
    try:
        # LLM 초기화
        # gpt-5 시리즈는 reasoning 모델이라 temperature 미지원
        if model_name.startswith("gpt-5"):
            llm = ChatOpenAI(model=model_name)
        else:
            llm = ChatOpenAI(model=model_name, temperature=0)
        
        tools = [
            mock_search_properties_near_subway,
            mock_search_properties_with_safety,
            mock_search_properties_near_hospital,
            mock_search_properties_near_convenience,
            mock_search_properties_near_park,
            mock_search_properties_multi_criteria,
        ]
        llm_with_tools = llm.bind_tools(tools)
        
        messages = [
            SystemMessage(content="You are a smart real estate assistant. Select the appropriate search tool based on the user's request."),
            HumanMessage(content=question)
        ]
        
        # 시간 측정 시작
        start_time = time.time()
        
        found_properties = []
        max_steps = 3
        
        for step in range(max_steps):
            ai_msg = llm_with_tools.invoke(messages)
            messages.append(ai_msg)
            
            if not ai_msg.tool_calls:
                break
            
            for tool_call in ai_msg.tool_calls:
                t_name = tool_call['name']
                t_args = tool_call['args']
                
                # Mock tool 실행
                tool_output = None
                if t_name == "mock_search_properties_near_subway":
                    tool_output = mock_search_properties_near_subway.invoke(t_args)
                elif t_name == "mock_search_properties_with_safety":
                    tool_output = mock_search_properties_with_safety.invoke(t_args)
                elif t_name == "mock_search_properties_near_hospital":
                    tool_output = mock_search_properties_near_hospital.invoke(t_args)
                elif t_name == "mock_search_properties_near_convenience":
                    tool_output = mock_search_properties_near_convenience.invoke(t_args)
                elif t_name == "mock_search_properties_near_park":
                    tool_output = mock_search_properties_near_park.invoke(t_args)
                elif t_name == "mock_search_properties_multi_criteria":
                    tool_output = mock_search_properties_multi_criteria.invoke(t_args)
                
                if tool_output and isinstance(tool_output, list):
                    found_properties.extend(tool_output)
                
                messages.append(ToolMessage(
                    content=json.dumps(tool_output or [], default=str), 
                    tool_call_id=tool_call["id"]
                ))
        
        # 시간 측정 종료
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        return BenchmarkResult(
            model=model_name,
            question=question,
            response_time_ms=response_time_ms,
            success=True,
            result_count=len(found_properties)
        )
        
    except Exception as e:
        return BenchmarkResult(
            model=model_name,
            question=question,
            response_time_ms=0,
            success=False,
            result_count=0,
            error=str(e)
        )


def run_benchmark() -> List[BenchmarkResult]:
    """
    전체 벤치마크 실행
    """
    results = []
    
    print("\n" + "="*80)
    print("🚀 Neo4j Search Node Model Benchmark")
    print("="*80)
    
    for model in MODELS_TO_TEST:
        print(f"\n📊 Testing model: {model}")
        print("-"*40)
        
        for question in TEST_QUESTIONS:
            print(f"  ❓ {question[:40]}...", end=" ", flush=True)
            
            result = benchmark_model(model, question)
            results.append(result)
            
            if result.success:
                print(f"✅ {result.response_time_ms:.0f}ms ({result.result_count} results)")
            else:
                print(f"❌ Error: {result.error[:50]}")
    
    return results


def print_summary(results: List[BenchmarkResult]):
    """
    벤치마크 결과 요약 출력
    """
    print("\n" + "="*80)
    print("📈 BENCHMARK RESULTS SUMMARY")
    print("="*80)
    
    # 모델별 평균 계산
    model_stats: Dict[str, Dict[str, Any]] = {}
    
    for result in results:
        if result.model not in model_stats:
            model_stats[result.model] = {
                "times": [],
                "success_count": 0,
                "total_count": 0
            }
        
        model_stats[result.model]["total_count"] += 1
        if result.success:
            model_stats[result.model]["times"].append(result.response_time_ms)
            model_stats[result.model]["success_count"] += 1
    
    # 표 출력
    print("\n" + "-"*80)
    print(f"{'Model':<20} {'Avg Time (ms)':<15} {'Min (ms)':<12} {'Max (ms)':<12} {'Success Rate':<15}")
    print("-"*80)
    
    for model, stats in model_stats.items():
        times = stats["times"]
        success_rate = stats["success_count"] / stats["total_count"] * 100
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            print(f"{model:<20} {avg_time:<15.0f} {min_time:<12.0f} {max_time:<12.0f} {success_rate:<15.1f}%")
        else:
            print(f"{model:<20} {'N/A':<15} {'N/A':<12} {'N/A':<12} {success_rate:<15.1f}%")
    
    print("-"*80)
    
    # 질문별 결과
    print("\n📋 Results by Question:")
    print("-"*80)
    
    for question in TEST_QUESTIONS:
        print(f"\n❓ {question}")
        q_results = [r for r in results if r.question == question]
        for r in q_results:
            status = "✅" if r.success else "❌"
            time_str = f"{r.response_time_ms:.0f}ms" if r.success else "Failed"
            print(f"   {r.model:<20}: {status} {time_str}")


def main():
    """
    메인 함수
    """
    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("   export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)
    
    print("\n🔑 API Key detected. Starting benchmark...")
    
    # 벤치마크 실행
    results = run_benchmark()
    
    # 결과 요약
    print_summary(results)
    
    # 결과 JSON 저장
    output_file = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([{
            "model": r.model,
            "question": r.question,
            "response_time_ms": r.response_time_ms,
            "success": r.success,
            "result_count": r.result_count,
            "error": r.error
        } for r in results], f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
