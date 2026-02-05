#!/usr/bin/env python3
"""
    Cognitive Bus Event Schema
=========================

Definisce gli schemi eventi standardizzati per:
- Audit Engine events
- Vault Keepers events  
- Cross-module communication
- Event validation and routing

Conforme alla checklist: domain:intent:payload pattern

Author: Vitruvian Development Team
Created: 2025-01-15 - Compliance Implementation
"""
    
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


class EventDomain(Enum):
    """Event domains for categorization"""
    AUDIT = "audit"
    VAULT = "vault"
    ORTHODOXY = "orthodoxy"
    CODEX = "codex"
    GRAPH = "graph"
    NEURAL = "neural"
    CREW = "crew"
    GEMMA = "gemma"
    SENTINEL = "sentinel"
    BABEL = "babel"
    MEMORY = "memory"
    SYSTEM = "system"


class AuditIntent(Enum):
    """Audit Engine event intents"""
    ALERT_DATA_INCONSISTENT = "alert.data_inconsistent"
    ALERT_CONTAINER_DOWN = "alert.container_down"
    ALERT_BACKFILL_NEEDED = "alert.backfill_needed"
    REPORT_GENERATED = "report.generated"
    HEALTH_CHECK_COMPLETED = "health.check_completed"
    INTEGRITY_VERIFICATION = "integrity.verification"
    

class VaultIntent(Enum):
    """Vault Keepers event intents - Phase 4.4 Sacred Orders"""
    # Incoming requests to Vault Keepers
    INTEGRITY_CHECK_REQUESTED = "integrity.check.requested"
    BACKUP_CREATE_REQUESTED = "backup.create.requested"
    RECOVERY_EXECUTE_REQUESTED = "recovery.execute.requested"
    AUDIT_VAULT_REQUESTED = "audit.vault.requested"
    
    # Outgoing responses from Vault Keepers
    INTEGRITY_VERIFIED = "integrity.verified"
    INTEGRITY_FAILED = "integrity.failed"
    BACKUP_CREATED = "backup.created"
    BACKUP_FAILED = "backup.failed"
    RECOVERY_EXECUTED = "recovery.executed"
    RECOVERY_FAILED = "recovery.failed"
    AUDIT_COMPLETED = "audit.completed"
    PROTECTION_GRANTED = "protection.granted"
    
    # Legacy backup events (for compatibility)
    SNAPSHOT_REQUESTED = "snapshot.requested"
    SNAPSHOT_STARTED = "snapshot.started"
    SNAPSHOT_COMPLETED = "snapshot.completed"
    SNAPSHOT_FAILED = "snapshot.failed"
    RESTORE_REQUESTED = "restore.requested"
    RESTORE_STARTED = "restore.started"  
    RESTORE_COMPLETED = "restore.completed"
    RESTORE_FAILED = "restore.failed"
    BACKUP_INCREMENTAL = "backup.incremental"


class OrthodoxIntent(Enum):
    """Orthodoxy Wardens event intents - Phase 4.1 Sacred Orders"""
    # Incoming requests to Orthodoxy Wardens
    AUDIT_REQUESTED = "audit.requested"
    CONFESSION_REQUESTED = "confession.requested"
    ABSOLUTION_REQUESTED = "absolution.requested"
    
    # Outgoing responses from Orthodoxy Wardens
    CONFESSION_STARTED = "confession.started"
    CONFESSION_HEARD = "confession.heard"
    PENANCE_ASSIGNED = "penance.assigned"
    ABSOLUTION_GRANTED = "absolution.granted"
    HEALING_APPLIED = "healing.applied"
    CHRONICLE_RECORDED = "chronicle.recorded"


