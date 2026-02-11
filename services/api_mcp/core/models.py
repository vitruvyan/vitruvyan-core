"""
MCP Core Models - Frozen dataclasses for MCP domain logic.

Gateway pattern: lightweight, domain-agnostic data structures.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class ValidationStatus(str, Enum):
    """Orthodoxy validation status (Sacred Orders integration)."""
    BLESSED = "blessed"       # No issues detected
    PURIFIED = "purified"     # Passed validation with warnings (outliers normalized)
    HERETICAL = "heretical"   # Failed validation (invariants violated)


@dataclass(frozen=True)
class FactorScore:
    """
    Generic factor score container (domain-agnostic).
    
    Replaces finance-specific fields (momentum_z, trend_z, volatility_z).
    Can represent ANY normalized metric (technical indicators, semantic similarity, risk scores, etc.).
    """
    factor_name: str           # Generic: "momentum" | "trend" | "semantic_relevance" | "quality_score"
    normalized_value: float    # z-score or [0,1] normalized
    raw_value: Optional[float] = None  # Original value before normalization
    metadata: Optional[Dict] = None    # Domain-specific context (e.g., {"time_window": "30d", "source": "vare"})


@dataclass(frozen=True)
class ValidationResult:
    """
    Pure validation result (no I/O, testable standalone).
    
    Used by Orthodoxy Wardens middleware to enforce invariants.
    """
    status: ValidationStatus
    warnings: list[str]                # Human-readable warning messages
    outlier_factors: list[str]         # Factors exceeding thresholds
    composite_score: Optional[float] = None
    metadata: Optional[Dict] = None


@dataclass(frozen=True)
class MCPToolContext:
    """
    Context envelope for Sacred Orders middleware orchestration.
    
    Passed through validation + archiving pipeline.
    """
    conclave_id: str
    user_id: str
    tool_name: str
    args: Dict
    result: Dict
    timestamp: str
