"""
Vitruvyan Cognitive Bus — Plasticity System
============================================

Governed learning with bounded, auditable, reversible parameter adjustments.

Modules:
--------
- outcome_tracker: Links decisions to outcomes for learning feedback
- manager: Governs parameter adjustments with bounds enforcement
- learning_loop: Periodic analysis and adaptation

Philosophy:
-----------
"A system that cannot learn is brittle. 
 A system that learns without governance is dangerous. 
 We build the middle path."

Version: 1.0.0
Date: January 24, 2026
"""

from core.cognitive_bus.plasticity.outcome_tracker import (
    Outcome,
    OutcomeTracker
)
from core.cognitive_bus.plasticity.manager import (
    ParameterBounds,
    Adjustment,
    PlasticityManager
)
from core.cognitive_bus.plasticity.learning_loop import (
    PlasticityLearningLoop
)

__all__ = [
    "Outcome",
    "OutcomeTracker",
    "ParameterBounds",
    "Adjustment",
    "PlasticityManager",
    "PlasticityLearningLoop"
]

__version__ = "1.0.0"
