# Edge Oculus Prime API Service

Runtime Oculus Prime API service following LIVELLO 2 service structure.

## Scope

- Exposes HTTP endpoints for `infrastructure/edge/oculus_prime/core` agents.
- Persists immutable Evidence Packs in PostgreSQL.
- Emits canonical `oculus_prime.evidence.created` via Redis Streams.
- Supports versioned migration with legacy alias `intake.evidence.created`.
- Uses `adapters/persistence.py` as service-side I/O point for read models.

## Event migration mode

- `OCULUS_PRIME_EVENT_MIGRATION_MODE=dual_write` (default): emit both channels.
- `OCULUS_PRIME_EVENT_MIGRATION_MODE=v2_only`: emit only canonical channel.
- `OCULUS_PRIME_EVENT_MIGRATION_MODE=v1_only`: rollback mode (legacy only).

## Run (local)

```bash
uvicorn services.api_edge_oculus_prime.main:app --host 0.0.0.0 --port 8050
```

## Build

```bash
docker build -f services/api_edge_oculus_prime/Dockerfile -t vitruvyan_edge_oculus_prime:latest .
```
