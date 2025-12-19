// Create constraints
CREATE CONSTRAINT listing_id IF NOT EXISTS FOR (l:Listing) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT facility_id IF NOT EXISTS FOR (f:Facility) REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT property_id IF NOT EXISTS FOR (p:Property) REQUIRE p.id IS UNIQUE;

// Create indexes
CREATE INDEX listing_price IF NOT EXISTS FOR (l:Listing) ON (l.price);
CREATE INDEX listing_area IF NOT EXISTS FOR (l:Listing) ON (l.area);

// TEXT INDEX - 이름 검색 최적화 (Requirements 3.1, 3.3)
// SubwayStation, College, Hospital, Park 노드에 name 필드 TEXT INDEX 추가
CREATE TEXT INDEX subway_name_text IF NOT EXISTS FOR (s:SubwayStation) ON (s.name);
CREATE TEXT INDEX college_name_text IF NOT EXISTS FOR (c:College) ON (c.name);
CREATE TEXT INDEX hospital_name_text IF NOT EXISTS FOR (h:Hospital) ON (h.name);
CREATE TEXT INDEX park_name_text IF NOT EXISTS FOR (p:Park) ON (p.name);

// Additional TEXT INDEX for GeneralHospital (used in search queries)
CREATE TEXT INDEX general_hospital_name_text IF NOT EXISTS FOR (g:GeneralHospital) ON (g.name);
