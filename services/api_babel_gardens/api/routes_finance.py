"""
Finance Routes - Conditional endpoints for BABEL_DOMAIN=finance.

These routes are registered only when finance vertical is enabled.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..adapters.finance_adapter import get_finance_adapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/finance", tags=["finance"])


class FinanceSignalsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8192, description="Text to analyze")
    language: str = Field(default="auto", description="ISO 639-1 code or 'auto'")


class FinanceSignalsResponse(BaseModel):
    status: str
    signals: List[Dict[str, Any]]
    context: Dict[str, Any]
    metadata: Dict[str, Any]


class SectorResolveRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2048, description="Sector query text")
    language: str = Field(default="auto", description="ISO 639-1 code or 'auto'")


class SectorResolveResponse(BaseModel):
    status: str
    sector: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class FinanceSentimentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8192)
    language: str = Field(default="auto")


@router.post("/signals", response_model=FinanceSignalsResponse)
async def extract_finance_signals(request: FinanceSignalsRequest):
    """
    Extract finance-specific signals from text.

    Returns: sentiment_valence, market_fear_index, volatility_perception.
    """
    adapter = get_finance_adapter()
    if adapter is None:
        raise HTTPException(status_code=404, detail="Finance vertical not enabled. Set BABEL_DOMAIN=finance")

    signals = adapter.extract_finance_signals(request.text)
    context = adapter.detect_financial_context(request.text, request.language)

    return FinanceSignalsResponse(
        status="success",
        signals=signals,
        context=context,
        metadata={
            "signals_count": len(signals),
            "language": request.language,
            "vertical": "finance",
        },
    )


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


@router.post("/sentiment/enhanced")
async def enhanced_finance_sentiment(request: FinanceSentimentRequest):
    """
    Finance-enhanced sentiment analysis.

    Combines LLM-first sentiment + finance signals + adjusted fusion weights.
    """
    adapter = get_finance_adapter()
    if adapter is None:
        raise HTTPException(status_code=404, detail="Finance vertical not enabled")

    from ..main import service

    if service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    llm_sentiment = await service.sentiment_fusion.analyze(
        text=request.text,
        language=request.language,
    )
    finance_signals = adapter.extract_finance_signals(request.text)
    weights = adapter.get_fusion_weights(request.language, request.text)
    context = adapter.detect_financial_context(request.text, request.language)

    return {
        "status": "success",
        "llm_sentiment": llm_sentiment,
        "finance_signals": finance_signals,
        "fusion_weights": weights,
        "financial_context": context,
        "enhanced": True,
        "vertical": "finance",
    }


@router.get("/config")
async def get_finance_config():
    """Get active finance vertical configuration."""
    adapter = get_finance_adapter()
    if adapter is None:
        raise HTTPException(status_code=404, detail="Finance vertical not enabled")

    config = adapter.sentiment_config
    return {
        "status": "success",
        "fusion_weights": dict(config.fusion_weights),
        "finbert_model": config.finbert_model,
        "finbert_device": config.finbert_device,
        "multilingual_boost": config.multilingual_boost,
        "finbert_boost": config.finbert_boost,
    }
