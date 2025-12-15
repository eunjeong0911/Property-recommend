# Elasticsearch 검색 기능 테스트 가이드

이 문서는 Elasticsearch 기반 검색 기능(벡터 검색, 키워드 검색, 하이브리드 검색)을 테스트하고 비교 분석하는 방법을 설명합니다.

## 테스트 스크립트 위치

```
scripts/ES답변테스트/
├── test_vector_search.py   # 검색 테스트 (벡터/키워드/하이브리드)
├── build_embeddings.py     # 임베딩 생성 스크립트
├── es_bulk_index.py        # ES 벌크 인덱싱
└── test_es_search.py       # ES 검색 테스트
```

## 사전 준비

### 1. 가상환경 활성화
```cmd
cd apps\backend
```

### 2. 임베딩 상태 확인
```cmd
python ..\..\scripts\ES답변테스트\test_vector_search.py --stats
```

출력 예시:
```
📊 임베딩 통계
📌 인덱스: realestate_listings
📦 전체 매물: 9,914건
✅ 임베딩 완료: 9,914건
⏳ 미완료: 0건
📈 완료율: 100.0%
```

### 3. 임베딩 생성 (미완료 시)
```cmd
python ..\..\scripts\ES답변테스트\build_embeddings.py
```

## 검색 모드 비교

| 모드 | 설명 | 장점 | 단점 |
|------|------|------|------|
| vector | 의미적 유사도 기반 | 추상적 표현 이해 | 정확한 키워드 매칭 약함 |
| keyword | 텍스트 매칭 기반 | 정확한 키워드 검색 | 동의어/추상적 표현 못 찾음 |
| hybrid | 벡터 60% + 키워드 40% | 두 장점 결합 | 약간의 오버헤드 |

## 테스트 방법

### 단일 검색 테스트

```cmd
# 벡터 검색 (기본)
python ..\..\scripts\ES답변테스트\test_vector_search.py "햇살 좋은 집" --top-k 3 --full

# 키워드 검색
python ..\..\scripts\ES답변테스트\test_vector_search.py "역삼동 원룸" -m keyword --top-k 3 --full

# 하이브리드 검색
python ..\..\scripts\ES답변테스트\test_vector_search.py "조용한 동네" -m hybrid --top-k 3 --full
```

### 대화형 모드

```cmd
python ..\..\scripts\ES답변테스트\test_vector_search.py -i -m hybrid --full --top-k 3
```

대화형 명령어:
- `/mode` - 검색 모드 순환 (vector → keyword → hybrid)
- `/mode hybrid` - 특정 모드로 변경
- `/full` - 청크 전문 보기 토글
- `/top 5` - 결과 개수 변경
- `/score 0.5` - 최소 유사도 점수 변경
- `quit` - 종료

## 비교 분석 테스트 시나리오

### 시나리오 1: 추상적 표현 (벡터 검색 우위)
```
쾌적하고 상큼한 원룸
햇살이 잘 드는 따뜻한 집
조용히 공부할 수 있는 곳
혼자 살기 좋은 아늑한 공간
```

예상: 벡터 검색이 "깔끔함", "채광좋음", "화이트톤" 등의 태그와 매칭

### 시나리오 2: 정확한 키워드 (키워드 검색 우위)
```
역삼동 원룸
강남구 오피스텔
신림동 월세 50만원
```

예상: 키워드 검색이 정확한 지역명/가격 매칭

### 시나리오 3: 복합 조건 (하이브리드 검색 우위)
```
강남역 근처 깨끗한 신축
역삼동에서 조용한 원룸
신림동 저렴하고 넓은 집
```

예상: 하이브리드가 키워드(지역) + 의미(깨끗한, 조용한) 모두 반영

## 결과 해석

### 유사도 점수
- 0.8 이상: 매우 높은 유사도
- 0.7 ~ 0.8: 높은 유사도
- 0.5 ~ 0.7: 중간 유사도
- 0.5 미만: 낮은 유사도 (기본 필터링됨)

### 검색 결과 필드
- 유사도 점수: ES에서 계산한 relevance score
- 매물번호: land_num (고유 식별자)
- 태그: style_tags (매물 특성)
- 청크 전문: search_text (임베딩된 텍스트)

## 문제 해결

### ES 연결 실패
```
❌ ES 연결 실패: Elasticsearch에 연결할 수 없습니다.
```
→ Docker에서 ES 컨테이너 실행 확인: `docker ps | grep elasticsearch`

### 임베딩 없음
```
❌ 검색 결과가 없습니다.
```
→ `--stats`로 임베딩 상태 확인 후 `build_embeddings.py` 실행

### OpenAI API 오류
```
❌ 오류: The api_key client option must be set
```
→ `.env` 파일에 `OPENAI_API_KEY` 설정 확인
