"""
Babel Gardens → Neural Engine Adapter (Phase 3)
================================================

Translates SignalExtractionResult outputs from Babel Gardens v2.1
into Neural Engine feature dictionaries.

This adapter enables any vertical (finance, cybersecurity, healthcare, legal, etc.)
to feed signals into the Neural Engine for ranking/scoring.

Architecture:
- LIVELLO 2 (Service layer) - bridges two Sacred Orders
- Consumes: SignalExtractionResult (from Babel Gardens)
- Produces: Features dict (for Neural Engine IDataProvider)

Sacred Orders Integration:
- Babel Gardens: Outputs signals (sentiment_valence, threat_severity, etc.)
- Neural Engine: Consumes features (generic key-value dict)
- This adapter: Translates signals → features

Example:
    # Babel Gardens extracts signals
    results = plugin.extract_signals(text="Fed signals rate hike", config=finance_config)
    
    # Adapter converts to Neural Engine features
    features = SignalToFeatureAdapter.convert(results)
    # {"sentiment_valence": 0.6, "market_fear_index": 0.35, ...}
    
    # Neural Engine uses features for ranking
    engine_results = neural_engine.run(features=features, profile="aggressive")
"""

from typing import Dict, List, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass
import logging

# Avoid runtime import of Babel Gardens to prevent numpy dependency
# Use TYPE_CHECKING for type annotations only
if TYPE_CHECKING:
    from core.cognitive.babel_gardens.domain.signal_schema import (
        SignalExtractionResult,
        SignalConfig,
    )

logger = logging.getLogger(__name__)


@dataclass
class FeatureMetadata:
    """Metadata about converted features for provenance tracking."""
    source: str = "babel_gardens"  # Sacred Order source
    timestamp: str = ""
    extraction_methods: Dict[str, str] = None  # signal_name → method
    confidence_scores: Dict[str, float] = None  # signal_name → confidence
    
    def __post_init__(self):
        if self.extraction_methods is None:
            self.extraction_methods = {}
        if self.confidence_scores is None:
            self.confidence_scores = {}


