# consumers/

> **Pure decision engines. No side effects. No I/O.**

## Contract

All consumers MUST follow this contract:
- `process()` is PURE — same input → same output, deterministic
- NO side effects — no database writes, no HTTP calls, no file I/O
- NO infrastructure imports — no StreamBus, PostgresAgent, QdrantAgent, httpx
- Type enforcement at concrete level — ABC uses `Any`
- `can_handle()` for selective routing (optional, default True)

---

## Contents

| File | Description |
|------|-------------|
| `base.py` | MemoryRole ABC (base class for all Memory Orders consumers) |
| `coherence_analyzer.py` | Pure drift calculation logic (input: counts → output: CoherenceReport) |
| `health_aggregator.py` | Pure component health aggregation (input: ComponentHealth tuple → output: SystemHealth) |
| `sync_planner.py` | Pure  sync operation planning (input: SyncInput → output: SyncPlan) |

---

## Usage Pattern (Service Layer)

```python
from vitruvyan_core.core.governance.memory_orders.consumers import CoherenceAnalyzer
from vitruvyan_core.core.governance.memory_orders.domain import CoherenceInput
from vitruvyan_core.core.governance.memory_orders.governance import DEFAULT_THRESHOLDS

# Service adapter handles I/O
pg_count = persistence.get_postgres_count("entities", "embedded")
qdrant_count = persistence.get_qdrant_count("entities_embeddings")

# Consumer handles PURE logic
analyzer = CoherenceAnalyzer()
input_data = CoherenceInput(pg_count, qdrant_count, DEFAULT_THRESHOLDS.as_tuple())
report = analyzer.process(input_data)

# Service adapter emits event
bus.emit("memory.coherence.checked", report)
```

---

**Sacred Order**: Memory & Coherence  
**Layer**: Foundational (LIVELLO 1 — consumers)
