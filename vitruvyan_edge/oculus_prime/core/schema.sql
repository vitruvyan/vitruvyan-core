-- ============================================================================
-- Vitruvyan INTAKE — PostgreSQL Schema (Append-Only)
-- ============================================================================
-- Purpose: Immutable persistence for Evidence Packs and event audit trail
-- Compliance: ACCORDO-FONDATIVO-INTAKE-V1.1
-- 
-- Design Principles:
-- - Append-only (INSERT only, NO UPDATE/DELETE)
-- - Immutability enforced via RBAC (application user has INSERT+SELECT only)
-- - JSONB for flexible metadata storage
-- - Indexes for performance (evidence_id, source_hash, created_utc)
-- - Audit trail for event emission (success + failures)
-- ============================================================================

-- ============================================================================
-- TABLE: evidence_packs
-- ============================================================================
-- Storage for all Evidence Packs created by Intake Agents
-- Primary key: id (auto-increment)
-- Business key: evidence_id + chunk_id (unique constraint)
-- ============================================================================

CREATE TABLE IF NOT EXISTS evidence_packs (
    -- Primary key (internal)
    id BIGSERIAL PRIMARY KEY,
    
    -- Business keys
    evidence_id VARCHAR(255) NOT NULL,
    chunk_id VARCHAR(50) NOT NULL,
    
    -- Schema metadata
    schema_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    created_utc TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Source reference (JSONB)
    -- Example: {"source_type": "document", "source_uri": "/path/to/file.pdf", 
    --           "source_hash": "sha256:...", "mime_type": "application/pdf", "byte_size": 12345}
    source_ref JSONB NOT NULL,
    
    -- Normalized text (literal, pre-epistemic)
    normalized_text TEXT NOT NULL,  -- Can be empty string for non-text media
    
    -- Technical metadata (JSONB)
    -- Example: {"extraction_method": "pdfplumber", "extraction_version": "1.0.0",
    --           "language_detected": "en", "confidence_score": 0.95, 
    --           "chunk_position": {"start_offset": 0, "end_offset": 1024, "total_chunks": 3}}
    technical_metadata JSONB NOT NULL,
    
    -- Integrity (JSONB)
    -- Example: {"evidence_hash": "sha256:...", "immutable": true, "signature": null}
    integrity JSONB NOT NULL,
    
    -- Sampling Policy reference (external, versioned)
    sampling_policy_ref VARCHAR(255),
    
    -- Tags (JSONB array)
    -- Example: ["priority:high", "source:satellite"]
    tags JSONB DEFAULT '[]'::jsonb,
    
    -- Unique constraint on business key
    CONSTRAINT evidence_packs_unique_key UNIQUE (evidence_id, chunk_id)
);

-- Indexes for performance
CREATE INDEX idx_evidence_packs_evidence_id ON evidence_packs(evidence_id);
CREATE INDEX idx_evidence_packs_source_hash ON evidence_packs USING HASH ((source_ref->>'source_hash'));
CREATE INDEX idx_evidence_packs_source_type ON evidence_packs((source_ref->>'source_type'));
CREATE INDEX idx_evidence_packs_created_utc ON evidence_packs(created_utc DESC);
CREATE INDEX idx_evidence_packs_sampling_policy ON evidence_packs(sampling_policy_ref) WHERE sampling_policy_ref IS NOT NULL;

-- GIN index for JSONB queries
CREATE INDEX idx_evidence_packs_technical_metadata ON evidence_packs USING GIN (technical_metadata);
CREATE INDEX idx_evidence_packs_tags ON evidence_packs USING GIN (tags);

