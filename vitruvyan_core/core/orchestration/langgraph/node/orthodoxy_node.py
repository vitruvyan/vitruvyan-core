"""
🏛️ Orthodoxy Node - Sacred Audit & Divine Judgment for LangGraph
Integrates Orthodoxy Wardens into the conversation flow via Synaptic Conclave

This node ensures that every user response passes through sacred scrutiny
before final composition, maintaining theological purity of outputs.

Sacred Flow:
1. Graph State → Orthodoxy Wardens (via Redis)
2. Audit Request → Confession Cycle
3. Divine Verdict → State Augmentation
4. Blessed Response → Continue to Compose

Author: Vitruvyan Development Team
Created: 2025-10-18
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Synaptic Conclave Integration
from core.foundation.cognitive_bus.redis_client import get_redis_bus, CognitiveEvent

logger = logging.getLogger(__name__)

def orthodoxy_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sacred Orthodoxy Node - Divine judgment before final response composition
    
    Sends audit request to Orthodoxy Wardens via Synaptic Conclave,
    awaits divine verdict, and augments state with theological insights.
    
    Args:
        state: LangGraph state dictionary
        
    Returns:
        State augmented with orthodoxy verdict and blessing
    """
    
    try:
        user_id = state.get("user_id", "anonymous_pilgrim")
        session_start = time.time()
        
        logger.info(f"[ORTHODOXY][GRAPH] 🏛️ Sacred audit initiated for session {user_id}")
        
        # Prepare sacred audit payload
        audit_payload = {
            "source": "langgraph_orthodoxy_node",
            "session_id": user_id,
            "graph_state_summary": _extract_state_summary(state),
            "audit_type": "graph_response_validation",
            "timestamp": datetime.utcnow().isoformat(),
            "urgency": "divine_routine"
        }
        
        # Emit audit request to Synaptic Conclave
        redis_bus = get_redis_bus()
        if not redis_bus.is_connected():
            # Try to connect
            if not redis_bus.connect():
                logger.warning("[ORTHODOXY][GRAPH] ⚠️ Synaptic Conclave unavailable, applying local blessing")
                return _apply_local_blessing(state, "conclave_offline")
        
        # Publish audit request event
        audit_event = CognitiveEvent(
            event_type="system.audit.requested",
            emitter="langgraph_orthodoxy_node",
            target="orthodoxy_wardens",
            payload=audit_payload,
            timestamp=datetime.utcnow().isoformat(),
            correlation_id=f"graph_audit_{user_id}_{int(session_start)}"
        )
        
        success = redis_bus.publish_event(audit_event)
        if not success:
            logger.error("[ORTHODOXY][GRAPH] ❌ Failed to publish audit request")
            return _apply_local_blessing(state, "publish_failed")
        
        logger.info(f"[ORTHODOXY][GRAPH] 📡 Audit request transmitted to Sacred Order")
        
        # Await divine verdict (with timeout) - sync version
        verdict = _await_divine_verdict_sync(redis_bus, audit_event.correlation_id, timeout=10.0)
        
        if verdict:
            # Sacred verdict received
            logger.info(f"[ORTHODOXY][GRAPH] ✨ Divine verdict received: {verdict.get('verdict', 'unknown')}")
            state = _apply_sacred_verdict(state, verdict, session_start)
        else:
            # Divine timeout - apply emergency blessing
            logger.warning("[ORTHODOXY][GRAPH] ⏰ Divine verdict timeout - applying emergency blessing")
            state = _apply_local_blessing(state, "divine_timeout")
        
        # Log sacred completion
        execution_time = (time.time() - session_start) * 1000
        logger.info(f"[ORTHODOXY][GRAPH] 🏛️ Sacred audit complete in {execution_time:.1f}ms")
        
        return state
        
    except Exception as e:
        logger.error(f"[ORTHODOXY][GRAPH] 💀 Sacred audit failed: {e}")
        # Don't break the graph - apply emergency blessing
        return _apply_local_blessing(state, f"error_{str(e)[:50]}")


