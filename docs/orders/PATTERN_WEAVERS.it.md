# Pattern Weavers

- **Livello epistemico**: Reason (Ontology Resolution / Semantic Contextualization)
- **Mandato**: risolvere testo in match tassonomici (concetti, settori, regioni, entità)
- **Confine**: estrarre struttura, non interpretare (no risk/scoring)

## Charter (Mandato + Non-goals)

### Mandato
Risoluzione ontologica domain-agnostic tramite tassonomie YAML e match spiegabili.

### Non-goals
- Non è un motore di scoring (→ Neural Engine).
- Non è un signal extractor (→ Babel Gardens).

## Interfacce

### Contratto eventi (Cognitive Bus)
Definiti in `vitruvyan_core/core/cognitive/pattern_weavers/events/__init__.py`:

- `pattern.weave.request` → `pattern.weave.response`
- `pattern.weave.error`

### Servizio (LIVELLO 2)
- `services/api_pattern_weavers/`

## Pipeline (happy path)

1. Query → embedding (adapter/service)
2. Similarity search + keyword fallback
3. `WeaveResult` con match spiegabili (score, match_type, metadata)

## Mappa codice

### LIVELLO 1 (pure)
- `vitruvyan_core/core/cognitive/pattern_weavers/domain/`
- `vitruvyan_core/core/cognitive/pattern_weavers/consumers/`

### LIVELLO 2 (adapters)
- `services/api_pattern_weavers/adapters/`

## Verticalizzazione (pilota finanza)

Finanza fornisce tassonomie YAML (settori/strumenti/regioni) e keyword; il core resta solo il resolver.