-- Comment
COMMENT ON TABLE evidence_packs IS 'Append-only storage for immutable Evidence Packs created by Intake Agents';
COMMENT ON COLUMN evidence_packs.evidence_id IS 'Business key: EVD-UUID format';
COMMENT ON COLUMN evidence_packs.chunk_id IS 'Business key: CHK-N format (N = chunk index)';
COMMENT ON COLUMN evidence_packs.normalized_text IS 'Literal, descriptive text (pre-epistemic, NO semantic interpretation)';
COMMENT ON COLUMN evidence_packs.integrity IS 'JSONB: {evidence_hash, immutable, signature}';
COMMENT ON COLUMN evidence_packs.sampling_policy_ref IS 'External, versioned Sampling Policy reference (e.g., SAMPPOL-DOC-DEFAULT-V1)';


-- ============================================================================
-- TABLE: intake_event_log
-- ============================================================================
-- Audit trail for successful event emissions to Redis Cognitive Bus
-- ============================================================================

CREATE TABLE IF NOT EXISTS intake_event_log (
    -- Primary key
    id BIGSERIAL PRIMARY KEY,
    
    -- Event metadata
    event_id VARCHAR(255) NOT NULL,
    event_version VARCHAR(20) NOT NULL,
    schema_ref VARCHAR(255) NOT NULL,  -- e.g., "vitruvyan://oculus_prime/events/evidence_created/v2.0"
    
    -- Business keys
    evidence_id VARCHAR(255) NOT NULL,
    chunk_id VARCHAR(50) NOT NULL,
    
    -- Idempotency key (SHA-256 of evidence_id + chunk_id + source_hash)
    idempotency_key VARCHAR(64) NOT NULL,
    
    -- Event payload (JSONB)
    payload JSONB NOT NULL,
    
    -- Metadata (JSONB)
    metadata JSONB NOT NULL,
    
    -- Timestamp
    emitted_utc TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Unique constraint on idempotency key
    CONSTRAINT intake_event_log_idempotency_unique UNIQUE (idempotency_key)
);

-- Indexes
CREATE INDEX idx_intake_event_log_event_id ON intake_event_log(event_id);
CREATE INDEX idx_intake_event_log_evidence_id ON intake_event_log(evidence_id);
CREATE INDEX idx_intake_event_log_emitted_utc ON intake_event_log(emitted_utc DESC);
CREATE INDEX idx_intake_event_log_schema_ref ON intake_event_log(schema_ref);

-- Comment
COMMENT ON TABLE intake_event_log IS 'Audit trail for emitted evidence-created events (v2 canonical + legacy alias)';
COMMENT ON COLUMN intake_event_log.idempotency_key IS 'SHA-256 hash: prevents duplicate event emission';
COMMENT ON COLUMN intake_event_log.schema_ref IS 'Event schema URI (e.g., vitruvyan://oculus_prime/events/evidence_created/v2.0)';


-- ============================================================================
-- TABLE: intake_event_failures
-- ============================================================================
-- Audit trail for FAILED event emissions (retry candidates)
-- ============================================================================

