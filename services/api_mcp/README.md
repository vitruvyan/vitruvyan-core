# MCP Server - Model Context Protocol Gateway

MCP is a stateless gateway that exposes function-calling tools and applies Sacred Orders governance to each execution.

Canonical docs: `docs/services/mcp.md`

## Runtime Modes

- `MCP_DOMAIN=generic` (default): domain-agnostic tool catalog.
- `MCP_DOMAIN=finance`: enables finance adapter (Vitruvyan-compatible aliases and args normalization).

Finance alias examples:

- `screen_tickers` -> `screen_entities`
- `compare_tickers` -> `compare_entities`
- `query_sentiment` -> `query_signals`

## API Endpoints

- `GET /tools` - Tool discovery (OpenAI function-calling schema)
- `POST /execute` - Execute tool + governance/audit pipeline
- `GET /health` - Service health
- `GET /metrics` - Prometheus metrics

Finance mode extra endpoints:

- `GET /v1/finance/config` - Active finance config and source candidates
- `GET /v1/finance/tools` - Finance-oriented tool catalog + executor names
- `POST /v1/finance/normalize` - Resolve alias tool/args to canonical request

## Core Environment Variables

- `PORT`, `LOG_LEVEL`, `MCP_DOMAIN`
- `REDIS_HOST`, `REDIS_PORT`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `LANGGRAPH_URL`/`LANGGRAPH_API`, `NEURAL_ENGINE_API`, `PATTERN_WEAVERS_API`
- `MCP_Z_THRESHOLD`, `MCP_COMPOSITE_THRESHOLD`, `MCP_MIN_SUMMARY_WORDS`, `MCP_MAX_SUMMARY_WORDS`, `MCP_FACTOR_KEYS`

Finance-specific:

- `MCP_FINANCE_EXPOSE_LEGACY_TOOLS` (default `true`)
- `MCP_FINANCE_SIGNAL_TABLE` (optional override)
- `MCP_FINANCE_SIGNAL_ENTITY_COLUMN` (optional override)

