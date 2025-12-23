# Neo4j Integrated Documentation

이 문서는 Neo4j 그래프 데이터베이스 기반의 **①데이터 적재(Import) 시스템**과 **②검색 엔진(Search) 아키텍처**에 대한 통합 가이드입니다.

---

# Part 1. 데이터 임포트 가이드 (Data Import System)

서울시의 교통, 편의시설, 안전시설, 관공서 및 부동산 매물 데이터를 수집, 가공하여 Neo4j에 노드(Node)와 관계(Relationship)로 저장하는 방법에 대한 상세 가이드입니다.

## 1. 개요

이 시스템은 서울시의 다양한 도시 데이터를 수집하여 Neo4j에 그래프 형태로 구축합니다. 모든 스크립트는 모듈화되어 있으며, `scripts/data_import` 폴더 내에 위치합니다.

## 2. 🚀 한 번에 실행하는 법 (Docker 권장)

Docker를 사용하면 복잡한 환경 설정 없이 **크롤링부터 DB 적재까지** 한 번에 실행할 수 있습니다.

### 2.1 이미지 빌드 (Build)

최초 실행이거나 코드를 수정한 경우, 이미지를 빌드해야 합니다.

```bash
docker-compose --profile crawling build crawling
```

### 2.2 파이프라인 실행 (Run)

아래 명령어를 입력하면 **통합 파이프라인(크롤링 → 지오코딩 → Import)**이 자동으로 시작됩니다.

```bash
docker-compose --profile crawling up crawling
```

> **Tip**: 백그라운드에서 실행하려면 뒤에 `-d` 옵션을 붙이세요. (`up -d crawling`)

---

## 3. 폴더 구조 및 파일 설명

```text
scripts/dataCrawling/    # [수집] 매물 크롤링 스크립트 원본
scripts/data_import/
├── run_neo4j_full_import.py   # [실행] 전체 데이터 임포트 파이프라인 진입점 (Docker 실행 파일)
├── config.py                  # [설정] 환경 변수 및 경로
├── database.py                # [공통] Neo4j 접속 관리
├── geocoder.py                # [공통] 주소 -> 좌표 변환
└── importers/
    ├── import_properties_full.py # [파이프라인] 매물 크롤링~Import 중간 관리자
    ├── property_importer.py      # [로직] 매물 DB 적재
    ├── transport_importer.py     # [로직] 지하철/버스
    ├── amenity_importer.py       # [로직] 편의시설(병원/학교/상가)
    └── safety_importer.py        # [로직] 안전시설(CCTV/경찰/소방)
```

### 3.1 주요 스크립트 역할 구분

혼동하기 쉬운 스크립트들의 역할을 명확히 구분합니다.

| 파일명                          | 역할 (Role)               | 설명                                                                                          |
| :------------------------------ | :------------------------ | :-------------------------------------------------------------------------------------------- |
| **`run_neo4j_full_import.py`**  | **[메인] 전체 통합 실행** | 시설 데이터 + 매물 파이프라인을 모두 총괄합니다. **Docker가 내부적으로 실행하는 파일**입니다. |
| **`import_properties_full.py`** | **매물 갱신 파이프라인**  | 매물 크롤링 ➔ 지오코딩 ➔ Import를 순차적으로 수행합니다. 매물 데이터만 갱신할 때 유용합니다.  |
| `property_importer.py`          | 매물 DB 적재 (단순)       | 크롤링 기능 없이, **준비된 JSON 파일**만 DB에 넣습니다.                                       |

---

## 4. 모듈별 상세 기능 설명

### 4.1 Transport Importer (`transport_importer.py`)

- **대상**: 지하철역, 버스정류장
- **기능**: 서울시 내 역/정류장 저장 및 매물과의 거리 계산 연결.
- **연결 기준**:
  - 지하철: **1km** 이내 (`NEAR_SUBWAY`)
  - 버스: **200m** 이내 (`NEAR_BUS`)

### 4.2 Amenity Importer (`amenity_importer.py`)

