from pathlib import Path
import sys


SERVICES_ROOT = Path(__file__).resolve().parents[2]
if str(SERVICES_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICES_ROOT))

from api_codex_hunters.streams_listener import _build_discovery_request


def test_discovery_request_omits_source_when_env_not_set(monkeypatch) -> None:
    monkeypatch.delenv("CODEX_OCULUS_SOURCE", raising=False)

    request = _build_discovery_request(
        payload={},
        channel="oculus_prime.evidence.created",
        correlation_id="corr-1",
        fallback_event_id="evt-1",
        transport_emitter="edge.oculus",
    )

    assert "source_type" not in request


def test_discovery_request_uses_env_source_when_set(monkeypatch) -> None:
    monkeypatch.setenv("CODEX_OCULUS_SOURCE", "reddit")

    request = _build_discovery_request(
        payload={},
        channel="oculus_prime.evidence.created",
        correlation_id="corr-1",
        fallback_event_id="evt-1",
        transport_emitter="edge.oculus",
    )

    assert request["source_type"] == "reddit"