class CodexIntent(Enum):
    """Codex Hunters event intents (extended for PHASE 4.5)"""
    # Incoming requests to Codex Hunters
    DATA_REFRESH_REQUESTED = "data.refresh.requested"
    DATA_DISCOVERY_REQUESTED = "data.discovery.requested"
    
    # Outgoing responses from Codex Hunters
    DISCOVERY_MAPPED = "discovery.mapped"
    DISCOVERY_FAILED = "discovery.failed"
    
    # Legacy events (for compatibility)
    NEW_DISCOVERY = "new_discovery"
    INTEGRITY_ALERT = "integrity.alert"
    EXPEDITION_COMPLETED = "expedition.completed"


class SentinelIntent(Enum):
    """Sentinel Order event intents - Phase 4.7 Collection Guardian Cognitive Integration"""
    # Risk assessment events
    RISK_ASSESSED = "risk.assessed"
    ALERT_ISSUED = "alert.issued"
    EMERGENCY_TRIGGERED = "emergency.triggered"
    
    # Recovery and protection events
    RECOVERY_STARTED = "recovery.started"
    RECOVERY_COMPLETED = "recovery.completed"
    PROTECTION_ACTIVATED = "protection.activated"
    
    # Escalation events
    ESCALATION_TRIGGERED = "escalation.triggered"
    BACKUP_REQUESTED = "backup.requested"
    AUDIT_REQUESTED = "audit.requested"


class CrewIntent(Enum):
    """CrewAI Strategic Order event intents - Phase 4.6 Cognitive Integration"""
    # Incoming requests to CrewAI
    STRATEGY_ANALYSIS_REQUESTED = "strategy.analysis.requested"
    TREND_ANALYSIS_REQUESTED = "trend.analysis.requested"
    MOMENTUM_ANALYSIS_REQUESTED = "momentum.analysis.requested"
    VOLATILITY_ANALYSIS_REQUESTED = "volatility.analysis.requested"
    RISK_ANALYSIS_REQUESTED = "risk.analysis.requested"
    PORTFOLIO_ANALYSIS_REQUESTED = "collection.analysis.requested"
    BACKTEST_REQUESTED = "backtest.requested"
    
    # Outgoing responses from CrewAI
    STRATEGY_GENERATED = "strategy.generated"
    TREND_COMPLETED = "trend.completed"
    MOMENTUM_COMPLETED = "momentum.completed"
    VOLATILITY_COMPLETED = "volatility.completed"
    RISK_COMPLETED = "risk.completed"
    PORTFOLIO_COMPLETED = "collection.completed"
    BACKTEST_COMPLETED = "backtest.completed"
    
    # Task lifecycle events
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"


class BabelIntent(Enum):
    """Babel Gardens event intents - EPOCH II Linguistic & Sentiment Fusion"""
    # Incoming requests to Babel Gardens
    SENTIMENT_REQUESTED = "sentiment.requested"
    LINGUISTIC_ANALYSIS_REQUESTED = "linguistic.analysis.requested"
    
    # Outgoing responses from Babel Gardens
    SENTIMENT_FUSED = "sentiment.fused"
    LANGUAGE_INTERPRETED = "language.interpreted"
    
    # Legacy events (for compatibility)
    LINGUISTIC_SYNTHESIS = "linguistic.synthesis"
    MULTILINGUAL_BRIDGE = "multilingual.bridge"
    KNOWLEDGE_CULTIVATION = "knowledge.cultivation"
    CULTIVATION_STARTED = "cultivation.started"
    CULTIVATION_COMPLETED = "cultivation.completed"
    CULTIVATION_FAILED = "cultivation.failed"


class MemoryIntent(Enum):
    """Memory Orders event intents - EPOCH II Dual Memory System (Archivarium + Mnemosyne)"""
    # Incoming requests to Memory Orders
    READ_REQUESTED = "read.requested"
    WRITE_REQUESTED = "write.requested"
    CLEAN_REQUESTED = "clean.requested"
    SEARCH_REQUESTED = "search.requested"
    
    # Outgoing responses from Memory Orders
    READ_FULFILLED = "read.fulfilled"
    WRITE_COMPLETED = "write.completed"
    CLEAN_EXECUTED = "clean.executed"
    VECTOR_MATCH = "vector.match"
    SEARCH_COMPLETED = "search.completed"
    
    # Memory lifecycle events
    MEMORY_INDEXED = "memory.indexed"
    MEMORY_EXPIRED = "memory.expired"
    MEMORY_CORRUPTED = "memory.corrupted"


