"""HTTP routes for Edge Oculus Prime API service."""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from ..adapters.oculus_prime_adapter import OculusPrimeAdapter

logger = logging.getLogger(__name__)
router = APIRouter()
OCULUS_PRIME_PREFIX = "/api/oculus-prime"
LEGACY_INTAKE_PREFIX = "/api/intake"


def _get_adapter(request: Request) -> OculusPrimeAdapter:
    adapter = getattr(request.app.state, "oculus_prime_adapter", None)
    if adapter is None:
        adapter = getattr(request.app.state, "intake_adapter", None)
    if adapter is None:
        raise HTTPException(status_code=503, detail="Oculus Prime adapter unavailable")
    return adapter


@router.get("/health")
async def health_check(request: Request):
    adapter = _get_adapter(request)
    try:
        return adapter.health()
    except Exception as exc:
        logger.error("Health check failed: %s", exc)
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {exc}")


@router.post(f"{OCULUS_PRIME_PREFIX}/document")
@router.post(f"{LEGACY_INTAKE_PREFIX}/document", deprecated=True)
async def ingest_document(
    request: Request,
    file: UploadFile = File(..., description="Document file (PDF, DOCX, XLSX, PPTX, MD, TXT, JSON, XML)"),
    sampling_policy_ref: str | None = Form(None),
    correlation_id: str | None = Form(None),
    chunking_strategy: str = Form("size"),
    chunk_size: int = Form(4000),
    tenant_id: str | None = Form(None, description="Tenant ID for GDrive folder organization"),
    project_name: str | None = Form(None, description="Project name for GDrive subfolder"),
):
    adapter = _get_adapter(request)
    try:
        return adapter.ingest_document(
            file=file,
            sampling_policy_ref=sampling_policy_ref,
            correlation_id=correlation_id,
            chunking_strategy=chunking_strategy,
            chunk_size=chunk_size,
            tenant_id=tenant_id,
            project_name=project_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Document intake failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}")


@router.post(f"{OCULUS_PRIME_PREFIX}/image")
@router.post(f"{LEGACY_INTAKE_PREFIX}/image", deprecated=True)
async def ingest_image(
    request: Request,
    file: UploadFile = File(..., description="Image file (JPG, PNG, TIFF)"),
    sampling_policy_ref: str | None = Form(None),
    correlation_id: str | None = Form(None),
    enable_ocr: bool = Form(True),
    enable_caption: bool = Form(True),
):
    adapter = _get_adapter(request)
    try:
        return adapter.ingest_image(
            file=file,
            sampling_policy_ref=sampling_policy_ref,
            correlation_id=correlation_id,
            enable_ocr=enable_ocr,
            enable_caption=enable_caption,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Image intake failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}")


@router.post(f"{OCULUS_PRIME_PREFIX}/audio")
@router.post(f"{LEGACY_INTAKE_PREFIX}/audio", deprecated=True)
async def ingest_audio(
    request: Request,
    file: UploadFile = File(..., description="Audio file (MP3, WAV, M4A, AAC, FLAC, OGG)"),
    sampling_policy_ref: str | None = Form(None),
    correlation_id: str | None = Form(None),
    chunk_duration_sec: int = Form(300),
):
    adapter = _get_adapter(request)
    try:
        return adapter.ingest_audio(
            file=file,
            sampling_policy_ref=sampling_policy_ref,
            correlation_id=correlation_id,
            chunk_duration_sec=chunk_duration_sec,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Audio intake failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}")


@router.post(f"{OCULUS_PRIME_PREFIX}/video")
@router.post(f"{LEGACY_INTAKE_PREFIX}/video", deprecated=True)
async def ingest_video(
    request: Request,
    file: UploadFile = File(..., description="Video file (MP4, AVI, MOV, MKV, WEBM)"),
    sampling_policy_ref: str | None = Form(None),
    correlation_id: str | None = Form(None),
    chunk_duration_sec: int = Form(60),
    enable_audio: bool = Form(True),
):
    adapter = _get_adapter(request)
    try:
        return adapter.ingest_video(
            file=file,
            sampling_policy_ref=sampling_policy_ref,
            correlation_id=correlation_id,
            chunk_duration_sec=chunk_duration_sec,
            enable_audio=enable_audio,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Video intake failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}")


@router.post(f"{OCULUS_PRIME_PREFIX}/cad")
@router.post(f"{LEGACY_INTAKE_PREFIX}/cad", deprecated=True)
async def ingest_cad(
    request: Request,
    file: UploadFile = File(..., description="CAD/BIM file (DXF, DWG, IFC, RVT, OBJ, FBX, 3DS)"),
    description: str | None = Form(None),
    domain_family: str = Form("logistics"),
    run_id: str | None = Form(None),
):
    adapter = _get_adapter(request)
    try:
        return adapter.ingest_cad(
            file=file,
            description=description,
            domain_family=domain_family,
            run_id=run_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("CAD intake failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}")


@router.post(f"{OCULUS_PRIME_PREFIX}/landscape")
@router.post(f"{LEGACY_INTAKE_PREFIX}/landscape", deprecated=True)
async def ingest_landscape(
    request: Request,
    file: UploadFile = File(..., description="Raster map/satellite file (PNG/JPG/GeoTIFF)"),
    map_url: str | None = Form(None),
    description: str | None = Form(None),
    domain_family: str = Form("logistics"),
    run_id: str | None = Form(None),
):
    adapter = _get_adapter(request)
    try:
        result = adapter.ingest_landscape(
            file=file,
            map_url=map_url,
            description=description,
            domain_family=domain_family,
            run_id=run_id,
        )
        return JSONResponse(status_code=201, content=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Landscape intake failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}")


@router.post(f"{OCULUS_PRIME_PREFIX}/geo")
@router.post(f"{LEGACY_INTAKE_PREFIX}/geo", deprecated=True)
async def ingest_geo(
    request: Request,
    file: UploadFile = File(..., description="Geo-point data file (CSV, GeoJSON, GPX)"),
    description: str | None = Form(None),
    domain_family: str = Form("logistics"),
    run_id: str | None = Form(None),
):
    adapter = _get_adapter(request)
    try:
        result = adapter.ingest_geo(
            file=file,
            description=description,
            domain_family=domain_family,
            run_id=run_id,
        )
        return JSONResponse(status_code=201, content=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Geo intake failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}")


@router.get(f"{OCULUS_PRIME_PREFIX}/evidence/{{evidence_id}}")
@router.get(f"{LEGACY_INTAKE_PREFIX}/evidence/{{evidence_id}}", deprecated=True)
async def get_evidence_pack(request: Request, evidence_id: str):
    adapter = _get_adapter(request)
    try:
        return adapter.get_evidence_pack(evidence_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Evidence retrieval failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}")


@router.get(f"{OCULUS_PRIME_PREFIX}/pipeline")
@router.get(f"{LEGACY_INTAKE_PREFIX}/pipeline", deprecated=True)
async def get_pipeline_status(request: Request, hours: int = 24, limit: int = 10):
    adapter = _get_adapter(request)
    try:
        return adapter.get_pipeline_status(hours=hours, limit=limit)
    except Exception as exc:
        logger.error("Pipeline status failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(f"{OCULUS_PRIME_PREFIX}/events")
@router.get(f"{LEGACY_INTAKE_PREFIX}/events", deprecated=True)
async def get_oculus_prime_events(request: Request, hours: int = 24):
    adapter = _get_adapter(request)
    try:
        return adapter.get_oculus_prime_events(hours=hours)
    except Exception as exc:
        logger.error("Oculus Prime events failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/")
async def root(request: Request):
    return _get_adapter(request).root()
