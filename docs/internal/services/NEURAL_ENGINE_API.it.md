# Neural Engine API

<p class="kb-subtitle">Servizio LIVELLO 2 per ranking e screening domain-agnostic.</p>

## Location

- Service: `services/api_neural_engine/`

## Base URL / Port

Porta di default **`8003`** (env: `PORT`).

## Endpoints (implementati)

Definiti in `services/api_neural_engine/api/routes.py`:

- `POST /screen` — screening multi-fattore
- `POST /rank` — ranking mono-fattore
- `GET /health` — health con dipendenze
- `GET /metrics` — metriche Prometheus
- `GET /profiles` — elenco profili

Root info:

- `GET /` (definito in `services/api_neural_engine/main.py`)

## Request/Response schemas

Modelli Pydantic in `services/api_neural_engine/schemas/api_models.py`.

Tipi principali:

- `ScreenRequest` (`profile`, `filters`, `top_k`, `stratification_mode`, `risk_tolerance`)
- `RankRequest` (`feature_name`, `entity_ids[]`, `top_k`, `higher_is_better`)

## Env vars del servizio

Caricati in `services/api_neural_engine/config.py`:

- `PORT`
- `LOG_LEVEL`
- `CORS_ORIGINS`
