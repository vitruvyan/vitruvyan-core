"""
Codex Hunters API Schemas
=========================

Pydantic request/response models for HTTP endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Request Models
# ============================================================================

class ExpeditionRunRequest(BaseModel):
    """Request model for expedition trigger."""
    
    expedition_type: str = Field(
        ...,
        description="Type of expedition: full_audit, healing, discovery"
    )
    target_collections: Optional[List[str]] = Field(
        default=None,
        description="Specific collections to target"
    )
    priority: str = Field(
        default="medium",
        description="Priority level: critical, high, medium, low"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional parameters"
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Correlation ID for tracking"
    )


class DiscoveryRequest(BaseModel):
    """Request for entity discovery."""
    
    entity_id: str = Field(..., description="Unique entity identifier")
    source_type: str = Field(..., description="Source type (configurable)")
    raw_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Raw data from source"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class RestoreRequest(BaseModel):
    """Request for data restoration/normalization."""
    
    entity_id: str = Field(..., description="Entity identifier")
    raw_data: Dict[str, Any] = Field(..., description="Raw data to restore")
    source_type: str = Field(..., description="Source type")


class BindRequest(BaseModel):
    """Request for binding entity to persistent storage."""
    
    entity_id: str = Field(..., description="Entity identifier")
    normalized_data: Dict[str, Any] = Field(..., description="Normalized data")
    embedding: Optional[List[float]] = Field(
        default=None,
        description="Vector embedding (if available)"
    )


# ============================================================================
# Response Models
# ============================================================================

class ExpeditionStatusResponse(BaseModel):
    """Response model for expedition status."""
    
    expedition_id: str
    status: str  # "running", "completed", "failed", "queued"
    progress: float  # 0.0 to 1.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    agents_deployed: List[str] = Field(default_factory=list)
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class DiscoveryResponse(BaseModel):
    """Response for discovery operation."""
    
    success: bool
    entity_id: str
    status: str  # "discovered", "duplicate", "invalid"
    message: str
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


class RestoreResponse(BaseModel):
    """Response for restore operation."""
    
    success: bool
    entity_id: str
    quality_score: float  # 0.0 to 1.0
    normalized_fields: List[str]
    warnings: List[str] = Field(default_factory=list)


class BindResponse(BaseModel):
    """Response for bind operation."""
    
    success: bool
    entity_id: str
    postgres_stored: bool
    qdrant_stored: bool
    bound_at: datetime = Field(default_factory=datetime.utcnow)


class SystemHealthResponse(BaseModel):
    """Response model for system health."""
    
    status: str  # "healthy", "degraded", "unhealthy"
    agents_status: Dict[str, str] = Field(default_factory=dict)
    redis_connected: bool = False
    database_connected: bool = False
    active_expeditions: int = 0
    completed_expeditions_24h: int = 0
    error_rate: float = 0.0


class StatsResponse(BaseModel):
    """Response model for system statistics."""
    
    total_discoveries: int = 0
    total_restored: int = 0
    total_bound: int = 0
    expeditions_completed: int = 0
    expeditions_failed: int = 0
    uptime_seconds: float = 0.0


# ============================================================================
# Event Models (for internal use)
# ============================================================================

class ProcessResult(BaseModel):
    """Generic processing result."""
    
    success: bool
    entity_id: Optional[str] = None
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)
