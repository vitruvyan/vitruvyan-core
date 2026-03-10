"""
Babel Gardens - Signal Schema Domain Primitives
================================================

Domain-agnostic semantic signal extraction specification.

CRITICAL: This module is LIVELLO 1 (Pure Domain).
- No I/O (no HTTP, no database, no Redis)
- No external dependencies beyond Python stdlib
- Testable in isolation without infrastructure

Philosophy:
    "Signals are inferred, never invented."
    
Babel Gardens does NOT know what a signal means — only how to extract it.
Domain semantics (sentiment, threat, risk) are injected via configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional, Dict, Any, List, Tuple


@dataclass(frozen=True)
class SignalSchema:
    """
    Universal semantic signal definition.
    
    Represents a single extractable signal dimension that can be applied
    to any text domain (finance, cybersecurity, maritime, healthcare, etc.)
    
    Examples:
        Finance:
            SignalSchema(
                name="sentiment_valence",
                value_range=(-1.0, 1.0),
                aggregation_method="weighted",
                extraction_method="model:sentiment_v2"
            )
        
        Cybersecurity:
            SignalSchema(
                name="threat_severity",
                value_range=(0.0, 1.0),
                aggregation_method="max",
                extraction_method="model:secbert"
            )
        
        Maritime:
            SignalSchema(
                name="delay_severity",
                value_range=(0, 10),  # days
                aggregation_method="max",
                extraction_method="heuristic:temporal_extraction"
            )
    
    Attributes:
        name: Unique signal identifier (snake_case)
        value_range: Valid min/max values for signal output
        aggregation_method: How to combine multiple signal instances
        fusion_weight: Weight for multi-signal synthesis (0.0 to 1.0)
        explainability_required: Must trace extraction method/model
        extraction_method: How signal is computed (model:name or heuristic:name)
        description: Human-readable signal purpose
    """
    
    name: str
    value_range: Tuple[float, float]
    aggregation_method: Literal["mean", "max", "min", "weighted", "sum"]
    fusion_weight: float = 1.0
    explainability_required: bool = True
    extraction_method: str = ""
    description: str = ""
    
    def __post_init__(self):
        """Validate signal schema invariants."""
        # Validate name
        if not self.name or not self.name.replace("_", "").isalnum():
            raise ValueError(f"Signal name must be alphanumeric with underscores: {self.name}")
        
        # Validate range
        if len(self.value_range) != 2:
            raise ValueError(f"value_range must be (min, max): {self.value_range}")
        
        min_val, max_val = self.value_range
        if min_val >= max_val:
            raise ValueError(f"value_range min must be < max: {self.value_range}")
        
        # Validate fusion weight
        if not (0.0 <= self.fusion_weight <= 1.0):
            raise ValueError(f"fusion_weight must be in [0, 1]: {self.fusion_weight}")
    
    def normalize_value(self, raw_value: float) -> float:
        """
        Normalize raw value to signal's expected range.
        
        Args:
            raw_value: Raw signal output (may be outside range)
        
        Returns:
            Clamped value within [value_range[0], value_range[1]]
        """
        min_val, max_val = self.value_range
        return max(min_val, min(max_val, raw_value))
    
    def is_valid_value(self, value: float) -> bool:
        """Check if value is within signal's valid range."""
        min_val, max_val = self.value_range
        return min_val <= value <= max_val


@dataclass(frozen=True)
class SignalExtractionResult:
    """
    Output of signal extraction process.
    
    Contains signal value + provenance metadata for explainability.
    Integrates with Orthodoxy Wardens for validation/audit.
    
    Attributes:
        signal_name: Name from SignalSchema
        value: Extracted signal value (normalized to schema range)
        confidence: Model/extraction confidence [0, 1]
        extraction_trace: Provenance metadata (model, method, timestamp)
        metadata: Optional vertical-specific context
    """
    
    signal_name: str
    value: float
    confidence: float
    extraction_trace: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate extraction result invariants."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be in [0, 1]: {self.confidence}")
        
        # Explainability trace must contain minimum required fields
        required_trace_fields = {"method", "timestamp"}
        if not required_trace_fields.issubset(self.extraction_trace.keys()):
            raise ValueError(f"extraction_trace missing required fields: {required_trace_fields}")


