-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create initial schema
CREATE TABLE IF NOT EXISTS listings (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    address TEXT,
    price BIGINT,
    area FLOAT,
    room_count INT,
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
