# Neo4j Data Importers

Neo4j 그래프 데이터베이스 임포터 모음

## 구조

```
neo4j/
├── import_neo4j_only.py      # 메인 실행 스크립트
├── facility/                 # 시설 노드 임포터
│   ├── transport_importer.py # 지하철/버스
│   ├── amenity_importer.py   # 편의시설
│   ├── safety_importer.py    # 안전시설 (CCTV, 비상벨)
│   ├── culture_importer.py   # 문화시설
│   └── animal_importer.py    # 반려동물 시설
├── property/                 # 매물 노드 임포터
└── temperature/              # 온도 점수 임포터
    ├── safety_score_importer.py
    ├── convenience_score_importer.py
    ├── traffic_score_importer.py
    ├── culture_score_importer.py
    └── pet_score_importer.py
```

## 실행

```bash
# 프로젝트 루트에서
python scripts/03_import/neo4j/import_neo4j_only.py
```