@dataclass
class SignalConfig:
    """
    Collection of signal schemas for a vertical.
    
    Loaded from YAML at deploy time. Represents complete signal extraction
    specification for a domain (finance, cybersecurity, etc.)
    
    Attributes:
        signals: List of SignalSchema definitions
        taxonomy_categories: Topic classification labels
        embedding_model: Model name for semantic vectorization
        embedding_dimension: Vector dimensionality
        metadata: Vertical identification/versioning
    """
    
    signals: List[SignalSchema]
    taxonomy_categories: List[str] = field(default_factory=list)
    embedding_model: str = "nomic-ai/nomic-embed-text-v1.5"
    embedding_dimension: int = 768
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_signal(self, name: str) -> Optional[SignalSchema]:
        """Retrieve signal schema by name."""
        return next((s for s in self.signals if s.name == name), None)
    
    def select_signals(self, names: List[str]) -> "SignalConfig":
        """Create subset config with only specified signals."""
        filtered = [s for s in self.signals if s.name in names]
        return SignalConfig(
            signals=filtered,
            taxonomy_categories=self.taxonomy_categories,
            embedding_model=self.embedding_model,
            embedding_dimension=self.embedding_dimension,
            metadata=self.metadata
        )
    
    def validate(self) -> List[str]:
        """
        Validate signal config for conflicts/issues.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check for duplicate signal names
        names = [s.name for s in self.signals]
        duplicates = {n for n in names if names.count(n) > 1}
        if duplicates:
            errors.append(f"Duplicate signal names: {duplicates}")
        
        # Check for taxonomy overlap issues
        if len(self.taxonomy_categories) != len(set(self.taxonomy_categories)):
            errors.append("Duplicate taxonomy categories detected")
        
        # Validate each signal schema
        for signal in self.signals:
            try:
                signal.__post_init__()
            except ValueError as e:
                errors.append(f"Invalid signal '{signal.name}': {e}")
        
        return errors


@dataclass
class MultiSignalFusionConfig:
    """
    Configuration for fusing multiple signals into composite score.
    
    Used for cross-vertical signal synthesis (e.g., geopolitical event
    impacts both market sentiment and maritime route safety).
    
    Attributes:
        signals: Signals to fuse (from potentially different verticals)
        fusion_method: Aggregation strategy
        output_name: Name for fused composite signal
    """
    
    signals: List[SignalSchema]
    fusion_method: Literal["weighted_sum", "max", "mean", "product"]
    output_name: str
    
    def compute_fusion(self, signal_values: Dict[str, float]) -> float:
        """
        Fuse multiple signal values into single composite.
        
        Args:
            signal_values: Map of signal_name -> extracted_value
        
        Returns:
            Fused composite value
        """
        # Filter to signals in this fusion config
        relevant_values = [
            (signal.fusion_weight, signal_values.get(signal.name, 0.0))
            for signal in self.signals
            if signal.name in signal_values
        ]
        
        if not relevant_values:
            return 0.0
        
        if self.fusion_method == "weighted_sum":
            return sum(w * v for w, v in relevant_values) / sum(w for w, _ in relevant_values)
        
        elif self.fusion_method == "max":
            return max(v for _, v in relevant_values)
        
        elif self.fusion_method == "mean":
            return sum(v for _, v in relevant_values) / len(relevant_values)
        
        elif self.fusion_method == "product":
            result = 1.0
            for _, v in relevant_values:
                result *= v
            return result
        
        else:
            raise ValueError(f"Unknown fusion method: {self.fusion_method}")


# ============================================================================
# YAML Config Loading
# ============================================================================

def load_config_from_yaml(signals_path: str, taxonomy_path: Optional[str] = None) -> SignalConfig:
    """
    Load SignalConfig from YAML file.
    
    Parses signal schema definitions from YAML and constructs validated SignalConfig.
    
    Expected YAML structure:
    ```yaml
    signals:
      - name: signal_name
        range: [min, max]
        aggregation_method: mean|max|min|weighted|sum
        fusion_weight: 0.0-1.0
        explainability_required: true|false
        extraction_method: "model:name" or "heuristic:name"
        description: "..."
    
    taxonomy:
      categories: [cat1, cat2, ...]
      embeddings:
        model: "model-name"
        dimension: 768
    
    metadata:
      vertical: "vertical-name"
      version: "2.1.0"
    ```
    
    Args:
        signals_path: Path to signals YAML config
        taxonomy_path: Optional path to taxonomy YAML (currently unused)
    
    Returns:
        Validated SignalConfig instance
    
    Raises:
        FileNotFoundError: Config file not found
        ValueError: Invalid config schema
        ImportError: PyYAML not installed
    """
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML is required for config loading. Install with: pip install pyyaml"
        )
    
    from pathlib import Path
    
    config_path = Path(signals_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {signals_path}")
    
    with config_path.open('r') as f:
        data = yaml.safe_load(f)
    
    # Validate top-level structure
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML structure: expected dict, got {type(data)}")
    
    if "signals" not in data:
        raise ValueError("Missing required 'signals' section in config")
    
    if "taxonomy" not in data:
        raise ValueError("Missing required 'taxonomy' section in config")
    
    # Parse signals
    signals = []
    for signal_data in data["signals"]:
        # Map 'range' to 'value_range' for SignalSchema constructor
        signal_dict = {
            "name": signal_data["name"],
            "value_range": tuple(signal_data["range"]),  # [min, max] → (min, max)
            "aggregation_method": signal_data["aggregation_method"],
            "fusion_weight": signal_data.get("fusion_weight", 1.0),
            "explainability_required": signal_data.get("explainability_required", True),
            "extraction_method": signal_data.get("extraction_method", ""),
            "description": signal_data.get("description", ""),
        }
        signals.append(SignalSchema(**signal_dict))
    
    # Parse taxonomy
    taxonomy = data["taxonomy"]
    taxonomy_categories = taxonomy.get("categories", [])
    
    # Parse embedding model (optional)
    embedding_model = "nomic-ai/nomic-embed-text-v1.5"  # default
    if "embeddings" in taxonomy:
        embedding_model = taxonomy["embeddings"].get("model", embedding_model)
    
    # Parse metadata (optional)
    metadata = data.get("metadata", {})
    
    config = SignalConfig(
        signals=signals,
        taxonomy_categories=taxonomy_categories,
        embedding_model=embedding_model,
        metadata=metadata,
    )
    
    # Validate config
    errors = config.validate()
    if errors:
        raise ValueError(f"Config validation failed: {errors}")
    
    return config


def merge_configs(configs: List[SignalConfig]) -> SignalConfig:
    """
    Merge multiple SignalConfigs for cross-vertical fusion.
    
    Combines signals and taxonomies from multiple verticals while detecting
    duplicate signal names (which is an error condition).
    
    Example: Merge finance + maritime configs for geopolitical event analysis.
    
    Args:
        configs: List of vertical-specific configs to merge
    
    Returns:
        Combined SignalConfig with all signals
    
    Raises:
        ValueError: Conflicting signal names across configs
    """
    if not configs:
        raise ValueError("Cannot merge empty config list")
    
    if len(configs) == 1:
        return configs[0]
    
    # Collect all signals
    all_signals: List[SignalSchema] = []
    signal_names_seen: set[str] = set()
    
    for config in configs:
        for signal in config.signals:
            if signal.name in signal_names_seen:
                raise ValueError(
                    f"Duplicate signal name '{signal.name}' found in merge. "
                    f"Signal names must be unique across configs."
                )
            signal_names_seen.add(signal.name)
            all_signals.append(signal)
    
    # Merge taxonomy categories (union, preserving order)
    all_categories: List[str] = []
    categories_seen: set[str] = set()
    
    for config in configs:
        for cat in config.taxonomy_categories:
            if cat not in categories_seen:
                categories_seen.add(cat)
                all_categories.append(cat)
    
    # Use first config's embedding model (TODO: allow override in future)
    embedding_model = configs[0].embedding_model
    
    # Merge metadata
    merged_metadata = {}
    for config in configs:
        if hasattr(config, "metadata") and config.metadata:
            merged_metadata.update(config.metadata)
    
    merged_metadata["merged_from"] = [
        config.metadata.get("vertical", "unknown") for config in configs
    ]
    
    merged_config = SignalConfig(
        signals=all_signals,
        taxonomy_categories=all_categories,
        embedding_model=embedding_model,
        metadata=merged_metadata,
    )
    
    # Validate merged config
    errors = merged_config.validate()
    if errors:
        raise ValueError(f"Merged config validation failed: {errors}")
    
    return merged_config
