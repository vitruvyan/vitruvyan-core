"""
Memory Orders — Base Consumer (MemoryRole ABC)

Abstract base class for all Memory Orders decision engines.
Enforces PURE function contract: no I/O, no side effects.

Sacred Order: Memory & Coherence
Layer: Foundational (LIVELLO 1 — consumers/base)
"""

from abc import ABC, abstractmethod
from typing import Any


class MemoryRole(ABC):
    """
    Base class for all Memory Orders consumers.
    
    Contract:
    - `process()` MUST be PURE (same input → same output)
    - NO I/O (no database, no HTTP, no filesystem)
    - NO side effects (no mutations, no external state changes)
    - Deterministic and testable in isolation
    
    Override `can_handle()` for selective event routing (default: accepts all).
    """
    
    @abstractmethod
    def process(self, payload: Any) -> Any:
        """
        Pure transformation: input → output.
        
        Args:
            payload: Input data (typically a domain object or dict)
        
        Returns:
            Transformed output (typically a domain object)
        
        Raises:
            ValueError: If payload is invalid or cannot be processed
        """
        pass
    
    def can_handle(self, payload: Any) -> bool:
        """
        Override for selective routing.
        
        Used by service adapters to determine if this consumer
        should process a given event.
        
        Args:
            payload: Input data to evaluate
        
        Returns:
            True if this consumer can process the payload, False otherwise
        
        Default: True (accepts all payloads)
        """
        return True