class GraphIntent(Enum):
    """LangGraph event intents"""
    ERROR = "error"
    RESTORE_REQUEST = "restore.request"
    AUDIT_REQUEST = "audit.request"
    NOTIFICATION = "notification"


# Standard event payload schemas
@dataclass
class AuditAlertPayload:
    """Payload schema for audit alerts"""
    alert_type: str                    # "data_inconsistent", "container_down", "backfill_needed"
    severity: str                      # "critical", "high", "medium", "low"
    affected_components: List[str]     # Components affected
    description: str                   # Human-readable description
    suggested_actions: List[str]       # Recommended actions
    metadata: Dict[str, Any]          # Additional context
    correlation_id: Optional[str] = None


@dataclass
class SentinelRiskPayload:
    """Payload schema for sentinel risk assessment events"""
    risk_score: float                  # 0.0 to 1.0 risk score
    portfolio_value: float             # Current collection value
    daily_pnl_pct: float              # Daily P&L percentage
    drawdown: float                    # Current drawdown
    market_condition: str              # "bull_market", "bear_market", "high_volatility", etc.
    alerts: List[str]                  # List of active alert types
    protection_mode: str               # "conservative", "balanced", "aggressive", "emergency"
    recommended_actions: List[str]     # Suggested actions
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class SentinelEmergencyPayload:
    """Payload schema for sentinel emergency events"""
    emergency_type: str                # "market_crash", "portfolio_breach", "system_failure"
    severity: str                      # "critical", "emergency"
    reason: str                        # Human-readable emergency reason
    portfolio_impact: float            # Estimated impact (loss percentage)
    triggered_by: str                  # What triggered the emergency
    immediate_actions: List[str]       # Actions taken immediately
    escalation_required: bool          # Whether escalation is needed
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class VaultSnapshotPayload:
    """Payload schema for vault snapshot events"""
    snapshot_id: str                   # Unique snapshot identifier
    snapshot_type: str                 # "full", "incremental", "emergency"
    target_components: List[str]       # ["postgresql", "qdrant", "redis"]
    file_path: Optional[str] = None    # Path to backup file
    checksum: Optional[str] = None     # SHA256 checksum
    size_bytes: Optional[int] = None   # Backup size
    metadata: Dict[str, Any] = None    # Additional data


@dataclass
class VaultRestorePayload:
    """Payload schema for vault restore events"""
    restore_id: str                    # Unique restore identifier
    snapshot_id: str                   # Source snapshot
    target_components: List[str]       # Components to restore
    restore_mode: str                  # "full", "selective", "test"
    validation_required: bool = True   # Whether validation is needed
    metadata: Dict[str, Any] = None    


@dataclass
class CodexDataRefreshPayload:
    """Payload schema for data refresh requests (PHASE 4.5)"""
    entity_id: Optional[str] = None               # Specific entity_id to refresh
    entity_ids: Optional[List[str]] = None        # Multiple entity_ids to refresh
    sources: Optional[List[str]] = None        # Data sources to query
    priority: str = "medium"                   # "critical", "high", "medium", "low"
    batch_size: int = 10                       # Batch processing size
    correlation_id: Optional[str] = None       # For tracking event chains
    metadata: Dict[str, Any] = None            # Additional context


@dataclass
class CodexDiscoveryPayload:
    """Payload schema for codex discovery events"""
    discovery_id: str                  # Discovery session ID
    collections_mapped: List[str]      # Collections analyzed
    consistency_scores: Dict[str, float]  # Collection -> score
    inconsistencies_found: int         # Total inconsistencies
    recommendations: List[str]         # Action recommendations
    sources_found: Optional[List[str]] = None  # Sources discovered (PHASE 4.5)
    expedition_type: Optional[str] = None      # Type of expedition
    metadata: Dict[str, Any] = None


