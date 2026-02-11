"""
MCP Core Validation - Pure validation logic (config-driven, domain-agnostic).

ZERO I/O: All functions are testable standalone without Redis/PostgreSQL/Docker.
Thresholds come from config (ValidationConfig), not hardcoded.
"""

import logging
from typing import Dict, Any, Optional

from .models import ValidationStatus, ValidationResult, FactorScore

logger = logging.getLogger(__name__)


def validate_factor_scores(
    factors: Dict[str, float],
    z_threshold: float,
    entity_id: Optional[str] = None
) -> ValidationResult:
    """
    Validate normalized factor scores (domain-agnostic).
    
    Args:
        factors: Dict of {factor_name: normalized_value} (e.g., {"momentum": 2.5, "trend": -1.3})
        z_threshold: Max absolute z-score (e.g., 3.0 = 99.7% confidence interval)
        entity_id: Optional entity identifier (for logging)
    
    Returns:
        ValidationResult with status, warnings, outlier_factors
    
    Examples:
        >>> validate_factor_scores({"momentum": 2.1, "trend": 1.5}, z_threshold=3.0)
        ValidationResult(status=BLESSED, warnings=[], outlier_factors=[])
        
        >>> validate_factor_scores({"momentum": 4.5, "trend": -0.5}, z_threshold=3.0)
        ValidationResult(status=PURIFIED, warnings=["Outlier: momentum=4.500"], outlier_factors=["momentum"])
    """
    warnings = []
    outlier_factors = []
    status = ValidationStatus.BLESSED
    
    for factor_name, value in factors.items():
        if value is None:
            continue
        
        if abs(value) > z_threshold:
            outlier_factors.append(factor_name)
            msg = f"Outlier: {factor_name}={value:.3f} (threshold=±{z_threshold})"
            if entity_id:
                msg += f" for {entity_id}"
            warnings.append(msg)
            logger.warning(f"⚠️ {msg}")
            
            if status == ValidationStatus.BLESSED:
                status = ValidationStatus.PURIFIED
    
    return ValidationResult(
        status=status,
        warnings=warnings,
        outlier_factors=outlier_factors
    )


def validate_composite_score(
    composite: float,
    composite_threshold: float,
    entity_id: Optional[str] = None
) -> ValidationResult:
    """
    Validate composite/aggregate score (domain-agnostic).
    
    Args:
        composite: Aggregate score (weighted sum, normalized, etc.)
        composite_threshold: Max absolute value (e.g., 5.0)
        entity_id: Optional entity identifier
    
    Returns:
        ValidationResult with status, warnings
    
    Examples:
        >>> validate_composite_score(3.2, composite_threshold=5.0)
        ValidationResult(status=BLESSED, warnings=[], outlier_factors=[])
        
        >>> validate_composite_score(6.8, composite_threshold=5.0)
        ValidationResult(status=PURIFIED, warnings=["Extreme composite=6.800"], ...)
    """
    warnings = []
    status = ValidationStatus.BLESSED
    
    if abs(composite) > composite_threshold:
        msg = f"Extreme composite={composite:.3f} (threshold=±{composite_threshold})"
        if entity_id:
            msg += f" for {entity_id}"
        warnings.append(msg)
        logger.warning(f"⚠️ {msg}")
        status = ValidationStatus.PURIFIED
    
    return ValidationResult(
        status=status,
        warnings=warnings,
        outlier_factors=[],
        composite_score=composite
    )


def validate_summary_length(
    word_count: int,
    min_words: int,
    max_words: int,
    summary_id: Optional[str] = None
) -> ValidationResult:
    """
    Validate text summary length (generic, not VEE-specific).
    
    Args:
        word_count: Number of words in summary
        min_words: Minimum threshold (e.g., 100)
        max_words: Maximum threshold (e.g., 200)
        summary_id: Optional identifier
    
    Returns:
        ValidationResult with status, warnings
    
    Examples:
        >>> validate_summary_length(150, min_words=100, max_words=200)
        ValidationResult(status=BLESSED, warnings=[], outlier_factors=[])
        
        >>> validate_summary_length(50, min_words=100, max_words=200)
        ValidationResult(status=PURIFIED, warnings=["Summary length 50 out of range"], ...)
    """
    warnings = []
    status = ValidationStatus.BLESSED
    
    if word_count < min_words or word_count > max_words:
        msg = f"Summary length {word_count} out of range ({min_words}-{max_words})"
        if summary_id:
            msg += f" for {summary_id}"
        warnings.append(msg)
        logger.warning(f"⚠️ {msg}")
        status = ValidationStatus.PURIFIED
    
    return ValidationResult(
        status=status,
        warnings=warnings,
        outlier_factors=[]
    )


def aggregate_validation_results(results: list[ValidationResult]) -> ValidationResult:
    """
    Aggregate multiple validation results into single status.
    
    Logic: BLESSED only if all BLESSED, HERETICAL if any HERETICAL, else PURIFIED.
    
    Args:
        results: List of ValidationResult objects
    
    Returns:
        Aggregated ValidationResult
    """
    if not results:
        return ValidationResult(status=ValidationStatus.BLESSED, warnings=[], outlier_factors=[])
    
    # Aggregate status (worst wins)
    if any(r.status == ValidationStatus.HERETICAL for r in results):
        final_status = ValidationStatus.HERETICAL
    elif any(r.status == ValidationStatus.PURIFIED for r in results):
        final_status = ValidationStatus.PURIFIED
    else:
        final_status = ValidationStatus.BLESSED
    
    # Combine warnings and outliers
    all_warnings = []
    all_outliers = []
    for r in results:
        all_warnings.extend(r.warnings)
        all_outliers.extend(r.outlier_factors)
    
    return ValidationResult(
        status=final_status,
        warnings=all_warnings,
        outlier_factors=list(set(all_outliers))  # deduplicate
    )
