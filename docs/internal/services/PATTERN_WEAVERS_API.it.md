# Pattern Weavers API

<p class="kb-subtitle">Façade HTTP per Pattern Weavers (LIVELLO 2). Embedding + similarità Qdrant + weaving semantico.</p>

## Location

- Service: `services/api_pattern_weavers/`
- Core puro: `vitruvyan_core/core/cognitive/pattern_weavers/`

## Base URL / Porta

- Lo startup script avvia Uvicorn su **porta `8017`** (`services/api_pattern_weavers/start.sh`).
- La config del servizio ha un default separato (`PATTERN_PORT`, `services/api_pattern_weavers/config.py`).

In deploy fa fede il mapping di **docker-compose**.

## Endpoint (implementati)

Definiti in `services/api_pattern_weavers/api/routes.py` e `services/api_pattern_weavers/main.py`:

- `GET /` — info servizio
- `GET /health` — health dipendenze (Postgres, Qdrant, Redis, embedding service)
- `GET /metrics` — Prometheus
- `POST /weave` — flow principale (embedding → Qdrant → consumer LIVELLO 1)
- `POST /keyword-match` — fallback keyword-only (senza embedding/Qdrant)
- `GET /taxonomy/stats` — categorie/dimensione tassonomia (da config LIVELLO 1)

## Modelli request/response

Vedi `services/api_pattern_weavers/models/schemas.py`.

### `POST /weave`

Request (`WeaveRequest`):

- `query: str` (required)
- `user_id: str | null`
- `context: dict` (opzionale)
- `limit: int` (default 10)
- `threshold: float` (default 0.4)

Response (`WeaveResult`):

- `request_id: str`
- `status: str`
- `matches: PatternMatch[]`
- `processing_time_ms: float`
- `metadata: dict`

### `POST /keyword-match`

Usa lo stesso schema `WeaveRequest`, ma ritorna:

- `request_id`
- `matches` *(dict grezzi dal keyword consumer LIVELLO 1)*
- `method = "keyword"`

## Flusso implementativo (happy path)

In `POST /weave`:

1. `EmbeddingAdapter.get_embedding(query)` ottiene il vettore dall’embedding service
2. `Persistence.search_similar(...)` interroga Qdrant
3. `WeaverConsumer.process(mode="process_results")` converte raw results → `WeaveResult`
4. Il service logga la weave via persistence quando `user_id` è presente

## Env vars (service)

Caricate in `services/api_pattern_weavers/config.py`:

- `PATTERN_HOST`, `PATTERN_PORT`
- `EMBEDDING_URL`, `EMBEDDING_ENDPOINT`, `EMBEDDING_TIMEOUT`
- `QDRANT_HOST`, `QDRANT_PORT`, `PATTERN_COLLECTION`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`
- `PATTERN_TAXONOMY_PATH`

