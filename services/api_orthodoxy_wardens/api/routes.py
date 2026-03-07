"""
🏛️ ORTHODOXY WARDENS - Sacred API Routes
FastAPI router for all Orthodoxy Wardens endpoints.

This module contains all sacred confession, surveillance, and validation endpoints,
delegating business logic to core/workflows.py and monitoring/health.py.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Import Pydantic schemas
from api_orthodoxy_wardens.models.schemas import (
    DivineHealthResponse,
    ConfessionRequest,
    OrthodoxyStatusResponse
)
from pydantic import BaseModel

# Import workflow orchestration
from api_orthodoxy_wardens.adapters.workflows import (
    run_confession_workflow,
    run_purification_ritual
)

# Synaptic Conclave integration
from core.synaptic_conclave.transport.streams import StreamBus
from core.synaptic_conclave.events.event_envelope import CognitiveEvent

logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter()

# NOTE: Agent references (confessor_agent, penitent_agent, etc.) are accessed
# via dependency injection or global module-level variables set during initialization.
# These will be refactored into proper FastAPI dependencies in future iterations.

# For now, we access them from the parent main.py module
import __main__ as main_module

def get_agent(agent_name: str):
    """Helper to get agent from main module"""
    return getattr(main_module, agent_name, None)

# =============================================================================
# HEALTH CHECKS
# =============================================================================

@router.get("/health")
async def health_check():
    """Standard health check endpoint"""
    divine_response = await divine_health_check()
    return {
        "status": divine_response.sacred_status,
        "service": "orthodoxy_wardens",
        "version": "2.0.0",
        "blessing_level": divine_response.blessing_level,
        "divine_council": divine_response.divine_council
    }

@router.get("/divine-health", response_model=DivineHealthResponse)
async def divine_health_check():
    """Sacred health check - Verify the divine council's spiritual status"""
    confessor_agent = get_agent("confessor_agent")
    penitent_agent = get_agent("penitent_agent")
    chronicler_agent = get_agent("chronicler_agent")
    inquisitor_agent = get_agent("inquisitor_agent")
    abbot_agent = get_agent("abbot_agent")
    llm_interface = get_agent("llm_interface")
    orthodoxy_db_manager = get_agent("orthodoxy_db_manager")
    sacred_guardrails = get_agent("sacred_guardrails")
    
    divine_council_status = {
        "confessor": "blessed" if confessor_agent else "absent_from_prayers",
        "penitent": "blessed" if penitent_agent else "absent_from_prayers",
        "chronicler": "blessed" if chronicler_agent else "absent_from_prayers",
        "inquisitor": "blessed" if inquisitor_agent else "absent_from_prayers",
        "abbot": "blessed" if abbot_agent else "absent_from_prayers",
        "sacred_interface": "blessed" if llm_interface else "silent",
        "orthodoxy_db": "blessed" if orthodoxy_db_manager else "corrupted",
        "sacred_guardrails": "blessed" if sacred_guardrails else "unprotected"
    }
    
    blessed_count = sum(1 for status in divine_council_status.values() if status == "blessed")
    total_count = len(divine_council_status)
    blessing_level = blessed_count / total_count
    
    if blessing_level >= 0.9:
        sacred_status = "blessed"
    elif blessing_level >= 0.7:
        sacred_status = "purifying"
    else:
        sacred_status = "cursed"
        
    return DivineHealthResponse(
        sacred_status=sacred_status,
        divine_council=divine_council_status,
        timestamp=datetime.now().isoformat(),
        blessing_level=blessing_level
    )

# =============================================================================
# SACRED CONFESSION ENDPOINTS  
# =============================================================================

