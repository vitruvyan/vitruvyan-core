"""
Semantic Engine — Domain-Agnostic Stub
=======================================

This is a STUB implementation for vitruvyan-core.
The actual semantic parsing logic is domain-specific (finance parses for
tickers/horizons, logistics parses for routes/schedules). The real
implementation should be provided by a domain plugin or service.

In the domain-agnostic core, this module provides passthrough functions.

Author: Vitruvyan Core Team  
Created: February 10, 2026
Status: STUB — Override with domain-specific implementation
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def parse_user_input(
    user_input: str,
    extract_intent: bool = True,
    detect_language: bool = True
) -> Dict[str, Any]:
    """
    🌐 [DOMAIN-AGNOSTIC] Parse User Input
    
    Stub implementation that returns minimal parsed structure.
    Domain plugins override this with actual semantic parsing.
    
    In finance domain: Extracts tickers, horizon, budget, intent
    In logistics domain: Extracts routes, dates, carriers
    In healthcare domain: Extracts patients, symptoms, urgency
    
    Args:
        user_input: Raw user text
        extract_intent: Whether to extract intent (stub ignores this)
        detect_language: Whether to detect language (stub ignores this)
        
    Returns:
        Dict with parsed fields (stub returns minimal structure)
    """
    logger.debug("[semantic_engine] 🌐 STUB - minimal parsing (no domain-specific parser)")
    
    return {
        # Core fields (domain-agnostic)
        "input_text": user_input,
        "language": "en",  # Default to English
        "language_confidence": 0.5,  # Low confidence (stub)
        
        # Intent (to be filled by intent_detection_node)
        "intent": None,
        
        # Domain-specific fields (empty in stub)
        "entity_ids": [],  # Tickers, routes, patients, etc.
        "horizon": None,   # Time horizon
        "amount": None,    # Budget/quantity
        
        # Semantic matches (to be filled by semantic_grounding_node)
        "semantic_matches": [],
        
        # Metadata
        "_stub": True,
        "_message": "Using domain-agnostic stub parser"
    }


def extract_entities(
    text: str,
    entity_type: Optional[str] = None
) -> List[str]:
    """
    🌐 [DOMAIN-AGNOSTIC] Extract Entities from Text
    
    Stub implementation that returns empty list.
    Domain plugins override this with actual entity extraction.
    
    Args:
        text: Text to extract entities from
        entity_type: Optional entity type filter
        
    Returns:
        Empty list (stub behavior)
    """
    logger.debug("[semantic_engine] 🌐 STUB - no entity extraction")
    return []


def detect_language(text: str) -> Dict[str, Any]:
    """
    🌐 [DOMAIN-AGNOSTIC] Detect Language
    
    Stub implementation that defaults to English.
    The actual language detection is handled by Babel Gardens.
    
    Args:
        text: Text to detect language for
        
    Returns:
        Dict with language code and confidence
    """
    return {
        "language": "en",
        "confidence": 0.5,
        "_stub": True
    }
