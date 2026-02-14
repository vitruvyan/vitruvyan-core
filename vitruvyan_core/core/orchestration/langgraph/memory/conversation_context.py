# Context Memory for LLM Enhancement
# core/langgraph/memory/conversation_context.py
#
# Version: 2.0 (Feb 14, 2026)
#   - Finance-specific terms removed (MarketContextProvider → DomainContextProvider)
#   - investment_horizon → temporal_horizon
#   - Hardcoded market narrative removed

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

class ConversationContextManager:
    """
    Manages conversational context for enhanced LLM responses.
    Domain-agnostic: tracks user preferences, entities, and interaction patterns.
    """
    
    def __init__(self):
        self.context_window = 5  # Remember last 5 interactions
        
    def build_conversation_context(self, user_id: str, current_state: Dict[str, Any]) -> str:
        """Build conversation context from recent interactions"""
        
        # Get recent conversation history (would integrate with postgres)
        conversation_history = self._get_recent_conversations(user_id)
        
        # Extract key themes and preferences
        context_summary = self._extract_context_themes(conversation_history)
        
        # Build context string for LLM
        return self._format_context_for_llm(context_summary, current_state)
    
    def _get_recent_conversations(self, user_id: str) -> List[Dict]:
        """Get recent conversation history - uses VSGS semantic_grounding_node"""
        # Phase 2 Migration (Nov 2025): Use semantic_grounding_node state["semantic_matches"]
        return []
    
    def _extract_context_themes(self, history: List[Dict]) -> Dict[str, Any]:
        """Extract recurring themes and user preferences"""
        themes = {
            "preferred_entities": [],
            "risk_tolerance": "unknown",
            "temporal_horizon": "unknown", 
            "emotional_state": "neutral",
            "expertise_level": "intermediate",
            "language_preference": "en"
        }
        
        # Analyze conversation patterns
        for conv in history:
            # Extract entity_ids mentioned
            if "entity_ids" in conv:
                themes["preferred_entities"].extend(conv["entity_ids"])
            
            # Extract risk signals
            input_text = conv.get("input_text", "").lower()
            if any(word in input_text for word in ["safe", "conservative", "low risk"]):
                themes["risk_tolerance"] = "conservative"
            elif any(word in input_text for word in ["aggressive", "growth", "high return"]):
                themes["risk_tolerance"] = "aggressive"
        
        # Deduplicate preferred entity_ids
        themes["preferred_entities"] = list(set(themes["preferred_entities"]))
        
        return themes
    
    def _format_context_for_llm(self, themes: Dict[str, Any], current_state: Dict[str, Any]) -> str:
        """Format context for LLM consumption"""
        
        context_parts = []
        
        # User profile
        if themes["preferred_entities"]:
            context_parts.append(f"User often discusses: {', '.join(themes['preferred_entities'][:5])}")
        
        if themes["risk_tolerance"] != "unknown":
            context_parts.append(f"Risk tolerance: {themes['risk_tolerance']}")
        
        if themes["temporal_horizon"] != "unknown":
            context_parts.append(f"Temporal horizon: {themes['temporal_horizon']}")
        
        # Current session context
        current_entities = current_state.get("entity_ids", [])
        if current_entities:
            context_parts.append(f"Current focus: {', '.join(current_entities)}")
        
        return "CONVERSATION CONTEXT:\n" + "\n".join(f"- {part}" for part in context_parts)


class DomainContextProvider:
    """
    Provides dynamic domain context for LLM responses.
    Domain-agnostic: returns generic context by default.
    Domain plugins can override or extend this via configuration.
    """
    
    def get_domain_narrative(self, entity_ids: List[str] = None) -> str:
        """Get current domain narrative context"""
        
        # Base domain context
        base_context = self._get_base_context()
        
        # Entity-specific context
        entity_context = ""
        if entity_ids:
            entity_context = self._get_entity_specific_context(entity_ids)
        
        return f"{base_context}\n{entity_context}".strip()
    
    def _get_base_context(self) -> str:
        """Base environment context (domain-neutral)"""
        # Domain plugins should override this with domain-specific context
        return """
CURRENT ENVIRONMENT:
- Domain context not configured (using generic defaults)
- Configure a domain plugin to provide environment-specific context
"""
    
    def _get_entity_specific_context(self, entity_ids: List[str]) -> str:
        """Get specific context for mentioned entity_ids"""
        # Domain plugins should override this with entity-specific lookups
        if not entity_ids:
            return ""
        return f"ENTITY CONTEXT:\n- Entities referenced: {', '.join(entity_ids)}"


# Integration function for enhanced LLM node
def enhance_llm_with_context(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance LLM state with conversation and domain context"""
    
    user_id = state.get("user_id", "demo")
    entity_ids = state.get("entity_ids", [])
    
    # Add conversation context
    context_manager = ConversationContextManager()
    conversation_context = context_manager.build_conversation_context(user_id, state)
    
    # Add domain context  
    domain_provider = DomainContextProvider()
    domain_context = domain_provider.get_domain_narrative(entity_ids)
    
    # Enhance state
    state["conversation_context"] = conversation_context
    state["domain_context"] = domain_context
    
    return state