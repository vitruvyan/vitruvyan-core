"""
Channel Registry — Single Source of Truth
==========================================

Canonical registry of ALL Redis Streams channels in Vitruvyan Core.

This is an architectural contract (LIVELLO 1): no I/O, no Redis, no imports
from services. Both producers and consumers import from here.

Usage:
    from core.synaptic_conclave.channels import CHANNEL_REGISTRY, get_channels_for_consumer

    # Get all channels a service should listen to
    channels = get_channels_for_consumer("vault_keepers")

    # Validate a channel name before emitting
    validate_channel("vault.archive.requested")

Created: Mar 06, 2026
"""

from dataclasses import dataclass
from typing import Dict, FrozenSet, Optional, Tuple


@dataclass(frozen=True)
class EventContract:
    """
    Contract for a single bus channel.

    Attributes:
        name: Canonical channel name (dot notation)
        producer: Service/component that emits on this channel
        consumers: Services that subscribe to this channel
        description: Human-readable purpose
        direction: "request" (inbound to a service), "response" (outbound from service), or "event" (fire-and-forget)
        response_channel: For request channels, the expected response channel (if any)
        status: "active", "deprecated", or "reserved"
    """

    name: str
    producer: str
    consumers: Tuple[str, ...]
    description: str
    direction: str = "event"
    response_channel: Optional[str] = None
    status: str = "active"


# =============================================================================
# ORTHODOXY WARDENS — Truth & Governance
# =============================================================================

_ORTHODOXY_CHANNELS = {
    # Inbound: graph → orthodoxy listener
    "orthodoxy.audit.requested": EventContract(
        name="orthodoxy.audit.requested",
        producer="langgraph_orthodoxy_node",
        consumers=("orthodoxy_wardens",),
        description="Request audit of LangGraph output before delivery",
        direction="request",
        response_channel="orthodoxy.audit.completed",
    ),
    # Outbound: orthodoxy listener → vault, memory, conclave
    "orthodoxy.audit.completed": EventContract(
        name="orthodoxy.audit.completed",
        producer="orthodoxy_wardens",
        consumers=("vault_keepers", "conclave"),
        description="Audit verdict rendered (blessed/heretical/non_liquet)",
        direction="response",
    ),
    "orthodoxy.verdict.rendered": EventContract(
        name="orthodoxy.verdict.rendered",
        producer="orthodoxy_wardens",
        consumers=("vault_keepers", "conclave"),
        description="Final verdict after tribunal pipeline",
        direction="event",
    ),
    "orthodoxy.heresy.detected": EventContract(
        name="orthodoxy.heresy.detected",
        producer="orthodoxy_wardens",
        consumers=("vault_keepers", "conclave"),
        description="Critical governance violation detected",
        direction="event",
    ),
    "orthodoxy.purification.requested": EventContract(
        name="orthodoxy.purification.requested",
        producer="orthodoxy_wardens",
        consumers=("vault_keepers",),
        description="Correction needed on a previous output",
        direction="event",
    ),
    "orthodoxy.archive.requested": EventContract(
        name="orthodoxy.archive.requested",
        producer="orthodoxy_wardens",
        consumers=("vault_keepers",),
        description="Archive audit findings to Vault",
        direction="event",
    ),
}

# =============================================================================
# VAULT KEEPERS — Memory & Archival
# =============================================================================

