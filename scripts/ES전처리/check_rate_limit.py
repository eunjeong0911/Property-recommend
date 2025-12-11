"""
OpenAI API Rate Limit 확인 스크립트

사용법:
    cd scripts
    ..\apps\backend\.venv\Scripts\python.exe ES전처리\check_rate_limit.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent.parent.parent / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def check_limits():
    print("=" * 60)
    print("OpenAI API Rate Limit 확인")
    print("=" * 60)
    
    # 간단한 요청으로 헤더 확인
    response = client.chat.completions.with_raw_response.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": "hi"}],
        max_completion_tokens=10
    )
    
    headers = response.headers
    
    print("\n[Rate Limit 정보]")
    print(f"  요청 제한 (RPM): {headers.get('x-ratelimit-limit-requests', 'N/A')}")
    print(f"  토큰 제한 (TPM): {headers.get('x-ratelimit-limit-tokens', 'N/A')}")
    print(f"  남은 요청: {headers.get('x-ratelimit-remaining-requests', 'N/A')}")
    print(f"  남은 토큰: {headers.get('x-ratelimit-remaining-tokens', 'N/A')}")
    print(f"  리셋 시간(요청): {headers.get('x-ratelimit-reset-requests', 'N/A')}")
    print(f"  리셋 시간(토큰): {headers.get('x-ratelimit-reset-tokens', 'N/A')}")
    
    # 권장 동시 처리 수 계산
    rpm = headers.get('x-ratelimit-limit-requests')
    if rpm:
        rpm = int(rpm)
        # 40초/요청 기준, 분당 처리 가능 수
        safe_concurrent = min(rpm // 2, 50)  # 안전하게 절반만 사용
        print(f"\n[권장 설정]")
        print(f"  분당 요청 제한: {rpm}")
        print(f"  권장 동시 처리 수: {safe_concurrent}개")
        print(f"  예상 처리 시간 (9,900개): {(9900 * 40 / safe_concurrent) / 3600:.1f}시간")


if __name__ == "__main__":
    check_limits()
