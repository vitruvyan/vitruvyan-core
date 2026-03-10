"""
Finance Routes - Conditional endpoints for PATTERN_DOMAIN=finance.

These routes are registered only when finance vertical is enabled.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..adapters.finance_adapter import get_finance_adapter
from ..models import WeaveRequest
from .routes import run_weave_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/finance", tags=["finance"])


class FinanceContextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8192)
    language: str = Field(default="auto")


class FinanceContextResponse(BaseModel):
    status: str
    context: Dict[str, Any]


class SectorResolveRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2048)
    language: str = Field(default="auto")


class SectorResolveResponse(BaseModel):
    status: str
    sector: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class FinanceWeaveRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=8192)
    user_id: Optional[str] = None
    language: str = Field(default="auto")
    context: Dict[str, Any] = Field(default_factory=dict)
    categories: Optional[List[str]] = None
    limit: int = Field(10, ge=1, le=100)
    threshold: float = Field(0.4, ge=0.0, le=1.0)
    apply_finance_boost: bool = True


class FinanceWeaveResponse(BaseModel):
    request_id: str
    status: str
    matches: List[Dict[str, Any]]
    processing_time_ms: float
    metadata: Dict[str, Any]
    financial_context: Dict[str, Any]
    vertical: str = "finance"


@router.post("/context/detect", response_model=FinanceContextResponse)
async def detect_context(request: FinanceContextRequest):
    """Detect whether a text is finance-related."""
    adapter = get_finance_adapter()
    if adapter is None:
        raise HTTPException(status_code=404, detail="Finance vertical not enabled. Set PATTERN_DOMAIN=finance")

    context = adapter.detect_financial_context(request.text, request.language)
    return FinanceContextResponse(status="success", context=context)


@router.post("/sector/resolve", response_model=SectorResolveResponse)
async def resolve_sector(request: SectorResolveRequest):
    """Resolve GICS sector from multilingual text query."""
    adapter = get_finance_adapter()
    if adapter is None:
        raise HTTPException(status_code=404, detail="Finance vertical not enabled")

    result = adapter.resolve_sector(request.query, request.language)
    if result:
        return SectorResolveResponse(status="success", sector=result)

    return SectorResolveResponse(
        status="not_found",
        error=f"No sector matched for query: {request.query}",
    )


@router.post("/weave", response_model=FinanceWeaveResponse)
async def weave_finance(request: FinanceWeaveRequest):
    """Run finance-enhanced weave with context detection and optional score boost."""
    adapter = get_finance_adapter()
    if adapter is None:
        raise HTTPException(status_code=404, detail="Finance vertical not enabled")

    context = adapter.detect_financial_context(request.query, request.language)

    try:
        from domains.finance.pattern_weavers.weave_config import get_finance_threshold
    except ModuleNotFoundError:
        from core.domains.finance.pattern_weavers.weave_config import (
            get_finance_threshold,
        )

    threshold = request.threshold
    if "threshold" not in request.model_fields_set:
        threshold = get_finance_threshold(context["is_financial"])

    base_request = WeaveRequest(
        query=request.query,
        user_id=request.user_id,
        language=request.language,
        context=request.context,
        categories=request.categories,
        limit=request.limit,
        threshold=threshold,
    )
    result = run_weave_pipeline(base_request)

    plain_matches = [match.model_dump() for match in result["matches"]]
    if request.apply_finance_boost:
        plain_matches = adapter.score_matches(plain_matches, context["is_financial"])

    result["matches"] = plain_matches
    result["financial_context"] = context
    result["vertical"] = "finance"
    result["metadata"] = {
        **result["metadata"],
        "finance_boost_applied": request.apply_finance_boost,
        "resolved_threshold": threshold,
    }

    return FinanceWeaveResponse(**result)


@router.get("/taxonomy/stats")
async def finance_taxonomy_stats():
    """Get finance taxonomy stats from vertical package."""
    adapter = get_finance_adapter()
    if adapter is None:
        raise HTTPException(status_code=404, detail="Finance vertical not enabled")
    return {
        "status": "success",
        "vertical": "finance",
        **adapter.get_taxonomy_stats(),
    }


@router.get("/config")
async def finance_config():
    """Get active finance weave config."""
    adapter = get_finance_adapter()
    if adapter is None:
        raise HTTPException(status_code=404, detail="Finance vertical not enabled")

    cfg = adapter.weave_config
    return {
        "status": "success",
        "vertical": "finance",
        "base_similarity_threshold": cfg.base_similarity_threshold,
        "finance_similarity_threshold": cfg.finance_similarity_threshold,
        "top_k": cfg.top_k,
        "category_boosts": dict(cfg.category_boosts),
        "taxonomy_path": adapter.taxonomy_path,
    }
