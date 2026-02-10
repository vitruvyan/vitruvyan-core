"""
Event Handlers - Synaptic Conclave (Redis Streams) event processing

These handlers process events from the cognitive bus and orchestrate
Sacred Roles to execute audit workflows.

**Pragmatic Purpose**:
- Decouple event handling from FastAPI routing
- Enable testing without HTTP server
- Provide clean separation between infrastructure and business logic

**Design**: Async handlers that receive CognitiveEvents and coordinate Sacred Roles
"""

import sys
import logging
from typing import Dict, Any

# Add /app to path for imports (Docker compatibility)
if '/app' not in sys.path:
    sys.path.append('/app')

from core.synaptic_conclave.events.event_envelope import CognitiveEvent

logger = logging.getLogger("OrthodoxyWardens.EventHandlers")

# Global references to Sacred Roles (injected by main.py during startup)
sacred_confessor = None
sacred_penitent = None
sacred_chronicler = None
sacred_inquisitor = None
sacred_abbot = None


def inject_sacred_roles(confessor, penitent, chronicler, inquisitor, abbot):
    """
    Inject Sacred Role instances into event handlers.
    
    **Why**: Avoid circular imports and enable dependency injection for testing.
    
    **Usage** (in main.py startup):
    ```python
    from core import event_handlers
    event_handlers.inject_sacred_roles(
        confessor=sacred_confessor,
        penitent=sacred_penitent,
        chronicler=sacred_chronicler,
        inquisitor=sacred_inquisitor,
        abbot=sacred_abbot
    )
    ```
    """
    global sacred_confessor, sacred_penitent, sacred_chronicler, sacred_inquisitor, sacred_abbot
    sacred_confessor = confessor
    sacred_penitent = penitent
    sacred_chronicler = chronicler
    sacred_inquisitor = inquisitor
    sacred_abbot = abbot
    logger.info("✅ Sacred Roles injected into event handlers")


async def handle_audit_request(event: CognitiveEvent):
    """
    Handle system.audit.requested events from Synaptic Conclave.
    
    **Workflow**:
    1. Inquisitor triggers investigation
    2. Confessor performs examination
    3. Abbot grants final verdict
    
    **Event Sources**: neural_engine, langgraph, external audit triggers
    """
    global sacred_inquisitor, sacred_confessor, sacred_abbot
    
    logger.info(f"[ORTHODOXY][CONCLAVE] Received audit request: {event.payload}")
    
    try:
        # 1. Inquisitor triggers investigation
        if sacred_inquisitor:
            confession_data = await sacred_inquisitor.trigger_investigation(event.payload)
            
            # 2. Confessor performs examination
            if sacred_confessor:
                findings = await sacred_confessor.hear_confession(event.payload)
                
                # 3. Abbot grants final verdict with correlation_id for response matching
                if sacred_abbot:
                    absolution = await sacred_abbot.grant_absolution(findings, event.correlation_id)
                    logger.info(f"[ORTHODOXY][CONCLAVE] Audit cycle complete: {absolution['verdict']}")
                
    except Exception as e:
        logger.error(f"[ORTHODOXY][CONCLAVE] Error handling audit request: {e}", exc_info=True)


async def handle_heresy_detection(event: CognitiveEvent):
    """
    Handle orthodoxy.heresy.detected events - trigger purification.
    
    **Workflow**:
    1. Penitent applies purification
    2. Chronicler records the event
    
    **Event Sources**: Confessor emits after detecting violations
    """
    global sacred_penitent, sacred_chronicler
    
    logger.info(f"[ORTHODOXY][CONCLAVE] Heresy detected, initiating purification: {event.payload}")
    
    try:
        # Penitent applies purification
        if sacred_penitent:
            purification = await sacred_penitent.apply_purification(event.payload)
            
            # Chronicler records the event
            if sacred_chronicler:
                await sacred_chronicler.record_sacred_event({
                    "event_type": "heresy_purification",
                    "heresy_data": event.payload,
                    "purification_data": purification
                })
                
    except Exception as e:
        logger.error(f"[ORTHODOXY][CONCLAVE] Error handling heresy detection: {e}", exc_info=True)


async def handle_system_events(event: CognitiveEvent):
    """
    Handle general system events that require orthodoxy oversight.
    
    **Workflow**:
    1. Chronicler records event for audit trail
    
    **Event Sources**: neural_engine, babel, memory, vee, langgraph (completion events)
    """
    global sacred_chronicler
    
    logger.info(f"[ORTHODOXY][CONCLAVE] System event received for monitoring: {event.event_type}")
    
    try:
        # Chronicle all system events for divine oversight
        if sacred_chronicler:
            await sacred_chronicler.record_sacred_event(event.to_dict())
            
    except Exception as e:
        logger.error(f"[ORTHODOXY][CONCLAVE] Error handling system event: {e}", exc_info=True)
