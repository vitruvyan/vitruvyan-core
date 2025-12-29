#!/usr/bin/env python3
"""
Codex Hunters LangGraph Trigger Helper
=====================================

Helper functions to trigger Codex Hunters expeditions from LangGraph nodes
and other system components. Provides simplified interface for expedition
management and integration.

Key Functions:
- trigger_full_audit(): Comprehensive system integrity audit
- trigger_healing(): Targeted database healing and consistency restoration  
- trigger_discovery(): Data mapping and anomaly discovery
- check_expedition_status(): Monitor expedition progress

Integration Points:
- Called from LangGraph nodes when data integrity issues detected
- Used by Audit Engine for automated system maintenance
- Triggered by external APIs for on-demand expeditions

Author: Vitruvyan Development Team
Created: 2025-01-14
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from core.orchestration.langgraph.graph_flow import build_graph

logger = logging.getLogger(__name__)


class CodexExpeditionTrigger:
    """
    Helper class for triggering Codex Hunters expeditions from LangGraph
    """
    
    def __init__(self):
        self.graph = build_graph()
        
    
    def trigger_full_audit(self, 
                          user_id: str = "system",
                          correlation_id: str = None,
                          priority: str = "high") -> Dict[str, Any]:
        """
        Trigger comprehensive system integrity audit
        
        Returns:
        - expedition_id: str
        - status: str  
        - results: Dict[str, Any] (when completed)
        """
        
        correlation_id = correlation_id or f"audit_{int(datetime.utcnow().timestamp())}"
        
        state = {
            "input_text": "system integrity audit requested",
            "user_id": user_id,
            "route": "codex_expedition",
            "codex_expedition_type": "full_audit",
            "codex_priority": priority,
            "codex_parameters": {
                "automated_trigger": True,
                "comprehensive": True
            },
            "correlation_id": correlation_id
        }
        
        logger.info(f"🔍 Triggering full system audit - correlation: {correlation_id}")
        
        try:
            result = self.graph.invoke(state)
            
            return {
                "expedition_id": result.get("codex_expedition_id"),
                "status": result.get("codex_expedition_status", "unknown"),
                "success": result.get("codex_success", False),
                "results": result.get("codex_expedition_results", {}),
                "agents_deployed": result.get("codex_agents_deployed", []),
                "correlation_id": correlation_id,
                "error": result.get("codex_error_message")
            }
            
        except Exception as e:
            logger.error(f"❌ Full audit trigger failed: {e}")
            return {
                "expedition_id": None,
                "status": "failed",
                "success": False,
                "error": str(e),
                "correlation_id": correlation_id
            }
    
    
    def trigger_healing(self,
                       target_collections: Optional[List[str]] = None,
                       user_id: str = "system", 
                       correlation_id: str = None,
                       priority: str = "high") -> Dict[str, Any]:
        """
        Trigger targeted database healing and consistency restoration
        
        Args:
            target_collections: Specific collections to heal (optional)
            
        Returns:
            expedition_result: Dict with expedition details
        """
        
        correlation_id = correlation_id or f"heal_{int(datetime.utcnow().timestamp())}"
        
        state = {
            "input_text": f"database healing requested for {target_collections or 'all collections'}",
            "user_id": user_id,
            "route": "codex_expedition", 
            "codex_expedition_type": "healing",
            "codex_target_collections": target_collections,
            "codex_priority": priority,
            "codex_parameters": {
                "automated_trigger": True,
                "healing_mode": "comprehensive"
            },
            "correlation_id": correlation_id
        }
        
        logger.info(f"🔧 Triggering database healing - targets: {target_collections}, correlation: {correlation_id}")
        
        try:
            result = self.graph.invoke(state)
            
            return {
                "expedition_id": result.get("codex_expedition_id"),
                "status": result.get("codex_expedition_status", "unknown"), 
                "success": result.get("codex_success", False),
                "results": result.get("codex_expedition_results", {}),
                "collections_healed": target_collections,
                "correlation_id": correlation_id,
                "error": result.get("codex_error_message")
            }
            
        except Exception as e:
            logger.error(f"❌ Healing trigger failed: {e}")
            return {
                "expedition_id": None,
                "status": "failed", 
                "success": False,
                "error": str(e),
                "correlation_id": correlation_id
            }
    
    
    def trigger_discovery(self,
                         user_id: str = "system",
                         correlation_id: str = None,
                         priority: str = "medium") -> Dict[str, Any]:
        """
        Trigger data mapping and anomaly discovery expedition
        
        Returns:
            expedition_result: Dict with discovery results
        """
        
        correlation_id = correlation_id or f"disc_{int(datetime.utcnow().timestamp())}"
        
        state = {
            "input_text": "data discovery and mapping requested",
            "user_id": user_id,
            "route": "codex_expedition",
            "codex_expedition_type": "discovery", 
            "codex_priority": priority,
            "codex_parameters": {
                "automated_trigger": True,
                "deep_scan": True
            },
            "correlation_id": correlation_id
        }
        
        logger.info(f"🗺️ Triggering discovery expedition - correlation: {correlation_id}")
        
        try:
            result = self.graph.invoke(state)
            
            return {
                "expedition_id": result.get("codex_expedition_id"),
                "status": result.get("codex_expedition_status", "unknown"),
                "success": result.get("codex_success", False), 
                "results": result.get("codex_expedition_results", {}),
                "discovery_map": result.get("codex_expedition_results", {}).get("consistency_map", []),
                "correlation_id": correlation_id,
                "error": result.get("codex_error_message")
            }
            
        except Exception as e:
            logger.error(f"❌ Discovery trigger failed: {e}")
            return {
                "expedition_id": None,
                "status": "failed",
                "success": False, 
                "error": str(e),
                "correlation_id": correlation_id
            }


# Singleton instance for easy access
_trigger_instance = None

def get_codex_trigger() -> CodexExpeditionTrigger:
    """Get singleton CodexExpeditionTrigger instance"""
    global _trigger_instance
    if _trigger_instance is None:
        _trigger_instance = CodexExpeditionTrigger()
    return _trigger_instance


# Convenience functions for direct usage
def trigger_full_audit(**kwargs) -> Dict[str, Any]:
    """Convenience function for full audit trigger"""
    return get_codex_trigger().trigger_full_audit(**kwargs)


def trigger_healing(**kwargs) -> Dict[str, Any]:
    """Convenience function for healing trigger"""
    return get_codex_trigger().trigger_healing(**kwargs)


def trigger_discovery(**kwargs) -> Dict[str, Any]:
    """Convenience function for discovery trigger"""
    return get_codex_trigger().trigger_discovery(**kwargs)


# Integration hook for route_node.py
def should_trigger_codex_expedition(state: Dict[str, Any]) -> bool:
    """
    Determine if Codex Hunters expedition should be triggered based on state
    
    Trigger conditions:
    1. Intent contains "audit", "check", "integrity", "consistency"
    2. Error detection in previous nodes
    3. Explicit codex_expedition_type set
    4. System maintenance requests
    """
    
    # Check explicit expedition request
    if state.get("codex_expedition_type"):
        return True
    
    # Check intent-based triggers
    intent = state.get("intent", "").lower()
    trigger_intents = ["audit", "check", "integrity", "consistency", "healing", "repair", "discovery", "map"]
    
    if any(keyword in intent for keyword in trigger_intents):
        logger.info(f"🎯 Intent-based Codex trigger detected: {intent}")
        
        # Set default expedition type based on intent
        if "audit" in intent or "check" in intent or "integrity" in intent:
            state["codex_expedition_type"] = "full_audit"
        elif "heal" in intent or "repair" in intent:
            state["codex_expedition_type"] = "healing"
        elif "discover" in intent or "map" in intent:
            state["codex_expedition_type"] = "discovery"
        else:
            state["codex_expedition_type"] = "full_audit"  # Default
            
        return True
    
    # Check for error conditions in previous nodes
    if state.get("error") or state.get("codex_error_message"):
        logger.info("🚨 Error-based Codex trigger detected")
        state["codex_expedition_type"] = "healing"
        return True
    
    # Check for system maintenance mode
    input_text = state.get("input_text", "").lower()
    maintenance_keywords = ["maintenance", "system check", "data integrity", "database health"]
    
    if any(keyword in input_text for keyword in maintenance_keywords):
        logger.info(f"🔧 Maintenance-based Codex trigger detected: {input_text}")
        state["codex_expedition_type"] = "full_audit"
        return True
    
    return False


if __name__ == "__main__":
    # Test the trigger system
    import asyncio
    
    def test_triggers():
        trigger = CodexExpeditionTrigger()
        
        print("🧪 Testing Codex Hunters triggers...")
        
        # Test full audit
        print("\n1. Testing full audit...")
        audit_result = trigger.trigger_full_audit(correlation_id="test_audit_001")
        print(f"   Result: {audit_result}")
        
        # Test healing
        print("\n2. Testing healing...")
        heal_result = trigger.trigger_healing(target_collections=["phrases"], correlation_id="test_heal_001")
        print(f"   Result: {heal_result}")
        
        # Test discovery
        print("\n3. Testing discovery...")
        disc_result = trigger.trigger_discovery(correlation_id="test_disc_001")
        print(f"   Result: {disc_result}")
        
        print("\n✅ All tests completed")
    
    test_triggers()