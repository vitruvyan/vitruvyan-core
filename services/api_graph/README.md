# Graph Orchestrator API (`api_graph`)

**LangGraph orchestration service with domain-agnostic architecture**  
Pattern: **Orchestrator** (request-response HTTP, NOT event-driven)

---

## Overview

The Graph Orchestrator is Vitruvyan's conversational intelligence layer, powered by LangGraph. It routes user intents through a multi-node graph, performs slot filling, entity resolution, and generates domain-specific responses.

**Key Characteristics:**
- **Sync orchestration**: HTTP request → graph execution → JSON response
- **Domain-agnostic core**: Finance is a plugin, not hardcoded
- **Audit monitoring**: Optional execution tracking
- **Dependency injection**: Clean adapter pattern

---

## Architecture

### Service Structure (LIVELLO 2)

```
services/api_graph/
├── main.py                    # FastAPI bootstrap (86 lines)
├── config.py                  # Environment variables (54 lines)
├── adapters/
│   ├── graph_adapter.py       # Graph orchestration (130 lines)
│   └── persistence.py         # PostgreSQL queries (177 lines)
├── api/
│   └── routes.py              # 16 endpoints (428 lines)
├── models/
│   └── schemas.py             # Pydantic models (66 lines)
├── monitoring/
│   └── health.py              # Prometheus metrics (146 lines)
└── examples/                  # E2E test scripts
```

**Pattern**: Orchestrator (NO `streams_listener.py`, NO event emission)

---

## Core Integration

The service orchestrates **domain-agnostic LangGraph** from `vitruvyan_core/core/orchestration/`:

```python
from core.orchestration.langgraph.graph_runner import run_graph_once, run_graph
```

**Graph Flow:**
1. **Intent parsing** → Classify user request
2. **Slot filling** → Ask clarifying questions (if needed)
3. **Entity resolution** → Match entities to database
4. **Domain logic** → Execute business rules (via plugins)
5. **Response composition** → Format result (verdict, gauge, comparison)

---

## Endpoints

### Health & Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service status, version, audit state |
| `/metrics` | GET | Prometheus metrics (10+ counters/histograms) |

### Graph Execution

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/run` | POST | Main endpoint: `{input_text, user_id}` → graph result |
| `/graph/dispatch` | POST | With audit monitoring wrapper |
| `/dispatch` | POST | Backward compatibility (no audit) |

### Audit Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/audit/graph/health` | GET | Monitoring session status |
| `/audit/graph/metrics` | GET | Performance metrics |
| `/audit/graph/trigger` | POST | Manual audit trigger |
| `/audit/grafana/webhook` | POST | Grafana alert receiver |

### Data Queries

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/clusters/semantic` | GET | Documentation semantic clusters |
| `/api/entity_ids/search?q=` | GET | Entity fuzzy search (autocomplete) |

### Persistence Health

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/pg/health` | GET | PostgreSQL placeholder |
| `/qdrant/health` | GET | Qdrant placeholder |

---

## Configuration

### Environment Variables

```bash
# Service
SERVICE_NAME=api_graph
SERVICE_VERSION=2.0.0
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8004
LOG_LEVEL=INFO

# CORS (7 origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,https://*.vercel.app,...

# PostgreSQL
POSTGRES_HOST=core_postgres
POSTGRES_PORT=5432
POSTGRES_DB=vitruvyan_core
POSTGRES_USER=vitruvyan_core_user
POSTGRES_PASSWORD=<secret>

# Redis
REDIS_URL=redis://core_redis:6379

# Audit
AUDIT_ENABLED=false
DEFAULT_USER_ID=demo
GRAPH_TIMEOUT_SECONDS=30
```

---

## Adapters

### Graph Adapter (`adapters/graph_adapter.py`)

**Responsibility**: Orchestrate LangGraph execution (NO event emission)

```python
class GraphOrchestrationAdapter:
    async def execute_graph(input_text: str, user_id: str) -> Dict:
        """Execute graph with optional audit monitoring"""
        
    def execute_graph_dispatch(payload: dict) -> Dict:
        """Execute graph with raw payload (no audit)"""
        
    async def execute_graph_with_audit(payload: dict) -> Dict:
        """Execute graph with explicit audit wrapper"""
```

**Pattern**: Request-response (NOT event-driven, NO bus emission)

### Persistence Adapter (`adapters/persistence.py`)

**Responsibility**: PostgreSQL queries wrapper

```python
class GraphPersistence:
    def get_semantic_clusters() -> Dict:
        """SELECT FROM semantic_clusters ORDER BY n_points DESC"""
        
    def search_entities(query: str, limit: int) -> Dict:
        """Fuzzy ILIKE search on entity_ids (match_score 0.3-1.0)"""
```

---

## Prometheus Metrics

**10 metrics** exposed at `/metrics`:

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `graph_requests_total` | Counter | route, method, status | Total requests |
| `graph_failures_total` | Counter | route, error_type | Failed requests |
| `graph_request_duration_seconds` | Histogram | route, method | Request latency (0.1-60s) |
| `graph_execution_duration_seconds` | Histogram | graph_type | Graph execution time (0.5-80s) |
| `api_requests_inflight` | Gauge | - | Concurrent requests |
| ~~`crew_agent_latency_seconds`~~ | ~~Histogram~~ | ~~agent_type~~ | ~~CrewAI agent execution~~ (deprecated) |
| `graph_node_executions_total` | Counter | node_name, status | Node executions |

**Middleware**: `prometheus_middleware` tracks all HTTP requests (auto-labels, error tracking)

