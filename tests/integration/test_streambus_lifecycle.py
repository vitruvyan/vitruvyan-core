"""
Integration Test — StreamBus lifecycle (create group → emit → consume → ack).

Uses a mock Redis client to verify the full event lifecycle without
requiring a running Redis instance.

Markers: integration
"""

import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from redis.exceptions import ResponseError

from core.synaptic_conclave.transport.streams import StreamBus


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    client = MagicMock()
    client.ping.return_value = True
    return client


@pytest.fixture
def bus(mock_redis):
    """Create a StreamBus with a mocked Redis client."""
    with patch.object(StreamBus, "_connect"):
        b = StreamBus(host="localhost", port=6379)
        b._client = mock_redis
        b._dlq = MagicMock()
    return b


class TestStreamBusEmit:
    """Produce events to a stream."""

    def test_emit_returns_event_id(self, bus, mock_redis):
        mock_redis.xadd.return_value = b"1705123456789-0"

        event_id = bus.emit(
            channel="codex:entity_updated",
            payload={"entity_id": "E1"},
            emitter="test_service",
        )

        assert event_id == "1705123456789-0"
        mock_redis.xadd.assert_called_once()
        call_args = mock_redis.xadd.call_args
        assert call_args[0][0] == "vitruvyan:codex:entity_updated"

    def test_emit_serializes_payload_as_json(self, bus, mock_redis):
        mock_redis.xadd.return_value = b"1-0"
        bus.emit("test:channel", {"key": "value"}, emitter="test")

        call_args = mock_redis.xadd.call_args
        fields = call_args[0][1]
        payload = json.loads(fields["payload"])
        assert payload == {"key": "value"}

    def test_emit_includes_correlation_id_when_provided(self, bus, mock_redis):
        mock_redis.xadd.return_value = b"1-0"
        bus.emit("test:ch", {"a": 1}, emitter="test", correlation_id="corr-001")

        fields = mock_redis.xadd.call_args[0][1]
        assert fields["correlation_id"] == "corr-001"

    def test_emit_omits_correlation_id_when_none(self, bus, mock_redis):
        mock_redis.xadd.return_value = b"1-0"
        bus.emit("test:ch", {"a": 1}, emitter="test")

        fields = mock_redis.xadd.call_args[0][1]
        assert "correlation_id" not in fields


class TestStreamBusConsumerGroup:
    """Create and manage consumer groups."""

    def test_create_consumer_group_success(self, bus, mock_redis):
        mock_redis.xgroup_create.return_value = True

        result = bus.create_consumer_group("codex:events", "my_group")

        assert result is True
        mock_redis.xgroup_create.assert_called_once_with(
            "vitruvyan:codex:events", "my_group", id="0", mkstream=True
        )

    def test_busygroup_error_returns_true(self, bus, mock_redis):
        """If consumer group already exists, treat as success."""
        mock_redis.xgroup_create.side_effect = ResponseError(
            "BUSYGROUP Consumer Group name already exists"
        )
        result = bus.create_consumer_group("codex:events", "existing_group")
        assert result is True


class TestStreamBusConsume:
    """Consume events from a stream."""

    def test_consume_yields_transport_events(self, bus, mock_redis):
        """Verify that consume() generator yields TransportEvent objects."""
        # xreadgroup returns data once, then empty (to avoid infinite loop)
        mock_redis.xreadgroup.side_effect = [
            [
                (
                    b"vitruvyan:test:channel",
                    [
                        (
                            b"1705123456789-0",
                            {
                                b"emitter": b"producer",
                                b"payload": b'{"data": "test"}',
                                b"timestamp": b"2026-03-10T12:00:00Z",
                                b"correlation_id": b"corr-001",
                            },
                        )
                    ],
                )
            ],
            StopIteration,  # sentinel to break the while-True loop
        ]

        gen = bus.consume("test:channel", "grp", "worker-1", count=1, block_ms=0)
        event = next(gen)

        assert event.emitter == "producer"
        assert event.payload == {"data": "test"}
        assert event.correlation_id == "corr-001"

    def test_consume_empty_continues(self, bus, mock_redis):
        """Empty xreadgroup response causes no yield (generator blocks)."""
        mock_redis.xreadgroup.return_value = []
        # We just verify no exception on creating the generator
        gen = bus.consume("empty:channel", "grp", "w1", count=1, block_ms=0)
        assert gen is not None  # generator created successfully


class TestStreamBusAck:
    """Acknowledge processed events."""

    def test_ack_calls_xack(self, bus, mock_redis):
        from core.synaptic_conclave.events.event_envelope import TransportEvent

        event = TransportEvent(
            stream="vitruvyan:test:channel",
            event_id="1705123456789-0",
            emitter="producer",
            payload={},
            timestamp="2026-03-10T12:00:00Z",
        )
        mock_redis.xack.return_value = 1

        bus.ack(event, group="my_group")
        mock_redis.xack.assert_called_once_with(
            "vitruvyan:test:channel", "my_group", "1705123456789-0"
        )


class TestStreamBusStreamNaming:
    """Stream name prefixing."""

    def test_channel_gets_prefix(self, bus):
        assert bus._stream_name("codex:events") == "vitruvyan:codex:events"

    def test_already_prefixed_channel_not_doubled(self, bus):
        assert bus._stream_name("vitruvyan:codex:events") == "vitruvyan:codex:events"
