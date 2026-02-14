"""
Neural Engine Module
====================

Domain-agnostic multi-factor ranking engine.

Components:
- engine.py: Main orchestrator (NeuralEngine)
- scoring.py: Z-score calculation (ZScoreCalculator)
- composite.py: Composite scoring (CompositeScorer)
- ranking.py: Entity ranking (RankingEngine)

Usage:
    from vitruvyan_core.core.neural_engine import NeuralEngine
    from contracts import IDataProvider, IScoringStrategy
    
    # Provide domain-specific implementations
    provider = MyDataProvider()  # implements IDataProvider
    strategy = MyScoringStrategy()  # implements IScoringStrategy
    
    # Initialize engine
    engine = NeuralEngine(
        data_provider=provider,
        scoring_strategy=strategy,
        stratification_mode="composite"
    )
    
    # Run ranking
    results = engine.run(
        profile="balanced",
        top_k=10,
        risk_tolerance="medium"
    )

Author: vitruvyan-core
Date: February 8, 2026
"""

from .engine import NeuralEngine, NeuralEngineError
from .scoring import ZScoreCalculator, ZScoreError
from .composite import CompositeScorer, CompositeScorerError
from .ranking import RankingEngine, RankingError

__all__ = [
    # Main Engine
    "NeuralEngine",
    "NeuralEngineError",
    
    # Components
    "ZScoreCalculator",
    "ZScoreError",
    "CompositeScorer",
    "CompositeScorerError",
    "RankingEngine",
    "RankingError",
]
