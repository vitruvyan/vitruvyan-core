# Graph Orchestrator API (`api_graph`)

LangGraph HTTP orchestrator service (request-response pattern).

## Scope

`api_graph` is not a Sacred Order listener.

- no `streams_listener.py`
- no bus emit/consume loop for primary flow
- synchronous HTTP orchestration over LangGraph

## Runtime Responsibilities

- Execute graph requests through `run_graph_once(...)` / `run_graph(...)`
- Expose health and Prometheus metrics
- Expose auxiliary read APIs (entity search, semantic clusters)
- Optionally wrap execution with graph audit monitor

Core files:

- `services/api_graph/main.py`
- `services/api_graph/api/routes.py`
- `services/api_graph/adapters/graph_adapter.py`
- `services/api_graph/adapters/persistence.py`

## Endpoint Map

Execution:

- `POST /run`
- `POST /dispatch`
- `POST /graph/dispatch`

Health/metrics:

- `GET /health`
- `GET /metrics`
- `GET /pg/health`
- `GET /qdrant/health`

Audit endpoints:

- `GET /audit/graph/health`
- `GET /audit/graph/metrics`
- `POST /audit/graph/trigger`
- `POST /audit/grafana/webhook`

Query helpers:

- `GET /clusters/semantic`
- `GET /api/entity_ids/search?q=<term>`

## Request/Response Contracts

Primary input (`/run`):

```json
{
  "input_text": "hello",
  "user_id": "demo",
  "validated_tickers": ["AAPL"],
  "language": "en"
}
```

Adapter output is normalized to `GraphResponseMin` (contract), while keeping legacy keys (`json`, `human`, `audit_monitored`, `execution_timestamp`) for backward compatibility.

## Current LangGraph Behavior (v1.4+)

- Early-exit path for conversational intents is active.
- Slot-template gating is not part of active core flow.
- Routing uses intent registry + route node configuration.
- Domain behavior is attached via hook pattern (`INTENT_DOMAIN`, `ENTITY_DOMAIN`, `EXEC_DOMAIN`, `GRAPH_DOMAIN`).

## Domain Wiring

Typical env setup:

```bash
export INTENT_DOMAIN=<domain>
export ENTITY_DOMAIN=<domain>
export EXEC_DOMAIN=<domain>
export GRAPH_DOMAIN=<domain>
```

`EXEC_DOMAIN` note:

- `exec_node` reads `EXEC_DOMAIN`, but domain handler registration is startup-time responsibility.

## Concurrency Model

`GraphOrchestrationAdapter` applies:

- `asyncio.to_thread(...)` for blocking graph execution
- per-user `asyncio.Lock` to serialize concurrent requests of the same user

This prevents same-user race conditions while allowing cross-user parallelism.

## Local Run

```bash
export PYTHONPATH=$(pwd)
uvicorn services.api_graph.main:app --reload --port 8004
```

Quick check:

```bash
curl -s http://localhost:8004/health | jq
curl -s -X POST http://localhost:8004/run \
  -H "Content-Type: application/json" \
  -d '{"input_text":"hello","user_id":"demo"}' | jq
```

## Related Docs

- Orchestration core: `vitruvyan_core/core/orchestration/README.md`
- Vertical orchestration guide: `docs/knowledge_base/development/verticals/Vertical_Orchestration_LangGraph.md`
- Slot-filling alignment note: `vitruvyan_core/core/orchestration/langgraph/docs/SLOT_FILLING_ARCHITECTURE_ALIGNMENT.md`
