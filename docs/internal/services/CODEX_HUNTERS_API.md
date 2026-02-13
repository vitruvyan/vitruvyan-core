# Codex Hunters API

<p class="kb-subtitle">LIVELLO 2 service for discovery/restoration/binding and expedition tracking.</p>

## Location

- Service: `services/api_codex_hunters/`
- Pure core: `vitruvyan_core/core/governance/codex_hunters/`

## Base URL / Port

Default port is **`8008`** (`services/api_codex_hunters/config.py`, env: `CODEX_API_PORT`).

> Deploy note: some higher-level docs reference different “fleet ports” (e.g. 9005). Treat docker-compose mapping as source-of-truth.

## Endpoints (implemented)

Defined in `services/api_codex_hunters/api/routes.py`:

- `GET /health`
- `GET /stats`
- `GET /metrics`
- `POST /expedition/run`
- `GET /expedition/status/{expedition_id}`
- `GET /expedition/history`

Discovery pipeline:

- `POST /discover`
- `POST /restore`
- `POST /bind`

## Service config env vars

Loaded in `services/api_codex_hunters/config.py`:

- `CODEX_API_HOST`, `CODEX_API_PORT`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_GRPC_PORT`
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`

