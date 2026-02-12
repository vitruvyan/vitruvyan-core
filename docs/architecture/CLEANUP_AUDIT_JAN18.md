# Vitruvyan-Core Cleanup Audit
**Date**: January 18, 2026  
**Purpose**: Guida per agenti di pulizia

---

## SUMMARY

| Category | Files | Action |
|----------|-------|--------|
| CrewAI (DELETE) | 34 | Eliminare cartella + rimuovere import |
| Codex Hunters | 38 | Astrarre ticker→entity_id |
| Vault Keepers | 1 | Astrarre portfolio→collection |
| Orthodoxy Wardens | 3 | Astrarre ticker refs |
| Memory Orders | 5 | Astrarre migration schemas |
| Cognitive Layer | 21 | Astrarre o spostare a Mercator |
| Orchestration | 34 | Astrarre nodi finanziari |
| Foundation | 22 | Astrarre persistence + prompts |
| Services | 10 | Astrarre o eliminare |
| **TOTAL** | **168 files** | |

---

## 1. CREWAI — DELETE ENTIRELY

### Folder to delete:
```
rm -rf vitruvyan_core/core/orchestration/crewai/
```

### Files to clean (remove crewai imports):
```
vitruvyan_core/core/foundation/cognitive_bus/herald.py
vitruvyan_core/core/foundation/cognitive_bus/event_schema.py
vitruvyan_core/core/foundation/cognitive_bus/lexicon.py
vitruvyan_core/core/orchestration/langgraph/node/crew_node.py          # DELETE FILE
vitruvyan_core/core/orchestration/langgraph/node/quality_check_node.py
vitruvyan_core/core/orchestration/langgraph/node/compose_node.py
vitruvyan_core/core/orchestration/langgraph/node/llm_soft_node.py
vitruvyan_core/core/orchestration/langgraph/node/output_normalizer_node.py
vitruvyan_core/core/orchestration/langgraph/node/__init__.py
vitruvyan_core/core/orchestration/langgraph/graph_flow.py
vitruvyan_core/core/governance/vault_keepers/chamberlain.py
vitruvyan_core/core/governance/vault_keepers/chamberlain_crewai_backup.py  # DELETE FILE
vitruvyan_core/core/governance/vault_keepers/__init__.py
vitruvyan_core/core/governance/codex_hunters/scripts/backfill_technical_logs.py
vitruvyan_core/core/governance/codex_hunters/scripts/backfill_all.py
vitruvyan_core/core/governance/codex_hunters/tests/test_backfill_integration.py
vitruvyan_core/core/governance/codex_hunters/backfill/backfill_technical_logs.py
vitruvyan_core/core/governance/codex_hunters/backfill/backfill_all.py
vitruvyan_core/core/governance/orthodoxy_wardens/inquisitor_agent.py
vitruvyan_core/core/governance/orthodoxy_wardens/chronicler_agent.py
vitruvyan_core/core/governance/orthodoxy_wardens/docker_manager.py
vitruvyan_core/core/governance/orthodoxy_wardens/penitent_agent.py
vitruvyan_core/core/governance/orthodoxy_wardens/confessor_agent.py
vitruvyan_core/core/cognitive/vitruvyan_proprietary/vee/vee_engine.py
services/core/api_portfolio_guardian/main.py
services/core/api_crewai/main.py                                        # DELETE FOLDER
services/core/api_crewai/__init__.py
services/core/api_graph/main.py
services/core/api_babel_gardens/modules/cognitive_bridge.py
config/api_config.py
```

---

## 2. SACRED ORDERS — ABSTRACT

### 2.1 Codex Hunters (Order I - Perception)
**Action**: Abstract `ticker` → `entity_id`, remove financial-specific backfills

