-- ============================================
-- VITRUVYAN CORE - DOMAIN-AGNOSTIC DATABASE SCHEMA
-- Phase 1D: Cognitive Foundation Tables
-- Date: December 29, 2025
-- ============================================
-- Purpose: Generic tables for cognitive processing, independent of domain
-- Supports: Any cognitive application (finance, healthcare, research, etc.)

-- ============================================
-- 1. COGNITIVE ENTITIES - Core data objects
-- ============================================

-- Generic entities table for any domain objects
CREATE TABLE IF NOT EXISTS cognitive_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(100) NOT NULL, -- 'document', 'user', 'concept', 'pattern', etc.
    name VARCHAR(500),
    description TEXT,
    metadata JSONB, -- Flexible metadata for any domain
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    version INTEGER DEFAULT 1
);

-- Entity relationships (graph structure)
CREATE TABLE IF NOT EXISTS entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID REFERENCES cognitive_entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES cognitive_entities(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL, -- 'contains', 'references', 'similar_to', etc.
    strength FLOAT DEFAULT 1.0,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================
-- 2. COGNITIVE EVENTS - Event sourcing
-- ============================================

-- Generic event log for all cognitive operations
CREATE TABLE IF NOT EXISTS cognitive_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(200) NOT NULL, -- 'entity.created', 'relationship.formed', etc.
    entity_id UUID REFERENCES cognitive_entities(id) ON DELETE SET NULL,
    event_data JSONB NOT NULL,
    correlation_id UUID, -- For tracking event chains
    source_service VARCHAR(100), -- Which service generated the event
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================
-- 3. VECTOR STORAGE METADATA - For embeddings
-- ============================================

-- Metadata for vector collections (Qdrant integration)
CREATE TABLE IF NOT EXISTS vector_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_name VARCHAR(200) UNIQUE NOT NULL,
    vector_dimension INTEGER NOT NULL,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Mapping between entities and their vectors
CREATE TABLE IF NOT EXISTS entity_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES cognitive_entities(id) ON DELETE CASCADE,
    collection_name VARCHAR(200) NOT NULL,
    vector_id VARCHAR(500) NOT NULL, -- Qdrant vector ID
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================
-- 4. CONFIGURATION & SETTINGS
-- ============================================

-- Generic configuration table for any service
CREATE TABLE IF NOT EXISTS service_configuration (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(200) NOT NULL,
    config_key VARCHAR(300) NOT NULL,
    config_value JSONB,
    environment VARCHAR(50) DEFAULT 'production',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(service_name, config_key, environment)
);

-- ============================================
-- 5. AUDIT & COMPLIANCE - Domain agnostic
-- ============================================

-- Generic audit log for all operations
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_type VARCHAR(100) NOT NULL, -- 'create', 'update', 'delete', 'process'
    entity_type VARCHAR(100),
    entity_id UUID,
    user_id VARCHAR(200), -- Generic user identifier
    operation_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================
-- 6. PROCESSING QUEUES - For async operations
-- ============================================

-- Generic job queue for background processing
CREATE TABLE IF NOT EXISTS processing_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(200) NOT NULL,
    job_data JSONB NOT NULL,
    priority INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- ============================================
-- INDEXES for Performance
-- ============================================

-- Cognitive entities indexes
CREATE INDEX IF NOT EXISTS idx_cognitive_entities_type ON cognitive_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_cognitive_entities_created ON cognitive_entities(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cognitive_entities_updated ON cognitive_entities(updated_at DESC);

-- Relationships indexes
CREATE INDEX IF NOT EXISTS idx_entity_relationships_source ON entity_relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_relationships_target ON entity_relationships(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_relationships_type ON entity_relationships(relationship_type);

-- Events indexes
CREATE INDEX IF NOT EXISTS idx_cognitive_events_type ON cognitive_events(event_type);
CREATE INDEX IF NOT EXISTS idx_cognitive_events_entity ON cognitive_events(entity_id);
CREATE INDEX IF NOT EXISTS idx_cognitive_events_created ON cognitive_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cognitive_events_correlation ON cognitive_events(correlation_id);

-- Vector indexes
CREATE INDEX IF NOT EXISTS idx_entity_vectors_entity ON entity_vectors(entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_vectors_collection ON entity_vectors(collection_name);

-- Configuration indexes
CREATE INDEX IF NOT EXISTS idx_service_config_service ON service_configuration(service_name);
CREATE INDEX IF NOT EXISTS idx_service_config_key ON service_configuration(config_key);

-- Audit indexes
CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit_log(operation_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at DESC);

-- Queue indexes
CREATE INDEX IF NOT EXISTS idx_processing_queue_status ON processing_queue(status);
CREATE INDEX IF NOT EXISTS idx_processing_queue_type ON processing_queue(job_type);
CREATE INDEX IF NOT EXISTS idx_processing_queue_priority ON processing_queue(priority DESC);
CREATE INDEX IF NOT EXISTS idx_processing_queue_created ON processing_queue(created_at);

-- ============================================
-- COMMENTS for Documentation
-- ============================================

COMMENT ON TABLE cognitive_entities IS 'Domain-agnostic entities for any cognitive application';
COMMENT ON TABLE entity_relationships IS 'Graph relationships between cognitive entities';
COMMENT ON TABLE cognitive_events IS 'Event sourcing for all cognitive operations';
COMMENT ON TABLE vector_collections IS 'Metadata for vector collections (Qdrant integration)';
COMMENT ON TABLE entity_vectors IS 'Mapping between entities and their vector representations';
COMMENT ON TABLE service_configuration IS 'Generic configuration storage for all services';
COMMENT ON TABLE audit_log IS 'Domain-agnostic audit trail for compliance';
COMMENT ON TABLE processing_queue IS 'Background job processing queue';

-- ============================================
-- INITIAL DATA - Generic configurations
-- ============================================

-- Insert default configurations for core services
INSERT INTO service_configuration (service_name, config_key, config_value, environment)
VALUES
    ('cognitive_core', 'version', '"1.0.0"', 'production'),
    ('cognitive_core', 'domain_mode', '"agnostic"', 'production'),
    ('vector_storage', 'default_dimension', '384', 'production'),
    ('event_system', 'retention_days', '90', 'production')
ON CONFLICT (service_name, config_key, environment) DO NOTHING;

-- Insert default vector collections
INSERT INTO vector_collections (collection_name, vector_dimension, description, metadata)
VALUES
    ('cognitive_entities', 384, 'General purpose entity embeddings', '{"model": "sentence-transformers/all-MiniLM-L6-v2"}'),
    ('semantic_search', 384, 'Semantic search vectors', '{"model": "sentence-transformers/all-MiniLM-L6-v2"}'),
    ('relationship_vectors', 384, 'Relationship strength embeddings', '{"model": "sentence-transformers/all-MiniLM-L6-v2"}')
ON CONFLICT (collection_name) DO NOTHING;