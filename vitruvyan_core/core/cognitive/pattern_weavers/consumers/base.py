"""
Pattern Weavers - Base Consumer
===============================

Abstract base for all Pattern Weavers consumers.
Pure Python - no I/O, no external dependencies.

Author: Vitruvyan Core Team
Created: February 2026
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import logging

from ..domain import PatternConfig, get_config

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
    Abstract base class for Pattern Weavers consumers.
    
    Consumers are pure processing units:
    - NO I/O (database, network, file system)
    - NO external dependencies (Redis, PostgreSQL, Qdrant, httpx)
    - Receive data as input, return processed data as output
    
    I/O is handled by adapters in LIVELLO 2 (service layer).
    """
    
    def __init__(self, config: PatternConfig = None):
        """
        Initialize consumer with configuration.
        
        Args:
            config: PatternConfig instance. If None, uses global config.
        """
        self.config = config or get_config()
        self._process_count = 0
        self._error_count = 0
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> ProcessResult:
        """
        Process input data and return result.
        
        Args:
            data: Input data dictionary
            
        Returns:
            ProcessResult with success status and output data
        """
        pass
    
    def validate_input(self, data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """
        Validate that required fields are present.
        
        Args:
            data: Input dictionary
            required_fields: List of required field names
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")
            elif isinstance(data[field], str) and not data[field].strip():
                errors.append(f"Empty required field: {field}")
        return errors
    
    def _record_success(self) -> None:
        """Record successful processing."""
        self._process_count += 1
    
    def _record_error(self) -> None:
        """Record processing error."""
        self._error_count += 1
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        return {
            "process_count": self._process_count,
            "error_count": self._error_count,
        }