@router.post("/confession/initiate")
async def initiate_confession(request: ConfessionRequest, background_tasks: BackgroundTasks):
    """🏛️ Initiate sacred confession ritual for system compliance"""
    confessor_agent = get_agent("confessor_agent")
    orthodoxy_db_manager = get_agent("orthodoxy_db_manager")
    
    if not confessor_agent:
        raise HTTPException(status_code=503, detail="Confessor is absent from sacred duties")
    
    if not orthodoxy_db_manager:
        raise HTTPException(status_code=503, detail="Sacred database is corrupted")
    
    try:
        # Generate sacred confession ID
        confession_id = f"confession_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create confession in PostgreSQL first
        await orthodoxy_db_manager.create_confession(
            confession_id=confession_id,
            service=request.penitent_service or "unknown_service",
            event_type=request.confession_type,
            payload={
                "sacred_scope": request.sacred_scope,
                "urgency": request.urgency,
                "initiated_at": datetime.now().isoformat()
            },
            assigned_warden="confessor"
        )
        
        # Create sacred confession state
        confession_state = {
            "confession_id": confession_id,
            "confession_type": request.confession_type,
            "sacred_scope": request.sacred_scope,
            "urgency": request.urgency,
            "penitent_service": request.penitent_service,
            "confession_results": {},
            "orthodoxy_score": 0.0,
            "penance_actions": [],
            "purification_rituals": [],
            "divine_insights": {},
            "sacred_notifications": [],
            "status": "confessing",
            "assigned_warden": "confessor"
        }
        
        # Start sacred confession workflow
        background_tasks.add_task(run_confession_workflow, confession_state)
        
        logger.info(f"🏛️ Sacred confession initiated: {confession_id}")
        
        return {
            "confession_id": confession_id,
            "sacred_status": "confessing",
            "message": "Sacred confession ritual has begun, Confessor is hearing your system's sins",
            "assigned_warden": "confessor",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"💀 Failed to initiate confession: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# SYNAPTIC CONCLAVE INTEGRATION ENDPOINTS
# =============================================================================

@router.post("/conclave/audit-request")
async def trigger_synaptic_audit(request: Dict[str, Any]):
    """🕯️ Trigger audit via Synaptic Conclave (Redis event bus)"""
    sacred_inquisitor = get_agent("sacred_inquisitor")
    
    if not sacred_inquisitor:
        raise HTTPException(status_code=503, detail="Sacred Inquisitor not available for divine investigation")
    
    try:
        # Emit audit request event to Synaptic Conclave
        redis_bus = StreamBus()
        
        event = CognitiveEvent(
            event_type="orthodoxy.audit.requested",
            emitter="orthodoxy_wardens_api",
            target="orthodoxy_wardens",
            payload=request,
            timestamp=datetime.utcnow().isoformat()
        )
        
        success = redis_bus.publish_event(event)
        
        if success:
            logger.info(f"[ORTHODOXY][CONCLAVE] Audit request published to Synaptic Conclave")
            return {
                "status": "sacred_investigation_initiated",
                "message": "Divine audit request transmitted through Synaptic Conclave",
                "event_type": event.event_type,
                "timestamp": event.timestamp
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to publish audit request to Synaptic Conclave")
            
    except Exception as e:
        logger.error(f"[ORTHODOXY][CONCLAVE] Error triggering synaptic audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conclave/status")
async def get_conclave_status():
    """🕯️ Get Synaptic Conclave integration status"""
    sacred_confessor = get_agent("sacred_confessor")
    sacred_penitent = get_agent("sacred_penitent")
    sacred_chronicler = get_agent("sacred_chronicler")
    sacred_inquisitor = get_agent("sacred_inquisitor")
    sacred_abbot = get_agent("sacred_abbot")
    
    try:
        redis_bus = StreamBus()
        bus_stats = redis_bus.get_stats()
        health = redis_bus.health_check()
        
        return {
            "conclave_status": "connected" if health["connected"] else "disconnected",
            "listening": health["listening"],
            "events_published": health["events_published"],
            "events_received": health["events_received"],
            "connection_errors": health["connection_errors"],
            "sacred_roles_status": {
                "confessor": "active" if sacred_confessor else "dormant",
                "penitent": "active" if sacred_penitent else "dormant", 
                "chronicler": "active" if sacred_chronicler else "dormant",
                "inquisitor": "active" if sacred_inquisitor else "dormant",
                "abbot": "active" if sacred_abbot else "dormant"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[ORTHODOXY][CONCLAVE] Error getting conclave status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conclave/test-confession-cycle")
async def test_confession_cycle():
    """🧪 Test complete confession cycle via Synaptic Conclave"""
    try:
        # Trigger audit request that should go through full cycle
        test_payload = {
            "test_mode": True,
            "source": "orthodoxy_api_test",
            "target": "vitruvyan_system",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # This should trigger: orthodoxy.audit.requested → orthodoxy events → orthodoxy.absolution.granted
        result = await trigger_synaptic_audit(test_payload)
        
        return {
            "test_status": "confession_cycle_initiated",
            "message": "Sacred confession cycle test started - monitor logs for full event chain",
            "trigger_result": result,
            "expected_events": [
                "orthodoxy.audit.requested (published)",
                "orthodoxy.confession.started (emitted by inquisitor)",
                "orthodoxy.heresy.detected (potentially emitted by confessor)",
                "orthodoxy.purification.executed (potentially emitted by penitent)",
                "orthodoxy.absolution.granted (emitted by abbot)"
            ]
        }
        
    except Exception as e:
        logger.error(f"[ORTHODOXY][CONCLAVE] Error testing confession cycle: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/confession/{confession_id}/status", response_model=OrthodoxyStatusResponse)
async def get_confession_status(confession_id: str):
    """🏛️ Get status of sacred confession and penance progress"""
    orthodoxy_db_manager = get_agent("orthodoxy_db_manager")
    
    if not orthodoxy_db_manager:
        raise HTTPException(status_code=503, detail="Sacred database is corrupted")
    
    try:
        confession_status = await orthodoxy_db_manager.get_confession_status(confession_id)
        
        if not confession_status:
            raise HTTPException(status_code=404, detail=f"Sacred confession {confession_id} not found in divine records")
        
        return OrthodoxyStatusResponse(
            confession_id=confession_id,
            sacred_status=confession_status["sacred_status"],
            penance_progress=confession_status.get("penance_progress", 0.0),
            divine_results=confession_status.get("divine_results"),
            assigned_warden=confession_status.get("assigned_warden", "confessor"),
            timestamp=confession_status.get("timestamp", datetime.now().isoformat())
        )
        
    except Exception as e:
        logger.error(f"💀 Failed to retrieve confession status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sacred-records/recent")
async def get_recent_confessions(limit: int = 10):
    """📜 Get recent sacred confessions from the divine chronicles"""
    orthodoxy_db_manager = get_agent("orthodoxy_db_manager")
    
    if not orthodoxy_db_manager:
        raise HTTPException(status_code=503, detail="Sacred database is corrupted")
    
    try:
        recent_confessions = await orthodoxy_db_manager.get_recent_confessions(limit=limit)
        return {
            "sacred_confessions": recent_confessions,
            "chronicler_note": "These are the recent sins confessed to our divine order"
        }
        
    except Exception as e:
        logger.error(f"💀 Failed to retrieve sacred records: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# DIVINE SURVEILLANCE & SACRED HEALING
# =============================================================================

@router.get("/divine-surveillance/realm-status")
async def get_realm_surveillance():
    """👁️ Divine surveillance of the sacred realm - Inquisitor's omniscient watch"""
    inquisitor_agent = get_agent("inquisitor_agent")
    
    if not inquisitor_agent:
        raise HTTPException(status_code=503, detail="Inquisitor is absent from divine watch")
    
    try:
        surveillance_data = await inquisitor_agent.perform_divine_surveillance()
        return {
            "surveillance_report": surveillance_data,
            "inquisitor_blessing": "The divine eye sees all transgressions"
        }
        
    except Exception as e:
        logger.error(f"💀 Divine surveillance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sacred-healing/initiate-purification")
async def initiate_purification_ritual(background_tasks: BackgroundTasks):
    """✨ Initiate sacred purification ritual - Penitent performs system cleansing"""
    penitent_agent = get_agent("penitent_agent")
    
    if not penitent_agent:
        raise HTTPException(status_code=503, detail="Penitent is absent from sacred duties")
    
    try:
        purification_id = f"purification_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        purification_state = {
            "purification_id": purification_id,
            "ritual_type": "system_purification",
            "purification_actions": [],
            "status": "ritual_initiated",
            "assigned_warden": "penitent"
        }
        
        # Start sacred purification ritual
        background_tasks.add_task(run_purification_ritual, purification_state)
        
        return {
            "purification_id": purification_id,
            "sacred_status": "ritual_initiated", 
            "message": "Sacred purification ritual has begun, Penitent is cleansing system sins",
            "assigned_warden": "penitent",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"💀 Failed to initiate purification ritual: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ORTHODOXY VALIDATION ENDPOINTS
# =============================================================================

@router.get("/orthodoxy/sacred-validation")
async def perform_orthodoxy_validation():
    """⚖️ Perform sacred orthodoxy validation - Confessor judges system compliance"""
    confessor_agent = get_agent("confessor_agent")
    
    if not confessor_agent:
        raise HTTPException(status_code=503, detail="Confessor is absent from divine judgment")
    
    try:
        orthodoxy_results = await confessor_agent.validate_sacred_compliance()
        return {
            "orthodoxy_judgment": orthodoxy_results,
            "confessor_blessing": "Your sins have been weighed against divine law"
        }
        
    except Exception as e:
        logger.error(f"💀 Sacred validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orthodoxy/heresy-detection")
async def detect_architectural_heresy():
    """🔍 Detect architectural heresy and code blasphemy - Inquisitor's investigation"""
    inquisitor_agent = get_agent("inquisitor_agent")
    
    if not inquisitor_agent:
        raise HTTPException(status_code=503, detail="Inquisitor is absent from heresy investigation")
    
    try:
        heresy_report = await inquisitor_agent.investigate_code_heresy()
        return {
            "heresy_investigation": heresy_report,
            "inquisitor_warning": "Blasphemous code patterns have been examined"
        }
        
    except Exception as e:
        logger.error(f"💀 Heresy detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# SACRED GUARDRAILS ENDPOINTS
# =============================================================================

@router.post("/sacred-boundaries/validate-service-sanctity")
async def validate_service_sanctity(request: Dict[str, Any]):
    """⛪ Validate sacred service boundaries and divine dependency rules"""
    sacred_guardrails = get_agent("sacred_guardrails")
    
    try:
        service = request.get("service")
        if not service:
            raise HTTPException(status_code=400, detail="Sacred service name required for divine validation")
        
        result = await sacred_guardrails.validate_sacred_service_boundaries(service)
        return {
            "sacred_validation": result,
            "warden_blessing": "Service boundaries have been blessed by sacred architecture"
        }
        
    except Exception as e:
        logger.error(f"💀 Sacred boundary validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sacred-dependencies/divine-consistency-check")
async def check_divine_dependencies(request: Dict[str, Any]):
    """📿 Check divine dependency consistency between sacred code and blessed requirements"""
    sacred_guardrails = get_agent("sacred_guardrails")
    
    try:
        service = request.get("service")
        if not service:
            raise HTTPException(status_code=400, detail="Sacred service name required for divine dependency check")
        
        result = await sacred_guardrails.check_divine_dependency_consistency(service)
        return {
            "divine_dependency_report": result,
            "warden_blessing": "Dependencies have been examined for sacred consistency"
        }
        
    except Exception as e:
        logger.error(f"💀 Divine dependency check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sacred-harmony/async-sync-conflicts")
async def detect_sacred_harmony_conflicts():
    """⚡ Detect async/sync conflicts that disturb sacred code harmony"""
    sacred_guardrails = get_agent("sacred_guardrails")
    
    try:
        result = await sacred_guardrails.detect_sacred_harmony_conflicts()
        return {
            "sacred_harmony_report": result,
            "warden_warning": "Code harmony has been examined for divine synchronization"
        }
        
    except Exception as e:
        logger.error(f"💀 Sacred harmony detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SYNCHRONOUS VERDICT ENDPOINT (F3.4)
# =============================================================================

class SyncVerdictRequest(BaseModel):
    """Lightweight request for synchronous verdict."""
    trigger_type: str = "api_call"
    text: Optional[str] = ""
    code: Optional[str] = ""
    scope: Optional[str] = "general"


@router.post("/verdict/sync")
async def sync_verdict(request: SyncVerdictRequest):
    """
    Synchronous verdict — quick validation pipeline.

    Uses handle_quick_validation() (Confessor → Inquisitor → Verdict only).
    No correction plan, no chronicle, no bus emission.
    Designed for latency-sensitive callers needing an immediate answer.

    Returns verdict dict with timing metadata.
    """
    import time

    adapter = getattr(main_module, "bus_adapter", None)
    if adapter is None:
        raise HTTPException(status_code=503, detail="OrthodoxyBusAdapter not initialized")

    event = {
        "trigger_type": request.trigger_type,
        "text": request.text or "",
        "code": request.code or "",
        "scope": request.scope or "general",
        "source": "sync_verdict_api",
    }

    t0 = time.perf_counter()
    result = adapter.handle_quick_validation(event)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    result["latency_ms"] = round(elapsed_ms, 2)
    result["pipeline"] = "quick_validation"
    return result
