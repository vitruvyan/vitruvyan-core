"""
MCP Core Transforms - Domain-agnostic data transformations.

Extract, normalize, and map external API responses to generic factor representations.
ZERO domain assumptions: no finance-specific field names.
"""

import logging
from typing import Dict, Any, List, Optional

from .models import FactorScore

logger = logging.getLogger(__name__)


def extract_factors(
    entity_data: Dict[str, Any],
    factor_keys: List[str],
    factor_prefix: str = "z_scores"
) -> List[FactorScore]:
    """
    Extract generic factor scores from entity data (domain-agnostic).
    
    Args:
        entity_data: Raw entity dict from external API
        factor_keys: List of factor names to extract (e.g., ["momentum", "trend", "volatility"])
        factor_prefix: Nested key path to factor dict (default: "z_scores")
    
    Returns:
        List of FactorScore objects
    
    Examples:
        >>> data = {"entity_id": "AAPL", "z_scores": {"momentum": 2.1, "trend": -0.5}}
        >>> extract_factors(data, ["momentum", "trend"])
        [FactorScore(factor_name="momentum", normalized_value=2.1), ...]
        
        >>> data = {"id": "doc_123", "semantic_scores": {"relevance": 0.85, "quality": 0.92}}
        >>> extract_factors(data, ["relevance", "quality"], factor_prefix="semantic_scores")
        [FactorScore(factor_name="relevance", normalized_value=0.85), ...]
    """
    factors = []
    factor_data = entity_data.get(factor_prefix, {})
    
    for key in factor_keys:
        value = factor_data.get(key)
        if value is not None:
            factors.append(FactorScore(
                factor_name=key,
                normalized_value=value,
                metadata={"entity_id": entity_data.get("entity_id") or entity_data.get("id")}
            ))
    
    return factors


def transform_screen_response(
    raw_response: Dict[str, Any],
    factor_keys: List[str]
) -> Dict[str, Any]:
    """
    Transform external screening API response to generic structure (domain-agnostic).
    
    Replaces finance-specific mappings:
    - OLD: momentum_z, trend_z, volatility_z, sentiment_z, fundamental_z
    - NEW: generic factor_keys from config (e.g., ["factor_1", "factor_2", ...])
    
    Args:
        raw_response: Raw response from Neural Engine / external API
        factor_keys: Config-driven factor names (deployment-specific taxonomy)
    
    Returns:
        Normalized response dict with generic "factors" key
    
    Examples:
        >>> response = {"data": {"entity_ids": [{"entity_id": "AAPL", "z_scores": {"momentum": 1.5}}]}}
        >>> transform_screen_response(response, ["momentum"])
        {"data": {"entities": [{"id": "AAPL", "factors": [FactorScore(...)]}]}}
    """
    transformed = {
        "data": {
            "entities": []
        }
    }
    
    for entity_data in raw_response.get("data", {}).get("entity_ids", []):
        # Extract generic factors (no finance assumptions)
        factors = extract_factors(entity_data, factor_keys)
        
        transformed["data"]["entities"].append({
            "id": entity_data.get("entity_id"),
            "factors": [
                {
                    "name": f.factor_name,
                    "value": f.normalized_value
                }
                for f in factors
            ],
            "composite_score": entity_data.get("composite_score"),
            "metadata": entity_data.get("metadata", {})
        })
    
    return transformed


def transform_sentiment_response(
    raw_response: Dict[str, Any],
    entity_id: str
) -> Dict[str, Any]:
    """
    Transform sentiment API response to generic structure (domain-agnostic).
    
    Removes finance-specific assumptions (sentiment_scores table structure).
    
    Args:
        raw_response: Raw response from Sentiment API / database query
        entity_id: Entity identifier
    
    Returns:
        Normalized sentiment dict with generic "signals" key
    
    Examples:
        >>> response = {"sentiment": 0.65, "source": "news", "timestamp": "2026-02-11T10:00:00Z"}
        >>> transform_sentiment_response(response, "AAPL")
        {"entity_id": "AAPL", "signals": [{"type": "sentiment", "value": 0.65, ...}]}
    """
    signals = []
    
    # Generic sentiment signal extraction (config-driven in production)
    if "sentiment" in raw_response:
        signals.append({
            "type": "sentiment",
            "value": raw_response["sentiment"],
            "source": raw_response.get("source", "unknown"),
            "timestamp": raw_response.get("timestamp")
        })
    
    # Support multiple signal types (extensible)
    for signal_type in ["momentum", "trend", "volatility", "quality", "relevance"]:
        if signal_type in raw_response:
            signals.append({
                "type": signal_type,
                "value": raw_response[signal_type],
                "source": raw_response.get("source", "unknown")
            })
    
    return {
        "entity_id": entity_id,
        "signals": signals,
        "metadata": raw_response.get("metadata", {})
    }


def map_legacy_factors(factor_mapping: Dict[str, str], legacy_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map legacy finance-specific field names to generic factor names (backwards compatibility).
    
    Args:
        factor_mapping: Dict of {legacy_name: generic_name}
            e.g., {"momentum_z": "factor_1", "trend_z": "factor_2"}
        legacy_data: Data with finance-specific keys
    
    Returns:
        Data with generic keys
    
    Examples:
        >>> mapping = {"momentum_z": "factor_1", "trend_z": "factor_2"}
        >>> legacy = {"momentum_z": 2.1, "trend_z": -0.5}
        >>> map_legacy_factors(mapping, legacy)
        {"factor_1": 2.1, "factor_2": -0.5}
    """
    transformed = {}
    
    for legacy_key, generic_key in factor_mapping.items():
        if legacy_key in legacy_data:
            transformed[generic_key] = legacy_data[legacy_key]
    
    # Preserve unmapped keys (pass-through)
    for key, value in legacy_data.items():
        if key not in factor_mapping:
            transformed[key] = value
    
    return transformed
