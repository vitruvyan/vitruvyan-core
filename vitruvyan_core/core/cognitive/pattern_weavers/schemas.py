"""
Pattern Weavers Schemas — Pydantic Models for API

Epistemic Order: REASON (Semantic Layer)
Sacred Order: #5

Defines request/response schemas for Pattern Weaver API.

Author: Sacred Orders
Created: December 10, 2025
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class WeaveRequest(BaseModel):
    """
    Pattern Weaver request schema.
    
    Fields:
        query_text: User query to analyze
        user_id: User identifier for logging
        language: ISO 639-1 language code ('auto' for detection)
        top_k: Number of top semantic matches to return
        similarity_threshold: Minimum cosine similarity (0.0-1.0)
    """
    query_text: str = Field(..., description="User query text")
    user_id: str = Field(..., description="User identifier")
    language: str = Field(default="auto", description="ISO 639-1 language code")
    top_k: int = Field(default=10, description="Number of top matches", ge=1, le=50)
    similarity_threshold: float = Field(
        default=0.4,  # 🟣 LOWERED from 0.6 to 0.4 (Dec 10, 2025) - Financials matches at 0.41
        description="Minimum cosine similarity",
        ge=0.0,
        le=1.0
    )


class WeaveResponse(BaseModel):
    """
    Pattern Weaver response schema.
    
    Fields:
        concepts: List of extracted concepts (e.g., ["Banking", "Technology"])
        patterns: List of matched patterns with confidence scores
        risk_profile: Aggregated risk profile (sector_risk, dimensions)
        latency_ms: Processing latency in milliseconds
        status: Response status ('success' or 'error')
        error: Error message (if status='error')
    """
    concepts: List[str] = Field(default_factory=list, description="Extracted concepts")
    patterns: List[Dict[str, Any]] = Field(default_factory=list, description="Matched patterns")
    risk_profile: Dict[str, Any] = Field(default_factory=dict, description="Risk profile")
    latency_ms: float = Field(description="Processing latency (ms)")
    status: str = Field(default="success", description="Response status")
    error: Optional[str] = Field(default=None, description="Error message")
