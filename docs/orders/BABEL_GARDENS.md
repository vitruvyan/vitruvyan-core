# Babel Gardens

> **Last Updated**: February 25, 2026

## What it does

- Extracts structured semantic signals from text (with confidence + traceability)
- Produces embeddings/features that downstream components can consume safely
- Exposes a clean boundary via events/API (service executes I/O)

- **Epistemic Layer**: Perception (Linguistic Processing / Signal Extraction)
- **Mandate**: transform unstructured text into **structured, explainable semantic signals**
- **Verticalization**: YAML-driven signal definitions + optional model plugins

## Charter (Mandate + Non-goals)

### Mandate
Extract signals that are grounded in text evidence and safe to consume downstream (Neural Engine, Orthodoxy Wardens, Vault Keepers).

### Non-goals
- Not a decision engine (no risk scoring / ranking).
- Not a taxonomy engine (ontology resolution belongs to Pattern Weavers).

## Interfaces

### Event contract (Cognitive Bus)
Defined in `vitruvyan_core/core/cognitive/babel_gardens/events/__init__.py` (selected):

- `babel.embedding.request` → `babel.embedding.response`
- `babel.sentiment.request` → `babel.sentiment.response`
- `babel.synthesis.request` → `babel.synthesis.response`
- `babel.error`

### Service (LIVELLO 2)
- `services/api_babel_gardens/` — model loading + inference + I/O boundary

## Pipeline (happy path)

1. Input text → (optional) language detection
2. Model/plugin inference → signal values + confidence
3. Emit structured results with explainability traces

## Code map

### LIVELLO 1 (pure)
- `vitruvyan_core/core/cognitive/babel_gardens/domain/signal_schema.py`
- `vitruvyan_core/core/cognitive/babel_gardens/domain/config.py` (YAML loading/merge)
- `vitruvyan_core/core/cognitive/babel_gardens/consumers/` (pure orchestration)

### LIVELLO 2 (adapters)
- `services/api_babel_gardens/plugins/` (optional model wrappers)
- `services/api_babel_gardens/` (API + runtime)

## Verticalization (finance pilot)

Finance defines a signal set (YAML) and, optionally, a plugin:

- `signals_finance.yaml`: what signals exist (e.g., sentiment_valence, market_fear_index)
- `FinanceSignalsPlugin`: how to compute them (model wrapper), if needed

Rule:
the **signal schema** belongs to the domain pack, not to the Babel Gardens core.

## Comprehension Engine v3

With `BABEL_COMPREHENSION_V3=1`, Babel Gardens gains a unified comprehension pipeline that produces both semantic signals (`SemanticPayload`) and ontology structure (`OntologyPayload`) in a **single LLM call**.

### New endpoints
- `POST /v2/comprehend` — full comprehension (ontology + semantics)
- `POST /v2/fuse` — multi-source signal fusion (LLM + domain models)

### 3-layer architecture
- **L1**: LLM comprehension → `ComprehensionResult` (ontology + semantics)
- **L2**: Domain models (e.g., FinBERT) → `SignalEvidence[]`
- **L3**: Signal fusion (weighted/bayesian/LLM-arbitrated) → `FusionResult`

### Plugin system
- `IComprehensionPlugin` — domain-wide prompt shaping (ontology + semantics sections)
- `ISignalContributor` — domain-specific model contributions (lazy-loaded, availability-checked)

### Code map (v3 additions)
- `contracts/comprehension.py` — `ComprehensionResult`, `IComprehensionPlugin`, `ISignalContributor`
- `core/cognitive/babel_gardens/consumers/comprehension_consumer.py` — JSON→result parser
- `core/cognitive/babel_gardens/consumers/signal_fusion_consumer.py` — fusion strategies
- `core/cognitive/babel_gardens/governance/signal_registry.py` — plugin + contributor registries
- `services/api_babel_gardens/adapters/comprehension_adapter.py` — LLM orchestration
- `services/api_babel_gardens/adapters/signal_fusion_adapter.py` — fusion + arbitration
- `services/api_babel_gardens/api/routes_comprehension.py` — HTTP endpoints
- `core/orchestration/langgraph/node/comprehension_node.py` — graph node (replaces PW + emotion nodes)

For the full architectural rationale, see [Semantic & Ontology Architecture](../architecture/SEMANTIC_ONTOLOGY_ARCHITECTURE.md).
