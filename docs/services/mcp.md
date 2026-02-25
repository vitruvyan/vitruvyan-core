# MCP Gateway (Model Context Protocol)

Il servizio **MCP** è un **gateway stateless** che espone un set di tool “function-calling” e applica una catena di governance/audit (Sacred Orders) a ogni esecuzione.

## Runtime mode

- `MCP_DOMAIN=generic` (default): catalogo tool agnostico.
- `MCP_DOMAIN=finance`: abilita adapter finance (alias compatibili Vitruvyan come `screen_tickers`, `compare_tickers`, `query_sentiment`).

## Scopo (domain-agnostic)

- Fornire un endpoint per **scoprire** i tool disponibili (`GET /tools`).
- Fornire un endpoint per **eseguire** un tool (`POST /execute`) e:
  - emettere un evento sul bus (Synaptic Conclave / Redis),
  - applicare validazioni minime (Orthodoxy Wardens),
  - archiviare input+output per audit (Vault Keepers / PostgreSQL),
  - esportare metriche (Prometheus).

## Non-scope (importante)

- Non è un orchestratore di flussi: l’orchestrazione deve restare altrove (es. LangGraph o equivalente).
- Non contiene logica di dominio: **il catalogo tool e i relativi executor sono vertical-specific**.

> Nota: l’implementazione corrente include alcuni tool con terminologia e dataset legati a una vertical precedente. In vitruvyan-core vanno trattati come **placeholder/migrazione**, non come contratto canonico.

## API

- `GET /` descrizione servizio + link agli endpoint
- `GET /health` healthcheck (include stato Redis)
- `GET /tools` ritorna gli schema tool in formato compatibile “OpenAI function calling”
- `POST /execute` esegue un tool con audit/validazione
- `GET /metrics` metriche Prometheus

Finance mode (`MCP_DOMAIN=finance`) aggiunge:

- `GET /v1/finance/config`
- `GET /v1/finance/tools`
- `POST /v1/finance/normalize`

## Configurazione (env)

Minime:

- `REDIS_HOST`, `REDIS_PORT` (bus/eventing)
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` (audit store via `PostgresAgent`)

Dipendenze esterne (tipicamente vertical-specific):

- `LANGGRAPH_URL` / `LANGGRAPH_API` (backend di esecuzione tool/orchestrazione)
- `NEURAL_ENGINE_API`, `VEE_ENGINE_API`, `PATTERN_WEAVERS_API` (se usati dagli executor attivi)

## Eventing (Redis)

Per ogni esecuzione tool, pubblica su `conclave.mcp.actions` un payload con:

- `conclave_id`
- `tool`, `args`
- `user_id`
- `timestamp`

## Audit (PostgreSQL)

Archivia ogni chiamata tool nella tabella `mcp_tool_calls` (schema definito dal vertical/deployment), includendo:

- `conclave_id`, `tool_name`, `args`, `result`, `orthodoxy_status`, `user_id`, `created_at`

## Observability (Prometheus)

Espone contatori/istogrammi per:

- volume richieste per tool e status
- durata esecuzione per tool
- outcome delle validazioni Orthodoxy

## Come aggiungere un tool (workflow)

1. Definisci lo schema in `services/api_mcp/schemas/tools.py`.
2. Implementa l’executor async in `services/api_mcp/tools/`.
3. Registra/normalizza in `services/api_mcp/tools/__init__.py`.
4. (Opzionale) aggiungi regole di validazione specifiche in `services/api_mcp/middleware.py`.
5. Aggiorna (se serve) le migrazioni DB per audit.
