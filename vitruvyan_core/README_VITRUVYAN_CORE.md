# vitruvyan_core/ — Core Library

> **Last Updated**: February 12, 2026  
> **Purpose**: Reusable OS components (domain-agnostic epistemic kernel)  
> **Type**: Python library (importable, zero I/O at core level)

---

## 🎯 Cosa Contiene

`vitruvyan_core/` è la **libreria core** di Vitruvyan — l'OS epistemico domain-agnostic. Fornisce primitivi cognitivi riutilizzabili che qualsiasi verticale può importare e specializzare.

**Caratteristiche**:
- ✅ **Domain-Agnostic**: Zero logica finance/medicale/logistica hardcoded
- ✅ **Importable Library**: Usabile da servizi esterni via `from vitruvyan_core import ...`
- ✅ **Pure Business Logic**: I/O delegato al livello service (LIVELLO 2)
- ✅ **SACRED_ORDER_PATTERN**: Architettura a due livelli obbligatoria

---

## 📂 Struttura

```
vitruvyan_core/
├── core/                        # Primitivi cognitivi OS-level
│   ├── agents/                  # Database agents (PostgreSQL, Qdrant, Redis)
│   │   ├── postgres_agent.py    → Single interface to PostgreSQL
│   │   ├── qdrant_agent.py      → Vector store interface
│   │   └── ...
│   ├── cognitive/               # Funzioni cognitive (NLP, patterns)
│   │   ├── babel_gardens/       → Linguistic analysis (LIVELLO 1)
│   │   └── pattern_weavers/     → Temporal pattern detection (LIVELLO 1)
│   ├── governance/              # 6 Sacred Orders (governance subsystems)
│   │   ├── memory_orders/       → Coherence & retrieval (LIVELLO 1)
│   │   ├── vault_keepers/       → Archival & persistence (LIVELLO 1)
│   │   ├── orthodoxy_wardens/   → Validation & audit (LIVELLO 1)
│   │   └── codex_hunters/       → Data discovery & mapping (LIVELLO 1)
│   ├── llm/                     # LLM integration (OpenAI, caching, prompts)
│   ├── monitoring/              # Metrics, health checks, observability
│   ├── neural_engine/           # Neural computation primitives
│   ├── orchestration/           # LangGraph state machines & node library
│   │   └── langgraph/           → LangGraph orchestration (domain-agnostic nodes)
│   └── synaptic_conclave/       # Cognitive Bus (Redis Streams transport)
│       ├── transport/           → StreamBus, Redis Streams
│       └── events/              → Event envelopes, adapters
├── domains/                     # Domain contracts (abstract interfaces)
│   ├── base_domain.py           → Abstract domain contract
│   └── finance/                 → Example vertical (legacy, being abstracted)
└── utils/                       # Shared utilities (logging, config, helpers)
```

---

## 🏗️ SACRED_ORDER_PATTERN (Mandatory)

Tutti i Sacred Orders seguono il **pattern a due livelli**:

### LIVELLO 1 — Pure Domain (`vitruvyan_core/core/governance/<order>/`)

**10 directory obbligatorie**:
```
<order>/
├── domain/          # Frozen dataclasses (immutable DTOs)
├── consumers/       # Pure process() functions (NO I/O)
├── governance/      # Rules, classifiers, engines
├── events/          # Channel name constants
├── monitoring/      # Metric NAME constants (no prometheus_client)
├── philosophy/      # charter.md (identity, mandate, invariants)
├── docs/            # Implementation notes (locality-first)
├── examples/        # Usage examples (pure Python)
├── tests/           # Unit tests (pytest, no Docker)
└── _legacy/         # Pre-refactoring code (frozen archive)
```

**Regole**:
- ✅ Zero I/O (no PostgreSQL, Redis, Qdrant, httpx instantiation)
- ✅ Relative imports only (`from .domain import X`)
- ✅ Type hints only for agents (never instantiate)
- ❌ No cross-Sacred-Order imports

### LIVELLO 2 — Service (`services/api_<order>/`)

**Service wrappers** (Docker, REST API, I/O):
- Vedere `services/README_SERVICES.md`

**Status**: ✅ 100% conformance (6/6 Sacred Orders refactored, Feb 2026)

---

## 📚 Documentazione

Ogni modulo ha la propria cartella `docs/` (locality-first pattern):

- **LangGraph**: [core/orchestration/langgraph/docs/](core/orchestration/langgraph/docs/)
- **Synaptic Conclave**: [core/synaptic_conclave/docs/](core/synaptic_conclave/docs/)
- **Neural Engine**: [core/neural_engine/docs/](core/neural_engine/docs/)
- **Sacred Orders**: Ogni order ha `docs/` in `core/governance/<order>/docs/`

**Global docs**: [../docs/](../docs/) (cross-cutting documentation)

---

## 🔌 Come Usarlo

### Import dalla Core Library

```python
# Agents (database access)
from vitruvyan_core.core.agents.postgres_agent import PostgresAgent
from vitruvyan_core.core.agents.qdrant_agent import QdrantAgent

# Cognitive Bus
from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamBus

# Sacred Order consumers (LIVELLO 1 - pure logic)
from vitruvyan_core.core.governance.memory_orders.consumers import CoherenceChecker
from vitruvyan_core.core.governance.vault_keepers.consumers import ArchiveProcessor

# LangGraph nodes (orchestration)
from vitruvyan_core.core.orchestration.langgraph.nodes import entity_resolver
```

### Pattern Usage

```python
# PostgreSQL via agent
pg = PostgresAgent()
rows = pg.fetch("SELECT * FROM entities WHERE id = %s", ("entity_1",))

# Cognitive Bus (StreamBus)
bus = StreamBus()
bus.publish("codex.discovery.mapped", {"entity_id": "entity_1", "mapped": True})

# Consume events
for event in bus.consume("codex.discovery.mapped", "vault_keepers", "vault_1"):
    process_event(event)
    bus.acknowledge(event.stream, "vault_keepers", event.event_id)
```

---

## 🎯 Design Principles

1. **Domain-Agnostic**: Nessuna logica verticale hardcoded nel core
2. **Zero I/O in LIVELLO 1**: Business logic pura, I/O delegato a LIVELLO 2
3. **Importable**: Libreria riutilizzabile, non monolite standalone
4. **SACRED_ORDER_PATTERN**: Architettura obbligatoria a due livelli
5. **Locality-First Docs**: Documentazione vive con il codice che descrive

---

## 📖 Link Utili

- **[README Principale](../README.md)** — Overview completa Vitruvyan
- **[Docs Portal](../docs/index.md)** — Entry point documentazione
- **[Services](../services/README_SERVICES.md)** — Microservizi che usano questo core
- **[Epistemic Charter](../docs/foundational/Vitruvyan_Epistemic_Charter.md)** — Filosofia core
- **[SACRED_ORDER_PATTERN](core/governance/SACRED_ORDER_PATTERN.md)** — Pattern tecnico completo

---

**Purpose**: Fornire primitivi cognitivi domain-agnostic riutilizzabili.  
**Consumers**: Microservizi in `services/`, verticali esterni, test suite.  
**Status**: Foundation phase — Post-refactoring (100% SACRED_ORDER_PATTERN conformance).
