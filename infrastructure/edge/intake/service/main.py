"""
AEGIS Core — INTAKE API Backend
================================

FastAPI endpoints for Evidence Pack ingestion (multi-media).

Endpoints:
    POST /api/intake/document   - Ingest documents
    POST /api/intake/image      - Ingest images
    POST /api/intake/audio      - Ingest audio
    POST /api/intake/video      - Ingest videos
    POST /api/intake/cad        - Ingest CAD/BIM files
    POST /api/intake/landscape  - Ingest landscape/satellite imagery
    POST /api/intake/geo        - Ingest geospatial files
    GET  /api/intake/evidence/:evidence_id - Retrieve Evidence Pack
    GET  /health                - Health check

Architecture:
    File Upload (multipart/form-data) →
    Media-specific IntakeAgent →
    PostgreSQL (evidence_packs, landscape_evidence, geospatial_evidence) →
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
from typing import Optional
from datetime import datetime
import os
import logging
import shutil
import mimetypes
from pathlib import Path

# AEGIS INTAKE agents
from infrastructure.edge.intake.core.agents.landscape_intake import LandscapeIntakeAgent
from infrastructure.edge.intake.core.agents.geo_intake import GeoIntakeAgent
from infrastructure.edge.intake.core.agents.cad_intake import CADIntakeAgent
from infrastructure.edge.intake.core.agents.document_intake import DocumentIntakeAgent
from infrastructure.edge.intake.core.agents.image_intake import ImageIntakeAgent
from infrastructure.edge.intake.core.agents.audio_intake import AudioIntakeAgent
from infrastructure.edge.intake.core.agents.video_stream_intake import VideoStreamIntakeAgent

# Foundation
from vitruvyan_core.core.agents.postgres_agent import PostgresAgent
from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamBus

# Event Emitter
from infrastructure.edge.intake.core.event_emitter import IntakeEventEmitter

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
# StreamBus Initialization (Redis Streams only)
# ============================================
try:
    stream_bus = StreamBus(
        host=os.getenv("REDIS_HOST", "core_redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
    )
    logger.info("✅ StreamBus connected")
except Exception as e:
    logger.warning(f"⚠️ StreamBus connection failed: {e}. Events will be logged but not emitted.")
    stream_bus = None

# ============================================
# CAD/BIM Format Detection
# ============================================
CAD_FORMATS = ['.dxf', '.dwg', '.ifc', '.rvt', '.obj', '.fbx', '.3ds']
RASTER_FORMATS = ['.png', '.jpg', '.jpeg', '.tif', '.tiff', '.geotiff']
DOCUMENT_FORMATS = [".pdf", ".docx", ".md", ".txt", ".json", ".xml"]
AUDIO_FORMATS = [".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"]
VIDEO_FORMATS = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
GEO_FORMATS = [".kml", ".kmz", ".geojson", ".json", ".gpx", ".wkt", ".txt"]


def _default_postgres_host() -> str:
    # In containerized runtime we resolve DB through Docker network DNS.
    return "core_postgres" if os.path.exists("/.dockerenv") else "localhost"


def _build_postgres_agent() -> PostgresAgent:
    return PostgresAgent(
        host=os.getenv("POSTGRES_HOST", _default_postgres_host()),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "vitruvyan_core"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def _build_runtime_dependencies():
    postgres = _build_postgres_agent()
    emitter = IntakeEventEmitter(stream_bus=stream_bus, postgres_agent=postgres)
    return postgres, emitter


def _save_upload_file(upload: UploadFile, fallback_ext: str = ".bin") -> str:
    original_filename = upload.filename or "upload"
    file_ext = Path(original_filename).suffix.lower() or fallback_ext
    safe_filename = f"{Path(original_filename).stem or 'upload'}_{int(datetime.now().timestamp())}{file_ext}"
    target_path = f"{UPLOADS_DIR}/{safe_filename}"
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    return target_path

# ============================================
# Health Check Endpoint
# ============================================
@app.get("/health")
async def health_check():
    """Health check endpoint for Docker HEALTHCHECK"""
    postgres = None
    try:
        # Verify PostgreSQL connection
        postgres = _build_postgres_agent()
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
    finally:
        if postgres:
            postgres.close()

# ============================================
# Document Intake Endpoint
# ============================================
@app.post("/api/intake/document")
async def ingest_document(
    file: UploadFile = File(..., description="Document file (PDF, DOCX, MD, TXT, JSON, XML)"),
    sampling_policy_ref: Optional[str] = Form(None),
    correlation_id: Optional[str] = Form(None),
    chunking_strategy: str = Form("size"),
    chunk_size: int = Form(4000),
):
    temp_path = None
    postgres = None
    try:
        temp_path = _save_upload_file(file, fallback_ext=".txt")
        file_ext = Path(temp_path).suffix.lower()
        if file_ext not in DOCUMENT_FORMATS:
            raise ValueError(f"Unsupported document format: {file_ext}. Supported: {DOCUMENT_FORMATS}")

        postgres, emitter = _build_runtime_dependencies()
        agent = DocumentIntakeAgent(event_emitter=emitter, postgres_agent=postgres)
        evidence_ids = agent.ingest_document(
            source_path=Path(temp_path),
            sampling_policy_ref=sampling_policy_ref,
            chunking_strategy=chunking_strategy,
            chunk_size=chunk_size,
            correlation_id=correlation_id,
        )

        return {
            "status": "success",
            "message": f"Document ingested. Created {len(evidence_ids)} evidence chunks.",
            "evidence_ids": evidence_ids,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ DOCUMENT INTAKE FAILED: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        if postgres:
            postgres.close()


# ============================================
# Image Intake Endpoint
# ============================================
@app.post("/api/intake/image")
async def ingest_image(
    file: UploadFile = File(..., description="Image file (JPG, PNG, TIFF)"),
    sampling_policy_ref: Optional[str] = Form(None),
    correlation_id: Optional[str] = Form(None),
    enable_ocr: bool = Form(True),
    enable_caption: bool = Form(True),
):
    temp_path = None
    postgres = None
    try:
        temp_path = _save_upload_file(file, fallback_ext=".jpg")
        file_ext = Path(temp_path).suffix.lower()
        if file_ext not in RASTER_FORMATS:
            raise ValueError(f"Unsupported image format: {file_ext}. Supported: {RASTER_FORMATS}")

        postgres, emitter = _build_runtime_dependencies()
        agent = ImageIntakeAgent(event_emitter=emitter, postgres_agent=postgres)
        evidence_id = agent.ingest_image(
            source_path=Path(temp_path),
            sampling_policy_ref=sampling_policy_ref,
            enable_ocr=enable_ocr,
            enable_caption=enable_caption,
            correlation_id=correlation_id,
        )

        return {
            "status": "success",
            "message": "Image ingested successfully.",
            "evidence_ids": [evidence_id],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ IMAGE INTAKE FAILED: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        if postgres:
            postgres.close()


# ============================================
# Audio Intake Endpoint
# ============================================
@app.post("/api/intake/audio")
async def ingest_audio(
    file: UploadFile = File(..., description="Audio file (MP3, WAV, M4A, AAC, FLAC, OGG)"),
    sampling_policy_ref: Optional[str] = Form(None),
    correlation_id: Optional[str] = Form(None),
    chunk_duration_sec: int = Form(300),
):
    temp_path = None
    postgres = None
    try:
        temp_path = _save_upload_file(file, fallback_ext=".wav")
        file_ext = Path(temp_path).suffix.lower()
        if file_ext not in AUDIO_FORMATS:
            raise ValueError(f"Unsupported audio format: {file_ext}. Supported: {AUDIO_FORMATS}")

        postgres, emitter = _build_runtime_dependencies()
        agent = AudioIntakeAgent(event_emitter=emitter, postgres_agent=postgres)
        evidence_ids = agent.ingest_audio(
            source_path=Path(temp_path),
            sampling_policy_ref=sampling_policy_ref,
            chunk_duration_sec=chunk_duration_sec,
            correlation_id=correlation_id,
        )

        return {
            "status": "success",
            "message": f"Audio ingested. Created {len(evidence_ids)} evidence chunks.",
            "evidence_ids": evidence_ids,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ AUDIO INTAKE FAILED: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        if postgres:
            postgres.close()


# ============================================
# Video Intake Endpoint
# ============================================
@app.post("/api/intake/video")
async def ingest_video(
    file: UploadFile = File(..., description="Video file (MP4, AVI, MOV, MKV, WEBM)"),
    sampling_policy_ref: Optional[str] = Form(None),
    correlation_id: Optional[str] = Form(None),
    chunk_duration_sec: int = Form(60),
    enable_audio: bool = Form(True),
):
    temp_path = None
    postgres = None
    try:
        temp_path = _save_upload_file(file, fallback_ext=".mp4")
        file_ext = Path(temp_path).suffix.lower()
        if file_ext not in VIDEO_FORMATS:
            raise ValueError(f"Unsupported video format: {file_ext}. Supported: {VIDEO_FORMATS}")

        postgres, emitter = _build_runtime_dependencies()
        agent = VideoStreamIntakeAgent(event_emitter=emitter, postgres_agent=postgres)
        sampling_policy = {
            "frame_interval_sec": 1.0,
            "keyframes_only": False,
            "chunk_duration_sec": chunk_duration_sec,
            "policy_ref": sampling_policy_ref or "SAMPPOL-VIDEO-DEFAULT-V1",
        }
        evidence_ids = agent.ingest_video(
            source_path=Path(temp_path),
            sampling_policy=sampling_policy,
            enable_audio=enable_audio,
            correlation_id=correlation_id,
        )

        return {
            "status": "success",
            "message": f"Video ingested. Created {len(evidence_ids)} evidence chunks.",
            "evidence_ids": evidence_ids,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ VIDEO INTAKE FAILED: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        if postgres:
            postgres.close()


# ============================================
# CAD Intake Endpoint
# ============================================
@app.post("/api/intake/cad")
async def ingest_cad(
    file: UploadFile = File(..., description="CAD/BIM file (DXF, DWG, IFC, RVT, OBJ, FBX, 3DS)"),
    description: Optional[str] = Form(None),
    domain_family: str = Form("logistics"),
    run_id: Optional[str] = Form(None),
):
    temp_path = None
    postgres = None
    try:
        temp_path = _save_upload_file(file, fallback_ext=".dxf")
        file_ext = Path(temp_path).suffix.lower()
        if file_ext not in CAD_FORMATS:
            raise ValueError(f"Unsupported CAD format: {file_ext}. Supported: {CAD_FORMATS}")

        metadata = {"domain_family": domain_family}
        if description:
            metadata["human_description"] = description
        if run_id:
            metadata["run_id"] = run_id

        postgres, emitter = _build_runtime_dependencies()
        agent = CADIntakeAgent(event_emitter=emitter, postgres_agent=postgres)
        evidence_pack = agent.ingest(
            file_path=temp_path,
            source_type="document",
            metadata=metadata if metadata else None,
        )

        return {
            "status": "success",
            "message": "CAD/BIM ingested successfully.",
            "evidence_pack": evidence_pack,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ CAD INTAKE FAILED: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        if postgres:
            postgres.close()

# ============================================
# Landscape Intake Endpoint
# ============================================
@app.post("/api/intake/landscape")
async def ingest_landscape(
    file: UploadFile = File(..., description="Raster map/satellite file (PNG/JPG/GeoTIFF)"),
    map_url: Optional[str] = Form(None, description="Optional map URL (Mapbox, Google, OSM)"),
    description: Optional[str] = Form(None, description="Optional human description"),
    domain_family: str = Form("logistics", description="Domain family (default: logistics)"),
    run_id: Optional[str] = Form(None, description="Optional DSE run_id linkage")
):
    """
    Ingest landscape raster imagery and geospatial screenshots.
    """
    temp_path = None
    postgres = None
    try:
        fallback_ext = ".jpg"
        if file.content_type:
            fallback_ext = mimetypes.guess_extension(file.content_type) or fallback_ext

        temp_path = _save_upload_file(file, fallback_ext=fallback_ext)
        file_ext = Path(temp_path).suffix.lower()
        if file_ext not in RASTER_FORMATS:
            raise ValueError(f"Unsupported raster format: {file_ext}. Supported: {RASTER_FORMATS}")
        
        logger.info(f"📝 INTAKE REQUEST: landscape | file={Path(temp_path).name} | size={os.path.getsize(temp_path)} bytes")
        
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
        
        postgres, emitter = _build_runtime_dependencies()
        logger.info(f"🗺️ Raster file detected: {file_ext} → Routing to LandscapeIntakeAgent")
        agent = LandscapeIntakeAgent(
            postgres_agent=postgres,
            event_emitter=emitter
        )
        evidence_pack = agent.ingest(
            file_path=temp_path,
            source_type="image",
            metadata=metadata if metadata else None
        )
        
        evidence_hash = (
            evidence_pack.get("integrity", {}).get("hash")
            or evidence_pack.get("integrity", {}).get("evidence_hash")
            or evidence_pack.get("integrity", {}).get("hash_value")
            or "unknown"
        )
        logger.info(
            f"✅ INTAKE SUCCESS: evidence_id={evidence_pack['evidence_id']} | "
            f"hash={str(evidence_hash)[:16]}..."
        )
        
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
        if postgres:
            postgres.close()

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
    Ingest geospatial file into canonical Evidence Pack.
    
    Supported formats: KML, KMZ, GeoJSON, GPX, WKT
    
    Returns: Evidence Pack JSON with integrity_hash, metadata, literal_text
    """
    temp_path = None
    postgres = None
    try:
        temp_path = _save_upload_file(file, fallback_ext=".geojson")
        file_ext = Path(temp_path).suffix.lower()
        if file_ext not in GEO_FORMATS:
            raise ValueError(f"Unsupported geospatial format: {file_ext}. Supported: {GEO_FORMATS}")
        
        logger.info(f"📥 INTAKE REQUEST: geo | file={Path(temp_path).name} | size={os.path.getsize(temp_path)} bytes")
        
        postgres, emitter = _build_runtime_dependencies()

        # Initialize GeoIntakeAgent
        agent = GeoIntakeAgent(
            postgres_agent=postgres,
            event_emitter=emitter
        )
        
        metadata = {"domain_family": domain_family}
        if description:
            metadata["human_description"] = description
        if run_id:
            metadata["run_id"] = run_id

        # Ingest file (validates format, extracts points, persists to PostgreSQL)
        evidence_pack = agent.ingest(
            file_path=temp_path,
            source_type="document",
            metadata=metadata if metadata else None,
        )
        
        feature_count = evidence_pack.get("technical_metadata", {}).get("feature_count", "unknown")
        logger.info(
            f"✅ INTAKE SUCCESS: evidence_id={evidence_pack['evidence_id']} | "
            f"features={feature_count}"
        )
        
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
        if postgres:
            postgres.close()

