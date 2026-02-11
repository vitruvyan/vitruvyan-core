# 🏛️ Vitruvyan Core

**Domain-Agnostic Agentic AI Framework**

Vitruvyan Core is the foundation of an epistemic AI system built around cognitive architecture principles. It provides orchestration, reasoning, memory, and governance layers that can be specialized for ANY domain through a plugin-based contract system.

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
│   ├── foundation/          # Database, cache, event bus
│   ├── cognitive/           # NLP, scoring, analysis
│   ├── orchestration/       # LangGraph decision flow
│   ├── governance/          # Validation, audit, archival
│   └── monitoring/          # Observability
├── domains/
│   ├── base_domain.py      # Domain contract (ABSTRACT)
│   └── example_domain.py   # Minimal placeholder
└── services/               # API wrappers
```

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

See individual component READMEs:
- [Foundation Layer](vitruvyan_core/core/foundation/README.md)
- [Orchestration](vitruvyan_core/core/orchestration/README.md)
- [Domain Contract](vitruvyan_core/domains/README.md)

### Build the docs site (MkDocs)

```bash
# Prereqs: Python 3 + pip
# Debian/Ubuntu: sudo apt-get install -y python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.docs.txt
mkdocs serve
```

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

---

## 🗂️ Technical Debt

See [Technical Debt Audit](docs/TECHNICAL_DEBT_AUDIT.md) for current abstraction status.

The core contains ~134 files with financial-specific terminology that needs abstraction. This is documented for incremental cleanup.
