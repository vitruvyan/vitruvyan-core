# Neural Engine Architecture (Domain-Agnostic Core)

**Status**: ✅ PHASE 1 COMPLETE  
**Date**: February 8, 2026  
**Author**: vitruvyan-core team

---

## 🎯 **Design Philosophy**

> **"Separate logic from domain. Core is agnostic, domains are pluggable."**

The Neural Engine in `vitruvyan-core` is **100% domain-agnostic**. Financial logic (tickers, RSI, MACD, sentiment) does NOT exist in the core—it's implemented as a **pluggable domain** via contracts.

---

## 🏗️ **Architecture Layers**

```
┌─────────────────────────────────────────────────────┐
│  CONTRACTS (Interfaces)                             │
│  - IDataProvider: Data access contract              │
│  - IScoringStrategy: Scoring logic contract         │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  NEURAL ENGINE CORE (Domain-Agnostic)               │
│  ├── engine.py: Main orchestrator                   │
│  ├── scoring.py: Z-score calculator                 │
│  ├── composite.py: Composite scorer                 │
│  └── ranking.py: Entity ranker                      │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  DOMAINS (Pluggable Implementations)                │
│  ├── finance/                                       │
│  │   ├── providers/: TickerDataProvider            │
│  │   └── strategies/: FinancialScoringStrategy     │
│  ├── healthcare/                                    │
│  │   ├── providers/: PatientDataProvider           │
│  │   └── strategies/: ClinicalScoringStrategy      │
│  └── logistics/                                     │
│      ├── providers/: ShipmentDataProvider          │
│      └── strategies/: DeliveryScoringStrategy      │
└─────────────────────────────────────────────────────┘
```

---

## 📦 **File Structure**

```
vitruvyan-core/
├── vitruvyan_core/
│   ├── contracts/                  ← Interfaces (8 files)
│   │   ├── __init__.py
│   │   ├── data_provider.py       → IDataProvider interface
│   │   └── scoring_strategy.py    → IScoringStrategy interface
│   │
│   ├── core/
│   │   └── neural_engine/         ← Core Logic (5 files)
│   │       ├── __init__.py
│   │       ├── engine.py          → NeuralEngine (orchestrator)
│   │       ├── scoring.py         → ZScoreCalculator
│   │       ├── composite.py       → CompositeScorer
│   │       └── ranking.py         → RankingEngine
│   │
│   └── domains/                    ← Domain Implementations (stubs)
│       ├── __init__.py
│       └── [finance/healthcare/logistics implementations go here]
│
└── tests/
    ├── test_neural_engine_mock.py      ← Mock DataProvider
    └── test_neural_engine_integration.py ← Integration test
```

**Total Files Created**: 13 files (8 core + 5 contracts)

---

## 🧩 **Core Components**

### 1. **NeuralEngine** (engine.py)
Main orchestrator. Coordinates the entire pipeline:
1. Extract universe (entities to analyze)
2. Extract features (raw metrics)
3. Compute z-scores (stratified or global)
4. Apply time decay (optional)
5. Compute composite scores (weighted average)
6. Apply risk adjustment (optional)
7. Rank entities (by composite score)

**Usage**:
```python
from vitruvyan_core.core.neural_engine import NeuralEngine
from my_domain import MyDataProvider, MyScoringStrategy

engine = NeuralEngine(
    data_provider=MyDataProvider(),
    scoring_strategy=MyScoringStrategy(),
    stratification_mode="composite"
)

results = engine.run(
    profile="balanced",
    top_k=10,
    risk_tolerance="medium"
)
```

---

### 2. **ZScoreCalculator** (scoring.py)
Computes z-scores with 3 stratification modes:
- **global**: Z-score vs entire universe
- **stratified**: Z-score vs grouping field (e.g., sector, region)
- **composite**: 30% global + 70% stratified (balanced)

**Formula**:
```
z = (x - μ) / σ
```

**Time Decay** (optional):
```
z_decayed = z × exp(-days_old / 30)
```

---

### 3. **CompositeScorer** (composite.py)
Computes weighted composite score using profile weights.

**Formula**:
```
composite_score = Σ(z_score_i × weight_i) / Σ(weight_i)
```

**Handles missing data**: Dynamically normalizes weights when z-scores are NULL.

---

### 4. **RankingEngine** (ranking.py)
Ranks entities by composite score with bucketing:
- **top**: percentile ≥ 70
- **middle**: 30 ≤ percentile < 70
- **bottom**: percentile < 30

