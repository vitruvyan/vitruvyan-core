# Vertical Orchestration (LangGraph)

> Focus: runtime wiring through env vars + dynamic import + registries  
> Canonical matrix/status: `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`

## TOC

1. [Simple mental model](#simple-mental-model)
2. [INTENT_DOMAIN](#intent_domain)
3. [ENTITY_DOMAIN](#entity_domain)
4. [EXEC_DOMAIN](#exec_domain)
5. [GRAPH_DOMAIN (`graph_nodes` hook)](#graph_domain-graph_nodes-hook)
6. [Where to implement domain nodes](#where-to-implement-domain-nodes)
7. [Full activation checklist](#full-activation-checklist)
8. [GraphPlugin status](#graphplugin-status)

## Simple mental model

There are three concrete hooks in current orchestration:

1. `INTENT_DOMAIN` selects which intent registry to load.
2. `ENTITY_DOMAIN` selects which entity resolver to register/use.
3. `EXEC_DOMAIN` selects which execution handler to call.

Core remains unchanged; you only add a domain package and service startup wiring.

## INTENT_DOMAIN

Loader:

- `vitruvyan_core/core/orchestration/langgraph/graph_flow.py`

Behavior:

- imports `domains.<domain>.intent_config`
- expects `create_<domain>_registry()`
- configures `intent_detection_node` and `route_node`
- falls back to generic registry if import/factory fails

Status:

- `ACTIVE`

## ENTITY_DOMAIN

Loader/registration:

- `graph_flow.py` imports `domains.<domain>.entity_resolver_config`
- calls `register_<domain>_entity_resolver()`

Execution point:

- `vitruvyan_core/core/orchestration/langgraph/node/entity_resolver_node.py`
- uses `ENTITY_DOMAIN` + `EntityResolverRegistry`

Status:

- `ACTIVE`

Practical note:

- set `ENTITY_DOMAIN` explicitly.
- registration in `graph_flow.py` can default to `INTENT_DOMAIN`, but runtime resolver selection reads `ENTITY_DOMAIN` directly.

## EXEC_DOMAIN

Execution point:

- `vitruvyan_core/core/orchestration/langgraph/node/exec_node.py`
- uses `ExecutionRegistry` + `EXEC_DOMAIN`

Current wiring:

- handler is not auto-loaded by `graph_flow.py`
- handler registration must happen at service startup (documented in `services/api_graph/README.md`)

Status:

- `EXPERIMENTAL` (hook exists, manual startup wiring required)

Startup pattern:

```python
import os
from domains.<domain>.execution_config import register_<domain>_execution_handler

if os.getenv("EXEC_DOMAIN") == "<domain>":
    register_<domain>_execution_handler()
```

## GRAPH_DOMAIN (`graph_nodes` hook)

Loader:

- `vitruvyan_core/core/orchestration/langgraph/graph_flow.py`
- env var: `GRAPH_DOMAIN` (defaults to `INTENT_DOMAIN`)

Expected module contract:

- module: `domains.<domain>.graph_nodes.registry`
- required factory:
  - `get_<domain>_graph_nodes() -> Dict[str, Callable]`
- optional factories:
  - `get_<domain>_graph_edges() -> List[Tuple[str, str]]`
  - `get_<domain>_route_targets() -> Dict[str, str]`

Behavior:

- if module/factory is missing, graph uses core-only nodes/routes (safe fallback)
- extension cannot override existing core node names

Status:

- `EXPERIMENTAL`

## Where to implement domain nodes

Current contract-first rule in this repo:

- core graph nodes in `vitruvyan_core/core/orchestration/langgraph/node/` stay domain-agnostic.
- domain behavior is implemented under `vitruvyan_core/domains/<domain>/...`.
- core nodes (`intent_detection_node`, `entity_resolver_node`, `exec_node`) call domain logic through hook/registry wiring.

Only add or change files under `core/.../langgraph/node/` when the behavior is generic for all domains.

## Full activation checklist

```bash
export INTENT_DOMAIN=<domain>
export ENTITY_DOMAIN=<domain>
export EXEC_DOMAIN=<domain>
```

Then:

1. register execution handler in service startup.
2. restart `api_graph`.
3. verify logs: no unexpected generic fallback.

## Early-Exit Integration (v1.4.0)

Since v1.4.0, `graph_flow.py` includes a **conditional edge** after `intent_detection`:

- If `is_early_exit(state)` evaluates to True, the graph routes to `early_exit` → `END`, bypassing 14 downstream nodes.
- **Default intents**: `greeting`, `farewell`, `thanks`, `chit_chat`, `smalltalk`, `goodbye`, `gratitude`.
- **Domain override**: set `EARLY_EXIT_INTENTS` env var (comma-separated) to customize which intents take the fast path.

**Implications for verticals**:
- Domain plugins registered via `INTENT_DOMAIN` produce intent names. If a domain defines custom greeting-like intents, add them to `EARLY_EXIT_INTENTS`.
- The `early_exit` node is a core node (domain-agnostic). It uses `LLMAgent` for response generation and sets `orthodoxy_status=blessed`.
- Route hooks, entity resolvers, and execution handlers are NOT invoked on the early-exit path.

**Response contract**: All responses (including early-exit) are returned as `GraphResponseMin` (`vitruvyan_core/contracts/graph_response.py`), providing channel-agnostic `human` + `follow_ups` + `session_min`.

## GraphPlugin status

`graph_plugin.py` exists as a domain pattern (finance example), but current `graph_flow.py` does not include a global auto-loader for full `GraphPlugin` contracts.

Current operational status:

- `PLANNED/EXPERIMENTAL` for global automatic `GraphPlugin` loading.
- use concrete hooks now: `INTENT_DOMAIN`, `ENTITY_DOMAIN`, `EXEC_DOMAIN`, `GRAPH_DOMAIN` (`graph_nodes` extension).
