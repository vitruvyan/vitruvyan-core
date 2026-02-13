# TODO: Service Conformance → 100%

> **Created**: February 13, 2026  
> **Status**: 🔴 Not started  
> **Priority**: Medium  
> **Context**: Post legacy-elimination cleanup (Feb 13, 2026)

---

## Current State

9/11 services at **100%** SACRED_ORDER_PATTERN conformance.  
2 services remaining:

| Service | Current | Missing | Target |
|---------|---------|---------|--------|
| **api_babel_gardens** | 75% | `api/routes.py` (canonical), `monitoring/` | 100% |
| **api_graph** | 88% | `adapters/bus_adapter.py` | 100% |

---

## Action Items

### 1. api_babel_gardens → 100%

**Missing: `api/routes.py`**
- Extract route definitions from `main.py` into `api/routes.py`
- main.py should only do `app.include_router(routes.router)`
- Follow pattern from api_mcp, api_neural_engine

**Missing: `monitoring/`**
- Create `monitoring/__init__.py` with Prometheus metric declarations
- Create `monitoring/health.py` with health check router
- Follow pattern from api_embedding, api_mcp

**Estimated effort**: ~1 hour

### 2. api_graph → 100%

**Missing: `adapters/bus_adapter.py`**
- Create `adapters/bus_adapter.py` with GraphBusAdapter class
- Wrap StreamBus event emission for graph execution events
- Follow pattern from api_embedding, api_mcp bus adapters

**Estimated effort**: ~30 min

---

## Verification

After each fix, run:

```bash
# Check structure
for d in services/api_*/; do
  echo "=== $(basename $d) ==="
  ls "$d"/{main.py,config.py,adapters/bus_adapter.py,adapters/persistence.py,api/routes.py,monitoring/} 2>&1
  wc -l < "$d/main.py" 2>/dev/null
  echo ""
done
```

Expected: all 11 services pass, all main.py < 100 lines.

---

## Reference

Conformant services (use as templates):
- `api_embedding` — simplest adapter pattern
- `api_mcp` — metrics extraction pattern
- `api_neural_engine` — main.py refactoring (386→83L)
