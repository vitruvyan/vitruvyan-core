"""Route tests for Edge Oculus Prime API service."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest


SERVICES_DIR = Path(__file__).resolve().parents[2]
CORE_DIR = Path(__file__).resolve().parents[3] / "vitruvyan_core"
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

pytest.importorskip("multipart")

from api_edge_oculus_prime.api.routes import router  # noqa: E402


def _client(adapter) -> TestClient:
    app = FastAPI()
    app.state.intake_adapter = adapter
    app.include_router(router)
    return TestClient(app)


def test_health_route_delegates_to_adapter():
    class Adapter:
        def health(self):
            return {"status": "healthy", "service": "aegis_oculus_prime_api"}

    client = _client(Adapter())
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_document_route_returns_400_on_validation_error():
    class Adapter:
        def ingest_document(self, **kwargs):
            raise ValueError("Unsupported document format")

    client = _client(Adapter())
    response = client.post(
        "/api/oculus-prime/document",
        files={"file": ("bad.exe", b"dummy", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "Unsupported document format" in response.json()["detail"]


def test_get_evidence_route_returns_payload():
    class Adapter:
        def get_evidence_pack(self, evidence_id):
            return {"evidence_id": evidence_id, "chunks": [{"chunk_id": "CHK-0"}]}

    client = _client(Adapter())
    response = client.get("/api/oculus-prime/evidence/EVD-123")

    assert response.status_code == 200
    payload = response.json()
    assert payload["evidence_id"] == "EVD-123"
    assert payload["chunks"][0]["chunk_id"] == "CHK-0"
