# 🧠 Vitruvyan OS

<p class="kb-subtitle"><strong>A Domain-Agnostic Cognitive Framework for Explainable Intelligence</strong></p>

<div class="kb-hero">
  <p class="kb-hero__tagline">A cognitive kernel for building intelligent systems</p>
  <p class="kb-hero__cta">
    <a href="/docs/" class="md-button md-button--primary">Enter Documentation</a>
    <a href="/admin/" class="md-button">Admin Access</a>
  </p>
</div>

---

## 1. What is Vitruvyan OS

Vitruvyan OS is a **modular cognitive framework** designed to build intelligent systems that are **explainable**, **auditable**, and **governed**.

It’s not “just an LLM wrapper”.
It’s a distributed architecture that cleanly separates:

- perception
- memory
- reasoning
- language
- truth & governance

into independent but coordinated modules.

The result is a system that can reason, explain, and—most importantly—declare its own limits.

## 2. Why it was created

Vitruvyan was born from a precise need: to move beyond the monolithic **“prompt → answer”** paradigm.

Traditional AI systems often:

- don’t distinguish computation from narration
- don’t track causality
- don’t have structured memory
- don’t have internal governance

Vitruvyan OS was designed as a distributed cognitive system inspired by:

- biological neural networks (local autonomy)
- mycelial networks (emergent coordination)
- modern event-driven architectures

Intelligence isn’t concentrated in a single model: it **emerges** from the interaction between specialized modules.

## 3. High-level architecture

Vitruvyan OS stands on three structural pillars:

### 🕸 Orchestration

Cognitive flows are managed with conversational graphs and intent-based routing.
Each request traverses analysis, validation, and composition nodes.

### 🧠 Cognitive Bus

A sophisticated, distributed event bus (Redis Streams-based) that provides:

- asynchronous communication between modules
- causal traceability
- fault isolation
- event replay

No module depends directly on another: everything communicates through structured events.

### ⚖ Governance & Audit

Every output can be:

- validated
- corrected
- rejected
- marked as uncertain

The system integrates an epistemic control layer that prevents unfounded answers.

## 4. Domain agnosticism

Vitruvyan OS is **domain-agnostic**.

That means:

- it’s not limited to finance
- it’s not tied to a single use case
- it’s not dependent on a single AI model

Domain logic lives in specialized verticals.

Example verticalization:

- Trading Intelligence
- Risk Monitoring
- Compliance Systems
- Portfolio Governance
- Defense & Civil Protection Systems
- Knowledge Graph Intelligence

The core stays invariant.
You specialize the domain, not the architecture.

## 5. How a vertical is built

A vertical in Vitruvyan OS:

- defines domain ontology and models
- implements specialized agents
- integrates scoring/evaluation logic
- connects to the Cognitive Bus
- inherits automatically:
  - structured memory
  - explainability
  - audit trail
  - governance

This lets you build complex systems without reinventing orchestration, audit, traceability, and event management.

## 6. Explainable intelligence, not opaque

Vitruvyan OS separates:

- quantitative computation
- semantic fusion
- linguistic narration
- epistemic validation

Every decision can be reconstructed.
Every output can be traced back to its causal origin.

This makes it suitable for:

- regulated environments
- institutional contexts
- mission-critical systems

## 7. Vision

Vitruvyan OS is not a single product.
It is a **cognitive operating system**.

A framework to build:

- modular agentic AI
- multi-service systems
- distributed intelligent infrastructures
- auditable architectures for complex domains

The goal is not to generate text.
It is to generate **structured, governed intelligence**.

---

Vitruvyan Core is a **domain-agnostic operating system** for epistemic processing — the foundation for building intelligent systems that reason, remember, and evolve.

Unlike traditional frameworks tied to specific verticals (finance, healthcare, etc.), Vitruvyan provides **pure cognitive primitives** that adapt to any domain:

- **🧠 Perception**: Ingest and normalize heterogeneous inputs
- **💾 Memory**: Persistent semantic and structural state
- **⚡ Reason**: Deterministic and explainable computations
- **📖 Discourse**: Transform system state into narratives
- **✅ Truth**: Governance, validation, and audit trails

---

## Architecture Highlights

### Sacred Orders Pattern
Vitruvyan organizes capabilities into autonomous **Sacred Orders** — cognitive microservices with strict separation:

| Order | Responsibility | Example Use Cases |
|-------|----------------|-------------------|
| **Memory Orders** | Semantic coherence, RAG operations | Context retrieval, knowledge synthesis |
| **Vault Keepers** | Archival, persistence, snapshots | Event sourcing, audit logs |
| **Orthodoxy Wardens** | Code quality, validation, governance | CI/CD integration, policy enforcement |
| **Babel Gardens** | Multilingual NLP, emotion detection | Conversational AI, sentiment analysis |
| **Codex Hunters** | System introspection, maintenance | Auto-documentation, dependency mapping |
| **Pattern Weavers** | Behavioral analysis, anomaly detection | Signal extraction, pattern mining |

### LangGraph Cognitive Pipeline
A **100% domain-agnostic graph** orchestrating intent detection → semantic grounding → execution → validation.

**Pluggable verticals**: Finance, healthcare, legal — add your domain without touching core logic.

### Synaptic Conclave (Event Bus)
**Redis Streams**-based cognitive transport with:
- Payload-blind routing (no semantic coupling)
- Consumer group autonomy
- Event traceability and replay

