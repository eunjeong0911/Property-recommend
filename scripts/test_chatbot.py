#!/usr/bin/env python3
"""
챗봇 테스트 스크립트
RAG 챗봇 서비스에 질문을 보내고 응답을 확인합니다.
"""

import requests
import json
import sys

def test_chatbot(message, base_url="http://localhost:8001"):
    """
    챗봇에 메시지를 보내고 응답을 받습니다.
    
    Args:
        message: 챗봇에 보낼 질문
        base_url: RAG 서비스 URL
    """
    print(f"\n질문: {message}")
    print("-" * 70)
    
    try:
        # RAG 서비스 엔드포인트
        response = requests.post(
            f"{base_url}/query",
            json={"question": message},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"응답: {result.get('response', result)}")
            return True
        else:
            print(f"✗ 오류 (상태 코드: {response.status_code})")
            print(f"응답: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ RAG 서비스에 연결할 수 없습니다.")
        print("  docker-compose ps로 rag 서비스가 실행 중인지 확인하세요.")
        return False
    except requests.exceptions.Timeout:
        print("✗ 요청 시간 초과 (30초)")
        return False
    except Exception as e:
        print(f"✗ 오류 발생: {e}")
        return False


def test_health(base_url="http://localhost:8001"):
    """RAG 서비스 헬스체크"""
    print("\nRAG 서비스 헬스체크...")
    print("-" * 70)
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✓ RAG 서비스가 정상 작동 중입니다.")
            return True
        else:
            print(f"✗ RAG 서비스 응답 이상 (상태 코드: {response.status_code})")
            return False
    except Exception as e:
        print(f"✗ RAG 서비스에 연결할 수 없습니다: {e}")
        return False


def main():
    print("\n" + "=" * 70)
    print(" " * 25 + "챗봇 테스트")
    print("=" * 70)
    
    # 헬스체크
    if not test_health():
        print("\n⚠ RAG 서비스가 실행되지 않았습니다.")
        print("다음 명령어로 서비스를 시작하세요:")
        print("  docker-compose up -d rag")
        sys.exit(1)
    
    # 테스트 질문들
    test_questions = [
        "홍대입구역 근처 매물 추천해줘",
        "강남역 주변 원룸 찾아줘",
        "신촌역 근처 편의시설이 좋은 곳 알려줘",
    ]
    
    print("\n" + "=" * 70)
    print("테스트 질문 실행")
    print("=" * 70)
    
    success_count = 0
    for question in test_questions:
        if test_chatbot(question):
            success_count += 1
        print()
    
    print("=" * 70)
    print(f"결과: {success_count}/{len(test_questions)} 성공")
    print("=" * 70)
    
    if success_count == len(test_questions):
        print("\n✓ 모든 테스트가 성공했습니다!")
    else:
        print("\n⚠ 일부 테스트가 실패했습니다.")


if __name__ == "__main__":
    main()
