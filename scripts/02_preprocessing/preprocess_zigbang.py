"""
직방 크롤링 데이터를 피터팬 형식으로 변환 + search_text/style_tags 생성
4개 모델 독립 병렬 처리 버전

=============================================================================
사용법:
    python preprocess_zigbang.py
=============================================================================
"""

import os
import re
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
import threading
from collections import deque

# .env 로드
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# 설정
MODELS = ["gpt-5-mini", "gpt-4.1-nano", "gpt-4.1-mini"]
CONCURRENT_PER_MODEL = 100  # 모델당 동시 처리
SAVE_INTERVAL = 100  # 저장 간격

DATA_DIR = Path(__file__).parent.parent / "01_crawling" / "zigbang" / "data"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "RDB" / "zigbangland"

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


def transform_zigbang_to_peterpan(item: dict) -> dict:
    """직방 데이터를 피터팬 형식으로 변환"""
    deal_info = item.get("거래_정보", {})
    deal_type = deal_info.get("거래유형", "")
    
    if deal_type == "월세":
        deposit = deal_info.get("보증금", 0)
        monthly = deal_info.get("월세", 0)
        deposit_str = f"{deposit:,}만원" if deposit else "-"
        monthly_str = f"{monthly:,}만원" if monthly else "-"
    elif deal_type == "전세":
        deposit = deal_info.get("전세금", 0)
        deposit_str = f"{deposit:,}만원" if deposit else "-"
        monthly_str = "-"
    else:
        deposit_str = "-"
        monthly_str = "-"
    
    manage_fee = deal_info.get("관리비", 0)
    manage_str = f"{manage_fee}만원" if manage_fee else "-"
    
    listing = item.get("매물_정보", {})
    area_m2 = listing.get("전용면적_m2", 0)
    area_pyeong = listing.get("전용면적_평", 0)
    floor = listing.get("해당층", "")
    total_floor = listing.get("총층", "")
    
    room_type = listing.get("방타입", "")
    if "투룸" in room_type or "쓰리룸" in room_type:
        room_count = "2개" if "투룸" in room_type else "3개"
    else:
        room_count = "1개"
    
    options = item.get("추가_옵션", [])
    life_facilities = ", ".join(options) if options else "-"
    
    has_elevator = listing.get("엘리베이터", False)
    parking = listing.get("주차", "")
    
    extra_options = []
    if has_elevator:
        extra_options.append("엘리베이터")
    if parking and "가능" in parking:
        extra_options.append("주차가능")
    if "풀옵션" in str(options) or len(options) >= 5:
        extra_options.append("풀옵션")
    
    return {
        "중개사_정보": item.get("중개사_정보", {}),
        "매물번호": item.get("매물번호", ""),
        "매물_URL": item.get("매물_URL", ""),
        "매물_이미지": item.get("매물_이미지", []),
        "주소_정보": {"전체주소": item.get("주소_정보", {}).get("전체주소", "")},
        "평면도_URL": [],
        "거래_정보": {
            "관리비": manage_str, "융자금": "-",
            "입주가능일": deal_info.get("입주가능일", "-"),
            "거래유형": deal_type, "매매가": "-",
            "보증금": deposit_str,
            "월세": monthly_str if deal_type == "월세" else "-"
        },
        "매물_정보": {
            "전입신고 여부": "-", "건축물용도": "공동주택",
            "건물형태": listing.get("건물유형", "원룸"), "건물명": "-",
            "전용/공급면적": f"{area_m2}m2/{area_m2}m2 ({area_pyeong}평/{area_pyeong}평)",
            "해당층/전체층": f"{floor}층/{total_floor}층" if floor and total_floor else "-",
            "방/욕실개수": f"{room_count}/1개",
            "방거실형태": "분리형" if "분리" in room_type else "오픈형",
            "주실기준/방향": f"안방/{listing.get('방향', '-')}향" if listing.get('방향') else "-",
            "현관유형": "-", "총세대수": "-", "총주차대수": "-",
            "주차": "가능" if parking and "가능" in parking else "불가",
            "위반건축물 여부": "-", "사용승인일": "-", "난방방식": "-",
            "냉방시설": "에어컨" if "에어컨" in options else "-",
            "생활시설": life_facilities, "보안시설": "-", "기타시설": "-"
        },
        "추가_옵션": extra_options if extra_options else options[:3],
        "주변_학교": [],
        "상세_설명": item.get("상세_설명", ""),
        "좌표_정보": {
            "위도": item.get("위치", {}).get("위도"),
            "경도": item.get("위치", {}).get("경도")
        },
        "search_text": "",
        "style_tags": []
    }


