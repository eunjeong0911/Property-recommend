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
CREATE TEXT INDEX university_name_text IF NOT EXISTS FOR (u:University) ON (u.name);

// Additional TEXT INDEX for GeneralHospital (used in search queries)
CREATE TEXT INDEX general_hospital_name_text IF NOT EXISTS FOR (g:GeneralHospital) ON (g.name);

// Temperature Related Node Indexes
CREATE TEXT INDEX convenience_name_text IF NOT EXISTS FOR (c:Convenience) ON (c.name);
CREATE TEXT INDEX laundry_name_text IF NOT EXISTS FOR (l:Laundry) ON (l.name);
CREATE TEXT INDEX mart_name_text IF NOT EXISTS FOR (m:Mart) ON (m.name);
CREATE TEXT INDEX culture_name_text IF NOT EXISTS FOR (c:Culture) ON (c.name);
CREATE TEXT INDEX animal_hospital_name_text IF NOT EXISTS FOR (a:AnimalHospital) ON (a.name);
CREATE TEXT INDEX pet_playground_name_text IF NOT EXISTS FOR (p:PetPlayground) ON (p.name);
CREATE TEXT INDEX pet_shop_name_text IF NOT EXISTS FOR (p:PetShop) ON (p.name);
CREATE TEXT INDEX bus_station_name_text IF NOT EXISTS FOR (b:BusStation) ON (b.name);

// Facilities Added
CREATE TEXT INDEX pharmacy_name_text IF NOT EXISTS FOR (p:Pharmacy) ON (p.name);
CREATE TEXT INDEX police_station_name_text IF NOT EXISTS FOR (p:PoliceStation) ON (p.name);
CREATE TEXT INDEX fire_station_name_text IF NOT EXISTS FOR (f:FireStation) ON (f.name);
