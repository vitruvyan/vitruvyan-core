"""
Orthodoxy Wardens — Consumers (Decision Engines)

Concrete SacredRole implementations that form the tribunal pipeline:

  Confessor  → Intake: raw events → Confession
  Inquisitor → Examination: Confession + text/code → Findings
  Penitent   → Correction advisor: Verdict → CorrectionPlan
  Chronicler → Log strategist: Verdict → ChronicleDecision

Each consumer is pure, deterministic, and side-effect free.
"""

from .base import SacredRole
from .confessor import Confessor
from .inquisitor import Inquisitor, InquisitorResult
from .penitent import Penitent, CorrectionRequest, CorrectionPlan
from .chronicler import Chronicler, ArchiveDirective, ChronicleDecision

__all__ = [
    # ABC
    "SacredRole",
    # Concrete roles
    "Confessor",
    "Inquisitor",
    "Penitent",
    "Chronicler",
    # Result types
    "InquisitorResult",
    "CorrectionRequest",
    "CorrectionPlan",
    "ArchiveDirective",
    "ChronicleDecision",
]