- **대상**: 병원, 약국, 대학교, 상가, 공원
- **기능**:
  - **병원**: 종합병원(1km), 일반병원(500m) 연결.
  - **약국/편의점**: 200m 이내 연결 (`NEAR_PHARMACY`, `NEAR_CONVENIENCE`).
  - **공원**: 500m 이내 연결 (`NEAR_PARK`).
  - **대학교**: 1km 이내 연결 (`NEAR_COLLEGE`).

### 4.3 Safety Importer (`safety_importer.py`)

- **대상**: CCTV, 비상벨, 경찰서, 소방서
- **기능**:
  - **CCTV/비상벨**: 100m 이내 연결 (`NEAR_CCTV`).
  - **관공서**: 경찰서(1km), 소방서(2.5km) 연결.

### 4.4 Property Importer (`property_importer.py`)

- **대상**: 지오코딩 완료된 매물 좌표 파일 (`data/GraphDB_data/land/*.json`)
- **기능**:
  - 매물 ID와 좌표를 읽어 `Property` 노드 생성.
  - **자동 삭제**: DB에는 있으나, 최신 크롤링 파일에 없는 매물(판매 완료)을 감지하여 삭제.

---

## 5. 환경 설정 (`config.py` & `.env`)

실행 전 프로젝트 루트의 `.env` 파일 설정이 필수입니다.

```ini
# Neo4j 접속 정보
NEO4J_URI=bolt://host.docker.internal:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=****

# Kakao API Key (지오코딩용)
KAKAO_API_KEY=****

# Headless 설정 (Docker 사용 시 자동 설정됨)
# HEADLESS_MODE=true
```

## 6. [부록] 로컬 직접 실행하기

Docker 없이 로컬에서 Python으로 직접 실행하려면 아래 명령어를 사용하세요.

```bash
python scripts/data_import/run_neo4j_full_import.py
```

<br>

---

# Part 2. Neo4j 검색 아키텍처 (Search Architecture)

> **문서 작성일**: 2025-12-17
> **목제**: Neo4j 그래프 데이터베이스를 활용한 부동산 매물 검색 시스템의 구조와 원리 설명
> **특이사항**: LLM Agent(Tool) 방식을 폐기하고 **100% 규칙 기반(Rule-Based)** 검색 엔진으로 전환하여 속도 최적화

## 1. Neo4j 데이터 구조

### 1.1 노드 (Nodes)

| 노드 타입         | 설명        | 주요 속성    |
| :---------------- | :---------- | :----------- |
| `Property`        | 부동산 매물 | id, lat, lon |
| `SubwayStation`   | 지하철역    | name, line   |
| `Hospital`        | 병원        | name, type   |
| `GeneralHospital` | 종합병원    | name         |
| `Pharmacy`        | 약국        | name         |
| `Convenience`     | 편의점      | name, brand  |
| `Park`            | 공원        | name         |
| `College`         | 대학교      | name         |
| `PoliceStation`   | 경찰서      | name         |
| `FireStation`     | 소방서      | name         |
| `CCTV`            | CCTV        | location     |
| `EmergencyBell`   | 비상벨      | location     |

> **Note**: `Property` 노드는 **id와 좌표(lat, lon)만** 저장합니다. 상세 정보는 PostgreSQL에서 조회합니다.

### 1.2 관계 (Relationships)

```
(Property)-[:NEAR_SUBWAY]->(SubwayStation)
(Property)-[:NEAR_HOSPITAL]->(Hospital)
... (각 시설별 NEAR_* 관계 존재)
```

- **관계 속성**: `distance` (거리 m), `walking_time` (도보 분)

## 2. 거리 기준 설정

### 2.1 시설별 검색 거리 기준

| 시설            | 거리 기준 | 설명                   |
| :-------------- | :-------- | :--------------------- |
| **지하철역**    | 1.5km     | 도보 20분 이내         |
| **버스정류장**  | 200m      | 도보 3~5분 이내        |
| **편의점/약국** | 200m      | 슬세권, 도보 3~5분     |
| **종합병원**    | 1km       | 소음 등 주거 영향 고려 |
| **병원**        | 300m      | 도보 5분 이내          |
| **공원**        | 500m      | 산책 가능 거리         |
| **대학교**      | 2km       | 도보 30분 기준         |
| **경찰서**      | 1km       | 긴급 출동 3~5분        |
| **소방서**      | 2.5km     | 골든타임 5분           |
| **CCTV/비상벨** | 200m      | 심리적 안정감          |

