# 🔍 Neo4j 기반 부동산 매물 검색 시스템

> **문서 작성일**: 2025-12-17
> **목적**: Neo4j 그래프 데이터베이스를 활용한 부동산 매물 검색 시스템의 구조와 원리 설명
> **특이사항**: LLM Agent(Tool) 방식을 폐기하고 **100% 규칙 기반(Rule-Based)** 검색 엔진으로 전환하여 속도 최적화

---

## 📊 목차

1. [Neo4j 데이터 구조](#1-neo4j-데이터-구조)
2. [거리 기준 설정](#2-거리-기준-설정)
3. [검색 시스템 아키텍처](#3-검색-시스템-아키텍처)
4. [규칙 기반 검색 엔진 원리](#4-규칙-기반-검색-엔진-원리)
5. [모델 벤치마크 결과](#5-모델-벤치마크-결과)
6. [응답 속도 최적화 및 확장 전략](#6-응답-속도-최적화-및-확장-전략)
7. [관련 파일](#7-관련-파일)

---

## 1. Neo4j 데이터 구조

### 1.1 노드 (Nodes)

| 노드 타입         | 설명              | 주요 속성    |
| ----------------- | ----------------- | ------------ |
| `Property`        | 부동산 매물       | id, lat, lon |
| `SubwayStation`   | 지하철역          | name, line   |
| `Hospital`        | 병원              | name, type   |
| `GeneralHospital` | 종합병원/대학병원 | name         |
| `Pharmacy`        | 약국              | name         |
| `Convenience`     | 편의점            | name, brand  |
| `Park`            | 공원              | name         |
| `College`         | 대학교            | name         |
| `PoliceStation`   | 경찰서            | name         |
| `FireStation`     | 소방서            | name         |
| `CCTV`            | CCTV              | location     |
| `EmergencyBell`   | 비상벨            | location     |

> [!NOTE] > `Property` 노드는 **id와 좌표(lat, lon)만** 저장합니다.
> 주소, 가격 등 상세 정보는 **PostgreSQL**에서 조회합니다.

### 1.2 관계 (Relationships)

```
(Property)-[:NEAR_SUBWAY]->(SubwayStation)
(Property)-[:NEAR_HOSPITAL]->(Hospital)
(Property)-[:NEAR_GENERAL_HOSPITAL]->(GeneralHospital)
(Property)-[:NEAR_PHARMACY]->(Pharmacy)
(Property)-[:NEAR_CONVENIENCE]->(Convenience)
(Property)-[:NEAR_PARK]->(Park)
(Property)-[:NEAR_COLLEGE]->(College)
(Property)-[:NEAR_POLICE]->(PoliceStation)
(Property)-[:NEAR_FIRE]->(FireStation)
(Property)-[:NEAR_CCTV]->(CCTV)
(Property)-[:NEAR_BELL]->(EmergencyBell)
```

### 1.3 관계 속성

| 속성           | 설명      | 단위    |
| -------------- | --------- | ------- |
| `distance`     | 거리      | 미터(m) |
| `walking_time` | 도보 시간 | 분      |

---

## 2. 거리 기준 설정

### 2.1 시설별 검색 거리 기준

| 시설           | 거리 기준   | 설명                                      |
| -------------- | ----------- | ----------------------------------------- |
| **지하철역**   | 1.5km       | 도보 20분 이내                            |
| **버스정류장** | 200m        | 도보 3~5분 이내                           |
| **편의점**     | 200m        | 슬세권, 도보 3~5분 이내                   |
| **종합병원**   | 1km         | 응급차 소음, 장례식장 등 주거 선호도 감소 |
| **병원**       | 300m        | 도보 5분 이내                             |
| **약국**       | 200m        | 도보 3~5분 이내                           |
| **공원**       | 500m        | 산책 가능 거리                            |
| **대학교**     | 2km         | 도보 30분 기준                            |
| **경찰서**     | 1km         | 긴급상황 시 경찰 출동 3~5분 이내          |
| **소방서**     | 2.5km       | 서울 기준 소방차 출동 골든타임 5분        |
| **CCTV**       | 200m (개수) | 동네 안전도 + 심리적 안정감               |
| **비상벨**     | 200m (개수) | 동네 안전도 + 심리적 안정감               |

### 2.2 거리 기준 설계 원칙

1. **도보 접근성**: 일상적으로 자주 이용하는 시설(편의점, 약국)은 5분 이내
2. **응급 상황 대응**: 경찰서, 소방서는 골든타임 기준
3. **소음 영향**: 종합병원은 너무 가까우면 응급차 소음으로 주거 환경 저하

---

## 3. 검색 시스템 아키텍처

### 3.1 전체 검색 흐름 (Pipeline)

```mermaid
graph TD
    A[사용자 질문] --> B[규칙 기반 분석 (Regex)]
    B -->|위치 + 시설 추출| C{검색 타입 결정}

    C -->|Subway| D[지하철역 쿼리]
    C -->|University| E[대학교 쿼리]
    C -->|Multi| F[다중 조건 쿼리]

    D --> G[Neo4j 검색]
    E --> G
    F --> G

    G --> H[매물 ID 목록]
    H --> I[PostgreSQL 상세 정보 조회]
    I --> J[답변 생성 LLM]
    J --> K[사용자 응답]
```

### 3.2 검색 노드별 역할

| 노드             | 파일                   | 역할                                              |
| ---------------- | ---------------------- | ------------------------------------------------- |
| **neo4j_search** | `neo4j_search_node.py` | 정규식으로 질문을 분석하고 Neo4j Cypher 쿼리 실행 |
| **sql_search**   | `sql_search_node.py`   | 검색된 매물 ID로 PostgreSQL에서 상세 정보 조회    |
| **generate**     | `generate_node.py`     | 조회된 정보를 바탕으로 LLM 답변 생성              |

### 3.3 Neo4j Cypher 쿼리 예시 (검색 로직)

```cypher
MATCH (s:SubwayStation)
WHERE s.name CONTAINS '홍대'
WITH s LIMIT 3

MATCH (p:Property)-[r:NEAR_SUBWAY]->(s)
WITH p, s, r, (5000 - toInteger(r.distance)) as score

RETURN p.id as id, score,
       collect({name: s.name, dist: toInteger(r.distance), time: toInteger(r.walking_time)}) as poi_details
ORDER BY score DESC LIMIT 50
```

---

## 4. 규칙 기반 검색 엔진 원리

과거에는 LLM Agent가 Tool을 선택하여 검색했으나, 속도 문제로 인해 **100% 규칙 기반 로직**으로 변경되었습니다.

### 4.1 동작 프로세스 (Rule-Based Workflow)

```
사용자 질문: "홍대입구역 근처 안전한 매물 찾아줘"
    │
    ▼ [Step 1] 질문 분석 (Python Regex)
┌─────────────────────────────────────────────┐
│ - 1. 위치 추출: "홍대입구" (LOCATION_PATTERNS) │
│ - 2. 시설 감지: "안전" → safety (FACILITY_MAP) │
└─────────────────────────────────────────────┘
    │
    ▼ [Step 2] 쿼리 빌더 (Query Builder)
┌─────────────────────────────────────────────┐
│ - search_type 결정: "multi" (Subway + Safety)│
│ - Cypher 쿼리 템플릿 로딩 및 파라미터 바인딩    │
└─────────────────────────────────────────────┘
    │
    ▼ [Step 3] Neo4j 실행
┌─────────────────────────────────────────────┐
│ - graph.query(cypher, params) 실행          │
└─────────────────────────────────────────────┘
    │
    ▼
결과 반환 (소요시간: ~150ms)
```

### 4.2 주요 패턴 및 키워드

- **위치 패턴 (`LOCATION_PATTERNS`)**: "홍대", "강남", "서울대" 등 주요 역/대학/지역명 정규식
- **시설 키워드 (`FACILITY_KEYWORDS`)**:
  - `safety`: 안전, 치안, CCTV, 경찰
  - `convenience`: 편의점, 마트
  - `university`: 대학, 학교
  - `subway`: 역, 지하철

### 4.3 성능 비교 (vs Legacy LLM Agent)

| 구분            | 방식              | 소요 시간     | 장점                | 단점               |
| --------------- | ----------------- | ------------- | ------------------- | ------------------ |
| **규칙 기반**   | Python 정규식     | **~150ms** 🚀 | 매우 빠름, 비용 0원 | 복잡한 자연어 한계 |
| LLM Agent (Old) | Tool Calling (FC) | ~17,000ms 🐢  | 유연한 해석         | 느리고 비쌈        |

---

## 5. 모델 벤치마크 결과

> **Note**: 규칙 기반 검색으로 전환하면서 검색 단계에서 LLM 모델 성능은 더 이상 중요하지 않게 되었으나, 답변 생성 단계(`generate_node`)에서는 여전히 모델 성능이 중요합니다.

### 5.1 복잡한 질문 응답 성능

| 모델            | 평균 응답 시간 | 성공률      |
| --------------- | -------------- | ----------- |
| **gpt-4o-mini** | **17,134ms**   | **100%** 🏆 |
| gpt-5-mini      | 26,985ms       | 67%         |

_검색 시간은 단축되었으나, 최종 답변 생성(generation) 시간은 모델에 따라 차이가 큼._

### 5.2 권장 설정

```python
# generate_node.py
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

---

## 6. 응답 속도 최적화 및 확장 전략

Neo4j 검색 시스템은 속도와 정확성을 모두 확보하기 위해 단계적인 최적화 및 확장 전략을 가지고 있습니다.

### 6.1 현재 최적화 현황 (Phase 1)

- **하이브리드 라우터**: 간단한 위치 검색은 LLM 없이 **규칙 기반(Regex)**으로 즉시 처리 (~150ms)
- **모델 경량화**: `gpt-5-mini` 대신 빠르고 저렴한 `gpt-4o-mini` 채택 (응답 속도 40% 향상)
- **Input 최적화**: LLM에 전달하는 매물 정보(Context)에서 불필요한 필드를 제거하여 토큰 처리 시간 단축

### 6.2 향후 확장 계획 (Phase 2 - Elasticsearch 도입 시)

텍스트 검색(Elasticsearch) 도입으로 데이터가 방대해질 경우를 대비한 구조적 최적화 방안입니다.

1.  **병렬 검색 (Parallel Execution)**

    - **구조**: Neo4j(위치/그래프)와 Elasticsearch(텍스트/키워드) 검색을 `asyncio`로 동시에 실행
    - **효과**: 검색 엔진이 늘어나도 전체 대기 시간(Latency)은 가장 느린 엔진 기준으로 유지됨

2.  **Two-Stage RAG (Re-ranking)**

    - **1단계 Retrieval**: Neo4j + Elastic에서 후보 매물 100개 이상을 빠르게 수집
    - **2단계 Re-ranking**: 가벼운 Cross-Encoder 모델을 사용하여 질문 적합성 점수 산출 후 상위 5~10개만 선별
    - **효과**: LLM Input 비용 절감 및 환각(Hallucination) 최소화, 정밀한 답변 생성

3.  **데이터 전처리 (Preprocessing)**

    - **요약 필드 생성**: 매물의 긴 설명(`description`)을 미리 LLM으로 요약하여 인덱싱
    - **검색 vs 생성 분리**: 검색은 원본 텍스트로, 답변 생성용 Input은 요약된 텍스트로 제공
    - **효과**: 답변 생성 속도(Token Generation) 획기적 단축

4.  **하이브리드 스트리밍**
    - **UI 최적화**: 검색된 매물 카드(UI)를 먼저 화면에 표시하고, LLM 답변 텍스트는 후속 스트리밍으로 전송
    - **효과**: 사용자 체감 대기 시간(Perceived Latency) 제로(0)화

---

## 7. 관련 파일

| 파일                                  | 설명                 |
| ------------------------------------- | -------------------- |
| `apps/rag/nodes/neo4j_search_node.py` | Neo4j 검색 노드      |
| `apps/rag/nodes/sql_search_node.py`   | PostgreSQL 검색 노드 |
| `apps/rag/nodes/generate_node.py`     | 답변 생성 노드       |