**Core files to abstract (keep but clean):**
```
vitruvyan_core/core/governance/codex_hunters/base_hunter.py        # KEEP - abstract
vitruvyan_core/core/governance/codex_hunters/binder.py             # ABSTRACT
vitruvyan_core/core/governance/codex_hunters/tracker.py            # ABSTRACT
vitruvyan_core/core/governance/codex_hunters/event_hunter.py       # ABSTRACT
vitruvyan_core/core/governance/codex_hunters/scribe.py             # ABSTRACT
vitruvyan_core/core/governance/codex_hunters/hunter.py             # ABSTRACT
vitruvyan_core/core/governance/codex_hunters/inspector.py          # ABSTRACT
vitruvyan_core/core/governance/codex_hunters/restorer.py           # ABSTRACT
vitruvyan_core/core/governance/codex_hunters/conclave_cycle.py     # ABSTRACT
vitruvyan_core/core/governance/codex_hunters/cartographer.py       # ABSTRACT
vitruvyan_core/core/governance/codex_hunters/expedition_leader.py  # ABSTRACT
vitruvyan_core/core/governance/codex_hunters/expedition_planner.py # ABSTRACT
```

**Financial-specific files to DELETE or move to Mercator:**
```
vitruvyan_core/core/governance/codex_hunters/cassandra.py          # FINANCIAL - DELETE
vitruvyan_core/core/governance/codex_hunters/scholastic.py         # FINANCIAL - DELETE  
vitruvyan_core/core/governance/codex_hunters/fundamentalist.py     # FINANCIAL - DELETE
vitruvyan_core/core/governance/codex_hunters/scripts/              # FINANCIAL - DELETE FOLDER
vitruvyan_core/core/governance/codex_hunters/backfill/             # FINANCIAL - DELETE FOLDER
vitruvyan_core/core/governance/codex_hunters/tests/                # FINANCIAL - DELETE FOLDER
```

### 2.2 Vault Keepers (Order II - Memory)
**Action**: Abstract portfolio → collection

```
vitruvyan_core/core/governance/vault_keepers/sentinel.py           # ABSTRACT
vitruvyan_core/core/governance/vault_keepers/chamberlain.py        # ABSTRACT + remove crewai
vitruvyan_core/core/governance/vault_keepers/archivist.py          # KEEP - likely clean
vitruvyan_core/core/governance/vault_keepers/courier.py            # KEEP - likely clean
vitruvyan_core/core/governance/vault_keepers/keeper.py             # KEEP - likely clean
vitruvyan_core/core/governance/vault_keepers/chamberlain_crewai_backup.py  # DELETE
```

### 2.3 Orthodoxy Wardens (Order V - Truth)
**Action**: Abstract ticker refs, keep validation logic

```
vitruvyan_core/core/governance/orthodoxy_wardens/inquisitor_agent.py   # ABSTRACT
vitruvyan_core/core/governance/orthodoxy_wardens/docker_manager.py     # ABSTRACT
vitruvyan_core/core/governance/orthodoxy_wardens/schema_validator.py   # ABSTRACT
```

### 2.4 Memory Orders (Order II - Memory)
**Action**: Abstract migration schemas

```
vitruvyan_core/core/governance/memory_orders/migrations/versions/001_create_external_datasets.py
vitruvyan_core/core/governance/memory_orders/migrations/versions/a675c9c6611e_initial_baseline_migration.py
vitruvyan_core/core/governance/memory_orders/migrations/versions/f6cbae421c43_create_initial_database_schema_from_.py
vitruvyan_core/core/governance/memory_orders/tests/test_memory_orders_cycle.py
vitruvyan_core/core/governance/memory_orders/tests/test_memory_orders_vsgs.py
```

---

## 3. COGNITIVE LAYER — HEAVY FINANCIAL

### 3.1 Neural Engine (FINANCIAL SPECIFIC)
**Decision**: Move entirely to Mercator vertical or DELETE from core

```
vitruvyan_core/core/cognitive/neural_engine/                       # MOVE TO MERCATOR
```

### 3.2 Vitruvyan Proprietary (MIXED)
**Decision**: VEE is useful for any domain (keep abstract), others are financial

