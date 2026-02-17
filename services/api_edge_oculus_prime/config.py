"""Configuration for Edge Oculus Prime API service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List


def _in_container() -> bool:
    return Path("/.dockerenv").exists()


def _default_postgres_host() -> str:
    return "core_postgres" if _in_container() else "localhost"


def _default_redis_host() -> str:
    return "core_redis" if _in_container() else "localhost"


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class OculusPrimeSettings:
    service_name: str
    service_version: str
    host: str
    port: int
    log_level: str
    uploads_dir: str
    frontend_url: str
    cors_origins: List[str]
    cors_origin_regex: str
    redis_host: str
    redis_port: int
    postgres_host: str
    postgres_port: str
    postgres_db: str
    postgres_user: str | None
    postgres_password: str | None
    document_formats: tuple[str, ...]
    image_formats: tuple[str, ...]
    audio_formats: tuple[str, ...]
    video_formats: tuple[str, ...]
    cad_formats: tuple[str, ...]
    geo_formats: tuple[str, ...]
    event_migration_mode: str = "dual_write"


def load_settings() -> OculusPrimeSettings:
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    default_origins = ",".join(
        [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3003",
            "http://vitruvyan_aegis_ui:3000",
            "https://aegis.vitruvyan.com",
            "https://aegis-ui-seven.vercel.app",
            frontend_url,
        ]
    )
    cors_origins = _split_csv(
        os.getenv("OCULUS_PRIME_CORS_ORIGINS", os.getenv("INTAKE_CORS_ORIGINS", default_origins))
    )

    return OculusPrimeSettings(
        service_name="aegis_oculus_prime_api",
        service_version="1.0.0",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8050")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        uploads_dir=os.getenv("OCULUS_PRIME_UPLOADS_DIR", os.getenv("INTAKE_UPLOADS_DIR", "/app/uploads")),
        frontend_url=frontend_url,
        cors_origins=cors_origins,
        cors_origin_regex=os.getenv(
            "OCULUS_PRIME_CORS_ORIGIN_REGEX",
            os.getenv("INTAKE_CORS_ORIGIN_REGEX", r"https://.*\\.vercel\\.app"),
        ),
        redis_host=os.getenv("REDIS_HOST", _default_redis_host()),
        redis_port=int(os.getenv("REDIS_PORT", "6379")),
        postgres_host=os.getenv("POSTGRES_HOST", _default_postgres_host()),
        postgres_port=os.getenv("POSTGRES_PORT", "5432"),
        postgres_db=os.getenv("POSTGRES_DB", "vitruvyan_core"),
        postgres_user=os.getenv("POSTGRES_USER"),
        postgres_password=os.getenv("POSTGRES_PASSWORD"),
        event_migration_mode=os.getenv(
            "OCULUS_PRIME_EVENT_MIGRATION_MODE",
            os.getenv("INTAKE_EVENT_MIGRATION_MODE", "dual_write"),
        ),
        cad_formats=(".dxf", ".dwg", ".ifc", ".rvt", ".obj", ".fbx", ".3ds"),
        image_formats=(".png", ".jpg", ".jpeg", ".tif", ".tiff", ".geotiff"),
        document_formats=(".pdf", ".docx", ".md", ".txt", ".json", ".xml"),
        audio_formats=(".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"),
        video_formats=(".mp4", ".avi", ".mov", ".mkv", ".webm"),
        geo_formats=(".kml", ".kmz", ".geojson", ".json", ".gpx", ".wkt", ".txt"),
    )


# Legacy alias kept to avoid breaking existing imports.
IntakeSettings = OculusPrimeSettings
settings = load_settings()
