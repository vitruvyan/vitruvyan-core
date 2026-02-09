# api_gemma_cognitive/__init__.py
"""
🧠 Unified Gemma Cognitive Layer
Phase 2 of Vitruvyan OS Blueprint 2026 - Hybrid Transition Plan

This package provides a unified container combining 4 specialized cognitive modules:
- EmbeddingEngine: Multilingual embedding generation with Gemma models
- SentimentFusion: Multi-model sentiment analysis with advanced fusion
- ProfileProcessor: User profiling and content personalization
- CognitiveBridge: Intelligent routing and service orchestration

Architecture:
- Shared infrastructure (models, cache, integrity monitoring)
- Modular design with clear separation of concerns
- Backward compatibility with existing Vitruvyan services
- Performance optimized with lazy loading and caching
"""

__version__ = "1.0.0"
__author__ = "Vitruvyan AI Team"
__description__ = "Unified Gemma Cognitive Layer for Vitruvyan OS"

# Export key components for external use
from .modules import (
    EmbeddingEngineModule,
    SentimentFusionModule,
    ProfileProcessorModule, 
    CognitiveBridgeModule
)

from .shared import (
    GemmaServiceBase,
    UnifiedModelManager,
    UnifiedVectorCache,
    UnifiedIntegrityWatcher
)

__all__ = [
    # Modules
    "EmbeddingEngineModule",
    "SentimentFusionModule",
    "ProfileProcessorModule", 
    "CognitiveBridgeModule",
    
    # Shared Infrastructure
    "GemmaServiceBase",
    "UnifiedModelManager",
    "UnifiedVectorCache", 
    "UnifiedIntegrityWatcher",
    
    # Metadata
    "__version__",
    "__author__",
    "__description__"
]