_VAULT_CHANNELS = {
    # Inbound: graph → vault listener
    "vault.archive.requested": EventContract(
        name="vault.archive.requested",
        producer="langgraph_vault_node",
        consumers=("vault_keepers",),
        description="Archive content (critical protection level)",
        direction="request",
        response_channel="vault.archive.completed",
    ),
    "vault.integrity.requested": EventContract(
        name="vault.integrity.requested",
        producer="langgraph_vault_node",
        consumers=("vault_keepers",),
        description="Integrity check (standard/integrity_check protection)",
        direction="request",
        response_channel="vault.integrity.validated",
    ),
    "vault.restore.requested": EventContract(
        name="vault.restore.requested",
        producer="api",
        consumers=("vault_keepers",),
        description="Restore archived data",
        direction="request",
        response_channel="vault.restore.completed",
    ),
    "vault.snapshot.requested": EventContract(
        name="vault.snapshot.requested",
        producer="api",
        consumers=("vault_keepers",),
        description="Create a point-in-time snapshot",
        direction="request",
        response_channel="vault.snapshot.created",
    ),
    "audit.vault.requested": EventContract(
        name="audit.vault.requested",
        producer="langgraph_vault_node",
        consumers=("vault_keepers",),
        description="Domain guardian audit request",
        direction="request",
    ),
    # Outbound: vault listener → conclave, memory
    "vault.archive.completed": EventContract(
        name="vault.archive.completed",
        producer="vault_keepers",
        consumers=("conclave",),
        description="Archive operation completed",
        direction="response",
    ),
    "vault.integrity.validated": EventContract(
        name="vault.integrity.validated",
        producer="vault_keepers",
        consumers=("conclave",),
        description="Integrity check passed/failed",
        direction="response",
    ),
    "vault.snapshot.created": EventContract(
        name="vault.snapshot.created",
        producer="vault_keepers",
        consumers=("conclave",),
        description="Snapshot created successfully",
        direction="response",
    ),
    "vault.restore.completed": EventContract(
        name="vault.restore.completed",
        producer="vault_keepers",
        consumers=(),
        description="Restore operation completed",
        direction="response",
    ),
}

# =============================================================================
# MEMORY ORDERS — Coherence & Health
# =============================================================================

_MEMORY_CHANNELS = {
    "memory.coherence.requested": EventContract(
        name="memory.coherence.requested",
        producer="api",
        consumers=("memory_orders",),
        description="Check PG↔Qdrant coherence",
        direction="request",
        response_channel="memory.coherence.checked",
    ),
    "memory.coherence.checked": EventContract(
        name="memory.coherence.checked",
        producer="memory_orders",
        consumers=(),
        description="Coherence check result (healthy/warning/critical)",
        direction="response",
    ),
    "memory.health.requested": EventContract(
        name="memory.health.requested",
        producer="api",
        consumers=("memory_orders",),
        description="Request system health aggregation",
        direction="request",
        response_channel="memory.health.checked",
    ),
    "memory.health.checked": EventContract(
        name="memory.health.checked",
        producer="memory_orders",
        consumers=(),
        description="Aggregated health status",
        direction="response",
    ),
    "memory.sync.requested": EventContract(
        name="memory.sync.requested",
        producer="api",
        consumers=("memory_orders",),
        description="Trigger PG↔Qdrant synchronization",
        direction="request",
        response_channel="memory.sync.completed",
    ),
    "memory.sync.completed": EventContract(
        name="memory.sync.completed",
        producer="memory_orders",
        consumers=(),
        description="Sync operation completed successfully",
        direction="response",
    ),
    "memory.sync.failed": EventContract(
        name="memory.sync.failed",
        producer="memory_orders",
        consumers=(),
        description="Sync operation failed",
        direction="response",
    ),
    "memory.write.completed": EventContract(
        name="memory.write.completed",
        producer="embedding_service",
        consumers=("memory_orders", "orthodoxy_wardens"),
        description="New data written to dual memory (PG+Qdrant)",
        direction="event",
    ),
}

# =============================================================================
# CODEX HUNTERS — Perception & Discovery
# =============================================================================

