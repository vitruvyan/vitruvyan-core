# _legacy/ — Deprecated Memory Orders Files

> **These files are FROZEN. Do not modify.**  
> **Removal target**: After FASE 1-3 complete + services migrated to LIVELLO 1 consumers

---

## What's Here

| File | Lines | Purpose | Why Deprecated |
|------|-------|---------|----------------|
| `coherence.py` | 235 | Coherence check (PostgreSQL ↔ Qdrant) | Mixed I/O + business logic |
| `rag_health.py` | 277 | Multi-component RAG health check | Direct httpx calls inline |
| `phrase_sync.py` | 270 | Phrase synchronization logic | PostgresAgent/QdrantAgent in domain code |

**Total**: 782 lines of impure code

---

## Why Deprecated

These files violate **SACRED_ORDER_PATTERN** principles:

### Violations
1. **I/O in domain logic**: Instantiate `PostgresAgent()`, `QdrantAgent()` directly
2. **HTTP calls inline**: Use `httpx.get()` for Qdrant/Embedding API/Babel Gardens
3. **Not testable**: Cannot test without PostgreSQL/Qdrant/Redis running
4. **Mixed concerns**: Business logic (drift calculation) + infrastructure (DB queries)

### Example (coherence.py lines 75-76)
```python
pg = PostgresAgent()  # ❌ LIVELLO 2 dependency in LIVELLO 1
qdrant = QdrantAgent()  # ❌ I/O in domain logic
```

---

## Refactoring Strategy

### LIVELLO 1 (Pure Domain)
Extract **only** business logic to `consumers/`:
- `CoherenceAnalyzer` — drift calculation (pure math)
- `HealthAggregator` — component status aggregation (pure logic)
- `SyncPlanner` — sync operation planning (pure decision)

### LIVELLO 2 (Service Adapters)
Move **all** I/O to `services/api_memory_orders/adapters/persistence.py`:
- `get_postgres_count()` → PostgresAgent wrapper
- `get_qdrant_count()` → httpx wrapper
- `check_component_health()` → health check I/O
- `execute_sync_operations()` → mutation I/O

---

## Who Still Imports These

| File | Import Location | Migration Path |
|------|----------------|----------------|
| `rag_health.py` | `services/api_memory_orders/main.py:23` | Replace with `HealthAggregator` + `MemoryPersistence` |
| (all) | (none external) | Only main.py, safe to refactor |

---

## Removal Timeline

- **Feb 10, 2026**: Files moved to _legacy/ (FASE 0)
- **Feb 11, 2026**: LIVELLO 1 consumers created (FASE 1)
- **Feb 11, 2026**: LIVELLO 2 adapters created (FASE 2)
- **Feb 12, 2026**: main.py refactored (FASE 3)
- **Feb 13, 2026**: Tests pass, Docker rebuild successful
- **Feb 14, 2026**: _legacy/ files removed from codebase

---

**Created**: Feb 10, 2026  
**Status**: 🔒 FROZEN — DO NOT MODIFY  
**Removal**: After FASE 4 validation complete