### 2.2 거리 기준 설계 원칙

1. **도보 접근성**: 자주 가는 곳(편의점)은 가깝게.
2. **응급 상황**: 경찰/소방서는 골든타임 기준.
3. **환경 요인**: 종합병원은 소음 고려하여 적절한 거리 유지.

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

| 노드             | 파일                   | 역할                                  |
| :--------------- | :--------------------- | :------------------------------------ |
| **neo4j_search** | `neo4j_search_node.py` | 질문 분석(Regex) 및 Cypher 쿼리 실행  |
| **sql_search**   | `sql_search_node.py`   | 매물 ID로 상세 정보 조회 (PostgreSQL) |
| **generate**     | `generate_node.py`     | LLM 답변 생성                         |

### 3.3 Neo4j Cypher 쿼리 예시

```cypher
MATCH (s:SubwayStation) WHERE s.name CONTAINS '홍대'
WITH s LIMIT 3
MATCH (p:Property)-[r:NEAR_SUBWAY]->(s)
WITH p, s, r, (5000 - toInteger(r.distance)) as score
RETURN p.id as id, score, collect({name: s.name, dist: r.distance}) as poi_details
ORDER BY score DESC LIMIT 50
```

## 4. 규칙 기반 검색 엔진 원리

### 4.1 동작 프로세스 (Rule-Based Workflow)

1. **질문 분석**: Python Regex로 위치("홍대")와 시설("안전") 키워드 추출.
2. **쿼리 빌더**: 추출된 키워드에 맞는 `search_type` 결정 및 Cypher 생성.
3. **실행**: 약 150ms 내외로 결과 반환.

### 4.2 성능 비교

| 방식                    | 소요 시간  | 특징                                   |
| :---------------------- | :--------- | :------------------------------------- |
| **규칙 기반 (Current)** | **~150ms** | Python Regex 사용. 매우 빠르고 정확함. |
| LLM Agent (Legacy)      | ~17,000ms  | Tool Calling 방식. 느려서 폐기됨.      |

## 5. 모델 벤치마크 결과

검색 단계는 규칙 기반으로 변경되었으나, 최종 답변 생성(`generate_node`) 단계에서는 모델 성능이 중요합니다.

| 모델            | 평균 응답 시간 | 성공률   |
| :-------------- | :------------- | :------- |
| **gpt-4o-mini** | **17,134ms**   | **100%** |
| gpt-5-mini      | 26,985ms       | 67%      |

> **권장 설정**: `gpt-4o-mini` (temperature=0)

## 6. 응답 속도 최적화 및 확장 전략

### 6.1 최적화 적용 현황 (Phase 1 - 완료)

1. **Pure Rule-Based Search**: LLM을 배제하고 정규식으로 전환하여 검색 속도 99% 단축.
2. **Extreme Input Diet**: LLM에게 전달하는 매물 정보에서 불필요한 텍스트를 제거하고 핵심 데이터만 압축하여 토큰 60% 절감.
3. **Parallel Batch Generation**: 여러 매물의 답변 생성을 병렬(Parallel)로 처리하여 속도 3배 향상 (분신술 전략).

### 6.2 향후 확장 계획 (Phase 2)

1. **병렬 검색**: Neo4j(위치)와 Elasticsearch(텍스트) 동시 실행.
2. **Two-Stage RAG**: 후보군 100개 조회 후 Cross-Encoder로 Re-ranking.
3. **데이터 전처리**: 긴 설명 텍스트를 미리 요약(Summary)하여 인덱싱.
4. **하이브리드 스트리밍**: 매물 카드 UI 먼저 표시 후 텍스트 스트리밍.

## 7. 관련 파일

| 파일                                  | 설명                 |
| :------------------------------------ | :------------------- |
| `apps/rag/nodes/neo4j_search_node.py` | Neo4j 검색 노드      |
| `apps/rag/nodes/sql_search_node.py`   | PostgreSQL 검색 노드 |
| `apps/rag/nodes/generate_node.py`     | 답변 생성 노드       |
