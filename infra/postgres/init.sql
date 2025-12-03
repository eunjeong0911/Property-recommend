-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create initial schema
CREATE TABLE IF NOT EXISTS listings (
    id SERIAL PRIMARY KEY,
    listing_id VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255),
    address TEXT,
    url TEXT,
    images JSONB,
    address_info JSONB,
    floor_plan_url TEXT[],
    trade_info JSONB,
    listing_info JSONB,
    additional_options TEXT[],
    nearby_schools TEXT[],
    description TEXT,
    agent_info JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS listing_embeddings (
    id SERIAL PRIMARY KEY,
    listing_id INT REFERENCES listings(id) ON DELETE CASCADE,
    chunk_text TEXT,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ON listing_embeddings USING ivfflat (embedding vector_cosine_ops);