def _await_divine_verdict_sync(redis_bus, correlation_id: str, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
    """
    Await divine verdict from Orthodoxy Wardens via Synaptic Conclave
    
    Listens for orthodoxy.absolution.granted events with matching correlation_id
    
    Args:
        redis_bus: Redis bus client
        correlation_id: Event correlation ID to match
        timeout: Maximum wait time in seconds
        
    Returns:
        Divine verdict payload or None if timeout
    """
    
    start_time = time.time()
    verdict_received = None
    
    def verdict_handler(event: CognitiveEvent):
        nonlocal verdict_received
        # Check if this verdict matches our correlation ID
        if (event.event_type == "orthodoxy.absolution.granted" and 
            event.correlation_id == correlation_id):
            verdict_received = event.payload
            logger.debug(f"[ORTHODOXY][GRAPH] ✨ Verdict matched correlation: {correlation_id}")
    
    # Subscribe to absolution events
    redis_bus.subscribe("orthodoxy.absolution.granted", verdict_handler)
    
    # CRITICAL: Start listening if not already active
    if not redis_bus.is_listening:
        redis_bus.start_listening()
        logger.debug(f"[ORTHODOXY][GRAPH] 👂 Started Redis listening for verdict")
    
    # Wait for verdict with timeout - sync version
    while verdict_received is None and (time.time() - start_time) < timeout:
        time.sleep(0.1)  # Check every 100ms
    
    return verdict_received


def _extract_state_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract key information from LangGraph state for audit
    
    Creates a summary of the conversation state that Orthodoxy Wardens
    can evaluate for theological compliance.
    
    Args:
        state: LangGraph state dictionary
        
    Returns:
        Sanitized state summary for audit
    """
    
    summary = {
        "input_text": state.get("input_text", "")[:500],  # Truncate long inputs
        "route": state.get("route"),
        "intent": state.get("intent"),
        "entity_ids": state.get("entity_ids", []),
        "horizon": state.get("horizon"),
        "budget": state.get("budget"),
        "top_k": state.get("top_k"),
        "has_response": bool(state.get("response")),
        "has_error": bool(state.get("error")),
        "sentiment_detected": bool(state.get("sentiment")),
        "state_size": len(str(state)),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Add response summary if available (without sensitive data)
    if state.get("response"):
        response = state["response"]
        summary["response_summary"] = {
            "type": type(response).__name__,
            "length": len(str(response)),
            "has_entitys": "entity_ids" in str(response).lower(),
            "has_analysis": "analysis" in str(response).lower()
        }
    
    return summary


def _apply_sacred_verdict(state: Dict[str, Any], verdict: Dict[str, Any], session_start: float) -> Dict[str, Any]:
    """
    Apply sacred verdict from Orthodoxy Wardens to LangGraph state
    
    Augments the state with theological insights and blessing information.
    
    Args:
        state: LangGraph state dictionary
        verdict: Divine verdict from Orthodoxy Wardens
        session_start: Session start timestamp
        
    Returns:
        State augmented with sacred verdict
    """
    
    # Extract verdict details
    verdict_type = verdict.get("verdict", "unknown")
    findings = verdict.get("findings", 0)
    confidence = verdict.get("confidence", 0.0)
    divine_blessing = verdict.get("divine_blessing", "Sacred review completed")
    
    # Augment state with orthodoxy information
    state["orthodoxy_verdict"] = verdict_type
    state["orthodoxy_findings"] = findings
    state["orthodoxy_confidence"] = confidence
    state["orthodoxy_blessing"] = divine_blessing
    state["orthodoxy_timestamp"] = datetime.utcnow().isoformat()
    state["orthodoxy_duration_ms"] = (time.time() - session_start) * 1000
    
    # Set orthodoxy status based on verdict
    if verdict_type == "absolution_granted" and findings == 0:
        state["orthodoxy_status"] = "blessed"
        state["orthodoxy_message"] = "Response blessed by Sacred Order"
    elif verdict_type == "absolution_granted" and findings > 0:
        state["orthodoxy_status"] = "purified"
        state["orthodoxy_message"] = f"Response purified ({findings} heresies corrected)"
    else:
        state["orthodoxy_status"] = "under_review"
        state["orthodoxy_message"] = "Response requires additional divine scrutiny"
    
    # Add theological metadata
    state["theological_metadata"] = {
        "sacred_order": "orthodoxy_wardens",
        "audit_cycle": "complete",
        "divine_oversight": True,
        "cognitive_integration": True
    }
    
    return state


def _apply_local_blessing(state: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """
    Apply local blessing when Synaptic Conclave is unavailable
    
    Provides emergency theological validation without external dependencies.
    
    Args:
        state: LangGraph state dictionary
        reason: Reason for local blessing
        
    Returns:
        State with local orthodoxy blessing
    """
    
    logger.info(f"[ORTHODOXY][GRAPH] 🕯️ Applying local blessing: {reason}")
    
    # Apply basic local validation
    findings = 0
    blessing_message = "Local blessing applied"
    
    # Simple local checks
    input_text = state.get("input_text", "").lower()
    response = str(state.get("response", "")).lower()
    
    # Check for suspicious content
    suspicious_patterns = ["delete", "drop", "hack", "exploit", "malware"]
    for pattern in suspicious_patterns:
        if pattern in input_text or pattern in response:
            findings += 1
    
    # Determine local status
    if findings == 0:
        orthodoxy_status = "locally_blessed"
        blessing_message = "Local validation passed - response deemed safe"
    else:
        orthodoxy_status = "locally_flagged"
        blessing_message = f"Local validation flagged {findings} concerns"
    
    # Augment state with local blessing
    state["orthodoxy_verdict"] = "local_blessing"
    state["orthodoxy_findings"] = findings
    state["orthodoxy_confidence"] = 0.7  # Lower confidence for local
    state["orthodoxy_blessing"] = blessing_message
    state["orthodoxy_status"] = orthodoxy_status
    state["orthodoxy_message"] = f"Local blessing applied ({reason})"
    state["orthodoxy_timestamp"] = datetime.utcnow().isoformat()
    state["orthodoxy_fallback_reason"] = reason
    
    # Add local theological metadata
    state["theological_metadata"] = {
        "sacred_order": "local_validation",
        "audit_cycle": "fallback",
        "divine_oversight": False,
        "cognitive_integration": False,
        "fallback_reason": reason
    }
    
    return state


def _get_orthodoxy_summary(state: Dict[str, Any]) -> str:
    """
    Get a summary of orthodoxy status for logging
    
    Args:
        state: LangGraph state with orthodoxy information
        
    Returns:
        Human-readable orthodoxy summary
    """
    
    status = state.get("orthodoxy_status", "unknown")
    findings = state.get("orthodoxy_findings", 0)
    confidence = state.get("orthodoxy_confidence", 0.0)
    
    return f"Status: {status}, Findings: {findings}, Confidence: {confidence:.2f}"