**Output**:
```
| entity_id | rank | composite_score | percentile | bucket |
|-----------|------|-----------------|------------|--------|
| E001      | 1    | 1.85            | 100.0      | top    |
| E002      | 2    | 1.23            | 90.0       | top    |
```

---

## 🔌 **Contracts (Interfaces)**

### IDataProvider
Defines how to fetch data for any domain.

**Required Methods**:
- `get_universe(filters)` → DataFrame with entities
- `get_features(entity_ids, feature_names)` → DataFrame with metrics
- `get_metadata()` → Domain metadata
- `validate_entity_ids(entity_ids)` → Validate IDs

**Example (Finance)**:
```python
class TickerDataProvider(IDataProvider):
    def get_universe(self, filters):
        # Query tickers table (PostgreSQL)
        # Returns: entity_id=ticker, stratification_field=sector
    
    def get_features(self, entity_ids, feature_names):
        # Query momentum_logs, trend_logs, sentiment_scores
        # Returns: momentum, trend, volatility, sentiment
```

---

### IScoringStrategy
Defines scoring profiles and weights.

**Required Methods**:
- `get_profile_weights(profile)` → Dict[feature, weight]
- `get_available_profiles()` → List[profile_names]
- `compute_composite_score()` → (delegated to CompositeScorer)
- `apply_risk_adjustment()` → Risk adjustment logic (optional)

**Example (Finance)**:
```python
class FinancialScoringStrategy(IScoringStrategy):
    PROFILES = {
        "short_spec": {"momentum": 0.35, "trend": 0.20, "volatility": 0.15, "sentiment": 0.10, ...},
        "balanced_mid": {"momentum": 0.15, "trend": 0.20, "volatility": 0.12, "sentiment": 0.10, ...}
    }
    
    def get_profile_weights(self, profile):
        return self.PROFILES[profile]
```

---

## 🎭 **Domain Stubs (Future)**

The `domains/` directory will contain domain-specific implementations:

```
domains/
├── finance/
│   ├── providers/
│   │   ├── ticker_provider.py       → PostgreSQL: tickers, momentum_logs, trend_logs
│   │   ├── sentiment_provider.py    → sentiment_scores
│   │   └── fundamentals_provider.py → fundamentals table
│   └── strategies/
│       ├── profile_weights.py       → 5 profiles (short_spec, balanced_mid, ...)
│       └── vare_adjustment.py       → VARE risk adjustment
│
├── healthcare/
│   ├── providers/
│   │   └── patient_provider.py      → EHR database
│   └── strategies/
│       └── clinical_scoring.py      → Risk stratification profiles
│
└── logistics/
    ├── providers/
    │   └── shipment_provider.py     → Shipment tracking DB
    └── strategies/
        └── delivery_scoring.py      → Delivery urgency profiles
```

---

## ✅ **What's Domain-Agnostic (Core)**

| Component | Agnostic? | Logic |
|-----------|-----------|-------|
| Z-score calculation | ✅ | Pure math: (x - μ) / σ |
| Stratification (global/sector/composite) | ✅ | Group-by logic, any field |
| Composite scoring | ✅ | Weighted average of z-scores |
| Time decay | ✅ | exp(-t / half_life) |
| Ranking & bucketing | ✅ | Sort by score, percentile calc |
| Entity universe extraction | ✅ | DataFrame operations |

---

## ❌ **What's Domain-Specific (Pluggable)**

| Component | Domain | Logic |
|-----------|--------|-------|
| Data source (PostgreSQL/API/files) | Finance/Healthcare/Logistics | IDataProvider |
| Feature names (RSI vs severity_score) | Finance/Healthcare/Logistics | IDataProvider.get_metadata() |
| Profile weights (short_spec vs high_risk) | Finance/Healthcare/Logistics | IScoringStrategy |
| Risk adjustment (VARE vs clinical) | Finance/Healthcare/Logistics | IScoringStrategy.apply_risk_adjustment() |

---

## 🚀 **Migration Path from Vitruvyan (Finance)**

Original `vitruvyan/core/logic/neural_engine/engine_core.py` (2,860 lines):
- **Lines 1-500**: PostgreSQL queries (tickers, momentum_logs, trend_logs, etc.)
- **Lines 500-1500**: Z-score functions (get_momentum_z, get_trend_z, etc.)
- **Lines 1500-2000**: Composite scoring with profile weights
- **Lines 2000-2500**: VARE risk adjustment, dark pool analysis
- **Lines 2500-2860**: Ranking, bucketing, API response formatting

