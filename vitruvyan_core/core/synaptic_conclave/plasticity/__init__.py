"""
Vitruvyan Cognitive Bus — Plasticity System
============================================

Governed learning with bounded, auditable, reversible parameter adjustments.

Modules:
--------
- outcome_tracker: Links decisions to outcomes for learning feedback
- manager: Governs parameter adjustments with bounds enforcement
- learning_loop: Periodic analysis and adaptation
- metrics: Prometheus metrics for observability

Philosophy:
-----------
"A system that cannot learn is brittle. 
 A system that learns without governance is dangerous. 
 We build the middle path."

Version: 1.0.0
Date: January 24, 2026
"""

from vitruvyan_core.core.synaptic_conclave.plasticity.outcome_tracker import (
    Outcome,
    OutcomeTracker
)
from vitruvyan_core.core.synaptic_conclave.plasticity.manager import (
    ParameterBounds,
    Adjustment,
    PlasticityManager
)
from vitruvyan_core.core.synaptic_conclave.plasticity.learning_loop import (
    PlasticityLearningLoop
)
from vitruvyan_core.core.synaptic_conclave.plasticity.observer import (
    PlasticityObserver,
    AnomalyType,
    LearningHealth,
    AnomalyReport,
    LearningHealthReport
)

# Metrics module (for optional Prometheus integration)
from vitruvyan_core.core.synaptic_conclave.plasticity import metrics

__all__ = [
    "Outcome",
    "OutcomeTracker",
    "ParameterBounds",
    "Adjustment",
    "PlasticityManager",
    "PlasticityLearningLoop",
    "PlasticityObserver",
    "AnomalyType",
    "LearningHealth",
    "AnomalyReport",
    "LearningHealthReport",
    "metrics"
]

__version__ = "1.0.0"