def extract_listing_info(item: dict) -> str:
    """매물 정보 추출 (GPT 프롬프트용)"""
    parts = []
    addr = item.get("주소_정보", {}).get("전체주소", "")
    if addr:
        parts.append(f"주소: {addr}")
    
    deal = item.get("거래_정보", {})
    if deal.get("거래유형"):
        parts.append(f"거래유형: {deal['거래유형']}")
    if deal.get("보증금") and deal["보증금"] != "-":
        parts.append(f"보증금: {deal['보증금']}")
    if deal.get("월세") and deal["월세"] != "-":
        parts.append(f"월세: {deal['월세']}")
    if deal.get("관리비") and deal["관리비"] != "-":
        parts.append(f"관리비: {deal['관리비']}")
    
    listing = item.get("매물_정보", {})
    for key in ["건물형태", "전용/공급면적", "해당층/전체층", "방/욕실개수", "방거실형태"]:
        if listing.get(key) and listing[key] != "-":
            parts.append(f"{key}: {listing[key]}")
    
    if listing.get("생활시설") and listing["생활시설"] != "-":
        parts.append(f"생활시설: {listing['생활시설']}")
    
    options = item.get("추가_옵션", [])
    if options:
        parts.append(f"추가옵션: {', '.join(options)}")
    
    detail = item.get("상세_설명", "")
    if detail:
        parts.append(f"상세설명: {detail[:500]}")
    
    return "\n".join(parts)


def parse_retry_after(error_message: str) -> float:
    match = re.search(r'try again in (\d+(?:\.\d+)?)(ms|s)', error_message)
    if match:
        value = float(match.group(1))
        unit = match.group(2)
        if unit == 'ms':
            return value / 1000
        return value
    return 1.0


# 모델별 진행 상황 추적
model_stats = {}
model_totals = {}
stats_lock = threading.Lock()


def update_stats(model: str, success: bool = True):
    with stats_lock:
        if model not in model_stats:
            model_stats[model] = {"completed": 0, "failed": 0}
        if success:
            model_stats[model]["completed"] += 1
        else:
            model_stats[model]["failed"] += 1


def print_progress_bars():
    """4개 모델 각각 프로그레스 바 표시"""
    with stats_lock:
        lines = []
        for model in MODELS:
            total = model_totals.get(model, 0)
            if total == 0:
                continue
            completed = model_stats.get(model, {}).get("completed", 0)
            percent = (completed / total) * 100 if total > 0 else 0
            bar_len = 20
            filled = int(bar_len * completed / total) if total > 0 else 0
            bar = "█" * filled + "░" * (bar_len - filled)
            short_name = model.replace("gpt-", "").replace("-mini", "m").replace("-nano", "n")
            lines.append(f"{short_name:8} [{bar}] {completed:4}/{total} ({percent:5.1f}%)")
        
        # 커서 위로 이동해서 덮어쓰기
        if lines:
            print(f"\033[{len(lines)}A", end="")  # 커서 위로
            for line in lines:
                print(f"\r{line}          ")  # 줄 덮어쓰기