_CODEX_CHANNELS = {
    # --- Graph → Codex Hunters (expedition lifecycle) ---
    "codex.expedition.started": EventContract(
        name="codex.expedition.started",
        producer="langgraph_codex_node",
        consumers=("codex_hunters",),
        description="Expedition kicked off from graph node",
        direction="event",
    ),
    "codex.expedition.completed": EventContract(
        name="codex.expedition.completed",
        producer="codex_hunters",
        consumers=("conclave",),
        description="Expedition finished successfully",
        direction="response",
    ),
    "codex.expedition.failed": EventContract(
        name="codex.expedition.failed",
        producer="codex_hunters",
        consumers=("conclave",),
        description="Expedition failed",
        direction="response",
    ),
    # --- Codex Hunters outbound (discovery) ---
    "codex.discovery.mapped": EventContract(
        name="codex.discovery.mapped",
        producer="codex_hunters",
        consumers=("orthodoxy_wardens", "vault_keepers"),
        description="New data source discovered and mapped",
        direction="event",
    ),
    # --- Codex Hunters request channels (consumed by listener, dispatched to API) ---
    "codex.data.refresh.requested": EventContract(
        name="codex.data.refresh.requested",
        producer="api",
        consumers=("codex_hunters",),
        description="Request data refresh expedition",
        direction="request",
    ),
    "codex.technical.momentum.requested": EventContract(
        name="codex.technical.momentum.requested",
        producer="api",
        consumers=("codex_hunters",),
        description="Request momentum backfill expedition",
        direction="request",
    ),
    "codex.technical.trend.requested": EventContract(
        name="codex.technical.trend.requested",
        producer="api",
        consumers=("codex_hunters",),
        description="Request trend backfill expedition",
        direction="request",
    ),
    "codex.technical.volatility.requested": EventContract(
        name="codex.technical.volatility.requested",
        producer="api",
        consumers=("codex_hunters",),
        description="Request volatility backfill expedition",
        direction="request",
    ),
    "codex.schema.validation.requested": EventContract(
        name="codex.schema.validation.requested",
        producer="api",
        consumers=("codex_hunters",),
        description="Request schema validation expedition",
        direction="request",
    ),
    "codex.fundamentals.refresh.requested": EventContract(
        name="codex.fundamentals.refresh.requested",
        producer="api",
        consumers=("codex_hunters",),
        description="Request fundamentals refresh expedition",
        direction="request",
    ),
    # --- Oculus Prime → Codex Hunters (evidence ingestion) ---
    "oculus_prime.evidence.created": EventContract(
        name="oculus_prime.evidence.created",
        producer="oculus_prime",
        consumers=("codex_hunters",),
        description="Evidence pack created by Oculus Prime (canonical v2 channel)",
        direction="event",
    ),
    "intake.evidence.created": EventContract(
        name="intake.evidence.created",
        producer="oculus_prime",
        consumers=("codex_hunters",),
        description="Evidence pack created (legacy v1 alias, migration-dependent)",
        direction="event",
        status="deprecated",
    ),
}

# =============================================================================
# BABEL GARDENS — Perception & Linguistics
# =============================================================================

_BABEL_CHANNELS = {
    "babel.sentiment.completed": EventContract(
        name="babel.sentiment.completed",
        producer="babel_gardens",
        consumers=("orthodoxy_wardens", "vault_keepers"),
        description="Sentiment analysis completed",
        direction="response",
    ),
    "babel.emotion.detected": EventContract(
        name="babel.emotion.detected",
        producer="babel_gardens",
        consumers=("conclave",),
        description="Emotion detection result",
        direction="event",
    ),
    "babel.linguistic.completed": EventContract(
        name="babel.linguistic.completed",
        producer="babel_gardens",
        consumers=("pattern_weavers",),
        description="Linguistic analysis completed (feeds Pattern Weavers)",
        direction="response",
    ),
    "babel.comprehension.completed": EventContract(
        name="babel.comprehension.completed",
        producer="babel_gardens",
        consumers=("memory_orders",),
        description="Full comprehension (v2 unified) completed",
        direction="response",
    ),
}

# =============================================================================
# PATTERN WEAVERS — Reason & Ontology
# =============================================================================

_PATTERN_CHANNELS = {
    "pattern.weave.request": EventContract(
        name="pattern.weave.request",
        producer="babel_gardens",
        consumers=("pattern_weavers",),
        description="Request ontology extraction from text",
        direction="request",
        response_channel="pattern_weavers.weave.completed",
    ),
    "pattern_weavers.weave.completed": EventContract(
        name="pattern_weavers.weave.completed",
        producer="pattern_weavers",
        consumers=(),
        description="Weave extraction completed",
        direction="response",
    ),
    "pattern_weavers.context.extracted": EventContract(
        name="pattern_weavers.context.extracted",
        producer="pattern_weavers",
        consumers=("conclave",),
        description="Contextual concepts extracted",
        direction="event",
    ),
}

# =============================================================================
# ORCHESTRATION — LangGraph ↔ Sacred Orders
# =============================================================================

_ORCHESTRATION_CHANNELS = {
    "langgraph.response.completed": EventContract(
        name="langgraph.response.completed",
        producer="langgraph",
        consumers=("orthodoxy_wardens", "conclave"),
        description="Graph pipeline completed, response ready for audit",
        direction="event",
    ),
}

