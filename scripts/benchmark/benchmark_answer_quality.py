#!/usr/bin/env python3
"""
RAG 답변 품질 비교 벤치마크

각 모델이 생성한 답변의 품질을 비교합니다:
- 매물 개수
- 주소 정보 포함 여부
- 가격 정보 포함 여부
- 시설 정보 포함 여부
- 안전 정보 포함 여부

Usage:
    python scripts/benchmark_answer_quality.py
"""

import os
import sys
import subprocess
import time
import json
import re
import requests
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
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
]

# 테스트 질문
TEST_QUESTION = "홍대입구역 근처 치안 좋은 매물 찾아줘"

# 타임아웃 설정 (초)
API_TIMEOUT = 180

@dataclass
class QualityMetrics:
    """답변 품질 메트릭"""
    property_count: int = 0          # 추천된 매물 수
    has_address: bool = False         # 주소 정보 포함
    has_price: bool = False           # 가격 정보 포함
    has_area: bool = False            # 면적 정보 포함
    has_station: bool = False         # 역 정보 포함
    has_safety: bool = False          # 안전 정보 (CCTV, 경찰서 등)
    has_facilities: bool = False      # 시설 정보 (편의점, 병원 등)
    has_detail_link: bool = False     # 상세보기 링크
    response_length: int = 0          # 응답 길이
    quality_score: float = 0.0        # 종합 품질 점수 (0-100)


@dataclass 
class AnswerQualityResult:
    """모델별 답변 품질 결과"""
    model: str
    question: str
    response_time_ms: float
    success: bool
    answer: str = ""
    metrics: QualityMetrics = field(default_factory=QualityMetrics)
    error: str = ""


def analyze_answer_quality(answer: str) -> QualityMetrics:
    """답변 품질 분석"""
    metrics = QualityMetrics()
    
    if not answer:
        return metrics
    
    metrics.response_length = len(answer)
    
    # 1. 매물 개수 - "1순위", "2순위", "3순위" 또는 "**1.**", "**2.**" 패턴
    rank_patterns = [
        r'\*\*\d순위\*\*',
        r'\*\*\d\.\*\*',
        r'\d순위',
        r'^\d\.',
    ]
    property_count = 0
    for pattern in rank_patterns:
        matches = re.findall(pattern, answer, re.MULTILINE)
        if matches:
            property_count = max(property_count, len(matches))
    metrics.property_count = min(property_count, 3)  # 최대 3개
    
    # 2. 주소 정보 - "서울", "구", "동", "로" 등
    address_patterns = [
        r'서울[시]?\s*\w+구',
        r'\w+구\s*\w+동',
        r'\w+로\s*\d+',
        r'주소[:：]',
    ]
    metrics.has_address = any(re.search(p, answer) for p in address_patterns)
    
    # 3. 가격 정보 - "만원", "억", "보증금", "월세"
    price_patterns = [
        r'\d+[,\d]*만원',
        r'\d+억',
        r'보증금',
        r'월세',
        r'전세',
        r'가격[:：]',
    ]
    metrics.has_price = any(re.search(p, answer) for p in price_patterns)
    
    # 4. 면적 정보 - "㎡", "평", "m²"
    area_patterns = [
        r'\d+\.?\d*\s*[㎡m²]',
        r'\d+\.?\d*\s*평',
        r'면적[:：]',
    ]
    metrics.has_area = any(re.search(p, answer) for p in area_patterns)
    
    # 5. 역 정보 - "역", "지하철"
    station_patterns = [
        r'\w+역',
        r'지하철',
        r'도보\s*\d+분',
        r'\d+m',
    ]
    metrics.has_station = any(re.search(p, answer) for p in station_patterns)
    
    # 6. 안전 정보 - "CCTV", "경찰", "비상벨", "치안"
    safety_patterns = [
        r'CCTV',
        r'cctv',
        r'경찰',
        r'비상벨',
        r'소방',
        r'안전',
        r'치안',
    ]
    metrics.has_safety = any(re.search(p, answer) for p in safety_patterns)
    
    # 7. 시설 정보 - "편의점", "병원", "약국", "공원"
    facility_patterns = [
        r'편의',
        r'병원',
        r'약국',
        r'공원',
        r'마트',
        r'교육',
    ]
    metrics.has_facilities = any(re.search(p, answer) for p in facility_patterns)
    
    # 8. 상세보기 링크
    metrics.has_detail_link = '/landDetail/' in answer or '상세보기' in answer
    
    # 9. 종합 품질 점수 계산 (0-100)
    score = 0
    score += min(metrics.property_count * 15, 45)  # 매물 수 (최대 45점)
    score += 10 if metrics.has_address else 0
    score += 10 if metrics.has_price else 0
    score += 5 if metrics.has_area else 0
    score += 10 if metrics.has_station else 0
    score += 10 if metrics.has_safety else 0
    score += 5 if metrics.has_facilities else 0
    score += 5 if metrics.has_detail_link else 0
    
    metrics.quality_score = score
    
    return metrics


