# Neo4j 스크립트 실행 가이드

이 문서는 Neo4j 데이터 적재 스크립트들의 **용도**와 **환경별(Docker/Local) 실행 방법**을 안내합니다.

---

## 1. `run_neo4j_full_import.py` (전체 자동화)

**[용도]** 교통/시설 데이터 적재 + **매물 크롤링** + **지오코딩** + **DB 적재**를 모두 수행합니다. **가장 추천하는 실행 방법**입니다.

### 🐳 Docker 실행 (권장)

환경 설정 없이 바로 실행 가능합니다.

```bash
# 전체 파이프라인 자동 실행 (백그라운드 실행 시 -d 추가)
docker-compose --profile crawling up crawling
```

### 💻 Local 실행

Python 및 Chrome 브라우저가 설치되어 있어야 합니다.

```bash
python scripts/data_import/run_neo4j_full_import.py
```

---

## 2. `import_neo4j_only.py` (기존 파일 적재)

**[용도]** **크롤링을 하지 않고**, 이미 가지고 있는 데이터 파일(`data/`)을 사용하여 Neo4j DB를 재구축합니다. 빠릅니다.

### 🐳 Docker 실행

```bash
# crawling 컨테이너 내부에서 스크립트 실행
docker-compose --profile crawling run --rm crawling python scripts/data_import/import_neo4j_only.py
```

### 💻 Local 실행

```bash
python scripts/data_import/import_neo4j_only.py
```

---

## 3. `importers/import_properties_full.py` (매물만 갱신)

**[용도]** 지하철/병원 등 시설 데이터는 건드리 건너뛰고, **부동산 매물 데이터만** 크롤링해서 새로고침합니다.

### 🐳 Docker 실행

```bash
docker-compose --profile crawling run --rm crawling python scripts/data_import/importers/import_properties_full.py
```

### 💻 Local 실행

```bash
python scripts/data_import/importers/import_properties_full.py
```

---

## 4. `importers/property_importer.py` (매물 단순 적재)

**[용도]** 크롤링도 안 하고, 지오코딩도 안 합니다. 그냥 **이미 준비된 매물 JSON 파일**을 DB에 넣기만 합니다. (테스트용)

### 🐳 Docker 실행

```bash
docker-compose --profile crawling run --rm crawling python scripts/data_import/importers/property_importer.py
```

### 💻 Local 실행

```bash
python scripts/data_import/importers/property_importer.py
```

---

## ⚙️ 필수 설정 확인 (`.env`)

오류 없는 실행을 위해 `.env` 파일에 아래 내용이 있는지 확인하세요.

```ini
NEO4J_URI=bolt://host.docker.internal:7687  # Docker 사용 시
# NEO4J_URI=bolt://localhost:7687           # Local 사용 시

NEO4J_USER=neo4j
NEO4J_PASSWORD=****
KAKAO_API_KEY=****  # 크롤링/지오코딩 시 필수
```
