# Appendix L — Synaptic Conclave: The Cognitive Bus
**Status**: ✅ PRODUCTION READY (Redis Streams Architecture — Domain-Agnostic Core)
**Last Updated**: February 11, 2026 (Domain-Agnostic Refactoring Documentation)

---

## Executive Summary

**Synaptic Conclave** (also known as the **Cognitive Bus**) is Vitruvyan's distributed event backbone — a Redis Streams-based neural substrate that enables asynchronous, durable, and causally-linked communication between Sacred Orders services.

### The Big Picture

Vitruvyan's architecture is inspired by two biological systems:
1. **Octopus Neural System**: 2/3 of neurons in arms (local autonomy), 1/3 in brain (minimal governance)
2. **Fungal Mycelial Networks**: No central processor, emergent routing, topological resilience

The Cognitive Bus implements this philosophy at the infrastructure level: **services communicate through events, not through direct calls**. This creates a system where:
- Each Sacred Order operates autonomously
- Coordination emerges from event chains, not orchestration
- Failures are localized, not cascading
- Every decision is traceable to its causal ancestry

---

## Architecture Principles

### 1. Bio-Inspired Distributed Cognition

**Traditional Architecture** (Centralized):
```
User → API Gateway → Orchestrator → Service A → Service B → Service C → Response
```
**Problem**: Single point of failure. If orchestrator dies, system dies.

**Vitruvyan Architecture** (Mycelial):
```
User → LangGraph → Cognitive Bus (Redis Streams) → Services (consume at own pace)
                        ↓
                  Event History (7 days)
                        ↓
                  Vault Keepers (immutable audit trail)
```
**Benefit**: No single point of failure. Services can restart, catch up, replay events.

---

### 2. The Socratic System

> **"The only true wisdom is in knowing you know nothing."** — Socrates

Vitruvyan is designed to **declare uncertainty explicitly**, not hallucinate confidence. The Cognitive Bus enforces this through architectural constraints:

**4 Sacred Invariants** (Enforced at Code Level):
1. ❌ **No Payload Inspection**: Bus NEVER looks inside event payloads (semantically blind)
2. ❌ **No Correlation Logic**: Bus NEVER correlates events (no "smart routing")
3. ❌ **No Semantic Routing**: Bus routes by namespace only (no content-based decisions)
4. ❌ **No Synthesis**: Bus NEVER combines/transforms events (pure transport)

**Why This Matters**: By limiting the bus to "dumb" transport, we prevent it from making decisions disguised as infrastructure. Intelligence belongs in consumers, not in the network.

---

## Technical Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRODUCER SERVICE                            │
│  (e.g., LangGraph, Neural Engine, Pattern Weavers)                 │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ emit(channel, payload)
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       HERALD (Event Emitter)                        │
│  • Converts CognitiveEvent → TransportEvent                        │
│  • Adds trace_id, causation_id (parent event reference)            │
│  • Serializes to JSON                                              │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ XADD stream:channel payload
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   REDIS STREAMS (Cognitive Bus)                     │
│  • Durable storage (7-day TTL via MAXLEN)                          │
│  • Consumer groups (load balancing across replicas)                │
│  • Pending Entries List (automatic retry on failure)               │
│  • Causal event chains (parent_id → event_id linkage)              │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ XREADGROUP group:consumer stream
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    SCRIBE (Event Consumer)                          │
│  • Reads from streams (blocking, async)                            │
│  • Deserializes TransportEvent → CognitiveEvent                    │
│  • Routes to BaseConsumer.process()                                │
│  • Sends ACK (XACK) if successful, NACK if failed                  │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ process(event)
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      CONSUMER SERVICE                               │
│  (e.g., Vault Keepers, Orthodoxy Wardens, Memory Orders)           │
│  • Process event locally (octopus-style autonomy)                  │
│  • Optional: emit child events (mycelial propagation)              │
│  • Optional: record outcome for learning (plasticity)              │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 2-Layer Event Model

