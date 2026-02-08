#!/usr/bin/env python3
"""
ConsumerRegistry — Tentacle Catalog
====================================

Central registry of all consumers in the Vitruvyan system.

Purpose:
- Discovery without coupling
- Health monitoring
- Subscription routing
- Lifecycle management

This is NOT a router or coordinator. The registry is purely
observational — it knows what exists but doesn't direct traffic.
Routing happens via the bus based on event types.

Biological Model: Not the brain, more like the "body awareness" 
that lets the octopus know where its arms are.

Author: Vitruvyan Cognitive Architecture
Date: January 18, 2026
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging
import asyncio
import fnmatch

from .base_consumer import BaseConsumer, ConsumerType, ConsumerConfig

logger = logging.getLogger(__name__)


@dataclass
class ConsumerHealth:
    """Health status of a registered consumer."""
    name: str
    consumer_type: ConsumerType
    running: bool
    last_heartbeat: Optional[datetime] = None
    events_processed: int = 0
    events_emitted: int = 0
    escalations: int = 0
    errors: int = 0
    avg_latency_ms: float = 0.0


class ConsumerRegistry:
    """
    Registry of all consumers in the Vitruvyan system.
    
    Features:
    - Register/unregister consumers
    - Query consumers by name, type, or subscription
    - Health monitoring with heartbeats
    - Subscription pattern matching (wildcards)
    
    The registry is passive — it observes but doesn't control.
    Consumers operate autonomously. The registry just knows they exist.
    """
    
    def __init__(self):
        self._consumers: Dict[str, BaseConsumer] = {}
        self._health: Dict[str, ConsumerHealth] = {}
        self._by_type: Dict[ConsumerType, Set[str]] = {
            ConsumerType.CRITICAL: set(),
            ConsumerType.ADVISORY: set(),
            ConsumerType.AMBIENT: set()
        }
        self._subscriptions: Dict[str, Set[str]] = {}  # pattern -> consumer names
        self._lock = asyncio.Lock()
        
        logger.info("ConsumerRegistry initialized")
    
    # ─────────────────────────────────────────────────────────────
    # Registration
    # ─────────────────────────────────────────────────────────────
    
    async def register(self, consumer: BaseConsumer) -> None:
        """
        Register a consumer with the registry.
        
        This does NOT start the consumer — just records its existence.
        """
        async with self._lock:
            name = consumer.config.name
            
            if name in self._consumers:
                logger.warning(f"Consumer {name} already registered, updating")
            
            self._consumers[name] = consumer
            
            # Track by type
            self._by_type[consumer.config.consumer_type].add(name)
            
            # Track subscriptions
            for pattern in consumer.config.subscriptions:
                if pattern not in self._subscriptions:
                    self._subscriptions[pattern] = set()
                self._subscriptions[pattern].add(name)
            
            # Initialize health tracking
            self._health[name] = ConsumerHealth(
                name=name,
                consumer_type=consumer.config.consumer_type,
                running=consumer._running
            )
            
            logger.info(
                f"Registered consumer: {name} "
                f"[{consumer.config.consumer_type.value}] "
                f"subscriptions={consumer.config.subscriptions}"
            )
    
    async def unregister(self, name: str) -> Optional[BaseConsumer]:
        """
        Unregister a consumer.
        
        Returns the consumer instance if found.
        Does NOT stop the consumer — caller is responsible for lifecycle.
        """
        async with self._lock:
            if name not in self._consumers:
                logger.warning(f"Consumer {name} not found in registry")
                return None
            
            consumer = self._consumers.pop(name)
            
            # Remove from type tracking
            self._by_type[consumer.config.consumer_type].discard(name)
            
            # Remove from subscriptions
            for pattern in consumer.config.subscriptions:
                if pattern in self._subscriptions:
                    self._subscriptions[pattern].discard(name)
                    if not self._subscriptions[pattern]:
                        del self._subscriptions[pattern]
            
            # Remove health tracking
            self._health.pop(name, None)
            
            logger.info(f"Unregistered consumer: {name}")
            return consumer
    
    # ─────────────────────────────────────────────────────────────
    # Queries
    # ─────────────────────────────────────────────────────────────
    
    def get(self, name: str) -> Optional[BaseConsumer]:
        """Get consumer by name."""
        return self._consumers.get(name)
    
    def get_all(self) -> List[BaseConsumer]:
        """Get all registered consumers."""
        return list(self._consumers.values())
    
    def get_by_type(self, consumer_type: ConsumerType) -> List[BaseConsumer]:
        """Get all consumers of a specific type."""
        names = self._by_type.get(consumer_type, set())
        return [self._consumers[n] for n in names if n in self._consumers]
    
    def get_critical(self) -> List[BaseConsumer]:
        """Get all CRITICAL consumers."""
        return self.get_by_type(ConsumerType.CRITICAL)
    
    def get_advisory(self) -> List[BaseConsumer]:
        """Get all ADVISORY consumers."""
        return self.get_by_type(ConsumerType.ADVISORY)
    
    def get_ambient(self) -> List[BaseConsumer]:
        """Get all AMBIENT consumers."""
        return self.get_by_type(ConsumerType.AMBIENT)
    
    def get_subscribers(self, event_type: str) -> List[str]:
        """
        Get all consumer names subscribed to an event type.
        
        Supports wildcard matching:
        - "analysis.*" matches "analysis.complete", "analysis.started"
        - "*" matches everything
        - Exact matches always included
        """
        result = set()
        
        for pattern, consumers in self._subscriptions.items():
            if self._matches(pattern, event_type):
                result.update(consumers)
        
        return list(result)
    
    def _matches(self, pattern: str, event_type: str) -> bool:
        """Match event type against subscription pattern."""
        # Exact match
        if pattern == event_type:
            return True
        
        # Global wildcard
        if pattern == "*":
            return True
        
        # Prefix wildcard (analysis.* matches analysis.complete)
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return event_type.startswith(prefix + ".")
        
        # fnmatch for complex patterns
        return fnmatch.fnmatch(event_type, pattern)
    
    # ─────────────────────────────────────────────────────────────
    # Health monitoring
    # ─────────────────────────────────────────────────────────────
    
    async def heartbeat(self, name: str) -> None:
        """Record a heartbeat from a consumer."""
        if name in self._health:
            self._health[name].last_heartbeat = datetime.utcnow()
            self._health[name].running = True
    
    async def record_event_processed(self, name: str, latency_ms: float) -> None:
        """Record that a consumer processed an event."""
        if name in self._health:
            h = self._health[name]
            h.events_processed += 1
            # Rolling average
            h.avg_latency_ms = (
                h.avg_latency_ms * (h.events_processed - 1) + latency_ms
            ) / h.events_processed
    
    async def record_event_emitted(self, name: str) -> None:
        """Record that a consumer emitted an event."""
        if name in self._health:
            self._health[name].events_emitted += 1
    
    async def record_escalation(self, name: str) -> None:
        """Record that a consumer escalated."""
        if name in self._health:
            self._health[name].escalations += 1
    
    async def record_error(self, name: str) -> None:
        """Record that a consumer had an error."""
        if name in self._health:
            self._health[name].errors += 1
    
    def health_check(self) -> Dict[str, ConsumerHealth]:
        """Get health status of all consumers."""
        # Update running status from actual consumers
        for name, consumer in self._consumers.items():
            if name in self._health:
                self._health[name].running = consumer._running
        
        return self._health.copy()
    
    def summary(self) -> Dict[str, Any]:
        """Get summary statistics of the registry."""
        health = self.health_check()
        
        running = sum(1 for h in health.values() if h.running)
        total_processed = sum(h.events_processed for h in health.values())
        total_emitted = sum(h.events_emitted for h in health.values())
        total_escalations = sum(h.escalations for h in health.values())
        total_errors = sum(h.errors for h in health.values())
        
        return {
            "total_consumers": len(self._consumers),
            "by_type": {
                "critical": len(self._by_type[ConsumerType.CRITICAL]),
                "advisory": len(self._by_type[ConsumerType.ADVISORY]),
                "ambient": len(self._by_type[ConsumerType.AMBIENT])
            },
            "running": running,
            "stopped": len(self._consumers) - running,
            "subscriptions": len(self._subscriptions),
            "total_events_processed": total_processed,
            "total_events_emitted": total_emitted,
            "total_escalations": total_escalations,
            "total_errors": total_errors
        }
    
    # ─────────────────────────────────────────────────────────────
    # Lifecycle helpers
    # ─────────────────────────────────────────────────────────────
    
    async def start_all(self) -> Dict[str, bool]:
        """Start all registered consumers."""
        results = {}
        for name, consumer in self._consumers.items():
            try:
                await consumer.start()
                results[name] = True
            except Exception as e:
                logger.error(f"Failed to start {name}: {e}")
                results[name] = False
        return results
    
    async def stop_all(self) -> Dict[str, bool]:
        """Stop all registered consumers."""
        results = {}
        for name, consumer in self._consumers.items():
            try:
                await consumer.stop()
                results[name] = True
            except Exception as e:
                logger.error(f"Failed to stop {name}: {e}")
                results[name] = False
        return results
    
    async def start_critical(self) -> Dict[str, bool]:
        """Start only CRITICAL consumers (governance layer)."""
        results = {}
        for consumer in self.get_critical():
            try:
                await consumer.start()
                results[consumer.name] = True
            except Exception as e:
                logger.error(f"Failed to start {consumer.name}: {e}")
                results[consumer.name] = False
        return results
    
    # ─────────────────────────────────────────────────────────────
    # Introspection
    # ─────────────────────────────────────────────────────────────
    
    def __len__(self) -> int:
        return len(self._consumers)
    
    def __contains__(self, name: str) -> bool:
        return name in self._consumers
    
    def __repr__(self) -> str:
        return f"<ConsumerRegistry({len(self)} consumers)>"


# ─────────────────────────────────────────────────────────────
# Global registry singleton
# ─────────────────────────────────────────────────────────────

_global_registry: Optional[ConsumerRegistry] = None


def get_registry() -> ConsumerRegistry:
    """Get or create the global consumer registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ConsumerRegistry()
    return _global_registry


def set_registry(registry: ConsumerRegistry) -> None:
    """Set the global consumer registry (for testing)."""
    global _global_registry
    _global_registry = registry
