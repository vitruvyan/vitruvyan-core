# Pattern Weavers

## A cosa serve

- Mappa testo libero in categorie tassonomiche (concetti, settori, regioni, …)
- Estrae concetti per pipeline downstream
- Fornisce fallback keyword quando la ricerca semantica non è disponibile

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

## v3 — Compilazione Semantica LLM

Con `PATTERN_WEAVERS_V3=1`, la pipeline embedding a due stadi viene sostituita da una **singola chiamata LLM** (`LLMAgent.complete_json()`) che produce un `OntologyPayload` a schema strict. Il sistema di plugin (`ISemanticPlugin`) permette ai domini di iniettare prompt, tipi entità e regole di validazione.

Finanza: `FinanceSemanticPlugin` — 11 tipi entità, keyword multilingua (en/it/es/fr/de), normalizzazione ticker uppercase.

## Comprehension Engine v3

Con `BABEL_COMPREHENSION_V3=1`, la risoluzione ontologica di Pattern Weavers è unificata con l'estrazione semantica di Babel Gardens in una **singola chiamata LLM** — il Comprehension Engine. L'`OntologyPayload` (di proprietà PW) e il `SemanticPayload` (di proprietà BG) vengono prodotti insieme ma restano contratti architetturalmente separati.

PW continua a possedere la dimensione ontologica (gate, entità, intent, topic) mentre BG possiede la semantica (sentiment, emozione, registro linguistico).

Per la filosofia architetturale completa, vedi [Architettura Semantica & Ontologica](../architecture/SEMANTIC_ONTOLOGY_ARCHITECTURE.it.md).
