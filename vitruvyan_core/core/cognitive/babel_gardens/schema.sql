-- core/gemma_shared/schema.sql
-- Gemma Cognitive Layer Database Schema

CREATE EXTENSION IF NOT EXISTS vector;

-- Seedbank: Fused embeddings storage
CREATE TABLE IF NOT EXISTS seedbank (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    text_content TEXT NOT NULL,
    embedding_fused VECTOR(384) NOT NULL,
    sentiment_label VARCHAR(16) NOT NULL,
    sentiment_score FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Metadata fields
    model_version VARCHAR(50) DEFAULT 'gemma_v1.0',
    fusion_method VARCHAR(50) DEFAULT 'semantic_sentiment_concat',
    confidence_score FLOAT DEFAULT 0.0,
    
    -- Indexing for performance
    CONSTRAINT valid_sentiment_label CHECK (sentiment_label IN ('positive', 'negative', 'neutral')),
    CONSTRAINT valid_sentiment_score CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_seedbank_source ON seedbank(source);
CREATE INDEX IF NOT EXISTS idx_seedbank_sentiment ON seedbank(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_seedbank_created_at ON seedbank(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_seedbank_confidence ON seedbank(confidence_score DESC);

-- Embedding similarity search index with explicit dimension
CREATE INDEX IF NOT EXISTS idx_seedbank_embedding_cosine 
ON seedbank USING ivfflat (embedding_fused vector_cosine_ops) 
WITH (lists = 100);

-- Additional performance index for L2 distance
CREATE INDEX IF NOT EXISTS idx_seedbank_embedding_l2
ON seedbank USING ivfflat (embedding_fused vector_l2_ops)
WITH (lists = 100);

COMMENT ON TABLE seedbank IS 'Gemma Cognitive Layer: Fused semantic and sentiment embeddings storage';
COMMENT ON COLUMN seedbank.embedding_fused IS 'Concatenated vector: semantic(384) + sentiment features';
COMMENT ON COLUMN seedbank.source IS 'Source system: codex_hunters, reddit_scraper, etc.';
COMMENT ON COLUMN seedbank.fusion_method IS 'Algorithm used for embedding fusion';