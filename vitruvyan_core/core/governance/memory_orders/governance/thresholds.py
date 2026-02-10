"""
Memory Orders — Coherence Thresholds

Frozen configuration for coherence drift thresholds.
Immutable, versioned, auditable.

Sacred Order: Memory & Coherence
Layer: Foundational (LIVELLO 1 — governance)
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CoherenceThresholds:
    """
    Drift percentage thresholds for coherence status determination.
    
    Attributes:
        healthy: Maximum drift for 'healthy' status (default: 5.0%)
        warning: Minimum drift for 'critical' status (default: 15.0%)
    
    Status mapping:
    - drift < healthy → 'healthy'
    - healthy <= drift < warning → 'warning'
    - drift >= warning → 'critical'
    """
    healthy: float = 5.0
    warning: float = 15.0
    
    def __post_init__(self):
        if self.healthy < 0:
            raise ValueError(f"healthy threshold must be >= 0, got {self.healthy}")
        if self.warning <= self.healthy:
            raise ValueError(f"warning threshold ({self.warning}) must be > healthy threshold ({self.healthy})")
    
    def as_tuple(self) -> tuple[tuple[str, float], ...]:
        """Convert to immutable tuple for domain objects."""
        return (
            ("healthy", self.healthy),
            ("warning", self.warning),
        )


# Default thresholds (can be overridden via config)
DEFAULT_THRESHOLDS = CoherenceThresholds()


# Alternative threshold presets
STRICT_THRESHOLDS = CoherenceThresholds(healthy=2.0, warning=5.0)
RELAXED_THRESHOLDS = CoherenceThresholds(healthy=10.0, warning=25.0)
