# Vertical Technical Reference

> Status: canonical technical source for vertical implementation details  
> Scope: runtime wiring + contracts + status matrix (`ACTIVE`/`EXPERIMENTAL`/`PLANNED`)

## TOC

1. [Glossary](#glossary)
2. [End-to-end map](#end-to-end-map)
3. [Quick Start (minimal vertical)](#quick-start-minimal-vertical)
4. [Production file map (MUST/SHOULD)](#production-file-map-mustshould)
5. [Registration and wiring](#registration-and-wiring)
6. [Binding contracts and manifest](#binding-contracts-and-manifest)
7. [Sacred Orders status](#sacred-orders-status)
8. [Verticalization Matrix](#verticalization-matrix)
9. [Testing and conformance checklist](#testing-and-conformance-checklist)
10. [Troubleshooting](#troubleshooting)

## Glossary

- `vertical`: product/domain specialization package under `vitruvyan_core/domains/<domain>/`.
- `domain`: runtime label used by loaders (for example `finance`, `energy`, `security`).
- `plugin`: domain extension loaded without modifying core internals.
- `hook pattern`: extension via env var + dynamic import + registry call.
- `Sacred Orders`: cognitive/governance orders (Orthodoxy, Vault, Babel, Pattern Weavers, Codex, Neural).
- `LIVELLO 1`: pure domain logic, no I/O.
- `LIVELLO 2`: adapters/services, env/config/I/O wiring.

## End-to-end map

| Area | Domain-agnostic part | Domain-specific part | Where it lives | How it is loaded |
|---|---|---|---|---|
| Intent routing | `intent_detection_node` + `IntentRegistry` | `domains.<domain>.intent_config` + `create_<domain>_registry()` | `vitruvyan_core/core/orchestration/langgraph/` + `vitruvyan_core/domains/<domain>/` | Dynamic import in `vitruvyan_core/core/orchestration/langgraph/graph_flow.py` using `INTENT_DOMAIN` |
| Entity resolution | `entity_resolver_node` + `EntityResolverRegistry` | `domains.<domain>.entity_resolver_config.register_<domain>_entity_resolver()` | Same as above | Auto-registration in `graph_flow.py` through `ENTITY_DOMAIN` (registration); runtime execution uses `ENTITY_DOMAIN` in `entity_resolver_node.py` |
| Execution | `exec_node` + `ExecutionRegistry` | `domains.<domain>.execution_config.register_<domain>_execution_handler()` | `vitruvyan_core/core/orchestration/langgraph/node/exec_node.py` + domain package | `EXEC_DOMAIN` selects registry handler, but handler registration is manual at service startup |
| Graph node extension | Core graph pipeline in `build_graph()` | `domains.<domain>.graph_nodes/registry.py` factories | `vitruvyan_core/core/orchestration/langgraph/graph_flow.py` + domain package | Optional dynamic import through `GRAPH_DOMAIN` (defaults to `INTENT_DOMAIN`) |
| Governance | Orthodoxy default ruleset | `domains.<domain>.governance_rules.get_domain_rules()` | `vitruvyan_core/core/governance/orthodoxy_wardens/` + domain package | `GovernanceRuleRegistry.register_domain(domain)` dynamic import |
| Babel Gardens | Signal domain primitives + YAML loader | `signals_<domain>.yaml` + optional service plugin | `vitruvyan_core/core/cognitive/babel_gardens/` + `services/api_babel_gardens/plugins/` | `load_config_from_yaml(...)` exists; service-level domain plugin loading is manual |
| Pattern Weavers | Domain config objects + taxonomy support | Domain taxonomy YAML (`PATTERN_TAXONOMY_PATH`) | `vitruvyan_core/core/cognitive/pattern_weavers/domain/config.py` + `services/api_pattern_weavers/config.py` | Hook exists in config, but service startup does not inject `PatternConfig.from_env()` into domain config |
| Codex Hunters | Domain-agnostic consumers with `CodexConfig` | Domain pack YAML + normalizers + graph routing hook | `vitruvyan_core/core/governance/codex_hunters/` + `examples/verticals/finance/` | Domain pack is pattern/manual; no automatic service startup loader found |
| Neural Engine | `NeuralEngine` core + contracts | Domain `IDataProvider` + `IScoringStrategy` implementations | `vitruvyan_core/core/neural_engine/` + `vitruvyan_core/contracts/neural_engine/` | Service orchestrator currently initializes mock implementations; domain loader is TODO |

## Quick Start (minimal vertical)

Goal: enable only domain intents with minimum files.

### 1) Create minimal structure

```text
vitruvyan_core/domains/security/
  __init__.py
  intent_config.py
```

### 2) Implement `intent_config.py`

```python
from core.orchestration.intent_registry import IntentRegistry, IntentDefinition


def create_security_registry() -> IntentRegistry:
    registry = IntentRegistry(domain_name="security")
    registry.register_intent(IntentDefinition(
        name="threat",
        description="Threat analysis",
        examples=["analyze threat level"],
        route_type="exec",
    ))
    return registry
```

Optional (recommended):

- `CONTEXT_KEYWORDS`
- `AMBIGUOUS_PATTERNS`

`graph_flow.py` reads both when present.

### 3) Enable runtime

```bash
export INTENT_DOMAIN=security
```

Recommended explicit setup for consistency:

```bash
export ENTITY_DOMAIN=security
export EXEC_DOMAIN=security
```

### 4) Verify loading

- Start graph service (`services/api_graph`).
- Confirm no warning for missing `domains.security.intent_config`.
- Send a query matching your new intent and verify routing is no longer generic-only.

## Production file map (MUST/SHOULD)

### MUST (Vertical Contract V1)

- `intent_config.py`
- `README.md`
- `vertical_manifest.yaml`
- tests for contract conformance

Source: `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md`

### SHOULD (contract production baseline)

- `graph_plugin.py`
- `governance_rules.py`
- `slot_filler.py` (legacy in current core flow)
- `response_formatter.py`
- integration tests

Source: `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md`

### SHOULD (operational hooks currently used at runtime)

- `entity_resolver_config.py`
- `execution_config.py`
- `graph_nodes/registry.py` (optional graph extension hook)

These two files are part of current LangGraph hook pattern (`ENTITY_DOMAIN`, `EXEC_DOMAIN`), even if not listed in baseline SHOULD of the contract.

### Suggested layout

```text
vitruvyan_core/domains/<domain>/
  __init__.py
  README.md                        # MUST
  intent_config.py                 # MUST
  vertical_manifest.yaml           # MUST
  governance_rules.py              # SHOULD
  entity_resolver_config.py        # SHOULD (runtime hook)
  execution_config.py              # SHOULD (runtime hook)
  slot_filler.py                   # LEGACY (not in active core flow)
  response_formatter.py            # SHOULD
  graph_plugin.py                  # SHOULD / optional by architecture status
  tests/
```

## Registration and wiring

### Core nodes vs domain logic (normative clarification)

- `vitruvyan_core/core/orchestration/langgraph/node/` is for domain-agnostic core nodes.
- Domain-specific behavior must live in `vitruvyan_core/domains/<domain>/...`.
- In the current architecture, domain logic is attached to core nodes through hook modules and registries, not by editing core nodes per domain.

### INTENT_DOMAIN (`ACTIVE`)

- Loader: `vitruvyan_core/core/orchestration/langgraph/graph_flow.py`
- Dynamic import: `domains.<domain>.intent_config`
- Required factory: `create_<domain>_registry()`
- Fallback: generic registry if import/factory fails

### ENTITY_DOMAIN (`ACTIVE`, with caveat)

- Auto-registration in `graph_flow.py`:
  - imports `domains.<domain>.entity_resolver_config`
  - calls `register_<domain>_entity_resolver()`
- Runtime execution in `entity_resolver_node.py` reads `ENTITY_DOMAIN` directly.

Practical note:

- Even if registration defaults to `INTENT_DOMAIN` in `graph_flow.py`, resolver execution still depends on `ENTITY_DOMAIN` env in `entity_resolver_node.py`.
- Set `ENTITY_DOMAIN` explicitly to avoid silent passthrough.

### EXEC_DOMAIN (`EXPERIMENTAL`)

- `exec_node.py` uses `ExecutionRegistry` and `EXEC_DOMAIN`.
- Domain handler is not auto-imported by `graph_flow.py`.
- You must register handler at service startup.

Startup pattern (from `services/api_graph/README.md` and finance hook docs):

```python
import os
from domains.security.execution_config import register_security_execution_handler

if os.getenv("EXEC_DOMAIN") == "security":
    register_security_execution_handler()
```

### GRAPH_DOMAIN (`EXPERIMENTAL`)

- `graph_flow.py` optionally loads domain graph node packs from:
  - `domains.<domain>.graph_nodes.registry`
- env selector:
  - `GRAPH_DOMAIN` (defaults to `INTENT_DOMAIN`)
- required factory:
  - `get_<domain>_graph_nodes()`
- optional factories:
  - `get_<domain>_graph_edges()`
  - `get_<domain>_route_targets()`

Fallback behavior:

- if module/factories are missing, graph runs with core-only nodes/routes.

### Governance rules hook (`EXPERIMENTAL`)

- Registry: `vitruvyan_core/core/governance/orthodoxy_wardens/governance/rule_registry.py`
- Dynamic import path: `domains.<domain>.governance_rules`
- Required function: `get_domain_rules()`
- Domain example: `vitruvyan_core/domains/finance/governance_rules.py`

Current wiring gap:

- Default Orthodoxy service startup does not call `register_domain(...)`.
- `GOVERNANCE_DOMAIN` appears in docs/comments but no startup/runtime wiring was found.

## Binding contracts and manifest

### Contracts namespace

Use canonical contracts:

- `contracts` / `vitruvyan_core.contracts`

Do not introduce deprecated contract namespaces.

### Binding references

- `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md`
- `docs/contracts/verticals/VERTICAL_CONFORMANCE_CHECKLIST.md`
- `docs/contracts/verticals/templates/vertical_manifest.yaml`
- `docs/contracts/verticals/schema/vertical_manifest.schema.json`

### Manifest and compatibility

`vertical_manifest.yaml` is required for:

- contract conformance metadata
- update/compatibility checks
- ownership/governance traceability

Compatibility fields from template are consumed by update-manager flows (`min_core_version`, `max_core_version`, `contracts_major`, `update_channel`).

### Validation options

- Update-manager validator exists in repo:
  - `vitruvyan_core/core/platform/update_manager/ci/contract_validator.py`
- JSON schema file exists:
  - `docs/contracts/verticals/schema/vertical_manifest.schema.json`

No dedicated runtime/startup command was found in this repo that automatically validates vertical manifests against that JSON schema. Add explicit schema validation in CI if needed.

Practical caution (verified in-repo):

- template/schema vertical status uses `draft|active|deprecated`.
- update-manager `ContractValidator` currently accepts `active|deprecated|experimental`.

If CI uses update-manager validator, align manifest status with validator policy or update validator policy first.

## Sacred Orders status

Detailed per-order guide:

- `docs/knowledge_base/development/verticals/Vertical_Sacred_Orders.md`

Implementation status summary:

- Orthodoxy domain rules hook: implemented hook, startup wiring missing.
- Vault signal timeseries: adapter-level integration exists; dedicated HTTP endpoints are not exposed in current routes.
- Babel signals YAML + plugin pattern: primitives available, integration remains manual.
- Pattern taxonomy env hook: config hook exists, startup wiring missing.
- Codex domain pack: pattern exists, automatic loading not wired.
- Neural providers/strategies: contracts active, service domain loader TODO.

## Verticalization Matrix

| Extension point | File to create (path) | Env var / config | Loader / wiring | Status | Reference contract |
|---|---|---|---|---|---|
| Intent | `vitruvyan_core/domains/<domain>/intent_config.py` with `create_<domain>_registry()` | `INTENT_DOMAIN` | Dynamic import in `vitruvyan_core/core/orchestration/langgraph/graph_flow.py` | `ACTIVE` | `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md` |
| Entity | `vitruvyan_core/domains/<domain>/entity_resolver_config.py` with `register_<domain>_entity_resolver()` | `ENTITY_DOMAIN` | Auto-register in `graph_flow.py`, execute via `entity_resolver_node.py` + `EntityResolverRegistry` | `ACTIVE` (set `ENTITY_DOMAIN` explicitly) | `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md` |
| Exec | `vitruvyan_core/domains/<domain>/execution_config.py` with `register_<domain>_execution_handler()` | `EXEC_DOMAIN` | `exec_node.py` + `ExecutionRegistry`; manual startup registration in service | `EXPERIMENTAL` | `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md` |
| Graph Nodes | `vitruvyan_core/domains/<domain>/graph_nodes/registry.py` with `get_<domain>_graph_nodes()` | `GRAPH_DOMAIN` (default `INTENT_DOMAIN`) | Optional dynamic import in `graph_flow.py`; adds nodes/edges/route targets with safe fallback | `EXPERIMENTAL` | `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md` |
| Governance | `vitruvyan_core/domains/<domain>/governance_rules.py` with `get_domain_rules()` | (no wired env selector found) | `GovernanceRuleRegistry.register_domain(domain)` imports `domains.<domain>.governance_rules` | `EXPERIMENTAL` | `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md` |
| Babel | `signals_<domain>.yaml` (+ optional plugin in `services/api_babel_gardens/plugins/`) | plugin path/config path (manual) | `load_config_from_yaml(...)` in Babel domain layer; plugin loading remains manual | `EXPERIMENTAL` | `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md` |
| Pattern | taxonomy YAML + domain config injection | `PATTERN_TAXONOMY_PATH` | Hook exists in `PatternConfig.from_env()`, but service startup does not inject domain config | `PLANNED` | `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md` |
| Codex | domain pack files (for example `examples/verticals/<domain>/...`) + optional graph routing hook | config YAML via `CodexConfig.from_yaml(...)` (manual) | Core supports config objects; service/domain-pack auto-loading is not wired | `EXPERIMENTAL` | `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md` |
| Neural | domain `data_provider.py` + `scoring_strategy.py` implementing contracts | service/domain selector is TODO | `NeuralEngine(data_provider, scoring_strategy)` supports injection; API orchestrator initializes mock providers | `EXPERIMENTAL` | `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md` + `vitruvyan_core/contracts/neural_engine/` |

## Testing and conformance checklist

Use `tests/verticals/test_finance_vertical.py` as reference pattern.

Minimum gate:

- intent registry load test (`create_<domain>_registry()` import + call)
- conformance tests for required files
- manifest validation (schema + compatibility checks)

Recommended:

- graph integration test (intent -> route -> node)
- governance behavior test (domain rule hit/miss)
- negative tests (invalid env, missing factory, missing handler)

Checklist:

- `docs/contracts/verticals/VERTICAL_CONFORMANCE_CHECKLIST.md`

## Troubleshooting

### Dynamic import fails (`INTENT_DOMAIN` / `ENTITY_DOMAIN`)

- Check module path and naming:
  - `domains.<domain>.intent_config`
  - `create_<domain>_registry()`
  - `domains.<domain>.entity_resolver_config`
  - `register_<domain>_entity_resolver()`
- Ensure `domains` package is importable in runtime (`PYTHONPATH`/service import path).

### `EXEC_DOMAIN` has no effect

- `execution_config.py` is not auto-loaded.
- Register handler at service startup.
- Verify domain and supported intent in `ExecutionRegistry`.

### `GRAPH_DOMAIN` extension is not loaded

- Verify `domains.<domain>.graph_nodes.registry` import path.
- Verify required factory `get_<domain>_graph_nodes()`.
- Check that custom node names do not collide with core node names.

### Governance rules are not applied

- `GovernanceRuleRegistry` must be initialized.
- `register_domain("<domain>")` must be called.
- `Inquisitor` must receive the resulting `RuleSet`.

### Pattern taxonomy YAML is not loaded

- `PATTERN_TAXONOMY_PATH` alone is not sufficient.
- Service startup must build `PatternConfig.from_env()` and inject it with `set_config(...)` into pattern-weavers domain config.

### Babel signals YAML/plugin is not loaded

- `load_config_from_yaml(...)` is explicit.
- Service-level plugin integration is manual.
- Verify config path and plugin invocation in service adapter/module layer.
