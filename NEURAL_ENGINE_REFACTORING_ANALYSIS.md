# Neural Engine — Refactoring Analysis & Design Proposal

**Date**: February 10, 2026  
**Author**: AI Architect (Copilot)  
**Scope**: Align Neural Engine (Reason layer) with Sacred Orders design patterns  
**Goal**: Modularity, scalability, consistent tree structure, easy readability

---

## Table of Contents

1. [Current State Audit](#1-current-state-audit)
2. [Pattern Comparison: Governance vs Reason](#2-pattern-comparison-governance-vs-reason)
3. [Gap Analysis: vitruvyan-core (agnostic) vs vitruvyan (monolith)](#3-gap-analysis)
4. [Proposed Target Architecture](#4-proposed-target-architecture)
5. [File-by-File Migration Plan](#5-file-by-file-migration-plan)
6. [Service Layer Alignment](#6-service-layer-alignment)
7. [Contract Refinements](#7-contract-refinements)
8. [Implementation Phases](#8-implementation-phases)
9. [Risk Assessment](#9-risk-assessment)

---

## 1. Current State Audit

### 1.1 vitruvyan (Production Monolith)

**Location**: `core/logic/neural_engine/engine_core.py`  
**Size**: **2,860 lines in 1 file** (God Object)

| Component | Lines | Notes |
|-----------|-------|-------|
| `extract_universe()` | ~100 | Direct `psycopg2.connect()` — violates PostgresAgent rule |
| `extract_features()` | ~10 | Thin wrapper over extract_universe |
| `get_momentum_z()` | ~100 | SQL query + z-score calc + stratification + time decay |
| `get_trend_z()` | ~90 | Same pattern as momentum |
| `get_volatility_z()` | ~90 | Same pattern |
| `get_sentiment_z()` | ~110 | Same pattern + NE_DISABLE_SENTIMENT flag |
| `get_fundamentals_z()` | ~100 | 6 fundamental metrics, composite calculation |
| `apply_portfolio_diversification()` | ~110 | Function J — correlation matrix filtering |
| `apply_macro_sensitivity_filter()` | ~100 | Function K — macro factor filtering |
| `get_dark_pool_z()` | ~75 | Function P — institutional flow |
| `apply_smart_money_filter()` | ~35 | Threshold filter on dark_pool_z |
| `get_vare_scores()` | ~145 | VARE integration (proprietary risk engine) |
| `get_days_to_earnings()` | ~50 | Earnings calendar lookup |
| `apply_earnings_safety_filter()` | ~35 | Exclude tickers near earnings |
| `get_divergence_score()` | ~85 | Function H — price-RSI divergence |
| `get_multi_timeframe_consensus()` | ~50 | Function I — multi-TF alignment |
| `get_macro_outlook()` | ~30 | Macro rates/inflation lookup |
| `get_factor_scores()` | ~20 | Academic factor scores |
| `PROFILE_WEIGHTS` | ~70 | 6 hardcoded profiles (static dict) |
| `compute_composite()` | ~30 | Weighted sum of z-scores |
| `apply_risk_adjustment()` | ~90 | VARE-based composite adjustment |
| `apply_guardrails_and_topk()` | ~80 | Sector capping, momentum breakout filters |
| `build_json()` | ~640 | JSON response builder (includes `pack_rows()` ~240 lines) |
| `persist_results()` | ~60 | Save to PostgreSQL |
| `run_ne_once()` | ~300 | Main orchestrator function (God function) |

**Service Layer**: `docker/services/api_neural_engine/api_server.py` (206 lines)  
- Single endpoint `POST /neural-engine` → calls `run_ne_once()` directly
- 15 parameters pass-through (momentum_breakout, value_screening, etc.)

**Critical Issues**:
1. ❌ **2,860 lines in 1 file** — impossible to test, maintain, or extend independently
2. ❌ **Direct psycopg2.connect()** everywhere (13+ raw SQL calls) — violates PostgresAgent mandate
3. ❌ **Finance-hardcoded** — tickers, sectors, RSI, MACD, SMA baked in at every level
4. ❌ **No separation of concerns** — data access, scoring, filtering, formatting, persistence all interleaved
5. ❌ **God function** — `run_ne_once()` (300 lines) does everything sequentially
6. ❌ **No event bus integration** — no Cognitive Bus events published/consumed
7. ❌ **Untestable** — no interfaces, no DI, every function depends on live PostgreSQL

---

### 1.2 vitruvyan-core (Agnostic, Current State)

**Core Domain**: `vitruvyan_core/core/neural_engine/` — **1,478 lines across 7 files**

```
vitruvyan_core/core/neural_engine/
├── __init__.py              (56 lines)  — Clean exports
├── engine.py                (296 lines) — NeuralEngine orchestrator
├── scoring.py               (195 lines) — ZScoreCalculator (3 modes)
├── composite.py             (152 lines) — CompositeScorer (weighted avg)
├── ranking.py               (184 lines) — RankingEngine (rank, percentile, bucket)
├── domain_examples/
│   ├── __init__.py          (19 lines)
│   ├── mock_data_provider.py    (272 lines)
│   └── mock_scoring_strategy.py (304 lines)
└── README.md
```

**Service Layer**: `services/api_neural_engine/` — **911 lines across 7 files**

```
services/api_neural_engine/
├── __init__.py              (1 line)
├── main.py                  (385 lines) — FastAPI app + Prometheus metrics
├── modules/
│   └── engine_orchestrator.py (278 lines) — Bridge: API → NeuralEngine
├── schemas/
│   ├── __init__.py          (18 lines)
│   └── api_models.py        (143 lines) — Pydantic request/response models
├── shared/
│   └── __init__.py          (1 line)
├── examples/
│   └── 05_compare_profiles.py (81 lines)
└── Dockerfile
```

**Contracts**: `vitruvyan_core/contracts/` — **406 lines**
- `IDataProvider` (165 lines) — get_universe(), get_features(), get_metadata(), validate_entity_ids()
- `IScoringStrategy` (199 lines) — get_profile_weights(), compute_composite_score(), apply_risk_adjustment()

**What's Good** ✅:
- Clean separation: engine.py orchestrates, scoring.py calculates, composite.py weights, ranking.py ranks
- Contract-based DI via IDataProvider/IScoringStrategy
- 100% domain-agnostic (entity_id, not ticker)
- Mock implementations for testing

**What's Missing** ❌:
- No `domain/` layer (domain objects, value objects)
- No `events/` layer (no Cognitive Bus integration)
- No `consumers/` layer (no stream consumers for reactive processing)
- No `governance/` layer (no self-validation rules)
- No `monitoring/` layer (metrics defined only in service, not core)
- No `_legacy/` path (no migration bridge from monolith)
- No `adapters/` in service layer (no persistence adapter, no bus adapter)
- No `philosophy/` charter (no identity doc like Vault Keepers/Orthodoxy have)
- `engine_orchestrator.py` hardcodes MockDataProvider (no env-based domain loading)

---

## 2. Pattern Comparison: Governance vs Reason

The Governance orders (Orthodoxy Wardens, Vault Keepers) have been refactored to a **canonical 7-layer pattern**. Neural Engine is the **Reason** order — different role, same structural principles.

### 2.1 Canonical Sacred Orders Pattern

```
vitruvyan_core/core/<order>/
├── __init__.py              — Public API + exports
├── <main_agents>.py         — Core business logic (stateless)
├── _legacy/                 — Original monolith code (preserved, deprecated)
├── consumers/               — Cognitive Bus stream consumers
│   ├── __init__.py
│   ├── base.py              — Abstract base consumer
│   ├── <role_1>.py          — Consumer for specific event types
│   └── <role_N>.py
├── domain/                  — Domain objects (dataclasses, value objects)
│   ├── __init__.py
│   └── <objects>.py
├── events/                  — Event definitions (what this order publishes/consumes)
│   ├── __init__.py
│   └── <order>_events.py
├── governance/              — Self-governance rules and workflows
│   ├── __init__.py
│   ├── rules.py
│   └── workflows.py
├── monitoring/              — Metrics definitions (Prometheus)
│   └── __init__.py
├── philosophy/              — Charter.md (identity, principles, boundaries)
│   └── charter.md
└── tests/                   — Unit tests
    └── test_<module>.py
```

### 2.2 How This Maps to Neural Engine (Reason Order)

| Governance Layer | Orthodoxy Wardens | Vault Keepers | Neural Engine (Target) |
|:---:|:---:|:---:|:---:|
| **Main agents** | confessor, inquisitor, penitent, code_analyzer | archivist, keeper, sentinel | engine, scoring, composite, ranking |
| **_legacy/** | chronicler, docker_manager, git_monitor, schema_validator | archivist, chamberlain, courier, sentinel, gdrive | engine_core.py (2860 lines) |
| **consumers/** | chronicler, confessor, inquisitor, penitent | archivist, chamberlain, guardian, sentinel | N/A — request-response |
| **domain/** | confession, finding, verdict, log_decision | vault_objects | ranking_result, screening_request, entity_score |
| **events/** | orthodoxy_events | vault_events | N/A — service-level notification only |
| **governance/** | classifier, rule, verdict_engine, workflow | rules, workflows | quality_rules, freshness_rules |
| **monitoring/** | metrics | *(empty)* | metrics |
| **philosophy/** | *(implied)* | charter.md | charter.md |
| **tests/** | 4 test files | 3 test files | test_engine, test_scoring, test_pipeline |

### 2.3 Key Differences: Governance vs Reason

Neural Engine is NOT a governance order. It doesn't audit, validate, or enforce rules on other services. It **computes**. This changes the internal structure fundamentally:

| Aspect | Governance (Orthodoxy/Vault) | Reason (Neural Engine) |
|--------|------------------------------|----------------------|
| **Primary action** | Validate, audit, archive | Compute, rank, score |
| **Input** | Events from other services | Data from IDataProvider |
| **Output** | Verdicts, findings, archives | Ranked entity lists |
| **Communication** | Event-driven (async, bus-native) | Request-response (sync, HTTP) |
| **consumers/** role | ✅ Essential (react to events) | ❌ Not needed (called via REST) |
| **events/** role | ✅ Core concern (publish verdicts) | ❌ Not core (service can notify bus optionally) |
| **governance/** role | Classify violations, apply rules | Validate data quality, freshness thresholds |
| **domain/** role | Findings, confessions, verdicts | Scores, rankings, screening results |
| **Statefulness** | Event-driven (stateless processing) | Stateless computation (pure functions) |
| **Bus interaction** | Heavy (publish + consume) | None in core; optional adapter in service layer |

### 2.4 The Bus Boundary Principle

> **The Cognitive Bus is the nervous system of Sacred Orders (governance/truth/memory). The Neural Engine is called, not summoned.**

Sacred Orders are **reactive**: they listen for events and act autonomously. The Neural Engine is **imperative**: LangGraph calls it via HTTP, it computes, it returns results.

The only bus touchpoint is an **optional service-level adapter** that publishes `screening.completed` events so Sacred Orders can react (Vault Keepers archive results, Orthodoxy Wardens audit rankings). This is NOT a core concern — it's a notification, not a dependency.

```
# Sacred Orders (bus-native):
Bus Event → Consumer → Process → Publish Result → Bus Event

# Neural Engine (request-response):
HTTP Request → Engine.run() → Return Result → (optionally) Notify Bus
```

---

## 3. Gap Analysis

### 3.1 vitruvyan-core: What Exists vs What Should Exist

| Layer | Exists? | Files | GAP |
|-------|:---:|-------|-----|
| `__init__.py` | ✅ | Clean exports | — |
| Core agents (engine, scoring, composite, ranking) | ✅ | 4 files, 827 lines | — |
| `_legacy/` | ❌ | — | Need bridge from monolith |
| `consumers/` | N/A | — | **Not needed** — NE is request-response, not event-driven |
| `domain/` | ❌ | — | Need RankingResult, ScreeningRequest, EntityScore |
| `events/` | N/A | — | **Not needed in core** — bus notification is service-level adapter |
| `governance/` | ❌ | — | Need quality rules (data completeness, freshness) |
| `monitoring/` | ❌ | — | Need core metric definitions |
| `philosophy/` | ❌ | — | Need charter.md (identity, boundaries) |
| `tests/` | ❌ | — | Need unit tests for each module |
| `domain_examples/` | ✅ | 2 files (mock provider, mock strategy) | Move to `examples/` for naming consistency |

### 3.2 Service Layer: What Exists vs What Should Exist

| Layer | Exists? | Files | GAP |
|-------|:---:|-------|-----|
| `main.py` | ✅ | 385 lines | ✅ Well structured |
| `modules/engine_orchestrator.py` | ✅ | 278 lines | Hardcodes MockDataProvider — needs env-based loader |
| `schemas/api_models.py` | ✅ | 143 lines | ✅ Clean Pydantic models |
| `adapters/` | ❌ | — | Need bus_adapter.py, persistence.py |
| `api/routes.py` | ❌ | — | Routes inline in main.py — should extract |
| `config.py` | ❌ | — | Need centralized config (env vars, defaults) |
| `_legacy/` | ❌ | — | Need preserved original main.py |
| `monitoring/` | ❌ | — | Prometheus metrics inline in main.py |

### 3.3 Monolith Decomposition Map

The 2,860-line `engine_core.py` maps to vitruvyan-core modules as follows:

| Monolith Function(s) | Lines | Target vitruvyan-core Module | Notes |
|----------------------|-------|------------------------------|-------|
| `extract_universe()`, `extract_features()` | ~110 | `IDataProvider` implementation (vitruvyan plugin) | Finance-specific, not core |
| `get_momentum_z()`, `get_trend_z()`, `get_volatility_z()`, `get_sentiment_z()` | ~390 | `IDataProvider.get_features()` + `scoring.py` | SQL → provider; z-score → core |
| `get_fundamentals_z()` | ~100 | `IDataProvider.get_features()` | Finance-specific |
| `get_factor_scores()`, `get_macro_outlook()` | ~50 | `IDataProvider.get_features()` | Finance-specific |
| `get_dark_pool_z()`, `get_divergence_score()`, `get_multi_timeframe_consensus()` | ~160 | `IDataProvider.get_features()` | Finance-specific (Functions P, H, I) |
| `get_vare_scores()` | ~145 | `IScoringStrategy.apply_risk_adjustment()` | Finance-specific (VARE proprietary) |
| `get_days_to_earnings()`, `apply_earnings_safety_filter()` | ~85 | Filter plugin or `IScoringStrategy` extension | Finance-specific |
| `apply_portfolio_diversification()` | ~110 | Filter plugin | Finance-specific (Function J) |
| `apply_macro_sensitivity_filter()` | ~100 | Filter plugin | Finance-specific (Function K) |
| `apply_smart_money_filter()` | ~35 | Filter plugin | Finance-specific |
| `PROFILE_WEIGHTS`, `FACTOR_MAP` | ~70 | `IScoringStrategy` implementation (vitruvyan plugin) | Finance-specific |
| `compute_composite()` | ~30 | `composite.py` | ✅ Already in core |
| `apply_risk_adjustment()` | ~90 | `composite.py` → `IScoringStrategy.apply_risk_adjustment()` | ✅ Already in core |
| `apply_guardrails_and_topk()` | ~80 | `ranking.py` + new `IFilterStrategy` contract | Needs new contract |
| `build_json()` + `pack_rows()` | ~640 | `services/.../modules/response_builder.py` | Service-layer concern |
| `persist_results()` | ~60 | `services/.../adapters/persistence.py` | Service-layer concern |
| `run_ne_once()` | ~300 | `engine.py` (NeuralEngine.run) | ✅ Already in core (simplified) |

**Key Insight**: Of 2,860 lines, ~**1,750 lines (61%)** are finance-specific data acquisition/transformation that belong in an `IDataProvider` implementation (vitruvyan plugin), NOT in vitruvyan-core.

---

## 4. Proposed Target Architecture

### 4.1 Core Domain Layer (vitruvyan-core)

```
vitruvyan_core/core/neural_engine/
├── __init__.py                          — Public API + exports
│
├── engine.py                            — NeuralEngine orchestrator (KEEP)
├── scoring.py                           — ZScoreCalculator (KEEP)
├── composite.py                         — CompositeScorer (KEEP)
├── ranking.py                           — RankingEngine (KEEP)
│
├── _legacy/                             — NEW: Migration bridge
│   ├── __init__.py
│   └── README.md                        — "Monolith was here" + migration notes
│
├── domain/                              — NEW: Domain objects (frozen dataclasses)
│   ├── __init__.py
│   ├── screening_request.py             — ScreeningRequest (profile, filters, top_k, ...)
│   ├── ranking_result.py                — RankingResult (ranked_entities, metadata, stats)
│   └── entity_score.py                  — EntityScore (entity_id, composite, percentile, bucket)
│
├── governance/                          — NEW: Self-governance (data quality, not audit)
│   ├── __init__.py
│   ├── quality_rules.py                 — Data completeness checks (min features, min entities)
│   └── freshness_rules.py               — Data freshness validation (max age thresholds)
│
├── monitoring/                          — NEW: Metric definitions
│   └── __init__.py                      — Prometheus counters/histograms (imported by service)
│
├── philosophy/                          — NEW: Identity charter
│   └── charter.md                       — "I am the Reason layer. I compute, rank, and explain."
│
├── examples/                            — RENAMED from domain_examples/
│   ├── __init__.py
│   ├── mock_data_provider.py            — KEEP
│   └── mock_scoring_strategy.py         — KEEP
│
└── tests/                               — NEW: Unit tests
    ├── __init__.py
    ├── test_engine.py                   — Test full pipeline
    ├── test_scoring.py                  — Test z-score modes
    ├── test_composite.py                — Test weighted scoring
    ├── test_ranking.py                  — Test ranking + bucketing
    └── test_domain_objects.py           — Test dataclass validation
```

### 4.2 Service Layer (vitruvyan-core)

```
services/api_neural_engine/
├── __init__.py
├── main.py                              — FastAPI app (slim: lifespan + middleware)
├── config.py                            — NEW: Centralized config (DomainLoader)
│
├── _legacy/                             — NEW: Preserved original
│   └── main_legacy.py
│
├── api/                                 — NEW: Route extraction
│   ├── __init__.py
│   └── routes.py                        — /screen, /rank, /health, /metrics, /profiles
│
├── adapters/                            — NEW: External system adapters
│   ├── __init__.py
│   ├── bus_adapter.py                   — Cognitive Bus publish/subscribe
│   └── persistence.py                   — Result persistence (PostgresAgent)
│
├── modules/
│   ├── __init__.py
│   ├── engine_orchestrator.py           — KEEP (fix: env-based domain loading)
│   └── response_builder.py             — NEW: JSON response formatting (extracted from monolith)
│
├── schemas/
│   ├── __init__.py
│   └── api_models.py                    — KEEP
│
├── monitoring/                          — NEW: Prometheus metric instances
│   └── __init__.py
│
├── examples/
│   └── 05_compare_profiles.py           — KEEP
│
├── Dockerfile
└── streams_listener.py                  — NEW: Redis Streams listener entry point
```

### 4.3 Contract Additions (vitruvyan-core)

```
vitruvyan_core/contracts/
├── __init__.py                          — Add new exports
├── data_provider.py                     — KEEP
├── scoring_strategy.py                  — KEEP
└── filter_strategy.py                   — NEW: IFilterStrategy contract
```

### 4.4 Finance Plugin (vitruvyan only)

The finance-specific `IDataProvider` and `IScoringStrategy` implementations live in vitruvyan:

```
# vitruvyan (production repo)
core/logic/neural_engine/
├── engine_core.py                       — KEEP AS-IS (production, deprecated gradually)
├── financial_data_provider.py           — NEW: implements IDataProvider
│   (extract_universe, get_momentum_z, get_trend_z, etc. → provider methods)
├── financial_scoring_strategy.py        — NEW: implements IScoringStrategy
│   (PROFILE_WEIGHTS, FACTOR_MAP, compute_composite, apply_risk_adjustment)
├── financial_filters.py                 — NEW: implements IFilterStrategy
│   (apply_guardrails_and_topk, momentum_breakout, earnings_safety, etc.)
└── response_builder.py                  — NEW: build_json() + pack_rows()
```

---

## 5. File-by-File Migration Plan

### Phase 1: Core Domain Enrichment (vitruvyan-core)

| # | Action | File | Lines | Effort |
|---|--------|------|-------|--------|
| 1.1 | CREATE | `domain/screening_request.py` | ~50 | 20 min |
| 1.2 | CREATE | `domain/ranking_result.py` | ~60 | 20 min |
| 1.3 | CREATE | `domain/entity_score.py` | ~40 | 15 min |
| 1.4 | CREATE | `events/neural_events.py` | ~40 | 15 min |
| 1.5 | CREATE | `governance/quality_rules.py` | ~80 | 30 min |
| 1.6 | CREATE | `governance/freshness_rules.py` | ~60 | 20 min |
| 1.7 | CREATE | `philosophy/charter.md` | ~60 | 15 min |
| 1.8 | RENAME | `domain_examples/` → `examples/` | — | 5 min |
| 1.9 | CREATE | `_legacy/README.md` | ~20 | 5 min |
| 1.10 | CREATE | `monitoring/__init__.py` (metric defs) | ~40 | 15 min |
| **Total** | | | ~450 | **~2.5h** |

### ~~Phase 2: Consumers~~ — REMOVED

> **Architectural Decision**: Neural Engine is request-response (REST), NOT event-driven.
> Consumers are a Sacred Orders pattern for governance services that react to bus events.
> NE doesn't need them — it's called by LangGraph via HTTP.
>
> The only bus integration is an **optional adapter** in the service layer (`adapters/bus_adapter.py`)
> that publishes result notifications so Sacred Orders can react.

### Phase 3: Service Layer Alignment (vitruvyan-core)

| # | Action | File | Lines | Effort |
|---|--------|------|-------|--------|
| 3.1 | CREATE | `config.py` | ~60 | 20 min |
| 3.2 | EXTRACT | `api/routes.py` from `main.py` | ~150 | 45 min |
| 3.3 | SIMPLIFY | `main.py` (→ slim app factory) | ~100 | 30 min |
| 3.4 | CREATE | `adapters/bus_adapter.py` | ~120 | 45 min |
| 3.5 | CREATE | `adapters/persistence.py` | ~80 | 30 min |
| 3.6 | CREATE | `monitoring/__init__.py` (instances) | ~60 | 15 min |
| 3.7 | FIX | `engine_orchestrator.py` (env-based domain) | ~40 | 30 min |
| 3.8 | CREATE | `streams_listener.py` | ~80 | 30 min |
| 3.9 | PRESERVE | `_legacy/main_legacy.py` | — | 5 min |
| **Total** | | | ~690 | **~4h** |

### Phase 4: Contract Extension (vitruvyan-core)

| # | Action | File | Lines | Effort |
|---|--------|------|-------|--------|
| 4.1 | CREATE | `contracts/filter_strategy.py` (IFilterStrategy) | ~80 | 30 min |
| 4.2 | UPDATE | `contracts/__init__.py` (add exports) | ~5 | 5 min |
| **Total** | | | ~85 | **~35 min** |

### Phase 5: Unit Tests (vitruvyan-core)

| # | Action | File | Lines | Effort |
|---|--------|------|-------|--------|
| 5.1 | CREATE | `tests/test_engine.py` | ~120 | 45 min |
| 5.2 | CREATE | `tests/test_scoring.py` | ~100 | 30 min |
| 5.3 | CREATE | `tests/test_composite.py` | ~80 | 30 min |
| 5.4 | CREATE | `tests/test_ranking.py` | ~80 | 30 min |
| 5.5 | CREATE | `tests/test_domain_objects.py` | ~60 | 20 min |
| **Total** | | | ~440 | **~2.5h** |

### Phase 6: Finance Plugin (vitruvyan repo)

| # | Action | File | Lines | Effort |
|---|--------|------|-------|--------|
| 6.1 | EXTRACT | `financial_data_provider.py` from engine_core.py | ~600 | 3h |
| 6.2 | EXTRACT | `financial_scoring_strategy.py` from engine_core.py | ~200 | 1h |
| 6.3 | EXTRACT | `financial_filters.py` from engine_core.py | ~400 | 2h |
| 6.4 | EXTRACT | `response_builder.py` from engine_core.py | ~640 | 2h |
| 6.5 | PRESERVE | `engine_core.py` → deprecated (production remains) | — | 10 min |
| **Total** | | | ~1840 | **~8h** |

---

## 6. Service Layer Alignment

### 6.1 Target Service Pattern (Consistent with Vault Keepers)

```python
# services/api_neural_engine/main.py — SLIM APP FACTORY

from fastapi import FastAPI
from .config import Settings
from .api.routes import router
from .adapters.bus_adapter import NeuralBusAdapter
from .monitoring import setup_metrics

def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title="Neural Engine API", version="2.1.0")
    
    # Include routes
    app.include_router(router, tags=["Neural Engine"])
    
    # Setup bus adapter
    app.state.bus = NeuralBusAdapter(settings)
    
    # Setup metrics
    setup_metrics(app)
    
    return app

app = create_app()
```

### 6.2 Config Pattern (env-based domain loading)

```python
# services/api_neural_engine/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Domain selection
    DOMAIN: str = "mock"  # "mock", "finance", "healthcare", ...
    
    # Database
    POSTGRES_HOST: str = "core_postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "vitruvyan_core"
    POSTGRES_USER: str = "vitruvyan_core_user"
    POSTGRES_PASSWORD: str = ""
    
    # Redis (Cognitive Bus)
    REDIS_HOST: str = "core_redis"
    REDIS_PORT: int = 6379
    
    # Vector DB
    QDRANT_HOST: str = "core_qdrant"
    QDRANT_PORT: int = 6333
    
    # Engine
    STRATIFICATION_MODE: str = "global"
    ENABLE_TIME_DECAY: bool = False
    CACHE_TTL_SECONDS: int = 30
    
    class Config:
        env_prefix = ""
```

### 6.3 Domain Loader (replaces hardcoded MockDataProvider)

```python
# services/api_neural_engine/modules/engine_orchestrator.py

async def initialize(self):
    domain = os.getenv("DOMAIN", "mock")
    
    if domain == "mock":
        from vitruvyan_core.core.neural_engine.examples import MockDataProvider, MockScoringStrategy
        self.data_provider = MockDataProvider(num_entities=100)
        self.scoring_strategy = MockScoringStrategy()
    
    elif domain == "finance":
        # ← vitruvyan (production repo) provides these
        from core.logic.neural_engine.financial_data_provider import FinancialDataProvider
        from core.logic.neural_engine.financial_scoring_strategy import FinancialScoringStrategy
        self.data_provider = FinancialDataProvider()
        self.scoring_strategy = FinancialScoringStrategy()
    
    else:
        raise ValueError(f"Unknown domain: {domain}")
    
    self.engine = NeuralEngine(
        data_provider=self.data_provider,
        scoring_strategy=self.scoring_strategy,
        stratification_mode=os.getenv("STRATIFICATION_MODE", "global")
    )
```

---

## 7. Contract Refinements

### 7.1 New Contract: IFilterStrategy

The monolith has 7 filtering functions (momentum_breakout, value_screening, divergence_detection, etc.) with no common interface. Proposal:

```python
# vitruvyan_core/contracts/filter_strategy.py

from abc import ABC, abstractmethod
import pandas as pd

class IFilterStrategy(ABC):
    """
    Optional filter strategy applied AFTER composite scoring, BEFORE ranking.
    
    Examples:
    - Finance: momentum breakout (z > 2.0), earnings safety, sector capping
    - Healthcare: acuity threshold, readmission risk filter
    - Logistics: delivery deadline filter, capacity constraint
    """
    
    @abstractmethod
    def get_available_filters(self) -> list[str]:
        """Returns list of available filter names."""
        pass
    
    @abstractmethod
    def apply_filters(
        self,
        df: pd.DataFrame,
        active_filters: dict[str, Any],
        **kwargs
    ) -> pd.DataFrame:
        """
        Applies active filters to scored DataFrame.
        
        Args:
            df: DataFrame with composite_score column
            active_filters: Dict of filter_name → config
                e.g., {"momentum_breakout": True, "earnings_safety_days": 7}
        
        Returns:
            Filtered DataFrame
        """
        pass
```

### 7.2 IDataProvider Enhancement

Add optional `get_features_batch()` for bulk + streaming support:

```python
# Addition to IDataProvider

def get_features_batch(
    self,
    entity_ids: list[str],
    feature_names: Optional[list[str]] = None,
    batch_size: int = 100
) -> Iterator[pd.DataFrame]:
    """
    Yields features in batches (for large universes).
    Default: single batch via get_features().
    """
    yield self.get_features(entity_ids, feature_names)
```

---

## 8. Implementation Phases

### Summary

| Phase | Description | Effort | Depends On |
|-------|------------|--------|------------|
| **Phase 1** | Core domain enrichment (domain/, governance/, philosophy/) | 2.5h | Nothing |
| ~~**Phase 2**~~ | ~~Consumers~~ — REMOVED (NE is request-response, not event-driven) | — | — |
| **Phase 3** | Service layer alignment (config, adapters, routes) | 4h | Phase 1 |
| **Phase 4** | Contract extension (IFilterStrategy) | 35 min | Nothing |
| **Phase 5** | Unit tests | 2.5h | Phase 1,3 |
| **Phase 6** | Finance plugin extraction (vitruvyan repo) | 8h | Phase 4 |
| **TOTAL** | | **~18h** | |

### Recommended Order

```
Phase 1 + Phase 4 (parallel, no deps)          → 3h
Phase 3 (after Phase 1)                        → 4h
Phase 5 (after Phase 1+3)                      → 2.5h
Phase 6 (after Phase 4, can be deferred)       → 8h
                                                ────
                                  Fast track: ~8h (Phases 1,3-5, core only)
                                  Full delivery: ~18h (including finance plugin)
```

---

## 9. Risk Assessment

### Low Risk ✅
- **Domain enrichment (Phase 1)**: Additive only, no existing code changes
- **Philosophy charter**: Documentation only
- **Contract extension (Phase 4)**: New file, no breaking changes

### Medium Risk ⚠️
- **Service layer restructure (Phase 3)**: Routes extraction requires careful import management
- **engine_orchestrator.py domain loading**: Must test MockDataProvider still works after refactor
- **Consumer base class**: Must follow StreamBus patterns (mkstream=True, acknowledge, generator)

### High Risk 🔴
- **Finance plugin extraction (Phase 6)**: 2,860-line monolith decomposition
  - Production system, zero-downtime required
  - 13+ direct psycopg2 connections to replace with PostgresAgent
  - VARE engine tight coupling (proprietary)
  - `build_json()` has 640 lines of financial response formatting
  - **Mitigation**: Keep `engine_core.py` as production fallback, new files as opt-in via DOMAIN env

### Data Loss Risk: NONE
- Original monolith preserved in production
- _legacy/ directories preserve all original code
- No database migrations required

---

## Appendix A: File Size Comparison

### Before (Current)

| Location | Files | Lines | Notes |
|----------|:-----:|------:|-------|
| vitruvyan `engine_core.py` | 1 | 2,860 | God Object |
| vitruvyan `api_server.py` | 1 | 206 | Thin wrapper |
| vitruvyan-core `core/neural_engine/` | 7 | 1,478 | Clean but incomplete |
| vitruvyan-core `services/api_neural_engine/` | 7 | 911 | Clean but minimal |
| vitruvyan-core `contracts/` | 3 | 406 | Good |
| **TOTAL** | **19** | **5,861** | |

### After (Target)

| Location | Files | Lines (est.) | Notes |
|----------|:-----:|------:|-------|
| vitruvyan-core `core/neural_engine/` | ~22 | ~2,100 | Complete 7-layer pattern |
| vitruvyan-core `services/api_neural_engine/` | ~14 | ~1,300 | Full service pattern |
| vitruvyan-core `contracts/` | 4 | ~490 | +IFilterStrategy |
| vitruvyan `engine_core.py` (preserved) | 1 | 2,860 | Deprecated, production fallback |
| vitruvyan new plugin files | 4 | ~1,840 | Finance implementations |
| **TOTAL** | **~45** | **~8,590** | |

### Metrics

- **Average file size**: 5,861/19 = 308 lines → ~7,800/~38 = **~205 lines** (33% smaller per file)
- **Max file size**: 2,860 lines → **~600 lines** (financial_data_provider — largest plugin)
- **Testability**: 0% → 100% (every module independently testable via contracts)
- **Domain coupling**: 100% finance → **0% in core** (finance only in vitruvyan plugin)
- **Bus coupling**: 0% in core (optional adapter in service layer only)
- **Bus coupling**: 0% in core (optional adapter in service layer only)

---

## Appendix B: Cognitive Bus — Optional Service-Level Notifications

The Neural Engine core has **NO bus dependency**. The service layer MAY publish notifications via `adapters/bus_adapter.py` so Sacred Orders can react:

```
neural_engine.screening.completed     — Service notifies Sacred Orders after successful screening
neural_engine.screening.failed        — Service notifies Sacred Orders after failure
```

These are **fire-and-forget notifications**, not request-response patterns. NE doesn't consume bus events.

**Publisher**: api_neural_engine service (optional, via bus_adapter)
**Subscribers**: vault_keepers (archive results), orthodoxy_wardens (audit rankings)

> **Note**: The bus adapter is OPTIONAL. NE works 100% without it. Sacred Orders subscribe if they want to react to screening results.

---

## Appendix C: Naming Conventions (Consistent With Sacred Orders)

| Concept | Governance Order | Reason Order (Neural Engine) |
|---------|:---:|:---:|
| Primary agent | `inquisitor_agent.py` | `engine.py` |
| Specialized agents | `confessor_agent.py`, `penitent_agent.py` | `scoring.py`, `composite.py`, `ranking.py` |
| Domain objects | `domain/confession.py`, `domain/verdict.py` | `domain/screening_request.py`, `domain/entity_score.py` |
| Events | `events/orthodoxy_events.py` | N/A in core (bus_adapter in service) |
| Bus consumers | `consumers/chronicler.py` | N/A — request-response |
| Service routes | `api/routes.py` | `api/routes.py` |
| Config | `config.py` | `config.py` |
| Bus adapter | `adapters/bus_adapter.py` | `adapters/bus_adapter.py` |
| Persistence | `adapters/persistence.py` | `adapters/persistence.py` |
| Tests | `tests/test_consumers.py` | `tests/test_engine.py` |
| Identity | `philosophy/charter.md` | `philosophy/charter.md` |

---

*Last updated: February 10, 2026*
