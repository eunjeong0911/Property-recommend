"""
OpenAI API를 사용하여 매물 데이터에 search_text와 style_tags 생성 (병렬 처리 버전)

=============================================================================
# 설정
MODEL = "gpt-5-mini"
CONCURRENT_LIMIT = 100   # 동시 처리 수 (배치당)
SAVE_INTERVAL = 100     # 저장 간격

# 1. scripts/ES전처리 폴더로 이동
cd scripts\ES전처리

# 2. uv로 가상환경 생성
uv venv

# 3. 패키지 설치
uv pip install -r requirements.txt

# 4. 스크립트 실행
.venv\Scripts\python.exe generate_search_text_parallel.py

=============================================================================
"""

import os
import re
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm_asyncio

# .env 로드
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# 설정
MODEL = "gpt-5-mini"
CONCURRENT_LIMIT = 20   # 동시 처리 수 (배치당)
SAVE_INTERVAL = 20     # 저장 간격

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "preprocessing"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "RDB" / "land"

# OpenAI 비동기 클라이언트
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 스타일 태그 후보 (34개)
STYLE_TAGS = [
    "깔끔함", "세련됨", "아늑함", "모던함", "럭셔리함", "탁트인전망", "화이트톤인테리어",
    "실용적임", "풀옵션", "채광좋음", "조용함", "넓은공간", "수납공간많음", "복층구조", "테라스있음",
    "1인가구추천", "신혼부부추천", "직장인추천", "학생추천", "재택근무추천",
    "신축", "가성비좋음", "반려동물가능", "주차가능", "보안좋음", "엘리베이터있음", "분리형원룸",
    "에어컨있음", "세탁기있음", "냉장고있음", "인덕션있음",
    "고층", "저층", "남향"
]

SYSTEM_PROMPT = f"""당신은 부동산 매물 설명을 작성하는 전문가입니다.

주어진 매물 정보를 바탕으로 다음 두 가지를 생성하세요:

1) search_text
- 3~6문장의 자연스러운 한국어 매물 설명
- 핵심 정보(위치, 건물 종류, 층수, 면적, 가격, 옵션 등) 포함
- 객관적이고 읽기 편한 문장
- 상세설명의 중개사 홍보/광고는 무시하고 매물 정보만 활용

2) style_tags
- 다음 중 1~5개 선택: {STYLE_TAGS}
- 매물 정보에 근거하여 적절한 태그만 선택

JSON만 출력: {{"search_text": "설명", "style_tags": ["태그1", "태그2"]}}"""


def extract_listing_info(item: dict) -> str:
    """매물 정보 추출"""
    parts = []
    
    addr = item.get("주소_정보", {}).get("전체주소", "")
    if addr:
        parts.append(f"주소: {addr}")
    
    deal = item.get("거래_정보", {})
    if deal.get("거래방식"):
        parts.append(f"거래방식: {deal['거래방식']}")
    if deal.get("관리비"):
        parts.append(f"관리비: {deal['관리비'].split(chr(10))[0][:50]}")
    
    listing = item.get("매물_정보", {})
    for key in ["건물형태", "전용/공급면적", "해당층/전체층", "방/욕실개수", "방거실형태", "사용승인일"]:
        if listing.get(key) and listing[key] != "-":
            parts.append(f"{key}: {listing[key]}")
    
    if listing.get("생활시설"):
        parts.append(f"생활시설: {listing['생활시설']}")
    if listing.get("보안시설"):
        parts.append(f"보안시설: {listing['보안시설']}")
    
    options = item.get("추가_옵션", [])
    if options:
        parts.append(f"추가옵션: {', '.join(options)}")
    
    detail = item.get("상세_설명", "")
    if detail:
        parts.append(f"상세설명 (중개사 홍보 무시): {detail}")
    
    return "\n".join(parts)


def parse_retry_after(error_message: str) -> float:
    """429 에러 메시지에서 대기 시간 추출"""
    # "Please try again in 72ms" 또는 "Please try again in 1.5s" 패턴 매칭
    match = re.search(r'try again in (\d+(?:\.\d+)?)(ms|s)', error_message)
    if match:
        value = float(match.group(1))
        unit = match.group(2)
        if unit == 'ms':
            return value / 1000  # ms를 초로 변환
        return value
    return 1.0  # 기본값 1초


async def generate_single(item: dict, semaphore: asyncio.Semaphore) -> dict:
    """단일 매물 처리 (비동기)"""
    async with semaphore:
        listing_info = extract_listing_info(item)
        
        for attempt in range(10):  # 재시도 횟수 증가
            try:
                response = await client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": listing_info}
                    ],
                    response_format={"type": "json_object"}
                )
                
                result_text = response.choices[0].message.content
                if result_text:
                    result = json.loads(result_text.strip())
                    result["style_tags"] = [t for t in result.get("style_tags", []) if t in STYLE_TAGS]
                    return result
                    
            except Exception as e:
                error_str = str(e)
                # Rate limit 에러면 응답에서 대기 시간 추출 후 재시도
                if "429" in error_str or "rate_limit" in error_str.lower():
                    wait_time = parse_retry_after(error_str)
                    wait_time = max(wait_time, 0.1)  # 최소 0.1초
                    await asyncio.sleep(wait_time)
                elif attempt < 9:
                    await asyncio.sleep(0.5)
                else:
                    print(f"실패 (매물 {item.get('매물번호', 'N/A')}): {e}")
        
        return {"search_text": "", "style_tags": []}


