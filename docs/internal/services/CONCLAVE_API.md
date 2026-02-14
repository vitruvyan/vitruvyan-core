# Synaptic Conclave API

<p class="kb-subtitle">LIVELLO 2 service that bridges HTTP → Redis Streams (observatory + emitter).</p>

## Location

- Service: `services/api_conclave/`

## Base URL / Port

Default port is **`8012`** (env: `CONCLAVE_PORT`).

## Endpoints (implemented)

Defined in `services/api_conclave/api/routes.py`:

- `GET /` — service info (observatory metadata)
- `POST /emit/{emission_channel}` — emit event to Redis Streams
- `GET /health` — Redis connectivity
- `GET /metrics` — Prometheus metrics

## Request/Response schemas

Pydantic models live in `services/api_conclave/models/schemas.py`.

Key request types:

- `EventPayload` (`data`, `emitter`)

## Service config env vars

Loaded in `services/api_conclave/config.py`:

- `CONCLAVE_PORT`
- `CONCLAVE_HOST`
- `LOG_LEVEL`
- `REDIS_HOST`
- `REDIS_PORT`
- `CONSUMER_GROUP`
- `CONSUMER_NAME`
