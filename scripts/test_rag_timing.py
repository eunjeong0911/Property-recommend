#!/usr/bin/env python3
"""
RAG 파이프라인 타이밍 테스트 스크립트

사용법:
    python scripts/test_rag_timing.py "홍대입구 근처 편의점 가까운 방 추천해줘"
    python scripts/test_rag_timing.py  # 대화형 모드

각 단계별 소요 시간을 측정하여 출력합니다.
"""

import requests
import time
import sys
import subprocess
import threading
import queue
from datetime import datetime

# RAG API 엔드포인트
RAG_API_URL = "http://localhost:8001/query"
DOCKER_CONTAINER = "skn18-final-1team-rag-1"

def print_header():
    """헤더 출력"""
    print("\n" + "=" * 70)
    print("🏠 RAG 파이프라인 타이밍 테스트 (상세 모드)")
    print("=" * 70)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 API: {RAG_API_URL}")
    print("-" * 70)

def get_docker_logs_since(container: str, since_time: str) -> str:
    """Docker 컨테이너 로그 가져오기"""
    try:
        result = subprocess.run(
            ["docker", "logs", container, "--since", since_time],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"로그 가져오기 실패: {e}"

def parse_timing_from_logs(logs: str) -> dict:
    """로그에서 타이밍 정보 추출"""
    timings = {
        'location': '',
        'location_type': '',
        'facilities': '',
        'cache_hit': False,
        'neo4j_results': 0,
        'sql_results': 0,
        'final_results': 0,
        # 시간 정보 (ms)
        'neo4j_time': None,
        'sql_time': None,
        'generate_time': None,
        'total_time': None,
    }
    
    lines = logs.split('\n')
    
    # 시간 파싱을 위한 타임스탬프 추적
    step_starts = {}
    
    for i, line in enumerate(lines):
        # 위치 정보
        if '[QueryBuilder] 📍 Location:' in line:
            timings['location'] = line.split('Location:')[-1].strip()
        
        # 시설 정보  
        if '[QueryBuilder] 🏷️ Facilities:' in line or '[QueryBuilder] 🏷️ Facilities:' in line:
            timings['facilities'] = line.split('Facilities:')[-1].strip()
        
        # 캐시 히트
        if 'Cache hit' in line or 'Cache HIT' in line:
            timings['cache_hit'] = True
        
        # Neo4j 결과 수
        if '[QueryBuilder] ✅ Found' in line:
            try:
                count = int(line.split('Found')[1].split('results')[0].strip())
                timings['neo4j_results'] = count
            except:
                pass
        
        if '[Merge] 📊 Graph results:' in line:
            try:
                count = int(line.split(':')[-1].strip())
                timings['neo4j_results'] = count
            except:
                pass
        
        # PostgreSQL 결과
        if '✓ PostgreSQL에서' in line:
            try:
                parts = line.split('PostgreSQL에서')[1]
                count = int(parts.split('개')[0].strip())
                timings['sql_results'] = count
            except:
                pass
        
        # SQL Search 쿼리 실행 시간 (Executing 부터 Query executed 까지)
        if '[SQL Search] 🔍 Executing PostgreSQL query' in line:
            step_starts['sql'] = i
        if '[SQL Search] ✅ Query executed' in line and 'sql' in step_starts:
            # 대략적으로 줄 수로 추정 (실제 타임스탬프 없으면)
            pass
        
        # Generate 단계 정보
        if '[Generate] 📝 Prepared' in line:
            try:
                count = int(line.split('Prepared')[1].split('unique')[0].strip())
                timings['final_results'] = count
            except:
                pass
        
        # Generate 로그에서 시간 추출 "[Generate] 📝 Search log queued: 1234ms"
        if '[Generate] 📝 Search log queued' in line and 'ms' in line:
            try:
                time_part = line.split(':')[-1].strip()
                ms = int(time_part.replace('ms', '').strip())
                timings['generate_time'] = ms
            except:
                pass
        
        # Parallel Search 완료 시간
        if '[Parallel Search] 📊 Graph results:' in line:
            try:
                count = int(line.split(':')[-1].strip())
                timings['neo4j_results'] = count
            except:
                pass
    
    return timings


def test_query(question: str, session_id: str = None) -> dict:
    """
    RAG API에 질문을 보내고 응답 시간을 측정합니다.
    """
    print(f"\n📝 질문: {question}")
    print("-" * 60)
    
    # 요청 준비
    payload = {
        "question": question,
        "session_id": session_id or f"test_{int(time.time())}"
    }
    
    # 로그 시작 시간 기록
    log_start_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    # 단계별 타이밍 측정
    step_times = {}
    
    # 타이밍 시작
    start_time = time.time()
    
    try:
        # API 호출
        print("⏳ API 호출 중...\n")
        response = requests.post(
            RAG_API_URL,
            json=payload,
            timeout=120
        )
        
        # 타이밍 종료
        end_time = time.time()
        total_time_ms = int((end_time - start_time) * 1000)
        
        # 잠시 대기 후 로그 가져오기
        time.sleep(0.5)
        logs = get_docker_logs_since(DOCKER_CONTAINER, log_start_time)
        timings = parse_timing_from_logs(logs)
        
        # 로그에서 타임스탬프 파싱하여 단계별 시간 계산
        step_times = parse_step_times_from_logs(logs)
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "No answer received")
            
            # 로그에서 타임스탬프 파싱하여 단계별 시간 계산
            step_times = parse_step_times_from_logs(logs)
            
            # 상세 타이밍 출력 (간소화된 형식)
            print("\n" + "=" * 60)
            print("📊 단계별 처리 정보")
            print("=" * 60)
            
            if timings['location']:
                print(f"📍 위치: {timings['location']}")
            if timings['facilities']:
                print(f"🏷️  시설: {timings['facilities']}")
            
            print("-" * 60)
            
            # 결과 정보
            neo4j_results = timings.get('neo4j_results', '?')
            sql_results = timings.get('sql_results', '?')
            final_results = timings.get('final_results', '?')
            
            if timings['cache_hit']:
                print(f"⚡ Neo4j: 캐시 히트 (스킵)")
            else:
                neo4j_time = step_times.get('neo4j', '-')
                print(f"🔍 Neo4j 검색: {neo4j_results}개 결과 | 시간: {neo4j_time}")
            
            sql_time = step_times.get('sql', '-')
            print(f"🗄️  PostgreSQL: {sql_results}개 조회 | 시간: {sql_time}")
            
            gen_time = step_times.get('generate', '-')
            print(f"🤖 LLM 생성: {final_results}개 매물 답변 | 시간: {gen_time}")
            
            print("-" * 60)
            print(f"⏱️  총 소요 시간: {total_time_ms}ms ({total_time_ms/1000:.2f}초)")
            print("=" * 60)
            
            print(f"\n💬 답변:\n")
            # 답변 전체 출력 (500자 제한 제거)
            print(answer)
            print("\n" + "=" * 60)
            
            return {
                'success': True,
                'answer': answer,
                'total_time_ms': total_time_ms,
                'session_id': payload['session_id'],
                'timings': timings,
                'step_times': step_times
            }

        else:
            print(f"\n❌ API 오류: HTTP {response.status_code}")
            print(f"   응답: {response.text[:500]}")
            return {
                'success': False,
                'error': f"HTTP {response.status_code}",
                'total_time_ms': total_time_ms
            }
            
    except requests.exceptions.Timeout:
        print("\n❌ 타임아웃: API 응답이 2분을 초과했습니다.")
        return {'success': False, 'error': 'Timeout'}
    except requests.exceptions.ConnectionError:
        print("\n❌ 연결 오류: RAG 서버에 연결할 수 없습니다.")
        print("   → docker-compose up -d rag 명령으로 서버를 시작하세요.")
        return {'success': False, 'error': 'Connection refused'}
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
        return {'success': False, 'error': str(e)}


