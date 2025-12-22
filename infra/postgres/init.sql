-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable pg_trgm extension for text search optimization
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================
-- Land 테이블 (ERD 기반)
-- ============================================================
CREATE TABLE IF NOT EXISTS land (
    -- PK
    land_id SERIAL PRIMARY KEY,
    
    -- 매물 기본정보 (ERD Land 테이블)
    land_num VARCHAR(20) UNIQUE NOT NULL,       -- 매물번호
    landbroker_id INT,                           -- 중개사 FK (나중에 연결)
    building_type VARCHAR(20) NOT NULL,          -- 건물형태 (원룸, 빌라, 다가구 등)
    address VARCHAR(200),                        -- 주소
    deal_type VARCHAR(30),                       -- 거래유형 (월세, 전세, 매매)
    like_count INT DEFAULT 0,                    -- 찜 수
    view_count INT DEFAULT 0,                    -- 조회수
    
    -- 가격 (개별 컬럼 - 쿼리 성능 최적화, 만원 단위)
    deposit INT DEFAULT 0,                       -- 보증금 (만원)
    monthly_rent INT DEFAULT 0,                  -- 월세 (만원)
    jeonse_price INT DEFAULT 0,                  -- 전세가 (만원)
    sale_price INT DEFAULT 0,                    -- 매매가 (만원)
    
    -- 기타 정보
    url TEXT,                                    -- 매물 URL
    trade_info JSONB,                            -- 거래정보 (관리비, 입주가능일 등)
    listing_info JSONB,                          -- 상세정보 (방개수, 층수 등)
    additional_options TEXT[],                   -- 추가옵션
    description TEXT,                            -- 상세설명
    -- agent_info 제거 - landbroker_id FK로 대체 (데이터 정규화)
    
    -- 타임스탬프
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 가격/거래유형 조회 성능을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_land_deposit ON land(deposit);
CREATE INDEX IF NOT EXISTS idx_land_monthly_rent ON land(monthly_rent);
CREATE INDEX IF NOT EXISTS idx_land_jeonse_price ON land(jeonse_price);
CREATE INDEX IF NOT EXISTS idx_land_sale_price ON land(sale_price);
CREATE INDEX IF NOT EXISTS idx_land_deal_type ON land(deal_type);
CREATE INDEX IF NOT EXISTS idx_land_building_type ON land(building_type);
CREATE INDEX IF NOT EXISTS idx_land_land_num ON land(land_num);

-- 주소 검색을 위한 GIN 인덱스 (pg_trgm 사용)
CREATE INDEX IF NOT EXISTS idx_land_address_gin ON land USING gin(address gin_trgm_ops);

-- 복합 인덱스 (거래유형 + 건물유형)
CREATE INDEX IF NOT EXISTS idx_land_deal_building ON land(deal_type, building_type);

-- ============================================================
-- LandImage 테이블 (ERD 기반 - 부동산 이미지)
-- ============================================================
CREATE TABLE IF NOT EXISTS land_image (
    landimage_id SERIAL PRIMARY KEY,
    land_id INT NOT NULL REFERENCES land(land_id) ON DELETE CASCADE,
    img_url VARCHAR(500) NOT NULL,               -- 매물 사진 URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_land_image_land_id ON land_image(land_id);

-- ============================================================
-- Land Embeddings 테이블 (벡터 검색용)
-- ============================================================
CREATE TABLE IF NOT EXISTS land_embeddings (
    id SERIAL PRIMARY KEY,
    land_id INT REFERENCES land(land_id) ON DELETE CASCADE,
    chunk_text TEXT,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ON land_embeddings USING ivfflat (embedding vector_cosine_ops);


-- ============================================================
-- LandBroker 테이블 (ERD 기반 - 중개사 정보)
-- ============================================================
CREATE TABLE IF NOT EXISTS landbroker (
    landbroker_id SERIAL PRIMARY KEY,
    office_name VARCHAR(200),
    representative VARCHAR(100),
    phone VARCHAR(50),
    address VARCHAR(500),
    registration_number VARCHAR(100) UNIQUE,
    completed_deals INT DEFAULT 0,
    registered_properties INT DEFAULT 0,
    brokers_count INT DEFAULT 0,
    assistants_count INT DEFAULT 0,
    staff_count INT DEFAULT 0,
    region VARCHAR(100),
    registration_date DATE,
    trust_score VARCHAR(1) CHECK (trust_score IN ('A', 'B', 'C')),
    trust_score_updated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_landbroker_registration_number ON landbroker(registration_number);

-- Land 테이블의 landbroker_id FK 연결
ALTER TABLE land DROP CONSTRAINT IF EXISTS fk_land_landbroker;
ALTER TABLE land ADD CONSTRAINT fk_land_landbroker FOREIGN KEY (landbroker_id) REFERENCES landbroker(landbroker_id) ON DELETE SET NULL;

