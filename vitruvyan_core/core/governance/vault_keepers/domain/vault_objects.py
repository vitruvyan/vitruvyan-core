"""
Vault Keepers — Domain Objects

Immutable domain objects representing vault operations.

Sacred Order: Truth (Memory & Archival)
Layer: Foundational (LIVELLO 1)
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class VaultSnapshot:
    """
    Immutable snapshot of system state at a point in time.
    
    Attributes:
        snapshot_id: Unique identifier (format: "snapshot_YYYYMMDD_HHMMSS")
        timestamp: ISO 8601 creation time
        scope: What was captured ("full", "postgresql", "qdrant")
        postgresql_backup_path: Path to PostgreSQL dump
        qdrant_backup_path: Path to Qdrant snapshot
        size_bytes: Total size of snapshot
        status: Snapshot status ("completed", "partial", "failed")
        metadata: Additional context (tuple of key-value pairs)
    """
    snapshot_id: str
    timestamp: str
    scope: str
    postgresql_backup_path: Optional[str] = None
    qdrant_backup_path: Optional[str] = None
    size_bytes: int = 0
    status: str = "completed"
    metadata: tuple = ()  # Frozen: tuple of (key, value) pairs

    def __post_init__(self):
        _valid_scopes = {"full", "postgresql", "qdrant", "partial"}
        _valid_statuses = {"completed", "partial", "failed", "in_progress"}
        
        if self.scope not in _valid_scopes:
            raise ValueError(f"Invalid scope '{self.scope}'. Must be one of: {_valid_scopes}")
        if self.status not in _valid_statuses:
            raise ValueError(f"Invalid status '{self.status}'. Must be one of: {_valid_statuses}")


@dataclass(frozen=True)
class IntegrityReport:
    """
    Immutable report of data integrity validation.
    
    Attributes:
        report_id: Unique identifier
        timestamp: ISO 8601 validation time
        postgresql_status: PostgreSQL health ("healthy", "degraded", "corrupted")
        qdrant_status: Qdrant health ("healthy", "degraded", "corrupted")
        coherence_status: Cross-system coherence ("coherent", "drift_detected", "critical")
        overall_status: Overall integrity ("sacred", "blessed_with_concerns", "corruption_detected")
        findings: Tuple of specific issues found
        warden_blessing: Warden's judgment text
    """
    report_id: str
    timestamp: str
    postgresql_status: str
    qdrant_status: str
    coherence_status: str
    overall_status: str
    findings: tuple = ()  # Tuple of finding strings
    warden_blessing: str = "integrity_verified"

    def __post_init__(self):
        _valid_db_statuses = {"healthy", "degraded", "corrupted", "unreachable"}
        _valid_coherence = {"coherent", "drift_detected", "critical"}
        _valid_overall = {"sacred", "blessed_with_concerns", "corruption_detected"}
        
        if self.postgresql_status not in _valid_db_statuses:
            raise ValueError(f"Invalid postgresql_status: {self.postgresql_status}")
        if self.qdrant_status not in _valid_db_statuses:
            raise ValueError(f"Invalid qdrant_status: {self.qdrant_status}")
        if self.coherence_status not in _valid_coherence:
            raise ValueError(f"Invalid coherence_status: {self.coherence_status}")
        if self.overall_status not in _valid_overall:
            raise ValueError(f"Invalid overall_status: {self.overall_status}")


@dataclass(frozen=True)
class ArchiveMetadata:
    """
    Immutable metadata about archived content.
    
    Attributes:
        archive_id: Unique identifier
        timestamp: ISO 8601 archive time
        content_type: Type of content ("audit_result", "screening_result", "system_state")
        source_order: Which Sacred Order created the content
        correlation_id: Links to originating event
        storage_path: Where archived content is stored
        size_bytes: Archive size
        retention_until: ISO 8601 expiration date
    """
    archive_id: str
    timestamp: str
    content_type: str
    source_order: str
    correlation_id: Optional[str] = None
    storage_path: Optional[str] = None
    size_bytes: int = 0
    retention_until: Optional[str] = None

    def __post_init__(self):
        _valid_types = {"audit_result", "eval_result", "system_state", "agent_log", "generic"}
        if self.content_type not in _valid_types:
            raise ValueError(f"Invalid content_type: {self.content_type}")


@dataclass(frozen=True)
class RecoveryPlan:
    """
    Immutable plan for data recovery/restoration.
    
    Attributes:
        plan_id: Unique identifier
        timestamp: ISO 8601 plan creation time
        snapshot_id: Which snapshot to restore from
        target: What to restore ("all", "postgresql", "qdrant")
        dry_run: Whether this is a test restore
        estimated_downtime_seconds: Expected service interruption
        steps: Tuple of recovery steps (ordered)
        status: Plan status ("draft", "approved", "executing", "completed", "failed")
    """
    plan_id: str
    timestamp: str
    snapshot_id: str
    target: str
    dry_run: bool = True
    estimated_downtime_seconds: int = 0
    steps: tuple = ()  # Tuple of step descriptions
    status: str = "draft"

    def __post_init__(self):
        _valid_targets = {"all", "postgresql", "qdrant", "selective"}
        _valid_statuses = {"draft", "approved", "executing", "completed", "failed"}
        
        if self.target not in _valid_targets:
            raise ValueError(f"Invalid target: {self.target}")
        if self.status not in _valid_statuses:
            raise ValueError(f"Invalid status: {self.status}")


@dataclass(frozen=True)
class AuditRecord:
    """
    Immutable record of a vault operation for audit trail.
    
    Attributes:
        record_id: Unique identifier
        timestamp: ISO 8601 operation time
        operation: Operation performed ("backup", "restore", "integrity_check", "archive")
        performed_by: Who/what triggered the operation
        resource_type: Type of resource operated on
        resource_id: Identifier of resource
        action: Specific action taken
        status: Operation status ("initiated", "completed", "failed")
        correlation_id: Links to originating event
        metadata: Tuple of metadata key-value pairs
    """
    record_id: str
    timestamp: str
    operation: str
    performed_by: str
    resource_type: str
    resource_id: str
    action: str
    status: str
    correlation_id: Optional[str] = None
    metadata: tuple = ()

    def __post_init__(self):
        _valid_operations = {"backup", "restore", "integrity_check", "archive", "coherence_check"}
        _valid_statuses = {"initiated", "completed", "failed", "in_progress"}
        
        if self.operation not in _valid_operations:
            raise ValueError(f"Invalid operation: {self.operation}")
        if self.status not in _valid_statuses:
            raise ValueError(f"Invalid status: {self.status}")
