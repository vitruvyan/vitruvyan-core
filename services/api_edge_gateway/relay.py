from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import httpx

from .contracts import EdgeEnvelopeStored, EdgeSourceType


class CoreIntakeRelay:
    _ENDPOINT_MAP = {
        EdgeSourceType.document: "/api/intake/document",
        EdgeSourceType.image: "/api/intake/image",
        EdgeSourceType.audio: "/api/intake/audio",
        EdgeSourceType.video: "/api/intake/video",
        EdgeSourceType.cad: "/api/intake/cad",
        EdgeSourceType.landscape: "/api/intake/landscape",
        EdgeSourceType.geo: "/api/intake/geo",
    }

    def __init__(self, base_url: str, timeout_sec: int = 10, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec
        self.token = token

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def health(self) -> bool:
        try:
            with httpx.Client(timeout=self.timeout_sec) as client:
                response = client.get(f"{self.base_url}/health", headers=self._headers())
                return response.status_code == 200
        except Exception:
            return False

    def submit(self, envelope: EdgeEnvelopeStored) -> Tuple[bool, str]:
        endpoint = self._ENDPOINT_MAP[envelope.source_type]
        source_path = Path(envelope.source_uri)
        if not source_path.exists() or not source_path.is_file():
            return False, f"Source file not found: {envelope.source_uri}"

        form_data = dict(envelope.metadata or {})
        if envelope.correlation_id:
            form_data.setdefault("correlation_id", envelope.correlation_id)

        with source_path.open("rb") as file_obj:
            files = {"file": (source_path.name, file_obj, "application/octet-stream")}
            try:
                with httpx.Client(timeout=self.timeout_sec) as client:
                    response = client.post(
                        f"{self.base_url}{endpoint}",
                        data=form_data,
                        files=files,
                        headers=self._headers(),
                    )
                if 200 <= response.status_code < 300:
                    return True, response.text
                return False, f"Core intake returned {response.status_code}: {response.text[:512]}"
            except Exception as exc:
                return False, f"Relay error: {exc}"