async def generate_single(item: dict, idx: int, model: str, semaphore: asyncio.Semaphore, data: list, save_lock: asyncio.Lock, output_path: Path, batch_counter: dict):
    """단일 매물 처리"""
    async with semaphore:
        listing_info = extract_listing_info(item)
        
        for attempt in range(10):
            try:
                response = await client.chat.completions.create(
                    model=model,
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
                    
                    # 결과 저장
                    async with save_lock:
                        data[idx]["search_text"] = result.get("search_text", "")
                        data[idx]["style_tags"] = result.get("style_tags", [])
                        batch_counter["count"] += 1
                        
                        # 100개마다 저장
                        if batch_counter["count"] % SAVE_INTERVAL == 0:
                            output_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(output_path, "w", encoding="utf-8") as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    update_stats(model, True)
                    print_progress_bars()
                    return
                    
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "rate_limit" in error_str.lower():
                    wait_time = parse_retry_after(error_str)
                    wait_time = max(wait_time, 0.1)
                    await asyncio.sleep(wait_time)
                elif attempt < 9:
                    await asyncio.sleep(0.5)
                else:
                    update_stats(model, False)
                    return


async def process_file(input_path: Path, output_path: Path):
    """파일 처리 - 4개 모델 독립 병렬"""
    global model_stats, model_totals
    model_stats = {}
    model_totals = {}
    
    print(f"\n{'='*60}")
    print(f"처리 중: {input_path.name}")
    print(f"{'='*60}")
    
    # 데이터 로드
    if output_path.exists():
        print(f"📂 기존 파일에서 이어서 처리")
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        print(f"📥 원본 파일 로드 및 형식 변환 중...")
        with open(input_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        data = [transform_zigbang_to_peterpan(item) for item in raw_data]
        print(f"✅ {len(data)}개 매물 형식 변환 완료")
    
    # 처리할 항목 필터링
    to_process = [(i, item) for i, item in enumerate(data) if not item.get("search_text")]
    
    total = len(data)
    already_done = total - len(to_process)
    remaining = len(to_process)
    
    print(f"📊 총 {total}개 (완료: {already_done}, 남음: {remaining})")
    
    if not to_process:
        print("✅ 모두 처리 완료!")
        return
    
    # 모델별 할당량 계산
    for i, (idx, item) in enumerate(to_process):
        model = MODELS[i % len(MODELS)]
        model_totals[model] = model_totals.get(model, 0) + 1
    
    # 모델별 세마포어
    semaphores = {model: asyncio.Semaphore(CONCURRENT_PER_MODEL) for model in MODELS}
    save_lock = asyncio.Lock()
    batch_counter = {"count": already_done}
    
    print(f"\n🚀 4개 모델 동시 처리 시작 (각 {CONCURRENT_PER_MODEL}개 병렬)")
    print("-" * 60)
    
    # 프로그레스 바 초기 출력 (4줄)
    for model in MODELS:
        total_m = model_totals.get(model, 0)
        short_name = model.replace("gpt-", "").replace("-mini", "m").replace("-nano", "n")
        bar = "░" * 20
        print(f"{short_name:8} [{bar}]    0/{total_m} (  0.0%)")
    
    # 모든 태스크 생성 (라운드로빈으로 모델 할당)
    tasks = []
    for i, (idx, item) in enumerate(to_process):
        model = MODELS[i % len(MODELS)]
        task = generate_single(item, idx, model, semaphores[model], data, save_lock, output_path, batch_counter)
        tasks.append(task)
    
    # 모든 태스크 동시 실행
    await asyncio.gather(*tasks)
    
    # 최종 저장
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print("🎉 완료!")
    print(f"📁 저장: {output_path}")
    for model in MODELS:
        if model in model_stats:
            s = model_stats[model]
            print(f"   {model}: 성공 {s['completed']}, 실패 {s['failed']}")
    print("=" * 60)


async def main():
    print("=" * 60)
    print("직방 데이터 전처리 (4개 모델 독립 병렬)")
    print(f"모델: {MODELS}")
    print(f"모델당 동시: {CONCURRENT_PER_MODEL}개 (총 {CONCURRENT_PER_MODEL * len(MODELS)}개)")
    print(f"저장 간격: {SAVE_INTERVAL}개")
    print("=" * 60)
    
    files = [
        ("zigbang_seoul_wolse.json", "zigbang_seoul_wolse_processed.json"),
        ("zigbang_seoul_jeonse.json", "zigbang_seoul_jeonse_processed.json"),
    ]
    
    for input_name, output_name in files:
        input_path = DATA_DIR / input_name
        output_path = OUTPUT_DIR / output_name
        
        if input_path.exists():
            await process_file(input_path, output_path)
        else:
            print(f"⚠️ 파일 없음: {input_path}")
    
    print("\n🎉 모든 파일 처리 완료!")


if __name__ == "__main__":
    asyncio.run(main())
