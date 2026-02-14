# Embedding API

<p class="kb-subtitle">Servizio LIVELLO 2 per embeddings MiniLM e storage opzionale su Qdrant.</p>

## Location

- Service: `services/api_embedding/`

## Base URL / Port

Porta di default **`8010`** (env: `PORT`).

## Endpoints (implementati)

Definiti in `services/api_embedding/api/routes.py`:

- `GET /health`
- `POST /v1/embeddings/create` — embedding singolo
- `POST /v1/embeddings/batch` — batch embeddings (max 100)
- `POST /v1/sync/postgres_to_qdrant` — placeholder (attualmente ritorna zeri)
- `GET /v1/stats`

Endpoint metriche (Prometheus) definito in `services/api_embedding/main.py`:

- `GET /metrics`

## Request/Response schemas

Modelli Pydantic in `services/api_embedding/schemas.py`.

Tipi principali:

- `EmbeddingRequest` (`text`, `model`, `store_in_qdrant`, `collection_name`)
- `BatchEmbeddingRequest` (`texts[]`, `model`, `store_in_qdrant`, `collection_name`)
- `SyncRequest` (`limit`, `offset`)

## Env vars del servizio

Caricati in `services/api_embedding/config.py`:

- `PORT`
- `LOG_LEVEL`
- `EMBEDDING_MODEL`
- `QDRANT_COLLECTION`
