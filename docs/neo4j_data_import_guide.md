# Data Import System Guide

이 문서는 Neo4j 그래프 데이터베이스에 다양한 도시 데이터와 매물 정보를 적재하기 위한 **데이터 임포트 시스템**에 대해 설명합니다.

## 1. 개요

이 시스템은 서울시의 교통, 편의시설, 안전시설, 관공서 및 부동산 매물 데이터를 수집, 가공하여 Neo4j에 노드(Node)와 관계(Relationship)로 저장합니다. 모든 스크립트는 모듈화되어 있으며, `scripts/data_import` 폴더 내에 위치합니다.

## 2. 폴더 구조

```text
scripts/data_import/
├── main.py          # [실행] 전체 데이터 임포트 파이프라인 진입점
├── config.py        # [설정] 환경 변수(API Key, DB 접속 정보) 및 경로 설정
├── database.py      # [공통] Neo4j 드라이버 연결 및 세션 관리
├── geocoder.py      # [공통] Kakao Local API를 이용한 주소 -> 좌표 변환
└── importers/       # [로직] 카테고리별 데이터 임포트 모듈
    ├── transport_importer.py  # 지하철, 버스
    ├── amenity_importer.py    # 병원, 약국, 대학교, 상가, 공원
    ├── safety_importer.py     # CCTV, 비상벨, 경찰서, 소방서
    └── property_importer.py   # 부동산 매물 (Home Data)
```

## 3. 실행 방법

전체 데이터를 순서대로 임포트하려면 `main.py`를 실행하세요.

```bash
python scripts/data_import/main.py
```

> **주의**: 매물 데이터(`property_importer.py`)와 관공서 데이터는 Kakao API를 사용하여 지오코딩을 수행하므로, 데이터 양에 따라 시간이 소요될 수 있습니다.

## 4. 모듈별 상세 설명

### 4.1 Transport Importer (`transport_importer.py`)

- **대상**: 지하철역, 버스정류장
- **기능**:
  - 서울시 내의 역/정류장을 필터링하여 저장합니다.
  - **연결**: 매물(Property) 기준 지하철 **1km**, 버스 **200m** 이내 `NEAR_SUBWAY`, `NEAR_BUS` 관계 생성.

### 4.2 Amenity Importer (`amenity_importer.py`)

- **대상**: 병원, 약국, 대학교, 상가(편의점/슈퍼마켓), 공원
- **기능**:
  - **병원**: 종합병원(1km), 일반병원(500m) 구분 연결.
  - **약국**: 200m 이내 연결.
  - **상가**: 편의점/슈퍼마켓만 `Convenience`로 분류하여 200m 이내 연결.
  - **공원**: 500m 이내 연결.
  - **대학교**: 1km 이내 연결.

### 4.3 Safety Importer (`safety_importer.py`)

- **대상**: CCTV, 비상벨, 경찰서, 소방서
- **기능**:
  - **안전시설(CCTV/비상벨)**: 100m 이내 연결 (`NEAR_CCTV`, `NEAR_BELL`).
  - **관공서**: 경찰서(1km), 소방서(2.5km) 이내 연결.

### 4.4 Property Importer (`property_importer.py`)

- **대상**: 부동산 매물 JSON 파일 (`data/GraphDB_data/home_data/`)
- **기능**:
  - JSON 파일의 주소를 읽어 위경도로 변환(Geocoding) 후 `Property` 노드 생성.

## 5. 환경 설정 (`config.py`)

실행 전 `.env` 파일에 다음 정보가 설정되어 있어야 합니다.

```ini
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
KAKAO_API_KEY=your_kakao_api_key -> neo4j에 데이터 적재시 geocoding용으로 필요함
```
