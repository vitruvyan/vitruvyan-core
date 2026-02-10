# Memory Orders — Charter

> **Dual-Memory Coherence System**  
> Sacred Order responsible for epistemic integrity between Archivarium (relational) and Mnemosyne (semantic).

---

## Identity

**Memory Orders** is the Sacred Order that maintains coherence between two complementary memory systems:

- **Archivarium**: PostgreSQL (relational, structured, transactional)
- **Mnemosyne**: Qdrant (vector, semantic, similarity-based)

Together, these systems form the **dual-memory architecture** that powers Vitruvyan's RAG (Retrieval-Augmented Generation) capabilities.

---

## Mandate

### Primary Responsibilities

1. **Monitor Coherence**
   - Continuously track drift between PostgreSQL record counts and Qdrant point counts
   - Calculate drift percentage: `|pg_count - qdrant_count| / max(pg_count, qdrant_count)` × 100
   - Classify drift status: `healthy` (<5%), `warning` (5-15%), `critical` (>15%)

2. **Aggregate Health**
   - Collect health status from all RAG components:
     - PostgreSQL (Archivarium)
     - Qdrant (Mnemosyne)
     - Embedding API (semantic processing)
     - Babel Gardens (linguistic fusion)
     - Redis (Cognitive Bus)
   - Determine overall system health: `healthy`, `degraded`, or `critical`

3. **Plan Synchronization**
   - Analyze discrepancies between dual-memory systems
   - Generate sync plans: `incremental` (only missing/modified) or `full` (rebuild)
   - Estimate execution duration and resource requirements

4. **Emit Events**
   - Publish coherence checks, health status, and sync operations to Cognitive Bus
   - Enable other Sacred Orders to react to memory state changes
   - Maintain audit trail of all operations

---

## Invariants

These constraints MUST NEVER be violated:

### 1. Read-Only Coherence Checks
Coherence analysis MUST be read-only operations. Consumers analyze data but NEVER mutate it.

**Rationale**: Analysis should not affect the systems being analyzed. Mutations are delegated to sync operations.

### 2. Pure Domain Logic
All business logic in LIVELLO 1 MUST be pure functions:
- No database connections
- No HTTP calls
- No file I/O
- Deterministic (same input → same output)

**Rationale**: Testability, predictability, portability. Domain logic can run anywhere without infrastructure.

### 3. Configurable Thresholds
Drift thresholds MUST be configurable, not hardcoded.

Default thresholds:
- `healthy`: < 5%
- `warning`: 5-15%
- `critical`: > 15%

Alternative presets: `STRICT_THRESHOLDS`, `RELAXED_THRESHOLDS`.

**Rationale**: Different deployment environments have different tolerance levels.

### 4. Event Emission
All operations (coherence checks, health checks, sync operations) MUST emit events to Cognitive Bus.

Channels:
- `memory.coherence.checked`
- `memory.health.checked`
- `memory.sync.completed`
- `memory.audit.recorded`

**Rationale**: Observability, traceability, inter-order coordination.

### 5. Audit Trail
All operations MUST be recorded in `memory_audit_log` table with:
- Operation type (`coherence_check`, `health_check`, `sync`)
- Timestamp (UTC)
- Status (`completed`, `failed`)
- Metadata (drift percentage, component statuses, operation counts)

**Rationale**: Governance, debugging, compliance.

### 6. Immutable Domain Objects
All domain objects MUST be frozen dataclasses (`@dataclass(frozen=True)`).

Collections MUST use `tuple`, not `list`.

**Rationale**: Prevents accidental mutations, enables caching, simplifies reasoning.

---

## Constraints

### Performance
- Coherence checks MUST complete in < 500ms (normal operation)
- Health checks MUST complete in < 1s (includes HTTP calls to external services)
- Sync planning MUST be non-blocking (generates plan, execution delegated)

### Scalability
- System MUST handle 1M+ records in PostgreSQL
- System MUST handle 1M+ points in Qdrant
- Drift calculation MUST work with empty collections (edge case: both systems empty → 0% drift)

### Error Handling
- Component failures MUST NOT crash health aggregator
- Failed health checks MUST return `degraded` or `critical`, never crash
- Sync plan generation MUST validate input data before processing

---

## Architectural Decisions

### Why Two Memory Systems?

**Archivarium (PostgreSQL)**:
- Exact matching, structured queries
- Transactional integrity
- Relational joins
- Historical tracking

**Mnemosyne (Qdrant)**:
- Semantic similarity search
- Fuzzy matching
- Embedding-based retrieval
- High-dimensional vector operations

**Together**: Complementary strengths. PostgreSQL for precision, Qdrant for recall.

### Why Separate Coherence from Sync?

**Coherence**: Analysis (read-only, pure logic)  
**Sync**: Execution (write operations, state mutations)

**Rationale**: Separation of concerns. Analysis can run continuously without risk. Execution is controlled, audited, and reversible.

### Why Event-Driven?

**Rationale**: 
- Decouples Memory Orders from consumers (Orchestrator, Neural Engine, UI)
- Enables reactive patterns (e.g., auto-sync on critical drift)
- Provides audit trail automatically
- Scales horizontally (multiple listeners)

---

## Integration Points

### Consumes Events
- `memory.coherence.requested` → Trigger coherence check
- `memory.health.requested` → Trigger health check
- `memory.sync.requested` → Trigger sync operation

### Publishes Events
- `memory.coherence.checked` → Coherence report available
- `memory.health.checked` → Health report available
- `memory.sync.completed` → Sync operation finished
- `memory.audit.recorded` → Audit record persisted

### Database Tables
- `memory_audit_log` → Audit trail of all operations
- `memory_sync_history` → Historical sync operations

### External Dependencies
- **PostgreSQL** (via PostgresAgent)
- **Qdrant** (via QdrantAgent)
- **Redis** (via StreamBus)
- **Embedding API** (for health checks, via httpx)
- **Babel Gardens** (for health checks, via httpx)

---

## Evolution Timeline

| Date | Milestone |
|------|-----------|
| **Pre-Feb 2026** | Monolithic implementation in `services/api_memory_orders/main.py` (414 lines) |
| **Feb 10, 2026** | FASE 0: Legacy files moved to `_legacy/` |
| **Feb 10, 2026** | FASE 1: LIVELLO 1 structure created (domain, consumers, governance, events, monitoring, philosophy) |
| **Feb 11, 2026** | FASE 2: LIVELLO 2 adapters created (bus_adapter, persistence, routes, config) |
| **Feb 12, 2026** | FASE 3: main.py reduced to < 100 lines |
| **Feb 13, 2026** | FASE 4: Tests pass, Docker rebuild successful |
| **Future** | AI-powered drift prediction, auto-sync policies, multi-region coherence |

---

**Created**: Feb 10, 2026  
**Sacred Order**: Memory & Coherence  
**Layer**: Foundational (LIVELLO 1)  
**Status**: ✅ Charter Ratified
