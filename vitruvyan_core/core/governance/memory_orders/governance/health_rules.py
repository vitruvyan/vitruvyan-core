"""
Memory Orders — Health Aggregation Rules

Pure rules for determining overall system health from component statuses.
No I/O, no side effects.

Sacred Order: Memory & Coherence
Layer: Foundational (LIVELLO 1 — governance)
"""

from typing import Sequence


def aggregate_component_statuses(statuses: Sequence[str]) -> str:
    """
    Determine overall system status from component statuses.
    
    Priority: unhealthy > degraded > healthy
    
    Rules:
    - ANY component 'unhealthy' → overall='critical'
    - ANY component 'degraded' (but none unhealthy) → overall='degraded'
    - ALL components 'healthy' → overall='healthy'
    
    Args:
        statuses: Sequence of component status strings
    
    Returns:
        Overall status ('healthy' | 'degraded' | 'critical')
    
    Raises:
        ValueError: If any status is invalid
    """
    VALID_STATUSES = frozenset(["healthy", "degraded", "unhealthy"])
    
    # Validate all statuses
    for status in statuses:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid component status: {status}. Must be one of {VALID_STATUSES}")
    
    # Edge case: no components
    if not statuses:
        return "healthy"  # Default: optimistic
    
    # Priority-based aggregation
    if "unhealthy" in statuses:
        return "critical"
    elif "degraded" in statuses:
        return "degraded"
    else:
        return "healthy"


def calculate_health_score(statuses: Sequence[str]) -> float:
    """
    Calculate numeric health score from component statuses.
    
    Scoring:
    - 'healthy' = 1.0
    - 'degraded' = 0.5
    - 'unhealthy' = 0.0
    
    Overall score = average of all component scores
    
    Args:
        statuses: Sequence of component status strings
    
    Returns:
        Health score between 0.0 and 1.0
    """
    STATUS_SCORES = {
        "healthy": 1.0,
        "degraded": 0.5,
        "unhealthy": 0.0,
    }
    
    if not statuses:
        return 1.0  # Default: perfect health
    
    scores = [STATUS_SCORES.get(s, 0.0) for s in statuses]
    return sum(scores) / len(scores)
