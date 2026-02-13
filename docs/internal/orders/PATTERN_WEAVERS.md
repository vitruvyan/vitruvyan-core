# Pattern Weavers

<p class="kb-subtitle">Semantic contextualization: taxonomy weaving, concept extraction, and signal-ready structure.</p>

- **Epistemic layer**: Reason (Semantic)
- **Mandate**: resolve unstructured queries into **domain taxonomies** (concepts, sectors, regions, intents, …)
- **Outputs**: `WeaveResult` with `PatternMatch[]` + extracted concepts

## Charter (mandate + non-goals)

### Mandate

Pattern Weavers exists to turn “language” into **structured context**:

- validate a weave request (`query_text`, optional filters)
- preprocess text for embedding (light normalization)
- convert similarity search results into `PatternMatch` objects
- extract *concept names* (deduped) for downstream Sacred Orders

### Non-goals

- **No I/O in LIVELLO 1**: no HTTP calls, no Qdrant queries, no persistence, no StreamBus publishing
- **No risk scoring**: Pattern Weavers does not compute “risk”, “sentiment”, “advice”, or domain judgment
- **No domain hardcoding**: taxonomy content is injected/configured (YAML/env), not embedded in core logic

## Interfaces

- **HTTP (LIVELLO 2)**: `services/api_pattern_weavers/` exposes FastAPI endpoints (`/weave`, `/keyword-match`, `/health`, …)
- **Cognitive Bus (LIVELLO 2)**: optional event consumption/publication via `BusAdapter` + `StreamBus`
- **Taxonomy (config)**: `PatternConfig.taxonomy` loaded from YAML at deploy time

## Event contract (Cognitive Bus)

Defined in `vitruvyan_core/core/cognitive/pattern_weavers/events/__init__.py`:

- `pattern.weave.request`
- `pattern.weave.response`
- `pattern.weave.error`
- `pattern.taxonomy.updated` / `pattern.taxonomy.refresh`
- `pattern.health.check` / `pattern.health.status`

## Code map

- **LIVELLO 1 (pure, no I/O)**: `vitruvyan_core/core/cognitive/pattern_weavers/`
  - Consumers: `consumers/weaver.py`, `consumers/keyword_matcher.py`
  - Domain objects + config: `domain/entities.py`, `domain/config.py`
  - Events: `events/__init__.py`
- **LIVELLO 2 (service + adapters + I/O)**: `services/api_pattern_weavers/`
  - HTTP routes: `api/routes.py`
  - Bus orchestration: `adapters/bus_adapter.py`
  - Embedding/Qdrant/Persistence adapters: `adapters/embedding.py`, `adapters/persistence.py`

---

## Pipeline (happy path)

1. HTTP `POST /weave` receives a `WeaveRequest`
2. Embedding adapter calls the embedding service (Babel Gardens) to obtain `query_vector`
3. Persistence adapter queries Qdrant for similarity results
4. LIVELLO 1 `WeaverConsumer.process(mode="process_results")` converts raw results → `WeaveResult`
5. Service returns the response and optionally logs/publishes events

---

## Agents / Consumers (LIVELLO 1)

### `WeaverConsumer` — semantic weaving (results → matches)

- File: `vitruvyan_core/core/cognitive/pattern_weavers/consumers/weaver.py`
- Responsibilities:
  - `validate_request` mode:
    - validates `query_text` and length (`PatternConfig.max_query_length`)
    - builds a `WeaveRequest` and returns `preprocessed_query`
  - `process_results` mode:
    - filters results below `similarity_threshold`
    - converts each Qdrant payload → `PatternMatch(category, name, score, match_type=semantic, metadata)`
    - extracts unique concept names into `extracted_concepts`

**Input (validate_request)**:

- `query_text: str` (required)
- optional: `user_id`, `language`, `top_k`, `similarity_threshold`, `categories`, `correlation_id`

**Input (process_results)**:

- `similarity_results: list[dict]` (required)
- optional: `similarity_threshold`

**Output**:

- `data["request"] = WeaveRequest` *(validate_request)*
- `data["preprocessed_query"] = str` *(validate_request)*
- `data["result"] = WeaveResult` *(process_results)*

### `KeywordMatcherConsumer` — taxonomy keyword matching (fallback)

- File: `vitruvyan_core/core/cognitive/pattern_weavers/consumers/keyword_matcher.py`
- Purpose:
  - fast fallback when embedding/Qdrant is unavailable
  - matches tokenized query text against `PatternConfig.taxonomy`

**How it works**:

- tokenizes query to a `set[str]` (lowercase, punctuation stripped)
- for each `category_type` in taxonomy:
  - intersects query tokens with each category’s keyword set
  - scores as `match_count / total_keywords` (capped at 1.0)
- returns `PatternMatch(match_type=keyword)` with `matched_keywords` in metadata

---

## Service (LIVELLO 2) — API surface

Service location: `services/api_pattern_weavers/`.

### Endpoints (as implemented)

- `GET /health` — dependency health (Postgres, Qdrant, Redis, embedding service)
- `POST /weave` — embedding + Qdrant similarity + semantic weaving
- `POST /keyword-match` — keyword-only fallback (no embedding required)
- `GET /taxonomy/stats` — taxonomy counts/categories (from domain config)
- `GET /metrics` — Prometheus

> Ports note: the service code has multiple defaults (`PATTERN_PORT` vs `start.sh --port 8017`). Treat the **Docker compose mapping** as source-of-truth in deployment.

## Domain specialization (finance pilot)

Pattern Weavers stays domain-agnostic: finance specialization lives in the **taxonomy file** (YAML) and in downstream consumers.

Finance examples:

- taxonomy categories: sectors (GICS), regions, instruments, risk terms, macro terms
- extracted concepts feed:
  - Neural Engine feature generation
  - Orthodoxy Wardens compliance checks (guardrails)
  - Vault Keepers archival of weave results
