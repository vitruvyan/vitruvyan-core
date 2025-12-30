"""
Vitruvyan Core Verticals

Domain-specific implementations that incarnate the core through provider injection.
Each vertical provides:
- Domain factors (AbstractFactor implementations)
- Provider implementations (Aggregation, Risk, Explainability)
- Business logic and domain semantics
- Vertical-specific orchestration

Available Verticals:
- mercator: Financial analysis and portfolio management
- aegis: Defense and logistics operational risk assessment
"""

from .mercator import MercatorVertical

__all__ = ['MercatorVertical']