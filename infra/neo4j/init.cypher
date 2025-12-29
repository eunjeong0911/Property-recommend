// =============================================================================
// Neo4j 인덱스 및 제약조건 초기화
// =============================================================================
// 이 파일은 Neo4j 검색 성능을 최적화하기 위한 인덱스와 제약조건을 정의합니다.
// TEXT INDEX: STARTS WITH, CONTAINS 검색 최적화
// INDEX: 특정 속성 조회/정렬 최적화
// CONSTRAINT: 유니크 제약조건 (중복 방지 + 조회 최적화)

// =============================================================================
// 1. 핵심 노드 제약조건 (Constraints)
// =============================================================================
CREATE CONSTRAINT property_id IF NOT EXISTS FOR (p:Property) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT metric_name IF NOT EXISTS FOR (m:Metric) REQUIRE m.name IS UNIQUE;
CREATE CONSTRAINT listing_id IF NOT EXISTS FOR (l:Listing) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT facility_id IF NOT EXISTS FOR (f:Facility) REQUIRE f.id IS UNIQUE;

// =============================================================================
// 2. Property (매물) 인덱스
// =============================================================================
CREATE INDEX property_id_index IF NOT EXISTS FOR (p:Property) ON (p.id);
CREATE INDEX property_location IF NOT EXISTS FOR (p:Property) ON (p.location);

// =============================================================================
// 3. 교통 시설 (Transport)
// =============================================================================
CREATE TEXT INDEX subway_name_text IF NOT EXISTS FOR (s:SubwayStation) ON (s.name);
CREATE TEXT INDEX bus_station_name_text IF NOT EXISTS FOR (b:BusStation) ON (b.name);

// =============================================================================
// 4. 의료 시설 (Medical)
// =============================================================================
CREATE TEXT INDEX hospital_name_text IF NOT EXISTS FOR (h:Hospital) ON (h.name);
CREATE TEXT INDEX general_hospital_name_text IF NOT EXISTS FOR (g:GeneralHospital) ON (g.name);
CREATE TEXT INDEX pharmacy_name_text IF NOT EXISTS FOR (p:Pharmacy) ON (p.name);

// =============================================================================
// 5. 교육 시설 (Education)
// =============================================================================
CREATE TEXT INDEX college_name_text IF NOT EXISTS FOR (c:College) ON (c.name);
CREATE TEXT INDEX university_name_text IF NOT EXISTS FOR (u:University) ON (u.name);

// =============================================================================
// 6. 편의 시설 (Convenience)
// =============================================================================
CREATE TEXT INDEX store_name_text IF NOT EXISTS FOR (s:Store) ON (s.name);
CREATE TEXT INDEX convenience_name_text IF NOT EXISTS FOR (c:Convenience) ON (c.name);
CREATE TEXT INDEX laundry_name_text IF NOT EXISTS FOR (l:Laundry) ON (l.name);
CREATE TEXT INDEX mart_name_text IF NOT EXISTS FOR (m:Mart) ON (m.name);

// =============================================================================
// 7. 문화/여가 시설 (Culture & Leisure)
// =============================================================================
CREATE TEXT INDEX culture_name_text IF NOT EXISTS FOR (c:Culture) ON (c.name);
CREATE TEXT INDEX park_name_text IF NOT EXISTS FOR (p:Park) ON (p.name);

// =============================================================================
// 8. 안전 시설 (Safety)
// =============================================================================
CREATE INDEX cctv_id IF NOT EXISTS FOR (c:CCTV) ON (c.id);
CREATE INDEX emergency_bell_id IF NOT EXISTS FOR (e:EmergencyBell) ON (e.id);
CREATE TEXT INDEX police_station_name_text IF NOT EXISTS FOR (p:PoliceStation) ON (p.name);
CREATE TEXT INDEX fire_station_name_text IF NOT EXISTS FOR (f:FireStation) ON (f.name);

// =============================================================================
// 9. 반려동물 시설 (Pet)
// =============================================================================
CREATE TEXT INDEX pet_playground_name_text IF NOT EXISTS FOR (p:PetPlayground) ON (p.name);
CREATE TEXT INDEX animal_hospital_name_text IF NOT EXISTS FOR (a:AnimalHospital) ON (a.name);
CREATE TEXT INDEX pet_shop_name_text IF NOT EXISTS FOR (p:PetShop) ON (p.name);

// =============================================================================
// 10. 온도 점수 (Temperature Metrics)
// =============================================================================
// Metric 노드: Safety, Traffic, LivingConvenience, Culture, Pet
// (Property)-[r:HAS_TEMPERATURE {temperature: float}]->(Metric)
CREATE TEXT INDEX metric_name_text IF NOT EXISTS FOR (m:Metric) ON (m.name);

// =============================================================================
// 11. 기타 인덱스 (Listing - 레거시)
// =============================================================================
CREATE INDEX listing_price IF NOT EXISTS FOR (l:Listing) ON (l.price);
CREATE INDEX listing_area IF NOT EXISTS FOR (l:Listing) ON (l.area);