---

## Access Levels

Vitruvyan documentation is organized into **two access tiers**:

### 🔓 Basic Access (Developers & Integrators)
**What you get**:
- ✅ Full API documentation for all Sacred Orders
- ✅ Service architecture and deployment guides
- ✅ Integration examples and usage patterns
- ✅ LangGraph pipeline specifications
- ✅ Testing and development workflows

**Who needs this**:
- Backend developers integrating Vitruvyan into applications
- DevOps engineers deploying services
- Architects evaluating the system

**Request access**: Contact the core team for basic credentials.

---

### 🔐 Advanced Access (Core Team & Contributors)
**What you get** (everything in Basic +):
- ✅ Roadmaps and strategic planning documents
- ✅ Technical debt tracking and refactoring plans
- ✅ Proprietary algorithm specifications
- ✅ Internal architecture decision records (ADRs)
- ✅ Sacred Orders constitutional documents (charters)

**Who needs this**:
- Core maintainers and committers
- Strategic partners with IP agreements
- Funded contributors working on internals

**Request access**: Advanced credentials require NDA or contribution agreement.

---

## Getting Started

### 1. Request Credentials

**For Basic Access** (developers):
```bash
# Contact: vitruvyan-access@yourdomain.com
# Subject: Knowledge Base Access Request - Basic
# Include: Name, role, organization, use case
```

**For Advanced Access** (core team):
```bash
# Contact: vitruvyan-core@yourdomain.com
# Subject: Knowledge Base Access Request - Advanced
# Include: Contributor agreement or NDA reference
```

### 2. Access the Knowledge Base

Once you receive credentials, visit:

- **Basic Access**: [https://kb.vitruvyan.com/](https://kb.vitruvyan.com/)
- **Advanced Sections**: [https://kb.vitruvyan.com/planning/](https://kb.vitruvyan.com/planning/)

Use HTTP Basic Authentication when prompted.

---

## Quick Links (Preview)

<div style="background: #f5f5f5; padding: 1.5rem; border-radius: 8px; margin: 1rem 0;">

**🔒 Behind authentication** — these paths require credentials:

- **Getting Started**: `/` (Basic access)
- **Sacred Orders Architecture**: `/docs/foundational/` (Basic)
- **Service Deployment**: `/services/` (Basic)
- **LangGraph Pipeline**: `/docs/architecture/` (Basic)
- **Roadmaps & Planning**: `/planning/` (**Advanced only**)
- **Refactoring Plans**: `/docs/technical-debt/` (**Advanced only**)

</div>

---

## Why Vitruvyan?

### Domain-Agnostic by Design
Finance, healthcare, legal, operations — **one OS, infinite verticals**. Add your domain as a plugin without rewriting infrastructure.

### Sacred Orders Pattern
**Strict separation of concerns** inspired by epistemic hierarchy. Each Order has a constitutional charter defining mandate, invariants, and boundaries.

### LangGraph + MCP Integration
Modern AI orchestration with **OpenAI Function Calling** and **Model Context Protocol** for tool use.

### Event-Driven Architecture
**Pure payload-blind transport** (Redis Streams). No semantic coupling, full auditability, reproducible state.

### Open Core Philosophy
Core primitives are open. Verticals and proprietary algorithms available under commercial agreements.

---

## Repository Structure

```
vitruvyan-core/
├── vitruvyan_core/         # Reusable OS core (agents, bus, governance)
│   ├── core/agents/        # PostgreSQL, Qdrant, LLM agents
│   ├── core/governance/    # Sacred Orders (Memory, Vault, Orthodoxy...)
│   ├── core/orchestration/ # LangGraph pipeline (domain-agnostic)
│   └── core/synaptic_conclave/  # Event bus (Redis Streams)
├── services/               # Reference microservices
│   ├── api_memory_orders/  # Semantic coherence service
│   ├── api_vault_keepers/  # Archival service
│   ├── api_orthodoxy_wardens/  # Governance service
│   └── api_graph/          # LangGraph orchestration service
├── domains/                # Domain plugins (finance example included)
└── infrastructure/         # Docker, Nginx, monitoring (Grafana, Prometheus)
```

---

## Technical Stack

- **Language**: Python 3.11+
- **Orchestration**: LangGraph (graph-based workflows)
- **LLM**: OpenAI GPT-4o (configurable via `LLMAgent`)
- **Vector DB**: Qdrant (semantic memory)
- **Persistence**: PostgreSQL (structured state)
- **Bus**: Redis Streams (event transport)
- **Monitoring**: Grafana + Prometheus
- **Containers**: Docker Compose

---

## License

**Core**: Open source (specify license: MIT/Apache 2.0)  
**Verticals**: Proprietary (commercial agreements)  
**Algorithms**: Patent-pending (NDA required for specifications)

---

## Contact

- **General inquiries**: info@vitruvyan.com
- **Basic access**: vitruvyan-access@yourdomain.com
- **Advanced access**: vitruvyan-core@yourdomain.com

---

<div style="text-align: center; padding: 1rem 0; color: #666;">
  <p>Vitruvyan OS — Built for systems that think.</p>
  <p style="font-size: 0.9rem;">© 2026 Vitruvyan Team. All rights reserved.</p>
</div>
