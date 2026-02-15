# docs/ — Documentation Portal

> **Last Updated**: February 12, 2026  
> **Purpose**: Cross-cutting documentation (architecture, changelog, foundational)  
> **Organization**: Locality-First Pattern (Phase 1-2 reorganization complete)

---

## 🎯 Cosa Contiene

`docs/` è il **portal centrale** della documentazione cross-cutting di Vitruvyan — documenti che riguardano l'intero framework, non un singolo modulo.

**Caratteristiche**:
- ✅ **Organized by Purpose**: 7 categorie logiche (architecture, changelog, foundational, planning, prompts, services, testing)
- ✅ **Entry Point**: `index.md` per navigazione completa
- ✅ **Locality-First**: Module-specific docs stanno in `<module>/docs/`
- ✅ **77 Files Reorganized**: Feb 12, 2026 (Phase 1-2)

---

## 📂 Struttura

```
docs/
├── index.md                     # 📖 Documentation portal (START HERE)
│
├── architecture/                # 🏗️ Architecture (12 files)
│   ├── ARCHITECTURAL_DIALOGUE_RESPONSE.md
│   ├── ARCHITECTURAL_REFACTORING_FEB6_2026.md
│   ├── ARCHITECTURAL_SYNTHESIS_RESPONSE.md
│   ├── CLEANUP_AUDIT_JAN18.md
│   ├── TECHNICAL_DEBT_AUDIT.md
│   ├── TECH_DEBT_DOMAIN_MIGRATION.md
│   ├── CREWAI_DEPRECATION_PLAN.md
│   └── ...
│
├── changelog/                   # 📅 Changelog (21 files)
│   ├── CHANGELOG_JAN26_2026.md
│   ├── CHANGELOG_PHASE3_JAN26_2026.md
│   ├── CHANGELOG_PHASE6.md
│   ├── CHECKPOINT_PHASE1.md
│   ├── CHECKPOINT_PHASE1D.md
│   ├── COO_PHASE3_APPROVAL_REPORT.md
│   ├── PHASE1D_BOOT_TEST_FINAL_REPORT.md
│   ├── PHASE_0_BUS_HARDENING_REPORT.md
│   ├── PHASE_6_PLASTICITY_IMPLEMENTATION_REPORT.md
│   ├── REPORT_FINALE.md
│   └── ...
│
├── foundational/                # 🏛️ Foundational (7 files)
│   ├── Vitruvyan_Epistemic_Charter.md          ⭐ Philosophy & principles
│   ├── Vitruvyan_Bus_Invariants.md             ⭐ Cognitive Bus constraints
│   ├── Vitruvyan_Vertical_Specification.md     → Domain extension guide
│   ├── VITRUVYAN_OVERVIEW.md                   → What is Vitruvyan
│   ├── VITRUVYAN_PIPELINE_WALKTHROUGH.md       → Pipeline flow
│   ├── VITRUVYAN_CORE_STATUS_ANALYSIS.md       → Core status analysis
│   └── Vitruvyan_Octopus_Mycelium_Architecture.md  → Research paper
│
├── planning/                    # 🎯 Planning (2 files)
│   ├── _ALBERATURA_FRAMEWORK_CONSOLIDATA_FEB14_2026.md  ⭐ Reorganization roadmap
│   └── TODO_EXAMPLES_PATTERN.md
│
├── prompts/                     # 📝 Prompts (6 files)
│   ├── COPILOT_RESUME_PROMPT.md
│   ├── DEPLOYMENT_AGENT_PROMPT.md
│   ├── GROK_CLEANUP_PHASE2_PROMPT.md
│   ├── GROK_PHASE3_VEE_ABSTRACTION_PROMPT.md
│   ├── RESUME_DEBUG_SESSION.md
│   └── SACRED_ORDERS_REFACTORING_PROMPT.md
│
├── services/                    # 🌐 Services (2 files)
│   ├── mcp.md                   → MCP Gateway overview
│   └── codex_hunters.md         → Codex Hunters overview
│
└── testing/                     # 🧪 Testing (2 files)
    ├── BOOT_TEST_PLAN.md        → Boot test plan
    └── BOOT_TEST_STATUS.md      → Boot test status
```

---

## 🚀 Start Here

**Nuovi a Vitruvyan?** Leggi in questo ordine:

