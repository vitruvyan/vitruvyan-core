# 🏛️ Vitruvyan Core

**Domain-Agnostic Agentic AI Framework**

> **Last Updated**: February 14, 2026 (Priority 2B: Hook Pattern Implementation)  
> **Version**: 0.1.0-alpha  
> **Status**: Foundation Phase — Consolidation (SACRED_ORDER_PATTERN 100%, Hook Pattern 3/3 nodes)

Vitruvyan Core is an **opinionated architectural framework** for multi-service, multi-domain agentic AI systems. It provides LangGraph orchestration, Redis Streams event bus, Sacred Orders governance, and domain-agnostic primitives that can be specialized through a **registry-based plugin pattern** (hook registries + environment selection).

---

## 📖 New to Vitruvyan?

**Quick Orientation**:
1. Read [🔌 Domain Extension System (Hook Pattern)](#-domain-extension-system) to understand the plugin architecture
2. Check [📊 Module Status Map](docs/foundational/MODULE_STATUS_MAP.md) for complete inventory (nodes, services, registries)
3. Read [🔍 Pipeline Walkthrough](docs/foundational/VITRUVYAN_PIPELINE_WALKTHROUGH.md) for technical deep-dive
4. Review [🗂️ Repository Structure](#-repository-structure) to navigate the codebase
5. Try [🚀 Quick Start](#-quick-start) to run the system locally

---

## 🎯 What is Vitruvyan Core?

Vitruvyan Core is **NOT**:
- A financial advisor
- A domain-specific tool
- A simple chatbot

Vitruvyan Core **IS**:
- An agentic reasoning framework
- A domain-agnostic cognitive architecture
- An extensible epistemic operating system

---

## 🧠 Core Philosophy: Domain-Agnostic Framework

**Vitruvyan Core is NOT**:
- A chatbot toolkit
- A finance-specific AI system
- A ready-to-deploy product

**Vitruvyan Core IS**:
- An **architectural framework** for building multi-service agentic systems
- A **domain-agnostic orchestration layer** (LangGraph + Redis Streams + Sacred Orders)
- A **plugin pattern** for domain specialization (hook-based registries)

### What Core Provides

1. **LangGraph Orchestration** (19-node full graph, 4-node minimal graph; 6 route branches)
   - Domain-agnostic cognitive pipeline (parse → intent → weaver → resolver → grounding → decision)
   - Hook pattern for domain-specific behaviors (intent, entity resolution, execution) with stub fallback when unconfigured
   - Sacred Flow governance (output_normalizer → orthodoxy → vault → compose → CAN)

2. **Redis Streams Event Bus** (StreamBus, 641L)
   - At-least-once delivery (consumer groups + ACK/PEL)
   - Payload-blind transport (no semantic routing)
   - Durable replay + correlation tracking

3. **Sacred Orders** (6 governance subsystems, 100% SACRED_ORDER_PATTERN conformance)
   - Memory Orders: RAG, coherence analysis
   - Vault Keepers: Archival persistence
   - Orthodoxy Wardens: Validation, audit
   - Babel Gardens: Emotion, language detection
   - Codex Hunters: System maintenance, discovery
   - Pattern Weavers: Ontology mapping

4. **Infrastructure Agents**
   - PostgresAgent (relational data)
   - QdrantAgent (vector memory)
   - LLMAgent (centralized OpenAI gateway with caching)

5. **Hook Pattern** (domain plugin system)
   - IntentRegistry (ACTIVE: finance intents loaded)
   - EntityResolverRegistry (STUB: passthrough default)
   - ExecutionRegistry (STUB: fake success default)

### What Core Does NOT Provide

- **Domain knowledge**: No finance, logistics, healthcare logic in core
- **Execution logic**: Stub defaults (empty ranking, passthrough entity resolution)
- **Pre-built verticals**: Finance examples exist but are **not mandatory**

Domain-specific behavior is **opt-in via registration**:
```python
# Example: Finance domain plugin
if os.getenv("ENTITY_DOMAIN") == "finance":
    from domains.finance.entity_resolver_config import register_finance_entity_resolver
    register_finance_entity_resolver()  # Now entity_resolver uses finance logic
```

See [🔌 Domain Extension System](#-domain-extension-system) for complete pattern documentation.

---

## 🗂️ Repository Structure

Vitruvyan follows the **SACRED_ORDER_PATTERN** — a mandatory two-level architecture for all cognitive subsystems.

### Root Directory Layout

```
vitruvyan-core/
├── vitruvyan_core/          # Core library (reusable OS components)
│   ├── core/                # Sacred Orders & cognitive primitives
│   │   ├── agents/          # Database agents (PostgreSQL, Qdrant, Redis)
│   │   ├── cognitive/       # Cognitive functions (Babel Gardens, Pattern Weavers)
│   │   ├── governance/      # Sacred Orders (6 governance subsystems)
│   │   ├── llm/             # LLM integration (OpenAI, caching, prompts)
│   │   ├── monitoring/      # Observability (metrics, health checks)
│   │   ├── neural_engine/   # Neural computation primitives
│   │   ├── orchestration/   # LangGraph orchestration & state management
│   │   └── synaptic_conclave/ # Event bus (Redis Streams transport)
│   ├── domains/             # Domain contracts (abstract interfaces)
│   └── utils/               # Shared utilities
│
├── services/                # Microservices (Docker-based APIs)
│   ├── api_babel_gardens/   # Linguistic analysis service
│   ├── api_codex_hunters/   # Data discovery & mapping
│   ├── api_graph/           # LangGraph orchestration API
│   ├── api_mcp/             # Model Context Protocol gateway
│   ├── api_memory_orders/   # Memory & coherence service
│   ├── api_neural/          # Neural engine API
│   ├── api_orthodoxy_wardens/ # Governance & validation
│   ├── api_pattern_weavers/ # Pattern analysis service
│   └── api_vault_keepers/   # Archival & persistence
│
├── infrastructure/          # Deployment & ops
│   ├── docker/              # Docker Compose configurations
│   └── monitoring/          # Grafana dashboards, Prometheus configs
│
├── tests/                   # Test suite (unit + integration)
├── docs/                    # Cross-cutting documentation (see below)
├── config/                  # Shared configuration files
└── scripts/                 # Deployment & maintenance scripts
```

### Sacred Orders (6 Governance Subsystems)

All Sacred Orders follow the **SACRED_ORDER_PATTERN** (10-directory structure):

| Sacred Order | Domain | Location (LIVELLO 1) | Service (LIVELLO 2) |
|--------------|--------|---------------------|---------------------|
| **Memory Orders** | Coherence & Retrieval | `core/governance/memory_orders/` | `services/api_memory_orders/` |
| **Vault Keepers** | Archival & Persistence | `core/governance/vault_keepers/` | `services/api_vault_keepers/` |
| **Orthodoxy Wardens** | Validation & Audit | `core/governance/orthodoxy_wardens/` | `services/api_orthodoxy_wardens/` |
| **Babel Gardens** | Linguistic Processing | `core/cognitive/babel_gardens/` | `services/api_babel_gardens/` |
| **Codex Hunters** | Data Discovery | `core/governance/codex_hunters/` | `services/api_codex_hunters/` |
| **Pattern Weavers** | Temporal Patterns | `core/cognitive/pattern_weavers/` | `services/api_pattern_weavers/` |

**SACRED_ORDER_PATTERN** mandates:
- **LIVELLO 1** (Pure Domain): 10 directories (`domain/`, `consumers/`, `governance/`, `events/`, `monitoring/`, `philosophy/`, `docs/`, `examples/`, `tests/`, `_legacy/`)
- **LIVELLO 2** (Service): I/O adapters, REST API, Docker deployment
- **100% Conformance**: All 6 Sacred Orders refactored as of Feb 2026

---

## 📚 Documentation Organization

Vitruvyan uses the **locality-first pattern** — documentation lives with the code it documents.

### Module-Specific Documentation

Each major module has its own `docs/` directory:

```
vitruvyan_core/core/
├── orchestration/langgraph/docs/     # LangGraph refactoring, architecture
├── synaptic_conclave/docs/           # Cognitive Bus, Redis Streams, listeners
├── neural_engine/docs/               # Neural engine patterns, contracts
└── governance/
    ├── memory_orders/docs/           # Memory & coherence docs
    ├── vault_keepers/docs/           # Archival & persistence docs
    ├── orthodoxy_wardens/docs/       # Validation & audit docs
    └── codex_hunters/docs/           # Data discovery docs

services/
├── api_mcp/docs/                     # MCP server refactoring, audit
├── api_orthodoxy_wardens/docs/       # Orthodoxy service docs
└── ...

infrastructure/monitoring/docs/        # Grafana dashboards, metrics
```

### Global Documentation (`docs/`)

Cross-cutting documentation organized by purpose:

```
docs/
├── index.md                          # Documentation portal (entry point)
├── architecture/                     # Architecture audits, refactoring plans (12 files)
├── changelog/                        # Phase reports, checkpoints, COO approvals (21 files)
├── foundational/                     # Core philosophy, charter, invariants (7 files)
│   ├── Vitruvyan_Bus_Invariants.md
│   ├── Vitruvyan_Epistemic_Charter.md
│   ├── Vitruvyan_Vertical_Specification.md
│   ├── VITRUVYAN_OVERVIEW.md
│   └── Vitruvyan_Octopus_Mycelium_Architecture.md (research paper)
├── planning/                         # Strategic blueprints (2 files)
│   ├── _ALBERATURA_FRAMEWORK_DA-IMPLEMENTARE_FEB12_2026.md  # 🎯 Reorganization blueprint
│   └── TODO_EXAMPLES_PATTERN.md
├── prompts/                          # Session work logs (6 files)
├── services/                         # Service descriptions (2 files)
└── testing/                          # Test plans, boot validation (2 files)
```

**Key Documents**:
- **[Epistemic Charter](docs/foundational/Vitruvyan_Epistemic_Charter.md)** — Philosophy & principles
- **[Bus Invariants](docs/foundational/Vitruvyan_Bus_Invariants.md)** — Cognitive Bus constraints
- **[Architecture Audit](docs/planning/_ALBERATURA_FRAMEWORK_DA-IMPLEMENTARE_FEB12_2026.md)** — 🎯 Post-refactoring roadmap
- **[Changelog](docs/changelog/)** — Phase-by-phase evolution history

---

## 🏗️ Architecture

### Sacred Orders (Cognitive Layers)

| Order | Responsibility | Components |
|-------|---------------|------------|
| **Perception** | Data gathering | Generic collectors, adapters |
| **Memory** | Persistence | PostgreSQL, Qdrant, Redis |
| **Reason** | Quantitative analysis | Scoring engine, factor framework |
| **Discourse** | Language processing | LangGraph, explainability engine |
| **Truth** | Governance | Audit, validation, archival |

### Core Components

```
vitruvyan_core/
├── core/
│   ├── agents/              # PostgresAgent, QdrantAgent, Redis abstraction
│   ├── cognitive/           # Babel Gardens, Pattern Weavers (NLP, temporal analysis)
│   ├── governance/          # 6 Sacred Orders (Memory, Vault, Orthodoxy, Codex, etc.)
│   ├── llm/                 # OpenAI integration, caching, prompt templates
│   ├── monitoring/          # Metrics, health checks, observability
│   ├── neural_engine/       # Neural computation primitives
│   ├── orchestration/       # LangGraph state machines, node library
│   └── synaptic_conclave/   # Cognitive Bus (Redis Streams transport)
├── domains/
│   ├── base_domain.py       # Domain contract (ABSTRACT)
│   └── finance/             # Example vertical (legacy, being abstracted)
└── services/                # 9 microservices (Docker APIs wrapping core modules)
```

**Key Abstractions**:
- **Agents**: Single point of access for PostgreSQL (`PostgresAgent`), Qdrant (`QdrantAgent`), Redis (`StreamBus`)
- **Orchestration**: LangGraph state machines with domain-agnostic nodes
- **Governance**: Sacred Orders handle validation, archival, coherence, discovery
- **Event Bus**: Redis Streams via `StreamBus` (payload-blind transport)

---

## 🔌 Domain Extension System (Hook Pattern)

**Implemented**: February 14, 2026 (Priority 2B completion)

Vitruvyan uses a **registry-based hook pattern** for domain-specific extension points. This mirrors the proven `IntentRegistry` design and provides **graceful degradation** when domain plugins are absent.

### Three Hook Points

#### 1. Intent Detection (`intent_detection_node.py`)
- **Registry**: `IntentRegistry` (`core/orchestration/intent_registry.py`)
- **Domain Config**: `domains/finance/intent_config.py`
- **Env Var**: `INTENT_DOMAIN=finance` (default)
- **Behavior**:
  - **With finance**: `trend`, `momentum`, `risk`, `volatility`, `backtest`, `allocate`, etc.
  - **Without finance**: Core intents only (`soft`, `unknown`)
- **Status**: ✅ **ACTIVE** (finance domain loaded by default)

#### 2. Entity Resolution (`entity_resolver_node.py`)
- **Registry**: `EntityResolverRegistry` (`core/orchestration/entity_resolver_registry.py`)
- **Domain Config**: `domains/finance/entity_resolver_config.py`
- **Env Var**: `ENTITY_DOMAIN=finance` (optional)
- **Behavior**:
  - **Default**: Passthrough stub (preserves `entity_ids`, sets `flow='direct'`)
  - **With finance**: Ticker symbol → company entity resolution
- **Status**: 🟡 **STUB** (no domain registered, graceful passthrough)

#### 3. Execution Handler (`exec_node.py`)
- **Registry**: `ExecutionRegistry` (`core/orchestration/execution_registry.py`)
- **Domain Config**: `domains/finance/execution_config.py`
- **Env Var**: `EXEC_DOMAIN=finance` (optional)
- **Behavior**:
  - **Default**: Fake success stub (empty ranking, `route='ne_valid'`, `ok=True`)
  - **With finance**: Neural Engine ranking for finance entities
- **Status**: 🟡 **STUB** (no domain registered, graceful fake success)

### Hook Pattern Guarantees

- ✅ **Zero breaking changes** (stub behavior matches previous domain-neutral behavior)
- ✅ **Type-safe** via dataclasses (`IntentDefinition`, `EntityResolverDefinition`, `ExecutionHandlerDefinition`)
- ✅ **Singleton registry pattern** (`get_entity_resolver_registry()`, `get_execution_registry()`)
- ✅ **Graceful degradation** if domain plugin missing
- ✅ **Testable in isolation** (LIVELLO 1 pure, no I/O)

### How to Add a Domain Plugin

**Step 1**: Create domain configs
```python
# vitruvyan_core/domains/logistics/entity_resolver_config.py
from core.orchestration.entity_resolver_registry import (
    EntityResolverDefinition, get_entity_resolver_registry
)

def logistics_entity_resolver(state):
    # Resolve route_ids to route objects
    route_ids = state.get("entity_ids", [])
    # ... domain-specific logic ...
    return state

def register_logistics_entity_resolver():
    registry = get_entity_resolver_registry()
    registry.register(EntityResolverDefinition(
        domain="logistics",
        resolver_fn=logistics_entity_resolver,
        description="Resolve route IDs to route objects",
        requires_fields=["entity_ids"]
    ))
```

**Step 2**: Register in service startup
```python
# services/api_graph/main.py
import os

if os.getenv("ENTITY_DOMAIN") == "logistics":
    from domains.logistics.entity_resolver_config import register_logistics_entity_resolver
    register_logistics_entity_resolver()
```

**Step 3**: Set environment variable
```bash
export ENTITY_DOMAIN=logistics
```

**See**: `vitruvyan_core/domains/finance/README_HOOK_PATTERN.md` for complete examples

### Example Domains (Future)

| Domain | Entities | Intent Examples | Execution Logic |
|--------|----------|----------------|----------------|
| **Finance** | Tickers (AAPL, MSFT) | trend, momentum, risk | Neural Engine ranking |
| **Logistics** | Routes (route_123) | optimize, forecast, reroute | Route optimization scoring |
| **Healthcare** | Patients (patient_456) | diagnose, monitor, predict | Patient risk assessment |
| **Legal** | Cases (case_789) | precedent, probability | Case outcome prediction |

**Finance** is the only domain with example configs currently (`domains/finance/`). Other domains are **not implemented** in core.

---

## 🧠 LangGraph Orchestration

The cognitive flow is a stateful graph with 30+ nodes:

```
input → parse → intent_detection → semantic_grounding →
entity_resolution → parameter_extraction → routing →
[analysis nodes] → explanation → validation → output
```

Nodes remain domain-neutral - they operate on generic entities and signals.

---

## 🚀 Quick Start

### Prerequisites

- Docker + Docker Compose
- Python 3.11+
- Git

### 1. Start Infrastructure

```bash
# Clone repository
git clone https://github.com/yourusername/vitruvyan-core.git
cd vitruvyan-core

# Start all services (36 containers)
cd infrastructure/docker
docker compose up -d

# Verify containers
docker ps --filter "name=core_" --format "table {{.Names}}\t{{.Status}}"
# Expected: 32/32 UP, 31/32 healthy (redis_streams_exporter unhealthy is known issue)
```

### 2. Test LangGraph Pipeline

```bash
# Basic query (default: finance domain for intent detection)
curl -X POST http://localhost:9004/run \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "analyze momentum trends",
    "user_id": "test_user"
  }'

# Expected response:
{
  "status": "success",
  "intent": "momentum",
  "route": "dispatcher_exec",
  "output": {
    "ranking": [],  # Empty (exec_node is stub)
    "metadata": {"stub": true}
  }
}
```

### 3. Explore Documentation

```bash
# Start MkDocs site
mkdocs serve
# Access at http://localhost:8000
```

**Key Docs**:
- [📊 Module Status Map](docs/foundational/MODULE_STATUS_MAP.md) — Complete inventory (nodes, services, Sacred Orders)
- [🔍 Pipeline Walkthrough](docs/foundational/VITRUVYAN_PIPELINE_WALKTHROUGH.md) — Technical deep-dive
- [📖 Copilot Instructions](.github/copilot-instructions.md) — Architecture invariants

### 4. Check Logs

```bash
# API Graph (main orchestration)
docker logs --tail=50 core_graph

# Sacred Orders listeners
docker logs --tail=50 core_babel_listener
docker logs --tail=50 core_vault_keepers_listener
docker logs --tail=50 core_orthodoxy_wardens_listener

# Event bus
docker exec core_redis redis-cli XLEN vitruvyan:conclave.mcp.actions
```

### 5. Enable Domain Plugins (Optional)

**Finance example** (entity resolution + execution):

```python
# Uncomment in services/api_graph/main.py:
if os.getenv("ENTITY_DOMAIN") == "finance":
    from domains.finance.entity_resolver_config import register_finance_entity_resolver
    register_finance_entity_resolver()

if os.getenv("EXEC_DOMAIN") == "finance":
    from domains.finance.execution_config import register_finance_execution_handler
    register_finance_execution_handler()
```

```bash
# Set environment variables
export ENTITY_DOMAIN=finance
export EXEC_DOMAIN=finance

# Rebuild container
cd infrastructure/docker
docker compose build graph
docker compose up -d graph
```

Now `entity_resolver_node` and `exec_node` use finance-specific logic instead of stubs.

---

## 📊 Database Architecture

### PostgreSQL (Source of Truth)
- `entities` — Domain objects
- `signals` — Measurements over time
- `analysis_logs` — Decision history
- `audit_trails` — Governance records

### Qdrant (Semantic Memory)
- Conversation history
- Contextual grounding
- Similarity search

### Redis (Cognitive Bus)
- Event-driven coordination
- Inter-agent messaging
- State synchronization

---

## 🎯 Design Principles

1. **Domain Agnostic** — No hardcoded verticals
2. **Structurally Intact** — Preserve agentic architecture
3. **Extensible** — Plugin-based specialization
4. **Explainable** — Every decision is traceable
5. **Governable** — Audit and validation layers

---

## 🛡️ Sacred Orders Pattern

Vitruvyan inherits a pattern called "Sacred Orders" - cognitive subsystems that model human reasoning:

- **Order I (Perception)**: How do we gather information?
- **Order II (Memory)**: How do we remember and recall?
- **Order III (Reason)**: How do we analyze quantitatively?
- **Order IV (Discourse)**: How do we communicate in language?
- **Order V (Truth)**: How do we ensure integrity?

This isn't mysticism - it's a cognitive architecture metaphor.

---

## 🌉 MCP Gateway (Model Context Protocol)

**Status**: ✅ Production Ready — 100% Domain-Agnostic (Refactored Feb 2026)

The **MCP Gateway** (port 8020) is a stateless bridge between LLMs (OpenAI Function Calling) and the Sacred Orders, providing:

- **5 Generic Tools**: `screen_entities`, `generate_vee_summary`, `query_signals`, `compare_entities`, `extract_semantic_context`
- **Orthodoxy Validation**: BLESSED/PURIFIED/HERETICAL filtering via config-driven thresholds (z-scores, composite scores, text length)
- **StreamBus Native**: Events emitted to `conclave.mcp.actions` channel  
- **Zero Domain Logic**: All entity types, factor names, and thresholds from ENV variables

**Architecture**: LIVELLO 1 (pure validation logic) + LIVELLO 2 (I/O adapters)

```bash
# Test MCP Gateway
curl -X POST http://localhost:8020/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "screen_entities",
    "args": {"entity_ids": ["entity_1", "entity_2"], "profile": "balanced"},
    "user_id": "test_user"
  }'

# Response includes orthodoxy_status
{
  "status": "success",
  "orthodoxy_status": "blessed",  # or "purified", "heretical"
  "data": {...},
  "execution_time_ms": 145.2
}
```

**See**: [Appendix K — MCP Integration](.github/Vitruvyan_Appendix_K_MCP_Integration.md)

---

## 📝 Status

**Current State**: Foundation Phase  
**Version**: 0.1.0-alpha  
**Created**: December 28, 2025

This is the clean fork from the original Vitruvyan trading system. Core execution paths and primitives are domain-neutral; finance remains as an optional reference vertical under `vitruvyan_core/domains/finance/`.

---

## 🔮 Future Work

- [ ] Complete Neural Engine abstraction
- [ ] Finalize GraphState aliases
- [ ] Implement domain plugin loader
- [ ] Add domain-specific tests
- [ ] Create deployment templates
- [ ] Document extension API

---

## 📖 Documentation

### Quick Links

**Start Here** (New Developer Onboarding):
- [📊 Module Status Map](docs/foundational/MODULE_STATUS_MAP.md) — **Single-source-of-truth inventory** (nodes, services, Sacred Orders, test coverage)
- [🔍 Pipeline Walkthrough](docs/foundational/VITRUVYAN_PIPELINE_WALKTHROUGH.md) — **Technical deep-dive** (code maps, flow diagrams, hook pattern)
- [📖 Copilot Instructions](.github/copilot-instructions.md) — **Architecture invariants** (Sacred Orders, hook pattern, LIVELLO 1/2)
- [🔌 Hook Pattern README](vitruvyan_core/domains/finance/README_HOOK_PATTERN.md) — **Domain plugin examples** (entity resolution, execution)

**Foundational Documents**:
- [📚 Documentation Portal](docs/index.md) — Entry point to all documentation
- [🏛️ Epistemic Charter](docs/foundational/Vitruvyan_Epistemic_Charter.md) — Philosophy & principles
- [🔗 Bus Invariants](docs/foundational/Vitruvyan_Bus_Invariants.md) — Cognitive Bus constraints
- [📋 Architecture Audit](docs/planning/_ALBERATURA_FRAMEWORK_DA-IMPLEMENTARE_FEB12_2026.md) — Reorganization roadmap

**Module Documentation** (see [📚 Documentation Organization](#-documentation-organization)):
- **LangGraph**: [vitruvyan_core/core/orchestration/langgraph/docs/](vitruvyan_core/core/orchestration/langgraph/docs/)
- **Synaptic Conclave**: [vitruvyan_core/core/synaptic_conclave/docs/](vitruvyan_core/core/synaptic_conclave/docs/)
- **Sacred Orders**: Each has `docs/` in its module directory
- **Services**: Each service has `docs/` in `services/api_*/docs/`

**Cross-Cutting Docs** (`docs/`):
- **Architecture**: [docs/architecture/](docs/architecture/) — Audits, refactoring plans, technical debt
- **Changelog**: [docs/changelog/](docs/changelog/) — Phase reports, checkpoints, completion reports
- **Foundational**: [docs/foundational/](docs/foundational/) — Charter, invariants, overview, research paper
- **Planning**: [docs/planning/](docs/planning/) — Strategic blueprints, TODO patterns
- **Testing**: [docs/testing/](docs/testing/) — Test plans, boot validation

### Build the Documentation Site (MkDocs)

```bash
# Prerequisites: Python 3 + pip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.docs.txt
mkdocs serve
```

Access at **http://localhost:8000**

---

## 📊 Project Status

**Foundation Phase — Consolidation (Feb 2026)**  
**Hook Pattern**: intent/entity/exec registries implemented (3/3)

- **Core Status:** Domain-agnostic substrate with optional vertical injection (stub fallback when a vertical is not configured)
- **Architecture:** Provider incarnation pattern proven
- **Validation:** See `docs/foundational/MODULE_STATUS_MAP.md` and `tests/` for current coverage and integration status
- **Next:** Vertical integrations (e.g., AEGIS) + end-to-end domain execution wiring

📋 **[Report Finale Completo](REPORT_FINALE.md)** - Documentazione dettagliata progetto

---

**Built with discipline. Extended with purpose.**

---

## 📜 Foundational Documents

These documents define the immutable principles of the Vitruvyan cognitive architecture:

### [Bus Invariants](docs/foundational/Vitruvyan_Bus_Invariants.md)
Defines the non-negotiable technical constraints on the Cognitive Bus. The bus is a **substrate for correlation and memory**, never for interpretation or action.

Key principles:
- Bus primitives: publish, subscribe, get_history, snapshot, restore
- Hard invariants: no payload inspection, no event synthesis, no orchestration
- Amendment protocol for any changes to these constraints

### [Epistemic Charter](docs/foundational/Vitruvyan_Epistemic_Charter.md)
Defines the philosophical and epistemic principles. Vitruvyan is a **digital twin**, not an oracle.

Key principles:
- "Non so" is a valid and complete response
- Never simulate certainty where there is uncertainty
- Respect expert authority in their domains
- Probabilistic reasoning everywhere

### [Vertical Specification](docs/foundational/Vitruvyan_Vertical_Specification.md)
Defines how to build domain-specific applications on the core.

Key sections:
- Three-layer architecture (Core, Adaptation, Vertical)
- VerticalInterface contract
- Domain ontology definition
- Uncertainty model implementation

### [Octopus Mycelium Architecture](docs/foundational/Vitruvyan_Octopus_Mycelium_Architecture.md)
Research paper on the bio-inspired distributed cognitive architecture.

Key contributions:
- Socratic cognitive system (declares uncertainty vs. hallucinating confidence)
- Autonomous local processing (octopus neurons) + resilient routing (mycelial networks)
- Epistemic integrity for life-critical decision support

---

## 📊 Technical Debt & Refactoring Status

### Current State (Feb 12, 2026)

- ✅ **SACRED_ORDER_PATTERN**: 100% conformance (6/6 Sacred Orders refactored)
- ✅ **Documentation**: Locality-first organization (77 files reorganized, Feb 2026)
- ⚠️ **Domain-Agnostic Refactoring**: 30/55 files verified agnostic, 13 mixed, 9 finance-specific

**Active Roadmaps**:
- [Architecture Audit](docs/planning/_ALBERATURA_FRAMEWORK_DA-IMPLEMENTARE_FEB12_2026.md) — Full tree reorganization plan
- [Architecture Docs](docs/architecture/) — Refactoring plans, technical debt audits, cleanup reports

**Historical Evolution**:
- See [docs/changelog/](docs/changelog/) for phase-by-phase refactoring history (Phase 0 → Phase 6)
- [Technical Debt Audit](docs/architecture/TECHNICAL_DEBT_AUDIT.md) (Jan 2026, historical reference)

The core originally contained ~134 files with finance-specific terminology. This has been incrementally abstracted through 6 refactoring phases (Dec 2025 → Feb 2026).