**Refactoring Strategy**:
1. **Core Logic → vitruvyan-core** (DONE ✅):
   - Z-score calculation → `scoring.py`
   - Composite scoring → `composite.py`
   - Ranking → `ranking.py`

2. **Finance Domain → domains/finance/** (TODO 📋):
   - PostgreSQL queries → `providers/ticker_provider.py`
   - Profile weights → `strategies/profile_weights.py`
   - VARE adjustment → `strategies/vare_adjustment.py`

3. **API Layer → service wrapper** (TODO 📋):
   - FastAPI endpoint calls NeuralEngine with FinancialDataProvider
   - Backwards-compatible with existing `/neural-engine` endpoint

---

## 🧪 **Testing**

**Mock Test** (`test_neural_engine_mock.py`):
- MockDataProvider: 10 entities, 3 features (momentum, trend, volatility)
- MockScoringStrategy: 2 profiles (balanced, aggressive)
- Validates full pipeline (universe → features → z-scores → composite → ranking)

**Run Test**:
```bash
cd /home/caravaggio/vitruvyan-core
python3 tests/test_neural_engine_integration.py
```

**Expected Output**:
```
=== Neural Engine Test (Mock Data) ===
Domain: mock
Profile: balanced
Entities scored: 10

Top 5 entities:
  entity_id  rank  composite_score  percentile bucket
0      E001     1            1.234        100.0    top
1      E002     2            0.987         90.0    top
2      E003     3            0.765         80.0    top
...

Bucket statistics: {'top_count': 3, 'middle_count': 4, 'bottom_count': 3}
```

---

## 📊 **Benefits of This Architecture**

| Benefit | Impact |
|---------|--------|
| **Modularity** | Core + Contracts + Domains = clean separation |
| **Reusability** | Same core works for finance, healthcare, logistics |
| **Testability** | Mock providers for unit tests (no DB dependency) |
| **Scalability** | Add new domains without touching core |
| **Maintainability** | Each layer has single responsibility |
| **Enterprise-grade** | Clean contracts enable team collaboration |

---

## 🔮 **Next Steps**

### Phase 1: Core (COMPLETE ✅)
- [x] Contracts: IDataProvider, IScoringStrategy
- [x] Neural Engine core: engine, scoring, composite, ranking
- [x] Mock implementations for testing

### Phase 2: Finance Domain (TODO 📋)
- [ ] TickerDataProvider (PostgreSQL integration)
- [ ] FinancialScoringStrategy (5 profiles + VARE)
- [ ] Migration from vitruvyan/core/logic/neural_engine
- [ ] Unit tests for finance domain
- [ ] E2E test with real ticker data

### Phase 3: API Wrapper (TODO 📋)
- [ ] FastAPI service using NeuralEngine + FinancialDataProvider
- [ ] Backwards compatibility with existing MCP tools
- [ ] Docker service deployment

### Phase 4: Documentation & Examples (TODO 📋)
- [ ] Finance domain implementation guide
- [ ] Healthcare domain example (patient risk scoring)
- [ ] Logistics domain example (shipment prioritization)

---

## 📚 **Key Files**

| File | Purpose | Lines |
|------|---------|-------|
| `contracts/neural_engine/data_provider.py` | IDataProvider interface | 150 |
| `contracts/neural_engine/scoring_strategy.py` | IScoringStrategy interface | 180 |
| `core/neural_engine/engine.py` | Main orchestrator | 320 |
| `core/neural_engine/scoring.py` | Z-score calculator | 200 |
| `core/neural_engine/composite.py` | Composite scorer | 140 |
| `core/neural_engine/ranking.py` | Entity ranker | 160 |

**Total Core Lines**: ~1,150 lines (vs 2,860 in original monolithic file)

---

## 🎯 **Golden Rules**

1. ✅ **Core is domain-agnostic**: NO finance-specific logic in `core/neural_engine/`
2. ✅ **Contracts are stable**: IDataProvider, IScoringStrategy don't change per domain
3. ✅ **Domains are pluggable**: Add new domains without modifying core
4. ✅ **Test with mocks**: Unit tests don't need real databases
5. ✅ **Stratification is generic**: Works for sectors, regions, age groups, etc.

---

**Status**: ✅ Phase 1 Complete - Core architecture ready for domain implementations  
**Next**: Implement FinancialDataProvider and FinancialScoringStrategy (Phase 2)
