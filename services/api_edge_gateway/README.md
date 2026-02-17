# Vitruvyan Edge Gateway (MVP)

Edge Gateway is the ingress/data-plane component for Intake interoperability.

## Goals

- Accept H2M/M2M intake requests on edge devices.
- Persist requests locally in SQLite outbox (offline-first).
- Relay to Core Intake API when connectivity is available.
- Replay pending requests deterministically after reconnect.

## Runtime Model

`Client -> Edge Gateway -> SQLite Outbox -> Core Intake API -> Redis Streams`

## Endpoints

- `POST /api/edge/intake`: enqueue intake envelope and attempt immediate relay.
- `POST /api/edge/replay`: replay pending envelopes.
- `GET /health`: local health + optional core reachability check.
- `GET /status`: queue depth and relay counters.
- `GET /metrics`: lightweight operational counters.

## Environment Variables

- `EDGE_OUTBOX_PATH` (default: `/tmp/vitruvyan_edge_outbox.db`)
- `CORE_INTAKE_BASE_URL` (default: `http://localhost:9050`)
- `EDGE_HTTP_TIMEOUT_SEC` (default: `10`)
- `EDGE_REPLAY_BATCH_SIZE` (default: `50`)
- `CORE_EDGE_API_TOKEN` (optional bearer token)

## Run

```bash
uvicorn services.api_edge_gateway.main:app --host 0.0.0.0 --port 9070
```

## Notes

- This module is intentionally transport-focused and pre-epistemic.
- Semantic enrichment remains downstream (Codex/Pattern/Memory layers).
- MCP remains control-plane only; this gateway is data-plane ingestion.
