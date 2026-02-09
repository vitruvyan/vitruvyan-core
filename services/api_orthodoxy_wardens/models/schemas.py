"""
🏛️ Orthodoxy Wardens - Pydantic Schemas
Sacred data models for API request/response validation.
"""

from pydantic import BaseModel
from typing import Dict, Optional, Any
from datetime import datetime


class DivineHealthResponse(BaseModel):
    """Divine health check response schema"""
    sacred_status: str  # blessed, cursed, or purifying
    divine_council: Dict[str, str]  # Status of each sacred role
    timestamp: str
    blessing_level: float


class ConfessionRequest(BaseModel):
    """Confession request schema"""
    confession_type: str = "system_compliance"  # Type of confession
    sacred_scope: Optional[str] = "complete_realm"  # Scope of divine inspection
    urgency: Optional[str] = "divine_routine"  # divine_routine, sacred_priority, holy_emergency
    penitent_service: Optional[str] = None  # Which service seeks absolution


class OrthodoxyStatusResponse(BaseModel):
    """Orthodoxy status response schema"""
    confession_id: str
    sacred_status: str  # confessing, purifying, absolved, condemned
    penance_progress: float
    divine_results: Optional[Dict] = None
    timestamp: str
    assigned_warden: str
