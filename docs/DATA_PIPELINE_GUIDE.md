# SKN18-FINAL-1TEAM 데이터 파이프라인 가이드

본 문서는 데이터 수집(크롤링), 가공, 적재를 수행하는 3가지 주요 파이프라인 스크립트의 역할과 Docker 환경에서의 실행 방법을 설명합니다.

---

## 🏗️ 개요: 3가지 실행 모드

프로젝트는 목적에 따라 세분화된 3가지 실행 모드를 제공합니다.

| 모드                     | 스크립트 파일                                            | 역할                                                      | 주요 용도                           |
| :----------------------- | :------------------------------------------------------- | :-------------------------------------------------------- | :---------------------------------- |
| **1. 크롤링 (수집)**     | `scripts/dataCrawling/피터팬 매물 데이터/crawl_seoul.py` | 웹사이트에서 최신 매물 데이터 수집 (Raw Json 저장)        | DB 갱신 없이 데이터만 수집할 때     |
| **2. 데이터 적재 (ETL)** | `scripts/data_import/run_neo4j_full_import.py`           | 수집된 데이터를 가공하여 Neo4j/Postgres/OpenSearch에 적재 | 로직 수정 후 DB 재적재, 개발 테스트 |
| **3. 전체 실행 (Full)**  | `scripts/data_import/run_all_process.py`                 | **1번 + 2번** 순차 실행 (수집 → 적재 원큐 완료)           | 정기 배치, 시스템 초기화            |

---

## 🐳 Docker 환경 실행 방법

모든 스크립트는 `crawling` 서비스 컨테이너를 통해 실행하는 것을 권장합니다.

### 1. 🕷️ 크롤링만 실행 (Data Collection Only)

매물 데이터를 새로 수집하지만 DB에는 반영하지 않습니다. `data/Crawling` 폴더에 JSON 파일이 생성됩니다.

```bash
# Windows (PowerShell)
docker-compose run --rm crawling python "scripts/dataCrawling/피터팬 매물 데이터/crawl_seoul.py"

# Mac/Linux
docker-compose run --rm crawling python "scripts/dataCrawling/피터팬 매물 데이터/crawl_seoul.py"
```

### 2. 💾 데이터 적재만 실행 (ETL & Import Only)

이미 수집된(로컬에 저장된) JSON 데이터를 사용하여 지오코딩, 전처리, 임베딩 후 모든 DB에 적재합니다. API 호출 비용(Kakao, OpenAI)은 필요한 경우에만 발생하며, 중복 데이터는 자동으로 건너뜁니다.

**수행 작업:**

1.  **Geocoding**: 주소 → 좌표 변환 (`data/GraphDB_data` 생성)
2.  **Preprocessing**: LLM 활용 설명/태그 생성 (`data/RDB` 생성)
3.  **Transport/Amenity**: 인프라 데이터 적재
4.  **Reference DB**: PostgreSQL (상세), Neo4j (공간), OpenSearch (검색) 적재
5.  **Embedding**: 벡터 생성 및 인덱싱
6.  **Linking**: 데이터 간 관계 연결

```bash
docker-compose run --rm crawling python scripts/data_import/run_neo4j_full_import.py
```

### 3. 🚀 전체 파이프라인 실행 (Full Process)

데이터 수집부터 시작하여 가공, 적재까지 모든 과정을 한 번에 수행합니다. 가장 시간이 오래 걸립니다.

```bash
docker-compose run --rm crawling python scripts/data_import/run_all_process.py
```

---

## 💡 참고 사항

- **환경 변수 (`.env`)**: 실행 전 프로젝트 루트의 `.env` 파일에 다음 항목들이 설정되어 있어야 합니다.
  - `POSTGRES_*`, `NEO4J_*`, `OPENSEARCH_*` (DB 연결 정보)
  - `KAKAO_API_KEY` (지오코딩용)
  - `OPENAI_API_KEY` (전처리 및 임베딩용)
- **중복 방지**: 모든 적재 프로세스는 **Idempotent(멱등성)**하게 설계되어 있어, 여러 번 실행해도 데이터가 중복되거나 꼬이지 않습니다. (변경된 부분만 업데이트됨)
- **프로파일**: `docker-compose.yml`에 `scripts`와 `crawling` 프로파일이 정의되어 있으므로, 서비스 실행 시 `--profile` 옵션이 필요할 수 있습니다. (예: `docker-compose --profile crawling run ...`)
