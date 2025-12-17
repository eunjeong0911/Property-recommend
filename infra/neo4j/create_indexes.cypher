// =============================================================================
// Neo4j 인덱스 최적화 스크립트 (v2.0 - TEXT INDEX 포함)
// =============================================================================
// 
// 목적: 위치 및 시설 검색 성능 최적화
// 예상 효과: 쿼리 시간 5-8초 → 100ms 이하
//
// 실행 방법 (PowerShell):
// docker exec skn18-final-1team-neo4j-1 cypher-shell -u neo4j -p "1q2w3e4r!" < infra/neo4j/create_indexes.cypher
//
// 또는 Neo4j Browser (http://localhost:7474)에서 직접 실행
// =============================================================================


// =============================================================================
// 1. TEXT INDEX (Neo4j 5.0+)
// =============================================================================
// TEXT INDEX는 문자열 속성에 대한 빠른 검색을 지원합니다.
// CONTAINS, STARTS WITH, ENDS WITH 쿼리에 최적화되어 있습니다.
// Full-Text Index보다 단순하고 빠르며, 정확한 키워드 매칭에 적합합니다.

// 지하철역 이름 TEXT INDEX
CREATE TEXT INDEX subway_name_text IF NOT EXISTS
FOR (n:SubwayStation) ON (n.name);

// 대학교 이름 TEXT INDEX
CREATE TEXT INDEX college_name_text IF NOT EXISTS
FOR (n:College) ON (n.name);

// 병원 이름 TEXT INDEX
CREATE TEXT INDEX hospital_name_text IF NOT EXISTS
FOR (n:Hospital) ON (n.name);

// 종합병원 이름 TEXT INDEX
CREATE TEXT INDEX general_hospital_name_text IF NOT EXISTS
FOR (n:GeneralHospital) ON (n.name);

// 공원 이름 TEXT INDEX
CREATE TEXT INDEX park_name_text IF NOT EXISTS
FOR (n:Park) ON (n.name);

// 편의점 이름 TEXT INDEX
CREATE TEXT INDEX convenience_name_text IF NOT EXISTS
FOR (n:Convenience) ON (n.name);

// 약국 이름 TEXT INDEX
CREATE TEXT INDEX pharmacy_name_text IF NOT EXISTS
FOR (n:Pharmacy) ON (n.name);

// 경찰서 이름 TEXT INDEX  
CREATE TEXT INDEX police_name_text IF NOT EXISTS
FOR (n:PoliceStation) ON (n.name);

// 소방서 이름 TEXT INDEX
CREATE TEXT INDEX fire_name_text IF NOT EXISTS
FOR (n:FireStation) ON (n.name);


// =============================================================================
// 2. RANGE INDEX (B-tree) - 정확한 값 매칭 및 범위 검색용
// =============================================================================

// 매물 ID 인덱스 (PostgreSQL 조인용)
CREATE INDEX property_id_index IF NOT EXISTS FOR (p:Property) ON (p.id);
CREATE INDEX property_land_num_index IF NOT EXISTS FOR (p:Property) ON (p.land_num);

// 시설별 기본 인덱스
CREATE INDEX IF NOT EXISTS FOR (s:SubwayStation) ON (s.name);
CREATE INDEX IF NOT EXISTS FOR (c:College) ON (c.name);
CREATE INDEX IF NOT EXISTS FOR (h:Hospital) ON (h.name);
CREATE INDEX IF NOT EXISTS FOR (g:GeneralHospital) ON (g.name);
CREATE INDEX IF NOT EXISTS FOR (p:Pharmacy) ON (p.name);
CREATE INDEX IF NOT EXISTS FOR (c:Convenience) ON (c.name);
CREATE INDEX IF NOT EXISTS FOR (p:Park) ON (p.name);
CREATE INDEX IF NOT EXISTS FOR (p:PoliceStation) ON (p.name);
CREATE INDEX IF NOT EXISTS FOR (f:FireStation) ON (f.name);

// CCTV, 비상벨 (개수 집계용)
CREATE INDEX IF NOT EXISTS FOR (c:CCTV) ON (c.id);
CREATE INDEX IF NOT EXISTS FOR (e:EmergencyBell) ON (e.id);


// =============================================================================
// 3. FULL-TEXT INDEX (고급 검색용 - Lucene 기반)
// =============================================================================
// 와일드카드 검색, 퍼지 매칭이 필요한 경우 사용
// TEXT INDEX보다 무겁지만 더 유연한 검색 가능

// 지하철역 Full-Text (와일드카드 검색용)
CREATE FULLTEXT INDEX subway_name_fulltext IF NOT EXISTS
FOR (n:SubwayStation) ON EACH [n.name];

// 대학교 Full-Text
CREATE FULLTEXT INDEX college_name_fulltext IF NOT EXISTS
FOR (n:College) ON EACH [n.name];

// 통합 위치 검색 Full-Text (다중 라벨)
CREATE FULLTEXT INDEX location_search_fulltext IF NOT EXISTS
FOR (n:SubwayStation|College|Hospital|GeneralHospital|Park) ON EACH [n.name];


// =============================================================================
// 4. 관계 속성 인덱스 (Neo4j 5.7+)
// =============================================================================
// 관계의 distance 속성에 대한 인덱스 (정렬 최적화)
// 주의: Neo4j 버전에 따라 지원되지 않을 수 있음

// NEAR_SUBWAY 관계 거리 인덱스
// CREATE INDEX near_subway_dist IF NOT EXISTS FOR ()-[r:NEAR_SUBWAY]-() ON (r.distance);

// NEAR_CONVENIENCE 관계 거리 인덱스
// CREATE INDEX near_conv_dist IF NOT EXISTS FOR ()-[r:NEAR_CONVENIENCE]-() ON (r.distance);


// =============================================================================
// 5. 인덱스 확인 및 테스트 쿼리
// =============================================================================

// 모든 인덱스 목록 확인
// SHOW INDEXES;

// TEXT INDEX 테스트 (CONTAINS 사용)
// MATCH (s:SubwayStation) WHERE s.name CONTAINS '홍대' RETURN s.name LIMIT 5;

// FULL-TEXT INDEX 테스트 (db.index.fulltext.queryNodes 사용)
// CALL db.index.fulltext.queryNodes("subway_name_fulltext", "홍대*") YIELD node
// RETURN node.name LIMIT 5;

// 성능 비교 테스트
// PROFILE MATCH (s:SubwayStation) WHERE s.name STARTS WITH '강남' RETURN s.name;