---

## Example Usage

### Basic Execution

```bash
curl -X POST http://localhost:9004/run \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "Should I invest in Apple?",
    "user_id": "demo"
  }'
```

**Response:**
```json
{
  "json": "{\"intent\":\"investment_verdict\",\"entities\":[\"AAPL\"],\"verdict\":\"BUY\"}",
  "human": "Leonardo: Based on fundamentals, Apple is a strong buy.",
  "audit_monitored": true,
  "execution_timestamp": "2026-02-10T15:30:45.123456"
}
```

### Entity Search

```bash
curl "http://localhost:9004/api/entity_ids/search?q=app"
```

**Response:**
```json
{
  "status": "success",
  "query": "app",
  "results": [
    {"entity_id": "AAPL", "name": "Apple Inc.", "sector": "Technology", "match_score": 1.0},
    {"entity_id": "A", "name": "Agilent Technologies", "sector": "Healthcare", "match_score": 0.7}
  ],
  "total": 2
}
```

### Health Check

```bash
curl http://localhost:9004/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "api_graph",
  "version": "2.0.0",
  "audit_monitoring": "disabled",
  "heartbeat_count": 0,
  "last_heartbeat": "N/A"
}
```

---

## Deployment

### Docker

```bash
cd infrastructure/docker
docker compose build graph
docker compose up -d graph
```

**Container**: `core_graph`  
**Port**: `9004:8004`  
**Network**: `vitruvyan_core_net`

### Health Verification

```bash
docker logs core_graph --tail=20
curl http://localhost:9004/health
```

---

## Testing

See [`examples/`](./examples/) directory for E2E test scripts:

- `test_health.py` — Basic connectivity
- `test_graph_simple.py` — Single intent execution
- `test_graph_slots.py` — Slot filling dialogue
- `test_entity_search.py` — Entity autocomplete
- `test_audit.py` — Audit monitoring
- `test_e2e_pipeline.py` — Full conversational flow

**Run tests:**
```bash
cd services/api_graph/examples
pip install -r requirements.txt
pytest -v
```

---

## Pattern: Orchestrator vs Sacred Orders

| Aspect | Sacred Orders | **Graph Orchestrator** |
|--------|---------------|------------------------|
| Communication | Redis Streams events | **HTTP REST** |
| Nature | Async, event-driven | **Sync, request-response** |
| `streams_listener.py` | ✅ Required | **❌ Not needed** |
| Adapter | `bus_adapter.py` (emit/consume) | **`graph_adapter.py` (sync)** |
| Called by | Events (`vault.archive.requested`) | **HTTP (`POST /run`)** |
| Returns | Emits event (`vault.archive.completed`) | **JSON response direct** |

**Example Orchestrators**: `api_graph`, `api_neural_engine`  
**Example Sacred Orders**: `api_memory_orders`, `api_vault_keepers`, `api_orthodoxy_wardens`

---

## Domain-Agnostic Architecture

LangGraph core is **domain-agnostic**. Finance is a **plugin**, not hardcoded:

```python
# Core orchestration (domain-agnostic)
from core.orchestration.langgraph.graph_engine import GraphEngine
from core.orchestration.intent_registry import IntentRegistry

# Finance plugin (domain-specific)
from domains.finance.finance_plugin import FinancePlugin

# Register plugin
registry = IntentRegistry()
registry.register_plugin(FinancePlugin())
```

**Benefits:**
- ✅ Add new domains (logistics, healthcare, legal) without touching core
- ✅ Swap plugins at runtime (A/B testing)
- ✅ Test core orchestration independently

---

## Development

### Local Setup

```bash
# Install dependencies
pip install -r infrastructure/docker/requirements/requirements-graph.txt

# Set environment
export PYTHONPATH=$(pwd)
export POSTGRES_HOST=localhost
export POSTGRES_PORT=9432
export REDIS_URL=redis://localhost:9379

# Run service
uvicorn api_graph.main:app --reload --port 8004
```

### Debug Mode

```bash
# Enable audit monitoring
export AUDIT_ENABLED=true

# Increase log verbosity
export LOG_LEVEL=DEBUG

# Longer graph timeout
export GRAPH_TIMEOUT_SECONDS=60
```

---

## Related Documentation

- **Core Orchestration**: [`vitruvyan_core/core/orchestration/README.md`](../../vitruvyan_core/core/orchestration/README.md)
- **LangGraph Refactoring**: [`.github/Vitruvyan_Appendix_J_LangGraph_Executive_Summary.md`](../../.github/Vitruvyan_Appendix_J_LangGraph_Executive_Summary.md)
- **Domain Contracts**: [`vitruvyan_core/domains/`](../../vitruvyan_core/domains/)
- **Sacred Orders Pattern**: [`.github/copilot-instructions.md`](../../.github/copilot-instructions.md#sacred-orders-refactoring)

---

## Changelog

**v2.0.0** (Feb 10, 2026)
- ✅ SACRED_ORDER_PATTERN conformance (0% → 95%)
- ✅ main.py: 581 → 86 lines (-85%)
- ✅ Created LIVELLO 2 structure (adapters, api, models, monitoring)
- ✅ 16 endpoints with dependency injection
- ✅ 10 Prometheus metrics
- ✅ Orchestrator pattern (NO streams_listener)

**v1.0.5** (Jan 2026)
- Initial monolithic implementation (581-line main.py)
- Audit monitoring integration
- Leonardo graph execution

---

## License

Proprietary — Vitruvyan Core Team
