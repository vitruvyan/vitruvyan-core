# Finance Domain Configuration — Hook Pattern Examples

> **Created**: February 14, 2026  
> **Status**: Example implementations (not auto-loaded)  
> **Pattern**: Domain-specific plugin registration for entity resolution and execution

---

## Overview

This directory contains **example** domain-specific configurations for the finance vertical.

These files demonstrate the **hook pattern** architecture introduced in Phase 1 refactoring:
- Core remains domain-agnostic with graceful fallback stubs
- Domains register specific logic via registry pattern
- Configuration loaded conditionally via environment variables

---

## Files

| File | Purpose | Registry | Env Var |
|------|---------|----------|---------|
| `entity_resolver_config.py` | Ticker → company resolution | `EntityResolverRegistry` | `ENTITY_DOMAIN=finance` |
| `execution_config.py` | Neural Engine ranking | `ExecutionRegistry` | `EXEC_DOMAIN=finance` |
| `intent_config.py` | Finance intent definitions | `IntentRegistry` | `INTENT_DOMAIN=finance` |

---

## Usage Pattern

### 1. Entity Resolver (ticker → company)

**Registration** (in `services/api_graph/main.py`):
```python
import os
from domains.finance.entity_resolver_config import register_finance_entity_resolver

if os.getenv("ENTITY_DOMAIN") == "finance":
    register_finance_entity_resolver()
```

**Environment**:
```bash
export ENTITY_DOMAIN=finance
```

**Behavior**:
- **With registration**: `entity_resolver_node` calls `finance_entity_resolver()`
- **Without registration**: graceful passthrough stub (preserves `entity_ids`)

---

### 2. Execution Handler (Neural Engine)

**Registration** (in `services/api_graph/main.py`):
```python
import os
from domains.finance.execution_config import register_finance_execution_handler

if os.getenv("EXEC_DOMAIN") == "finance":
    register_finance_execution_handler()
```

**Environment**:
```bash
export EXEC_DOMAIN=finance
```

**Behavior**:
- **With registration**: `exec_node` calls `finance_execution_handler()` (Neural Engine ranking)
- **Without registration**: fake success stub (empty results)

---

### 3. Intent Detection (finance intents)

**Registration** (in `services/api_graph/main.py` — ALREADY IMPLEMENTED):
```python
import os
from domains.finance.intent_config import create_finance_registry

intent_domain = os.getenv("INTENT_DOMAIN", "finance")
if intent_domain == "finance":
    registry = create_finance_registry()
    intent_detection_node.configure(registry)
```

**Environment**:
```bash
export INTENT_DOMAIN=finance  # Current default
```

**Behavior**:
- **With registration**: Finance intents (trend, momentum, risk, etc.)
- **Without registration**: Core intents only (soft, unknown)

---

## Architecture Philosophy

**Two-Level Separation**:
1. **LIVELLO 1** (Core): Domain-agnostic nodes with registry hooks + graceful fallback
2. **Domain Plugin**: Registers specific logic via registry pattern

**Guarantees**:
- ✅ Core never hardcodes domain assumptions
- ✅ Missing plugin = graceful degradation (stub behavior)
- ✅ Zero breaking changes when switching domains
- ✅ Testable in isolation (no I/O in LIVELLO 1)

**Registry Pattern** (inspired by `intent_detection_node.py`):
- Singleton registry (`get_entity_resolver_registry()`, `get_execution_registry()`)
- Dataclass definitions (`EntityResolverDefinition`, `ExecutionHandlerDefinition`)
- Conditional registration via environment variables
- Domain-specific handler functions (pure Python, delegate to services for I/O)

---

## Testing

**Stub behavior** (no domain):
```bash
cd /home/vitruvyan/vitruvyan-core
PYTHONPATH=vitruvyan_core python3 << 'EOF'
from core.orchestration.langgraph.node.entity_resolver_node import entity_resolver_node
from core.orchestration.langgraph.node.exec_node import exec_node

state = {"entity_ids": ["AAPL"], "intent": "trend"}

# Should passthrough with flow=direct
result1 = entity_resolver_node(state.copy())
print(f"entity_resolver (stub): flow={result1.get('flow')}")

# Should return fake success with empty ranking
result2 = exec_node(state.copy())
print(f"exec_node (stub): ok={result2.get('ok')}, ranking={len(result2['raw_output']['ranking'])}")
EOF
```

**Domain behavior** (with finance registration):
```bash
ENTITY_DOMAIN=finance EXEC_DOMAIN=finance PYTHONPATH=vitruvyan_core python3 << 'EOF'
from domains.finance.entity_resolver_config import register_finance_entity_resolver
from domains.finance.execution_config import register_finance_execution_handler
from core.orchestration.langgraph.node.entity_resolver_node import entity_resolver_node
from core.orchestration.langgraph.node.exec_node import exec_node

# Register domain handlers
register_finance_entity_resolver()
register_finance_execution_handler()

state = {"entity_ids": ["AAPL"], "intent": "trend"}

# Should execute finance resolver
result1 = entity_resolver_node(state.copy())
print(f"entity_resolver (finance): resolved={len(result1.get('resolved_entities', []))}")

# Should execute finance handler (Neural Engine stub)
result2 = exec_node(state.copy())
print(f"exec_node (finance): ranking={len(result2['raw_output']['ranking'])}")
EOF
```

---

## Migration Notes

**From old hardcoded approach** (Phase 1C and earlier):
- ❌ **Before**: `exec_node.py` directly imported Neural Engine
- ✅ **After**: `exec_node.py` uses `ExecutionRegistry`, finance plugin registers handler

**Backwards compatibility**:
- Stub behavior matches previous domain-neutral behavior (passthrough/fake success)
- No breaking changes to state flow or routing logic
- Existing tests continue to work (stub = previous behavior)

**Future domains** (logistics, healthcare, etc.):
1. Create `domains/<domain>/entity_resolver_config.py`
2. Create `domains/<domain>/execution_config.py`
3. Register via `ENTITY_DOMAIN=<domain>` and `EXEC_DOMAIN=<domain>`
4. No changes needed to core nodes

---

## Status: EXAMPLE ONLY

⚠️ **These files are NOT auto-loaded** in the current implementation.

To enable finance domain handlers:
1. Uncomment registration calls in `services/api_graph/main.py`
2. Set environment variables (`ENTITY_DOMAIN=finance`, `EXEC_DOMAIN=finance`)
3. Restart api_graph service

Current behavior (as of Feb 14, 2026):
- `INTENT_DOMAIN=generic` → default (core intents only)
- `INTENT_DOMAIN=finance` → **ACTIVE** (finance intents loaded)
- `ENTITY_DOMAIN=finance` → **DISABLED** (stub passthrough)
- `EXEC_DOMAIN=finance` → **DISABLED** (fake success stub)

---

**Last updated**: February 15, 2026