def save_progress(data: list, output_path: Path):
    """중간 저장"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def process_file(input_path: Path, output_path: Path):
    """파일 처리 (비동기)"""
    print(f"\n처리 중: {input_path.name}")
    
    # 입력 파일 읽기 (data/preprocessing - 최신 크롤링 데이터)
    with open(input_path, "r", encoding="utf-8") as f:
        input_data = json.load(f)
    
    # 기존 출력 파일 읽기 (data/RDB/land - 이전에 처리된 데이터)
    existing_data_by_id = {}
    if output_path.exists():
        print(f"기존 출력 파일 확인 중...")
        with open(output_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            # 매물번호로 인덱싱
            for item in existing_data:
                listing_id = item.get("매물번호")
                if listing_id:
                    existing_data_by_id[listing_id] = item
        print(f"  기존 데이터: {len(existing_data_by_id)}개")
    
    # 입력 데이터를 기반으로 최종 데이터 구성
    final_data = []
    to_process = []  # 새로 처리해야 할 항목 (인덱스, 매물 데이터)
    
    for i, item in enumerate(input_data):
        listing_id = item.get("매물번호")
        if not listing_id:
            final_data.append(item)
            continue
        
        # 기존 데이터에 있는지 확인
        if listing_id in existing_data_by_id:
            existing_item = existing_data_by_id[listing_id]
            
            # 기존 search_text와 style_tags가 있으면 재사용
            if existing_item.get("search_text"):
                # 기존 데이터의 search_text와 style_tags를 현재 데이터에 복사
                item["search_text"] = existing_item.get("search_text", "")
                item["style_tags"] = existing_item.get("style_tags", [])
                final_data.append(item)
            else:
                # search_text가 없으면 새로 생성 필요
                final_data.append(item)
                to_process.append((len(final_data) - 1, item))
        else:
            # 새로운 매물 - 처리 필요
            final_data.append(item)
            to_process.append((len(final_data) - 1, item))
    
    total = len(final_data)
    already_done = total - len(to_process)
    remaining = len(to_process)
    
    print(f"총 {total}개 (완료: {already_done}, 새로 처리 필요: {remaining})")
    
    if not to_process:
        print("모두 처리 완료!")
        # 변경사항이 없어도 최신 입력 데이터로 저장 (매물 정보 업데이트 반영)
        save_progress(final_data, output_path)
        return
    
    semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)
    processed_count = 0
    start_time = asyncio.get_event_loop().time()
    
    # 배치 처리
    for batch_start in range(0, len(to_process), SAVE_INTERVAL):
        batch = to_process[batch_start:batch_start + SAVE_INTERVAL]
        
        tasks = [generate_single(item, semaphore) for _, item in batch]
        results = await tqdm_asyncio.gather(*tasks, desc=f"배치 {batch_start//SAVE_INTERVAL + 1}")
        
        # 결과 반영
        for (idx, item), result in zip(batch, results):
            final_data[idx]["search_text"] = result.get("search_text", "")
            final_data[idx]["style_tags"] = result.get("style_tags", [])
        
        processed_count += len(batch)
        
        # 중간 저장
        save_progress(final_data, output_path)
        
        # 진행 상황 출력
        elapsed = asyncio.get_event_loop().time() - start_time
        speed = processed_count / elapsed if elapsed > 0 else 0
        items_left = len(to_process) - (batch_start + SAVE_INTERVAL)
        eta_minutes = (items_left / speed / 60) if speed > 0 else 0
        
        print(f"[저장] {already_done + processed_count}/{total} 완료 | 경과: {elapsed/60:.1f}분 | 속도: {speed:.1f}개/초 | 남은 시간: 약 {eta_minutes:.1f}분")
    
    print(f"완료: {output_path}")


async def main():
    print("=" * 60)
    print("매물 search_text & style_tags 생성 (병렬 처리)")
    print(f"모델: {MODEL}")
    print(f"동시 처리: {CONCURRENT_LIMIT}개")
    print("429 에러 시 자동 대기 후 재시도")
    print("=" * 60)
    
    json_files = [f for f in DATA_DIR.glob("*.json") if f.name != "crawled_ids.txt"]
    print(f"\n파일: {len(json_files)}개")
    
    for json_file in json_files:
        output_path = OUTPUT_DIR / json_file.name
        await process_file(json_file, output_path)
    
    print("\n" + "=" * 60)
    print("모든 파일 처리 완료!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
