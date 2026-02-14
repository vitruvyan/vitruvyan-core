# Neural Engine API

<p class="kb-subtitle">LIVELLO 2 service for domain-agnostic ranking and screening.</p>

## Location

- Service: `services/api_neural_engine/`

## Base URL / Port

Default port is **`8003`** (env: `PORT`).

## Endpoints (implemented)

Defined in `services/api_neural_engine/api/routes.py`:

- `POST /screen` — multi-factor screening
- `POST /rank` — single-factor ranking
- `GET /health` — dependency-aware health
- `GET /metrics` — Prometheus metrics
- `GET /profiles` — list scoring profiles

Root info:

- `GET /` (defined in `services/api_neural_engine/main.py`)

## Request/Response schemas

Pydantic models live in `services/api_neural_engine/schemas/api_models.py`.

Key request types:

- `ScreenRequest` (`profile`, `filters`, `top_k`, `stratification_mode`, `risk_tolerance`)
- `RankRequest` (`feature_name`, `entity_ids[]`, `top_k`, `higher_is_better`)

## Service config env vars

Loaded in `services/api_neural_engine/config.py`:

- `PORT`
- `LOG_LEVEL`
- `CORS_ORIGINS`
