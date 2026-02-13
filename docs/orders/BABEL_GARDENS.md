# Babel Gardens

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

