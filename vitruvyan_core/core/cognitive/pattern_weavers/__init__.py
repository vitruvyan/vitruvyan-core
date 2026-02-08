"""
Pattern Weavers — Sacred Order of Semantic Contextualization
Epistemic Order: REASON (Semantic Layer)

Connects concepts, sectors, regions, and risk profiles to enrich 
quantitative analysis with semantic understanding.

Author: Sacred Orders
Created: November 9, 2025
Status: PRODUCTION READY
"""

__version__ = "1.0.0"
__epistemic_order__ = "REASON"
__layer__ = "SEMANTIC"

from core.cognitive.pattern_weavers.weaver_engine import PatternWeaverEngine
from core.cognitive.pattern_weavers.weaver_client import PatternWeaverClient

__all__ = ["PatternWeaverEngine", "PatternWeaverClient"]
