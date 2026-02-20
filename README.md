# 🏛️ Vitruvyan Core

**Domain-Agnostic Agentic AI Framework**

> **Last Updated**: February 20, 2026 (v1.2.0: Update Manager + Complete Pipeline Visualization)  
> **Version**: 1.2.0  
> **Status**: Foundation Phase — Update System Integrated (SACRED_ORDER_PATTERN 100%)

Vitruvyan Core is an **opinionated architectural framework** for multi-service, multi-domain agentic AI systems. It provides LangGraph orchestration, Redis Streams event bus, Sacred Orders governance, and domain-agnostic primitives that can be specialized through a **registry-based plugin pattern** (hook registries + environment selection).

---

## 🔧 Update Manager CLI

Vitruvyan Core includes a built-in **update management system** (`vit` CLI) that works **out-of-the-box** without installation:

```bash
# Check for updates (works immediately after git clone)
./vit status

# Add to PATH for global access (optional)
export PATH="$(pwd):${PATH}"
vit --help
```

**Key Features**:
- ✅ **Zero installation** — works immediately without `pip install`
- ✅ **Auto-configured autocomplete** — bash tab completion enabled automatically
- ✅ **GitHub authentication** — auto-detects `gh` token for private repositories
- ✅ **Semantic versioning** — update/upgrade/rollback with smoke tests
- ✅ **Rollback snapshots** — automatic git tags before upgrades
- ✅ **Audit logging** — complete upgrade history in `.vitruvyan/upgrade_history.json`

**Essential Commands**:
```bash
vit status              # Current version + available updates
vit plan                # Preview upgrade plan (dry-run)
vit update              # Pull latest changes
vit upgrade             # Update + smoke tests + rollback support
vit rollback            # Revert to previous version
```

**Autocomplete** (enabled automatically on first run):
```bash
vit <TAB>               # Commands: status, update, upgrade, plan, rollback
vit upgrade --<TAB>     # Flags: --channel, --target, --yes, --json
vit upgrade --channel <TAB>  # Channels: stable, beta
```

📚 **Full guide**: [VIT_CLI_QUICKSTART.md](VIT_CLI_QUICKSTART.md)  
📋 **Contract**: [UPDATE_SYSTEM_CONTRACT_V1.md](docs/contracts/platform/UPDATE_SYSTEM_CONTRACT_V1.md)

---

## 🚀 Quick Start
````
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
# Basic query (default: generic domain; set INTENT_DOMAIN=finance for finance intents)
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
    "results": [],  # Empty (exec_node is stub)
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
- [📋 Architecture Audit](docs/planning/_ALBERATURA_FRAMEWORK_CONSOLIDATA_FEB14_2026.md) — Reorganization roadmap

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
- **Next:** Vertical integrations (e.g., Vitruvyan) + end-to-end domain execution wiring

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
- [Architecture Audit](docs/planning/_ALBERATURA_FRAMEWORK_CONSOLIDATA_FEB14_2026.md) — Full tree reorganization plan
- [Architecture Docs](docs/architecture/) — Refactoring plans, technical debt audits, cleanup reports

**Historical Evolution**:
- See [docs/changelog/](docs/changelog/) for phase-by-phase refactoring history (Phase 0 → Phase 6)
- [Technical Debt Audit](docs/architecture/TECHNICAL_DEBT_AUDIT.md) (Jan 2026, historical reference)

The core originally contained ~134 files with finance-specific terminology. This has been incrementally abstracted through 6 refactoring phases (Dec 2025 → Feb 2026).
