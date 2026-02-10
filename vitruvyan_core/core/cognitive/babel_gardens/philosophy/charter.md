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

1. **Language Detection** — Identify the language of input text
2. **Embedding Generation** — Transform text into dense vector representations
3. **Sentiment Analysis** — Extract emotional valence from text
4. **Emotion Detection** — Classify fine-grained emotions
5. **Topic Classification** — Categorize text into configurable topics
6. **Linguistic Synthesis** — Fuse semantic and sentiment vectors

## Invariants

### Domain Agnostic

Babel Gardens is **completely domain-agnostic**:

- NO hardcoded topic categories (use `TopicConfig.from_yaml()`)
- NO domain-specific embedding models (use `EmbeddingModelConfig`)
- NO hardcoded sentiment labels (use `SentimentModelConfig.labels`)

### Purity Guarantee

LIVELLO 1 (this package) contains **pure** domain logic:

- NO I/O (no HTTP, no database, no Redis)
- NO external dependencies beyond Python stdlib + numpy
- Testable in isolation without infrastructure

### Configuration Injection

All domain-specific values are injected via `BabelConfig`:

```python
from core.cognitive.babel_gardens.domain import get_config, load_config_from_yaml

# Load domain-specific taxonomy at deploy time
config = load_config_from_yaml(topics_path=Path("config/topics.yaml"))
```

## Sacred Laws

1. **The Tower accepts all tongues** — Support any language the models can handle
2. **Words carry meaning, not secrets** — Never store raw text, only embeddings
3. **Emotions flow through, not from, the Tower** — Sentiment is detected, not generated
4. **The Gardens grow with configuration** — Topics and categories from YAML, never code

## Architecture

```
LIVELLO 1 (Pure Domain)
├── domain/           # Config + entities
├── consumers/        # Pure processors (SynthesisConsumer, TopicClassifier)
├── events/           # Channel constants
└── monitoring/       # Metric names

LIVELLO 2 (Service Layer - services/api_babel_gardens/)
├── adapters/         # I/O (embeddings API, Qdrant, Postgres)
├── api/routes.py     # HTTP endpoints
└── main.py           # FastAPI bootstrap (< 100 lines)
```

## Version History

- **v1.0** (November 2025) — Initial implementation
- **v2.0** (February 2026) — SACRED_ORDER_PATTERN refactoring, domain-agnostic
