"""
Vault Keepers — Pydantic Schemas

Request/response models for FastAPI endpoints.

Sacred Order: Truth (Memory & Archival)
Layer: Service (LIVELLO 2)
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class IntegrityCheckRequest(BaseModel):
    """Request model for manual integrity check"""
    check_type: str = Field(default="manual", description="Type of integrity check")
    priority: str = Field(default="high", description="Check priority level")
    correlation_id: Optional[str] = Field(None, description="Optional correlation ID")


class BackupRequest(BaseModel):
    """Request model for manual backup creation"""
    mode: str = Field(default="manual", description="Backup mode")
    priority: str = Field(default="high", description="Backup priority")
    include_vectors: bool = Field(default=True, description="Include Qdrant vectors")
    correlation_id: Optional[str] = Field(None, description="Optional correlation ID")


class RestoreRequest(BaseModel):
    """Request model for data restoration"""
    snapshot_id: str = Field(..., description="ID of snapshot to restore")
    target: str = Field(default="all", description="What to restore: all, postgresql, qdrant")
    dry_run: bool = Field(default=True, description="Test restore without applying changes")


class IntegrityStatus(BaseModel):
    """Integrity validation result"""
    integrity_status: str = Field(..., description="Overall integrity status")
    postgresql: Dict[str, Any] = Field(..., description="PostgreSQL health")
    qdrant: Dict[str, Any] = Field(..., description="Qdrant health")
    coherence: Dict[str, Any] = Field(..., description="Cross-system coherence")
    warden_blessing: str = Field(..., description="Warden's judgment")
    sacred_timestamp: str = Field(..., description="Validation timestamp")


class BackupResult(BaseModel):
    """Backup operation result"""
    success: bool = Field(..., description="Whether backup succeeded")
    snapshot_id: Optional[str] = Field(None, description="Created snapshot ID")
    postgresql_backup: Optional[Dict[str, Any]] = Field(None, description="PostgreSQL backup details")
    qdrant_backup: Optional[Dict[str, Any]] = Field(None, description="Qdrant backup details")
    sacred_timestamp: str = Field(..., description="Backup timestamp")


class VaultStatus(BaseModel):
    """Comprehensive vault status"""
    vault_status: str = Field(..., description="Overall vault status")
    integrity_status: Dict[str, Any] = Field(..., description="Integrity validation results")
    audit_summary: Dict[str, Any] = Field(..., description="Recent audit summary")
    sacred_roles: Dict[str, str] = Field(..., description="Sacred role statuses")
    synaptic_conclave: str = Field(..., description="Conclave connection status")
    sacred_timestamp: str = Field(..., description="Status check timestamp")


class HealthCheck(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Overall health status")
    vault_status: str = Field(..., description="Vault keeper status")
    synaptic_conclave: str = Field(..., description="Conclave connection")
    postgresql: str = Field(..., description="PostgreSQL status")
    qdrant: str = Field(..., description="Qdrant status")
    sacred_timestamp: str = Field(..., description="Check timestamp")
