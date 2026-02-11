"""
MCP Core - Pure domain logic (NO I/O, testable standalone).

Gateway-optimized structure for MCP Server:
- models.py: Frozen dataclasses (validation results, status envelopes)
- validation.py: Pure validation functions (config-driven, domain-agnostic)
- transforms.py: Generic data transformations (entity → factor mappings)
"""

from .models import ValidationResult, ValidationStatus, FactorScore
from .validation import validate_factor_scores, validate_composite_score, validate_summary_length
from .transforms import extract_factors, transform_screen_response, transform_sentiment_response

__all__ = [
    # Models
    "ValidationResult",
    "ValidationStatus",
    "FactorScore",
    # Validation
    "validate_factor_scores",
    "validate_composite_score",
    "validate_summary_length",
    # Transforms
    "extract_factors",
    "transform_screen_response",
    "transform_sentiment_response",
]