@dataclass
class BabelSentimentPayload:
    """Payload schema for Babel sentiment analysis - EPOCH II"""
    entity_id: Optional[str] = None               # Single entity_id
    entity_ids: Optional[List[str]] = None        # Multiple entity_ids
    text: Optional[str] = None                 # Direct text analysis
    language: Optional[str] = None             # Target language (en, it, es, etc.)
    mode: str = "enhanced"                     # "enhanced", "conservative", "aggressive"
    cultural_weighting: bool = True            # Apply cultural volatility weights
    correlation_id: Optional[str] = None       # Event correlation
    metadata: Dict[str, Any] = None


@dataclass
class BabelSentimentFusedPayload:
    """Payload schema for Babel sentiment fusion results - EPOCH II"""
    entity_id: Optional[str] = None               # Analyzed entity_id
    sentiment_score: float = 0.0               # -1.0 to 1.0
    sentiment_label: str = "neutral"           # "positive", "neutral", "negative"
    confidence: float = 0.0                    # 0.0 to 1.0
    language: Optional[str] = None             # Detected language
    fusion_method: str = "gemma_finbert"       # Fusion algorithm used
    cultural_adjustment: Optional[float] = None # Cultural weighting applied
    sources: Optional[List[str]] = None        # Data sources analyzed
    error: Optional[str] = None                # Error message if failed
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class BabelLanguagePayload:
    """Payload schema for Babel linguistic interpretation - EPOCH II"""
    text: str                                  # Text to analyze
    source_language: Optional[str] = None      # Original language
    target_languages: Optional[List[str]] = None  # Translation targets
    semantic_embedding: Optional[List[float]] = None  # 384-dim vector
    cultural_context: Optional[str] = None     # Cultural markers
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class MemoryReadPayload:
    """Payload schema for Memory read requests - EPOCH II"""
    query: str                                 # Search query
    collection: Optional[str] = None           # "phrases", "entity_ids", etc.
    limit: int = 10                           # Max results
    memory_type: str = "dual"                 # "archivarium", "mnemosyne", "dual"
    time_range: Optional[Dict[str, str]] = None  # {"start": ISO, "end": ISO}
    filters: Optional[Dict[str, Any]] = None   # Additional filters
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class MemoryReadFulfilledPayload:
    """Payload schema for Memory read fulfilled responses - EPOCH II"""
    query: str                                 # Original query
    results: List[Dict[str, Any]]             # Retrieved records
    source: str                                # "archivarium" (PostgreSQL)
    count: int = 0                            # Number of results
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class MemoryVectorMatchPayload:
    """Payload schema for Memory vector search results - EPOCH II"""
    query: str                                 # Original query
    matches: List[Dict[str, Any]]             # Vector search results
    source: str = "mnemosyne"                 # Qdrant collection
    scores: Optional[List[float]] = None       # Similarity scores
    count: int = 0
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class MemoryWritePayload:
    """Payload schema for Memory write requests - EPOCH II"""
    data: Dict[str, Any]                      # Data to write
    collection: str                            # Target collection
    memory_type: str = "dual"                 # "archivarium", "mnemosyne", "dual"
    embedding_required: bool = True            # Create vector embedding
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = None


