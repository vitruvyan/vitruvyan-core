# Babel Gardens — Sacred Order Charter

## Identity

**Babel Gardens** is Sacred Order #2, the **Tower of Linguistic Unity**.

> "Where all languages converge into divine understanding."

## Epistemic Order

| Order | Domain | Responsibility |
|-------|--------|----------------|
| **Perception** | Ingestion | Acquire + normalize external inputs |

Babel Gardens is the first point of contact for all textual input.
It transforms raw multilingual text into semantic vectors that the rest of the system can process.

## Mandate

1. **Language Identification** — Detect the language of input text
2. **Semantic Vectorization** — Transform text into dense embedding representations
3. **Signal Extraction** — Extract configurable semantic signals via injected schema
4. **Taxonomy Classification** — Categorize text into configurable topic hierarchies
5. **Multi-Model Fusion** — Fuse embeddings and signals across multiple dimensions
6. **Structured Signal Emission** — Output explainable, auditable signal artifacts

## Invariants

### Domain Agnostic

Babel Gardens is **completely domain-agnostic**:

- NO hardcoded signal schemas (use `SignalConfig.from_yaml()`)
- NO hardcoded topic categories (use `TaxonomyConfig.from_yaml()`)
- NO domain-specific embedding models (use `EmbeddingModelConfig`)
- NO vertical terminology in core (finance, cybersecurity, etc.)

### Purity Guarantee

LIVELLO 1 (this package) contains **pure** domain logic:

- NO I/O (no HTTP, no database, no Redis)
- NO external dependencies beyond Python stdlib + numpy
- Testable in isolation without infrastructure

### Configuration Injection

All domain-specific values are injected via `BabelConfig`:

```python
from core.cognitive.babel_gardens.domain import SignalSchema, load_config_from_yaml

# Load domain-specific signal schemas at deploy time
config = load_config_from_yaml(
    signals_path=Path("config/signals.yaml"),
    taxonomy_path=Path("config/taxonomy.yaml")
)

# Example: Finance vertical
# signals.yaml:
#   - name: sentiment_valence
#     range: [-1.0, 1.0]
#     fusion_weight: 0.8

# Example: Cybersecurity vertical  
# signals.yaml:
#   - name: threat_severity
#     range: [0.0, 1.0]
#     fusion_weight: 1.0
```

## Sacred Laws

1. **The Tower accepts all tongues** — Support any language the models can handle
2. **Words carry meaning, not secrets** — Never store raw text, only embeddings
3. **Signals are inferred, never invented** — Extract structured signals, never generate narrative
4. **Explainability is sacred** — Every signal must trace its origin and method
5. **The Gardens grow with configuration** — Signals and taxonomies from YAML, never code

## Architecture

```
LIVELLO 1 (Pure Domain)
├── domain/           # SignalSchema, TaxonomyConfig, ModelAdapter
├── consumers/        # Pure processors (SignalExtractor, TopicClassifier, SignalFusion)
├── events/           # Channel constants
└── monitoring/       # Metric names

LIVELLO 2 (Service Layer - services/api_babel_gardens/)
├── adapters/         # I/O (embeddings API, Qdrant, Postgres)
├── api/routes.py     # HTTP endpoints
├── plugins/          # Vertical-specific signal definitions (finance, cybersec, etc.)
└── main.py           # FastAPI bootstrap (< 100 lines)
```

## Core Abstractions

### SignalSchema

Universal semantic signal definition:

```python
@dataclass(frozen=True)
class SignalSchema:
    """Domain-agnostic signal extraction specification"""
    name: str                                    # e.g., "risk_intensity", "sentiment_valence"
    value_range: tuple[float, float]            # e.g., (0.0, 1.0), (-1.0, 1.0)
    aggregation_method: str                     # "mean", "max", "weighted"
    fusion_weight: float = 1.0                  # For multi-signal synthesis
    explainability_required: bool = True        # Trace extraction method
    extraction_method: str = ""                 # e.g., "model:finbert", "heuristic:lexicon"
```

### ModelToSignalAdapter

Maps HuggingFace model outputs to SignalSchema values:

```python
class ModelToSignalAdapter:
    """Translate model-specific outputs to signal values"""
    
    def adapt(
        self,
        model_output: dict,      # {"positive": 0.7, "negative": 0.1, "neutral": 0.2}
        schema: SignalSchema
    ) -> dict:
        """Transform to signal value + explainability trace"""
        return {
            "signal_name": schema.name,
            "value": self._compute_signal_value(model_output, schema),
            "confidence": self._compute_confidence(model_output),
            "extraction_trace": {
                "model": self.model_name,
                "method": schema.extraction_method,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
```

## Signal Extraction Examples

### Finance Vertical
```yaml
# config/signals/finance.yaml
signals:
  - name: sentiment_valence
    range: [-1.0, 1.0]
    aggregation_method: weighted
    fusion_weight: 0.8
    explainability_required: true
    extraction_method: "model:finbert"
  
  - name: market_fear_index
    range: [0.0, 1.0]
    aggregation_method: max
    fusion_weight: 0.6
```

### Cybersecurity Vertical
```yaml
# config/signals/cybersecurity.yaml
signals:
  - name: threat_severity
    range: [0.0, 1.0]
    aggregation_method: max
    fusion_weight: 1.0
    extraction_method: "model:secbert"
  
  - name: exploit_imminence
    range: [0.0, 1.0]
    aggregation_method: weighted
    fusion_weight: 0.9
```

### Maritime Vertical
```yaml
# config/signals/maritime.yaml
signals:
  - name: operational_disruption
    range: [0.0, 1.0]
    aggregation_method: weighted
    fusion_weight: 0.9
  
  - name: delay_severity
    range: [0, 10]  # days
    aggregation_method: max
    fusion_weight: 1.0
```

## Version History

- **v1.0** (November 2025) — Initial implementation
- **v2.0** (February 2026) — SACRED_ORDER_PATTERN refactoring, domain-agnostic
- **v2.1** (February 2026) — SignalSchema abstraction, removed sentiment/emotion hardcoding