**Layer 1: TransportEvent** (Bus Level, Immutable)
```python
@dataclass(frozen=True)  # Cannot mutate after creation
class TransportEvent:
    stream: str               # "vitruvyan:domain:intent"
    event_id: str             # Redis-assigned "1737734400000-0"
    emitter: str              # Source service name
    payload: Dict[str, Any]   # OPAQUE to bus (JSON serializable)
    timestamp: str            # ISO 8601 UTC
    correlation_id: Optional[str]  # External session ID
```

**Layer 2: CognitiveEvent** (Consumer Level, Mutable)
```python
@dataclass  # Mutable (consumers can add metadata)
class CognitiveEvent:
    id: str                    # UUID
    type: str                  # "memory.write.requested"
    payload: Dict[str, Any]    # Semantic content
    trace_id: str              # Full conversation chain ID
    causation_id: Optional[str]  # Parent event ID (causal chain)
    timestamp: datetime
    metadata: Dict[str, Any]   # Consumer-added context
```

**Key Insight**: Bus operates on TransportEvent (dumb). Consumers operate on CognitiveEvent (semantic). This separation enforces the invariants.

---

## Current Production Status (Jan 24, 2026)

### ✅ What's Working

1. **Redis Streams Infrastructure**:
   - Master: `vitruvyan_redis_master` (role:master, 3 replicas)
   - Streams: `stream:memory.write.requested`, `stream:memory.read.requested`, `stream:memory.vector.match.requested`
   - Consumer Groups: `group:memory_orders`, `group:babel_gardens`, `group:codex_hunters`, `group:vault_keepers`
   - All services connected to master (write access working)

2. **4 Listeners Migrated** (from legacy Pub/Sub):
   - Vault Keepers Listener ✅ (5 channels)
   - Memory Orders Listener ✅ (6 channels)
   - Babel Gardens Listener ✅ (3 channels)
   - Codex Hunters Listener ✅ (4 channels)

3. **Working Memory System** (Phase 4):
   - Distributed memory per consumer (isolated namespaces)
   - Mycelial sharing (opt-in via events, no direct access)
   - Memory Inspector API (port 8024) for debugging
   - TTL support (auto-expiration)

4. **Plasticity System** (Phase 6):
   - Bounded parameter adaptation (min/max/step constraints)
   - Auditable adjustments (every change logged as event)
   - Reversible rollback (exact state restoration)
   - Outcome tracking (PostgreSQL-backed success rate analysis)
   - Learning loop (7-day lookback, daily adaptation)

---

### ⚠️ What's Missing (In Progress)

1. **Metrics Layer** (CRITICAL - 7 hours implementation):
   - Dashboard exists (20 panels), but 80% show "No data"
   - Application metrics not implemented:
     - `cognitive_bus_events_total{channel, status}`
     - `herald_broadcast_total{channel, status}`
     - `scribe_write_total{stream, status}`
     - `listener_consumed_total{stream, consumer, status}`
   - Redis Streams metrics not exposed by redis_exporter:
     - `redis_stream_length{stream}`
     - `redis_stream_lag{stream, group}`
   - **Action Plan**: `COGNITIVE_BUS_METRICS_STATUS.md` (3 phases, 7 hours)

2. **Remaining Listener Migrations** (9/13 services):
   - ⏳ Orthodoxy Wardens (CRITICAL)
   - ⏳ Pattern Weavers
   - ⏳ Neural Engine (CRITICAL)
   - ⏳ LangGraph (CRITICAL)
   - ⏳ VEE Engine
   - ⏳ MCP Server
   - ⏳ Portfolio Architects
   - ⏳ CAN Node
   - ⏳ Sentiment Node

3. **Phase 7: Integration & Vertical Binding** (50% complete):
   - Metrics integration (Phase 7 committed)
   - Dashboard consolidation (9 dashboards done)
   - Alert rules (pending)
   - Plasticity dashboard (pending)

---

## Key Design Decisions

### 1. Why Redis Streams Over Pub/Sub?

**Pub/Sub** (Legacy, Deprecated):
- ❌ Fire-and-forget (no durability)
- ❌ If consumer offline, messages lost
- ❌ No replay capability
- ❌ No acknowledgment tracking

