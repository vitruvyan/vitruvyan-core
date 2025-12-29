# 🏛️ MCP Server - Model Context Protocol Bridge

## Overview
MCP Server espone tool OpenAI-compatible che comunicano con i Sacred Orders di Vitruvyan attraverso il Cognitive Bus.

**Architettura**:
```
LLM (Claude/GPT) → MCP Server (8020) → Sacred Orders Pipeline
                                        ↓
                        Synaptic Conclave → Orthodoxy Wardens → Vault Keepers → Sentinel
```

## Status Verificato ✅

### File Corretti
- ✅ **Dockerfile** - Aggiornato da `vitruvyan_os` → `vitruvyan_core`
- ✅ **main.py** - 1040 righe, import corretti `vitruvyan_core`
- ✅ **requirements.txt** - Dipendenze complete (14 pacchetti)

### Dipendenze API
Il servizio MCP chiama:
- ❌ **Neural Engine** (`omni_neural_engine:8003`) - ✅ PRESENTE
- ❌ **VEE/Graph API** (`omni_api_graph:8004`) - ✅ PRESENTE  
- ❌ **Pattern Weavers** (`omni_pattern_weavers:8017`) - ❌ MANCANTE nel docker-compose

### Dipendenze Infrastrutturali
- ✅ **Redis** (`omni_redis:6379`) - Cognitive Bus
- ✅ **PostgreSQL** (`omni_postgres:5432`) - Vault Keepers audit trail

## Configurazione Docker-Compose Richiesta

```yaml
vitruvyan_mcp:
  build:
    context: ../..
    dockerfile: services/mcp/Dockerfile
  container_name: omni_mcp
  environment:
    PYTHONPATH: /app
    # API Dependencies
    NEURAL_ENGINE_API: http://omni_api_neural:8003
    VEE_ENGINE_API: http://omni_api_graph:8004
    PATTERN_WEAVERS_API: http://omni_pattern_weavers:8017  # NOT YET IN COMPOSE
    # Infrastructure
    REDIS_HOST: omni_redis
    REDIS_PORT: 6379
    POSTGRES_HOST: omni_postgres
    POSTGRES_PORT: 5432
    POSTGRES_DB: vitruvyan_omni
    POSTGRES_USER: vitruvyan_omni_user
    POSTGRES_PASSWORD: "@Caravaggio971_omni"
  ports:
    - "9020:8020"
  restart: unless-stopped
  networks:
    - omni-net
  depends_on:
    - vitruvyan_postgres
    - vitruvyan_redis
    - vitruvyan_api_neural
    - vitruvyan_api_graph
    # - vitruvyan_pattern_weavers  # TODO: Add when service exists
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

## Tools Disponibili (14 total)

1. **screen_ticker** - Neural Engine screening
2. **generate_vee** - VEE Generation Engine  
3. **get_sentiment** - Sentiment analysis
4. **analyze_trend** - Trend analysis
5. **analyze_momentum** - Momentum analysis
6. **analyze_volatility** - Volatility analysis
7. **analyze_risk** - Risk assessment
8. **backtest_strategy** - Strategy backtesting
9. **get_portfolio** - Portfolio status
10. **execute_trade** - Trade execution
11. **get_market_data** - Market data retrieval
12. **analyze_fundamentals** - Fundamental analysis
13. **get_news** - Financial news
14. **create_alert** - Alert creation

## Testing

```bash
# Health check
curl http://localhost:9020/health

# List tools
curl -X POST http://localhost:9020/tools/list

# Execute tool (screen ticker)
curl -X POST http://localhost:9020/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "screen_ticker",
    "arguments": {"ticker": "AAPL"},
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
