# Pattern Weavers

<p class="kb-subtitle">Contestualizzazione semantica: weaving su tassonomie, estrazione concetti, struttura pronta per i downstream.</p>

## A cosa serve

- **Risoluzione su tassonomie**: mappa testo libero in categorie strutturate (concepts, sectors, regions, …)
- **Estrazione concetti**: ritorna nomi concetto deduplicati per pipeline downstream
- **Fallback**: keyword matching quando embedding/Qdrant non sono disponibili

- **Layer epistemico**: Reason (Semantic)
- **Mandato**: risolvere query non strutturate dentro **tassonomie di dominio** (concepts, sectors, regions, intents, …)
- **Output**: `WeaveResult` con `PatternMatch[]` + concetti estratti

## Charter (mandato + non-goals)

### Mandato

Pattern Weavers esiste per trasformare “linguaggio” in **contesto strutturato**:

- validare una weave request (`query_text`, filtri opzionali)
- preprocessare il testo per embedding (normalizzazione leggera)
- convertire i risultati di similarity search in `PatternMatch`
- estrarre nomi concetto (deduplicati) per gli altri Sacred Orders

### Non-goals

- **Niente I/O in LIVELLO 1**: niente HTTP, niente Qdrant, niente persistenza, niente publish su StreamBus
- **Niente risk scoring**: non calcola “rischio”, “sentiment”, “advice”, né giudizi di dominio
- **Niente hardcoding**: la tassonomia è in config/YAML/env, non nel core

## Interfacce

- **HTTP (LIVELLO 2)**: `services/api_pattern_weavers/` espone endpoint FastAPI (`/weave`, `/keyword-match`, `/health`, …)
- **Cognitive Bus (LIVELLO 2)**: event I/O opzionale via `BusAdapter` + `StreamBus`
- **Tassonomia (config)**: `PatternConfig.taxonomy` caricata da YAML in deploy

## Contratto eventi (Cognitive Bus)

Definiti in `vitruvyan_core/core/cognitive/pattern_weavers/events/__init__.py`:

- `pattern.weave.request`
- `pattern.weave.response`
- `pattern.weave.error`
- `pattern.taxonomy.updated` / `pattern.taxonomy.refresh`
- `pattern.health.check` / `pattern.health.status`

## Mappa del codice

- **LIVELLO 1 (puro, niente I/O)**: `vitruvyan_core/core/cognitive/pattern_weavers/`
  - Consumers: `consumers/weaver.py`, `consumers/keyword_matcher.py`
  - Oggetti dominio + config: `domain/entities.py`, `domain/config.py`
  - Eventi: `events/__init__.py`
- **LIVELLO 2 (service + adapters + I/O)**: `services/api_pattern_weavers/`
  - HTTP routes: `api/routes.py`
  - Bus orchestration: `adapters/bus_adapter.py`
  - Adapters embedding/Qdrant/persistenza: `adapters/embedding.py`, `adapters/persistence.py`

---

## Pipeline (happy path)

1. HTTP `POST /weave` riceve una `WeaveRequest`
2. L’adapter embedding chiama il servizio embedding (Babel Gardens) per ottenere `query_vector`
3. L’adapter persistence interroga Qdrant per similarity results
4. Il consumer LIVELLO 1 `WeaverConsumer.process(mode="process_results")` converte raw results → `WeaveResult`
5. Il service ritorna la response e opzionalmente logga/pubblica eventi

---

## Agenti / Consumers (LIVELLO 1)

### `WeaverConsumer` — semantic weaving (results → matches)

- File: `vitruvyan_core/core/cognitive/pattern_weavers/consumers/weaver.py`
- Funzioni:
  - modalità `validate_request`:
    - valida `query_text` e lunghezza (`PatternConfig.max_query_length`)
    - costruisce `WeaveRequest` e ritorna `preprocessed_query`
  - modalità `process_results`:
    - filtra risultati sotto `similarity_threshold`
    - converte ogni payload Qdrant → `PatternMatch(category, name, score, match_type=semantic, metadata)`
    - estrae concept names unici in `extracted_concepts`

**Input (validate_request)**:

- `query_text: str` (required)
- opzionali: `user_id`, `language`, `top_k`, `similarity_threshold`, `categories`, `correlation_id`

**Input (process_results)**:

- `similarity_results: list[dict]` (required)
- opzionale: `similarity_threshold`

**Output**:

- `data["request"] = WeaveRequest` *(validate_request)*
- `data["preprocessed_query"] = str` *(validate_request)*
- `data["result"] = WeaveResult` *(process_results)*

### `KeywordMatcherConsumer` — keyword matching su tassonomia (fallback)

- File: `vitruvyan_core/core/cognitive/pattern_weavers/consumers/keyword_matcher.py`
- Scopo:
  - fallback veloce quando embedding/Qdrant non sono disponibili
  - match del testo tokenizzato contro `PatternConfig.taxonomy`

**Come funziona**:

- tokenizza la query in `set[str]` (lowercase, punteggiatura rimossa)
- per ogni `category_type` della tassonomia:
  - intersezione tra token query e keywords della categoria
  - score = `match_count / total_keywords` (cap 1.0)
- ritorna `PatternMatch(match_type=keyword)` con `matched_keywords` in metadata

---

## Service (LIVELLO 2) — API surface

Service: `services/api_pattern_weavers/`.

### Endpoint (implementati)

- `GET /health` — health dipendenze (Postgres, Qdrant, Redis, embedding service)
- `POST /weave` — embedding + Qdrant similarity + weaving semantico
- `POST /keyword-match` — fallback keyword-only (no embedding)
- `GET /taxonomy/stats` — conteggi/categorie tassonomia (da domain config)
- `GET /metrics` — Prometheus

> Nota porte: il codice ha default multipli (`PATTERN_PORT` vs `start.sh --port 8017`). In deploy fa fede il mapping di Docker compose.

## Specializzazione dominio (finanza, pilota)

Pattern Weavers resta domain-agnostic: la finanza vive nella **tassonomia** (YAML) e nei consumer downstream.

Esempi finanza:

- tassonomia: settori (GICS), regioni, strumenti, risk terms, macro terms
- concetti estratti alimentano:
  - Neural Engine (feature generation)
  - Orthodoxy Wardens (guardrails/compliance)
  - Vault Keepers (archiviazione risultati weaving)
