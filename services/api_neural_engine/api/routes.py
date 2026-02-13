"""Neural Engine — API Routes"""
import time
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from api_neural_engine.schemas.api_models import (
    ScreenRequest, ScreenResponse,
    RankRequest, RankResponse,
    HealthResponse,
)
from api_neural_engine.monitoring.metrics import (
    screening_requests_total, screening_duration_seconds,
    entities_processed_total, service_is_healthy,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/screen", response_model=ScreenResponse, tags=["Screening"])
async def screen_entities(request: ScreenRequest, raw: Request = None):
    """Multi-factor entity screening and ranking."""
    start_time = time.time()
    try:
        result = await raw.app.state.orchestrator.screen(
            profile=request.profile,
            filters=request.filters,
            top_k=request.top_k,
            stratification_mode=request.stratification_mode or "global",
            risk_tolerance=request.risk_tolerance or "medium",
        )
        screening_requests_total.labels(
            profile=request.profile,
            stratification_mode=request.stratification_mode or "global",
        ).inc()
        duration = time.time() - start_time
        screening_duration_seconds.labels(profile=request.profile).observe(duration)
        entities_processed_total.labels(operation="screen").inc(len(result["ranked_entities"]))
        return ScreenResponse(**result)
    except Exception as e:
        logger.error(f"Screening failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rank", response_model=RankResponse, tags=["Ranking"])
async def rank_entities(request: RankRequest, raw: Request = None):
    """Single-factor entity ranking."""
    try:
        result = await raw.app.state.orchestrator.rank(
            feature_name=request.feature_name,
            entity_ids=request.entity_ids,
            top_k=request.top_k,
            higher_is_better=request.higher_is_better,
        )
        entities_processed_total.labels(operation="rank").inc(len(result["ranked_entities"]))
        return RankResponse(**result)
    except Exception as e:
        logger.error(f"Ranking failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(raw: Request = None):
    """Service health with dependency status."""
    try:
        orch = raw.app.state.orchestrator
        o_ok = await orch.health_check()
        p_ok = await orch.check_data_provider()
        s_ok = await orch.check_scoring_strategy()
        ok = all([o_ok, p_ok, s_ok])
        service_is_healthy.set(1 if ok else 0)
        return HealthResponse(
            status="healthy" if ok else "degraded",
            timestamp=datetime.utcnow().isoformat(),
            version="2.0.0",
            dependencies={
                "orchestrator": "healthy" if o_ok else "unhealthy",
                "data_provider": "healthy" if p_ok else "unhealthy",
                "scoring_strategy": "healthy" if s_ok else "unhealthy",
            },
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        service_is_healthy.set(0)
        return HealthResponse(status="unhealthy", timestamp=datetime.utcnow().isoformat(), version="2.0.0", error=str(e))


@router.get("/metrics", tags=["Observability"])
async def metrics():
    """Prometheus metrics exposition."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/profiles", tags=["Configuration"])
async def list_profiles(raw: Request = None):
    """List available scoring profiles."""
    try:
        profiles = await raw.app.state.orchestrator.get_available_profiles()
        return {"profiles": profiles}
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))
