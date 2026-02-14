# Synaptic Conclave API

<p class="kb-subtitle">Servizio LIVELLO 2 che fa bridge HTTP → Redis Streams (observatory + emitter).</p>

## Location

- Service: `services/api_conclave/`

## Base URL / Port

Porta di default **`8012`** (env: `CONCLAVE_PORT`).

## Endpoints (implementati)

Definiti in `services/api_conclave/api/routes.py`:

- `GET /` — info servizio (observatory metadata)
- `POST /emit/{emission_channel}` — emette evento su Redis Streams
- `GET /health` — connettività Redis
- `GET /metrics` — metriche Prometheus

## Request/Response schemas

Modelli Pydantic in `services/api_conclave/models/schemas.py`.

Tipi principali:

- `EventPayload` (`data`, `emitter`)

## Env vars del servizio

Caricati in `services/api_conclave/config.py`:

- `CONCLAVE_PORT`
- `CONCLAVE_HOST`
- `LOG_LEVEL`
- `REDIS_HOST`
- `REDIS_PORT`
- `CONSUMER_GROUP`
- `CONSUMER_NAME`
