# Vitruvyan-Core Technical Debt Audit
**Date**: January 18, 2026  
**Updated**: January 18, 2026  
**Objective**: Document contamination and deprecations for core abstraction

---

## Executive Summary

The `vitruvyan-core` repository has two major technical debt categories:

1. **Domain Contamination**: **134 files** with financial-specific terminology (ticker, AAPL, stock, portfolio)
2. **CrewAI Deprecation**: **20 files** with CrewAI dependency to be replaced with native agents

---

## 🚨 CrewAI Deprecation (HIGH PRIORITY)

**Decision**: Deprecate CrewAI in favor of native Vitruvyan agents.

**Rationale**: During Mercator development, we realized that agent work can be done with custom implementations that better integrate with Sacred Orders.

**Affected Files (20):**
```
vitruvyan_core/core/orchestration/crewai/ (4 files, 523 lines total)
├── __init__.py
├── base_agent.py
├── base_tool.py
└── logging_utils.py

vitruvyan_core/core/orchestration/langgraph/node/crew_node.py
vitruvyan_core/core/orchestration/langgraph/node/quality_check_node.py
vitruvyan_core/core/orchestration/langgraph/node/compose_node.py
vitruvyan_core/core/orchestration/langgraph/node/llm_soft_node.py
vitruvyan_core/core/orchestration/langgraph/node/output_normalizer_node.py
vitruvyan_core/core/orchestration/langgraph/graph_flow.py

vitruvyan_core/core/foundation/cognitive_bus/herald.py
vitruvyan_core/core/foundation/cognitive_bus/event_schema.py
vitruvyan_core/core/foundation/cognitive_bus/lexicon.py

vitruvyan_core/core/governance/vault_keepers/chamberlain.py
vitruvyan_core/core/governance/vault_keepers/chamberlain_crewai_backup.py
vitruvyan_core/core/governance/codex_hunters/scripts/backfill_*.py
```

**Migration Plan**: See [CREWAI_DEPRECATION_PLAN.md](CREWAI_DEPRECATION_PLAN.md)

---

## 🔴 Sacred Orders Contamination (HIGH PRIORITY)

ALL Sacred Orders are contaminated with financial terminology:

### Codex Hunters (Order I - Perception) — 25+ files
```
vitruvyan_core/core/governance/codex_hunters/
├── conclave_cycle.py      # ticker references
├── binder.py              # ticker references
├── tracker.py             # ticker references
├── cassandra.py           # ticker references
├── restorer.py            # ticker references
├── scholastic.py          # ticker references
├── inspector.py           # ticker references
├── event_hunter.py        # ticker references
├── scribe.py              # ticker references
├── hunter.py              # ticker references
├── fundamentalist.py      # ticker references
├── scripts/               # 8+ files with backfill_*
├── backfill/              # 10+ files
└── tests/                 # 3+ files
```

### Vault Keepers (Order II - Memory) — 2 files
```
vitruvyan_core/core/governance/vault_keepers/
├── sentinel.py            # portfolio, ticker references
└── chamberlain.py         # crewai + ticker references
```

### Memory Orders (Order II - Memory) — 5+ files
```
vitruvyan_core/core/governance/memory_orders/
├── migrations/            # 3+ files with ticker schemas
└── tests/                 # 2+ files
```

### Orthodoxy Wardens (Order V - Truth) — 3 files
```
vitruvyan_core/core/governance/orthodoxy_wardens/
├── inquisitor_agent.py    # ticker references
├── docker_manager.py      # ticker references
└── schema_validator.py    # ticker references
```

### Pattern Weavers (Cognitive - Discourse) — 1 file
```
vitruvyan_core/core/cognitive/pattern_weavers/
└── weaver_node.py         # ticker references
```

### Neural Engine (Cognitive - Reason) — 2 files
```
vitruvyan_core/core/cognitive/neural_engine/
├── neural_client.py       # ticker references
└── engine_core.py         # heavy financial logic
```

