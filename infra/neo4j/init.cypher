// Create constraints
CREATE CONSTRAINT listing_id IF NOT EXISTS FOR (l:Listing) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT facility_id IF NOT EXISTS FOR (f:Facility) REQUIRE f.id IS UNIQUE;

// Create indexes
CREATE INDEX listing_price IF NOT EXISTS FOR (l:Listing) ON (l.price);
CREATE INDEX listing_area IF NOT EXISTS FOR (l:Listing) ON (l.area);
