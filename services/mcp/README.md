# 🏛️ MCP Server — Model Context Protocol Gateway

MCP è un **gateway stateless** che espone tool in formato “function-calling” e applica una pipeline di governance/audit (Sacred Orders) a ogni esecuzione.

Documentazione canonica (vitruvyan-core): `docs/services/mcp.md`

## Architettura (alto livello)

```
LLM → MCP (8020) → tool executor (vertical-specific)
              ↓
 Redis bus (event) → Orthodoxy (validate) → Postgres (audit)
```

## Endpoints

- `GET /tools` — discovery tool schemas
- `POST /execute` — execute tool + governance/audit
- `GET /health` — healthcheck
- `GET /metrics` — Prometheus metrics

## Configurazione (env)

Infrastruttura:

- `REDIS_HOST`, `REDIS_PORT`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

Dipendenze esterne (se usate dagli executor attivi):

- `LANGGRAPH_URL` / `LANGGRAPH_API`
- `NEURAL_ENGINE_API`, `VEE_ENGINE_API`, `PATTERN_WEAVERS_API`

## Nota sulla neutralità di dominio

Il catalogo tool e i relativi executor **devono essere definiti dal vertical**. Se vedi tool con terminologia legata a un dominio specifico, considerali **placeholder/migrazione**.

## Esempio docker-compose (minimo)

```yaml
vitruvyan_mcp:
  build:
    context: ../..
    dockerfile: services/mcp/Dockerfile
  environment:
    PYTHONPATH: /app
    REDIS_HOST: omni_redis
    REDIS_PORT: 6379
    POSTGRES_HOST: omni_postgres
    POSTGRES_PORT: 5432
    POSTGRES_DB: vitruvyan
    POSTGRES_USER: vitruvyan
    POSTGRES_PASSWORD: vitruvyan
  ports:
    - "9020:8020"
  restart: unless-stopped
  networks:
    - omni-net
  depends_on:
    - vitruvyan_postgres
    - vitruvyan_redis
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8020/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Schema PostgreSQL Required

```sql
-- Migration: 001_mcp_tool_calls.sql
CREATE TABLE IF NOT EXISTS mcp_tool_calls (
    id SERIAL PRIMARY KEY,
    conclave_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    args JSONB NOT NULL,
    result JSONB NOT NULL,
    orthodoxy_status TEXT NOT NULL,
    user_id TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mcp_conclave_id ON mcp_tool_calls(conclave_id);
CREATE INDEX idx_mcp_tool_name ON mcp_tool_calls(tool_name);
CREATE INDEX idx_mcp_created_at ON mcp_tool_calls(created_at DESC);
```

## Endpoints

- **POST /tools/list** - Lista tool disponibili (OpenAI format)
- **POST /tools/execute** - Esegue tool con Sacred Orders pipeline
- **GET /health** - Health check
- **GET /metrics** - Prometheus metrics

## Testing

```bash
# Health check
curl http://localhost:9020/health

# List tools
curl -X POST http://localhost:9020/tools/list

# Execute tool (screen entity_id)
curl -X POST http://localhost:9020/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "screen_ticker",
    "arguments": {"entity_id": "EXAMPLE_ENTITY_1"},
    "user_id": "test_user"
  }'
```

## Blockers per Deployment

1. ❌ **Pattern Weavers** service non presente in docker-compose
   - Opzioni:
     a. Commentare dipendenza (service opzionale)
     b. Creare servizio Pattern Weavers
     c. Mock endpoint in MCP per fallback graceful

2. ✅ **Schema PostgreSQL** - Verifica che migration `001_mcp_tool_calls.sql` sia applicata

## Note

- Porta host: **9020** (mapped da container 8020)
- Il servizio NON è mai stato aggiunto al docker-compose originale
- Codice completo e funzionante, ready for deployment
- Prometheus metrics integrate per monitoring
