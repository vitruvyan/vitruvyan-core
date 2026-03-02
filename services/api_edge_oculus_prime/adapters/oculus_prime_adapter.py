"""Business adapter for Edge Oculus Prime API endpoints."""

from __future__ import annotations

import logging
import mimetypes
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException, UploadFile

from infrastructure.edge.oculus_prime.core.agents.audio_intake import AudioIntakeAgent
from infrastructure.edge.oculus_prime.core.agents.cad_intake import CADIntakeAgent
from infrastructure.edge.oculus_prime.core.agents.document_intake import DocumentIntakeAgent
from infrastructure.edge.oculus_prime.core.agents.geo_intake import GeoIntakeAgent
from infrastructure.edge.oculus_prime.core.agents.image_intake import ImageIntakeAgent
from infrastructure.edge.oculus_prime.core.agents.landscape_intake import LandscapeIntakeAgent
from infrastructure.edge.oculus_prime.core.agents.video_stream_intake import VideoStreamIntakeAgent

from .persistence import OculusPrimePersistence
from .runtime import build_runtime_dependencies
from ..config import OculusPrimeSettings

logger = logging.getLogger(__name__)


class OculusPrimeAdapter:
    """Delegates API operations to core oculus prime agents and persistence adapters."""

    def __init__(self, settings: OculusPrimeSettings, stream_bus: Any = None, gdrive_repo=None):
        self.settings = settings
        self.stream_bus = stream_bus
        self.persistence = OculusPrimePersistence(settings=settings)
        self.gdrive_repo = gdrive_repo  # GDriveAdapter in readwrite mode (optional)

    def ensure_uploads_dir(self) -> None:
        os.makedirs(self.settings.uploads_dir, exist_ok=True)

    def _save_upload_file(self, upload: UploadFile, fallback_ext: str = ".bin") -> str:
        original_filename = upload.filename or "upload"
        file_ext = Path(original_filename).suffix.lower() or fallback_ext
        safe_filename = f"{Path(original_filename).stem or 'upload'}_{int(datetime.now().timestamp())}{file_ext}"
        target_path = f"{self.settings.uploads_dir}/{safe_filename}"
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
        return target_path

    def _archive_to_gdrive(
        self,
        local_path: str,
        tenant_id: Optional[str] = None,
        project_name: Optional[str] = None,
        original_filename: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Upload the original file to GDrive repository (if configured).
        Folder structure: ROOT / {tenant_id} / {project_name} / filename
        Returns {"file_id": ..., "web_link": ...} or None.
        """
        if not self.gdrive_repo:
            return None

        root_folder_id = os.environ.get("GDRIVE_REPO_ROOT_FOLDER_ID", "").strip()
        if not root_folder_id:
            logger.debug("GDrive repo: GDRIVE_REPO_ROOT_FOLDER_ID not set — skipping archive.")
            return None

        try:
            # Build folder hierarchy: root / tenant / project
            segments = []
            if tenant_id:
                segments.append(tenant_id)
            if project_name:
                segments.append(project_name)

            if segments:
                target_folder_id = self.gdrive_repo.resolve_path(root_folder_id, *segments)
            else:
                target_folder_id = root_folder_id

            file_id = self.gdrive_repo.upload_file(
                local_path=local_path,
                folder_id=target_folder_id,
                filename=original_filename,
            )
            web_link = self.gdrive_repo.get_web_link(file_id)
            logger.info(
                "Archived to GDrive: %s → %s/%s (file_id=%s)",
                original_filename or os.path.basename(local_path),
                tenant_id or "root",
                project_name or "",
                file_id,
            )
            return {"file_id": file_id, "web_link": web_link}
        except Exception as exc:
            logger.error("GDrive archive failed (non-blocking): %s", exc)
            return None

    def health(self) -> dict[str, Any]:
        return self.persistence.health()

    def ingest_document(
        self,
        file: UploadFile,
        sampling_policy_ref: str | None,
        correlation_id: str | None,
        chunking_strategy: str,
        chunk_size: int,
        tenant_id: str | None = None,
        project_name: str | None = None,
    ) -> dict[str, Any]:
        temp_path = None
        postgres = None
        try:
            temp_path = self._save_upload_file(file, fallback_ext=".txt")
            file_ext = Path(temp_path).suffix.lower()
            if file_ext not in self.settings.document_formats:
                raise ValueError(
                    f"Unsupported document format: {file_ext}. Supported: {list(self.settings.document_formats)}"
                )

            # Archive original to GDrive repository (non-blocking)
            gdrive_info = self._archive_to_gdrive(
                local_path=temp_path,
                tenant_id=tenant_id,
                project_name=project_name,
                original_filename=file.filename,
            )

            postgres, emitter = build_runtime_dependencies(self.settings, self.stream_bus)
            agent = DocumentIntakeAgent(event_emitter=emitter, postgres_agent=postgres)
            evidence_ids = agent.ingest_document(
                source_path=Path(temp_path),
                sampling_policy_ref=sampling_policy_ref,
                chunking_strategy=chunking_strategy,
                chunk_size=chunk_size,
                correlation_id=correlation_id,
                tenant_id=tenant_id,
                project_name=project_name,
            )
            result = {
                "status": "success",
                "message": f"Document ingested. Created {len(evidence_ids)} evidence chunks.",
                "evidence_ids": evidence_ids,
            }
            if gdrive_info:
                result["gdrive"] = gdrive_info
            return result
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            if postgres:
                postgres.close()

    def ingest_image(
        self,
        file: UploadFile,
        sampling_policy_ref: str | None,
        correlation_id: str | None,
        enable_ocr: bool,
        enable_caption: bool,
    ) -> dict[str, Any]:
        temp_path = None
        postgres = None
        try:
            temp_path = self._save_upload_file(file, fallback_ext=".jpg")
            file_ext = Path(temp_path).suffix.lower()
            if file_ext not in self.settings.image_formats:
                raise ValueError(f"Unsupported image format: {file_ext}. Supported: {list(self.settings.image_formats)}")

            postgres, emitter = build_runtime_dependencies(self.settings, self.stream_bus)
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
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            if postgres:
                postgres.close()

    def ingest_audio(
        self,
        file: UploadFile,
        sampling_policy_ref: str | None,
        correlation_id: str | None,
        chunk_duration_sec: int,
    ) -> dict[str, Any]:
        temp_path = None
        postgres = None
        try:
            temp_path = self._save_upload_file(file, fallback_ext=".wav")
            file_ext = Path(temp_path).suffix.lower()
            if file_ext not in self.settings.audio_formats:
                raise ValueError(f"Unsupported audio format: {file_ext}. Supported: {list(self.settings.audio_formats)}")

            postgres, emitter = build_runtime_dependencies(self.settings, self.stream_bus)
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
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            if postgres:
                postgres.close()

    def ingest_video(
        self,
        file: UploadFile,
        sampling_policy_ref: str | None,
        correlation_id: str | None,
        chunk_duration_sec: int,
        enable_audio: bool,
    ) -> dict[str, Any]:
        temp_path = None
        postgres = None
        try:
            temp_path = self._save_upload_file(file, fallback_ext=".mp4")
            file_ext = Path(temp_path).suffix.lower()
            if file_ext not in self.settings.video_formats:
                raise ValueError(f"Unsupported video format: {file_ext}. Supported: {list(self.settings.video_formats)}")

            postgres, emitter = build_runtime_dependencies(self.settings, self.stream_bus)
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
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            if postgres:
                postgres.close()

    def ingest_cad(
        self,
        file: UploadFile,
        description: str | None,
        domain_family: str,
        run_id: str | None,
    ) -> dict[str, Any]:
        temp_path = None
        postgres = None
        try:
            temp_path = self._save_upload_file(file, fallback_ext=".dxf")
            file_ext = Path(temp_path).suffix.lower()
            if file_ext not in self.settings.cad_formats:
                raise ValueError(f"Unsupported CAD format: {file_ext}. Supported: {list(self.settings.cad_formats)}")

            metadata = {"domain_family": domain_family}
            if description:
                metadata["human_description"] = description
            if run_id:
                metadata["run_id"] = run_id

            postgres, emitter = build_runtime_dependencies(self.settings, self.stream_bus)
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
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            if postgres:
                postgres.close()

    def ingest_landscape(
        self,
        file: UploadFile,
        map_url: str | None,
        description: str | None,
        domain_family: str,
        run_id: str | None,
    ) -> dict[str, Any]:
        temp_path = None
        postgres = None
        try:
            fallback_ext = ".jpg"
            if file.content_type:
                fallback_ext = mimetypes.guess_extension(file.content_type) or fallback_ext

            temp_path = self._save_upload_file(file, fallback_ext=fallback_ext)
            file_ext = Path(temp_path).suffix.lower()
            if file_ext not in self.settings.image_formats:
                raise ValueError(f"Unsupported raster format: {file_ext}. Supported: {list(self.settings.image_formats)}")

            metadata: dict[str, Any] = {}
            if map_url:
                metadata["map_url"] = map_url
            if domain_family:
                metadata["domain_family"] = domain_family
            if description:
                metadata["human_description"] = description
            if run_id:
                metadata["run_id"] = run_id

            postgres, emitter = build_runtime_dependencies(self.settings, self.stream_bus)
            agent = LandscapeIntakeAgent(postgres_agent=postgres, event_emitter=emitter)
            evidence_pack = agent.ingest(
                file_path=temp_path,
                source_type="image",
                metadata=metadata if metadata else None,
            )
            return {
                "status": "success",
                "message": "Landscape Evidence Pack created",
                "evidence_pack": evidence_pack,
            }
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            if postgres:
                postgres.close()

    def ingest_geo(
        self,
        file: UploadFile,
        description: str | None,
        domain_family: str,
        run_id: str | None,
    ) -> dict[str, Any]:
        temp_path = None
        postgres = None
        try:
            temp_path = self._save_upload_file(file, fallback_ext=".geojson")
            file_ext = Path(temp_path).suffix.lower()
            if file_ext not in self.settings.geo_formats:
                raise ValueError(
                    f"Unsupported geospatial format: {file_ext}. Supported: {list(self.settings.geo_formats)}"
                )

            metadata: dict[str, Any] = {"domain_family": domain_family}
            if description:
                metadata["human_description"] = description
            if run_id:
                metadata["run_id"] = run_id

            postgres, emitter = build_runtime_dependencies(self.settings, self.stream_bus)
            agent = GeoIntakeAgent(postgres_agent=postgres, event_emitter=emitter)
            evidence_pack = agent.ingest(
                file_path=temp_path,
                source_type="document",
                metadata=metadata if metadata else None,
            )
            return {
                "status": "success",
                "message": "Geo Evidence Pack created",
                "evidence_pack": evidence_pack,
            }
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            if postgres:
                postgres.close()

    def get_evidence_pack(self, evidence_id: str) -> dict[str, Any]:
        chunks = self.persistence.fetch_evidence_chunks(evidence_id)
        if not chunks:
            raise HTTPException(status_code=404, detail=f"Evidence Pack not found: {evidence_id}")
        return {"evidence_id": evidence_id, "chunks": chunks}

    def get_pipeline_status(self, hours: int = 24, limit: int = 10) -> dict[str, Any]:
        return self.persistence.fetch_pipeline_status(hours=hours, limit=limit)

    def get_oculus_prime_events(self, hours: int = 24) -> dict[str, Any]:
        return self.persistence.fetch_oculus_prime_events(hours=hours)

    def get_intake_events(self, hours: int = 24) -> dict[str, Any]:
        # Legacy method name retained for compatibility.
        return self.get_oculus_prime_events(hours=hours)

    def root(self) -> dict[str, Any]:
        return {
            "service": "Vitruvyan OCULUS PRIME API",
            "version": self.settings.service_version,
            "status": "operational",
            "docs": "/docs",
            "endpoints": {
                "document": "POST /api/oculus-prime/document",
                "image": "POST /api/oculus-prime/image",
                "audio": "POST /api/oculus-prime/audio",
                "video": "POST /api/oculus-prime/video",
                "cad": "POST /api/oculus-prime/cad",
                "landscape": "POST /api/oculus-prime/landscape",
                "geo": "POST /api/oculus-prime/geo",
                "evidence": "GET /api/oculus-prime/evidence/:evidence_id",
            },
        }


# Legacy alias kept to avoid breaking existing imports.
IntakeAdapter = OculusPrimeAdapter
