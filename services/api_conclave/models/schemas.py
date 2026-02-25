"""
Synaptic Conclave — Pydantic Schemas

Data models for API request/response validation.
Follows SERVICE_PATTERN.md (LIVELLO 2).
"""

from pydantic import BaseModel
from typing import Any, Dict, List, Optional


# ── Request models ───────────────────────────────────────────

class EventPayload(BaseModel):
    """Event payload for emission to Redis Streams."""
    data: Dict[str, Any]
    emitter: str = "conclave.api"


class EventEmission(BaseModel):
    """Structured event emission (domain + intent + payload)."""
    domain: str
    intent: str
    payload: Dict[str, Any]


class EventSubscription(BaseModel):
    """Subscribe to a domain's events (optional webhook)."""
    domain: str
    callback_url: Optional[str] = None


class EventReceive(BaseModel):
    """Webhook ingress for inter-Order event delivery."""
    domain: str = "unknown"
    intent: str = "unknown"
    payload: Dict[str, Any] = {}
    source: str = "unknown"
    timestamp: Optional[str] = None


# ── Response models ──────────────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    timestamp: str
    redis_connected: bool
    service: str
    version: str


class DetailedHealthResponse(BaseModel):
    """Extended health with pulse and order counts."""
    status: str
    timestamp: str
    conclave_version: str
    redis_connected: bool
    pulse_active: bool
    active_orders: int


class OrdersHealthSummary(BaseModel):
    total_orders: int
    alive_orders: int
    health_percentage: float


class OrdersHealthResponse(BaseModel):
    orders: Dict[str, Any]
    summary: OrdersHealthSummary
    timestamp: str


class StreamStatisticsResponse(BaseModel):
    channels: Dict[str, Any]
    total_events: int
    total_channels: int
    timestamp: str


class RecentEventsResponse(BaseModel):
    events: List[Dict[str, Any]]
    total_returned: int
    limit: int
    domain_filter: Optional[str] = None
    timestamp: str
