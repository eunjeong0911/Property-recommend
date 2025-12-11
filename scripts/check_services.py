#!/usr/bin/env python3
"""
서비스 상태 확인 스크립트
모든 서비스가 정상 작동하는지 확인합니다.
"""

import requests
import time
import sys

def check_service(name, url, timeout=5):
    """서비스 헬스체크"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code < 500:
            print(f"✓ {name}: 정상 작동 중 ({url})")
            return True
        else:
            print(f"✗ {name}: 오류 (상태 코드: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print(f"✗ {name}: 연결 실패 ({url})")
        return False
    except requests.exceptions.Timeout:
        print(f"✗ {name}: 시간 초과 ({url})")
        return False
    except Exception as e:
        print(f"✗ {name}: 오류 - {e}")
        return False

def main():
    print("\n" + "=" * 70)
    print(" " * 20 + "서비스 상태 확인")
    print("=" * 70 + "\n")
    
    services = {
        "프론트엔드": "http://localhost:3000",
        "백엔드 API": "http://localhost:8000",
        "RAG 챗봇": "http://localhost:8001/health",
        "Neo4j Browser": "http://localhost:7474",
    }
    
    results = {}
    for name, url in services.items():
        results[name] = check_service(name, url)
        time.sleep(0.5)
    
    print("\n" + "=" * 70)
    print("결과 요약")
    print("=" * 70)
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\n정상: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n✓ 모든 서비스가 정상 작동 중입니다!")
        print("\n접속 URL:")
        print("  - 프론트엔드: http://localhost:3000")
        print("  - 백엔드 API: http://localhost:8000")
        print("  - 백엔드 Admin: http://localhost:8000/admin/")
        print("  - RAG 챗봇: http://localhost:8001")
        print("  - Neo4j Browser: http://localhost:7474")
    else:
        print("\n⚠ 일부 서비스에 문제가 있습니다.")
        print("\n문제 해결:")
        print("  1. docker-compose ps로 컨테이너 상태 확인")
        print("  2. docker-compose logs [서비스명]으로 로그 확인")
        print("  3. docker-compose restart [서비스명]으로 재시작")
        sys.exit(1)
    
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
