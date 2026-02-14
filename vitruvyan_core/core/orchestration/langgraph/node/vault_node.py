#!/usr/bin/env python3
"""
🏰 VAULT NODE - LANGGRAPH INTEGRATION
===================================
Sacred memory protection node for the LangGraph pipeline

Integrates the Vault Keepers Conclave into the main conversation flow,
providing divine protection for system integrity and memory preservation.

Author: Vitruvyan Development Team - Cognitive Integration Phase 4.4
Created: October 18, 2025 - Sacred Orders Expansion
"""

import time
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from core.synaptic_conclave.redis_client import get_redis_bus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def vault_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    🏰 Sacred Vault Protection Node
    =============================
    
    Requests divine protection from the Vault Keepers Conclave and integrates
    their blessing into the conversation state.
    
    Pipeline Position: output_normalizer → orthodoxy → vault → compose → END
    
    Domain-Agnostic: Uses domain_keywords from state["_domain_config"]["vault_keywords"]
    if available, otherwise uses core patterns only.
    """
    
    input_text = state.get("human_input", state.get("input", ""))
    
    logger.info(f"[VAULT][GRAPH] 🏰 Sacred vault protection initiated")
    
    # Get domain-specific keywords if available (injected by GraphPlugin)
    domain_keywords = None
    if "_domain_config" in state and "vault_keywords" in state["_domain_config"]:
        domain_keywords = state["_domain_config"]["vault_keywords"]
    
    try:
        # Determine if vault protection is needed
        protection_required = _assess_protection_requirements(state, domain_keywords)
        
        if protection_required['required']:
            # Request divine protection from Vault Keepers Conclave
            protection_result = _request_divine_protection(
                protection_required['protection_type'],
                state
            )
            
            # Apply vault blessing to state
            state = _apply_vault_blessing(state, protection_result)
            
            logger.info(f"[VAULT][GRAPH] 🏰 Divine vault protection applied: {protection_result.get('vault_status', 'blessed')}")
            
        else:
            # Apply standard blessing
            state = _apply_standard_blessing(state)
            logger.info(f"[VAULT][GRAPH] 🏰 Standard vault blessing applied")
        
        # Always proceed to next node
        state["route"] = "compose"
        return state
        
    except Exception as e:
        logger.error(f"[VAULT][GRAPH] ❌ Vault protection error: {e}")
        
        # Apply emergency blessing and continue
        state = _apply_emergency_blessing(state, str(e))
        state["route"] = "compose"
        return state


def _assess_protection_requirements(state: Dict[str, Any], domain_keywords: Dict[str, Any] = None) -> Dict[str, Any]:
    """Assess if divine vault protection is required
    
    Args:
        state: LangGraph state dictionary
        domain_keywords: Optional domain-specific keywords for protection detection
                        Format: {"high_value": [...], "intents": [...], "domain_patterns": [...]}
    """
    
    input_text = state.get("human_input", state.get("input", "")).lower()
    intent = state.get("intent", "")
    
    # Core patterns (domain-agnostic) that require vault protection
    core_patterns = [
        "backup", "restore", "recovery", "integrity", "audit",
        "critical", "emergency", "disaster", "corruption"
    ]
    
    # Domain-specific patterns (injected by GraphPlugin)
    domain_patterns = []
    domain_intents = []
    if domain_keywords:
        domain_patterns = domain_keywords.get("high_value", [])
        domain_intents = domain_keywords.get("intents", [])
    
    all_patterns = core_patterns + domain_patterns
    
    # Check for high-value operation indicators
    requires_protection = any(pattern in input_text for pattern in all_patterns)
    requires_protection = requires_protection or intent in domain_intents
    
    # Determine protection type based on context
    protection_type = "standard"
    if any(pattern in input_text for pattern in ["critical", "emergency", "disaster"]):
        protection_type = "critical"
    elif any(pattern in input_text for pattern in ["integrity", "audit", "backup"]):
        protection_type = "integrity_check"
    elif domain_keywords and any(pattern in input_text for pattern in domain_keywords.get("domain_patterns", [])):
        protection_type = domain_keywords.get("protection_type", "domain_guardian")
    
    return {
        "required": requires_protection,
        "protection_type": protection_type,
        "reasoning": f"Protection {'required' if requires_protection else 'not required'} for {protection_type}"
    }


def _request_divine_protection(protection_type: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """Request divine protection from Vault Keepers Conclave"""
    
    correlation_id = f"vault_protection_{int(time.time() * 1000)}"
    
    try:
        # Get Redis bus connection
        redis_bus = get_redis_bus()
        
        # Ensure connection
        if not redis_bus.is_connected():
            redis_bus.connect()
        
        # Start listening for responses
        if not redis_bus.is_listening:
            redis_bus.start_listening()
        
        # Prepare protection request event and publish via shim.publish()
        event_channel = _map_protection_to_event(protection_type)
        event_payload = {
            'target': 'vault_keepers_conclave',
            'protection_type': protection_type,
            'type': event_channel,
            'correlation_id': correlation_id,
            'state_context': {
                'intent': state.get('intent'),
                'entity_ids': state.get('entity_ids', []),
                'route': state.get('route'),
                'human_input_preview': state.get('human_input', '')[:100]
            },
            'priority': 'high' if protection_type == 'critical' else 'normal'
        }
        
        try:
            event_id = redis_bus.publish(
                channel=event_channel,
                payload=event_payload,
                emitter='langgraph_vault_node',
            )
            publish_success = bool(event_id)
        except Exception as pub_err:
            logger.warning(f"[VAULT][GRAPH] ⚠️ Publish error: {pub_err}")
            publish_success = False
        
        if not publish_success:
            logger.warning(f"[VAULT][GRAPH] ⚠️ Failed to publish protection request")
            return _create_fallback_protection()
        
        logger.info(f"[VAULT][GRAPH] 📡 Protection request published: {event_channel}")
        
        # TODO: Implement async protection retrieval via Postgres polling
        # Current: Synchronous pub/sub pattern incompatible with Redis Streams
        # Future: Poll vault_protection table with correlation_id or use HTTP callback
        # For now: Apply local blessing immediately (async processing by vault_listener)
        vault_response = None  # Disabled: _await_divine_protection(correlation_id, timeout=5.0)
        
        if vault_response:
            return vault_response
        else:
            logger.info(f"[VAULT][GRAPH] 🏰 Applying standard blessing (async protection in progress)")
            return _create_fallback_protection()
            
    except Exception as e:
        logger.error(f"[VAULT][GRAPH] ❌ Error requesting divine protection: {e}")
        return _create_fallback_protection()


def _map_protection_to_event(protection_type: str) -> str:
    """Map protection type to appropriate vault event"""
    mapping = {
        "integrity_check": "integrity.check.requested",
        "critical": "backup.create.requested",
        "domain_guardian": "audit.vault.requested",
        "standard": "integrity.check.requested"
    }
    return mapping.get(protection_type, "integrity.check.requested")


def _await_divine_protection(correlation_id: str, timeout: float = 5.0) -> Dict[str, Any]:
    """Wait for divine protection response from Vault Keepers"""
    
    start_time = time.time()
    received_response = {}
    
    def response_handler(event: Any):
        """Handle vault protection response"""
        nonlocal received_response
        
        if event.correlation_id == correlation_id:
            logger.info(f"[VAULT][GRAPH] ✨ Divine protection received: {event.type}")
            received_response = event.to_dict()
    
    try:
        # Subscribe to vault response patterns
        redis_bus = get_redis_bus()
        vault_response_patterns = [
            'vault.integrity.verified',
            'vault.backup.created',
            'vault.audit.completed',
            'vault.protection.granted'
        ]
        
        for pattern in vault_response_patterns:
            redis_bus.subscribe(pattern, response_handler)
        
        # Wait for response with timeout
        while time.time() - start_time < timeout:
            if received_response:
                protection_latency = (time.time() - start_time) * 1000
                logger.info(f"[VAULT][GRAPH] 🏰 Divine protection received in {protection_latency:.1f}ms")
                return received_response.get('payload', {})
            
            time.sleep(0.01)  # 10ms polling interval
        
        # Timeout reached
        logger.warning(f"[VAULT][GRAPH] ⏰ Divine protection timeout after {timeout}s")
        return None
        
    except Exception as e:
        logger.error(f"[VAULT][GRAPH] ❌ Error awaiting divine protection: {e}")
        return None


def _apply_vault_blessing(state: Dict[str, Any], protection_result: Dict[str, Any]) -> Dict[str, Any]:
    """Apply vault blessing to conversation state"""
    
    vault_status = protection_result.get('vault_status', 'blessed')
    guardian_oversight = protection_result.get('guardian_oversight', {})
    
    # Add vault metadata to state
    vault_metadata = {
        "vault_status": vault_status,
        "vault_protection": "divine_blessing_applied",
        "vault_guardian": guardian_oversight.get('guardian_blessing', 'protection_granted'),
        "vault_timestamp": datetime.utcnow().isoformat(),
        "protection_type": "synaptic_conclave_integration"
    }
    
    # Merge vault blessing into state
    state["vault_blessing"] = vault_metadata
    
    # Add vault context to response metadata
    if "metadata" not in state:
        state["metadata"] = {}
    state["metadata"]["vault_protection"] = vault_metadata
    
    logger.info(f"[VAULT][GRAPH] 🏰 Vault blessing applied: {vault_status}")
    
    return state


def _apply_standard_blessing(state: Dict[str, Any]) -> Dict[str, Any]:
    """Apply standard vault blessing when full protection not needed"""
    
    vault_metadata = {
        "vault_status": "blessed",
        "vault_protection": "standard_blessing",
        "vault_guardian": "routine_protection",
        "vault_timestamp": datetime.utcnow().isoformat(),
        "protection_type": "local_blessing"
    }
    
    state["vault_blessing"] = vault_metadata
    
    if "metadata" not in state:
        state["metadata"] = {}
    state["metadata"]["vault_protection"] = vault_metadata
    
    return state


def _apply_emergency_blessing(state: Dict[str, Any], error_message: str) -> Dict[str, Any]:
    """Apply emergency blessing when vault protection fails"""
    
    vault_metadata = {
        "vault_status": "emergency_blessed",
        "vault_protection": "emergency_fallback",
        "vault_guardian": "local_emergency_protection",
        "vault_timestamp": datetime.utcnow().isoformat(),
        "protection_type": "emergency_fallback",
        "vault_error": error_message
    }
    
    state["vault_blessing"] = vault_metadata
    
    if "metadata" not in state:
        state["metadata"] = {}
    state["metadata"]["vault_protection"] = vault_metadata
    
    # Add warning to state
    if "warnings" not in state:
        state["warnings"] = []
    state["warnings"].append(f"Vault protection failed, emergency blessing applied: {error_message}")
    
    logger.warning(f"[VAULT][GRAPH] ⚠️ Emergency blessing applied due to: {error_message}")
    
    return state


def _create_fallback_protection() -> Dict[str, Any]:
    """Create fallback protection response"""
    return {
        "vault_status": "locally_blessed",
        "guardian_oversight": {
            "guardian_blessing": "local_protection_granted",
            "protection_measures": ["local_integrity_check", "emergency_blessing"]
        },
        "sacred_response": {
            "type": "local_protection_response",
            "message": "Local vault protection applied"
        },
        "correlation_id": f"local_fallback_{int(time.time() * 1000)}",
        "sacred_timestamp": datetime.utcnow().isoformat()
    }


# Test function for development
def test_vault_node():
    """Test the vault node functionality"""
    test_state = {
        "human_input": "Show me collection allocation for retirement with backup protection",
        "intent": "allocate", 
        "entity_ids": ["EXAMPLE_ENTITY_1", "EXAMPLE_ENTITY_4"],
        "route": "vault"
    }
    
    result = vault_node(test_state)
    print(f"Test result: {result}")
    return result


if __name__ == "__main__":
    # Run test
    test_result = test_vault_node()
    print(f"✅ Vault node test completed: {test_result.get('vault_blessing', {}).get('vault_status', 'unknown')}")