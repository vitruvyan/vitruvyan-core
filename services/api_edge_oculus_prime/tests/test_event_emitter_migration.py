"""Tests for versioned Oculus Prime event naming migration."""

from __future__ import annotations

import sys
from pathlib import Path


SERVICES_DIR = Path(__file__).resolve().parents[2]
CORE_DIR = Path(__file__).resolve().parents[3] / "vitruvyan_core"
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from infrastructure.edge.oculus_prime.core.event_emitter import IntakeEventEmitter  # noqa: E402


class _FakeBus:
    def __init__(self):
        self.calls: list[dict] = []

    def emit(self, channel, payload, emitter="unknown", correlation_id=None):
        self.calls.append(
            {
                "channel": channel,
                "payload": payload,
                "emitter": emitter,
                "correlation_id": correlation_id,
            }
        )
        return "1700000000000-0"


def test_dual_write_emits_v2_and_legacy_alias():
    bus = _FakeBus()
    emitter = IntakeEventEmitter(stream_bus=bus, postgres_agent=None, migration_mode="dual_write")

    event = emitter.emit_evidence_created(
        evidence_id="EVD-12345678-1234-1234-1234-1234567890AB",
        chunk_id="CHK-0",
        source_type="document",
        source_uri="/tmp/a.txt",
        evidence_pack_ref="postgres://evidence_packs/EVD-123",
        source_hash="sha256:abc",
        intake_agent_id="document-intake-v1",
        intake_agent_version="1.0.0",
        correlation_id="trace-1",
    )

    assert [c["channel"] for c in bus.calls] == [
        "oculus_prime.evidence.created",
        "intake.evidence.created",
    ]
    assert event.event_version == "2.0.0"
    assert event.schema_ref == "aegis://oculus_prime/events/evidence_created/v2.0"
    assert event.metadata["migration_mode"] == "dual_write"
    assert event.metadata["emitted_channels"] == [
        "oculus_prime.evidence.created",
        "intake.evidence.created",
    ]


def test_v2_only_emits_canonical_channel_only():
    bus = _FakeBus()
    emitter = IntakeEventEmitter(stream_bus=bus, postgres_agent=None, migration_mode="v2_only")

    event = emitter.emit_evidence_created(
        evidence_id="EVD-12345678-1234-1234-1234-1234567890AB",
        chunk_id="CHK-0",
        source_type="image",
        source_uri="/tmp/a.png",
        evidence_pack_ref="postgres://evidence_packs/EVD-123",
        source_hash="sha256:def",
        intake_agent_id="image-intake-v1",
        intake_agent_version="1.0.0",
    )

    assert [c["channel"] for c in bus.calls] == ["oculus_prime.evidence.created"]
    assert event.event_version == "2.0.0"
    assert event.metadata["migration_mode"] == "v2_only"


def test_v1_only_supports_rollback_mode():
    bus = _FakeBus()
    emitter = IntakeEventEmitter(stream_bus=bus, postgres_agent=None, migration_mode="v1_only")

    event = emitter.emit_evidence_created(
        evidence_id="EVD-12345678-1234-1234-1234-1234567890AB",
        chunk_id="CHK-0",
        source_type="audio",
        source_uri="/tmp/a.wav",
        evidence_pack_ref="postgres://evidence_packs/EVD-123",
        source_hash="sha256:ghi",
        intake_agent_id="audio-intake-v1",
        intake_agent_version="1.0.0",
    )

    assert [c["channel"] for c in bus.calls] == ["intake.evidence.created"]
    assert event.event_version == "1.0.0"
    assert event.schema_ref == "aegis://intake/events/evidence_created/v1.0"
    assert event.metadata["migration_mode"] == "v1_only"