1. **[index.md](index.md)** — Documentation portal (entry point)
2. **[Epistemic Charter](foundational/Vitruvyan_Epistemic_Charter.md)** — Filosofia e principi fondamentali
3. **[Bus Invariants](foundational/Vitruvyan_Bus_Invariants.md)** — Cognitive Bus constraints (non-negoziabili)
4. **[VITRUVYAN_OVERVIEW.md](foundational/VITRUVYAN_OVERVIEW.md)** — Cos'è Vitruvyan e come funziona
5. **[ALBERATURA Framework](planning/_ALBERATURA_FRAMEWORK_CONSOLIDATA_FEB14_2026.md)** — 🚀 Post-refactoring reorganization roadmap

---

## 📚 Documentation Categories

### 🏗️ Architecture (12 files)

**Purpose**: Architectural audits, refactoring plans, technical debt analysis

**Key Documents**:
- [TECHNICAL_DEBT_AUDIT.md](architecture/TECHNICAL_DEBT_AUDIT.md) — Technical debt status (Jan 2026)
- [CLEANUP_AUDIT_JAN18.md](architecture/CLEANUP_AUDIT_JAN18.md) — Code cleanup audit
- [CREWAI_DEPRECATION_PLAN.md](architecture/CREWAI_DEPRECATION_PLAN.md) — CrewAI removal plan
- [ARCHITECTURAL_REFACTORING_FEB6_2026.md](architecture/ARCHITECTURAL_REFACTORING_FEB6_2026.md) — Post-Phase-6 refactoring

### 📅 Changelog (21 files)

**Purpose**: Phase-by-phase evolution history, checkpoints, COO approvals, final reports

**Key Documents**:
- [REPORT_FINALE.md](changelog/REPORT_FINALE.md) — Final comprehensive report
- [PHASE_6_PLASTICITY_IMPLEMENTATION_REPORT.md](changelog/PHASE_6_PLASTICITY_IMPLEMENTATION_REPORT.md) — Latest phase report
- [PHASE_0_BUS_HARDENING_REPORT.md](changelog/PHASE_0_BUS_HARDENING_REPORT.md) — Bus hardening (foundation)
- [CHECKPOINT_PHASE1.md](changelog/CHECKPOINT_PHASE1.md) — Phase 1 checkpoint

### 🏛️ Foundational (7 files)

**Purpose**: Core philosophy, charter, invariants, overview, research papers

**Key Documents** ⭐:
- [Vitruvyan_Epistemic_Charter.md](foundational/Vitruvyan_Epistemic_Charter.md) — **Immutable principles** (epistemic integrity, uncertainty, Socratic system)
- [Vitruvyan_Bus_Invariants.md](foundational/Vitruvyan_Bus_Invariants.md) — **Non-negotiable constraints** on Cognitive Bus
- [Vitruvyan_Vertical_Specification.md](foundational/Vitruvyan_Vertical_Specification.md) — How to build domain-specific applications
- [VITRUVYAN_OVERVIEW.md](foundational/VITRUVYAN_OVERVIEW.md) — Framework overview
- [Vitruvyan_Octopus_Mycelium_Architecture.md](foundational/Vitruvyan_Octopus_Mycelium_Architecture.md) — Bio-inspired architecture research paper

### 🎯 Planning (2 files)

**Purpose**: Strategic blueprints, master plans, TODO patterns

**Key Documents** 🚀:
- [_ALBERATURA_FRAMEWORK_CONSOLIDATA_FEB14_2026.md](planning/_ALBERATURA_FRAMEWORK_CONSOLIDATA_FEB14_2026.md) — **Master reorganization plan** (post-refactoring roadmap)
- [TODO_EXAMPLES_PATTERN.md](planning/TODO_EXAMPLES_PATTERN.md) — Examples directory pattern

### 📝 Prompts (6 files)

**Purpose**: Session work logs, debugging sessions, refactoring prompts

**Documents**:
- Session resume prompts (COPILOT_RESUME_PROMPT.md, RESUME_DEBUG_SESSION.md)
- Deployment prompts (DEPLOYMENT_AGENT_PROMPT.md)
- Refactoring session logs (SACRED_ORDERS_REFACTORING_PROMPT.md, GROK_CLEANUP_PHASE2_PROMPT.md)

### 🌐 Services (2 files)

**Purpose**: Service-level overviews (cross-cutting descriptions)

**Documents**:
- [mcp.md](services/mcp.md) — MCP Gateway (Model Context Protocol)
- [codex_hunters.md](services/codex_hunters.md) — Codex Hunters (Data Discovery)

