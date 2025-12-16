// =============================================================================
// Neo4j 인덱스 최적화 스크립트
// =============================================================================
// 
// 목적: 위치 및 시설 검색 성능 향상
// 예상 효과: 쿼리 시간 5-8초 → 1초 이하
//
// 실행 방법 (PowerShell):
// docker exec skn18-final-1team-neo4j-1 cypher-shell -u neo4j -p "1q2w3e4r!" < infra/neo4j/create_indexes.cypher
//
// 또는 Neo4j Browser (http://localhost:7474)에서 직접 실행
// =============================================================================

// -----------------------------------------------------------------------------
// 1. 기본 노드 인덱스 (name 필드)
// -----------------------------------------------------------------------------

// 지하철역
CREATE INDEX IF NOT EXISTS FOR (s:SubwayStation) ON (s.name);

// 편의점/마트
CREATE INDEX IF NOT EXISTS FOR (s:Store) ON (s.name);

// 병원
CREATE INDEX IF NOT EXISTS FOR (h:Hospital) ON (h.name);

// 약국
CREATE INDEX IF NOT EXISTS FOR (p:Pharmacy) ON (p.name);

// 대학교
CREATE INDEX IF NOT EXISTS FOR (c:College) ON (c.name);

// 공원
CREATE INDEX IF NOT EXISTS FOR (p:Park) ON (p.name);

// 버스정류장
CREATE INDEX IF NOT EXISTS FOR (b:BusStation) ON (b.name);

// 경찰서
CREATE INDEX IF NOT EXISTS FOR (p:PoliceStation) ON (p.name);

// 소방서
CREATE INDEX IF NOT EXISTS FOR (f:FireStation) ON (f.name);

// -----------------------------------------------------------------------------
// 2. ID 기반 인덱스
// -----------------------------------------------------------------------------

// 매물 (land_num으로 PostgreSQL과 연동)
CREATE INDEX IF NOT EXISTS FOR (p:Property) ON (p.land_num);

// CCTV
CREATE INDEX IF NOT EXISTS FOR (c:CCTV) ON (c.id);

// 비상벨
CREATE INDEX IF NOT EXISTS FOR (e:EmergencyBell) ON (e.id);

// -----------------------------------------------------------------------------
// 3. Full-Text Index (위치 키워드 검색용)
// -----------------------------------------------------------------------------

// 지하철역 Full-Text
CREATE FULLTEXT INDEX subway_name_fulltext IF NOT EXISTS
FOR (n:SubwayStation) ON EACH [n.name];

// 대학교 Full-Text
CREATE FULLTEXT INDEX college_name_fulltext IF NOT EXISTS
FOR (n:College) ON EACH [n.name];

// 병원 Full-Text
CREATE FULLTEXT INDEX hospital_name_fulltext IF NOT EXISTS
FOR (n:Hospital) ON EACH [n.name];

// 공원 Full-Text
CREATE FULLTEXT INDEX park_name_fulltext IF NOT EXISTS
FOR (n:Park) ON EACH [n.name];

// 통합 위치 검색 (권장)
CREATE FULLTEXT INDEX location_search_fulltext IF NOT EXISTS
FOR (n:SubwayStation|College|Hospital|Park) ON EACH [n.name];

// -----------------------------------------------------------------------------
// 4. 인덱스 확인 명령어
// -----------------------------------------------------------------------------
// SHOW INDEXES;
//
// Full-Text Index 사용 예시:
// CALL db.index.fulltext.queryNodes("location_search_fulltext", "홍대*") YIELD node
// RETURN node.name, labels(node) LIMIT 10;
