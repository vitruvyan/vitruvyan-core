"""
Channel Alignment Test — F1.4
============================

Verifies that every channel emitted by a graph node (producer) has at least
one registered consumer in the channel registry, and that every channel a
service listens to (SACRED_CHANNELS) is registered.

This prevents channel drift: the bug class where a producer emits to a channel
that no listener subscribes to (events lost in the void).

Created: Mar 06, 2026
"""

import pytest
from core.synaptic_conclave.channels.channel_registry import (
    CHANNEL_REGISTRY,
    get_channels_for_consumer,
    validate_channel,
    EventContract,
)


# ─── Graph Nodes: channels they emit to ─────────────────────────────────

GRAPH_EMITTED_CHANNELS = {
    "orthodoxy_node": "orthodoxy.audit.requested",
    "vault_node_standard": "vault.integrity.requested",
    "vault_node_critical": "vault.archive.requested",
    "vault_node_domain": "audit.vault.requested",
    "codex_node_started": "codex.expedition.started",
    "codex_node_completed": "codex.expedition.completed",
    "codex_node_failed": "codex.expedition.failed",
}

# ─── Service Listeners: channels they subscribe to ──────────────────────

SERVICE_SACRED_CHANNELS = {
    "orthodoxy_wardens": [
        "orthodoxy.audit.requested",
        "engine.eval.completed",
        "babel.sentiment.completed",
        "memory.write.completed",
        "langgraph.response.completed",
        "vee.explanation.completed",
        "conclave.mcp.actions",
        "synaptic.conclave.broadcast",
    ],
    "vault_keepers": [
        "vault.archive.requested",
        "vault.integrity.requested",
        "vault.restore.requested",
        "vault.snapshot.requested",
        "audit.vault.requested",
        "orthodoxy.audit.completed",
        "engine.eval.completed",
    ],
    "memory_orders": [
        "memory.coherence.requested",
        "memory.health.requested",
        "memory.sync.requested",
        "memory.write.completed",
    ],
    "codex_hunters": [
        "codex.data.refresh.requested",
        "codex.technical.momentum.requested",
        "codex.technical.trend.requested",
        "codex.technical.volatility.requested",
        "codex.schema.validation.requested",
        "codex.fundamentals.refresh.requested",
        "oculus_prime.evidence.created",
    ],
}


class TestChannelRegistryIntegrity:
    """Ensure the channel registry is internally consistent."""

    def test_all_channels_have_required_fields(self):
        """Every EventContract must have name, producer, consumers, description."""
        for name, contract in CHANNEL_REGISTRY.items():
            assert contract.name == name, f"Key/name mismatch: {name} vs {contract.name}"
            assert contract.producer, f"Channel {name} has no producer"
            assert contract.description, f"Channel {name} has no description"
            assert contract.direction in ("request", "response", "event"), (
                f"Channel {name} has invalid direction: {contract.direction}"
            )
            assert contract.status in ("active", "deprecated", "reserved"), (
                f"Channel {name} has invalid status: {contract.status}"
            )

    def test_request_channels_have_response(self):
        """Request channels should define a response_channel (if known)."""
        for name, contract in CHANNEL_REGISTRY.items():
            if contract.direction == "request" and contract.response_channel:
                assert contract.response_channel in CHANNEL_REGISTRY, (
                    f"Channel {name} references non-existent response "
                    f"channel: {contract.response_channel}"
                )

    def test_no_duplicate_channels(self):
        """Channel names must be unique (enforced by dict, but verify explicitly)."""
        names = [c.name for c in CHANNEL_REGISTRY.values()]
        assert len(names) == len(set(names)), "Duplicate channel names in registry"


class TestGraphNodeAlignment:
    """
    Every channel emitted by a graph node must:
    1. Be registered in the channel registry
    2. Have at least one consumer registered
    """

    @pytest.mark.parametrize(
        "node_label,channel",
        list(GRAPH_EMITTED_CHANNELS.items()),
    )
    def test_graph_emitted_channel_is_registered(self, node_label, channel):
        assert validate_channel(channel), (
            f"Graph node '{node_label}' emits to unregistered channel: {channel}. "
            f"Add it to channel_registry.py"
        )

    @pytest.mark.parametrize(
        "node_label,channel",
        list(GRAPH_EMITTED_CHANNELS.items()),
    )
    def test_graph_emitted_channel_has_consumer(self, node_label, channel):
        contract = CHANNEL_REGISTRY.get(channel)
        assert contract is not None, f"Channel {channel} not in registry"
        assert len(contract.consumers) > 0, (
            f"Graph node '{node_label}' emits to channel '{channel}' "
            f"which has NO registered consumers — events will be lost"
        )


class TestServiceListenerAlignment:
    """
    Every channel a service listener subscribes to must be registered
    in the channel registry.
    """

    @pytest.mark.parametrize(
        "service,channel",
        [
            (svc, ch)
            for svc, channels in SERVICE_SACRED_CHANNELS.items()
            for ch in channels
        ],
    )
    def test_listener_channel_is_registered(self, service, channel):
        assert validate_channel(channel), (
            f"Service '{service}' listens to unregistered channel: {channel}. "
            f"Add it to channel_registry.py or remove from SACRED_CHANNELS"
        )

    def test_consumer_query_returns_expected(self):
        """get_channels_for_consumer must return all channels where service is listed."""
        vault_channels = get_channels_for_consumer("vault_keepers")
        assert "vault.archive.requested" in vault_channels
        assert "vault.integrity.requested" in vault_channels
        assert "orthodoxy.audit.completed" in vault_channels

    def test_orthodoxy_consumer_query(self):
        orthodoxy_channels = get_channels_for_consumer("orthodoxy_wardens")
        assert "orthodoxy.audit.requested" in orthodoxy_channels
        assert "langgraph.response.completed" in orthodoxy_channels
        assert "memory.write.completed" in orthodoxy_channels

    def test_codex_consumer_query(self):
        codex_channels = get_channels_for_consumer("codex_hunters")
        assert "codex.data.refresh.requested" in codex_channels
        assert "codex.technical.momentum.requested" in codex_channels
        assert "oculus_prime.evidence.created" in codex_channels
