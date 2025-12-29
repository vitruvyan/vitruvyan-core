#!/usr/bin/env python3
"""
Base Node for LangGraph Integration
==================================

Abstract base class for all LangGraph nodes in Vitruvyan system.
Provides common functionality and interface for node implementations.

Author: Vitruvyan Development Team
Created: 2025-01-15
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseNode(ABC):
    """
    Abstract base class for LangGraph nodes
    """
    
    def __init__(self, node_name: str):
        self.node_name = node_name
        self.created_at = datetime.utcnow()
        logger.info(f"🔗 {self.node_name} node initialized")
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the state and return updated state
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state dictionary
        """
        pass
    
    def log_processing(self, state: Dict[str, Any], message: str) -> None:
        """Log processing information"""
        correlation_id = state.get("correlation_id", "unknown")
        logger.info(f"📊 [{self.node_name}] {message} - correlation: {correlation_id}")
    
    async def cleanup(self):
        """Cleanup resources (override if needed)"""
        pass