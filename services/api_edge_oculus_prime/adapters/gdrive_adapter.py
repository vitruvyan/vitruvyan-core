"""
GDrive Adapter — Edge Oculus Prime (AICOMSEC)
=============================================
Downloads files from Google Drive and routes them through the Oculus Prime
intake pipeline.

Authentication: service account JSON pointed to by GDRIVE_CREDENTIALS_FILE.
If the env var is absent, the adapter is disabled (graceful degradation).

LIVELLO 2 — I/O adapter, no domain logic.

> **Last updated**: Feb 27, 2026 17:00 UTC
"""

from __future__ import annotations

import io
import logging
import mimetypes
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# MIME → Oculus Prime ingest method name
_MIME_TO_INGEST_METHOD: Dict[str, str] = {
    # Documents
    "application/pdf": "ingest_document",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "ingest_document",
    "application/msword": "ingest_document",
    "application/vnd.ms-excel": "ingest_document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "ingest_document",
    "text/plain": "ingest_document",
    "text/csv": "ingest_document",
    "application/json": "ingest_document",
    "application/xml": "ingest_document",
    "text/xml": "ingest_document",
    "text/markdown": "ingest_document",
    # Images
    "image/jpeg": "ingest_image",
    "image/png": "ingest_image",
    "image/tiff": "ingest_image",
    "image/gif": "ingest_image",
    # Audio
    "audio/mpeg": "ingest_audio",
    "audio/wav": "ingest_audio",
    "audio/ogg": "ingest_audio",
    # Video
    "video/mp4": "ingest_video",
    "video/mpeg": "ingest_video",
    "video/quicktime": "ingest_video",
    # CAD / BIM
    "application/dxf": "ingest_cad",
    "application/octet-stream": "ingest_document",  # fallback
    # Google Workspace exports
    "application/vnd.google-apps.document": "ingest_document",
    "application/vnd.google-apps.spreadsheet": "ingest_document",
    "application/vnd.google-apps.presentation": "ingest_document",
}

_GDRIVE_EXPORT_FORMATS: Dict[str, str] = {
    "application/vnd.google-apps.document": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.google-apps.presentation": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    # Fallback: export remaining Google Workspace types as PDF
    "application/vnd.google-apps.form": "application/pdf",
    "application/vnd.google-apps.drawing": "application/pdf",
    "application/vnd.google-apps.script": "application/pdf",
    "application/vnd.google-apps.site": "application/pdf",
    "application/vnd.google-apps.jam": "application/pdf",
}

# Google Workspace types that cannot be exported at all (skip silently)
_GDRIVE_SKIP_TYPES: set = {
    "application/vnd.google-apps.folder",
    "application/vnd.google-apps.shortcut",
    "application/vnd.google-apps.map",
}


@dataclass
class SyntheticUploadFile:
    """Minimal UploadFile-compatible object for injecting bytes into Oculus Prime."""

    filename: str
    file: io.BytesIO
    content_type: str = "application/octet-stream"


@dataclass
class GDriveFileMetadata:
    file_id: str
    name: str
    mime_type: str
    size: Optional[int] = None
    modified_time: Optional[str] = None
    parents: List[str] = field(default_factory=list)