# Event validation utilities
class EventSchemaValidator:
    """Validates event payloads against schemas"""
    
    @staticmethod
    def validate_audit_alert(payload: Dict[str, Any]) -> bool:
        """Validate audit alert payload"""
        required_fields = ['alert_type', 'severity', 'affected_components', 'description']
        return all(field in payload for field in required_fields)
    
    @staticmethod
    def validate_vault_snapshot(payload: Dict[str, Any]) -> bool:
        """Validate vault snapshot payload"""
        required_fields = ['snapshot_id', 'snapshot_type', 'target_components']
        return all(field in payload for field in required_fields)
    
    @staticmethod
    def validate_vault_restore(payload: Dict[str, Any]) -> bool:
        """Validate vault restore payload"""
        required_fields = ['restore_id', 'snapshot_id', 'target_components', 'restore_mode']
        return all(field in payload for field in required_fields)
    
    @staticmethod
    def validate_codex_data_refresh(payload: Dict[str, Any]) -> bool:
        """Validate codex data refresh request payload (PHASE 4.5)"""
        # At least one entity_id specification is required
        has_entity = payload.get('entity_id') is not None
        has_entitys = payload.get('entity_ids') is not None and len(payload.get('entity_ids', [])) > 0
        
        return has_entity or has_entitys
    
    @staticmethod
    def validate_codex_discovery(payload: Dict[str, Any]) -> bool:
        """Validate codex discovery payload"""
        required_fields = ['discovery_id', 'collections_mapped', 'consistency_scores']
        return all(field in payload for field in required_fields)
    
    @staticmethod
    def validate_babel_sentiment(payload: Dict[str, Any]) -> bool:
        """Validate Babel sentiment request payload - EPOCH II"""
        has_entity = payload.get('entity_id') is not None
        has_entitys = payload.get('entity_ids') is not None and len(payload.get('entity_ids', [])) > 0
        has_text = payload.get('text') is not None
        
        return has_entity or has_entitys or has_text
    
    @staticmethod
    def validate_memory_read(payload: Dict[str, Any]) -> bool:
        """Validate Memory read request payload - EPOCH II"""
        return 'query' in payload
    
    @staticmethod
    def validate_memory_write(payload: Dict[str, Any]) -> bool:
        """Validate Memory write request payload - EPOCH II"""
        required_fields = ['data', 'collection']
        return all(field in payload for field in required_fields)


# Event factory functions
def create_audit_alert_event(
    alert_type: str,
    severity: str,
    affected_components: List[str],
    description: str,
    suggested_actions: List[str],
    emitter: str = "audit_engine",
    target: str = "system",
    **kwargs
) -> Dict[str, Any]:
    """Create standardized audit alert event"""
    
    payload = AuditAlertPayload(
        alert_type=alert_type,
        severity=severity,
        affected_components=affected_components,
        description=description,
        suggested_actions=suggested_actions,
        metadata=kwargs.get('metadata', {}),
        correlation_id=kwargs.get('correlation_id')
    )
    
    return {
        "event_type": f"{EventDomain.AUDIT.value}.{AuditIntent.ALERT_DATA_INCONSISTENT.value}",
        "emitter": emitter,
        "target": target,
        "payload": payload.__dict__,
        "timestamp": datetime.utcnow().isoformat(),
        "correlation_id": kwargs.get('correlation_id')
    }


def create_vault_snapshot_event(
    snapshot_id: str,
    snapshot_type: str,
    target_components: List[str],
    intent: VaultIntent,
    emitter: str = "vault_keepers",
    target: str = "audit_engine",
    **kwargs
) -> Dict[str, Any]:
    """Create standardized vault snapshot event"""
    
    payload = VaultSnapshotPayload(
        snapshot_id=snapshot_id,
        snapshot_type=snapshot_type,
        target_components=target_components,
        file_path=kwargs.get('file_path'),
        checksum=kwargs.get('checksum'),
        size_bytes=kwargs.get('size_bytes'),
        metadata=kwargs.get('metadata', {})
    )
    
    return {
        "event_type": f"{EventDomain.VAULT.value}.{intent.value}",
        "emitter": emitter,
        "target": target,
        "payload": payload.__dict__,
        "timestamp": datetime.utcnow().isoformat(),
        "correlation_id": kwargs.get('correlation_id')
    }


