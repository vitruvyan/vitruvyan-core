"""
Base service class for all Gemma cognitive modules.
Provides common functionality and dependency injection.
"""
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

# Import standard Vitruvyan agents as required
from core.foundation.persistence import PostgresAgent
from core.foundation.persistence import QdrantAgent

# Configure logger
logger = logging.getLogger(__name__)

class GemmaServiceBase(ABC):
    """Base class for all Gemma cognitive services."""
    
    def __init__(self, name: str):
        import os
        self.name = name
        self.logger = logging.getLogger(f"gemma.{name}")
        self.is_initialized = False
        self._model_manager = None
        self._vector_cache = None
        self._integrity_watcher = None
        
        # Sacred Test Mode Protection - Bypass database in test mode
        self.test_mode = os.getenv('VITRUVYAN_TEST_MODE', 'false').lower() == 'true'
        
        # Initialize standard Vitruvyan agents as required
        self._postgres_agent = None
        self._qdrant_agent = None
    
    async def initialize(self, model_manager, vector_cache, integrity_watcher):
        """Initialize the service with shared components."""
        try:
            self._model_manager = model_manager
            self._vector_cache = vector_cache
            self._integrity_watcher = integrity_watcher
            
            if self.test_mode:
                self.logger.info(f"🛡️ Sacred Test Mode: Bypassing PostgreSQL/Qdrant initialization for {self.name}")
                self._postgres_agent = None
                self._qdrant_agent = None
            else:
                # Initialize standard Vitruvyan agents as required
                self._postgres_agent = PostgresAgent()
                self._qdrant_agent = QdrantAgent()
                self.logger.info(f"✅ PostgresAgent and QdrantAgent initialized for {self.name}")
            
            # Perform service-specific initialization
            await self._initialize_service()
            
            self.is_initialized = True
            self.logger.info(f"{self.name} service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.name} service: {e}")
            raise
    
    @abstractmethod
    async def _initialize_service(self):
        """Service-specific initialization logic."""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Basic health check for the service."""
        return {
            "service": self.name,
            "status": "healthy" if self.is_initialized else "initializing",
            "initialized": self.is_initialized
        }
    
    def is_healthy(self) -> bool:
        """Simple boolean health check for monitoring systems."""
        return self.is_initialized
    
    def require_initialization(self):
        """Ensure the service is initialized before processing."""
        if not self.is_initialized:
            raise RuntimeError(f"{self.name} service not initialized")
    
    @property
    def model_manager(self):
        """Access to shared model manager."""
        self.require_initialization()
        return self._model_manager
    
    @property
    def vector_cache(self):
        """Access to shared vector cache."""
        self.require_initialization()
        return self._vector_cache
    
    @property
    def integrity_watcher(self):
        """Access to shared integrity watcher."""
        self.require_initialization()
        return self._integrity_watcher
    
    @property
    def postgres_agent(self):
        """Access to standard PostgresAgent."""
        self.require_initialization()
        return self._postgres_agent
    
    @property
    def qdrant_agent(self):
        """Access to standard QdrantAgent."""
        self.require_initialization()
        return self._qdrant_agent
    
    async def safe_execute(self, operation_name: str, operation_func, *args, **kwargs):
        """Execute an operation with error handling and logging."""
        try:
            self.require_initialization()
            self.logger.debug(f"Executing {operation_name}")
            
            result = await operation_func(*args, **kwargs)
            
            self.logger.debug(f"Completed {operation_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in {operation_name}: {e}")
            raise
    
    @asynccontextmanager
    async def operation_context(self, operation_name: str):
        """Context manager for operations with automatic logging."""
        self.logger.info(f"Starting {operation_name}")
        start_time = asyncio.get_event_loop().time()
        
        try:
            yield
            
        except Exception as e:
            self.logger.error(f"Failed {operation_name}: {e}")
            raise
            
        finally:
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            self.logger.info(f"Completed {operation_name} in {duration:.2f}s")


class GemmaModuleMetrics:
    """Metrics collection for Gemma modules."""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.total_processing_time = 0.0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def record_request(self, processing_time: float, cached: bool = False):
        """Record a processed request."""
        self.request_count += 1
        self.total_processing_time += processing_time
        
        if cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def record_error(self):
        """Record an error."""
        self.error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        avg_time = (
            self.total_processing_time / self.request_count 
            if self.request_count > 0 else 0
        )
        
        cache_rate = (
            self.cache_hits / (self.cache_hits + self.cache_misses)
            if (self.cache_hits + self.cache_misses) > 0 else 0
        )
        
        return {
            "requests": self.request_count,
            "errors": self.error_count,
            "avg_processing_time": avg_time,
            "cache_hit_rate": cache_rate,
            "total_processing_time": self.total_processing_time
        }