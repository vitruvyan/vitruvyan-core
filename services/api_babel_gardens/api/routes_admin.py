"""
Profile & Cognitive Routes — HTTP adapter for ProfileProcessor + CognitiveBridge.

Thin delegation layer: validate request → call module → return response.
"""

import logging
from fastapi import APIRouter, HTTPException

from ..schemas import (
    ProfileRequest,
    ProfileResponse,
    AdaptationRequest,
    AdaptationResponse,
    RecommendationRequest,
    EventRequest,
    RoutingRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["profiles", "cognitive"])


def _get_service():
    from ..main import service
    if service is None:
        raise HTTPException(status_code=503, detail="Babel Gardens not initialized")
    return service


# ── Profile Processor ──────────────────────────────────────────────

@router.post("/v1/profiles/create", response_model=ProfileResponse)
async def create_profile(request: ProfileRequest):
    """Create or update a user behavioral profile."""
    svc = _get_service()
    return await svc.profile_processor.create_profile(request)


@router.post("/v1/profiles/adapt", response_model=AdaptationResponse)
async def adapt_content(request: AdaptationRequest):
    """Adapt content tone/complexity to user profile."""
    svc = _get_service()
    return await svc.profile_processor.adapt_content(request)


@router.post("/v1/profiles/recommend")
async def generate_recommendations(request: RecommendationRequest):
    """Generate personalized content recommendations."""
    svc = _get_service()
    return await svc.profile_processor.generate_recommendations(request)


# ── Cognitive Bridge ───────────────────────────────────────────────

@router.post("/v1/events/publish")
async def publish_event(request: EventRequest):
    """Publish a cognitive event to the bus."""
    svc = _get_service()
    return await svc.cognitive_bridge.handle_event(request)


@router.post("/v1/routing/intelligent")
async def intelligent_routing(request: RoutingRequest):
    """Content-aware intelligent request routing."""
    svc = _get_service()
    return await svc.cognitive_bridge.route_request(request)