def parse_step_times_from_logs(logs: str) -> dict:
    """Docker 로그에서 각 단계별 시간을 추정"""
    import re
    
    step_times = {
        'neo4j': '-',
        'sql': '-',
        'generate': '-'
    }
    
    lines = logs.split('\n')
    
    for line in lines:
        # [Neo4j] ✅ 완료: 31개 결과 | 시간: 152ms
        if '[Neo4j] ✅' in line and '시간:' in line:
            match = re.search(r'시간:\s*(\d+)ms', line)
            if match:
                step_times['neo4j'] = f"{match.group(1)}ms"
        
        # [Neo4j] ⚡ 캐시 히트! | 시간: 5ms
        if '[Neo4j] ⚡' in line and '시간:' in line:
            match = re.search(r'시간:\s*(\d+)ms', line)
            if match:
                step_times['neo4j'] = f"{match.group(1)}ms (캐시)"
        
        # [SQL] ✅ 완료: 28개 조회 | 시간: 89ms
        if '[SQL] ✅' in line and '시간:' in line:
            match = re.search(r'시간:\s*(\d+)ms', line)
            if match:
                step_times['sql'] = f"{match.group(1)}ms"
        
        # [LLM] ✅ 완료: 25개 매물 답변 | 시간: 1823ms
        if '[LLM] ✅' in line and '시간:' in line:
            match = re.search(r'시간:\s*(\d+)ms', line)
            if match:
                step_times['generate'] = f"{match.group(1)}ms"
    
    return step_times



