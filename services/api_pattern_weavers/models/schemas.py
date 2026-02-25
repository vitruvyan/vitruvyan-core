"""
Pydantic Schemas for Pattern Weavers API
========================================

Request/response models for HTTP endpoints.
Domain-agnostic: no hardcoded taxonomy entries.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Request Models
# =============================================================================

class WeaveRequest(BaseModel):
    """Request to weave patterns for a query."""
    
    query: str = Field(..., description="Query text to analyze")
    user_id: Optional[str] = Field(None, description="User identifier")
    language: str = Field("auto", description="ISO 639-1 language code or 'auto'")
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional context for weaving",
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Optional category filter (e.g., sectors, instruments)",
    )
    limit: int = Field(10, ge=1, le=100, description="Maximum matches")
    threshold: float = Field(0.4, ge=0.0, le=1.0, description="Minimum score")


class TaxonomyLoadRequest(BaseModel):
    """Request to load taxonomy from YAML."""
    
    yaml_path: str = Field(..., description="Path to taxonomy YAML file")


# =============================================================================
# Response Models
# =============================================================================

class PatternMatch(BaseModel):
    """A matched pattern from Qdrant."""
    
    name: str = Field(..., description="Pattern name")
    category: str = Field(..., description="Pattern category")
    score: float = Field(..., description="Similarity score")
    match_type: str = Field("semantic", description="Match type")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WeaveResult(BaseModel):
    """Result of pattern weaving."""
    
    request_id: str = Field(..., description="Unique request ID")
    status: str = Field("completed", description="Processing status")
    matches: List[PatternMatch] = Field(default_factory=list)
    processing_time_ms: float = Field(0.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthStatus(BaseModel):
    """Service health status."""
    
    status: str = Field("healthy")
    qdrant: bool = Field(True)
    postgres: bool = Field(True)
    redis: bool = Field(True)
    embedding_service: bool = Field(True)


class TaxonomyStats(BaseModel):
    """Taxonomy statistics."""
    
    total_entries: int = Field(0)
    categories: List[str] = Field(default_factory=list)
    last_updated: Optional[str] = None


# =============================================================================
# Error Models
# =============================================================================

class ErrorResponse(BaseModel):
    """Error response."""
    
    error: str
    detail: Optional[str] = None
    request_id: Optional[str] = None


# =============================================================================
# Compile API Models (v3 — Semantic Compilation)
# =============================================================================

class CompileRequest(BaseModel):
    """Request to compile a query into structured ontology."""

    query: str = Field(..., min_length=1, description="User query text")
    user_id: str = Field("anonymous", description="User identifier")
    language: str = Field("auto", description="ISO 639-1 language hint or 'auto'")
    domain: str = Field("auto", description="Domain hint: 'auto', 'generic', 'finance', etc.")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class CompileResponse(BaseModel):
    """Result of semantic compilation."""

    request_id: str = Field(..., description="Unique request ID")
    payload: Dict[str, Any] = Field(..., description="OntologyPayload dict")
    fallback_used: bool = Field(False, description="Whether LLM fallback was used")
    processing_time_ms: float = Field(0.0)
