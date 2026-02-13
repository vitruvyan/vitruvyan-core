# Codex Hunters API

<p class="kb-subtitle">Service LIVELLO 2 per discovery/restoration/binding e tracking di expeditions.</p>

## Location

- Service: `services/api_codex_hunters/`
- Core puro: `vitruvyan_core/core/governance/codex_hunters/`

## Base URL / Porta

Porta di default: **`8008`** (`services/api_codex_hunters/config.py`, env: `CODEX_API_PORT`).

> Nota deploy: alcune doc “fleet” citano porte diverse (es. 9005). In deploy fa fede il mapping docker-compose.

## Endpoint (implementati)

Definiti in `services/api_codex_hunters/api/routes.py`:

- `GET /health`
- `GET /stats`
- `GET /metrics`
- `POST /expedition/run`
- `GET /expedition/status/{expedition_id}`
- `GET /expedition/history`

Pipeline discovery:

- `POST /discover`
- `POST /restore`
- `POST /bind`

## Env vars (service)

Caricate in `services/api_codex_hunters/config.py`:

- `CODEX_API_HOST`, `CODEX_API_PORT`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_GRPC_PORT`
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`