**KEEP (abstract):**
```
vitruvyan_core/core/cognitive/vitruvyan_proprietary/vee/           # KEEP - abstract explainability
```

**DELETE or MOVE TO MERCATOR:**
```
vitruvyan_core/core/cognitive/vitruvyan_proprietary/vare_engine.py        # FINANCIAL RISK
vitruvyan_core/core/cognitive/vitruvyan_proprietary/vhsw_engine.py        # HISTORICAL STOCK
vitruvyan_core/core/cognitive/vitruvyan_proprietary/vmfl_engine.py        # FINANCIAL METRICS
vitruvyan_core/core/cognitive/vitruvyan_proprietary/vwre_engine.py        # WEIGHTED RISK
vitruvyan_core/core/cognitive/vitruvyan_proprietary/orchestrator.py       # ABSTRACT or DELETE
vitruvyan_core/core/cognitive/vitruvyan_proprietary/algorithm_memory_adapter.py  # ABSTRACT
```

### 3.3 Semantic Engine (ABSTRACT)
**Action**: Abstract ticker extraction → entity extraction

```
vitruvyan_core/core/cognitive/semantic_engine/semantic_engine.py
vitruvyan_core/core/cognitive/semantic_engine/semantic_modules/intent/intent_module.py
vitruvyan_core/core/cognitive/semantic_engine/semantic_modules/entity/entity_module.py
vitruvyan_core/core/cognitive/semantic_engine/semantic_modules/enrichment/enrichment_module.py
vitruvyan_core/core/cognitive/semantic_engine/semantic_modules/routing/routing_module.py
vitruvyan_core/core/cognitive/semantic_engine/semantic_modules/data/reddit_scraper.py  # DELETE - financial
```

### 3.4 Pattern Weavers (ABSTRACT)
```
vitruvyan_core/core/cognitive/pattern_weavers/weaver_node.py       # ABSTRACT
```

---

## 4. ORCHESTRATION — LANGGRAPH NODES

### Nodes to DELETE (financial-specific):
```
vitruvyan_core/core/orchestration/langgraph/node/crew_node.py
vitruvyan_core/core/orchestration/langgraph/node/portfolio_node.py
vitruvyan_core/core/orchestration/langgraph/node/screener_node.py
vitruvyan_core/core/orchestration/langgraph/node/sentiment_node.py
vitruvyan_core/core/orchestration/langgraph/node/ticker_resolver_node.py
vitruvyan_core/core/orchestration/langgraph/utilities/llm_ticker_extractor.py
```

### Nodes to ABSTRACT:
```
vitruvyan_core/core/orchestration/langgraph/node/semantic_grounding_node.py
vitruvyan_core/core/orchestration/langgraph/node/route_node.py
vitruvyan_core/core/orchestration/langgraph/node/codex_node.py
vitruvyan_core/core/orchestration/langgraph/node/advisor_node.py
vitruvyan_core/core/orchestration/langgraph/node/babel_emotion_node.py
vitruvyan_core/core/orchestration/langgraph/node/cached_llm_node.py
vitruvyan_core/core/orchestration/langgraph/node/proactive_suggestions_node.py
vitruvyan_core/core/orchestration/langgraph/node/params_extraction_node.py
vitruvyan_core/core/orchestration/langgraph/node/quality_check_node.py
vitruvyan_core/core/orchestration/langgraph/node/intent_detection_node.py
vitruvyan_core/core/orchestration/langgraph/node/compose_node.py
vitruvyan_core/core/orchestration/langgraph/node/enhanced_llm_node.py
vitruvyan_core/core/orchestration/langgraph/node/sentinel_node.py
vitruvyan_core/core/orchestration/langgraph/node/vault_node.py
vitruvyan_core/core/orchestration/langgraph/node/can_node.py
vitruvyan_core/core/orchestration/langgraph/node/parse_node.py
vitruvyan_core/core/orchestration/langgraph/node/emotion_detector.py
vitruvyan_core/core/orchestration/langgraph/node/orthodoxy_node.py
vitruvyan_core/core/orchestration/langgraph/node/llm_mcp_node.py
vitruvyan_core/core/orchestration/langgraph/node/gemma_node.py
vitruvyan_core/core/orchestration/langgraph/graph_flow.py
vitruvyan_core/core/orchestration/langgraph/graph_runner.py
vitruvyan_core/core/orchestration/langgraph/memory_utils.py
vitruvyan_core/core/orchestration/langgraph/memory/conversation_context.py
```