class SignalToFeatureAdapter:
    """
    Adapter that converts Babel Gardens signals to Neural Engine features.
    
    Conversion Strategy:
    1. Signal name → feature name (1:1 mapping)
    2. Signal value → feature value (normalized to signal's range)
    3. Enrichment: Adds confidence scores as separate features (optional)
    
    Backward Compatibility:
    - Finance legacy: Converts sentiment_valence → sentiment/sentiment_score
    - Maintains explainability traces for Orthodoxy Wardens
    
    Usage:
        adapter = SignalToFeatureAdapter()
        features, metadata = adapter.convert(signal_results)
        
        # Use in Neural Engine
        neural_engine.run(entity_features=features, profile="aggressive")
    """
    
    def __init__(
        self,
        include_confidence_features: bool = True,
        legacy_sentiment_mapping: bool = False,
    ):
        """
        Initialize adapter.
        
        Args:
            include_confidence_features: Add "_confidence" features for each signal
            legacy_sentiment_mapping: Map sentiment_valence → sentiment/sentiment_score (backward compat)
        """
        self.include_confidence_features = include_confidence_features
        self.legacy_sentiment_mapping = legacy_sentiment_mapping
        
        logger.info(
            f"SignalToFeatureAdapter initialized "
            f"(confidence_features={include_confidence_features}, "
            f"legacy_sentiment={legacy_sentiment_mapping})"
        )
    
    def convert(
        self,
        signal_results: List[Any],  # List[SignalExtractionResult] - using Any to avoid import
        entity_id: Optional[str] = None,
    ) -> tuple[Dict[str, float], FeatureMetadata]:
        """
        Convert signal extraction results to Neural Engine features.
        
        Args:
            signal_results: List of SignalExtractionResult from Babel Gardens
            entity_id: Optional entity identifier (for logging/tracking)
        
        Returns:
            Tuple of (features_dict, metadata)
        
        Example Output:
            features = {
                "sentiment_valence": 0.6,
                "market_fear_index": 0.35,
                "volatility_perception": 0.72,
                # Optional confidence features
                "sentiment_valence_confidence": 0.88,
                "market_fear_index_confidence": 0.90,
            }
            
            metadata = FeatureMetadata(
                source="babel_gardens",
                timestamp="2026-02-11T14:00:00Z",
                extraction_methods={"sentiment_valence": "model:finbert", ...},
                confidence_scores={"sentiment_valence": 0.88, ...}
            )
        """
        features: Dict[str, float] = {}
        extraction_methods: Dict[str, str] = {}
        confidence_scores: Dict[str, float] = {}
        latest_timestamp = ""
        
        for result in signal_results:
            # Primary feature: signal value
            features[result.signal_name] = result.value
            
            # Track metadata
            extraction_methods[result.signal_name] = result.extraction_trace.get("method", "unknown")
            confidence_scores[result.signal_name] = result.confidence
            
            # Update timestamp (use latest)
            result_timestamp = result.extraction_trace.get("timestamp", "")
            if result_timestamp > latest_timestamp:
                latest_timestamp = result_timestamp
            
            # Optional: Add confidence as separate feature
            if self.include_confidence_features:
                features[f"{result.signal_name}_confidence"] = result.confidence
        
        # Backward compatibility: Legacy sentiment mapping
        if self.legacy_sentiment_mapping and "sentiment_valence" in features:
            valence = features["sentiment_valence"]
            
            # Map valence to legacy sentiment label
            if valence > 0.3:
                sentiment_label = "positive"
            elif valence < -0.3:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
            
            # Add legacy features (for old Neural Engine consumers)
            features["sentiment"] = sentiment_label  # type: ignore (Neural Engine accepts str or float)
            features["sentiment_score"] = abs(valence)  # Always positive [0, 1]
            
            logger.debug(
                f"Legacy sentiment mapping: valence={valence:.3f} → "
                f"sentiment={sentiment_label}, score={abs(valence):.3f}"
            )
        
        # Create metadata
        metadata = FeatureMetadata(
            source="babel_gardens",
            timestamp=latest_timestamp,
            extraction_methods=extraction_methods,
            confidence_scores=confidence_scores,
        )
        
        logger.info(
            f"Converted {len(signal_results)} signals → {len(features)} features "
            f"(entity={entity_id or 'N/A'})"
        )
        
        return features, metadata
    
    def convert_batch(
        self,
        entity_signals: Dict[str, List[Any]],  # Dict[str, List[SignalExtractionResult]] - using Any
    ) -> Dict[str, Dict[str, float]]:
        """
        Convert signals for multiple entities (batch processing).
        
        Args:
            entity_signals: Map of entity_id → List[SignalExtractionResult]
        
        Returns:
            Map of entity_id → features_dict
        
        Example:
            entity_signals = {
                "AAPL": [sentiment_result, fear_result],
                "MSFT": [sentiment_result, fear_result],
            }
            
            features = adapter.convert_batch(entity_signals)
            # {"AAPL": {"sentiment_valence": 0.6, ...}, "MSFT": {...}}
        """
        batch_features = {}
        
        for entity_id, signal_results in entity_signals.items():
            features, metadata = self.convert(signal_results, entity_id=entity_id)
            batch_features[entity_id] = features
        
        logger.info(f"Batch converted {len(entity_signals)} entities")
        
        return batch_features
    
    @staticmethod
    def validate_features(
        features: Dict[str, float],
        required_features: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Validate that features dict has required keys and valid values.
        
        Args:
            features: Features dict to validate
            required_features: List of feature names that must be present
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required features present
        if required_features:
            missing = set(required_features) - set(features.keys())
            if missing:
                errors.append(f"Missing required features: {missing}")
        
        # Check all values are numeric
        for name, value in features.items():
            if not isinstance(value, (int, float)):
                errors.append(f"Feature '{name}' has non-numeric value: {type(value)}")
        
        return errors


# Convenience function for direct usage
def signals_to_features(
    signal_results: List[Any],  # List[SignalExtractionResult] - using Any to avoid import
    include_confidence: bool = True,
    legacy_sentiment: bool = False,
) -> Dict[str, float]:
    """
    Convert signal results to features dict (simple API).
    
    Example:
        # Extract signals using a domain-specific signals plugin
        signals = plugin.extract_signals(text="...", config=config)
        
        # Convert to features
        features = signals_to_features(signals, legacy_sentiment=True)
        
        # Use in Neural Engine
        neural_engine.run(entity_features={"ENTITY": features})
    """
    adapter = SignalToFeatureAdapter(
        include_confidence_features=include_confidence,
        legacy_sentiment_mapping=legacy_sentiment,
    )
    
    features, _ = adapter.convert(signal_results)
    return features
