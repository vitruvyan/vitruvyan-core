"""
Babel Gardens - Base Consumer
=============================

Base class for all Babel Gardens consumers.
Pure Python - NO I/O, NO external dependencies.

Author: Vitruvyan Core Team
Version: 2.0.0 (February 2026)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..domain import BabelConfig, ProcessingStatus


@dataclass
class ProcessResult:
    """Result of consumer processing."""
    
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "errors": self.errors,
            "processing_time_ms": self.processing_time_ms,
        }


class BaseConsumer(ABC):
    """
    Base class for Babel Gardens consumers.
    
    Pure processing logic - NO I/O, NO HTTP calls, NO database access.
    Consumers receive data and return results.
    """
    
    def __init__(self, config: BabelConfig):
        """
        Initialize consumer with configuration.
        
        Args:
            config: BabelConfig instance (injected, not created here)
        """
        self.config = config
        self._processed_count = 0
        self._error_count = 0
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> ProcessResult:
        """
        Process input data and return result.
        
        This method must be pure - no side effects, no I/O.
        
        Args:
            data: Input data dictionary
            
        Returns:
            ProcessResult with success status and output data
        """
        pass
    
    def validate_input(self, data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """
        Validate input data has required fields.
        
        Args:
            data: Input data dictionary
            required_fields: List of required field names
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
            elif data[field] is None:
                errors.append(f"Field cannot be None: {field}")
        return errors
    
    def _record_success(self):
        """Record successful processing."""
        self._processed_count += 1
    
    def _record_error(self):
        """Record processing error."""
        self._error_count += 1
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        return {
            "processed": self._processed_count,
            "errors": self._error_count,
        }
