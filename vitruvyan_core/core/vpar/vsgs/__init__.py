"""
VSGS — Vitruvyan Semantic Grounding System v2.0

Semantic context enrichment engine.
Embed text → Search vectors → Classify matches → Return structured results.

Usage:
    from core.vpar.vsgs import VSGSEngine, GroundingConfig

    engine = VSGSEngine(GroundingConfig(enabled=True), embedding_url="http://gemma:8003")
    result = engine.ground("input text", user_id="demo")

Architecture:
    LIVELLO 1 (This module): VSGSEngine, types, config
    LIVELLO 2 (Adapter):     orchestration/langgraph/node/semantic_grounding_node.py
"""

from .types import GroundingConfig, SemanticMatch, GroundingResult
from .vsgs_engine import VSGSEngine

__all__ = ["VSGSEngine", "GroundingConfig", "SemanticMatch", "GroundingResult"]

__version__ = "2.0.0"
