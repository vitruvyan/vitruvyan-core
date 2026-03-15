# domains/enterprise/babel_gardens/enterprise_context.py
"""
Enterprise Context Detector — Babel Gardens Domain Pack

Re-exports from pattern_weavers pack (shared context detection).
Same pattern as finance domain (shared financial_context.py).
"""

from ..pattern_weavers.enterprise_context import EnterpriseContextDetector

__all__ = ["EnterpriseContextDetector"]
