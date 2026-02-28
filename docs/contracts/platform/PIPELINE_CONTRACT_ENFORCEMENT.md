---
title: "Pipeline Contract Enforcement"
description: "Runtime enforcement for LangGraph node contracts via @enforced decorator"
---

# Pipeline Contract Enforcement

> **Last updated**: Feb 28, 2026 22:30 UTC

## Overview

Runtime contract enforcement for the LangGraph pipeline. The `@enforced` decorator validates that nodes receive required state fields and produce declared output fields.

**Problem solved**: The LangGraph pipeline (20 nodes, 19+ transitions) operated with zero runtime validation. `BaseGraphState` is `TypedDict(total=False)` — all fields optional, no enforcement. `NodeContract.required_fields` in `graph_engine.py` was declared but never verified.

## Components

| File | Lines | Role |
|------|-------|------|
| `core/orchestration/contract_enforcement.py` | ~190 | `@enforced` decorator, `ContractViolationError`, `NodeContractSpec` |
| `core/orchestration/node_contracts_registry.py` | ~260 | `NODE_CONTRACTS` dict — 20 nodes with verified requires/produces |
| `tests/unit/orchestration/test_contract_enforcement.py` | ~190 | 19 tests covering warn/strict/off modes |

## Usage

### Environment Variable

```bash
CONTRACT_ENFORCE_MODE=warn    # default — log WARNING on violation
CONTRACT_ENFORCE_MODE=strict  # raise ContractViolationError (staging/test)
CONTRACT_ENFORCE_MODE=off     # zero overhead — original function returned
```

### In build_graph() (FASE 3 — pending)

```python
from core.orchestration.contract_enforcement import enforced
from core.orchestration.node_contracts_registry import NODE_CONTRACTS

def _wrap(name, fn):
    c = NODE_CONTRACTS.get(name)
    if c:
        return enforced(requires=c.requires, produces=c.produces)(fn)
    return fn

# In build_graph():
g.add_node("parse", _wrap("parse", parse_node))
g.add_node("orthodoxy", _wrap("orthodoxy", orthodoxy_node))
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
