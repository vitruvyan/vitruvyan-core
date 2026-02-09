"""
🕯 Synaptic Conclave — Pydantic Schemas

Sacred data models for API request/response validation.
Follows SERVICE_PATTERN.md (LIVELLO 2).
"""

from pydantic import BaseModel
from typing import Dict, Any


class EventPayload(BaseModel):
    """Event payload for emission to Redis Streams."""
    data: Dict[str, Any]
    emitter: str = "conclave.api"


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    timestamp: str
    redis_connected: bool
    service: str
    version: str
