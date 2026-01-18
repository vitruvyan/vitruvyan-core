# Vitruvyan-Core Technical Debt Audit
**Date**: January 18, 2026  
**Objective**: Document financial-specific contamination for abstraction

---

## Executive Summary

The `vitruvyan-core` repository contains **134 files** with domain-specific (financial) terminology that needs to be abstracted to make the core truly domain-agnostic.

---

## Contamination Categories

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

### Phase 1: Core Event Schema (2-4 hours)
1. Replace `ticker` → `entity_id` in event_schema.py
2. Replace `tickers` → `entity_ids` in event_schema.py
3. Make validation logic generic
4. Remove hardcoded AAPL examples

### Phase 2: Persistence Layer (4-6 hours)
1. Abstract `factor_persistence.py` to use domain-agnostic schemas
2. Update `postgres_agent.py` table references
3. Make Qdrant collections domain-parameterized

### Phase 3: LLM/Prompts (2-4 hours)
1. Make prompts template-based with domain injection
2. Remove financial vocabulary from base_prompts.py
3. Add domain-specific prompt loading

### Phase 4: Lexicon (2-3 hours)
1. Create domain-agnostic base lexicon
2. Move financial vocabulary to mercator vertical

---

## Files Requiring Changes

### Core Foundation (34 files)
```
vitruvyan_core/core/foundation/cognitive_bus/event_schema.py
vitruvyan_core/core/foundation/cognitive_bus/lexicon.py
vitruvyan_core/core/foundation/llm/prompts/base_prompts.py
vitruvyan_core/core/foundation/llm/prompts/version.py
vitruvyan_core/core/foundation/llm/prompts/scenario_prompts.py
vitruvyan_core/core/foundation/llm/cache_manager.py
vitruvyan_core/core/foundation/llm/conversational_llm.py
vitruvyan_core/core/foundation/persistence/factor_*.py (6 files)
vitruvyan_core/core/foundation/persistence/postgres_agent.py
vitruvyan_core/core/foundation/persistence/qdrant_agent.py
vitruvyan_core/core/foundation/persistence/sentiment_*.py (2 files)
vitruvyan_core/core/foundation/persistence/trend_access.py
```

### LangGraph Nodes (40+ files)
All nodes in `vitruvyan_core/core/orchestration/langgraph/nodes/` contain ticker references.

### Cognitive Services (20+ files)
- `vitruvyan_core/core/cognitive/codex_hunters/`
- `vitruvyan_core/core/cognitive/pattern_weavers/`
- `vitruvyan_core/core/cognitive/sentiment/`

---

## Recommended Approach

### Option A: Incremental Refactoring (Conservative)
- Pros: Lower risk, can be done gradually
- Cons: 40+ hours of work, merge conflicts risk
- Timeline: 2-3 weeks

### Option B: Parameterized Domain Loading (Recommended)
- Create domain configuration layer
- Load terminology/schemas from vertical config at startup
- Minimal code changes, maximum flexibility
- Timeline: 1 week

### Option C: Fresh Core Extraction (Aggressive)
- Extract truly domain-agnostic components
- Rebuild with clean interfaces
- Pros: Clean slate
- Cons: Significant effort, risk of missing functionality
- Timeline: 4-6 weeks

---

## Immediate Actions (Today)

1. ✅ Remove `verticals/mercator` folder
2. ✅ Create empty `verticals/` with README
3. ⏳ Keep `domains/` as-is (contracts are already abstract)
4. ⏳ Update main README to reflect core mission
5. ⏳ Add foundational docs reference to README

---

## Notes

The `domains/` folder contains abstract contracts (`base_domain.py`, `aggregation_contract.py`, etc.) that are **already domain-agnostic**. These should be preserved as-is.

The contamination is primarily in:
- Event schemas (using `ticker` instead of `entity_id`)
- Example code (using AAPL instead of `EXAMPLE_ENTITY`)
- LLM prompts (financial vocabulary)
- Lexicon (trading-specific terms)

**Priority**: Document debt now, clean incrementally later. The core is functional as-is.