**Streams** (Current, Production):
- ✅ Durable storage (7-day event history)
- ✅ Consumer groups (automatic load balancing)
- ✅ Replay capability (consumers can catch up)
- ✅ ACK/NACK (automatic retry on failure)
- ✅ Pending Entries List (at-least-once delivery)

**Migration Strategy**: ListenerAdapter pattern (zero-code-change wrapping)
- Existing listeners continue working unchanged
- Adapter converts Streams → Pub/Sub format internally
- Gradual migration without downtime

---

### 2. Why No Central Orchestrator?

**Traditional Approach**: Orchestrator (e.g., Temporal, Airflow) coordinates services.

**Vitruvyan Approach**: Services coordinate through events (no orchestrator).

**Rationale**:
- **Octopus Arms Analogy**: Arms don't wait for brain permission to react to stimulus
- **Mycelial Analogy**: No central fungus decides which path nutrients take
- **Emergent Coordination**: Complex behaviors emerge from simple local rules + event chains

**Example**:
- User asks: "What's the trend for entity E-001?"
- LangGraph emits: `stream:analysis.requested`
- Babel Gardens consumes, emits: `stream:analysis.language_processed`
- Neural Engine consumes, emits: `stream:neural.screening.completed`
- VEE consumes, emits: `stream:vee.narrative.generated`
- LangGraph consumes, responds to user
- **No orchestrator** — coordination through causal event chains

---

### 3. Why Causal Event Chains?

Every CognitiveEvent can reference a parent event (`causation_id`). This creates an **event genealogy**:

```
root_event (user query)
  ├─ child_event_1 (intent detection)
  │   ├─ grandchild_1a (entity extraction)
  │   └─ grandchild_1b (signal analysis)
  └─ child_event_2 (neural screening)
      └─ grandchild_2a (VEE narrative)
```

**Benefits**:
- **Traceability**: Every decision traceable to its inputs
- **Audit Trail**: Vault Keepers can reconstruct full decision history
- **Debugging**: If output wrong, follow causal chain backwards
- **Compliance**: Regulators can verify "why this recommendation?"

---

## Governance Layer

### Orthodoxy Wardens (Event Validation)

Every event passing through the bus can be audited:
- **Schema Validation**: Payload matches expected structure?
- **Epistemic Validation**: Metadata includes uncertainty quantification?
- **Causation Validation**: Parent event ID exists in history?
- **Temporal Validation**: Event timestamp plausible?

**Verdict Types**:
- ✅ **Blessed**: Event conforms to epistemic charter
- ⚠️ **Purified**: Event sanitized, warnings logged
- ❌ **Heretical**: Event rejected, producer alerted

**Result**: PostgreSQL `orthodoxy_findings` table (audit trail)

---

### Vault Keepers (Immutable Archive)

All events passing through the bus are archived to PostgreSQL:
- **Ledger Anchoring**: Merkle root of 100-event batches anchored on Tron blockchain
- **7-Day Streams Retention**: Redis Streams TTL (performance optimization)
- **Infinite PostgreSQL Archive**: Full history forever
- **Replay Capability**: Restore system state from any point in time

**Use Case**: Disaster recovery, compliance audits, post-mortem analysis.

---

### Plasticity Manager (Bounded Learning)

Consumers can adapt their parameters based on outcome feedback:

**Example**: Orthodoxy Wardens confidence threshold
- **Initial**: `confidence_threshold = 0.7` (escalate if confidence < 0.7)
- **Outcome**: Too many escalations (95% false positives)
- **Learning Loop**: Analyze 7-day outcomes → propose adjustment
- **Adjustment**: `confidence_threshold → 0.5` (lower, fewer escalations)
- **Bounds**: `min=0.3, max=0.9, step=0.05` (can't drift outside)
- **Audit**: Adjustment logged as CognitiveEvent, archived by Vault Keepers

**Structural Guarantees**:
1. **Bounded**: Parameters can't escape (min, max) range
2. **Auditable**: Every adjustment traceable
3. **Reversible**: Rollback restores exact previous value
4. **Governable**: CRITICAL consumers require approval
5. **Disableable**: Plasticity can be turned off per-parameter

---

## Real-World Example: User Query Flow

**User**: "Analyze entity E-001 trends, I'm concerned about risk"

**Event Chain** (domain-agnostic — works for any vertical):
1. **LangGraph** → `stream:intent.detected` (payload: entity_ids=["E-001"], intent="trend", horizon="short")
2. **Pattern Weavers** → `stream:context.extracted` (payload: risk_profile="conservative")
3. **Neural Engine** consumes `intent.detected` → `stream:screening.completed` (payload: composite_z=1.85, feature_z={"factor_a": 2.1})
4. **Risk Assessment** consumes `screening.completed` → `stream:risk.analyzed` (payload: risk_score=35, category="medium")
5. **VEE Engine** consumes `screening.completed` + `risk.analyzed` → `stream:narrative.generated` (payload: summary="Entity E-001 shows strong trends but moderate risk...")
6. **LangGraph** consumes `narrative.generated` → responds to user

**Note**: The same event chain works for finance (entity=ticker), healthcare (entity=patient), logistics (entity=shipment), or any other domain. The bus is payload-blind — only consumers interpret the content.

**Key Points**:
- No orchestrator coordinated this
- Each service decided when to act (local autonomy)
- Full causal chain recorded (audit trail)
- If any service fails, others continue (resilience)
- Events replay-able (disaster recovery)

---

## Monitoring & Observability

### Grafana Dashboard: Cognitive Bus Monitoring
**Location**: `monitoring/grafana/dashboards/30_cognitive_framework/cognitive_bus_monitoring.json`  
**Panels**: 22 (20 data panels + 2 headers)  
**Status**: Dashboard visible, metrics implementation pending

**Key Metrics** (When Implemented):
- Events processed per second
- Event processing latency (P50, P95, P99)
- Error rate by channel
- Stream length (backlog size)
- Consumer group lag
- Herald broadcasts (by source service)
- Scribe writes (by stream)
- Listener consumption (by consumer)
- Health score (composite metric)

**Current State** (Jan 24, 2026):
- ✅ 4/20 panels working (Redis infrastructure metrics)
- ❌ 16/20 panels "No data" (application metrics missing)
- 📋 Implementation plan ready (3 phases, 7 hours)

---

### Prometheus Metrics (Target Architecture)

**Application-Level**:
```python
# Cognitive Bus Events
cognitive_bus_events_total = Counter(
    'cognitive_bus_events_total',
    'Total events processed',
    ['channel', 'status']  # status = success|failed
)

cognitive_bus_event_duration_seconds = Histogram(
    'cognitive_bus_event_duration_seconds',
    'Event processing latency',
    ['channel', 'status']
)

# Herald Activity
herald_broadcast_total = Counter(
    'herald_broadcast_total',
    'Herald broadcasts',
    ['channel', 'status']
)

# Scribe Activity
scribe_write_total = Counter(
    'scribe_write_total',
    'Scribe stream writes',
    ['stream', 'status']
)

# Listener Activity
listener_consumed_total = Counter(
    'listener_consumed_total',
    'Listener consumption',
    ['stream', 'consumer', 'status']
)
```

**Infrastructure-Level** (redis_exporter with `--include-streams`):
```promql
redis_stream_length{stream="stream:memory.write.requested"}
redis_stream_groups{stream="..."}
redis_stream_lag{stream="...", group="..."}
redis_stream_pending{stream="...", group="..."}
```

---

## Migration Status

### Pub/Sub → Streams Migration
**Started**: January 19, 2026  
**Pattern**: ListenerAdapter (zero-code-change wrapping)  
**Progress**: 4/13 listeners migrated (31%)

**Completed**:
- ✅ Vault Keepers (5 channels) — Jan 19
- ✅ Memory Orders (6 channels) — Jan 24
- ✅ Babel Gardens (3 channels) — Jan 24
- ✅ Codex Hunters (4 channels) — Jan 24

**Pending** (9 services):
- ⏳ Orthodoxy Wardens (CRITICAL, 5 channels)
- ⏳ Pattern Weavers (3 channels)
- ⏳ Neural Engine (CRITICAL, 2 channels)
- ⏳ LangGraph (CRITICAL, 8 channels)
- ⏳ VEE Engine (2 channels)
- ⏳ MCP Server (4 channels)
- ⏳ Portfolio Architects (3 channels)
- ⏳ CAN Node (2 channels)
- ⏳ Sentiment Node (2 channels)

**Migration Timeline**: 2-3 weeks (1-2 services per day, testing included)

---

## Business Value

### 1. Resilience Through Decentralization
- **No Single Point of Failure**: If one service crashes, others continue
- **Automatic Retry**: Failed events re-queued automatically (Pending Entries List)
- **Disaster Recovery**: Full event history replay from PostgreSQL + Blockchain anchoring

### 2. Auditability & Compliance
- **Full Traceability**: Every decision traceable to causal event chain
- **Immutable Archive**: Vault Keepers + Blockchain ledger (Tron)
- **Epistemic Validation**: Orthodoxy Wardens enforce uncertainty quantification

### 3. Performance & Scalability
- **Asynchronous Processing**: Services process at own pace (no blocking)
- **Load Balancing**: Consumer groups distribute work across replicas
- **7-Day Event History**: Consumers can replay missed events

### 4. Adaptability Through Plasticity
- **Continuous Learning**: Consumers adjust parameters based on outcomes
- **Governed Adaptation**: Bounds + audit trail prevent unsafe drift
- **Reversible Changes**: Rollback capability for parameter errors

### 5. Cost Efficiency
- **Redis Streams**: ~$50/month (vs Kafka ~$500/month)
- **Self-Hosted**: No external SaaS dependencies (Temporal, AWS EventBridge)
- **Zero Orchestrator**: No orchestration service costs

---

## Domain-Agnostic Refactoring (Feb 10-11, 2026)

### Refactoring Summary

The Synaptic Conclave underwent a comprehensive domain-agnostic refactoring in February 2026. The **core infrastructure** is now **100% domain-agnostic** (zero finance-specific terms in production code).

### Architecture: Core vs Domain Consumers

The Synaptic Conclave cleanly separates **infrastructure** (core, domain-agnostic) from **domain consumers** (vertical-specific, tagged for migration):

#### Core Infrastructure — 100% Domain-Agnostic (0 finance terms)

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `transport/streams.py` | 642 | StreamBus (Redis Streams transport) | **PURE** |
| `events/event_envelope.py` | 290 | TransportEvent, CognitiveEvent, EventAdapter | **PURE** |
| `consumers/base_consumer.py` | 585 | BaseConsumer ABC (Tentacle Pattern) | **PURE** |
| `consumers/registry.py` | — | Consumer registration | **PURE** |
| `consumers/listener_adapter.py` | — | Pub/Sub → Streams migration adapter | **PURE** |
| `consumers/working_memory.py` | — | Distributed working memory | **PURE** |
| `plasticity/manager.py` | — | Plasticity Manager (governed parameter adaptation) | **PURE** |
| `plasticity/observer.py` | — | Parameter drift observation | **PURE** |
| `plasticity/outcome_tracker.py` | 312 | Decision outcome tracking | **PURE** |
| `plasticity/learning_loop.py` | — | Bounded learning loop | **PURE** |
| `plasticity/metrics.py` | — | Plasticity Prometheus metrics | **PURE** |

**Key architectural decisions**:
- StreamBus is **payload-blind** (4 Sacred Invariants enforced)
- TransportEvent is **frozen** (immutable, no business logic)
- BaseConsumer defines the **Tentacle Pattern** (local autonomy, escalate when uncertain)
- Plasticity system operates on **abstract parameters** (no domain assumptions)

#### Domain Consumers — Tagged for Migration to `domains/finance/`

These files contain finance-specific logic and are **correctly tagged** with `⚠️ DOMAIN MIGRATION NOTICE` headers directing them to `vitruvyan_core/domains/finance/`:

| File | Finance Terms | Migration Target | Status |
|------|--------------|------------------|--------|
| `consumers/narrative_engine.py` | 53 | `domains/finance/consumers/` | Tagged |
| `consumers/risk_guardian.py` | 50 | `domains/finance/consumers/` | Tagged |
| `listeners/shadow_traders.py` | 43 | `domains/finance/listeners/` | Tagged |
| `listeners/codex_hunters.py` | — | `domains/finance/listeners/` | Tagged |
| `listeners/vault_keepers.py` | — | `domains/finance/listeners/` | Tagged |

**Important**: These files are **domain vertical implementations** that temporarily cohabit in `core/`. They are NOT core infrastructure. The `DOMAIN MIGRATION NOTICE` at the top of each file explicitly marks them and specifies the target location.

#### Domain-Agnostic Listeners (infrastructure bridges)

| File | Finance Terms | Purpose |
|------|--------------|---------|
| `listeners/babel_gardens.py` | 0 | Language processing bridge |
| `listeners/mcp.py` | 0 | MCP Gateway bridge |
| `listeners/langgraph.py` | 22 (in channel names) | LangGraph workflow bridge |

#### Event Schema — Mixed (structural + domain)

`events/event_schema.py` (797 lines) contains both:
- **Domain-agnostic enums**: `EventDomain`, `VaultIntent`, `OrthodoxIntent` — pure infrastructure
- **Domain-specific schemas**: `PORTFOLIO_ANALYSIS_REQUESTED`, `ticker` fields — tagged for vertical extraction

### Refactoring Metrics

| Metric | Before (Jan 2026) | After (Feb 2026) | Change |
|--------|-------------------|-------------------|--------|
| Core infrastructure finance terms | ~50 | **0** | -100% |
| Infrastructure files domain-agnostic | 60% | **100%** | +40% |
| Domain consumers tagged for migration | 0/5 | **5/5** | +100% |
| Pub/Sub → Streams migration | 31% | ~80% | +49% |
| Plasticity system domain purity | 100% | **100%** | Maintained |

### LangGraph Orchestration Refactoring (Feb 10, 2026)

The LangGraph orchestration layer was also refactored to a clean **plugin-based architecture**:

#### Core Orchestration — LEVEL 1 (Pure Python, no I/O)

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `orchestration/graph_engine.py` | 442 | GraphPlugin ABC + GraphEngine builder | **PURE** |
| `orchestration/base_state.py` | 196 | BaseGraphState (~30 agnostic fields) | **PURE** |
| `orchestration/sacred_flow.py` | — | Post-routing pipeline (domain-agnostic) | **PURE** |
| `orchestration/parser.py` | — | Language-pattern parsing (no domain concepts) | **PURE** |
| `orchestration/compose/base_composer.py` | — | BaseComposer ABC | **PURE** |

**Key architectural decisions**:
- **`GraphPlugin` ABC**: Domains register nodes/routes/state via plugin pattern (no hardcoded finance nodes)
- **`BaseGraphState`**: ~30 fields, **zero domain-specific fields** (no tickers, portfolios, allocations)
- Domain verticals (finance, logistics, healthcare) **extend** BaseGraphState via inheritance
- **LEVEL 1 separation**: Core orchestration has no I/O, no infrastructure dependencies

#### Domain-Specific Nodes (finance vertical)

Nodes like `compose_node.py` (1376 lines, 48 finance terms), `proactive_suggestions_node.py` (28 terms) contain finance-specific logic. These are **vertical implementations** that plug into the domain-agnostic core via `GraphPlugin`.

---

## Technical Debt & Known Limitations

### 1. Domain Consumer Migration (Tagged, Not Moved)
- **Impact**: 5 finance-specific consumers/listeners still in `core/synaptic_conclave/`
- **Status**: All tagged with `⚠️ DOMAIN MIGRATION NOTICE` + target paths
- **Timeline**: Q2 2026 (move to `domains/finance/`)
- **Risk**: Low (functional, correct tagging, no core contamination)

### 2. Event Schema Mixed Content
- **Impact**: `event_schema.py` has domain-agnostic + finance-specific schemas in one file
- **Timeline**: Q2 2026 (split into `core_schemas.py` + `finance_schemas.py`)
- **Workaround**: Domain enums clearly separated by class names

### 3. LangGraph Finance Nodes in Core
- **Impact**: `compose_node.py`, `proactive_suggestions_node.py` contain finance logic
- **Status**: GraphPlugin architecture ready for extraction
- **Timeline**: Q2 2026 (register via `FinanceGraphPlugin` instead of direct import)

---

## Roadmap

### Q1 2026 (Completed)
- ✅ Redis Streams migration (core infrastructure)
- ✅ Domain-agnostic core infrastructure (0 finance terms)
- ✅ BaseConsumer Tentacle Pattern
- ✅ Plasticity system (bounded parameter adaptation)
- ✅ GraphPlugin architecture (domain extension via plugins)
- ✅ BaseGraphState (~30 agnostic fields)
- ✅ Domain Migration Notices on all finance consumers

### Q2 2026: Domain Extraction
- ⏳ Move tagged consumers to `domains/finance/consumers/`
- ⏳ Move tagged listeners to `domains/finance/listeners/`
- ⏳ Split event_schema.py (core vs domain schemas)
- ⏳ Extract finance nodes to `FinanceGraphPlugin`
- ⏳ Load testing (10K events/sec target)
- ⏳ Multi-region replication planning

---

## References

**Core Infrastructure** (domain-agnostic, LEVEL 1):
- `vitruvyan_core/core/synaptic_conclave/transport/streams.py` — StreamBus core (642 lines)
- `vitruvyan_core/core/synaptic_conclave/events/event_envelope.py` — TransportEvent/CognitiveEvent (290 lines)
- `vitruvyan_core/core/synaptic_conclave/consumers/base_consumer.py` — BaseConsumer Tentacle Pattern (585 lines)
- `vitruvyan_core/core/synaptic_conclave/consumers/listener_adapter.py` — Migration adapter
- `vitruvyan_core/core/synaptic_conclave/plasticity/manager.py` — Plasticity Manager
- `vitruvyan_core/core/synaptic_conclave/plasticity/outcome_tracker.py` — Outcome Tracker (312 lines)

**LangGraph Orchestration** (domain-agnostic, LEVEL 1):
- `vitruvyan_core/core/orchestration/graph_engine.py` — GraphPlugin ABC + GraphEngine (442 lines)
- `vitruvyan_core/core/orchestration/base_state.py` — BaseGraphState ~30 agnostic fields (196 lines)
- `vitruvyan_core/core/orchestration/sacred_flow.py` — Post-routing pipeline
- `vitruvyan_core/core/orchestration/compose/base_composer.py` — BaseComposer ABC

**Domain Consumers** (finance vertical, tagged for migration):
- `vitruvyan_core/core/synaptic_conclave/consumers/narrative_engine.py` — VEE narratives (571 lines, ⚠️ MIGRATION NOTICE)
- `vitruvyan_core/core/synaptic_conclave/consumers/risk_guardian.py` — Risk monitoring (613 lines, ⚠️ MIGRATION NOTICE)
- `vitruvyan_core/core/synaptic_conclave/listeners/shadow_traders.py` — Trading events (368 lines, ⚠️ MIGRATION NOTICE)

**Architecture Documentation**:
- `vitruvyan_core/core/synaptic_conclave/philosophy/` — Epistemic charter
- `vitruvyan_core/core/synaptic_conclave/docs/` — Technical architecture docs
- `vitruvyan_core/core/synaptic_conclave/consumers/MIGRATION_GUIDE.md` — Pub/Sub → Streams migration (331 lines)

**Monitoring**:
- Grafana dashboard: `monitoring/grafana/dashboards/30_cognitive_framework/cognitive_bus_monitoring.json`
- Prometheus metrics: `vitruvyan_core/core/synaptic_conclave/monitoring/`

---

## Quick Start Commands

### Check Cognitive Bus Health
```bash
# Verify Redis Streams exist
docker exec vitruvyan_redis_master redis-cli KEYS "stream:*"

# Check consumer groups
docker exec vitruvyan_redis_master redis-cli XINFO GROUPS "stream:memory.write.requested"

# Check listeners running
docker ps | grep listener

# Check listener logs (should show "Consuming stream...")
docker logs vitruvyan_memory_orders_listener --tail 20
```

### Monitor Cognitive Bus
```bash
# Access Grafana dashboard
open https://dash.vitruvyan.com

# Query Prometheus metrics (when implemented)
curl "http://localhost:9090/api/v1/query?query=cognitive_bus_events_total"

# Check Memory Inspector API
curl http://localhost:8024/health
curl http://localhost:8024/stats/memory_orders
```

### Debugging
```bash
# Check event history (7-day retention)
docker exec vitruvyan_redis_master redis-cli XRANGE "stream:memory.write.requested" - + COUNT 10

# Check pending events (not acknowledged)
docker exec vitruvyan_redis_master redis-cli XPENDING "stream:memory.write.requested" "group:memory_orders"

# Replay events from specific timestamp
docker exec vitruvyan_redis_master redis-cli XREAD STREAMS "stream:memory.write.requested" 1737734400000-0
```

---

## TL;DR — 5-Minute Summary

**What**: Distributed event backbone inspired by octopus brains + fungal networks.

**Why**: 
- No single point of failure (resilience)
- Full audit trail (compliance)
- Asynchronous processing (performance)
- Bounded learning (adaptability with guardrails)

**How**:
- Redis Streams (durable, ordered, replay-able)
- Herald/Scribe/Listener pattern (producer → bus → consumer)
- Causal event chains (every event can reference parent)
- 4 Sacred Invariants (bus stays "dumb", intelligence in consumers)

**Domain-Agnostic Status (Feb 2026)**:
- ✅ **Core infrastructure**: 100% domain-agnostic (0 finance terms in 11 core files)
- ✅ **Transport layer**: StreamBus payload-blind, TransportEvent frozen/immutable
- ✅ **Consumer framework**: BaseConsumer Tentacle Pattern (domain-agnostic ABC)
- ✅ **Plasticity system**: Abstract parameter adaptation (no domain assumptions)
- ✅ **LangGraph orchestration**: GraphPlugin ABC + BaseGraphState (~30 agnostic fields)
- ⚠️ **Domain consumers**: 5 files tagged with `DOMAIN MIGRATION NOTICE` → `domains/finance/` (Q2 2026)
- ⚠️ **Event schema**: Mixed content (core + finance enums in one file) → split planned Q2 2026

**Architecture Pattern**:
```
CORE (domain-agnostic)           DOMAIN (vertical-specific, tagged for migration)
├── transport/streams.py         ├── consumers/narrative_engine.py  ⚠️→ domains/finance/
├── events/event_envelope.py     ├── consumers/risk_guardian.py     ⚠️→ domains/finance/
├── consumers/base_consumer.py   ├── listeners/shadow_traders.py    ⚠️→ domains/finance/
├── consumers/listener_adapter.py├── listeners/codex_hunters.py     ⚠️→ domains/finance/
├── consumers/working_memory.py  └── listeners/vault_keepers.py     ⚠️→ domains/finance/
├── plasticity/* (5 files)
└── monitoring/*
```

**Next Steps** (Q2 2026):
1. Move tagged domain consumers to `domains/finance/` 
2. Split `event_schema.py` into core vs domain schemas
3. Extract finance LangGraph nodes to `FinanceGraphPlugin`
4. Load testing (10K events/sec target)

**Bottom Line**: The Synaptic Conclave's core infrastructure is **production-ready and 100% domain-agnostic**. Finance-specific consumers are correctly isolated and tagged for migration to the domains layer. The system supports any vertical (logistics, healthcare, cybersecurity) without core modifications.

---

**Last Updated**: February 11, 2026  
**Author**: Vitruvyan Engineering Team  
**Version**: 2.0 (Domain-Agnostic Production Architecture)
