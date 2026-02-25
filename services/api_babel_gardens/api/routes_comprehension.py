"""
Comprehension routes — Unified /comprehend + /fuse endpoints.

Feature-flagged: BABEL_COMPREHENSION_V3=1

These endpoints replace separate PW /compile + BG /emotion/detect
with a single unified call.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

try:
    from contracts.comprehension import (
        ComprehendRequest,
        ComprehendResponse,
        FuseRequest,
        FuseResponse,
        FusionStrategy,
        SignalEvidence,
        ComprehensionResult,
    )
except ModuleNotFoundError:
    from vitruvyan_core.contracts.comprehension import (
        ComprehendRequest,
        ComprehendResponse,
        FuseRequest,
        FuseResponse,
        FusionStrategy,
        SignalEvidence,
        ComprehensionResult,
    )

router = APIRouter(prefix="/v2", tags=["comprehension"])


def _check_feature_flag():
    """Verify BABEL_COMPREHENSION_V3 is enabled."""
    if os.getenv("BABEL_COMPREHENSION_V3", "0") != "1":
        raise HTTPException(
            status_code=404,
            detail="Comprehension v3 not enabled. Set BABEL_COMPREHENSION_V3=1",
        )


def _get_comprehension_adapter():
    """Lazy import to avoid circular dependency."""
    from ..main import service
    if service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    if not hasattr(service, "comprehension_adapter") or service.comprehension_adapter is None:
        raise HTTPException(status_code=503, detail="ComprehensionAdapter not initialized")
    return service.comprehension_adapter


def _get_fusion_adapter():
    """Lazy import to avoid circular dependency."""
    from ..main import service
    if service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    if not hasattr(service, "signal_fusion_adapter") or service.signal_fusion_adapter is None:
        raise HTTPException(status_code=503, detail="SignalFusionAdapter not initialized")
    return service.signal_fusion_adapter


# ── Comprehend ─────────────────────────────────────────────

class ComprehendRequestBody(BaseModel):
    """HTTP request body for /comprehend."""
    query: str = Field(..., min_length=1, description="User query text")
    user_id: str = Field(default="anonymous")
    language: str = Field(default="auto", description="ISO 639-1 code or 'auto'")
    domain: str = Field(default="auto", description="Domain or 'auto'")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Conversation context")


@router.post("/comprehend", response_model=ComprehendResponse)
async def comprehend(request: ComprehendRequestBody):
    """
    Unified comprehension — ontology + semantics in one LLM call.

    Replaces separate PW /compile + BG /emotion/detect.
    Feature flag: BABEL_COMPREHENSION_V3=1
    """
    _check_feature_flag()
    adapter = _get_comprehension_adapter()

    req = ComprehendRequest(
        query=request.query,
        user_id=request.user_id,
        language=request.language,
        domain=request.domain,
        context=request.context or {},
    )

    return adapter.comprehend(req)


# ── Fuse ───────────────────────────────────────────────────

class FuseRequestBody(BaseModel):
    """HTTP request body for /fuse."""
    comprehension: Dict[str, Any] = Field(..., description="ComprehensionResult dict")
    evidences: List[Dict[str, Any]] = Field(default_factory=list, description="Pre-computed evidences")
    strategy: str = Field(default="weighted", description="Fusion strategy")
    weights: Dict[str, float] = Field(default_factory=dict, description="Per-source weight overrides")


@router.post("/fuse", response_model=FuseResponse)
async def fuse(request: FuseRequestBody):
    """
    Signal fusion — merge Layer 1 + Layer 2 signals.

    Takes a ComprehensionResult + optional pre-computed evidences,
    runs all registered signal contributors, and fuses everything.
    Feature flag: BABEL_COMPREHENSION_V3=1
    """
    _check_feature_flag()
    adapter = _get_fusion_adapter()

    try:
        comp = ComprehensionResult.model_validate(request.comprehension)
        evidences = [SignalEvidence.model_validate(e) for e in request.evidences]
        strategy = FusionStrategy(request.strategy)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid request: {e}")

    req = FuseRequest(
        comprehension=comp,
        evidences=evidences,
        strategy=strategy,
        weights=request.weights,
    )

    return adapter.fuse(req)


# ── Stats ──────────────────────────────────────────────────

@router.get("/comprehension/stats")
async def comprehension_stats():
    """Comprehension engine statistics."""
    _check_feature_flag()
    adapter = _get_comprehension_adapter()
    fusion = _get_fusion_adapter()
    return {
        "comprehension": adapter.stats,
        "fusion": fusion.stats,
    }
