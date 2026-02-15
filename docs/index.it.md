# Vitruvyan Core — Documentation Portal

> **Last Updated**: February 12, 2026  
> **Organization**: Locality-First Pattern (Phase 1-2 Reorganization Complete)

Questa è la documentazione del progetto **Vitruvyan Core** — un framework agentic AI domain-agnostic basato su architettura cognitiva.

---

## 🚀 Start Here

**New to Vitruvyan?** Inizia da questi documenti chiave:

- [📖 Overview](foundational/VITRUVYAN_OVERVIEW.md) — Cos'è Vitruvyan e come funziona
- [🏛️ Epistemic Charter](foundational/Vitruvyan_Epistemic_Charter.md) — Filosofia e principi fondamentali
- [🔗 Bus Invariants](foundational/Vitruvyan_Bus_Invariants.md) — Cognitive Bus constraints
- [🧬 Octopus Mycelium Architecture](foundational/Vitruvyan_Octopus_Mycelium_Architecture.md) — Research paper (bio-inspired architecture)

---

## 📚 Global Documentation (docs/)

Documentazione cross-cutting organizzata per categoria:

### 🏗️ Architecture (12 files)
Audit architetturali, refactoring plans, technical debt:
- [Architecture Audits & Refactoring Plans](architecture/)
- [Technical Debt Audit](architecture/TECHNICAL_DEBT_AUDIT.md)
- [Cleanup Audit](architecture/CLEANUP_AUDIT_JAN18.md)
- [CrewAI Deprecation Plan](architecture/CREWAI_DEPRECATION_PLAN.md)

### 📅 Changelog (21 files)
Phase reports, checkpoints, COO approvals:
- [Phase Reports & Completion](changelog/)
- [Report Finale](changelog/REPORT_FINALE.md)
- [Phase 6 Plasticity Report](changelog/PHASE_6_PLASTICITY_IMPLEMENTATION_REPORT.md)

### 🏛️ Foundational (7 files)
Core philosophy, charter, invariants, overview:
- [Vitruvyan Overview](foundational/VITRUVYAN_OVERVIEW.md)
- [Epistemic Charter](foundational/Vitruvyan_Epistemic_Charter.md)
- [Bus Invariants](foundational/Vitruvyan_Bus_Invariants.md)
- [Vertical Specification](foundational/Vitruvyan_Vertical_Specification.md)
- [Pipeline Walkthrough](foundational/VITRUVYAN_PIPELINE_WALKTHROUGH.md)
- [Core Status Analysis](foundational/VITRUVYAN_CORE_STATUS_ANALYSIS.md)
- [Octopus Mycelium Architecture](foundational/Vitruvyan_Octopus_Mycelium_Architecture.md) (research paper)

### 🎯 Planning (2 files)
Strategic blueprints, TODO patterns:
- [**ALBERATURA Framework**](planning/_ALBERATURA_FRAMEWORK_CONSOLIDATA_FEB14_2026.md) — 🚀 Post-refactoring reorganization roadmap
- [TODO Examples Pattern](planning/TODO_EXAMPLES_PATTERN.md)

### 📝 Prompts (6 files)
Session work logs:
- [Session Prompts](prompts/)

### 🧪 Testing (2 files)
Test plans, boot validation:
- [Boot Test Plan](testing/BOOT_TEST_PLAN.md)
- [Boot Test Status](testing/BOOT_TEST_STATUS.md)

### 🌐 Services (2 files)
Service descriptions:
- [MCP Gateway](services/mcp.md) — Model Context Protocol
- [Codex Hunters](services/codex_hunters.md) — Data Discovery

---

## 🗂️ Module-Specific Documentation (Locality-First)

Ogni modulo ha la propria cartella `docs/` co-locata con il codice:

### Core Modules

**LangGraph Orchestration**  
→ [`vitruvyan_core/core/orchestration/langgraph/docs/`](../vitruvyan_core/core/orchestration/langgraph/docs/)

**Synaptic Conclave (Cognitive Bus)**  
→ [`vitruvyan_core/core/synaptic_conclave/docs/`](../vitruvyan_core/core/synaptic_conclave/docs/)

**Neural Engine**  
→ [`vitruvyan_core/core/neural_engine/docs/`](../vitruvyan_core/core/neural_engine/docs/)

### Sacred Orders (Governance Subsystems)

**Memory Orders**  
→ [`vitruvyan_core/core/governance/memory_orders/docs/`](../vitruvyan_core/core/governance/memory_orders/docs/)

**Vault Keepers**  
→ [`vitruvyan_core/core/governance/vault_keepers/docs/`](../vitruvyan_core/core/governance/vault_keepers/docs/)

**Orthodoxy Wardens**  
→ [`vitruvyan_core/core/governance/orthodoxy_wardens/docs/`](../vitruvyan_core/core/governance/orthodoxy_wardens/docs/)

**Codex Hunters**  
→ [`vitruvyan_core/core/governance/codex_hunters/docs/`](../vitruvyan_core/core/governance/codex_hunters/docs/)

**Babel Gardens**  
→ [`vitruvyan_core/core/cognitive/babel_gardens/docs/`](../vitruvyan_core/core/cognitive/babel_gardens/docs/)

**Pattern Weavers**  
→ [`vitruvyan_core/core/cognitive/pattern_weavers/docs/`](../vitruvyan_core/core/cognitive/pattern_weavers/docs/)

---

## 🏗️ SACRED_ORDER_PATTERN

Tutti i Sacred Orders seguono il **pattern a due livelli obbligatorio**:

- **LIVELLO 1** (Pure Domain): 10 directory (`domain/`, `consumers/`, `governance/`, `events/`, `monitoring/`, `philosophy/`, `docs/`, `examples/`, `tests/`, `_legacy/`)
- **LIVELLO 2** (Service): I/O adapters, REST API, Docker deployment

**Status**: ✅ 100% conformance (6/6 Sacred Orders refactored, Feb 2026)
