# api_neural_engine/schemas/api_models.py
"""
Pydantic models for Neural Engine API requests/responses.

All models follow Vitruvyan Sacred Orders contract pattern.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


# ===========================
# REQUEST MODELS
# ===========================

class ScreenRequest(BaseModel):
    """
    Request for multi-factor entity screening.
    
    Example:
        {
            "profile": "balanced_mid",
            "filters": {"sector": "Technology", "market_cap_min": 1000000000},
            "top_k": 10,
            "stratification_mode": "stratified",
            "risk_tolerance": "medium"
        }
    """
    profile: str = Field(..., description="Scoring profile name (e.g., 'balanced_mid', 'momentum_focus')")
    entity_ids: Optional[List[str]] = Field(None, description="Specific entity IDs to analyze (e.g. ['TSLA','AAPL']). If null, uses full universe.")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters for entity universe")
    top_k: int = Field(10, description="Number of top entities to return (default 10)", ge=1, le=100)
    stratification_mode: Optional[str] = Field("global", description="Z-score stratification: 'global', 'stratified', 'composite'")
    risk_tolerance: Optional[str] = Field("medium", description="Risk adjustment level: 'low', 'medium', 'high'")
    mode: Optional[str] = Field("discovery", description="Screening mode: discovery|analyze|comparative|sector")
    sector: Optional[str] = Field(None, description="Optional sector filter")
    momentum_breakout: bool = Field(False, description="Enable momentum breakout filter")
    value_screening: bool = Field(False, description="Enable value screening filter")
    divergence_detection: bool = Field(False, description="Enable divergence detection filter")
    multi_timeframe_filter: bool = Field(False, description="Enable multi-timeframe consensus filter")
    smart_money_flow: bool = Field(False, description="Enable smart money dark-pool filter")
    earnings_safety_days: Optional[int] = Field(None, ge=1, le=90, description="Exclude earnings events within N days")
    portfolio_diversification: Optional[List[str]] = Field(None, description="Portfolio tickers for diversification filter")
    macro_factor: Optional[str] = Field(None, description="Macro sensitivity filter: inflation|rates|volatility|dollar")
    
    @validator('stratification_mode')
    def validate_stratification(cls, v):
        if v == "sector":
            return "stratified"
        allowed = ['global', 'stratified', 'composite']
        if v not in allowed:
            raise ValueError(f"stratification_mode must be one of {allowed}")
        return v
    
    @validator('risk_tolerance')
    def validate_risk(cls, v):
        if v is None:
            return "medium"
        allowed = ['low', 'medium', 'high']
        if v not in allowed:
            raise ValueError(f"risk_tolerance must be one of {allowed}")
        return v

    @validator("mode")
    def validate_mode(cls, v):
        if v is None:
            return "discovery"
        allowed = ["discovery", "analyze", "comparative", "sector"]
        if v not in allowed:
            raise ValueError(f"mode must be one of {allowed}")
        return v

    @validator("macro_factor")
    def validate_macro_factor(cls, v):
        if v is None:
            return v
        allowed = ["inflation", "rates", "volatility", "dollar"]
        if v not in allowed:
            raise ValueError(f"macro_factor must be one of {allowed}")
        return v


class RankRequest(BaseModel):
    """
    Request for single-feature entity ranking.
    
    Example:
        {
            "feature_name": "momentum",
            "entity_ids": ["AAPL", "MSFT", "GOOGL"],
            "top_k": 5,
            "higher_is_better": true
        }
    """
    feature_name: str = Field(..., description="Feature to rank by (e.g., 'momentum', 'trend', 'volatility')")
    entity_ids: Optional[List[str]] = Field(None, description="Optional entity IDs to rank (or entire universe if null)")
    top_k: Optional[int] = Field(None, description="Number of top entities to return (default: all)", ge=1, le=1000)
    higher_is_better: bool = Field(True, description="Whether higher values are better (default true)")


# ===========================
# RESPONSE MODELS
# ===========================

class RankedEntity(BaseModel):
    """
    Single ranked entity with scores and metadata.
    """
    rank: int = Field(..., description="Rank position (1-based)")
    entity_id: str = Field(..., description="Entity unique identifier")
    entity_name: Optional[str] = Field(None, description="Entity display name")
    composite_score: float = Field(..., description="Weighted composite z-score")
    percentile: float = Field(..., description="Percentile rank (0-100)")
    bucket: str = Field(..., description="Performance bucket: 'top', 'middle', 'bottom'")
    
    # Factor z-scores (optional — named ones for backward compat)
    momentum_z: Optional[float] = None
    trend_z: Optional[float] = None
    volatility_z: Optional[float] = None
    sentiment_z: Optional[float] = None
    fundamentals_z: Optional[float] = None
    
    # Metadata
    group: Optional[str] = Field(None, description="Stratification group (sector, region, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional entity metadata")

    class Config:
        extra = "allow"  # Allow dynamic z-score fields (revenue_growth_yoy_z, etc.)


class ScreenResponse(BaseModel):
    """
    Response for screening request.
    """
    ranked_entities: List[RankedEntity] = Field(..., description="Ranked entities list")
    
    # Request echo
    profile: str
    top_k: int
    stratification_mode: str
    
    # Metadata
    total_entities_evaluated: int = Field(..., description="Total entities in universe")
    profile_weights: Dict[str, float] = Field(..., description="Feature weights used in this profile")
    
    # Diagnostics
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Optional aggregations
    statistics: Optional[Dict[str, Any]] = Field(None, description="Score statistics (mean, std, min, max)")
    ranking: Optional[Dict[str, Any]] = Field(None, description="Legacy-compatible ranking payload by instrument type")
    screening_criteria: Optional[Dict[str, Any]] = Field(None, description="Applied filters and diagnostics")
    run_id: Optional[int] = Field(None, description="Persisted run identifier (if persistence enabled)")


class RankResponse(BaseModel):
    """
    Response for ranking request.
    """
    ranked_entities: List[RankedEntity] = Field(..., description="Ranked entities list")
    
    # Request echo
    feature_name: str
    higher_is_better: bool
    
    # Metadata
    total_entities_ranked: int
    processing_time_ms: float
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class HealthResponse(BaseModel):
    """
    Health check response.
    """
    status: str = Field(..., description="Overall health status: 'healthy', 'degraded', 'unhealthy'")
    timestamp: str
    version: str
    dependencies: Optional[Dict[str, str]] = Field(None, description="Dependency health status")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
