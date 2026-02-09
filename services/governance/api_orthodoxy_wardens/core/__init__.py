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

from .workflows import (
    run_confession_workflow,
    run_purification_ritual,
    divine_surveillance_monitoring,
    set_agents
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
    "handle_system_events",
    
    # Workflows (FASE 2 - Feb 9, 2026)
    "run_confession_workflow",
    "run_purification_ritual",
    "divine_surveillance_monitoring",
    "set_agents"
]
