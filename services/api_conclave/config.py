"""
🕯 Synaptic Conclave — Service Configuration

Single source of truth for all environment variables.
No os.getenv() scattered across files.

Follows SERVICE_PATTERN.md (LIVELLO 2).
"""

import os


class Settings:
    """Centralized configuration for api_conclave service."""

    # Service identity
    SERVICE_NAME = "api_conclave"
    SERVICE_VERSION = "2.0.0"
    SERVICE_PORT = int(os.getenv("CONCLAVE_PORT", "8012"))
    SERVICE_HOST = os.getenv("CONCLAVE_HOST", "0.0.0.0")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Redis / Cognitive Bus
    REDIS_HOST = os.getenv("REDIS_HOST", "omni_redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

    # Consumer group (for streams_listener.py)
    CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "conclave_observatory")
    CONSUMER_NAME = os.getenv("CONSUMER_NAME", "observatory_1")

    # Sacred Channels observed (Epistemic Observatory)
    SACRED_CHANNELS = [
        # Orchestration
        "conclave.events.broadcast",
        "conclave.health.ping",
        "conclave.awakened",
        # System-wide
        "epistemic.drift.detected",
        "epistemic.coherence.alert",
        # Memory Orders
        "memory.write.completed",
        "memory.sync.requested",
        "memory.coherence.checked",
        # Codex Hunters (Perception)
        "codex.discovery.mapped",
        "codex.reddit.scraped",
        "codex.news.collected",
        "codex.refresh.scheduled",
        # Neural Engine (Reason)
        "neural_engine.screening.completed",
        "neural_engine.comparison.completed",
        "neural_engine.risk.assessed",
        # Babel Gardens (Discourse)
        "babel.sentiment.completed",
        "babel.fusion.completed",
        "babel.emotion.detected",
        "babel.translation.completed",
        # Orthodoxy Wardens (Truth)
        "orthodoxy.audit.requested",
        "orthodoxy.validation.completed",
        "orthodoxy.heresy.detected",
        # Vault Keepers (Truth)
        "vault.archive.completed",
        "vault.retrieval.requested",
        "vault.snapshot.created",
        # LangGraph (Orchestration)
        "langgraph.response.completed",
        "langgraph.comparison.routed",
        "langgraph.screening.executed",
        # Pattern Weavers
        "pattern_weavers.context.extracted",
        "pattern_weavers.weave.completed",
    ]


settings = Settings()
