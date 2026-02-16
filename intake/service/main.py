"""
AEGIS Core — INTAKE API Backend
================================

FastAPI endpoints for Evidence Pack ingestion (Landscape & Geo data).

Endpoints:
    POST /api/intake/landscape  - Ingest landscape/satellite imagery
    POST /api/intake/geo        - Ingest geo-point data (events, POIs, tracks)
    GET  /api/intake/evidence/:evidence_id - Retrieve Evidence Pack
    GET  /health                - Health check

Architecture:
    File Upload (multipart/form-data) →
    LandscapeIntakeAgent or GeoIntakeAgent →
    PostgreSQL (evidence_packs, landscape_evidence, geo_evidence) →
    Redis Event Emission (evidence_created) →
    Response (Evidence Pack JSON)

Compliance:
    - ACCORDO-FONDATIVO-INTAKE v1.1 (§1-8)
    - intake_payload_schema_v0.1.11.json
    - Intake Questionnaires (Section 1, 4, 5, 10)

Author: AEGIS Team
Created: January 9, 2026
Status: PRODUCTION READY
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from datetime import datetime
import os
import logging
import tempfile
import shutil
import redis
import json
import mimetypes
from pathlib import Path

# AEGIS INTAKE agents
import sys
sys.path.insert(0, '/app')
from vitruvyan_core.aegis.intake.agents.landscape_intake import LandscapeIntakeAgent
from vitruvyan_core.aegis.intake.agents.geo_intake import GeoIntakeAgent
from vitruvyan_core.aegis.intake.agents.cad_intake import CADIntakeAgent

# Foundation
from vitruvyan_core.core.foundation.persistence.postgres_agent import PostgresAgent

# Event Emitter
from vitruvyan_core.aegis.intake.event_emitter import IntakeEventEmitter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# FastAPI App Configuration
# ============================================
app = FastAPI(
    title="AEGIS INTAKE API",
    description="Evidence Pack ingestion service for Landscape & Geo data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================
# STARTUP: Create uploads directory
# ============================================
UPLOADS_DIR = "/app/uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)
logger.info(f"✅ Uploads directory ready: {UPLOADS_DIR}")

# CORS configuration (allow Next.js UI + Vercel deployments)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3003",
        "http://vitruvyan_aegis_ui:3000",
        "https://aegis.vitruvyan.com",
        "https://aegis-ui-seven.vercel.app",
        os.getenv("FRONTEND_URL", "http://localhost:3000")
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Redis + Event Emitter Initialization
# ============================================
# Connect to Redis Cognitive Bus
redis_host = os.getenv('REDIS_HOST', 'omni_redis')
redis_port = int(os.getenv('REDIS_PORT', 6379))

try:
    redis_client = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=0,
        decode_responses=True,
        socket_connect_timeout=5
    )
    redis_client.ping()
    logger.info(f"✅ Redis connected: {redis_host}:{redis_port}")
except Exception as e:
    logger.warning(f"⚠️ Redis connection failed: {e}. Events will be logged but not published.")
    redis_client = None

# Initialize REAL IntakeEventEmitter (replaces MockEventEmitter)
event_emitter = IntakeEventEmitter(
    redis_client=redis_client,
    postgres_agent=None  # Will be set per-request
)

# ============================================
# CAD/BIM Format Detection
# ============================================
CAD_FORMATS = ['.dxf', '.dwg', '.ifc', '.rvt', '.obj', '.fbx', '.3ds']
RASTER_FORMATS = ['.png', '.jpg', '.jpeg', '.tif', '.tiff', '.geotiff']

# ============================================
# Health Check Endpoint
# ============================================
@app.get("/health")
async def health_check():
    """Health check endpoint for Docker HEALTHCHECK"""
    try:
        # Verify PostgreSQL connection
        postgres = PostgresAgent()
        with postgres.connection.cursor() as cur:
            cur.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "service": "aegis_intake_api",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "postgresql": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# ============================================
# Landscape Intake Endpoint
# ============================================
@app.post("/api/intake/landscape")
async def ingest_landscape(
    file: UploadFile = File(..., description="Raster (PNG/JPG/GeoTIFF) or CAD/BIM file (DXF/IFC)"),
    map_url: Optional[str] = Form(None, description="Optional map URL (Mapbox, Google, OSM)"),
    description: Optional[str] = Form(None, description="Optional human description"),
    domain_family: str = Form("logistics", description="Domain family (default: logistics)"),
    run_id: Optional[str] = Form(None, description="Optional DSE run_id linkage")
):
    """
    Unified intake endpoint for raster images AND CAD/BIM files.
    
    Raster formats: PNG, JPG/JPEG, GeoTIFF (→ LandscapeIntakeAgent)
    CAD/BIM formats: DXF, DWG, IFC, RVT (→ CADIntakeAgent)
    
    Routing: Automatic based on file extension
    Returns: Evidence Pack JSON with integrity_hash, metadata, literal_text
    """
    temp_path = None
    try:
        # Determine file extension from content_type or filename
        original_filename = file.filename or "upload"
        file_ext = Path(original_filename).suffix.lower()
        
        # If no extension, detect from MIME type
        if not file_ext and file.content_type:
            ext_from_mime = mimetypes.guess_extension(file.content_type)
            if ext_from_mime:
                file_ext = ext_from_mime
                logger.info(f"🔍 No extension in filename, detected from MIME: {file.content_type} → {file_ext}")
        
        # Fallback extensions based on MIME type
        if not file_ext:
            mime_map = {
                "image/jpeg": ".jpg",
                "image/jpg": ".jpg",
                "image/png": ".png",
                "image/tiff": ".tiff",
                "image/tif": ".tif"
            }
            file_ext = mime_map.get(file.content_type, ".jpg")  # Default to .jpg for images
            logger.info(f"🔍 Using fallback extension: {file.content_type} → {file_ext}")
        
        # Generate safe filename with extension
        safe_filename = f"{Path(original_filename).stem or 'upload'}_{int(datetime.now().timestamp())}{file_ext}"
        temp_path = f"/app/uploads/{safe_filename}"
        
        logger.info(f"💾 Saving file: {original_filename} ({file.content_type}) → {safe_filename}")
        
        # Save uploaded file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"📝 INTAKE REQUEST: landscape | file={safe_filename} | size={os.path.getsize(temp_path)} bytes")
        
        # Detect file type and route to appropriate agent
        is_cad_file = file_ext in CAD_FORMATS
        is_raster_file = file_ext in RASTER_FORMATS
        
        # Build metadata dict with only non-None values
        metadata = {}
        if map_url:
            metadata["map_url"] = map_url
        if domain_family:
            metadata["domain_family"] = domain_family
        if description:
            metadata["human_description"] = description
        if run_id:
            metadata["run_id"] = run_id
        
        if is_cad_file:
            # Route to CADIntakeAgent
            logger.info(f"🏗️ CAD/BIM file detected: {file_ext} → Routing to CADIntakeAgent")
            agent = CADIntakeAgent(
                postgres_agent=PostgresAgent(),
                event_emitter=event_emitter
            )
            evidence_pack = agent.ingest(
                file_path=temp_path,
                source_type="document",
                metadata=metadata if metadata else None
            )
        elif is_raster_file:
            # Route to LandscapeIntakeAgent (existing behavior)
            logger.info(f"🗺️ Raster file detected: {file_ext} → Routing to LandscapeIntakeAgent")
            agent = LandscapeIntakeAgent(
                postgres_agent=PostgresAgent(),
                event_emitter=event_emitter
            )
            evidence_pack = agent.ingest(
                file_path=temp_path,
                source_type="image",
                metadata=metadata if metadata else None
            )
        else:
            # Unsupported format
            raise ValueError(f"Unsupported file format: {file_ext}. Supported: {RASTER_FORMATS + CAD_FORMATS}")
        
        logger.info(f"✅ INTAKE SUCCESS: evidence_id={evidence_pack['evidence_id']} | hash={evidence_pack['integrity']['hash'][:16]}...")
        
        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "message": "Landscape Evidence Pack created",
                "evidence_pack": evidence_pack
            }
        )
    
    except ValueError as e:
        # Format validation errors (unsupported file type, missing EXIF, etc.)
        logger.warning(f"⚠️ VALIDATION ERROR: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"❌ INTAKE FAILED: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    finally:
        # Cleanup temporary file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

# ============================================
# Geo Intake Endpoint
# ============================================
@app.post("/api/intake/geo")
async def ingest_geo(
    file: UploadFile = File(..., description="Geo-point data file (CSV, GeoJSON, GPX)"),
    description: Optional[str] = Form(None, description="Optional human description"),
    domain_family: str = Form("logistics", description="Domain family (default: logistics)"),
    run_id: Optional[str] = Form(None, description="Optional DSE run_id linkage")
):
    """
    Ingest geo-point data Evidence Pack.
    
    Supported formats: CSV, GeoJSON, GPX
    Data sources: GPS tracks, POI lists, event locations
    
    Returns: Evidence Pack JSON with integrity_hash, metadata, literal_text
    """
    temp_path = None
    try:
        # Save uploaded file to temporary location
        temp_path = f"/app/uploads/{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"📥 INTAKE REQUEST: geo | file={file.filename} | size={os.path.getsize(temp_path)} bytes")
        
        # Initialize GeoIntakeAgent
        agent = GeoIntakeAgent(
            postgres_agent=PostgresAgent(),
            event_emitter=event_emitter
        )
        
        # Ingest file (validates format, extracts points, persists to PostgreSQL)
        evidence_pack = agent.ingest(
            geo_path=temp_path,
            domain_family=domain_family,
            human_description=description
        )
        
        logger.info(f"✅ INTAKE SUCCESS: evidence_id={evidence_pack['evidence_id']} | points={evidence_pack['metadata']['point_count']}")
        
        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "message": "Geo Evidence Pack created",
                "evidence_pack": evidence_pack
            }
        )
    
    except ValueError as e:
        # Format validation errors
        logger.warning(f"⚠️ VALIDATION ERROR: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"❌ INTAKE FAILED: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    finally:
        # Cleanup temporary file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

# ============================================
# Evidence Pack Retrieval Endpoint
# ============================================
@app.get("/api/intake/evidence/{evidence_id}")
async def get_evidence_pack(evidence_id: str):
    """
    Retrieve Evidence Pack by evidence_id.
    
    Returns: Complete Evidence Pack JSON (from evidence_packs table)
    """
    try:
        postgres = PostgresAgent()
        
        with postgres.connection.cursor() as cur:
            cur.execute("""
                SELECT 
                    evidence_id,
                    schema_version,
                    timestamp_utc,
                    domain_family,
                    integrity_hash,
                    normalized_text,
                    metadata
                FROM evidence_packs
                WHERE evidence_id = %s
            """, (evidence_id,))
            
            row = cur.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail=f"Evidence Pack not found: {evidence_id}")
            
            evidence_pack = {
                "evidence_id": row[0],
                "schema_version": row[1],
                "timestamp_utc": row[2].isoformat() if row[2] else None,
                "domain_family": row[3],
                "integrity_hash": row[4],
                "normalized_text": row[5],
                "metadata": row[6]
            }
            
            return evidence_pack
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ RETRIEVAL FAILED: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ============================================
# Startup Event
# ============================================
@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("=" * 60)
    logger.info("🚀 AEGIS INTAKE API — Starting")
    logger.info("=" * 60)
    logger.info(f"📍 Endpoints:")
    logger.info(f"   POST /api/intake/landscape")
    logger.info(f"   POST /api/intake/geo")
    logger.info(f"   GET  /api/intake/evidence/:evidence_id")
    logger.info(f"   GET  /health")
    logger.info("=" * 60)
    logger.info(f"🔧 Configuration:")
    logger.info(f"   PostgreSQL: {os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '9432')}")
    logger.info(f"   Database: {os.getenv('POSTGRES_DB', 'vitruvyan_omni')}")
    logger.info("=" * 60)

# ============================================
# Pipeline Status Endpoint (NEW - Jan 13, 2026)
# ============================================
@app.get("/api/intake/pipeline")
async def get_pipeline_status(hours: int = 24, limit: int = 10):
    """
    Get AEGIS Pipeline status with recent fragments.
    
    Query params:
    - hours: Time window (default 24h)
    - limit: Max fragments to return (default 10)
    
    Returns:
    - events_count: Total events in timeframe
    - fragments: Recent fragments with processing status
    - embeddings_count: Total embeddings generated
    - vault_entries: Archived entries count
    """
    try:
        postgres = PostgresAgent()
        
        # Calculate time window
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        with postgres.connection.cursor() as cur:
            # Get total events count
            cur.execute("""
                SELECT COUNT(*) 
                FROM evidence_packs 
                WHERE created_utc >= %s
            """, (cutoff,))
            events_count = cur.fetchone()[0]
            
            # Get recent fragments with metadata
            cur.execute("""
                SELECT 
                    evidence_id,
                    (source_ref->>'domain_family') as domain_family,
                    created_utc,
                    normalized_text,
                    technical_metadata,
                    (integrity->>'hash') as integrity_hash
                FROM evidence_packs
                WHERE created_utc >= %s
                ORDER BY created_utc DESC
                LIMIT %s
            """, (cutoff, limit))
            
            fragments = []
            for row in cur.fetchall():
                metadata = row[4] or {}
                fragments.append({
                    "fragment_id": row[0],
                    "fragment_type": metadata.get("fragment_type", "unknown"),
                    "file_name": metadata.get("file_name", "unknown"),
                    "created_at": row[2].isoformat() if row[2] else None,
                    "hash": row[5],
                    "processing_status": "complete",  # All in DB are complete
                    "metadata": metadata
                })
            
            # Get embeddings count (from cognitive_entities if available)
            cur.execute("""
                SELECT COUNT(*) 
                FROM cognitive_entities 
                WHERE created_at >= %s
            """, (cutoff,))
            embeddings_count = cur.fetchone()[0] if cur.rowcount > 0 else 0
            
            # Get vault entries count
            cur.execute("""
                SELECT COUNT(*) 
                FROM evidence_packs 
                WHERE created_utc >= %s
            """, (cutoff,))
            vault_entries = cur.fetchone()[0]
        
        return {
            "status": "success",
            "events_count": events_count,
            "fragments_count": len(fragments),
            "recent_fragments": fragments,
            "embeddings_count": embeddings_count,
            "vault_entries": vault_entries,
            "time_window_hours": hours,
            "risk_score": 73,  # Mock for demo (TODO: calculate from DSE)
            "anomalies_detected": 12,  # Mock for demo
            "confidence": 0.85
        }
        
    except Exception as e:
        logger.error(f"Pipeline status error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# ENDPOINT: GET /api/intake/events (LiveStream)
# ============================================
@app.get("/api/intake/events")
async def get_intake_events(hours: int = 24):
    """
    Get recent intake events for LiveStreamCard.
    
    Query params:
    - hours: Time window (default 24h)
    
    Returns array of events with:
    - timestamp: ISO 8601
    - type: earthquake|upload|sensor|system
    - message: Event description
    - severity: low|medium|high
    - metadata: Additional context
    """
    try:
        postgres = PostgresAgent()
        
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        events = []
        
        with postgres.connection.cursor() as cur:
            # Get upload events from evidence_packs
            cur.execute("""
                SELECT 
                    created_utc,
                    evidence_id,
                    (source_ref->>'domain_family') as domain_family,
                    technical_metadata
                FROM evidence_packs
                WHERE created_utc >= %s
                ORDER BY created_utc DESC
            """, (cutoff,))
            
            for row in cur.fetchall():
                metadata = row[3] or {}
                file_name = metadata.get("file_name", "unknown")
                fragment_type = metadata.get("fragment_type", "unknown")
                
                events.append({
                    "timestamp": row[0].isoformat() if row[0] else None,
                    "type": "upload",
                    "message": f"Fragment ingested: {file_name} ({fragment_type})",
                    "severity": "low",
                    "metadata": {
                        "evidence_id": row[1],
                        "domain_family": row[2],
                        "file_name": file_name,
                        "fragment_type": fragment_type
                    }
                })
            
            # Get system events from cognitive_entities (if available)
            try:
                cur.execute("""
                    SELECT 
                        created_at,
                        entity_type,
                        entity_id
                    FROM cognitive_entities
                    WHERE created_at >= %s
                    ORDER BY created_at DESC
                    LIMIT 20
                """, (cutoff,))
                
                for row in cur.fetchall():
                    events.append({
                        "timestamp": row[0].isoformat() if row[0] else None,
                        "type": "system",
                        "message": f"Cognitive entity created: {row[1]}",
                        "severity": "low",
                        "metadata": {
                            "entity_id": row[2],
                            "entity_type": row[1]
                        }
                    })
            except Exception:
                pass  # cognitive_entities table may not exist
        
        # Sort all events by timestamp descending
        events.sort(key=lambda x: x["timestamp"] or "", reverse=True)
        
        return {
            "status": "success",
            "events": events,
            "total": len(events),
            "time_window_hours": hours
        }
        
    except Exception as e:
        logger.error(f"Events fetch error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Root Endpoint
# ============================================
@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "service": "AEGIS INTAKE API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "landscape": "POST /api/intake/landscape",
            "geo": "POST /api/intake/geo",
            "evidence": "GET /api/intake/evidence/:evidence_id"
        }
    }
