# 🏛️ Vitruvyan Core

**Domain-Agnostic Agentic AI Framework**

> **Last Updated**: February 12, 2026  
> **Version**: 0.1.0-alpha  
> **Status**: Foundation Phase — Post-Refactoring (SACRED_ORDER_PATTERN 100% Conformance)

Vitruvyan Core is the foundation of an epistemic AI system built around cognitive architecture principles. It provides orchestration, reasoning, memory, and governance layers that can be specialized for ANY domain through a plugin-based contract system.

---

## 📖 New to Vitruvyan?

**Quick Orientation**:
1. Read [🎯 What is Vitruvyan Core?](#-what-is-vitruvyan-core) to understand the philosophy
2. Review [🗂️ Repository Structure](#-repository-structure) to navigate the codebase
3. Check [📚 Documentation Organization](#-documentation-organization) to find relevant docs
4. Explore [🏗️ Architecture](#-architecture) to understand the Sacred Orders pattern

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

## 🧠 Philosophy: Structure, Not Solution

### What Vitruvyan Core Is NOT

Vitruvyan Core is not a framework with ready-made components.  
It is not a library of best practices.  
It is not a collection of domain-specific tools.

**It is a blank cognitive substrate.**

Think of it as:
- A CPU without an operating system
- An empty factory floor with conveyor belts, but no workers or products
- A spreadsheet with formula support, but no data

### Core Has Zero Opinions

The core has **zero opinions** about:

- What makes an entity "good" or "bad"
- Which factors matter in your domain
- How to weigh different dimensions of quality
- What "normal" or "optimal" means
- How to interpret scores or rankings

It provides **no domain knowledge**:
- No entity entity_ids, sectors, or financial ratios
- No patient symptoms, diagnoses, or treatments
- No routes, vehicles, or delivery windows
- No weapons systems, threat levels, or readiness scores

### What The Core DOES Provide

The core provides **structure without content**:

1. **Abstract contracts** that define what evaluation means
2. **Orchestration flows** that coordinate cognitive processes
3. **Data structures** for inputs, outputs, and state management
4. **One reference implementation** to show how contracts work

### Ontological Neutrality

The core does not teach you **what to evaluate**.  
It teaches you **how to structure evaluation**.

It says: "If you have dimensions of quality, here's how to:
- Normalize them to comparable scales
- Combine them into composites
- Track contributions and explanations"

But it never tells you:
- Which dimensions matter
- How to compute them
- What the results mean

### Verticals Are Epistemologically Specific

Your vertical makes the **epistemological choices**:

- **Mercator** says: "Quality = momentum + trend + volatility"
- **AEGIS** says: "Readiness = training + equipment + morale"
- **Your domain** says: "[YOUR DEFINITION OF QUALITY]"

The core doesn't care. It executes the structure you define.

### Anti-Framework Design

Most systems are frameworks that suggest what to do.  
Vitruvyan Core inverts this: it provides zero suggestions.

By providing **only structure**, the core forces you to think:
- What does "better" mean in my domain?
- How do I measure the qualities that matter?
- What tradeoffs am I making?

You can't cargo-cult from the core. You must understand your domain.

### The Inevitable Discomfort

Using Vitruvyan Core **should feel uncomfortable at first**.

You will think: "But where are the examples?"  
You will ask: "What's the best way to do X?"

**This discomfort is intentional.**  
It's the discomfort of taking responsibility for your domain's conceptual model.

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

## 🔌 Domain Extension System

Vitruvyan Core uses a **Domain Contract** pattern to remain agnostic while enabling vertical specialization.

### Domain Contract

Any domain must implement:

1. **Entity Schema** — What are the "things"?
2. **Signal Schema** — What measurable attributes exist?
3. **Scoring Factors** — What dimensions drive decisions?
4. **Policies** — What domain rules apply?
5. **Explanation Templates** — How to explain outcomes?

### Example Domains (Future)

- **Trade**: entities=entities, signals=momentum/volatility, factors=RSI/MACD
- **Logistics**: entities=routes, signals=traffic/weather, factors=cost/time  
- **Healthcare**: entities=patients, signals=vitals, factors=risk_scores
- **Defense**: entities=assets, signals=threats, factors=readiness
- **Legal**: entities=cases, signals=precedents, factors=probability

None of these are implemented in Core. They would be separate plugins.

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

## 🚀 Quick Start (Placeholder)

```python
from vitruvyan_core.domains import get_domain, GenericDomain

# Use generic domain (no specialization)
domain = get_domain("generic")

# Future: Load a specific domain plugin
# domain = get_domain("logistics")

# Run analysis
entity = domain.get_entity_schema()
signal = domain.compute_signal(entity, "example_signal")
```

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

This is the clean fork from the original Vitruvyan trading system. All finance-specific logic has been abstracted out, leaving a domain-neutral agentic core.

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

**Getting Started**:
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

**✅ Phase 4A Complete - Mercator Vertical Validated**  
**🚀 Phase 4B Ready - AEGIS Vertical Development**

- **Core Status:** Fully domain-agnostic and validated
- **Architecture:** Provider incarnation pattern proven
- **Validation:** All tests passing, 95%+ coverage
- **Next:** AEGIS governance vertical implementation

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