### Vitruvyan Proprietary (Cognitive) — 10+ files
```
vitruvyan_core/core/cognitive/vitruvyan_proprietary/
├── vare_engine.py         # portfolio risk
├── vhsw_engine.py         # historical stock
├── vmfl_engine.py         # financial metrics
├── vwre_engine.py         # weighted risk
├── vee/                   # 5 files with financial narratives
└── orchestrator.py        # ticker references
```

### Semantic Engine (Cognitive) — 6+ files
```
vitruvyan_core/core/cognitive/semantic_engine/
├── semantic_engine.py     # ticker extraction
└── semantic_modules/      # 5+ files
```

---

## Domain Contamination Categories

### Category 1: Terminology (HIGH PRIORITY)

| Current Term | Abstract Term | Affected Files |
|--------------|---------------|----------------|
| `ticker` | `entity_id` | 50+ files |
| `tickers` | `entities` / `entity_ids` | 50+ files |
| `stock` | `asset` / `entity` | 30+ files |
| `portfolio` | `collection` / `entity_set` | 20+ files |
| `trading` | `domain_operation` | 15+ files |
| `AAPL`, `NVDA`, etc. | `EXAMPLE_ENTITY` | 10+ files |

### Category 2: Schema Contamination (MEDIUM PRIORITY)

**Files with hardcoded financial schemas:**
- `vitruvyan_core/core/foundation/cognitive_bus/event_schema.py`
  - Lines 272-298: Ticker-specific fields in events
  - Lines 407-426: Ticker validation logic
  - Lines 762-774: Example with AAPL hardcoded

- `vitruvyan_core/core/foundation/cognitive_bus/lexicon.py`
  - Domain-specific vocabulary

- `vitruvyan_core/core/foundation/persistence/factor_*.py`
  - Financial factor terminology (momentum, trend, volatility)
  
### Category 3: Prompt Contamination (MEDIUM PRIORITY)

**Files with financial prompts:**
- `vitruvyan_core/core/foundation/llm/prompts/base_prompts.py`
- `vitruvyan_core/core/foundation/llm/prompts/scenario_prompts.py`
- `vitruvyan_core/core/foundation/llm/conversational_llm.py`

### Category 4: Example/Test Contamination (LOW PRIORITY)

Files using financial examples in tests/docs that should be parameterized.

---

## Abstraction Strategy

### Recommended: Parameterized Domain Loading

Rather than find/replace 134 files, implement domain-parameterized loading:

```python
# vitruvyan_core/core/foundation/domain_config.py

class DomainConfig:
    """Load domain terminology at startup"""
    
    ENTITY_TERM = "entity_id"      # Was: ticker
    ENTITIES_TERM = "entity_ids"   # Was: tickers
    COLLECTION_TERM = "collection" # Was: portfolio
    
    @classmethod
    def load_from_vertical(cls, vertical_name: str):
        """Load domain-specific terms from vertical config"""
        config_path = f"verticals/{vertical_name}/domain_config.yaml"
        # ... load and override class attributes
```

This approach:
- ✅ Minimal code changes (~50 lines)
- ✅ Verticals define their own terminology
- ✅ Core remains truly agnostic
- ✅ Backward compatible with existing code

---

## Migration Timeline

| Phase | Scope | Effort | Priority |
|-------|-------|--------|----------|
| 1 | CrewAI deprecation | 3 weeks | HIGH |
| 2 | Domain config layer | 1 week | HIGH |
| 3 | Sacred Orders cleanup | 2 weeks | MEDIUM |
| 4 | Test/example cleanup | 1 week | LOW |

**Total estimate**: 6-8 weeks for full abstraction

---

## Immediate Actions (Today)

1. ✅ Remove `verticals/mercator` folder
2. ✅ Create empty `verticals/` with README
3. ✅ Document CrewAI deprecation plan
4. ✅ Document Sacred Orders contamination
5. ⏳ Begin native agent framework

---

## Notes

The `domains/` folder contains abstract contracts (`base_domain.py`, `aggregation_contract.py`, etc.) that are **already domain-agnostic**. These should be preserved as-is.

**Priority**: Document debt now, clean incrementally. The core is functional as-is for Mercator. Oculus Prime development will drive further abstraction.
