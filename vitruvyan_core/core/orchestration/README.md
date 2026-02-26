# Orchestration Layer (`core/orchestration`)

> Last updated: February 26, 2026

Domain-agnostic orchestration based on LangGraph, with runtime hooks for vertical behavior.

## Runtime Path (Current)

Main request flow:

1. `services/api_graph` receives HTTP request.
2. `GraphOrchestrationAdapter` calls `run_graph_once(...)`.
3. `run_graph_once(...)` executes compiled graph from `graph_flow.py`.
4. Final output is transformed to `GraphResponseMin` (+ legacy API keys for compatibility).

Core runtime files:

- `vitruvyan_core/core/orchestration/langgraph/graph_flow.py`
- `vitruvyan_core/core/orchestration/langgraph/graph_runner.py`
- `services/api_graph/adapters/graph_adapter.py`
- `vitruvyan_core/contracts/graph_response.py`

## Active Graph Pipeline (`build_graph`)

The default graph includes:

- `parse`
- `intent_detection`
- `early_exit` (conditional)
- `weaver`
- `entity_resolver`
- `babel_emotion`
- `semantic_grounding`
- `params_extraction`
- `decide`
- routed branch:
  - `exec`
  - `qdrant`
  - `llm_soft`
  - `llm_mcp` (when MCP routing is active)
  - `codex_hunters` (maintenance path)
- post-routing chain:
  - `output_normalizer`
  - `orthodoxy`
  - `vault`
  - `compose`
  - `can`
  - conditional `advisor`

Important runtime behavior:

- Early exit is active for conversational intents (v1.4.0+).
- Route decision is registry-driven (`IntentRegistry` + `route_node` configuration).
- `codex_hunters` has dedicated conditional terminal behavior.

## Domain Hook Pattern

Current production hooks are env-driven dynamic imports:

- `INTENT_DOMAIN` -> `domains.<domain>.intent_config.create_<domain>_registry()`
- `ENTITY_DOMAIN` -> `domains.<domain>.entity_resolver_config.register_<domain>_entity_resolver()`
- `EXEC_DOMAIN` -> `ExecutionRegistry` selection in `exec_node` (handler registration is startup-time)
- `GRAPH_DOMAIN` -> optional `domains.<domain>.graph_nodes.registry` extension pack

Reference KB guide:

- `docs/knowledge_base/development/verticals/Vertical_Orchestration_LangGraph.md`

## Slot Filling Status

Slot-filling templates are not part of the active core orchestration path.

- Current policy is LLM-first + semantic clarification.
- MCP/tool contracts provide structured validation when needed.
- Legacy slot-filling docs are kept as archival engineering context only (not part of KB navigation).

## GraphPlugin Status

`GraphPlugin` and `GraphEngine` contracts exist in `graph_engine.py`.

Current state:

- useful as domain extension contract
- global auto-loading into `graph_flow.py` is not the active runtime default
- active runtime extension today is the hook pattern (`INTENT_DOMAIN`/`ENTITY_DOMAIN`/`EXEC_DOMAIN`/`GRAPH_DOMAIN`)

## Related Modules

- Intent registry: `vitruvyan_core/core/orchestration/intent_registry.py`
- Execution registry: `vitruvyan_core/core/orchestration/execution_registry.py`
- Entity resolver registry: `vitruvyan_core/core/orchestration/entity_resolver_registry.py`
- Base state: `vitruvyan_core/core/orchestration/base_state.py`
- Compose helpers (legacy + reusable): `vitruvyan_core/core/orchestration/compose/`

## Ops Quick Checks

```bash
# Graph service health
curl -s http://localhost:9004/health | jq

# Run a graph request
curl -s -X POST http://localhost:9004/run \
  -H "Content-Type: application/json" \
  -d '{"input_text":"hello","user_id":"demo"}' | jq
```
