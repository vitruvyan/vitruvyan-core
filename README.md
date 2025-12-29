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

- **Trade**: entities=stocks, signals=momentum/volatility, factors=RSI/MACD
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

---

**Built with discipline. Extended with purpose.**
