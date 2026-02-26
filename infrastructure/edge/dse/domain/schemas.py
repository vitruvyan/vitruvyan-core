"""
DSE Domain Schemas — Frozen Dataclasses
========================================

Core contracts for Design Space Exploration.
Immutable DTOs — zero I/O, zero Pydantic, zero infrastructure.

Key Design Decisions:
1. DesignPoint is KNOB-READY (parametric space), NOT semantic concepts.
2. All KPIs normalized to [0,1] range (DSE engine responsibility).
3. Schemas are VERSIONABLE (input_hash + schema_version).
4. Immutable after creation (audit trail guarantee).

Last updated: Feb 26, 2026
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class OptimizationDirection(str, Enum):
    """KPI optimization direction."""
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


# ---------------------------------------------------------------------------
# Value objects (frozen dataclasses — immutable DTOs)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KPIConfig:
    """Normalization config for a single KPI."""
    kpi_name: str
    min_value: float
    max_value: float
    direction: OptimizationDirection
    weight: float = 1.0

    def __post_init__(self) -> None:
        if self.max_value <= self.min_value:
            raise ValueError(
                f"KPIConfig '{self.kpi_name}': max_value must be > min_value"
            )
        if not (0.0 <= self.weight <= 1.0):
            raise ValueError(
                f"KPIConfig '{self.kpi_name}': weight must be in [0, 1]"
            )


@dataclass(frozen=True)
class ConstraintConfig:
    """A hard constraint definition (budget, time-to-deploy, etc.)."""
    constraint_type: str
    value: Union[float, int, str]
    operator: str  # "<=", ">=", "==", "!="


@dataclass(frozen=True)
class RunContext:
    """Run metadata linking DSE execution to orchestration context."""
    user_id: str
    trace_id: str
    use_case: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DesignPoint:
    """
    A single configuration point in the exploration space.

    CRITICAL: knobs are PARAMETERS (continuous/discrete variables),
    NOT semantic concepts. Concepts belong in tags.
    """
    design_id: int
    knobs: Dict[str, Union[float, int, str]]
    constraints: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.knobs:
            raise ValueError(f"DesignPoint #{self.design_id}: knobs cannot be empty")


@dataclass(frozen=True)
class NormalizationProfile:
    """Normalization config for all KPIs in a DSE run."""
    profile_name: str
    kpi_configs: List[KPIConfig]
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not self.kpi_configs:
            raise ValueError("NormalizationProfile: kpi_configs cannot be empty")


@dataclass(frozen=True)
class PolicySet:
    """Decision policy configuration for a DSE run."""
    policy_name: str
    optimization_objective: str
    doctrine_weights: Dict[str, float]
    constraints: List[ConstraintConfig] = field(default_factory=list)
    schema_version: str = "1.0.0"


@dataclass(frozen=True)
class RunArtifact:
    """Complete output of a DSE run (immutable audit record)."""
    run_context: RunContext
    policy_set: PolicySet
    normalization_profile: NormalizationProfile
    pareto_frontier: List[Dict[str, Any]]
    ranking_dottrinale: List[Dict[str, Any]]
    input_hash: str
    seed: int
    schema_version: str
    asof: datetime
    total_design_points: int
    pareto_count: int


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def compute_input_hash(
    design_points: List[DesignPoint],
    policy_set: PolicySet,
    normalization_profile: NormalizationProfile,
) -> str:
    """
    Deterministic SHA-256 hash of the run inputs.
    Guarantees reproducibility and tamper-detection in audit trail.
    """
    payload = {
        "design_points": [
            {"design_id": dp.design_id, "knobs": dp.knobs} for dp in design_points
        ],
        "policy_name": policy_set.policy_name,
        "kpi_names": [k.kpi_name for k in normalization_profile.kpi_configs],
    }
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()