def create_vault_restore_event(
    restore_id: str,
    snapshot_id: str,
    target_components: List[str],
    restore_mode: str,
    intent: VaultIntent,
    emitter: str = "vault_keepers",
    target: str = "audit_engine",
    **kwargs
) -> Dict[str, Any]:
    """Create standardized vault restore event"""
    
    payload = VaultRestorePayload(
        restore_id=restore_id,
        snapshot_id=snapshot_id,
        target_components=target_components,
        restore_mode=restore_mode,
        validation_required=kwargs.get('validation_required', True),
        metadata=kwargs.get('metadata', {})
    )
    
    return {
        "event_type": f"{EventDomain.VAULT.value}.{intent.value}",
        "emitter": emitter,
        "target": target,
        "payload": payload.__dict__,
        "timestamp": datetime.utcnow().isoformat(),
        "correlation_id": kwargs.get('correlation_id')
    }


def create_codex_data_refresh_request(
    emitter: str = "langgraph",
    target: str = "codex_hunters",
    entity_id: str = None,
    entity_ids: List[str] = None,
    sources: List[str] = None,
    priority: str = "medium",
    **kwargs
) -> Dict[str, Any]:
    """Create standardized data refresh request event (PHASE 4.5)"""
    
    payload = CodexDataRefreshPayload(
        entity_id=entity_id,
        entity_ids=entity_ids,
        sources=sources or ["yfinance", "reddit", "google_news"],
        priority=priority,
        batch_size=kwargs.get('batch_size', 10),
        correlation_id=kwargs.get('correlation_id'),
        metadata=kwargs.get('metadata', {})
    )
    
    return {
        "event_type": f"{EventDomain.CODEX.value}.{CodexIntent.DATA_REFRESH_REQUESTED.value}",
        "emitter": emitter,
        "target": target,
        "payload": payload.__dict__,
        "timestamp": datetime.utcnow().isoformat(),
        "correlation_id": kwargs.get('correlation_id')
    }


def create_codex_discovery_event(
    discovery_id: str,
    collections_mapped: List[str],
    consistency_scores: Dict[str, float],
    inconsistencies_found: int,
    recommendations: List[str],
    intent: CodexIntent = CodexIntent.DISCOVERY_MAPPED,
    emitter: str = "codex_hunters",
    target: str = "langgraph",
    **kwargs
) -> Dict[str, Any]:
    """Create standardized codex discovery response event (PHASE 4.5 extended)"""
    
    payload = CodexDiscoveryPayload(
        discovery_id=discovery_id,
        collections_mapped=collections_mapped,
        consistency_scores=consistency_scores,
        inconsistencies_found=inconsistencies_found,
        recommendations=recommendations,
        sources_found=kwargs.get('sources_found', []),
        expedition_type=kwargs.get('expedition_type', 'data_refresh'),
        metadata=kwargs.get('metadata', {})
    )
    
    return {
        "event_type": f"{EventDomain.CODEX.value}.{intent.value}",
        "emitter": emitter,
        "target": target,
        "payload": payload.__dict__,
        "timestamp": datetime.utcnow().isoformat(),
        "correlation_id": kwargs.get('correlation_id')
    }


def create_sentinel_risk_event(
    risk_score: float,
    portfolio_value: float,
    daily_pnl_pct: float,
    drawdown: float,
    market_condition: str,
    alerts: List[str],
    protection_mode: str,
    recommended_actions: List[str],
    emitter: str = "portfolio_guardian",
    target: str = "conclave",
    **kwargs
) -> Dict[str, Any]:
    """Create standardized sentinel risk assessment event"""
    
    payload = SentinelRiskPayload(
        risk_score=risk_score,
        portfolio_value=portfolio_value,
        daily_pnl_pct=daily_pnl_pct,
        drawdown=drawdown,
        market_condition=market_condition,
        alerts=alerts,
        protection_mode=protection_mode,
        recommended_actions=recommended_actions,
        correlation_id=kwargs.get('correlation_id'),
        metadata=kwargs.get('metadata', {})
    )
    
    return {
        "event_type": f"{EventDomain.SENTINEL.value}.{SentinelIntent.RISK_ASSESSED.value}",
        "emitter": emitter,
        "target": target,
        "payload": payload.__dict__,
        "timestamp": datetime.utcnow().isoformat(),
        "correlation_id": kwargs.get('correlation_id')
    }


