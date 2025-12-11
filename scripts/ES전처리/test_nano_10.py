"""
gpt-5-nano 모델 테스트 - 10개 매물만 처리

사용법:
    cd scripts
    ..\apps\backend\.venv\Scripts\python.exe ES전처리\test_nano_10.py
"""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# .env 로드
load_dotenv(Path(__file__).parent.parent.parent / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-5-nano"
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "landData"

STYLE_TAGS = [
    "깔끔함", "세련됨", "아늑함", "모던함", "럭셔리함", "탁트인전망", "화이트톤인테리어",
    "실용적임", "풀옵션", "채광좋음", "조용함", "넓은공간", "수납공간많음", "복층구조", "테라스있음",
    "1인가구추천", "신혼부부추천", "직장인추천", "학생추천", "재택근무추천",
    "신축", "가성비좋음", "반려동물가능", "주차가능", "보안좋음", "엘리베이터있음", "분리형원룸",
    "에어컨있음", "세탁기있음", "냉장고있음", "인덕션있음",
    "고층", "저층", "남향"
]

SYSTEM_PROMPT = f"""부동산 매물 설명 전문가입니다.

매물 정보를 바탕으로:
1) search_text: 3~6문장의 자연스러운 한국어 매물 설명
2) style_tags: 다음 중 1~5개 선택 {STYLE_TAGS}

JSON만 출력: {{"search_text": "설명", "style_tags": ["태그1", "태그2"]}}"""


def extract_info(item):
    parts = []
    addr = item.get("주소_정보", {}).get("전체주소", "")
    if addr:
        parts.append(f"주소: {addr}")
    
    deal = item.get("거래_정보", {})
    if deal.get("거래방식"):
        parts.append(f"거래방식: {deal['거래방식']}")
    
    listing = item.get("매물_정보", {})
    for key in ["건물형태", "전용/공급면적", "해당층/전체층", "방/욕실개수"]:
        if listing.get(key) and listing[key] != "-":
            parts.append(f"{key}: {listing[key]}")
    
    if listing.get("생활시설"):
        parts.append(f"생활시설: {listing['생활시설']}")
    
    return "\n".join(parts)


def test():
    print("=" * 60)
    print(f"모델: {MODEL}")
    print("테스트: 10개 매물")
    print("=" * 60)
    
    # 데이터 로드
    data_path = DATA_DIR / "00_통합_원투룸.json"
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    results = []
    total_time = 0
    success = 0
    
    for i, item in enumerate(data[:10]):
        print(f"\n[{i+1}/10] 매물번호: {item.get('매물번호', 'N/A')}")
        
        listing_info = extract_info(item)
        
        start = time.time()
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": listing_info}
                ],
                response_format={"type": "json_object"}
            )
            
            elapsed = time.time() - start
            total_time += elapsed
            
            result_text = response.choices[0].message.content
            if result_text:
                result = json.loads(result_text)
                print(f"  ✓ 성공 ({elapsed:.2f}초)")
                print(f"  태그: {result.get('style_tags', [])}")
                print(f"  설명: {result.get('search_text', '')[:50]}...")
                results.append(result)
                success += 1
            else:
                print(f"  ✗ 빈 응답 ({elapsed:.2f}초)")
                
        except Exception as e:
            elapsed = time.time() - start
            total_time += elapsed
            print(f"  ✗ 오류: {e}")
    
    print("\n" + "=" * 60)
    print("결과 요약")
    print("=" * 60)
    print(f"성공: {success}/10")
    print(f"총 시간: {total_time:.2f}초")
    print(f"평균 시간: {total_time/10:.2f}초/매물")
    
    if success > 0:
        print(f"\n예상 전체 처리 시간 (1만개 기준): {(total_time/10)*10000/60:.1f}분")


if __name__ == "__main__":
    test()