def update_model_in_code(model_name: str) -> bool:
    """neo4j_search_node.py에서 모델명 변경"""
    try:
        content = NEO4J_SEARCH_NODE.read_text(encoding='utf-8')
        
        import re
        pattern = r'(llm = ChatOpenAI\(model=")[^"]+(")'
        replacement = f'\\1{model_name}\\2'
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content == content:
            print(f"  ⚠️ No model pattern found")
            return False
        
        NEO4J_SEARCH_NODE.write_text(new_content, encoding='utf-8')
        print(f"  ✅ Model updated to: {model_name}")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


def rebuild_rag_container() -> bool:
    """RAG Docker 컨테이너 재빌드"""
    try:
        print("  🔨 Rebuilding RAG container...")
        
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
        
        print("  ⏳ Waiting for service...")
        for i in range(30):
            time.sleep(1)
            try:
                response = requests.post(
                    f"{RAG_API_URL}/query",
                    json={"question": "test"},
                    timeout=5
                )
                if response.status_code in [200, 400, 422]:
                    print("  ✅ Ready!")
                    return True
            except:
                pass
        
        return False
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


def test_model(model: str) -> AnswerQualityResult:
    """단일 모델 테스트"""
    result = AnswerQualityResult(
        model=model,
        question=TEST_QUESTION,
        response_time_ms=0,
        success=False
    )
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{RAG_API_URL}/query",
            json={"question": TEST_QUESTION},
            timeout=API_TIMEOUT
        )
        
        end_time = time.time()
        result.response_time_ms = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            result.success = True
            data = response.json()
            result.answer = data.get('response', str(data))
            result.metrics = analyze_answer_quality(result.answer)
        else:
            result.error = response.text[:100]
            
    except requests.exceptions.Timeout:
        result.error = f"Timeout ({API_TIMEOUT}s)"
        result.response_time_ms = API_TIMEOUT * 1000
    except Exception as e:
        result.error = str(e)
    
    return result


def run_quality_benchmark() -> List[AnswerQualityResult]:
    """품질 벤치마크 실행"""
    results = []
    
    print("\n" + "="*80)
    print("🎯 RAG Answer Quality Benchmark")
    print("="*80)
    print(f"❓ Test Question: {TEST_QUESTION}")
    print(f"📊 Models: {MODELS_TO_TEST}")
    print("="*80)
    
    for model in MODELS_TO_TEST:
        print(f"\n{'='*60}")
        print(f"📦 Testing: {model}")
        print("="*60)
        
        if not update_model_in_code(model):
            continue
        
        if not rebuild_rag_container():
            continue
        
        print(f"  🧪 Running test...", end=" ", flush=True)
        result = test_model(model)
        results.append(result)
        
        if result.success:
            m = result.metrics
            print(f"✅ {result.response_time_ms:.0f}ms")
            print(f"     📊 Quality Score: {m.quality_score}/100")
            print(f"     🏠 Properties: {m.property_count}")
            print(f"     📍 Address: {'✓' if m.has_address else '✗'}")
            print(f"     💰 Price: {'✓' if m.has_price else '✗'}")
            print(f"     🛡️ Safety: {'✓' if m.has_safety else '✗'}")
        else:
            print(f"❌ {result.error[:50]}")
    
    return results


def print_quality_comparison(results: List[AnswerQualityResult]):
    """품질 비교 표 출력"""
    print("\n" + "="*80)
    print("📊 ANSWER QUALITY COMPARISON")
    print("="*80)
    
    successful = [r for r in results if r.success]
    
    if not successful:
        print("❌ No successful results!")
        return
    
    # 비교 표
    print("\n" + "-"*90)
    print(f"{'Model':<15} {'Time(ms)':<10} {'Score':<8} {'Props':<6} {'Addr':<6} {'Price':<6} {'Safety':<6} {'Link':<6}")
    print("-"*90)
    
    for r in successful:
        m = r.metrics
        print(f"{r.model:<15} {r.response_time_ms:<10.0f} {m.quality_score:<8.0f} "
              f"{m.property_count:<6} {'✓' if m.has_address else '✗':<6} "
              f"{'✓' if m.has_price else '✗':<6} {'✓' if m.has_safety else '✗':<6} "
              f"{'✓' if m.has_detail_link else '✗':<6}")
    
    print("-"*90)
    
    # 최고 품질 모델
    best = max(successful, key=lambda x: x.metrics.quality_score)
    fastest = min(successful, key=lambda x: x.response_time_ms)
    
    print(f"\n🏆 Best Quality: {best.model} (Score: {best.metrics.quality_score}/100)")
    print(f"⚡ Fastest: {fastest.model} ({fastest.response_time_ms:.0f}ms)")
    
    # 답변 샘플 출력
    print("\n" + "="*80)
    print("📝 ANSWER SAMPLES (first 500 chars)")
    print("="*80)
    
    for r in successful:
        print(f"\n--- {r.model} ---")
        print(r.answer[:500] + "..." if len(r.answer) > 500 else r.answer)


def main():
    print("\n🔍 Starting Answer Quality Benchmark...")
    
    results = run_quality_benchmark()
    
    print_quality_comparison(results)
    
    # 결과 저장
    output_file = PROJECT_ROOT / "scripts" / "benchmark_answer_quality_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        data = []
        for r in results:
            d = asdict(r)
            data.append(d)
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # 원래 모델 복구
    print("\n🔄 Restoring original model (gpt-5-mini)...")
    update_model_in_code("gpt-5-mini")
    rebuild_rag_container()


if __name__ == "__main__":
    main()