CREATE TABLE IF NOT EXISTS intake_event_failures (
    -- Primary key
    id BIGSERIAL PRIMARY KEY,
    
    -- Business keys
    evidence_id VARCHAR(255) NOT NULL,
    chunk_id VARCHAR(50) NOT NULL,
    
    -- Failure metadata
    error_message TEXT NOT NULL,
    error_traceback TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    
    -- Event payload (JSONB) — for retry
    payload JSONB NOT NULL,
    
    -- Timestamps
    failed_utc TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_retry_utc TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_intake_event_failures_evidence_id ON intake_event_failures(evidence_id);
CREATE INDEX idx_intake_event_failures_failed_utc ON intake_event_failures(failed_utc DESC);
CREATE INDEX idx_intake_event_failures_retry_count ON intake_event_failures(retry_count);

-- Comment
COMMENT ON TABLE intake_event_failures IS 'Audit trail for failed event emissions (retry candidates)';
COMMENT ON COLUMN intake_event_failures.retry_count IS 'Number of retry attempts (for exponential backoff)';


-- ============================================================================
-- VIEW: evidence_packs_recent
-- ============================================================================
-- Quick access to most recent Evidence Packs (last 24 hours)
-- ============================================================================

CREATE OR REPLACE VIEW evidence_packs_recent AS
SELECT 
    id,
    evidence_id,
    chunk_id,
    source_ref->>'source_type' AS source_type,
    source_ref->>'source_uri' AS source_uri,
    LEFT(normalized_text, 200) AS text_preview,
    created_utc
FROM evidence_packs
WHERE created_utc >= NOW() - INTERVAL '24 hours'
ORDER BY created_utc DESC
LIMIT 100;

COMMENT ON VIEW evidence_packs_recent IS 'Most recent Evidence Packs (last 24 hours, max 100)';


-- ============================================================================
-- VIEW: intake_event_log_recent
-- ============================================================================
-- Quick access to most recent event emissions
-- ============================================================================

CREATE OR REPLACE VIEW intake_event_log_recent AS
SELECT 
    id,
    event_id,
    evidence_id,
    chunk_id,
    schema_ref,
    payload->>'source_type' AS source_type,
    emitted_utc
FROM intake_event_log
WHERE emitted_utc >= NOW() - INTERVAL '24 hours'
ORDER BY emitted_utc DESC
LIMIT 100;

COMMENT ON VIEW intake_event_log_recent IS 'Most recent event emissions (last 24 hours, max 100)';


-- ============================================================================
-- FUNCTION: get_evidence_pack_by_id
-- ============================================================================
-- Retrieve Evidence Pack by evidence_id (for debugging/audit)
-- ============================================================================

CREATE OR REPLACE FUNCTION get_evidence_pack_by_id(p_evidence_id VARCHAR)
RETURNS TABLE (
    evidence_id VARCHAR,
    chunk_id VARCHAR,
    schema_version VARCHAR,
    created_utc TIMESTAMP WITH TIME ZONE,
    source_ref JSONB,
    normalized_text TEXT,
    technical_metadata JSONB,
    integrity JSONB,
    sampling_policy_ref VARCHAR,
    tags JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ep.evidence_id,
        ep.chunk_id,
        ep.schema_version,
        ep.created_utc,
        ep.source_ref,
        ep.normalized_text,
        ep.technical_metadata,
        ep.integrity,
        ep.sampling_policy_ref,
        ep.tags
    FROM evidence_packs ep
    WHERE ep.evidence_id = p_evidence_id
    ORDER BY ep.chunk_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_evidence_pack_by_id IS 'Retrieve all chunks for given evidence_id';


-- ============================================================================
-- RBAC ENFORCEMENT (Application User Restrictions)
-- ============================================================================
-- IMPORTANT: Application user must have INSERT + SELECT only
-- NO UPDATE or DELETE permissions (enforces immutability)
-- ============================================================================

-- Example role creation (adjust for your setup)
-- CREATE ROLE vitruvyan_oculus_prime_user WITH LOGIN PASSWORD 'secure_password';
-- GRANT CONNECT ON DATABASE vitruvyan TO vitruvyan_oculus_prime_user;
-- GRANT USAGE ON SCHEMA public TO vitruvyan_oculus_prime_user;
-- GRANT SELECT, INSERT ON evidence_packs TO vitruvyan_oculus_prime_user;
-- GRANT SELECT, INSERT ON intake_event_log TO vitruvyan_oculus_prime_user;
-- GRANT SELECT, INSERT ON intake_event_failures TO vitruvyan_oculus_prime_user;
-- GRANT SELECT ON evidence_packs_recent TO vitruvyan_oculus_prime_user;
-- GRANT SELECT ON intake_event_log_recent TO vitruvyan_oculus_prime_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO vitruvyan_oculus_prime_user;

-- Revoke dangerous permissions
-- REVOKE UPDATE, DELETE, TRUNCATE ON evidence_packs FROM vitruvyan_oculus_prime_user;
-- REVOKE UPDATE, DELETE, TRUNCATE ON intake_event_log FROM vitruvyan_oculus_prime_user;
-- REVOKE UPDATE, DELETE, TRUNCATE ON intake_event_failures FROM vitruvyan_oculus_prime_user;

COMMENT ON SCHEMA public IS 'RBAC enforced: application user has INSERT+SELECT only on Oculus Prime tables';


-- ============================================================================
-- APPEND-ONLY ENFORCEMENT (Trigger-Based)
-- ============================================================================
-- Prevents UPDATE/DELETE on evidence_packs table (immutability guarantee)
-- ============================================================================

CREATE OR REPLACE FUNCTION prevent_evidence_pack_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Evidence Packs are immutable. UPDATE/DELETE operations forbidden. (ACCORDO-FONDATIVO-INTAKE-V1.1)';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_evidence_pack_immutability_update
BEFORE UPDATE ON evidence_packs
FOR EACH ROW
EXECUTE FUNCTION prevent_evidence_pack_modification();

CREATE TRIGGER enforce_evidence_pack_immutability_delete
BEFORE DELETE ON evidence_packs
FOR EACH ROW
EXECUTE FUNCTION prevent_evidence_pack_modification();

COMMENT ON FUNCTION prevent_evidence_pack_modification IS 'Enforces append-only constraint on evidence_packs table';


-- ============================================================================
-- SAMPLE QUERIES (For Debugging/Audit)
-- ============================================================================

-- Query 1: Count Evidence Packs by source type
-- SELECT source_ref->>'source_type' AS source_type, COUNT(*) AS count
-- FROM evidence_packs
-- GROUP BY source_ref->>'source_type'
-- ORDER BY count DESC;

-- Query 2: Find Evidence Packs by source hash (detect duplicates)
-- SELECT evidence_id, chunk_id, created_utc
-- FROM evidence_packs
-- WHERE source_ref->>'source_hash' = 'sha256:abc123...';

-- Query 3: Find failed events with retry_count > 3
-- SELECT evidence_id, chunk_id, error_message, retry_count, failed_utc
-- FROM intake_event_failures
-- WHERE retry_count > 3
-- ORDER BY failed_utc DESC;

-- Query 4: Verify event emission for specific Evidence Pack
-- SELECT el.event_id, el.emitted_utc, el.schema_ref
-- FROM intake_event_log el
-- WHERE el.evidence_id = 'EVD-12345678-1234-5678-1234-567812345678';

-- Query 5: Get all chunks for a multi-chunk Evidence Pack
-- SELECT * FROM get_evidence_pack_by_id('EVD-12345678-1234-5678-1234-567812345678');


-- ============================================================================
-- GEOSPATIAL EVIDENCE (EXTENSION FOR GEO-INTAKE AGENT)
-- ============================================================================
-- Storage for canonical GeoJSON data from KML, KMZ, GPX, WKT files
-- Enables spatial queries (PostGIS optional for advanced queries)
-- ============================================================================

CREATE TABLE IF NOT EXISTS geospatial_evidence (
    -- Primary key
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign key to evidence_packs business key
    evidence_id VARCHAR(255) NOT NULL,
    chunk_id VARCHAR(50) NOT NULL DEFAULT 'CHK-0',
    
    -- Canonical GeoJSON (FeatureCollection or Feature)
    geo_json JSONB NOT NULL,
    
    -- Bounding box [min_lon, min_lat, max_lon, max_lat]
    bounding_box FLOAT8[4],
    
    -- Geometry types present (e.g., ["Polygon", "Point"])
    geometry_types TEXT[] NOT NULL,
    
    -- Calculated metrics
    area_km2 FLOAT8,              -- For polygons (approximate)
    total_length_km FLOAT8,       -- For linestrings (GPS tracks)
    
    -- Coordinate system (default WGS84)
    coordinate_system VARCHAR(50) DEFAULT 'WGS84',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Foreign key constraint
    CONSTRAINT fk_geospatial_evidence_pack
        FOREIGN KEY (evidence_id, chunk_id)
        REFERENCES evidence_packs(evidence_id, chunk_id)
        ON DELETE CASCADE
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'geospatial_evidence_unique_key'
    ) THEN
        ALTER TABLE geospatial_evidence
            ADD CONSTRAINT geospatial_evidence_unique_key UNIQUE (evidence_id, chunk_id);
    END IF;
END $$;

-- Indexes for geospatial queries
CREATE INDEX IF NOT EXISTS idx_geospatial_evidence_id
    ON geospatial_evidence(evidence_id);
CREATE INDEX IF NOT EXISTS idx_geospatial_evidence_chunk
    ON geospatial_evidence(chunk_id);

CREATE INDEX IF NOT EXISTS idx_geospatial_geometry_types
    ON geospatial_evidence USING GIN(geometry_types);

CREATE INDEX IF NOT EXISTS idx_geospatial_bounding_box
    ON geospatial_evidence USING GIST(box(
        point(bounding_box[1], bounding_box[2]),
        point(bounding_box[3], bounding_box[4])
    ));  -- Requires PostGIS for advanced spatial operations

COMMENT ON TABLE geospatial_evidence IS 'Canonical GeoJSON storage for KML, KMZ, GPX, WKT, GeoJSON imports';
COMMENT ON COLUMN geospatial_evidence.geo_json IS 'Normalized GeoJSON FeatureCollection (coordinate system: WGS84)';
COMMENT ON COLUMN geospatial_evidence.bounding_box IS 'Array: [min_lon, min_lat, max_lon, max_lat] for spatial indexing';
COMMENT ON COLUMN geospatial_evidence.area_km2 IS 'Approximate area for polygons (geodesic calculation requires PostGIS)';


-- ============================================================================
-- GEOSPATIAL QUERY EXAMPLES
-- ============================================================================

-- Query 1: Find all polygon evidence packs
-- SELECT ge.evidence_id, ge.area_km2, ge.bounding_box
-- FROM geospatial_evidence ge
-- WHERE 'Polygon' = ANY(ge.geometry_types)
-- ORDER BY ge.area_km2 DESC NULLS LAST;

-- Query 2: Find evidence packs within bounding box (rough filter)
-- SELECT ge.evidence_id, ge.bounding_box
-- FROM geospatial_evidence ge
-- WHERE ge.bounding_box[1] >= 9.0 AND ge.bounding_box[3] <= 10.0  -- Lon range
--   AND ge.bounding_box[2] >= 45.0 AND ge.bounding_box[4] <= 46.0; -- Lat range

-- Query 3: Get GeoJSON for specific evidence (for rendering on map)
-- SELECT ge.geo_json
-- FROM geospatial_evidence ge
-- WHERE ge.evidence_id = 'EVD-geo-12345678';

-- Query 4: Find GPS tracks (LineString geometries) longer than 10km
-- SELECT ge.evidence_id, ge.total_length_km, ep.literal_text
-- FROM geospatial_evidence ge
-- JOIN evidence_packs ep ON ge.evidence_id = ep.evidence_id
-- WHERE 'LineString' = ANY(ge.geometry_types)
--   AND ge.total_length_km > 10.0
-- ORDER BY ge.total_length_km DESC;


-- =============================================================================
-- TABLE: landscape_evidence
-- PURPOSE: Store landscape/raster map imagery with geospatial context
-- INTAKE AGENT: LandscapeIntakeAgent
-- SOURCES: Mapbox tiles, Google Maps screenshots, OpenStreetMap, satellite imagery
-- =============================================================================

CREATE TABLE IF NOT EXISTS landscape_evidence (
    id BIGSERIAL PRIMARY KEY,
    evidence_id VARCHAR(255) NOT NULL,
    chunk_id VARCHAR(50) NOT NULL DEFAULT 'CHK-0',
    
    -- Raster format & dimensions
    raster_format VARCHAR(50) NOT NULL,      -- PNG, JPG, GeoTIFF
    dimensions INT[],                        -- [width, height] in pixels
    
    -- Georeference data
    has_georeference BOOLEAN DEFAULT FALSE,
    coordinate_system VARCHAR(100),          -- WGS84, EPSG:3857, UTM zones
    bounds FLOAT[],                          -- [min_lon, min_lat, max_lon, max_lat]
    resolution_meters FLOAT,                 -- Meters per pixel
    
    -- Map provider context (if screenshot/tile)
    map_provider VARCHAR(50),                -- mapbox, google_maps, openstreetmap
    map_zoom INT,                            -- Zoom level (0-22)
    map_style VARCHAR(100),                  -- satellite-v9, streets, terrain
    map_center FLOAT[],                      -- [lon, lat]
    
    -- EXIF GPS (if photo)
    exif_gps JSONB,                          -- {"latitude": 45.4654, "longitude": 9.1859, "altitude": 120}
    
    -- Audit trail
    created_utc TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_hash VARCHAR(64) NOT NULL,
    
    -- Foreign key to main Evidence Pack
    CONSTRAINT fk_landscape_evidence_pack
        FOREIGN KEY (evidence_id, chunk_id)
        REFERENCES evidence_packs(evidence_id, chunk_id)
        ON DELETE CASCADE
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'landscape_evidence_unique_key'
    ) THEN
        ALTER TABLE landscape_evidence
            ADD CONSTRAINT landscape_evidence_unique_key UNIQUE (evidence_id, chunk_id);
    END IF;
END $$;

-- Indexes for query performance
CREATE INDEX idx_landscape_evidence_id ON landscape_evidence(evidence_id);
CREATE INDEX idx_landscape_evidence_chunk ON landscape_evidence(chunk_id);
CREATE INDEX idx_landscape_created ON landscape_evidence(created_utc);
CREATE INDEX idx_landscape_provider ON landscape_evidence(map_provider);
CREATE INDEX idx_landscape_georef ON landscape_evidence(has_georeference);

-- GIN index for EXIF GPS queries (JSONB)
CREATE INDEX idx_landscape_exif_gps ON landscape_evidence USING GIN(exif_gps);

-- Comments
COMMENT ON TABLE landscape_evidence IS 'Landscape raster/satellite imagery with geospatial context (Mapbox, OSM, Google Maps tiles)';
COMMENT ON COLUMN landscape_evidence.raster_format IS 'Image format: PNG, JPG, GeoTIFF';
COMMENT ON COLUMN landscape_evidence.has_georeference IS 'TRUE if image contains embedded coordinates (GeoTIFF tags, EXIF GPS)';
COMMENT ON COLUMN landscape_evidence.map_provider IS 'Map tile provider: mapbox, google_maps, openstreetmap, esri';
COMMENT ON COLUMN landscape_evidence.map_zoom IS 'Zoom level for web map tiles (0-22, higher = more detail)';
COMMENT ON COLUMN landscape_evidence.resolution_meters IS 'Spatial resolution in meters per pixel';

-- Example queries
-- Query 1: Find all Mapbox satellite imagery with zoom >= 15
-- SELECT le.evidence_id, le.map_zoom, le.bounds, ep.literal_text
-- FROM landscape_evidence le
-- JOIN evidence_packs ep ON le.evidence_id = ep.evidence_id
-- WHERE le.map_provider = 'mapbox'
--   AND le.map_style LIKE '%satellite%'
--   AND le.map_zoom >= 15;

-- Query 2: Find georeferenced images within bounding box (Milan area)
-- SELECT le.evidence_id, le.bounds, le.resolution_meters
-- FROM landscape_evidence le
-- WHERE le.has_georeference = TRUE
--   AND le.bounds[1] >= 45.4 AND le.bounds[3] <= 45.5  -- lat range
--   AND le.bounds[0] >= 9.1 AND le.bounds[2] <= 9.3;   -- lon range

-- Query 3: Find images with EXIF GPS altitude > 1000m
-- SELECT le.evidence_id, le.exif_gps->>'altitude' as altitude_m
-- FROM landscape_evidence le
-- WHERE le.exif_gps IS NOT NULL
--   AND (le.exif_gps->>'altitude')::float > 1000.0;
