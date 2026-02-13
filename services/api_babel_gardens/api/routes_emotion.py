"""Emotion detection routes — thin HTTP adapter for EmotionDetectorModule."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

router = APIRouter(tags=["emotion"])


class EmotionDetectRequest(BaseModel):
    """Request body for /v1/emotion/detect."""
    text: str = Field(..., description="Text to analyze", max_length=8192)
    language: str = Field(default="auto", description="Language code or 'auto'")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Conversation context")
    user_profile: Optional[Dict[str, Any]] = Field(default=None, description="User profile for cultural context")


def _get_detector():
    """Lazy import to avoid circular dependency."""
    from ..main import service
    if service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return service.emotion_detector


@router.post("/v1/emotion/detect")
async def detect_emotion(request: EmotionDetectRequest):
    """
    Detect emotion from text with cultural awareness.

    Returns flat response with top-level `emotion` (str) and `confidence` (float)
    for graph node compatibility, plus full metadata.
    """
    detector = _get_detector()
    return await detector.detect_emotion(
        text=request.text,
        language=request.language,
        context=request.context,
        user_profile=request.user_profile,
    )
