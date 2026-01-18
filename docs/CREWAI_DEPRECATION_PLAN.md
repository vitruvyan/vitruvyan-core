# CrewAI Removal Plan
**Date**: January 18, 2026  
**Status**: PLANNED  
**Decision**: DELETE without replacement

---

## Executive Summary

CrewAI will be **removed entirely** from `vitruvyan-core`. No replacement framework is needed.

**Rationale:**
1. CrewAI was used only for Mercator-specific financial agents
2. LangGraph already handles orchestration
3. Agentic modules run as Docker services with REST APIs
4. Aegis doesn't use CrewAI
5. The core doesn't need an agent framework — it needs orchestration (LangGraph) and services (Docker)

---

## Architecture Without CrewAI

```
┌─────────────────────────────────────────────────┐
│                  LangGraph                       │
│            (Orchestration Layer)                 │
│   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐              │
│   │Node │→│Node │→│Node │→│Node │              │
│   └─────┘ └─────┘ └─────┘ └─────┘              │
└─────────────────────────────────────────────────┘
                      ↓ HTTP/Redis
┌─────────────────────────────────────────────────┐
│              Docker Services                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ Codex    │ │ Pattern  │ │ Neural   │        │
│  │ Hunters  │ │ Weavers  │ │ Engine   │  ...   │
│  │ :8001    │ │ :8017    │ │ :8003    │        │
│  └──────────┘ └──────────┘ └──────────┘        │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│            Cognitive Bus (Redis)                 │
│         Event-driven communication               │
└─────────────────────────────────────────────────┘
```

**This is already the architecture. CrewAI was a detour.**

---

## Files to Delete

```
vitruvyan_core/core/orchestration/crewai/     # DELETE ENTIRE FOLDER
├── __init__.py
├── base_agent.py
├── base_tool.py
└── logging_utils.py
```

## Files to Clean (remove CrewAI imports)

```
vitruvyan_core/core/orchestration/langgraph/node/crew_node.py      # DELETE or refactor
vitruvyan_core/core/orchestration/langgraph/node/quality_check_node.py
vitruvyan_core/core/orchestration/langgraph/node/compose_node.py
vitruvyan_core/core/orchestration/langgraph/node/llm_soft_node.py
vitruvyan_core/core/orchestration/langgraph/node/output_normalizer_node.py
vitruvyan_core/core/orchestration/langgraph/graph_flow.py

vitruvyan_core/core/foundation/cognitive_bus/herald.py
vitruvyan_core/core/foundation/cognitive_bus/event_schema.py
vitruvyan_core/core/foundation/cognitive_bus/lexicon.py

vitruvyan_core/core/governance/vault_keepers/chamberlain.py
vitruvyan_core/core/governance/vault_keepers/chamberlain_crewai_backup.py  # DELETE
```

---

## Migration Steps

### Phase 1: Delete CrewAI folder (5 min)
```bash
rm -rf vitruvyan_core/core/orchestration/crewai/
```

### Phase 2: Remove imports from LangGraph nodes (1-2 hours)
- Remove `from crewai import ...` statements
- Replace CrewAI agent calls with direct HTTP calls to Docker services
- Or simply remove unused code paths

### Phase 3: Update requirements.txt (5 min)
```bash
# Remove crewai from dependencies
pip uninstall crewai
```

### Phase 4: Test (1 hour)
- Verify LangGraph flow works without CrewAI
- Verify Docker services respond correctly

---

## Why No Replacement?

| Need | Solution (Already Exists) |
|------|---------------------------|
| Orchestration | LangGraph |
| Agent execution | Docker services + REST APIs |
| Inter-agent communication | Cognitive Bus (Redis pub/sub) |
| Task delegation | LangGraph conditional edges |
| Logging/Audit | Sacred Orders (Vault Keepers) |

**CrewAI added complexity without value.**

---

## Timeline

| Task | Effort |
|------|--------|
| Delete crewai folder | 5 min |
| Clean imports | 1-2 hours |
| Update deps | 5 min |
| Test | 1 hour |
| **Total** | **~3 hours** |

---

## Decision Log

| Date | Decision |
|------|----------|
| Jan 18, 2026 | CrewAI deprecation decided |
| Jan 18, 2026 | Changed from "replace" to "delete without replacement" |
| Jan 18, 2026 | Confirmed: LangGraph + Docker services = sufficient |
