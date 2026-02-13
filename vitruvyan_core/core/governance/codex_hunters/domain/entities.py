"""
Codex Hunters - Domain Entities
===============================

Immutable dataclasses representing core domain concepts.
These are pure data structures with no I/O dependencies.

Author: Vitruvyan Core Team
Created: February 2026
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class ExpeditionStatus(str, Enum):
    """Status of an expedition."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EntityStatus(str, Enum):
    """Status of a discovered entity."""
    DISCOVERED = "discovered"
    RESTORED = "restored"
    BOUND = "bound"
    VERIFIED = "verified"
    INVALID = "invalid"


class Severity(str, Enum):
    """Event severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True)
class CodexEvent:
    """
    Immutable event representing a Codex Hunters action.
    
    Used for internal event passing between consumers.
    Transport-layer events are handled separately in LIVELLO 2.
    """
    event_type: str
    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    target: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    severity: Severity = Severity.INFO
    correlation_id: Optional[str] = None
    
    def with_payload(self, **kwargs) -> 'CodexEvent':
        """Create new event with additional payload data."""
        new_payload = {**self.payload, **kwargs}
        return CodexEvent(
            event_type=self.event_type,
            source=self.source,
            timestamp=self.timestamp,
            target=self.target,
            payload=new_payload,
            severity=self.severity,
            correlation_id=self.correlation_id
        )


@dataclass(frozen=True)
class DiscoveredEntity:
    """
    Represents a discovered entity from a data source.
    
    Domain-agnostic: 'entity_id' can be any identifier.
    Additional fields stored in 'metadata'.
    """
    entity_id: str
    source: str
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: EntityStatus = EntityStatus.DISCOVERED


@dataclass(frozen=True)
class RestoredEntity:
    """
    Represents a normalized/restored entity.
    
    After discovery, entities are normalized to a standard format.
    """
    entity_id: str
    source: str
    restored_at: datetime = field(default_factory=datetime.utcnow)
    normalized_data: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 1.0  # 0.0 to 1.0
    validation_errors: List[str] = field(default_factory=list)
    status: EntityStatus = EntityStatus.RESTORED


@dataclass(frozen=True)
class BoundEntity:
    """
    Represents a permanently stored entity.
    
    After restoration, entities are bound to persistent storage.
    """
    entity_id: str
    source: str
    bound_at: datetime = field(default_factory=datetime.utcnow)
    storage_refs: Dict[str, str] = field(default_factory=dict)  # storage_type -> ref_id
    embedding_id: Optional[str] = None
    dedupe_key: Optional[str] = None
    status: EntityStatus = EntityStatus.BOUND


@dataclass(frozen=True)
class ExpeditionRequest:
    """
    Request to start an expedition.
    
    Expeditions are batch operations that discover, restore, and bind entities.
    """
    expedition_id: str
    expedition_type: str  # "discovery", "restoration", "full_cycle", etc.
    entity_ids: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: str = "medium"  # "critical", "high", "medium", "low"
    correlation_id: Optional[str] = None
    requested_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExpeditionResult:
    """
    Result of a completed expedition.
    
    Mutable to allow incremental updates during processing.
    """
    expedition_id: str
    status: ExpeditionStatus = ExpeditionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Counts
    entities_discovered: int = 0
    entities_restored: int = 0
    entities_bound: int = 0
    entities_failed: int = 0
    
    # Details
    discovered_entities: List[DiscoveredEntity] = field(default_factory=list)
    restored_entities: List[RestoredEntity] = field(default_factory=list)
    bound_entities: List[BoundEntity] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    # Metrics
    processing_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "expedition_id": self.expedition_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "entities_discovered": self.entities_discovered,
            "entities_restored": self.entities_restored,
            "entities_bound": self.entities_bound,
            "entities_failed": self.entities_failed,
            "errors": self.errors,
            "processing_time_ms": self.processing_time_ms,
        }


class ConsistencyStatus(str, Enum):
    """Consistency status classification."""
    EXCELLENT = "excellent"  # >= 95%
    GOOD = "good"            # >= 85%
    POOR = "poor"            # >= 70%
    CRITICAL = "critical"    # >= 50%
    EMPTY = "empty"          # both sides have 0 records
    ERROR = "error"          # computation failed


@dataclass(frozen=True)
class CollectionPairInput:
    """
    Input data for a single collection-pair consistency check.

    Domain-agnostic: represents any two mirrored data stores
    (e.g. relational DB ↔ vector DB, primary ↔ replica).
    """
    collection_name: str
    source_a_count: int            # record count in store A
    source_b_count: int            # record count in store B
    source_a_ids: List[str] = field(default_factory=list)  # IDs present in A
    source_b_ids: List[str] = field(default_factory=list)  # IDs present in B
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CollectionConsistency:
    """
    Consistency report for a single collection pair.
    """
    collection_name: str
    source_a_count: int
    source_b_count: int
    consistency_score: float       # 0.0 – 1.0
    status: ConsistencyStatus
    orphans_a: List[str] = field(default_factory=list)  # IDs only in store A
    orphans_b: List[str] = field(default_factory=list)  # IDs only in store B
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "collection_name": self.collection_name,
            "source_a_count": self.source_a_count,
            "source_b_count": self.source_b_count,
            "consistency_score": round(self.consistency_score, 4),
            "status": self.status.value,
            "orphans_a_count": len(self.orphans_a),
            "orphans_b_count": len(self.orphans_b),
            "orphans_a": self.orphans_a[:50],  # cap for serialization
            "orphans_b": self.orphans_b[:50],
        }


@dataclass(frozen=True)
class InspectionReport:
    """
    Full inspection report across all collection pairs.
    """
    overall_score: float                              # weighted average
    overall_status: ConsistencyStatus
    collections: List[CollectionConsistency] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    needs_healing: bool = False
    inspected_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 4),
            "overall_status": self.overall_status.value,
            "collections": [c.to_dict() for c in self.collections],
            "recommendations": self.recommendations,
            "needs_healing": self.needs_healing,
            "inspected_at": self.inspected_at.isoformat(),
        }


@dataclass(frozen=True)
class HealthStatus:
    """
    Health status of Codex Hunters system.
    """
    healthy: bool
    components: Dict[str, bool] = field(default_factory=dict)
    active_expeditions: int = 0
    pending_expeditions: int = 0
    last_expedition_at: Optional[datetime] = None
    error_rate_1h: float = 0.0
    message: str = ""