---

## 5. FOUNDATION — PERSISTENCE + PROMPTS

### Files to ABSTRACT:
```
vitruvyan_core/core/foundation/cognitive_bus/event_schema.py       # ticker → entity_id
vitruvyan_core/core/foundation/cognitive_bus/lexicon.py            # remove financial vocab
vitruvyan_core/core/foundation/llm/prompts/base_prompts.py         # make domain-agnostic
vitruvyan_core/core/foundation/llm/prompts/scenario_prompts.py     # make templates
vitruvyan_core/core/foundation/llm/conversational_llm.py           # abstract
vitruvyan_core/core/foundation/persistence/postgres_agent.py       # abstract table names
vitruvyan_core/core/foundation/persistence/qdrant_agent.py         # abstract collections
```

### Files to DELETE (financial-specific):
```
vitruvyan_core/core/foundation/persistence/factor_explanations.py
vitruvyan_core/core/foundation/persistence/factor_access.py
vitruvyan_core/core/foundation/persistence/factor_persistence.py
vitruvyan_core/core/foundation/persistence/sentiment_persistence_qdrant.py
vitruvyan_core/core/foundation/persistence/sentiment_persistence.py
vitruvyan_core/core/foundation/persistence/sentiment_access.py
vitruvyan_core/core/foundation/persistence/trend_access.py
vitruvyan_core/core/foundation/persistence/import_seed_dataset.py
vitruvyan_core/core/foundation/cache/neural_cache.py
```

---

## 6. SERVICES — DOCKER APIS

### Services to DELETE:
```
services/core/api_crewai/                                          # DELETE FOLDER
services/core/api_portfolio_guardian/                              # MOVE TO MERCATOR
services/core/api_neural_engine/                                   # MOVE TO MERCATOR
```

### Services to ABSTRACT:
```
services/mcp/main.py
services/governance/api_orthodoxy_wardens/redis_listener.py
services/core/api_codex_hunters/main.py
services/core/api_graph/main.py
services/core/api_babel_gardens/modules/profile_processor.py
services/core/api_babel_gardens/modules/cognitive_bridge.py
services/core/api_babel_gardens/modules/sentiment_fusion.py
```

---

## TERMINOLOGY MAPPING

| Financial Term | Abstract Term |
|----------------|---------------|
| `ticker` | `entity_id` |
| `tickers` | `entity_ids` / `entities` |
| `stock` | `entity` / `asset` |
| `portfolio` | `collection` / `entity_set` |
| `trading` | `domain_operation` |
| `momentum` | `signal_a` / `metric_a` |
| `trend` | `signal_b` / `metric_b` |
| `volatility` | `signal_c` / `metric_c` |
| `AAPL`, `NVDA`, etc. | `EXAMPLE_ENTITY_1`, `EXAMPLE_ENTITY_2` |

---

## EXECUTION ORDER

1. **Phase 1**: Delete CrewAI (30 min)
2. **Phase 2**: Delete financial-specific files (1 hour)
3. **Phase 3**: Abstract Sacred Orders (4 hours)
4. **Phase 4**: Abstract Cognitive Layer (4 hours)
5. **Phase 5**: Abstract Orchestration nodes (4 hours)
6. **Phase 6**: Abstract Foundation (2 hours)
7. **Phase 7**: Clean Services (2 hours)
8. **Phase 8**: Test everything (2 hours)

**Total**: ~20 hours of mechanical work
