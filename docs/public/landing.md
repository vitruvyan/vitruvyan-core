# Vitruvyan Core — Domain-Agnostic Epistemic Operating System

<div style="text-align: center; padding: 2rem 0;">
  <p style="font-size: 1.3rem; color: #5e35b1; font-weight: 500;">
    A cognitive kernel for building intelligent systems
  </p>
</div>

---

## What is Vitruvyan?

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
- **GitHub**: [github.com/vitruvyan/vitruvyan-core](https://github.com/vitruvyan/vitruvyan-core)

---

<div style="text-align: center; padding: 2rem 0; color: #666;">
  <p>Vitruvyan Core — Built for systems that think.</p>
  <p style="font-size: 0.9rem;">© 2026 Vitruvyan Team. All rights reserved.</p>
</div>