# =============================================================================
# INTEGRATION — External Systems (Neural Engine, VEE, Edge)
# =============================================================================

_INTEGRATION_CHANNELS = {
    "engine.eval.completed": EventContract(
        name="engine.eval.completed",
        producer="neural_engine",
        consumers=("orthodoxy_wardens", "vault_keepers", "conclave"),
        description="Neural engine evaluation completed",
        direction="response",
    ),
    "vee.explanation.completed": EventContract(
        name="vee.explanation.completed",
        producer="vee_service",
        consumers=("orthodoxy_wardens",),
        description="VEE explanation generated",
        direction="response",
    ),
    "ingestion.acquired": EventContract(
        name="ingestion.acquired",
        producer="perception",
        consumers=("memory_orders",),
        description="External data acquired and normalized",
        direction="event",
    ),
    "ingestion.normalized": EventContract(
        name="ingestion.normalized",
        producer="perception",
        consumers=("memory_orders", "embedding_service"),
        description="Data normalized and ready for embedding",
        direction="event",
    ),
}

# =============================================================================
# CONCLAVE — Infrastructure & Observability
# =============================================================================

_CONCLAVE_CHANNELS = {
    "conclave.mcp.actions": EventContract(
        name="conclave.mcp.actions",
        producer="mcp_middleware",
        consumers=("orthodoxy_wardens", "conclave"),
        description="MCP tool execution actions for observability",
        direction="event",
    ),
    "synaptic.conclave.broadcast": EventContract(
        name="synaptic.conclave.broadcast",
        producer="system",
        consumers=("orthodoxy_wardens",),
        description="System-wide broadcast from Conclave",
        direction="event",
    ),
}

# =============================================================================
# PLASTICITY — Learning & Feedback
# =============================================================================

_PLASTICITY_CHANNELS = {
    "plasticity.feedback.received": EventContract(
        name="plasticity.feedback.received",
        producer="api_graph",
        consumers=("plasticity",),
        description="User feedback signal (thumbs up/down) for outcome tracking",
        direction="event",
    ),
    "plasticity.outcome.recorded": EventContract(
        name="plasticity.outcome.recorded",
        producer="plasticity",
        consumers=("orthodoxy_wardens",),
        description="Outcome recorded by OutcomeTracker, ready for learning cycle",
        direction="event",
    ),
}


# =============================================================================
# UNIFIED REGISTRY
# =============================================================================

CHANNEL_REGISTRY: Dict[str, EventContract] = {
    **_ORTHODOXY_CHANNELS,
    **_VAULT_CHANNELS,
    **_MEMORY_CHANNELS,
    **_CODEX_CHANNELS,
    **_BABEL_CHANNELS,
    **_PATTERN_CHANNELS,
    **_ORCHESTRATION_CHANNELS,
    **_INTEGRATION_CHANNELS,
    **_CONCLAVE_CHANNELS,
    **_PLASTICITY_CHANNELS,
}

# Frozen set of all valid channel names for fast O(1) validation
_VALID_CHANNELS: FrozenSet[str] = frozenset(CHANNEL_REGISTRY.keys())


# =============================================================================
# QUERY FUNCTIONS
# =============================================================================

def validate_channel(channel: str) -> bool:
    """Return True if channel is registered. Use before emitting."""
    return channel in _VALID_CHANNELS


def get_channels_for_consumer(service: str) -> Tuple[str, ...]:
    """
    Return all channels a given service should subscribe to.

    Usage in service config:
        from core.synaptic_conclave.channels import get_channels_for_consumer
        SACRED_CHANNELS = get_channels_for_consumer("vault_keepers")
    """
    return tuple(
        contract.name
        for contract in CHANNEL_REGISTRY.values()
        if service in contract.consumers and contract.status == "active"
    )


def get_channels_for_producer(producer: str) -> Tuple[str, ...]:
    """Return all channels a given producer is allowed to emit on."""
    return tuple(
        contract.name
        for contract in CHANNEL_REGISTRY.values()
        if contract.producer == producer and contract.status == "active"
    )


def get_contract(channel: str) -> Optional[EventContract]:
    """Get the EventContract for a channel, or None if not registered."""
    return CHANNEL_REGISTRY.get(channel)