class GDriveAdapter:
    """
    Downloads/uploads files from/to Google Drive.

    Usage (read):
        adapter = GDriveAdapter.from_env()
        file_meta, upload = adapter.download_as_upload(file_id="abc123")

    Usage (write):
        adapter = GDriveAdapter.from_env(mode="readwrite")
        folder_id = adapter.find_or_create_folder("clienteA", parent_id="root_id")
        file_id = adapter.upload_file("/tmp/report.pptx", folder_id)
    """

    SCOPES_READONLY = ["https://www.googleapis.com/auth/drive.readonly"]
    SCOPES_READWRITE = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.file",
    ]

    def __init__(self, credentials_json: str, mode: str = "readonly") -> None:
        self._credentials_json = credentials_json
        self._mode = mode
        self._service = None
        self._folder_cache: Dict[str, str] = {}  # "parent_id/name" → folder_id

    # ── Factory ──────────────────────────────────────────────

    @classmethod
    def from_env(cls, mode: str = "readonly", env_prefix: str = "GDRIVE") -> Optional["GDriveAdapter"]:
        """
        Return GDriveAdapter if credentials are configured, else None.

        Args:
            mode: "readonly" or "readwrite" (determines Google API scopes)
            env_prefix: prefix for env vars. Default "GDRIVE" reads GDRIVE_CREDENTIALS_FILE.
                        Use "GDRIVE_REPO" to read GDRIVE_REPO_CREDENTIALS_FILE.
        """
        env_key = f"{env_prefix}_CREDENTIALS_FILE"
        credentials_file = os.environ.get(env_key, "").strip()
        if not credentials_file:
            # Fallback: try the default key if using a prefix
            if env_prefix != "GDRIVE":
                credentials_file = os.environ.get("GDRIVE_CREDENTIALS_FILE", "").strip()
            if not credentials_file:
                logger.info("GDriveAdapter: %s not set — disabled.", env_key)
                return None
        if not os.path.isfile(credentials_file):
            logger.warning(
                "GDriveAdapter: credentials file not found at %s — disabled.",
                credentials_file,
            )
            return None
        return cls(credentials_json=credentials_file, mode=mode)

    # ── Google Drive service ──────────────────────────────────

    def _get_service(self) -> Any:
        if self._service is not None:
            return self._service
        try:
            import json as _json
            from googleapiclient.discovery import build

            scopes = self.SCOPES_READWRITE if self._mode == "readwrite" else self.SCOPES_READONLY

            # Auto-detect credential type
            with open(self._credentials_json) as f:
                cred_data = _json.load(f)
            cred_type = cred_data.get("type", "service_account")

            if cred_type == "authorized_user":
                # OAuth2 user credentials (personal Google account)
                # drive.file scope: read+write for files/folders created by this app
                from google.oauth2.credentials import Credentials
                from google.auth.transport.requests import Request

                creds = Credentials(
                    token=None,
                    refresh_token=cred_data["refresh_token"],
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=cred_data["client_id"],
                    client_secret=cred_data["client_secret"],
                    scopes=["https://www.googleapis.com/auth/drive.file"],
                )
                # Refresh immediately to validate
                creds.refresh(Request())
                logger.info("GDriveAdapter: authenticated via OAuth2 user credentials (mode=%s).", self._mode)
            else:
                # Service account credentials
                from google.oauth2 import service_account

                creds = service_account.Credentials.from_service_account_file(
                    self._credentials_json,
                    scopes=scopes,
                )
                logger.info("GDriveAdapter: authenticated via service account (mode=%s).", self._mode)

            self._service = build("drive", "v3", credentials=creds, cache_discovery=False)
            return self._service
        except ImportError:
            raise RuntimeError(
                "google-api-python-client not installed. "
                "Add 'google-api-python-client google-auth' to requirements."
            )

    # ── Public API ────────────────────────────────────────────

    def get_file_metadata(self, file_id: str) -> GDriveFileMetadata:
        """Return metadata for a single file."""
        service = self._get_service()
        meta = (
            service.files()
            .get(
                fileId=file_id,
                fields="id,name,mimeType,size,modifiedTime,parents",
            )
            .execute()
        )
        return GDriveFileMetadata(
            file_id=meta["id"],
            name=meta.get("name", file_id),
            mime_type=meta.get("mimeType", "application/octet-stream"),
            size=meta.get("size"),
            modified_time=meta.get("modifiedTime"),
            parents=meta.get("parents", []),
        )

    def list_folder(self, folder_id: str, page_size: int = 50, include_folders: bool = False) -> List["GDriveFileMetadata"]:
        """List files directly inside a Drive folder. Subfolders are excluded by default."""
        service = self._get_service()
        query = f"'{folder_id}' in parents and trashed=false"
        if not include_folders:
            query += " and mimeType != 'application/vnd.google-apps.folder'"
        results = (
            service.files()
            .list(
                q=query,
                pageSize=page_size,
                fields="files(id,name,mimeType,size,modifiedTime,parents)",
            )
            .execute()
        )
        return [
            GDriveFileMetadata(
                file_id=f["id"],
                name=f.get("name", f["id"]),
                mime_type=f.get("mimeType", "application/octet-stream"),
                size=f.get("size"),
                modified_time=f.get("modifiedTime"),
                parents=f.get("parents", []),
            )
            for f in results.get("files", [])
        ]

    def download_bytes(self, meta: GDriveFileMetadata) -> tuple[bytes, str]:
        """
        Download file content. Returns (bytes, effective_mime_type).
        Google Workspace files are exported to Office/PDF format automatically.
        Raises ValueError for non-downloadable types (folders, shortcuts).
        """
        from googleapiclient.http import MediaIoBaseDownload

        if meta.mime_type in _GDRIVE_SKIP_TYPES:
            raise ValueError(
                f"File '{meta.name}' ({meta.mime_type}) cannot be downloaded — skip"
            )

        service = self._get_service()
        buf = io.BytesIO()

        export_mime = _GDRIVE_EXPORT_FORMATS.get(meta.mime_type)
        if export_mime:
            # Google Workspace → export as Office/PDF format
            request = service.files().export_media(fileId=meta.file_id, mimeType=export_mime)
            effective_mime = export_mime
        elif meta.mime_type.startswith("application/vnd.google-apps."):
            # Unknown Google Workspace type — PDF fallback
            logger.warning(
                "GDrive: unknown Workspace type %s for '%s' — exporting as PDF",
                meta.mime_type, meta.name,
            )
            request = service.files().export_media(fileId=meta.file_id, mimeType="application/pdf")
            effective_mime = "application/pdf"
        else:
            request = service.files().get_media(fileId=meta.file_id)
            effective_mime = meta.mime_type

        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        buf.seek(0)
        return buf.read(), effective_mime

    def download_as_upload(
        self,
        file_id: str,
    ) -> tuple[GDriveFileMetadata, SyntheticUploadFile]:
        """
        Download a file by ID and wrap it as a SyntheticUploadFile ready for
        OculusPrimeAdapter.ingest_*().
        """
        meta = self.get_file_metadata(file_id)
        content, effective_mime = self.download_bytes(meta)

        # Derive extension for the filename
        ext = mimetypes.guess_extension(effective_mime) or ""
        filename = meta.name if "." in meta.name else f"{meta.name}{ext}"

        upload = SyntheticUploadFile(
            filename=filename,
            file=io.BytesIO(content),
            content_type=effective_mime,
        )
        return meta, upload

    def resolve_ingest_method(self, mime_type: str) -> str:
        """Return the OculusPrimeAdapter method name for this MIME type."""
        return _MIME_TO_INGEST_METHOD.get(mime_type, "ingest_document")

    # ── Write API (requires mode="readwrite") ─────────────────

    def _require_write(self) -> None:
        if self._mode != "readwrite":
            raise RuntimeError(
                "GDriveAdapter: write operation requires mode='readwrite'. "
                "Initialize with GDriveAdapter.from_env(mode='readwrite')."
            )

    def find_folder(self, name: str, parent_id: str) -> Optional[str]:
        """
        Find a folder by name under a parent. Returns folder_id or None.
        Results are cached for the lifetime of the adapter.
        """
        cache_key = f"{parent_id}/{name}"
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]

        service = self._get_service()
        query = (
            f"'{parent_id}' in parents "
            f"and name = '{name}' "
            f"and mimeType = 'application/vnd.google-apps.folder' "
            f"and trashed = false"
        )
        results = service.files().list(
            q=query,
            fields="files(id,name)",
            pageSize=1,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
        files = results.get("files", [])
        if files:
            folder_id = files[0]["id"]
            self._folder_cache[cache_key] = folder_id
            return folder_id
        return None

    def create_folder(self, name: str, parent_id: str) -> str:
        """
        Create a new folder under parent_id. Returns the new folder's ID.
        """
        self._require_write()
        service = self._get_service()
        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        folder = service.files().create(body=metadata, fields="id", supportsAllDrives=True).execute()
        folder_id = folder["id"]
        self._folder_cache[f"{parent_id}/{name}"] = folder_id
        logger.info("GDriveAdapter: created folder '%s' (id=%s) under %s", name, folder_id, parent_id)
        return folder_id

    def find_or_create_folder(self, name: str, parent_id: str) -> str:
        """Find existing folder or create it. Returns folder_id."""
        existing = self.find_folder(name, parent_id)
        if existing:
            return existing
        return self.create_folder(name, parent_id)

    def resolve_path(self, root_folder_id: str, *segments: str) -> str:
        """
        Resolve a nested folder path, creating folders as needed.
        Example: resolve_path(root, "aicom-clienteA", "assessment-roma")
        """
        current_id = root_folder_id
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
            current_id = self.find_or_create_folder(segment, current_id)
        return current_id

    def upload_file(
        self,
        local_path: str,
        folder_id: str,
        filename: Optional[str] = None,
    ) -> str:
        """
        Upload a local file to a GDrive folder. Returns the Drive file ID.
        """
        self._require_write()
        from googleapiclient.http import MediaFileUpload

        service = self._get_service()
        actual_filename = filename or os.path.basename(local_path)
        mime_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"

        metadata = {
            "name": actual_filename,
            "parents": [folder_id],
        }
        media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
        result = service.files().create(
            body=metadata,
            media_body=media,
            fields="id,name,webViewLink",
            supportsAllDrives=True,
        ).execute()

        file_id = result["id"]
        web_link = result.get("webViewLink", "")
        logger.info(
            "GDriveAdapter: uploaded '%s' → folder %s (id=%s, link=%s)",
            actual_filename, folder_id, file_id, web_link,
        )
        return file_id

    def get_web_link(self, file_id: str) -> str:
        """Get the web view link for a file."""
        service = self._get_service()
        result = service.files().get(fileId=file_id, fields="webViewLink", supportsAllDrives=True).execute()
        return result.get("webViewLink", f"https://drive.google.com/file/d/{file_id}/view")
