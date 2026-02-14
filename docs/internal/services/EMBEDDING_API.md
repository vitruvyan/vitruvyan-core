# Embedding API

<p class="kb-subtitle">LIVELLO 2 service for MiniLM embeddings and optional Qdrant storage.</p>

## Location

- Service: `services/api_embedding/`

## Base URL / Port

Default port is **`8010`** (env: `PORT`).

## Endpoints (implemented)

Defined in `services/api_embedding/api/routes.py`:

- `GET /health`
- `POST /v1/embeddings/create` — single text embedding
- `POST /v1/embeddings/batch` — batch embeddings (max 100)
- `POST /v1/sync/postgres_to_qdrant` — sync placeholder (currently returns zeros)
- `GET /v1/stats`

Metrics endpoint (Prometheus) is defined in `services/api_embedding/main.py`:

- `GET /metrics`

## Request/Response schemas

Pydantic models live in `services/api_embedding/schemas.py`.

Key request types:

- `EmbeddingRequest` (`text`, `model`, `store_in_qdrant`, `collection_name`)
- `BatchEmbeddingRequest` (`texts[]`, `model`, `store_in_qdrant`, `collection_name`)
- `SyncRequest` (`limit`, `offset`)

## Service config env vars

Loaded in `services/api_embedding/config.py`:

- `PORT`
- `LOG_LEVEL`
- `EMBEDDING_MODEL`
- `QDRANT_COLLECTION`
