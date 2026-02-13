# Pattern Weavers API

<p class="kb-subtitle">HTTP façade for Pattern Weavers (LIVELLO 2). Embedding + Qdrant similarity + semantic weaving.</p>

## Location

- Service: `services/api_pattern_weavers/`
- Pure core: `vitruvyan_core/core/cognitive/pattern_weavers/`

## Base URL / Port

- The container startup script runs Uvicorn on **port `8017`** (`services/api_pattern_weavers/start.sh`).
- The service config has a separate default (`PATTERN_PORT`, `services/api_pattern_weavers/config.py`).

Treat **docker-compose port mapping** as the source of truth in deployment.

## Endpoints (implemented)

Defined in `services/api_pattern_weavers/api/routes.py` and `services/api_pattern_weavers/main.py`:

- `GET /` — service info
- `GET /health` — dependency health (Postgres, Qdrant, Redis, embedding service)
- `GET /metrics` — Prometheus metrics
- `POST /weave` — main semantic weaving flow (embedding → Qdrant → LIVELLO 1 consumer)
- `POST /keyword-match` — keyword-only fallback (no embedding/Qdrant required)
- `GET /taxonomy/stats` — taxonomy categories/size (from LIVELLO 1 domain config)

## Request/Response models

See `services/api_pattern_weavers/models/schemas.py`.

### `POST /weave`

Request (`WeaveRequest`):

- `query: str` (required)
- `user_id: str | null`
- `context: dict` (optional)
- `limit: int` (default 10)
- `threshold: float` (default 0.4)

Response (`WeaveResult`):

- `request_id: str`
- `status: str`
- `matches: PatternMatch[]`
- `processing_time_ms: float`
- `metadata: dict`

### `POST /keyword-match`

Uses the same `WeaveRequest` schema, but returns:

- `request_id`
- `matches` *(raw dicts from LIVELLO 1 keyword consumer)*
- `method = "keyword"`

## Implementation flow (happy path)

In `POST /weave`:

1. `EmbeddingAdapter.get_embedding(query)` obtains a vector from the embedding service
2. `Persistence.search_similar(...)` queries Qdrant
3. `WeaverConsumer.process(mode="process_results")` converts raw results → `WeaveResult`
4. The service logs the weave via persistence when `user_id` is present

## Env vars (service-level)

Loaded in `services/api_pattern_weavers/config.py`:

- `PATTERN_HOST`, `PATTERN_PORT`
- `EMBEDDING_URL`, `EMBEDDING_ENDPOINT`, `EMBEDDING_TIMEOUT`
- `QDRANT_HOST`, `QDRANT_PORT`, `PATTERN_COLLECTION`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`
- `PATTERN_TAXONOMY_PATH`

