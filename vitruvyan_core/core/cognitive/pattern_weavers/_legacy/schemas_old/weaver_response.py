"""
Pattern Weaver Response Schema — Pydantic Models

Author: Sacred Orders
Created: November 9, 2025
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any


class PatternMatch(BaseModel):
    """Single pattern match."""
    
    type: str = Field(..., description="Pattern type (concept, sector, region, risk_profile)")
    value: str = Field(..., description="Pattern value (e.g., 'Banking', 'Europe')")
    confidence: float = Field(..., description="Similarity score (0.0-1.0)", ge=0.0, le=1.0)
    
    # Optional fields depending on pattern type
    sector: str = Field(None, description="Sector (if type=concept)")
    region: str = Field(None, description="Region (if type=concept)")
    risk_level: str = Field(None, description="Risk level (if type=sector)")
    countries: List[str] = Field(None, description="Country codes (if type=region)")


class RiskProfile(BaseModel):
    """Aggregated risk profile."""
    
    sector_risk: str = Field(default="unknown", description="Sector risk level")
    dimensions: List[str] = Field(default=[], description="Risk dimensions")


class WeaveResponse(BaseModel):
    """Response model for Pattern Weaver API."""
    
    concepts: List[str] = Field(
        default=[],
        description="Extracted concepts (e.g., ['Banking', 'Europe'])"
    )
    
    patterns: List[PatternMatch] = Field(
        default=[],
        description="Detailed pattern matches"
    )
    
    risk_profile: RiskProfile = Field(
        default=RiskProfile(),
        description="Aggregated risk profile"
    )
    
    latency_ms: float = Field(
        default=0.0,
        description="Query processing latency in milliseconds"
    )
    
    status: str = Field(
        default="success",
        description="Processing status (success, no_matches, error)"
    )
    
    error: str = Field(
        None,
        description="Error message (if status=error)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "concepts": ["Banking", "Europe"],
                "patterns": [
                    {
                        "type": "concept",
                        "value": "Banking",
                        "confidence": 0.92,
                        "sector": "Financials",
                        "region": "Global"
                    },
                    {
                        "type": "region",
                        "value": "Europe",
                        "confidence": 0.89,
                        "countries": ["IT", "FR", "DE", "ES", "UK"]
                    }
                ],
                "risk_profile": {
                    "sector_risk": "medium",
                    "dimensions": ["Volatility"]
                },
                "latency_ms": 45.2,
                "status": "success"
            }
        }
