"""
DSE Service — Pydantic Request / Response Schemas (LIVELLO 2)
=============================================================

HTTP API contracts for the FastAPI service layer.
Pydantic models belong here — NOT in LIVELLO 1 domain.

Last updated: Feb 26, 2026
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# POST /run_dse
# ---------------------------------------------------------------------------

class RunDSERequest(BaseModel):
    """Run a full Design Space Exploration."""
    design_points: List[Dict[str, Any]] = Field(..., description="List of DesignPoint-compatible dicts")
    policy_set: Dict[str, Any] = Field(..., description="PolicySet-compatible dict")
    normalization_profile: Dict[str, Any] = Field(..., description="NormalizationProfile-compatible dict")
    run_context: Dict[str, Any] = Field(..., description="RunContext-compatible dict")
    seed: int = Field(42, description="Reproducibility seed")


class RunDSEResponse(BaseModel):
    """Response from a completed DSE run."""
    status: str
    data: Dict[str, Any]
    execution_time_ms: float


# ---------------------------------------------------------------------------
# POST /dse/prepare
# ---------------------------------------------------------------------------

class PrepareDSERequest(BaseModel):
    """
    Prepare design points from a Pattern Weavers context.
    Called by the Redis Streams listener when weave.completed fires.
    """
    weaver_context: Dict[str, Any] = Field(..., description="Pattern Weavers context (dimensions)")
    user_id: str
    trace_id: str
    trigger: str = "unknown"


class PrepareDSEResponse(BaseModel):
    """Response from /dse/prepare."""
    status: str
    design_points_count: int
    strategy: str
    confidence: float
    trace_id: str


# ---------------------------------------------------------------------------
# POST /dse/log_rejection
# ---------------------------------------------------------------------------

class LogRejectionRequest(BaseModel):
    """Log a Conclave governance rejection."""
    trace_id: str
    reason: str
    rejected_by: Optional[str] = None


# ---------------------------------------------------------------------------
# POST /dse/run_from_context  (LangGraph synchronous entry point)
# ---------------------------------------------------------------------------

class RunFromContextRequest(BaseModel):
    """
    Full synchronous DSE pipeline from a Pattern Weavers context.
    Designed for the LangGraph dse_node: one call → full artifact.
    """
    weaver_context: Dict[str, Any] = Field(
        ..., description="Pattern Weavers context (concepts, dimensions, kpis)"
    )
    user_id: str
    trace_id: str
    seed: int = 42
    use_case: str = "graph_pipeline"


class RunFromContextResponse(BaseModel):
    """Response from /dse/run_from_context."""
    status: str
    trace_id: str
    total_design_points: int
    pareto_count: int
    strategy: str
    confidence: float
    input_hash: str
    asof: str
    top_designs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top-3 designs from ranking_dottrinale"
    )
    artifact: Dict[str, Any] = Field(
        default_factory=dict,
        description="Full artifact (pareto_frontier + ranking_dottrinale)"
    )
