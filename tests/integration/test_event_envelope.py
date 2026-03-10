"""
Integration Test — Event Envelope adapter (TransportEvent ↔ CognitiveEvent).

Tests the bidirectional conversion between bus-level and consumer-level events,
ensuring causal chain preservation and payload integrity.

Markers: integration
"""

import pytest
from datetime import datetime

from core.synaptic_conclave.events.event_envelope import (
    TransportEvent,
    CognitiveEvent,
    EventAdapter,
)


class TestTransportToCognitive:
    """Transport (bus) → Cognitive (consumer) conversion."""

    def test_basic_conversion_preserves_identity(self):
        transport = TransportEvent(
            stream="vitruvyan:codex:discovery:mapped",
            event_id="1705123456789-0",
            emitter="codex_hunters",
            payload={"entity": "test_entity", "action": "mapped"},
            timestamp="2026-03-10T12:00:00Z",
            correlation_id="corr-001",
        )
        cognitive = EventAdapter.transport_to_cognitive(transport)

        assert cognitive.id == "1705123456789-0"
        assert cognitive.source == "codex_hunters"
        assert cognitive.correlation_id == "corr-001"
        assert cognitive.payload["entity"] == "test_entity"

    def test_stream_name_converted_to_dot_notation(self):
        transport = TransportEvent(
            stream="vitruvyan:codex:discovery:mapped",
            event_id="1-0",
            emitter="test",
            payload={},
            timestamp="2026-03-10T12:00:00Z",
        )
        cognitive = EventAdapter.transport_to_cognitive(transport)
        assert cognitive.type == "codex.discovery.mapped"

    def test_causal_fields_extracted_from_payload(self):
        transport = TransportEvent(
            stream="vitruvyan:vault:archive",
            event_id="2-0",
            emitter="vault_keepers",
            payload={"trace_id": "trace-abc", "causation_id": "cause-xyz", "data": "content"},
            timestamp="2026-03-10T12:00:00Z",
            correlation_id="corr-002",
        )
        cognitive = EventAdapter.transport_to_cognitive(transport)
        assert cognitive.trace_id == "trace-abc"
        assert cognitive.causation_id == "cause-xyz"

    def test_missing_correlation_id_uses_event_id(self):
        transport = TransportEvent(
            stream="vitruvyan:test:channel",
            event_id="3-0",
            emitter="test",
            payload={},
            timestamp="2026-03-10T12:00:00Z",
            correlation_id=None,
        )
        cognitive = EventAdapter.transport_to_cognitive(transport)
        assert cognitive.correlation_id == "3-0"

    def test_metadata_includes_transport_origin(self):
        transport = TransportEvent(
            stream="vitruvyan:memory:coherence",
            event_id="4-0",
            emitter="memory_orders",
            payload={},
            timestamp="2026-03-10T12:00:00Z",
        )
        cognitive = EventAdapter.transport_to_cognitive(transport)
        assert cognitive.metadata["transport_stream"] == "vitruvyan:memory:coherence"
        assert cognitive.metadata["transport_event_id"] == "4-0"


class TestCognitiveToTransport:
    """Cognitive (consumer) → Transport (bus) conversion."""

    def test_basic_conversion_preserves_identity(self):
        cognitive = CognitiveEvent(
            id="evt-001",
            type="vault.archive.completed",
            source="vault_keepers",
            payload={"snapshot_id": "snap-001"},
            correlation_id="corr-003",
            trace_id="trace-001",
        )
        transport = EventAdapter.cognitive_to_transport(cognitive)

        assert transport.emitter == "vault_keepers"
        assert transport.correlation_id == "corr-003"
        assert transport.payload["snapshot_id"] == "snap-001"

    def test_type_converted_to_stream_name(self):
        cognitive = CognitiveEvent(type="vault.archive.completed", source="test", payload={})
        transport = EventAdapter.cognitive_to_transport(cognitive)
        assert transport.stream == "vitruvyan:vault:archive:completed"

    def test_causal_chain_enriched_in_payload(self):
        cognitive = CognitiveEvent(
            type="test.event",
            source="test",
            payload={"data": "content"},
            trace_id="trace-xyz",
            causation_id="cause-abc",
        )
        transport = EventAdapter.cognitive_to_transport(cognitive)
        assert transport.payload["trace_id"] == "trace-xyz"
        assert transport.payload["causation_id"] == "cause-abc"
        assert transport.payload["data"] == "content"  # original payload preserved

    def test_custom_stream_prefix(self):
        cognitive = CognitiveEvent(type="custom.event", source="test", payload={})
        transport = EventAdapter.cognitive_to_transport(cognitive, stream_prefix="myapp")
        assert transport.stream == "myapp:custom:event"


class TestRoundTrip:
    """Bidirectional conversion preserves semantics."""

    def test_cognitive_roundtrip_preserves_payload(self):
        original = CognitiveEvent(
            type="memory.coherence.analyzed",
            source="memory_orders",
            payload={"drift": 3.5, "status": "healthy"},
            correlation_id="session-001",
            trace_id="root-001",
            causation_id="parent-001",
        )

        transport = EventAdapter.cognitive_to_transport(original)
        restored = EventAdapter.transport_to_cognitive(transport)

        assert restored.source == original.source
        assert restored.correlation_id == original.correlation_id
        assert restored.payload["drift"] == 3.5
        assert restored.payload["status"] == "healthy"
        assert restored.trace_id == "root-001"
        assert restored.causation_id == "parent-001"

    def test_child_event_preserves_causal_chain(self):
        parent = CognitiveEvent(
            id="parent-001",
            type="memory.coherence.analyzed",
            source="memory_orders",
            payload={"drift": 3.5},
            correlation_id="session-001",
            trace_id="root-001",
        )
        child = parent.child(
            event_type="vault.archive.triggered",
            payload={"reason": "drift_detected"},
            source="vault_keepers",
        )

        assert child.causation_id == "parent-001"
        assert child.correlation_id == "session-001"
        assert child.trace_id == "root-001"
        assert child.source == "vault_keepers"
        assert child.payload["reason"] == "drift_detected"
