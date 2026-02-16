"""
Memory Orders — Health Aggregator

Pure component health aggregation for RAG system.
Pure aggregation logic, NO httpx/I/O.

Sacred Order: Memory & Coherence
Layer: Foundational (LIVELLO 1 — consumers)
"""

from datetime import datetime
from .base import MemoryRole
from ..domain import (
    ComponentHealth,
    SystemHealth,
)


class HealthAggregator(MemoryRole):
    """
    Pure health status aggregation from individual components.
    
    Algorithm:
    1. Collect all component statuses
    2. Determine overall status:
       - ALL healthy → 'healthy'
       - ANY unhealthy → 'critical'
       - ANY degraded (but none unhealthy) → 'degraded'
    3. Aggregate summary metrics (drift, sync_lag, total_points)
    4. Generate timestamp
    
    NO I/O. NO HTTP calls. NO database queries.
    """
    
    def process(self, payload: dict) -> SystemHealth:
        """
        Aggregate component health into system-wide health.
        
        Args:
            payload: Dict with:
                - 'components': tuple[ComponentHealth, ...]
                - 'summary' (optional): dict with additional metrics
        
        Returns:
            SystemHealth with overall status and aggregated metrics
        
        Raises:
            ValueError: If payload is invalid or missing required keys
        """
        if not isinstance(payload, dict):
            raise ValueError(f"Expected dict, got {type(payload)}")
        
        if "components" not in payload:
            raise ValueError("Payload missing required key 'components'")
        
        components = payload["components"]
        
        if not isinstance(components, tuple):
            raise ValueError(f"'components' must be tuple, got {type(components)}")
        
        if not all(isinstance(c, ComponentHealth) for c in components):
            raise ValueError("All components must be ComponentHealth objects")
        
        # Extract component statuses
        statuses = [c.status for c in components]
        
        # Determine overall status (priority: unhealthy > degraded > healthy)
        if "unhealthy" in statuses:
            overall_status = "critical"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        # Extract summary metrics (if provided)
        summary_dict = payload.get("summary", {})
        summary_tuple = tuple(summary_dict.items()) if isinstance(summary_dict, dict) else summary_dict
        
        # Generate timestamp
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Return frozen health report
        return SystemHealth(
            overall_status=overall_status,
            components=components,
            summary=summary_tuple,
            timestamp=timestamp,
        )
    
    def can_handle(self, payload: dict) -> bool:
        """Check if payload has required 'components' key."""
        return isinstance(payload, dict) and "components" in payload
