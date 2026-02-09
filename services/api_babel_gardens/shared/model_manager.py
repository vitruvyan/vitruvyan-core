# api_gemma_cognitive/shared/model_manager.py
"""
🧠 Unified Model Manager
Handles Gemma models loading, caching, and lifecycle across all modules
"""

import asyncio
import logging
from typing import Dict, Optional, Any, List, Union
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModel, pipeline
from datetime import datetime, timedelta

from .base_service import GemmaServiceBase

logger = logging.getLogger(__name__)

class UnifiedModelManager(GemmaServiceBase):
    """
    🔧 Singleton model manager for all Gemma models
    Provides lazy loading, memory optimization, and model sharing
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            super().__init__("unified_model_manager")
            self.models: Dict[str, Any] = {}
            self.tokenizers: Dict[str, Any] = {}
            self.pipelines: Dict[str, Any] = {}
            self.model_configs: Dict[str, Dict] = {}
            self.last_used: Dict[str, datetime] = {}
            self.loading_locks: Dict[str, asyncio.Lock] = {}
            self._cleanup_task = None
            UnifiedModelManager._initialized = True
    
    async def _initialize_service(self):
        """Service-specific initialization for model manager"""
        # This will be called by the base class initialize method
        pass
    
    async def initialize(self):
        """Initialize the model manager"""
        # ModelManager doesn't have external dependencies, so we skip super().initialize()
        self.healthy = True
        
        # Model configurations
        self.model_configs = {
            "gemma_embeddings": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",  # Lightweight model for testing
                "type": "embeddings",
                "max_length": 512,
                "batch_size": 16,
                "device": "cpu"  # Keep on CPU for compatibility
            },
            "gemma_sentiment": {
                "model_name": "cardiffnlp/twitter-roberta-base-sentiment-latest", 
                "type": "sentiment",
                "max_length": 512,
                "batch_size": 8,
                "device": "cpu"
            },
            "gemma_multilingual": {
                "model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "type": "multilingual",
                "max_length": 512,
                "batch_size": 12,
                "device": "cpu"
            },
            "finbert": {
                "model_name": "ProsusAI/finbert",
                "type": "financial_sentiment",
                "max_length": 512,
                "batch_size": 16,
                "device": "cpu"  # FinBERT stays on CPU for compatibility
            }
        }
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._model_cleanup_task())
        
        logger.info("🧠 Unified Model Manager initialized")
    
    async def get_model(self, model_key: str, force_load: bool = False) -> Optional[Any]:
        """
        Get a model with lazy loading
        
        Args:
            model_key: Model identifier
            force_load: Force reload even if cached
            
        Returns:
            Loaded model or None if failed
        """
        # Auto-initialize if not done
        if not self.model_configs:
            logger.info("🔄 Auto-initializing model_manager on first use...")
            await self.initialize()
            logger.info(f"🧠 Model configs available: {list(self.model_configs.keys())}")
        
        if model_key not in self.model_configs:
            logger.error(f"❌ Unknown model key: {model_key}")
            return None
        
        # Check if already loaded
        if not force_load and model_key in self.models:
            self.last_used[model_key] = datetime.now()
            return self.models[model_key]
        
        # Get or create loading lock
        if model_key not in self.loading_locks:
            self.loading_locks[model_key] = asyncio.Lock()
        
        async with self.loading_locks[model_key]:
            # Double-check after acquiring lock
            if not force_load and model_key in self.models:
                self.last_used[model_key] = datetime.now()
                return self.models[model_key]
            
            try:
                config = self.model_configs[model_key]
                model_name = config["model_name"]
                
                logger.info(f"🔄 Loading model: {model_key} ({model_name})")
                
                # Load based on model type
                if config["type"] == "embeddings":
                    model = await self._load_embedding_model(model_name, config)
                elif config["type"] in ["sentiment", "financial_sentiment"]:
                    model = await self._load_sentiment_model(model_name, config)
                elif config["type"] == "multilingual":
                    model = await self._load_multilingual_model(model_name, config)
                else:
                    logger.error(f"❌ Unknown model type: {config['type']}")
                    return None
                
                self.models[model_key] = model
                self.last_used[model_key] = datetime.now()
                
                logger.info(f"✅ Model loaded successfully: {model_key}")
                return model
                
            except Exception as e:
                logger.error(f"❌ Failed to load model {model_key}: {str(e)}")
                return None
    
    async def get_tokenizer(self, model_key: str) -> Optional[Any]:
        """Get tokenizer for a model"""
        if model_key not in self.model_configs:
            return None
        
        if model_key not in self.tokenizers:
            try:
                config = self.model_configs[model_key]
                model_name = config["model_name"]
                
                logger.info(f"🔤 Loading tokenizer: {model_key}")
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.tokenizers[model_key] = tokenizer
                
            except Exception as e:
                logger.error(f"❌ Failed to load tokenizer {model_key}: {str(e)}")
                return None
        
        return self.tokenizers[model_key]
    
    async def get_pipeline(self, model_key: str, task: str) -> Optional[Any]:
        """Get or create a pipeline for a model"""
        pipeline_key = f"{model_key}_{task}"
        
        if pipeline_key not in self.pipelines:
            try:
                config = self.model_configs[model_key]
                model_name = config["model_name"]
                device = 0 if config["device"] == "cuda" else -1
                
                logger.info(f"🔧 Creating pipeline: {pipeline_key}")
                pipe = pipeline(
                    task=task,
                    model=model_name,
                    device=device,
                    return_all_scores=True
                )
                self.pipelines[pipeline_key] = pipe
                
            except Exception as e:
                logger.error(f"❌ Failed to create pipeline {pipeline_key}: {str(e)}")
                return None
        
        return self.pipelines[pipeline_key]
    
    async def _load_embedding_model(self, model_name: str, config: Dict) -> Any:
        """Load embedding model"""
        try:
            if "sentence-transformers" in model_name:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer(model_name)
                return model
            else:
                model = AutoModel.from_pretrained(model_name)
                if config["device"] == "cuda" and torch.cuda.is_available():
                    model = model.cuda()
                model.eval()
                return model
        except ImportError:
            # Fallback to transformers if sentence-transformers not available
            model = AutoModel.from_pretrained(model_name)
            if config["device"] == "cuda" and torch.cuda.is_available():
                model = model.cuda()
            model.eval()
            return model
    
    async def _load_sentiment_model(self, model_name: str, config: Dict) -> Any:
        """Load sentiment analysis model"""
        model = AutoModel.from_pretrained(model_name)
        if config["device"] == "cuda" and torch.cuda.is_available():
            model = model.cuda()
        model.eval()
        return model
    
    async def _load_multilingual_model(self, model_name: str, config: Dict) -> Any:
        """Load multilingual model"""
        model = AutoModel.from_pretrained(model_name)
        if config["device"] == "cuda" and torch.cuda.is_available():
            model = model.cuda()
        model.eval()
        return model
    
    async def preload_models(self, model_keys: List[str]):
        """Preload specified models"""
        tasks = []
        for model_key in model_keys:
            if model_key in self.model_configs:
                tasks.append(self.get_model(model_key))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"🚀 Preloaded {len(tasks)} models")
    
    def get_model_info(self, model_key: str) -> Optional[Dict[str, Any]]:
        """Get model information"""
        if model_key not in self.model_configs:
            return None
        
        config = self.model_configs[model_key].copy()
        config.update({
            "loaded": model_key in self.models,
            "last_used": self.last_used.get(model_key),
            "memory_efficient": config["device"] != "cuda" or not torch.cuda.is_available()
        })
        
        return config
    
    def get_all_models_info(self) -> Dict[str, Any]:
        """Get information about all models"""
        return {
            model_key: self.get_model_info(model_key)
            for model_key in self.model_configs.keys()
        }
    
    async def unload_model(self, model_key: str):
        """Unload a specific model"""
        if model_key in self.models:
            del self.models[model_key]
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info(f"🗑️ Unloaded model: {model_key}")
    
    async def unload_unused_models(self, max_age_minutes: int = 30):
        """Unload models that haven't been used recently"""
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        to_unload = []
        
        for model_key, last_used in self.last_used.items():
            if last_used < cutoff_time and model_key in self.models:
                to_unload.append(model_key)
        
        for model_key in to_unload:
            await self.unload_model(model_key)
        
        if to_unload:
            logger.info(f"🧹 Unloaded {len(to_unload)} unused models")
    
    async def _model_cleanup_task(self):
        """Background task for model cleanup"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                await self.unload_unused_models()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Model cleanup error: {str(e)}")
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        if torch.cuda.is_available():
            gpu_memory = {
                "allocated": torch.cuda.memory_allocated() / 1024**2,  # MB
                "reserved": torch.cuda.memory_reserved() / 1024**2,    # MB
                "max_allocated": torch.cuda.max_memory_allocated() / 1024**2  # MB
            }
        else:
            gpu_memory = {"message": "CUDA not available"}
        
        return {
            "models_loaded": len(self.models),
            "tokenizers_loaded": len(self.tokenizers),
            "pipelines_created": len(self.pipelines),
            "gpu_memory_mb": gpu_memory
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for model manager"""
        try:
            memory_info = self.get_memory_usage()
            models_info = self.get_all_models_info()
            
            # Test a simple model operation if any model is loaded
            test_result = "no_models_loaded"
            if self.models:
                test_result = "models_responsive"
            
            return {
                "status": "healthy",
                "models": models_info,
                "memory": memory_info,
                "test_result": test_result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Unload all models
        for model_key in list(self.models.keys()):
            await self.unload_model(model_key)
        
        self.tokenizers.clear()
        self.pipelines.clear()
        
        await super().cleanup()
        logger.info("🧠 Model Manager cleaned up")

# Global singleton instance
model_manager = UnifiedModelManager()