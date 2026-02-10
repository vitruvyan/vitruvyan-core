"""
Sentiment Node — Domain-Agnostic Stub
======================================

This is a STUB implementation for vitruvyan-core.
Sentiment analysis is domain-specific (finance sentiment differs from
healthcare sentiment). The actual implementation should be provided
by a GraphPlugin.

In the domain-agnostic core, this node simply passes through.

Author: Vitruvyan Core Team  
Created: February 10, 2026
Status: STUB — Override with domain-specific implementation
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def run_sentiment_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    🌐 [DOMAIN-AGNOSTIC] Sentiment Node
    
    Stub implementation that passes through without modification.
    Domain plugins override this with actual sentiment analysis.
    
    In finance domain: Analyzes market sentiment for entities
    In healthcare domain: Analyzes patient sentiment/mood
    In logistics domain: Analyzes customer satisfaction
    
    Args:
        state: LangGraph state dictionary
        
    Returns:
        State unchanged (stub behavior)
    """
    logger.debug("[sentiment_node] 🌐 STUB - passthrough (no domain-specific sentiment analysis)")
    
    # Preserve any existing sentiment data
    # The actual sentiment analysis comes from Babel Gardens emotion_node
    # which is already domain-agnostic
    
    return state


# Alias for backward compatibility
sentiment_node = run_sentiment_node