### 🧪 Testing (2 files)

**Purpose**: Test plans, boot validation, status reports

**Documents**:
- [BOOT_TEST_PLAN.md](testing/BOOT_TEST_PLAN.md) — Boot test plan (Phase 1D)
- [BOOT_TEST_STATUS.md](testing/BOOT_TEST_STATUS.md) — Boot test status

---

## 🗂️ Module-Specific Documentation (Elsewhere)

**Important**: `docs/` contiene solo documentazione **cross-cutting**. 

**Module-specific docs** stanno nelle cartelle dei rispettivi moduli (locality-first pattern):

### Core Modules
- **LangGraph**: `vitruvyan_core/core/orchestration/langgraph/docs/`
- **Synaptic Conclave**: `vitruvyan_core/core/synaptic_conclave/docs/`
- **Neural Engine**: `vitruvyan_core/core/neural_engine/docs/`

### Sacred Orders
- **Memory Orders**: `vitruvyan_core/core/governance/memory_orders/docs/`
- **Vault Keepers**: `vitruvyan_core/core/governance/vault_keepers/docs/`
- **Orthodoxy Wardens**: `vitruvyan_core/core/governance/orthodoxy_wardens/docs/`
- **Codex Hunters**: `vitruvyan_core/core/governance/codex_hunters/docs/`
- **Babel Gardens**: `vitruvyan_core/core/cognitive/babel_gardens/docs/`
- **Pattern Weavers**: `vitruvyan_core/core/cognitive/pattern_weavers/docs/`

### Services
- **MCP Gateway**: `services/api_mcp/docs/`
- **Orthodoxy Wardens Service**: `services/api_orthodoxy_wardens/docs/`

### Infrastructure
- **Monitoring**: `infrastructure/monitoring/docs/`

---

## 📖 How to Navigate

**Scenario 1: Capire la filosofia di Vitruvyan**
→ Leggi [foundational/](#-foundational-7-files) (Charter, Bus Invariants, Overview)

**Scenario 2: Vedere l'evoluzione del progetto**
→ Leggi [changelog/](#-changelog-21-files) (fase per fase, Dec 2025 → Feb 2026)

**Scenario 3: Pianificare il futuro**
→ Leggi [planning/](#-planning-2-files) (ALBERATURA roadmap, TODO patterns)

**Scenario 4: Capire l'architettura attuale**
→ Leggi [architecture/](#-architecture-12-files) (audits, refactoring plans, technical debt)

**Scenario 5: Lavorare su un modulo specifico**
→ Vai a `<module>/docs/` (non qui — locality-first pattern)

---

## 🎯 Locality-First Pattern

**Philosophy**: Documentation lives with the code it documents.

**Global docs** (qui):
- Cross-cutting concerns (philosophy, architecture, evolution history)
- Strategic planning (roadmaps, master plans)
- Service-level overviews (high-level descriptions)

**Module docs** (altrove):
- Implementation details (API reference, examples, patterns)
- Module-specific refactoring (audit, migration guides)
- Local decisions (architecture decisions, design notes)

**Benefit**: Riduce coupling, migliora discoverability, abilita parallel work.

---

## 📊 Reorganization History

### February 12, 2026 — Phase 1-2

**77 files riorganizzati** in 2 commit:

**Phase 1** (commit f1efd20):
- 39 file da **root repo** → module-specific `docs/`
- Root cleanup: solo `README.md` rimasto

**Phase 2** (commit 28f5b4a):
- 38 file da **docs/ root** → 7 categorie logiche
- 1 duplicato rimosso (REDIS_STREAMS_ARCHITECTURE.md)
- docs/ cleanup: solo `index.md` rimasto

**Result**: Locality-first organization, clear ownership, parallel work enabled.

---

## 📖 Link Utili

- **[Back to Main README](../README.md)** — Repository overview
- **[Vitruvyan Core](../vitruvyan_core/README_VITRUVYAN_CORE.md)** — Core library
- **[Services](../services/README_SERVICES.md)** — Microservices
- **[Infrastructure](../infrastructure/README_INFRASTRUCTURE.md)** — Docker, monitoring
- **[Tests](../tests/README_TESTS.md)** — Test suite

---

**Purpose**: Cross-cutting documentation portal.  
**Organization**: Locality-First Pattern (7 categories, 52 files).  
**Status**: Phase 1-2 reorganization complete (Feb 12, 2026).