def interactive_mode():
    """대화형 모드"""
    print_header()
    print("💡 대화형 모드 (종료: 'q' 또는 'exit')")
    print("-" * 70)
    
    session_id = f"interactive_{int(time.time())}"
    results = []
    
    while True:
        try:
            question = input("\n🔍 질문 입력: ").strip()
            
            if question.lower() in ['q', 'exit', 'quit', '종료']:
                break
            
            if not question:
                print("   ⚠️ 질문을 입력해주세요.")
                continue
            
            result = test_query(question, session_id)
            results.append({'question': question, **result})
            
        except KeyboardInterrupt:
            print("\n\n👋 종료합니다.")
            break
    
    # 결과 요약
    if results:
        print_summary(results)

def print_summary(results: list):
    """결과 요약 출력"""
    print("\n" + "=" * 70)
    print("📊 테스트 결과 요약")
    print("=" * 70)
    
    successful = [r for r in results if r.get('success')]
    if successful:
        times = [r['total_time_ms'] for r in successful]
        print(f"✅ 성공: {len(successful)}/{len(results)}")
        print(f"⏱️  평균: {sum(times)//len(times)}ms | 최소: {min(times)}ms | 최대: {max(times)}ms")
    
    print("-" * 70)
    for i, r in enumerate(results, 1):
        status = "✅" if r.get('success') else "❌"
        time_str = f"{r.get('total_time_ms', 0):>5}ms" if r.get('total_time_ms') else "  N/A"
        print(f"{i}. {status} [{time_str}] {r['question'][:40]}...")

def single_query_mode(question: str):
    """단일 질문 모드"""
    print_header()
    result = test_query(question)
    
    print("\n" + "=" * 70)
    if result['success']:
        print(f"✅ 테스트 완료 | 총 시간: {result['total_time_ms']}ms")
    else:
        print(f"❌ 테스트 실패 | 오류: {result.get('error')}")
    print("=" * 70)

def batch_test():
    """배치 테스트 모드"""
    test_questions = [
        "홍대입구 근처 편의점 가까운 방 추천해줘",
        "서울대 근처 월세 50만원 이하 방",
        "강남역 안전한 원룸 찾아줘",
    ]
    
    print_header()
    print("🔄 배치 테스트 모드")
    print(f"📋 테스트 질문 수: {len(test_questions)}")
    print("-" * 70)
    
    results = []
    for i, question in enumerate(test_questions, 1):
        print(f"\n[{i}/{len(test_questions)}]", end=" ")
        result = test_query(question)
        results.append({'question': question, **result})
        time.sleep(1)
    
    print_summary(results)

def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ['--batch', '-b']:
            batch_test()
        elif arg in ['--help', '-h']:
            print(__doc__)
        else:
            question = " ".join(sys.argv[1:])
            single_query_mode(question)
    else:
        interactive_mode()

if __name__ == "__main__":
    main()

