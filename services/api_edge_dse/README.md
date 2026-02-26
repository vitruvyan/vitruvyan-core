# DSE Edge Service — `api_edge_dse`

> **Last updated**: Feb 26, 2026 15:00 UTC

**LIVELLO 2**: Service layer for Design Space Exploration.  
Wraps `infrastructure/edge/dse/` (LIVELLO 1) with FastAPI + StreamBus + PostgresAgent.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/run_dse` | Execute DSE (stateless pure compute) |
| `POST` | `/dse/prepare` | Generate design points from Pattern Weavers context |
| `POST` | `/dse/log_rejection` | Log Conclave governance rejection |
| `GET`  | `/health` | Service health |
| `GET`  | `/metrics` | Prometheus metrics |

---

## Port: `8021`

---

## Structure (SERVICE_PATTERN conformant)

```
services/api_edge_dse/
├── main.py             # 76 lines — FastAPI bootstrap only
├── config.py           # All os.getenv() centralized
├── adapters/
│   ├── bus_adapter.py  # Orchestrates LIVELLO 1 + StreamBus
│   └── persistence.py  # ONLY I/O point (PostgresAgent)
├── api/
│   └── routes.py       # Thin HTTP endpoints
├── models/
│   └── schemas.py      # Pydantic request/response
├── monitoring/
│   └── health.py       # Prometheus metrics
├── streams_listener.py # Redis Streams consumer
├── Dockerfile
├── requirements.txt
└── _legacy/            # Pre-refactoring archive
```

---

## Quick start

```bash
# Build
docker build -f services/api_edge_dse/Dockerfile -t vitruvyan/api_edge_dse .

# Run
docker run -p 8021:8021 \
  -e REDIS_HOST=core_redis \
  -e POSTGRES_HOST=core_postgres \
  vitruvyan/api_edge_dse

# Health check
curl http://localhost:8021/health
```

---

## Environment Variables

See `config.py` for full list. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DSE_API_PORT` | `8021` | HTTP port |
| `DSE_DEFAULT_SEED` | `42` | Reproducibility seed |
| `DSE_DEFAULT_NUM_SAMPLES` | `50` | LHS sample count |
| `REDIS_HOST` | `core_redis` | StreamBus host |
| `POSTGRES_HOST` | `core_postgres` | PostgresAgent host |