def create_sentinel_emergency_event(
    emergency_type: str,
    severity: str,
    reason: str,
    portfolio_impact: float,
    triggered_by: str,
    immediate_actions: List[str],
    escalation_required: bool,
    emitter: str = "portfolio_guardian",
    target: str = "conclave",
    **kwargs
) -> Dict[str, Any]:
    """Create standardized sentinel emergency event"""
    
    payload = SentinelEmergencyPayload(
        emergency_type=emergency_type,
        severity=severity,
        reason=reason,
        portfolio_impact=portfolio_impact,
        triggered_by=triggered_by,
        immediate_actions=immediate_actions,
        escalation_required=escalation_required,
        correlation_id=kwargs.get('correlation_id'),
        metadata=kwargs.get('metadata', {})
    )
    
    return {
        "event_type": f"{EventDomain.SENTINEL.value}.{SentinelIntent.EMERGENCY_TRIGGERED.value}",
        "emitter": emitter,
        "target": target,
        "payload": payload.__dict__,
        "timestamp": datetime.utcnow().isoformat(),
        "correlation_id": kwargs.get('correlation_id')
    }


# Event routing configuration
EVENT_ROUTING_MAP = {
    # Audit Engine listens to these events
    "audit_engine": [
        f"{EventDomain.CODEX.value}.{CodexIntent.DISCOVERY_MAPPED.value}",
        f"{EventDomain.CODEX.value}.{CodexIntent.DISCOVERY_FAILED.value}",
        f"{EventDomain.GRAPH.value}.{GraphIntent.ERROR.value}",
        f"{EventDomain.NEURAL.value}.partial_results",
        f"{EventDomain.CREW.value}.failure",
        f"{EventDomain.GEMMA.value}.alert",
        f"{EventDomain.VAULT.value}.{VaultIntent.SNAPSHOT_COMPLETED.value}",
        f"{EventDomain.SENTINEL.value}.{SentinelIntent.AUDIT_REQUESTED.value}"
    ],
    
    # Codex Hunters listens to these events (PHASE 4.5)
    "codex_hunters": [
        f"{EventDomain.CODEX.value}.{CodexIntent.DATA_REFRESH_REQUESTED.value}",
        f"{EventDomain.CODEX.value}.{CodexIntent.DATA_DISCOVERY_REQUESTED.value}",
        f"{EventDomain.GRAPH.value}.{GraphIntent.AUDIT_REQUEST.value}"
    ],
    
    # Vault Keepers listens to these events
    "vault_keepers": [
        f"{EventDomain.AUDIT.value}.{AuditIntent.ALERT_BACKFILL_NEEDED.value}",
        f"{EventDomain.GRAPH.value}.{GraphIntent.RESTORE_REQUEST.value}",
        f"{EventDomain.CODEX.value}.{CodexIntent.NEW_DISCOVERY.value}",
        f"{EventDomain.SENTINEL.value}.{SentinelIntent.BACKUP_REQUESTED.value}",
        f"{EventDomain.SENTINEL.value}.{SentinelIntent.EMERGENCY_TRIGGERED.value}"
    ],
    
    # Collection Guardian / Sentinel Order listens to these events
    "portfolio_guardian": [
        f"{EventDomain.ORTHODOXY.value}.{OrthodoxIntent.HEALING_APPLIED.value}",
        f"{EventDomain.VAULT.value}.{VaultIntent.BACKUP_CREATED.value}",
        f"{EventDomain.VAULT.value}.{VaultIntent.PROTECTION_GRANTED.value}",
        f"{EventDomain.AUDIT.value}.{AuditIntent.REPORT_GENERATED.value}"
    ],
    
    # LangGraph listens to these events
    "langgraph": [
        f"{EventDomain.AUDIT.value}.{AuditIntent.ALERT_DATA_INCONSISTENT.value}",
        f"{EventDomain.AUDIT.value}.{AuditIntent.REPORT_GENERATED.value}",
        f"{EventDomain.VAULT.value}.{VaultIntent.RESTORE_COMPLETED.value}",
        f"{EventDomain.SENTINEL.value}.{SentinelIntent.RISK_ASSESSED.value}",
        f"{EventDomain.SENTINEL.value}.{SentinelIntent.EMERGENCY_TRIGGERED.value}",
        f"{EventDomain.CODEX.value}.{CodexIntent.DISCOVERY_MAPPED.value}",
        f"{EventDomain.CODEX.value}.{CodexIntent.DISCOVERY_FAILED.value}"
    ],
    
    # Orthodoxy Wardens listens to these events
    "orthodoxy_wardens": [
        f"{EventDomain.SENTINEL.value}.{SentinelIntent.ALERT_ISSUED.value}",
        f"{EventDomain.SENTINEL.value}.{SentinelIntent.EMERGENCY_TRIGGERED.value}",
        f"{EventDomain.AUDIT.value}.{AuditIntent.ALERT_DATA_INCONSISTENT.value}"
    ]
}


