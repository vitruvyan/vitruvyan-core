# api_gemma_cognitive/modules/__init__.py
"""
🧩 Cognitive Modules Package
All specialized modules for the unified Gemma Cognitive Layer
"""

from .embedding_engine import EmbeddingEngineModule
from .profile_processor import ProfileProcessorModule
from .cognitive_bridge import CognitiveBridgeModule

__all__ = [
    "EmbeddingEngineModule",
    "ProfileProcessorModule",
    "CognitiveBridgeModule"
]