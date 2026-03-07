"""
Codex Hunters — Event Channel Constants
========================================

Canonical channel names for Codex Hunters Sacred Order.
Imports from the central channel_registry to stay aligned.

Created: Mar 07, 2026
"""

# --- Expedition lifecycle (graph node → listener) ---
EXPEDITION_STARTED = "codex.expedition.started"
EXPEDITION_COMPLETED = "codex.expedition.completed"
EXPEDITION_FAILED = "codex.expedition.failed"

# --- Discovery (outbound from Codex to other Sacred Orders) ---
DISCOVERY_MAPPED = "codex.discovery.mapped"

# --- Request channels (consumed by Codex listener, dispatched to API) ---
DATA_REFRESH_REQUESTED = "codex.data.refresh.requested"
TECHNICAL_MOMENTUM_REQUESTED = "codex.technical.momentum.requested"
TECHNICAL_TREND_REQUESTED = "codex.technical.trend.requested"
TECHNICAL_VOLATILITY_REQUESTED = "codex.technical.volatility.requested"
SCHEMA_VALIDATION_REQUESTED = "codex.schema.validation.requested"
FUNDAMENTALS_REFRESH_REQUESTED = "codex.fundamentals.refresh.requested"

# --- Oculus Prime evidence ingestion ---
OCULUS_EVIDENCE_CREATED = "oculus_prime.evidence.created"
OCULUS_EVIDENCE_CREATED_LEGACY = "intake.evidence.created"

# All request channels the Codex listener should consume
CODEX_REQUEST_CHANNELS = (
    DATA_REFRESH_REQUESTED,
    TECHNICAL_MOMENTUM_REQUESTED,
    TECHNICAL_TREND_REQUESTED,
    TECHNICAL_VOLATILITY_REQUESTED,
    SCHEMA_VALIDATION_REQUESTED,
    FUNDAMENTALS_REFRESH_REQUESTED,
)

# Expedition type mapping (channel → expedition_type for API dispatch)
CHANNEL_TO_EXPEDITION_TYPE = {
    DATA_REFRESH_REQUESTED: "data_refresh",
    TECHNICAL_MOMENTUM_REQUESTED: "momentum_backfill",
    TECHNICAL_TREND_REQUESTED: "trend_backfill",
    TECHNICAL_VOLATILITY_REQUESTED: "volatility_backfill",
    SCHEMA_VALIDATION_REQUESTED: "schema_validation",
    FUNDAMENTALS_REFRESH_REQUESTED: "fundamentals_refresh",
}
