"""
GDrive Ingest & Repository Routes — Edge Oculus Prime
=================================================================
Endpoints for:
  - Ingesting files FROM Google Drive into the evidence pipeline
  - Browsing/managing the GDrive document repository (archived originals)

POST /oculus/v2/gdrive/ingest   — ingest a single file by Drive file_id
POST /oculus/v2/gdrive/folder   — list + ingest all files in a Drive folder
GET  /oculus/v2/gdrive/status   — check if GDrive adapters are configured
GET  /oculus/v2/gdrive/repo/browse — browse archived documents by tenant/project

> **Last updated**: Mar 2, 2026 19:00 UTC
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Body, HTTPException, Request
from pydantic import BaseModel, Field

from ..adapters.gdrive_adapter import GDriveAdapter
from ..adapters.oculus_prime_adapter import OculusPrimeAdapter

logger = logging.getLogger(__name__)
gdrive_router = APIRouter(prefix="/oculus/v2/gdrive", tags=["gdrive"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class GDriveIngestRequest(BaseModel):
    file_id: str = Field(..., description="Google Drive file ID")
    correlation_id: Optional[str] = Field(None, description="Optional correlation ID for tracing")
    chunking_strategy: str = Field("size", description="Chunking strategy: size | semantic")
    chunk_size: int = Field(4000, ge=256, le=32768, description="Chunk size in chars")


class GDriveFolderIngestRequest(BaseModel):
    folder_id: str = Field(..., description="Google Drive folder ID")
    correlation_id: Optional[str] = Field(None, description="Optional correlation ID")
    chunking_strategy: str = Field("size")
    chunk_size: int = Field(4000, ge=256, le=32768)
    max_files: int = Field(50, ge=1, le=200, description="Max files to ingest per call")
    ingest: bool = Field(True, description="False = dry-run (list only, no ingest)")
    exclude_extensions: List[str] = Field(
        default=[".drawio"],
        description="File extensions to skip (e.g. ['.drawio', '.tmp'])",
    )


class GDriveIngestResult(BaseModel):
    file_id: str
    filename: str
    mime_type: str
    ingest_method: str
    status: str
    evidence_ids: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class GDriveFolderResponse(BaseModel):
    folder_id: str
    total_files: int
    ingested: int
    failed: int
    excluded: int = 0
    results: List[GDriveIngestResult]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_gdrive(request: Request) -> GDriveAdapter:
    adapter = getattr(request.app.state, "gdrive_adapter", None)
    if adapter is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "GDrive adapter not configured. "
                "Set GDRIVE_CREDENTIALS_FILE and GDRIVE_SHARED_FOLDER_ID env vars."
            ),
        )
    return adapter


def _get_oculus(request: Request) -> OculusPrimeAdapter:
    adapter = getattr(request.app.state, "oculus_prime_adapter", None)
    if adapter is None:
        raise HTTPException(status_code=503, detail="Oculus Prime adapter unavailable.")
    return adapter


def _do_ingest(
    gdrive: GDriveAdapter,
    oculus: OculusPrimeAdapter,
    file_id: str,
    correlation_id: Optional[str],
    chunking_strategy: str,
    chunk_size: int,
    meta_hint=None,  # GDriveFileMetadata pre-fetched from list_folder
) -> GDriveIngestResult:
    """Download one file from GDrive and push into Oculus Prime."""
    try:
        meta, upload = gdrive.download_as_upload(file_id=file_id)
        method_name = gdrive.resolve_ingest_method(meta.mime_type)
        ingest_fn = getattr(oculus, method_name)

        # ingest_document / ingest_image / ingest_audio / ingest_video
        # They all accept (file, sampling_policy_ref, correlation_id, ...)
        # but with slightly different signatures — use common kwargs
        if method_name == "ingest_document":
            result = ingest_fn(
                file=upload,
                sampling_policy_ref=None,
                correlation_id=correlation_id,
                chunking_strategy=chunking_strategy,
                chunk_size=chunk_size,
            )
        else:
            # image / audio / video / cad / landscape / geo all take
            # (file, sampling_policy_ref, correlation_id)
            result = ingest_fn(
                file=upload,
                sampling_policy_ref=None,
                correlation_id=correlation_id,
            )

        return GDriveIngestResult(
            file_id=file_id,
            filename=meta.name,
            mime_type=meta.mime_type,
            ingest_method=method_name,
            status="success",
            evidence_ids=result.get("evidence_ids", []),
        )

    except Exception as exc:
        logger.error("GDrive ingest failed for file_id=%s: %s", file_id, exc)
        return GDriveIngestResult(
            file_id=file_id,
            filename=meta_hint.name if meta_hint else "",
            mime_type=meta_hint.mime_type if meta_hint else "",
            ingest_method="skipped" if meta_hint and meta_hint.mime_type in ("application/vnd.google-apps.folder", "application/vnd.google-apps.shortcut") else "unknown",
            status="skipped" if meta_hint and meta_hint.mime_type in ("application/vnd.google-apps.folder", "application/vnd.google-apps.shortcut") else "error",
            error=str(exc),
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@gdrive_router.get("/status")
async def gdrive_status(request: Request):
    """Check whether the GDrive adapters are configured and available."""
    # Ingestion adapter (readonly)
    ingestion = getattr(request.app.state, "gdrive_adapter", None)
    # Repository adapter (readwrite)
    repo = getattr(request.app.state, "gdrive_repo", None)

    result = {
        "ingestion": {"enabled": ingestion is not None},
        "repository": {"enabled": repo is not None},
    }

    if ingestion is None:
        import os
        creds_file = os.environ.get("GDRIVE_CREDENTIALS_FILE", "").strip()
        if not creds_file:
            result["ingestion"]["reason"] = "GDRIVE_CREDENTIALS_FILE not set"
        elif not os.path.isfile(creds_file):
            result["ingestion"]["reason"] = f"credentials file not found: {creds_file}"
    else:
        result["ingestion"]["scopes"] = GDriveAdapter.SCOPES_READONLY

    if repo is None:
        import os
        reason = "GDRIVE_REPO_CREDENTIALS_FILE not set (falls back to GDRIVE_CREDENTIALS_FILE)"
        root_id = os.environ.get("GDRIVE_REPO_ROOT_FOLDER_ID", "").strip()
        if not root_id:
            reason += " | GDRIVE_REPO_ROOT_FOLDER_ID not set"
        result["repository"]["reason"] = reason
    else:
        import os
        result["repository"]["scopes"] = GDriveAdapter.SCOPES_READWRITE
        result["repository"]["root_folder_id"] = os.environ.get("GDRIVE_REPO_ROOT_FOLDER_ID", "")

    return result


@gdrive_router.post("/ingest", response_model=GDriveIngestResult)
async def gdrive_ingest_file(
    request: Request,
    body: GDriveIngestRequest,
):
    """
    Download a single Google Drive file and ingest it into the Oculus Prime pipeline.

    Steps:
        1. Fetch file metadata from Drive
        2. Download bytes (auto-export Google Workspace → Office format)
        3. Resolve ingest method by MIME type
        4. Push through OculusPrimeAdapter
        5. Returns evidence_ids emitted on Redis Streams
    """
    gdrive = _get_gdrive(request)
    oculus = _get_oculus(request)
    result = _do_ingest(
        gdrive=gdrive,
        oculus=oculus,
        file_id=body.file_id,
        correlation_id=body.correlation_id,
        chunking_strategy=body.chunking_strategy,
        chunk_size=body.chunk_size,
    )
    if result.status == "error":
        raise HTTPException(status_code=422, detail=result.error)
    return result


@gdrive_router.post("/folder", response_model=GDriveFolderResponse)
async def gdrive_ingest_folder(
    request: Request,
    body: GDriveFolderIngestRequest,
):
    """
    List a Google Drive folder and ingest all contained files.

    Files are processed sequentially (rate-limit safe). Non-fatal errors
    are captured per-file and included in the response.
    """
    gdrive = _get_gdrive(request)
    oculus = _get_oculus(request)

    try:
        files = gdrive.list_folder(folder_id=body.folder_id, page_size=body.max_files)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to list folder: {exc}")

    import os as _os
    results: List[GDriveIngestResult] = []
    for file_meta in files[: body.max_files]:
        # Extension filter
        ext = _os.path.splitext(file_meta.name)[1].lower()
        if ext in [e.lower() for e in body.exclude_extensions]:
            results.append(GDriveIngestResult(
                file_id=file_meta.file_id,
                filename=file_meta.name,
                mime_type=file_meta.mime_type,
                ingest_method="excluded",
                status="excluded",
                evidence_ids=[],
            ))
            logger.info("GDrive: skipping %s (extension %s excluded)", file_meta.name, ext)
            continue

        if not body.ingest:
            # Dry-run: list only, no download/ingest
            results.append(GDriveIngestResult(
                file_id=file_meta.file_id,
                filename=file_meta.name,
                mime_type=file_meta.mime_type,
                ingest_method=gdrive.resolve_ingest_method(file_meta.mime_type),
                status="listed",
                evidence_ids=[],
            ))
        else:
            res = _do_ingest(
                gdrive=gdrive,
                oculus=oculus,
                file_id=file_meta.file_id,
                correlation_id=body.correlation_id,
                chunking_strategy=body.chunking_strategy,
                chunk_size=body.chunk_size,
                meta_hint=file_meta,
            )
            results.append(res)

    ingested = sum(1 for r in results if r.status == "success")
    failed = sum(1 for r in results if r.status == "error")
    excluded = sum(1 for r in results if r.status == "excluded")
    logger.info(
        "GDrive folder=%s ingested=%d failed=%d excluded=%d total=%d",
        body.folder_id, ingested, failed, excluded, len(files),
    )
    return GDriveFolderResponse(
        folder_id=body.folder_id,
        total_files=len(files),
        ingested=ingested,
        failed=failed,
        excluded=excluded,
        results=results,
    )


# ── Repository endpoints ─────────────────────────────────────────────────────

def _get_repo(request: Request):
    """Get the GDrive repository adapter (readwrite)."""
    repo = getattr(request.app.state, "gdrive_repo", None)
    if repo is None:
        raise HTTPException(
            status_code=503,
            detail="GDrive Repository not configured. Set GDRIVE_REPO_ROOT_FOLDER_ID.",
        )
    return repo


@gdrive_router.get("/repo/browse")
async def repo_browse(
    request: Request,
    tenant_id: str = None,
    project_name: str = None,
):
    """
    Browse the GDrive document repository.

    - No params → list tenant folders (top level)
    - tenant_id → list project folders for that tenant
    - tenant_id + project_name → list files in that project
    """
    import os

    repo = _get_repo(request)
    root_id = os.environ.get("GDRIVE_REPO_ROOT_FOLDER_ID", "").strip()
    if not root_id:
        raise HTTPException(status_code=503, detail="GDRIVE_REPO_ROOT_FOLDER_ID not set")

    try:
        if not tenant_id:
            # List tenant folders
            folders = repo.list_folder(root_id, include_folders=True)
            return {
                "level": "tenants",
                "root_folder_id": root_id,
                "items": [
                    {"name": f.name, "id": f.file_id, "type": "folder"}
                    for f in folders
                    if f.mime_type == "application/vnd.google-apps.folder"
                ],
            }

        # Resolve tenant folder
        tenant_folder_id = repo.find_folder(tenant_id, root_id)
        if not tenant_folder_id:
            return {"level": "projects", "tenant_id": tenant_id, "items": [], "note": "Tenant folder not found"}

        if not project_name:
            # List project folders
            items = repo.list_folder(tenant_folder_id, include_folders=True)
            return {
                "level": "projects",
                "tenant_id": tenant_id,
                "items": [
                    {
                        "name": f.name,
                        "id": f.file_id,
                        "type": "folder" if f.mime_type == "application/vnd.google-apps.folder" else "file",
                        "mime_type": f.mime_type,
                        "size": f.size,
                        "modified": f.modified_time,
                    }
                    for f in items
                ],
            }

        # List files in project folder
        project_folder_id = repo.find_folder(project_name, tenant_folder_id)
        if not project_folder_id:
            return {"level": "files", "tenant_id": tenant_id, "project": project_name, "items": [], "note": "Project folder not found"}

        files = repo.list_folder(project_folder_id)
        return {
            "level": "files",
            "tenant_id": tenant_id,
            "project": project_name,
            "items": [
                {
                    "name": f.name,
                    "id": f.file_id,
                    "mime_type": f.mime_type,
                    "size": f.size,
                    "modified": f.modified_time,
                }
                for f in files
            ],
        }
    except Exception as exc:
        logger.error("GDrive repo browse failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"GDrive error: {exc}")