# ============================================
# Evidence Pack Retrieval Endpoint
# ============================================
@app.get("/api/intake/evidence/{evidence_id}")
async def get_evidence_pack(evidence_id: str):
    """
    Retrieve Evidence Pack by evidence_id.
    
    Returns: Complete Evidence Pack JSON (from evidence_packs table)
    """
    postgres = None
    try:
        postgres = _build_postgres_agent()
        
        with postgres.connection.cursor() as cur:
            cur.execute("""
                SELECT 
                    evidence_id,
                    chunk_id,
                    schema_version,
                    created_utc,
                    source_ref,
                    normalized_text,
                    technical_metadata,
                    integrity,
                    sampling_policy_ref,
                    tags
                FROM evidence_packs
                WHERE evidence_id = %s
                ORDER BY chunk_id
            """, (evidence_id,))

            rows = cur.fetchall()
            if not rows:
                raise HTTPException(status_code=404, detail=f"Evidence Pack not found: {evidence_id}")

            chunks = []
            for row in rows:
                chunks.append(
                    {
                        "evidence_id": row[0],
                        "chunk_id": row[1],
                        "schema_version": row[2],
                        "created_utc": row[3].isoformat() if row[3] else None,
                        "source_ref": row[4],
                        "normalized_text": row[5],
                        "technical_metadata": row[6],
                        "integrity": row[7],
                        "sampling_policy_ref": row[8],
                        "tags": row[9],
                    }
                )

            return {"evidence_id": evidence_id, "chunks": chunks}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ RETRIEVAL FAILED: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if postgres:
            postgres.close()

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
    logger.info(f"   POST /api/intake/document")
    logger.info(f"   POST /api/intake/image")
    logger.info(f"   POST /api/intake/audio")
    logger.info(f"   POST /api/intake/video")
    logger.info(f"   POST /api/intake/cad")
    logger.info(f"   POST /api/intake/landscape")
    logger.info(f"   POST /api/intake/geo")
    logger.info(f"   GET  /api/intake/evidence/:evidence_id")
    logger.info(f"   GET  /health")
    logger.info("=" * 60)
    logger.info(f"🔧 Configuration:")
    logger.info(f"   PostgreSQL: {os.getenv('POSTGRES_HOST', _default_postgres_host())}:{os.getenv('POSTGRES_PORT', '5432')}")
    logger.info(f"   Database: {os.getenv('POSTGRES_DB', 'vitruvyan_core')}")
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
    postgres = None
    try:
        postgres = _build_postgres_agent()
        
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
                    COALESCE(
                        integrity->>'evidence_hash',
                        integrity->>'hash',
                        integrity->>'hash_value'
                    ) as integrity_hash
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
            embeddings_count = cur.fetchone()[0]
            
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
    finally:
        if postgres:
            postgres.close()

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
    postgres = None
    try:
        postgres = _build_postgres_agent()
        
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
    finally:
        if postgres:
            postgres.close()

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
            "document": "POST /api/intake/document",
            "image": "POST /api/intake/image",
            "audio": "POST /api/intake/audio",
            "video": "POST /api/intake/video",
            "cad": "POST /api/intake/cad",
            "landscape": "POST /api/intake/landscape",
            "geo": "POST /api/intake/geo",
            "evidence": "GET /api/intake/evidence/:evidence_id"
        }
    }
