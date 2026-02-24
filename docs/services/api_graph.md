# api_graph — Graph Orchestration Service

> **Last updated**: Feb 23, 2026 18:00 UTC

## Overview

`api_graph` is the FastAPI service that exposes the LangGraph pipeline as an HTTP endpoint.
It is the **primary entry point** for synchronous user queries (Path B).

- **Port**: 9004 (default)
- **Main endpoint**: `POST /run`
- **Layer**: LIVELLO 2 (Service — orchestrates LIVELLO 1 pure domain logic)

## Architecture (v1.4.0)

```
POST /run  ──▶  routes.py
                   │
                   ▼
           graph_adapter.py
           ├─ _get_user_lock(user_id)      # per-user asyncio.Lock
           └─ asyncio.to_thread(            # non-blocking execution
                  run_graph_once(...)        # graph_runner.py
              )
                   │
                   ▼
           graph_runner.py
           ├─ _session_get(user_id)         # LRU cache (RAM, TTL 1h)
           ├─ PG recovery on miss           # conversations table
           ├─ graph.invoke(state)           # LangGraph compiled graph
           ├─ _session_put(user_id, state)  # LRU write-back
           └─ PG write-through              # conversations persist
                   │
                   ▼
           GraphResponseMin                 # channel-agnostic contract
           (human, follow_ups, session_min,
            orthodoxy_status, route_taken,
            correlation_id, as_of)
```

## Concurrency Model

| Mechanism | Purpose | Config |
|---|---|---|
| `asyncio.to_thread()` | Offloads blocking graph to worker thread | Built-in |
| Per-user `asyncio.Lock` | Serializes same-user requests (no race on shared state) | Max 2000 locks |
| Thread-safe LRU cache | Session state with lazy eviction | `SESSION_CACHE_MAX=1000`, `SESSION_CACHE_TTL=3600` |
| PG write-through | Durable session persistence | Automatic |

## Pipeline Paths

### Full path (complex intents)

```
parse → intent_detection → weaver → entity_resolver → babel_emotion
  → semantic_grounding → params_extraction → decide → [route]
  → output_normalizer → orthodoxy → vault → compose → can → [advisor] → END
```

### Early-exit path (v1.4.0 — simple intents)

```
parse → intent_detection → early_exit → END
```

Default early-exit intents: `greeting`, `farewell`, `thanks`, `chit_chat`, `smalltalk`, `goodbye`, `gratitude`.

Bypasses 14 nodes. Response time: < 1 s (vs 3-8 s full path).

## Response Contract: GraphResponseMin

Every response (full path or early-exit) is returned as `GraphResponseMin`:

```python
from contracts.graph_response import GraphResponseMin

# Fields:
#   human: str                    — render this
#   follow_ups: List[str]         — suggested prompts
#   orthodoxy_status: str         — blessed|purified|heretical|non_liquet|clarification_needed
#   route_taken: str              — llm_soft, dispatcher_exec, early_exit, …
#   correlation_id: str           — deterministic dedup key
#   as_of: datetime               — when facts were computed
#   session_min: SessionMin       — per-turn session snapshot
#   full_payload: Optional[Dict]  — debug/admin only
```

## Environment Variables

| Variable | Default | Effect |
|---|---|---|
| `INTENT_DOMAIN` | `generic` | Which domain intent registry to load |
| `ENTITY_DOMAIN` | `= INTENT_DOMAIN` | Which entity resolver to register |
| `EXEC_DOMAIN` | (none) | Which execution handler to register |
| `GRAPH_DOMAIN` | `= INTENT_DOMAIN` | Experimental: domain graph_nodes extension |
| `ENABLE_MINIMAL_GRAPH` | `false` | Use 4-node minimal graph |
| `USE_MCP` | `0` | Route dispatcher_exec to MCP node |
| `VSGS_ENABLED` | `0` | Enable semantic grounding |
| `EARLY_EXIT_INTENTS` | `greeting,farewell,thanks,chit_chat,smalltalk,goodbye,gratitude` | Override early-exit intents |
| `SESSION_CACHE_MAX` | `1000` | Max entries in LRU session cache |
| `SESSION_CACHE_TTL` | `3600` | Session TTL in seconds |

## Quick Verification

```bash
# Health check
curl -s http://127.0.0.1:9004/health | jq .

# Simple query (will hit early-exit)
curl -sS -X POST http://127.0.0.1:9004/run \
  -H "Content-Type: application/json" \
  -d '{"input_text":"hello","user_id":"test_user"}' | jq .human

# Complex query (full pipeline)
curl -sS -X POST http://127.0.0.1:9004/run \
  -H "Content-Type: application/json" \
  -d '{"input_text":"analyze european banks","user_id":"test_user"}' | jq .human

# Logs
docker logs --since 5m core_graph
```

## Key Files

| File | Purpose |
|---|---|
| `services/api_graph/main.py` | FastAPI bootstrap |
| `services/api_graph/api/routes.py` | HTTP endpoints |
| `services/api_graph/adapters/graph_adapter.py` | Orchestrator (asyncio.to_thread + per-user lock) |
| `services/api_graph/config.py` | Centralized env var reads |
| `vitruvyan_core/core/orchestration/langgraph/graph_flow.py` | StateGraph definition + wiring |
| `vitruvyan_core/core/orchestration/langgraph/graph_runner.py` | Graph execution + session management |
| `vitruvyan_core/core/orchestration/langgraph/node/early_exit_node.py` | Early-exit governance node |
| `vitruvyan_core/contracts/graph_response.py` | GraphResponseMin + SessionMin contracts |

## Version History

| Version | Date | Changes |
|---|---|---|
| v1.4.0 | Feb 23, 2026 | Early-exit node, GraphResponseMin contract, asyncio.to_thread, per-user lock, LRU session cache |
| v1.3.1 | Feb 23, 2026 | PG session persistence restored, session recovery on RAM miss |
| v1.0.8 | Feb 16, 2026 | LangGraph 1.0.8 upgrade |
