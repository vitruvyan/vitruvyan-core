# Pattern Weavers

- **Epistemic Layer**: Reason (Ontology Resolution / Semantic Contextualization)
- **Mandate**: resolve user text into structured taxonomy matches (concepts, sectors, regions, entities)
- **Hard boundary**: extract structure, never interpret meaning (no risk/scoring here)

## Charter (Mandate + Non-goals)

### Mandate
Provide domain-agnostic ontology resolution via YAML-driven taxonomies and explainable similarity matches.

### Non-goals
- Not a scoring engine (Neural Engine responsibility).
- Not a signal extractor (Babel Gardens responsibility).

## Interfaces

### Event contract (Cognitive Bus)
Defined in `vitruvyan_core/core/cognitive/pattern_weavers/events/__init__.py` (selected):

- `pattern.weave.request` → `pattern.weave.response`
- `pattern.weave.error`

### Service (LIVELLO 2)
- `services/api_pattern_weavers/` — adapters for embedding + Qdrant, HTTP API

## Pipeline (happy path)

1. Query text → embedding (via Babel Gardens/service adapter)
2. Similarity search (Qdrant) + keyword fallback
3. `WeaveResult` with explainable matches (scores, match_type, metadata)

## Code map

### LIVELLO 1 (pure)
- `vitruvyan_core/core/cognitive/pattern_weavers/domain/entities.py` (WeaveRequest/WeaveResult)
- `vitruvyan_core/core/cognitive/pattern_weavers/domain/config.py` (taxonomy YAML)
- `vitruvyan_core/core/cognitive/pattern_weavers/consumers/weaver.py`
- `vitruvyan_core/core/cognitive/pattern_weavers/consumers/keyword_matcher.py`

### LIVELLO 2 (adapters)
- `services/api_pattern_weavers/adapters/` (Qdrant + embedding I/O boundary)

## Verticalization (finance pilot)

Finance provides:

- a taxonomy YAML (sectors, instruments, regions) used by Pattern Weavers
- optional keyword lists to improve deterministic recall

Rule:
domain taxonomies live outside the core; the core is only the resolver.

