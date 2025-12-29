#!/usr/bin/env python3
"""
Base Hunter - Foundation Class for Codex Hunters
===============================================

Abstract base class for all Codex Hunter agents.
Provides common functionality for data integrity agents.

Author: Vitruvyan Development Team  
Created: 2025-01-15
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CodexEvent:
    """Event data structure for Codex operations"""
    event_type: str
    source: str
    target: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class BaseHunter(ABC):
    """
    Abstract base class for all Codex Hunter agents
    """
    
    def __init__(self, agent_name: str):
        self.name = agent_name
        self.created_at = datetime.utcnow()
        
        # Redis connection for event publishing
        try:
            from core.foundation.cognitive_bus.redis_client import get_redis_bus
            self.redis_bus = get_redis_bus()
        except ImportError:
            logger.warning(f"⚠️ Redis not available for {self.name}")
            self.redis_bus = None
        
        logger.info(f"🗝️ {self.name} Hunter initialized")
    
    def publish_event(self, event_type: str, payload: Dict[str, Any], 
                     target: str = None, severity: str = "info") -> bool:
        """
        Publish event via Redis Cognitive Bus
        
        Args:
            event_type: Type of event (e.g., "codex.audit.ready")
            payload: Event payload data
            target: Target service (e.g., "audit_engine")
            severity: Event severity level
            
        Returns:
            bool: True if published successfully
        """
        try:
            if not self.redis_bus:
                logger.warning(f"⚠️ Redis not available - logging event: {event_type}")
                return False
            
            success = self.redis_bus.publish_codex_event(
                domain="codex",
                intent=event_type.replace("codex.", ""),
                emitter=self.name.lower(),
                target=target or "system",
                payload=payload
            )
            
            if success:
                logger.info(f"📡 {self.name}: Published {event_type} event")
            else:
                logger.error(f"❌ {self.name}: Failed to publish {event_type}")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ {self.name}: Event publishing failed: {e}")
            return False
    
    async def emit_event(self, event: CodexEvent) -> None:
        """
        Emit CodexEvent (alternative interface)
        
        Args:
            event: CodexEvent instance to emit
        """
        self.publish_event(
            event_type=event.event_type,
            payload=event.data or {},
            target=event.target,
            severity="info"
        )
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the hunter's main functionality
        
        Returns:
            Results dictionary
        """
        pass
    
    def activate(self) -> None:
        """Activate the hunter (synchronous version)"""
        logger.info(f"🎯 {self.name} Hunter activated")
    
    async def async_activate(self) -> None:
        """Activate the hunter (async version)"""
        self.activate()