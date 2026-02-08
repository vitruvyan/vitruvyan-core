"""
Orthodoxy Wardens Core Business Logic

This package contains the core domain logic for the Orthodoxy Wardens service,
separated from deployment code (FastAPI, Docker, etc.).

Purpose: Enable testing and reuse without Docker dependencies.
"""

from .roles import (
    SacredRole,
    OrthodoxConfessor,
    OrthodoxPenitent,
    OrthodoxChronicler,
    OrthodoxInquisitor,
    OrthodoxAbbot
)

from .event_handlers import (
    handle_audit_request,
    handle_heresy_detection,
    handle_system_events
)

__all__ = [
    # Sacred Roles
    "SacredRole",
    "OrthodoxConfessor",
    "OrthodoxPenitent",
    "OrthodoxChronicler",
    "OrthodoxInquisitor",
    "OrthodoxAbbot",
    
    # Event Handlers
    "handle_audit_request",
    "handle_heresy_detection",
    "handle_system_events"
]
