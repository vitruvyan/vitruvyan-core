"""
Orthodoxy Wardens — Consumers (Decision Engines)

Abstract base class and future concrete role implementations.
Each consumer is a SacredRole that renders judgments without side effects.
"""

from .base import SacredRole

__all__ = [
    "SacredRole",
]