if __name__ == "__main__":
    # Test event creation
    print("🧪 Testing Event Schema (PHASE 4.5 Extended)...")
    
    # Test audit alert
    alert_event = create_audit_alert_event(
        alert_type="data_inconsistent",
        severity="critical",
        affected_components=["postgresql", "qdrant"],
        description="Data consistency check failed",
        suggested_actions=["Run integrity check", "Execute backup restore"],
        correlation_id="test_001"
    )
    
    print("✅ Audit Alert Event:", alert_event)
    
    # Test vault snapshot
    snapshot_event = create_vault_snapshot_event(
        snapshot_id="snap_001", 
        snapshot_type="emergency",
        target_components=["postgresql"],
        intent=VaultIntent.SNAPSHOT_COMPLETED,
        checksum="abc123",
        correlation_id="test_001"
    )
    
    print("✅ Vault Snapshot Event:", snapshot_event)
    
    # Test PHASE 4.5 Codex data refresh request
    refresh_request = create_codex_data_refresh_request(
        entity_id="EXAMPLE_ENTITY_1",
        sources=["yfinance", "reddit"],
        priority="high",
        correlation_id="test_codex_001"
    )
    
    print("✅ Codex Data Refresh Request:", refresh_request)
    
    # Test PHASE 4.5 Codex discovery response
    discovery_response = create_codex_discovery_event(
        discovery_id="discovery_001",
        collections_mapped=["phrases", "entity_ids"],
        consistency_scores={"phrases": 0.95, "entity_ids": 0.98},
        inconsistencies_found=2,
        recommendations=["Update AAPL price data", "Refresh sentiment analysis"],
        sources_found=["yahoo", "reddit_post_12345"],
        expedition_type="data_refresh",
        correlation_id="test_codex_001"
    )
    
    print("✅ Codex Discovery Response:", discovery_response)
    
    # Validate schemas
    validator = EventSchemaValidator()
    
    alert_valid = validator.validate_audit_alert(alert_event["payload"])
    snapshot_valid = validator.validate_vault_snapshot(snapshot_event["payload"])
    refresh_valid = validator.validate_codex_data_refresh(refresh_request["payload"])
    discovery_valid = validator.validate_codex_discovery(discovery_response["payload"])
    
    print(f"✅ Alert validation: {alert_valid}")
    print(f"✅ Snapshot validation: {snapshot_valid}")
    print(f"✅ Codex Refresh validation: {refresh_valid}")
    print(f"✅ Codex Discovery validation: {discovery_valid}")
    
    print("\n🗺️ PHASE 4.5 Event Schema Update: COMPLETE ✅")