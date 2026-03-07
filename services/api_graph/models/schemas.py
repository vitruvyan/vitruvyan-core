"""
Graph Orchestrator Pydantic Models

Request/response schemas for Graph API endpoints.

Layer: LIVELLO 2 (Service)
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class GraphInputSchema(BaseModel):
    """Graph execution input schema."""
    input_text: str = Field(..., description="User input text to process")
    user_id: Optional[str] = Field(None, description="User ID (default: demo)")
    validated_tickers: Optional[List[str]] = Field(None, description="Client-validated tickers (authoritative per Golden Rules)")
    validated_entities: Optional[List[str]] = Field(None, description="DEPRECATED: Use validated_tickers. Backward-compat alias.")
    language: Optional[str] = Field(None, description="Language hint (en, it, es)")


class GraphResponseSchema(BaseModel):
    """Graph execution response schema."""
    json: str = Field(..., description="One-line JSON result")
    human: str = Field(..., description="Human-readable message")
    audit_monitored: bool = Field(False, description="Whether audit monitoring was active")
    execution_timestamp: str = Field(..., description="ISO timestamp of execution")


class FeedbackSignalSchema(BaseModel):
    """User feedback on an AI response — drives Plasticity learning."""
    message_id: str = Field(..., description="Chat message ID being rated")
    trace_id: Optional[str] = Field(None, description="Backend trace_id for causal linking")
    feedback: str = Field(..., pattern="^(positive|negative)$", description="positive or negative")
    comment: Optional[str] = Field(None, max_length=500, description="Optional correction/comment")
    timestamp: str = Field(..., description="ISO 8601 timestamp")


class SemanticClusterSchema(BaseModel):
    """Semantic cluster schema."""
    id: int
    label: str
    keywords: List[str]
    representative_phrases: List[str]
    size: int
    created_at: Optional[str] = None


class EntitySearchResultSchema(BaseModel):
    """Entity search result schema."""
    entity_id: str
    name: str
    sector: str
    match_score: float


class HealthResponseSchema(BaseModel):
    """Health check response schema."""
    status: str
    service: str
    timestamp: str
    version: str
    audit_monitoring: str
    heartbeat_count: int
    last_heartbeat: str
    portainer_anti_restart: str


class AuditHealthSchema(BaseModel):
    """Audit monitoring health schema."""
    status: str
    monitoring_active: bool
    current_session_id: Optional[str]
    performance_metrics: Dict[str, Any]
    timestamp: str
