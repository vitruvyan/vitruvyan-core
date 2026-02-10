"""
Vitruvyan Core — Event Schema (Compatibility Shim)
===================================================

Re-exports event_schema from events layer for backward compatibility.

Canonical location: core.synaptic_conclave.events.event_schema

Some legacy nodes import directly from:
    from core.synaptic_conclave.event_schema import EventDomain, ...

This file provides that compatibility path.

Author: Vitruvyan Core Team  
Created: February 10, 2026
Status: COMPATIBILITY LAYER
"""

from core.synaptic_conclave.events.event_schema import (
    # Domains
    EventDomain,
    
    # Intents
    AuditIntent,
    VaultIntent,
    OrthodoxIntent,
    CodexIntent,
    GraphIntent,
    CrewIntent,
    SentinelIntent,
    BabelIntent,
    MemoryIntent,
    
    # Event creation helpers
    create_audit_alert_event,
    create_vault_snapshot_event,
    create_vault_restore_event,
    create_codex_data_refresh_request,
    create_codex_discovery_event,
    create_sentinel_risk_event,
    create_sentinel_emergency_event,
    
    # Payload dataclasses
    AuditAlertPayload,
    SentinelRiskPayload,
    SentinelEmergencyPayload,
    VaultSnapshotPayload,
    VaultRestorePayload,
    CodexDataRefreshPayload,
    CodexDiscoveryPayload,
    BabelSentimentPayload,
    BabelSentimentFusedPayload,
    BabelLanguagePayload,
)

__all__ = [
    # Domains
    "EventDomain",
    
    # Intents
    "AuditIntent",
    "VaultIntent",
    "OrthodoxIntent",
    "CodexIntent",
    "GraphIntent",
    "CrewIntent",
    "SentinelIntent",
    "BabelIntent",
    "MemoryIntent",
    
    # Event creation helpers
    "create_audit_alert_event",
    "create_vault_snapshot_event",
    "create_vault_restore_event",
    "create_codex_data_refresh_request",
    "create_codex_discovery_event",
    "create_sentinel_risk_event",
    "create_sentinel_emergency_event",
    
    # Payload dataclasses
    "AuditAlertPayload",
    "SentinelRiskPayload",
    "SentinelEmergencyPayload",
    "VaultSnapshotPayload",
    "VaultRestorePayload",
    "CodexDataRefreshPayload",
    "CodexDiscoveryPayload",
    "BabelSentimentPayload",
    "BabelSentimentFusedPayload",
    "BabelLanguagePayload",
]
