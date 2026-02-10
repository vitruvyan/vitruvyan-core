"""
Codex Hunters - Base Consumer
=============================

Abstract base for all Codex Hunters consumers.
Pure Python - no I/O, no external dependencies.

Author: Vitruvyan Core Team
Created: February 2026
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging

from ..domain import CodexConfig, CodexEvent, get_config

logger = logging.getLogger(__name__)


@dataclass
class ProcessResult:
    """Result of a consumer process() call."""
    success: bool
    data: Dict[str, Any]
    errors: List[str] = None
    warnings: List[str] = None
    processing_time_ms: int = 0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class BaseConsumer(ABC):
    """
    Abstract base class for Codex Hunters consumers.
    
    Consumers are pure processing units:
    - NO I/O (database, network, file system)
    - NO external dependencies (Redis, PostgreSQL, Qdrant)
    - Receive data as input, return processed data as output
    
    I/O is handled by adapters in LIVELLO 2 (service layer).
    """
    
    def __init__(self, config: CodexConfig = None):
        """
        Initialize consumer with configuration.
        
        Args:
            config: Domain configuration. If None, uses default.
        """
        self._config = config or get_config()
        self._name = self.__class__.__name__
        self._created_at = datetime.utcnow()
        self._process_count = 0
        self._error_count = 0
    
    @property
    def config(self) -> CodexConfig:
        """Get configuration."""
        return self._config
    
    @property
    def name(self) -> str:
        """Get consumer name."""
        return self._name
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> ProcessResult:
        """
        Process input data and return result.
        
        Args:
            data: Input data dictionary
            
        Returns:
            ProcessResult with processed data
        """
        pass
    
    def validate_input(self, data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """
        Validate input data has required fields.
        
        Args:
            data: Input dictionary
            required_fields: List of required field names
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
            elif data[field] is None:
                errors.append(f"Field is None: {field}")
        return errors
    
    def create_event(
        self,
        event_type: str,
        payload: Dict[str, Any] = None,
        target: str = None,
        correlation_id: str = None
    ) -> CodexEvent:
        """
        Create a CodexEvent from this consumer.
        
        Args:
            event_type: Type of event
            payload: Event payload
            target: Target service/consumer
            correlation_id: Correlation ID for tracking
            
        Returns:
            CodexEvent instance
        """
        return CodexEvent(
            event_type=event_type,
            source=self._name,
            target=target,
            payload=payload or {},
            correlation_id=correlation_id
        )
    
    def _record_success(self):
        """Record successful processing."""
        self._process_count += 1
    
    def _record_error(self):
        """Record processing error."""
        self._process_count += 1
        self._error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get consumer statistics."""
        return {
            "name": self._name,
            "created_at": self._created_at.isoformat(),
            "process_count": self._process_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(1, self._process_count),
        }
