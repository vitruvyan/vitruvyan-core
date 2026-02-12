"""
VEE — Vitruvyan Explainability Engine v3.0

Domain-agnostic multi-level explainability.
All domain knowledge injected via ExplainabilityProvider contract.

Usage:
    from core.vpar.vee import VEEEngine
    from domains.explainability_contract import ExplainabilityProvider

    engine = VEEEngine()
    result = engine.explain(entity_id, metrics, provider)
"""

from .types import AnalysisResult, ExplanationLevels, HistoricalExplanation
from .vee_engine import VEEEngine
from .vee_analyzer import VEEAnalyzer
from .vee_generator import VEEGenerator
from .vee_memory_adapter import VEEMemoryAdapter

__all__ = [
    "VEEEngine", "VEEAnalyzer", "VEEGenerator", "VEEMemoryAdapter",
    "AnalysisResult", "ExplanationLevels", "HistoricalExplanation",
]

__version__ = "3.0.0"