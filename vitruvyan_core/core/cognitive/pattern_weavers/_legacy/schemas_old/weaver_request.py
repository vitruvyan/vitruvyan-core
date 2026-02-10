"""
Pattern Weaver Request Schema — Pydantic Models

Author: Sacred Orders
Created: November 9, 2025
Updated: November 9, 2025 (Babel Gardens multilingual integration)
"""

from pydantic import BaseModel, Field
from typing import Optional


class WeaveRequest(BaseModel):
    """Request model for Pattern Weaver API."""
    
    query_text: str = Field(
        ...,
        description="User query text to analyze",
        min_length=1,
        max_length=500
    )
    
    user_id: str = Field(
        ...,
        description="User identifier for logging",
        min_length=1,
        max_length=100
    )
    
    language: str = Field(
        default="auto",
        description="ISO 639-1 language code ('auto' for Babel Gardens detection)",
        min_length=2,
        max_length=4
    )
    
    top_k: int = Field(
        default=5,
        description="Number of top matches to return",
        ge=1,
        le=20
    )
    
    similarity_threshold: float = Field(
        default=0.6,
        description="Minimum cosine similarity score",
        ge=0.0,
        le=1.0
    )
    
    use_cache: bool = Field(
        default=True,
        description="Use Redis embedding cache"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "query_text": "analizza i titoli bancari europei",
                "user_id": "test_user",
                "language": "it",
                "top_k": 5,
                "similarity_threshold": 0.6,
                "use_cache": True
            }
        }
