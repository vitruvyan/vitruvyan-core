# Context Memory for LLM Enhancement
# core/langgraph/memory/conversation_context.py

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

class ConversationContextManager:
    """
    Manages conversational context for enhanced LLM responses
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
        # conversation_persistence.py moved to legacy/deprecated/
        return []
    
    def _extract_context_themes(self, history: List[Dict]) -> Dict[str, Any]:
        """Extract recurring themes and user preferences"""
        themes = {
            "preferred_entities": [],
            "risk_tolerance": "unknown",
            "investment_horizon": "unknown", 
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
        
        if themes["investment_horizon"] != "unknown":
            context_parts.append(f"Investment horizon: {themes['investment_horizon']}")
        
        # Current session context
        current_entitys = current_state.get("entity_ids", [])
        if current_entitys:
            context_parts.append(f"Current focus: {', '.join(current_entitys)}")
        
        return "CONVERSATION CONTEXT:\n" + "\n".join(f"- {part}" for part in context_parts)


class MarketContextProvider:
    """
    Provides dynamic market context for LLM responses
    """
    
    def get_market_narrative(self, entity_ids: List[str] = None) -> str:
        """Get current market narrative context"""
        
        # Base market context
        base_context = self._get_base_market_context()
        
        # EntityId-specific context
        entity_context = ""
        if entity_ids:
            entity_context = self._get_entity_specific_context(entity_ids)
        
        return f"{base_context}\n{entity_context}".strip()
    
    def _get_base_market_context(self) -> str:
        """Base market environment context"""
        # This could be enhanced with live market data
        return """
CURRENT MARKET ENVIRONMENT:
- Tech sector leadership continues amid AI revolution
- Interest rate environment remains dynamic
- Geopolitical tensions creating selective volatility
- Energy transition themes driving long-term flows
- Consumer discretionary showing mixed signals
"""
    
    def _get_entity_specific_context(self, entity_ids: List[str]) -> str:
        """Get specific context for mentioned entity_ids"""
        
        # Sector mapping for context
        tech_entities = ["EXAMPLE_ENTITY_1", "EXAMPLE_ENTITY_4", "EXAMPLE_ENTITY_5", "AMZN", "EXAMPLE_ENTITY_3", "EXAMPLE_ENTITY_2"]
        finance_entities = ["JPM", "BAC", "WFC", "GS"]
        
        context_parts = []
        
        for entity_id in entity_ids:
            if entity_id in tech_entities:
                context_parts.append(f"{entity_id}: Part of AI/tech revolution theme")
            elif entity_id in finance_entities:
                context_parts.append(f"{entity_id}: Sensitive to interest rate environment")
            # Add more sector classifications as needed
        
        return "ENTITY_ID-SPECIFIC CONTEXT:\n" + "\n".join(f"- {part}" for part in context_parts) if context_parts else ""


# Integration function for enhanced LLM node
def enhance_llm_with_context(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance LLM state with conversation and market context"""
    
    user_id = state.get("user_id", "demo")
    entity_ids = state.get("entity_ids", [])
    
    # Add conversation context
    context_manager = ConversationContextManager()
    conversation_context = context_manager.build_conversation_context(user_id, state)
    
    # Add market context  
    market_provider = MarketContextProvider()
    market_context = market_provider.get_market_narrative(entity_ids)
    
    # Enhance state
    state["conversation_context"] = conversation_context
    state["market_context"] = market_context
    
    return state