# api_neural_engine/main.py
"""
🧠 VITRUVYAN NEURAL ENGINE API - DOMAIN-AGNOSTIC RANKING SERVICE :8003

Neural Engine is the CORE quantitative ranking service in Vitruvyan ecosystem.
It reads data from domain providers, normalizes via z-scores, and returns ranked entities.

Architecture:
- Domain-agnostic core (vitruvyan_core.core.neural_engine)
- Pluggable data providers (IDataProvider contract)
- Pluggable scoring strategies (IScoringStrategy contract)
- RESTful API with Prometheus observability

Sacred Endpoints:
- POST /screen - Rank entities by profile (balancing multiple factors)
- POST /rank - Simple ranking by single metric
- GET /health - Health check with dependency status
- GET /metrics - Prometheus metrics exposition
"""

import os
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Import Neural Engine domain-agnostic core
from vitruvyan_core.core.neural_engine import NeuralEngine
from vitruvyan_core.contracts import IDataProvider, IScoringStrategy

# Import service modules
from .modules.engine_orchestrator import EngineOrchestrator
from .schemas.api_models import (
    ScreenRequest,
    ScreenResponse,
    RankRequest,
    RankResponse,
    HealthResponse,
    RankedEntity
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===========================
# PROMETHEUS METRICS
# ===========================

# HTTP request metrics
http_requests_total = Counter(
    'neural_engine_http_requests_total',
    'Total HTTP requests to Neural Engine',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'neural_engine_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Engine processing metrics
screening_requests_total = Counter(
    'neural_engine_screening_requests_total',
    'Total screening requests processed',
    ['profile', 'stratification_mode']
)

screening_duration_seconds = Histogram(
    'neural_engine_screening_duration_seconds',
    'Screening processing time in seconds',
    ['profile'],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

entities_processed_total = Counter(
    'neural_engine_entities_processed_total',
    'Total entities processed',
    ['operation']
)

# Data provider metrics
data_provider_calls_total = Counter(
    'neural_engine_data_provider_calls_total',
    'Total data provider calls',
    ['method', 'status']
)

# Cache metrics
cache_hits_total = Counter(
    'neural_engine_cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'neural_engine_cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# System health metrics
service_is_healthy = Gauge(
    'neural_engine_service_healthy',
    'Service health status (1=healthy, 0=unhealthy)'
)

# ===========================
# LIFESPAN CONTEXT
# ===========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    
    Startup:
    - Initialize engine orchestrator
    - Warm up data provider connections
    - Load scoring strategy profiles
    
    Shutdown:
    - Close data provider connections
    - Flush any pending metrics
    """
    logger.info("🧠 Neural Engine API starting up...")
    
    # Initialize engine orchestrator (loads domain provider + strategy)
    try:
        app.state.orchestrator = EngineOrchestrator()
        await app.state.orchestrator.initialize()
        service_is_healthy.set(1)
        logger.info("✅ Engine orchestrator initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize orchestrator: {e}")
        service_is_healthy.set(0)
        raise
    
    logger.info("🚀 Neural Engine API ready on port 8003")
    
    yield
    
    # Shutdown
    logger.info("🛑 Neural Engine API shutting down...")
    await app.state.orchestrator.shutdown()
    service_is_healthy.set(0)
    logger.info("👋 Neural Engine API stopped")

# ===========================
# FASTAPI APPLICATION
# ===========================

app = FastAPI(
    title="Vitruvyan Neural Engine API",
    description="Domain-agnostic quantitative ranking service with z-score normalization",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware (adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def track_requests(request, call_next):
    """Track request metrics"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Record metrics
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    # Add timing header
    response.headers["X-Process-Time"] = f"{duration:.3f}"
    
    return response

# ===========================
# ENDPOINTS
# ===========================

@app.post("/screen", response_model=ScreenResponse, tags=["Screening"])
async def screen_entities(request: ScreenRequest):
    """
    Screen and rank entities using multi-factor scoring.
    
    This is the PRIMARY endpoint of Neural Engine. It:
    1. Loads entity universe via IDataProvider
    2. Computes z-scores for each feature (momentum, trend, volatility, etc.)
    3. Applies profile weights via IScoringStrategy
    4. Ranks entities by composite score
    5. Returns top-k entities with metadata
    
    Args:
        request: ScreenRequest with profile, filters, top_k, etc.
    
    Returns:
        ScreenResponse with ranked entities and diagnostics
    """
    start_time = time.time()
    
    try:
        # Execute screening via orchestrator
        result = await app.state.orchestrator.screen(
            profile=request.profile,
            filters=request.filters,
            top_k=request.top_k,
            stratification_mode=request.stratification_mode or "global",
            risk_tolerance=request.risk_tolerance or "medium"
        )
        
        # Record metrics
        screening_requests_total.labels(
            profile=request.profile,
            stratification_mode=request.stratification_mode or "global"
        ).inc()
        
        duration = time.time() - start_time
        screening_duration_seconds.labels(profile=request.profile).observe(duration)
        
        entities_processed_total.labels(operation="screen").inc(len(result["ranked_entities"]))
        
        return ScreenResponse(**result)
    
    except Exception as e:
        logger.error(f"❌ Screening failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rank", response_model=RankResponse, tags=["Ranking"])
async def rank_entities(request: RankRequest):
    """
    Simple ranking by single feature (no profile weighting).
    
    Lighter alternative to /screen when you want to rank by ONE metric only.
    
    Args:
        request: RankRequest with feature_name and entity_ids
    
    Returns:
        RankResponse with ranked entities
    """
    start_time = time.time()
    
    try:
        result = await app.state.orchestrator.rank(
            feature_name=request.feature_name,
            entity_ids=request.entity_ids,
            top_k=request.top_k,
            higher_is_better=request.higher_is_better
        )
        
        entities_processed_total.labels(operation="rank").inc(len(result["ranked_entities"]))
        
        return RankResponse(**result)
    
    except Exception as e:
        logger.error(f"❌ Ranking failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Service health check with dependency status.
    
    Returns:
        HealthResponse with service status and dependency health
    """
    try:
        # Check orchestrator health
        orchestrator_healthy = await app.state.orchestrator.health_check()
        
        # Check data provider health
        provider_healthy = await app.state.orchestrator.check_data_provider()
        
        # Check scoring strategy health
        strategy_healthy = await app.state.orchestrator.check_scoring_strategy()
        
        overall_healthy = all([orchestrator_healthy, provider_healthy, strategy_healthy])
        service_is_healthy.set(1 if overall_healthy else 0)
        
        return HealthResponse(
            status="healthy" if overall_healthy else "degraded",
            timestamp=datetime.utcnow().isoformat(),
            version="2.0.0",
            dependencies={
                "orchestrator": "healthy" if orchestrator_healthy else "unhealthy",
                "data_provider": "healthy" if provider_healthy else "unhealthy",
                "scoring_strategy": "healthy" if strategy_healthy else "unhealthy"
            }
        )
    
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        service_is_healthy.set(0)
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            version="2.0.0",
            error=str(e)
        )


@app.get("/metrics", tags=["Observability"])
async def metrics():
    """
    Prometheus metrics exposition endpoint.
    
    Returns:
        Plain text Prometheus metrics
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/profiles", tags=["Configuration"])
async def list_profiles():
    """
    List available scoring profiles.
    
    Returns:
        Dict with profile names and descriptions
    """
    try:
        profiles = await app.state.orchestrator.get_available_profiles()
        return {"profiles": profiles}
    except Exception as e:
        logger.error(f"❌ Failed to list profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===========================
# ROOT ENDPOINT
# ===========================

@app.get("/", tags=["Root"])
async def root():
    """Service information"""
    return {
        "service": "Vitruvyan Neural Engine API",
        "version": "2.0.0",
        "architecture": "domain-agnostic",
        "port": 8003,
        "endpoints": {
            "screen": "POST /screen - Multi-factor entity screening",
            "rank": "POST /rank - Single-factor entity ranking",
            "health": "GET /health - Health check",
            "metrics": "GET /metrics - Prometheus metrics",
            "profiles": "GET /profiles - Available scoring profiles"
        },
        "documentation": "/docs",
        "philosophy": "Read data. Normalize. Rank. Return."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
