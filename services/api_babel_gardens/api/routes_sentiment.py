"""Sentiment analysis routes — thin HTTP adapter → SentimentFusionModule."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

router = APIRouter(prefix="/v1/sentiment", tags=["sentiment"])


# ── Request / Response models ──

class SentimentRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to analyze")
    language: str = Field(default="auto", description="ISO 639-1 code or 'auto'")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Conversation context")


class BatchSentimentRequest(BaseModel):
    texts: List[str] = Field(..., min_length=1, description="List of texts to analyze")
    language: str = Field(default="auto", description="ISO 639-1 code or 'auto'")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Conversation context")


# ── Endpoints ──

@router.post("/analyze")
async def analyze_sentiment(request: SentimentRequest):
    """Analyze sentiment of a single text (LLM-first, Nuclear Option)."""
    from ..main import service
    if service is None or service.sentiment_fusion is None:
        raise HTTPException(status_code=503, detail="SentimentFusion not initialized")
    return await service.sentiment_fusion.analyze(
        text=request.text,
        language=request.language,
        context=request.context,
    )


@router.post("/batch")
async def analyze_sentiment_batch(request: BatchSentimentRequest):
    """Analyze sentiment for a batch of texts (max 25)."""
    from ..main import service
    if service is None or service.sentiment_fusion is None:
        raise HTTPException(status_code=503, detail="SentimentFusion not initialized")
    return await service.sentiment_fusion.analyze_batch(
        texts=request.texts,
        language=request.language,
        context=request.context,
    )
