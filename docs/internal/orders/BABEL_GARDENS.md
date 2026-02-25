# Babel Gardens

> **Last Updated**: February 25, 2026

<p class="kb-subtitle">Text-to-signal extraction: embeddings, sentiment/signals, and explainable linguistic outputs.</p>

## What it does

- Extracts **structured semantic signals** from unstructured text (with confidence + traceability)
- Produces embeddings and model-driven features for downstream Orders (Pattern Weavers, Neural Engine, Vault)
- Publishes events and exposes APIs via LIVELLO 2 (service), while keeping LIVELLO 1 pure

- **Epistemic layer**: Perception (Linguistic Processing / Semantic Grounding)
- **Mandate**: turn multilingual text into **structured, auditable artifacts** (vectors + signals)
- **Outputs**: embeddings, sentiment/emotion signals, topic matches, fused vectors, explainability traces

## Charter (mandate + non-goals)

### Mandate

- detect language (or validate caller-provided language)
- produce semantic embeddings (single/batch, multilingual)
- expose semantic signals (sentiment/emotion + structured traces)
- classify text into configurable topics (taxonomy)
- fuse vectors deterministically when required (synthesis)

### Non-goals

- no business decisions (no ranking, no risk scoring)
- no domain ontology resolution (belongs to Pattern Weavers)
- no storage governance (belongs to Vault Keepers / Memory Orders)

## Interfaces

- **HTTP (LIVELLO 2)**: `services/api_babel_gardens/`
  - Embeddings: `/v1/embeddings/*`
  - Sentiment: `/v1/sentiment/*`
  - Emotion: `/v1/emotion/detect`
  - Profiles + cognitive routing: `/v1/profiles/*`, `/v1/events/*`, `/v1/routing/*`
- **Cognitive Bus (optional, LIVELLO 2)**: streams listener + event channels

## Event contract (Cognitive Bus)

Defined in `vitruvyan_core/core/cognitive/babel_gardens/events/__init__.py`:

- `babel.embedding.request` / `babel.embedding.response`
- `babel.sentiment.request` / `babel.sentiment.response`
- `babel.emotion.request` / `babel.emotion.response`
- `babel.topic.request` / `babel.topic.response`
- `babel.synthesis.request` / `babel.synthesis.response`
- `babel.error`

## Code map

- **LIVELLO 1 (pure, no I/O)**: `vitruvyan_core/core/cognitive/babel_gardens/`
  - Domain config: `domain/config.py` (language + cache + taxonomy injection)
  - Topic + language consumers: `consumers/classifiers.py`
  - Vector fusion consumer: `consumers/synthesis.py`
  - Events: `events/__init__.py`
  - Examples: `examples/*.yaml` (vertical signal schema examples)
- **LIVELLO 2 (service + modules + adapters)**: `services/api_babel_gardens/`
  - Embedding engine: `modules/embedding_engine.py`
  - Sentiment fusion: `modules/sentiment_fusion.py`
  - Emotion detection: `modules/emotion_detector.py`
  - Profile processor + cognitive bridge: `modules/profile_processor.py`, `modules/cognitive_bridge.py`
  - HTTP routes: `api/routes_*.py`

## Pipeline (happy path)

1. Service receives text (+ optional language hint)
2. Language is detected/validated (multilingual-safe path)
3. Embedding is generated (and optionally cached)
4. Optional: sentiment/emotion signals are extracted
5. Optional: vectors are fused (synthesis) for downstream consumers
6. Result is returned via HTTP and/or emitted on the bus

---

## Consumers (LIVELLO 1)

### `LanguageDetectorConsumer` — language detection (heuristic)

- File: `vitruvyan_core/core/cognitive/babel_gardens/consumers/classifiers.py`
- Purpose: lightweight language detection to support domain purity (adapters can use stronger ML cascades)

### `TopicClassifierConsumer` — taxonomy classification

- File: `vitruvyan_core/core/cognitive/babel_gardens/consumers/classifiers.py`
- Purpose: classify text into topics using a deploy-time taxonomy (YAML-driven, domain-agnostic)

### `SynthesisConsumer` — vector fusion

