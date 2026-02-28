---
title: "Pipeline Contract Enforcement"
description: "Runtime enforcement for LangGraph node contracts via @enforced decorator"
---

# Pipeline Contract Enforcement

> **Last updated**: Feb 28, 2026 23:00 UTC

## Overview

Runtime contract enforcement for the LangGraph pipeline. The `@enforced` decorator validates that nodes receive required state fields and produce declared output fields.

**Problem solved**: The LangGraph pipeline (20 nodes, 19+ transitions) operated with zero runtime validation. `BaseGraphState` is `TypedDict(total=False)` — all fields optional, no enforcement. `NodeContract.required_fields` in `graph_engine.py` was declared but never verified.

## Implementation Status (FASE 1-8)

| FASE | Description | Status |
|------|-------------|--------|
| 1 | `@enforced` decorator + `ContractViolationError` | DONE |
| 2 | `NODE_CONTRACTS` registry (20 nodes audited) | DONE |
| 3 | `_wrap()` in `build_graph()` + `build_minimal_graph()` | DONE |
| 4a | Orthodoxy canonical constants (`ORTHODOXY_BLESSED`, etc.) | DONE |
| 4 | codex_hunters orthodoxy fields (success/skip/error paths) | DONE |
| 4b | graph_adapter fallback `"blessed"` → `"non_liquet"` | DONE |
| 5 | Bus emit validation (opt-in) | DEFERRED |
| 6 | `_check_payload_contract` strict raise | DONE |
| 7 | `OntologyPayload.model_validate()` at pw_compile boundary | DONE |
| 8 | E2E architectural tests (21 tests) | DONE |

## Components

| File | Lines | Role |
|------|-------|------|
| `core/orchestration/contract_enforcement.py` | ~190 | `@enforced` decorator, `ContractViolationError`, `NodeContractSpec` |
| `core/orchestration/node_contracts_registry.py` | ~260 | `NODE_CONTRACTS` dict — 20 nodes with verified requires/produces |
| `core/orchestration/langgraph/graph_flow.py` | ~615 | `_wrap()` helper, all `add_node()` calls wrapped |
| `contracts/graph_response.py` | ~150 | `ORTHODOXY_*` canonical constants |
| `tests/unit/orchestration/test_contract_enforcement.py` | ~190 | 19 unit tests (warn/strict/off modes) |
| `tests/architectural/test_pipeline_contract_enforcement.py` | ~230 | 21 E2E tests (all BUCOs verified) |

## Usage

### Environment Variable

```bash
CONTRACT_ENFORCE_MODE=warn    # default — log WARNING on violation
CONTRACT_ENFORCE_MODE=strict  # raise ContractViolationError (staging/test)
CONTRACT_ENFORCE_MODE=off     # zero overhead — original function returned
```

### In build_graph() (FASE 3)

```python
from core.orchestration.contract_enforcement import enforced
from core.orchestration.node_contracts_registry import NODE_CONTRACTS

_NODE_ALIAS = {"llm_soft": "cached_llm", "intent": "intent_detection"}

def _wrap(name, fn):
    registry_key = _NODE_ALIAS.get(name, name)
    spec = NODE_CONTRACTS.get(registry_key)
    if spec and (spec.requires or spec.produces):
        return enforced(requires=spec.requires, produces=spec.produces, node_name=name)(fn)
    return fn

# In build_graph():
g.add_node("parse", _wrap("parse", parse_node))
g.add_node("orthodoxy", _wrap("orthodoxy", orthodoxy_node))
# Domain extension nodes also wrapped:
g.add_node(node_name, _wrap(node_name, node_handler))
```

### Domain Plugin Integration

```python
from core.orchestration.contract_enforcement import NodeContractSpec
from core.orchestration.node_contracts_registry import merge_domain_contracts

# In domains/<domain>/graph_nodes/registry.py:
def get_security_node_contracts():
    return {
        "security_scanner": NodeContractSpec(
            requires=["input_text"],
            produces=["scan_result", "threat_level"]
        )
    }
```

## Design Decisions

1. **Decorator, not Agent** — contracts are pure Python (no I/O). Agents wrap external systems.
2. **Applied in build_graph(), not in node files** — nodes are unaware of wrapping.
3. **Only critical requires** — fields using `.get(default)` are safe if missing, not listed.
4. **Only guaranteed produces** — conditional outputs not listed.
5. **LIVELLO 1 compliant** — no prometheus_client, no Redis, no I/O. Metric names are string constants only.

## Audit Findings (Feb 28, 2026)

Key corrections from the original roadmap (R2):

- **orthodoxy**: does NOT read `narrative` (reads `response`, `input_text`)
- **can**: does NOT read `narrative` (WRITES it)
- **All 20 nodes**: no critical requires — all use `.get()` with safe defaults
- **early_exit**: produces 10+ guaranteed fields, not 3

## BUCOs Resolved

| BUCO | Issue | Fix |
|------|-------|-----|
| 1 | `BaseGraphState` zero enforcement | `@enforced` via `_wrap()` on all 20 nodes |
| 2 | `pw_compile` raw dict → state | `OntologyPayload.model_validate()` at boundary |
| 3 | codex → END bypasses orthodoxy | Set orthodoxy fields on all 3 return paths |
| 4 | Bus `emit()` accepts raw dict | DEFERRED (opt-in, lower priority) |
| 5 | `_check_payload_contract` warn-only | `raise ValueError` in strict mode |
| 6 | graph_adapter `"blessed"` fallback | Changed to `"non_liquet"` + warning log |
| 7 | Domain nodes unwrapped | `_wrap()` applied in domain extension loop |
