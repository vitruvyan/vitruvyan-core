# api_gemma_cognitive/shared/__init__.py
"""
🔧 Shared Infrastructure Package
Unified components for Gemma Cognitive Layer
"""

from .base_service import GemmaServiceBase
from .model_manager import UnifiedModelManager, model_manager
from .vector_cache import UnifiedVectorCache, vector_cache  
from .integrity_watcher import UnifiedIntegrityWatcher, integrity_watcher

__all__ = [
    "GemmaServiceBase",
    "UnifiedModelManager", 
    "model_manager",
    "UnifiedVectorCache",
    "vector_cache", 
    "UnifiedIntegrityWatcher",
    "integrity_watcher"
]