- File: `vitruvyan_core/core/cognitive/babel_gardens/consumers/synthesis.py`
- Purpose: fuse semantic + sentiment vectors deterministically (`semantic_garden_fusion` default)

## Verticalization (finance pilot)

Finance binds Babel Gardens by providing:

- **topic taxonomy** (keywords/categories) via YAML injection
- **signal schema examples** (domain-agnostic primitives): `vitruvyan_core/core/cognitive/babel_gardens/examples/signals_finance.yaml`
- optional service plugins: `services/api_babel_gardens/plugins/finance_signals.py`

Rule: the **schema/config lives in the vertical**, not in the Babel Gardens core.

---

## Comprehension Engine v3 (February 25, 2026)

With `BABEL_COMPREHENSION_V3=1`, Babel Gardens gains a unified comprehension pipeline that produces both semantic signals and ontology structure in a **single LLM call**.

### Architecture

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| **L1** | `ComprehensionConsumer` | Parse LLM JSON → `ComprehensionResult` (ontology + semantics) |
| **L2** | Domain models (FinBERT, etc.) | Produce `SignalEvidence[]` via `ISignalContributor` |
| **L3** | `SignalFusionConsumer` | Weighted/bayesian/LLM-arbitrated fusion → `FusionResult` |

### New endpoints

- `POST /v2/comprehend` — full comprehension (ontology + semantics in one call)
- `POST /v2/fuse` — multi-source signal fusion

### Consumers (LIVELLO 1)

#### `ComprehensionConsumer` — LLM JSON parsing
- File: `vitruvyan_core/core/cognitive/babel_gardens/consumers/comprehension_consumer.py`
- Assembles prompt from domain plugin (ontology + semantics sections)
- Returns `ComprehensionResult` with separate `OntologyPayload` and `SemanticPayload`

#### `SignalFusionConsumer` — signal fusion
- File: `vitruvyan_core/core/cognitive/babel_gardens/consumers/signal_fusion_consumer.py`
- Strategies: `weighted` (default), `bayesian`, `llm_arbitrated`
- Fuses L1 (LLM) + L2 (domain model) signals into `FusionResult`

### Registries (LIVELLO 1)

#### `ComprehensionPluginRegistry` + `SignalContributorRegistry`
- File: `vitruvyan_core/core/cognitive/babel_gardens/governance/signal_registry.py`
- Domain plugins (`IComprehensionPlugin`) shape both ontology and semantics prompts
- Signal contributors (`ISignalContributor`) add domain-calibrated signals (lazy-loaded)

### Adapters (LIVELLO 2)

- `ComprehensionAdapter` (`services/api_babel_gardens/adapters/comprehension_adapter.py`) — LLM orchestration
- `SignalFusionAdapter` (`services/api_babel_gardens/adapters/signal_fusion_adapter.py`) — fusion + LLM arbitration

### Graph integration

- `comprehension_node` (`core/orchestration/langgraph/node/comprehension_node.py`) replaces both `pattern_weavers_node` and `emotion_detector_node` with full backward compatibility

### Plugin system

- `IComprehensionPlugin` — shapes both ontology and semantics prompt sections
- `ISignalContributor` — contributes domain-specific signals to fusion
- Built-in: `GenericComprehensionPlugin` (domain-agnostic)
- Finance: `FinanceComprehensionPlugin` (11 entity types, FinBERT signals) + `FinBERTContributor`

### Contracts

- `contracts/comprehension.py` — `ComprehensionResult`, `SemanticPayload`, `IComprehensionPlugin`, `ISignalContributor`, `SignalEvidence`, `FusionResult`
- `contracts/pattern_weavers.py` — `OntologyPayload` (reused, PW-owned)

### Tests

- 49 core tests (`tests/test_comprehension_engine.py`): contracts, consumers, registries, cross-domain
- 29 finance tests (`tests/test_finance_comprehension_plugin.py`): plugin, FinBERT, fusion
- All 78 pass ✅

For the full architectural rationale, see [Semantic & Ontology Architecture](../architecture/SEMANTIC_ONTOLOGY_ARCHITECTURE.md).
