# Domain Implementation Examples

**Location**: `vitruvyan_core/core/neural_engine/domain_examples/`  
**Purpose**: Stub implementations showing developers **exactly where and how** to implement domain-specific logic for Neural Engine.

---

## 🎯 Why This Folder Exists

When you want to use Neural Engine for your domain (finance, healthcare, logistics), you need to implement **2 contracts**:
1. **IDataProvider** - How to fetch your entities and features
2. **IScoringStrategy** - How to score and rank your entities

This folder contains **fully documented stub implementations** that:
- ✅ Work out-of-the-box for testing (no DB required)
- ✅ Show exact method signatures you must implement
- ✅ Include TODO comments pointing to real domain examples
- ✅ Demonstrate common patterns (filtering, validation, error handling)

---

## 📦 Files in This Package

### 1. `mock_data_provider.py`
**Stub implementation of `IDataProvider` contract.**

**What it does**:
- Generates 10 synthetic entities (E001-E010)
- Returns 3 mock features (momentum, trend, volatility)
- Assigns entities to 2 stratification groups (GroupA, GroupB)
- Validates entity IDs

**Methods implemented**:
- `get_universe(filters)` - Returns all entities with metadata
- `get_features(entity_ids, feature_names)` - Returns features for specified entities
- `get_metadata()` - Returns data source information
- `validate_entity_ids(entity_ids)` - Checks which IDs exist

**How to use as template**:
```python
# STEP 1: Copy to your domain
cp mock_data_provider.py ../../domains/finance/ticker_provider.py

# STEP 2: Rename class
class TickerDataProvider(IDataProvider):  # was MockDataProvider

# STEP 3: Replace synthetic data with PostgreSQL queries
def get_universe(self, filters=None):
    query = "SELECT ticker, company_name, sector FROM tickers WHERE active=true"
    return self.pg.execute_query(query).to_df()
```

**Real domain examples** (see TODO comments in file):
- **Finance**: Query `tickers`, `momentum_logs`, `trend_logs`, `volatility_logs` tables
- **Healthcare**: Query `patients`, `vitals`, `labs`, `diagnoses` tables
- **Logistics**: Query `shipments`, `routes`, `tracking_events` tables

---

### 2. `mock_scoring_strategy.py`
**Stub implementation of `IScoringStrategy` contract.**

**What it does**:
- Provides 2 mock profiles (balanced, aggressive)
- Computes weighted composite scores: Σ(z_score × weight) / Σ(weights)
- Handles missing features with dynamic weight normalization
- No-op risk adjustment (returns scores unchanged)

**Methods implemented**:
- `get_profile_weights(profile)` - Returns feature → weight mapping
- `get_available_profiles()` - Lists all profile names
- `compute_composite_score(z_scores, profile)` - Calculates weighted average
- `apply_risk_adjustment(scores, risk_data, risk_tolerance)` - Adjusts scores for risk

**How to use as template**:
```python
# STEP 1: Copy to your domain
cp mock_scoring_strategy.py ../../domains/finance/scoring_strategy.py

# STEP 2: Rename class
class FinancialScoringStrategy(IScoringStrategy):  # was MockScoringStrategy

# STEP 3: Load real profiles from config
def __init__(self, config_path: str):
    with open(config_path) as f:
        self._profiles = yaml.safe_load(f)  # Load from YAML/database

# STEP 4: Implement risk adjustment
def apply_risk_adjustment(self, scores, risk_data, risk_tolerance):
    vare = VAREEngine()  # Real risk engine
    risk_scores = vare.assess_risk(scores.index.tolist())
    penalty = {'low': 0.40, 'medium': 0.20, 'high': 0.08}[risk_tolerance]
    return scores * (1 - risk_scores / 100 * penalty)
```

**Real domain examples** (see TODO comments in file):
- **Finance**: 5 profiles (short_spec, balanced_mid, trend_follow, momentum_focus, sentiment_boost) + VARE risk adjustment
- **Healthcare**: 3 profiles (high_risk, moderate_risk, preventive) + comorbidity multipliers
- **Logistics**: 3 profiles (urgent, standard, bulk) + weather/route conditions

---

## 🚀 Quick Start Guide

### Testing Neural Engine Without Database

1. **Use mock implementations directly**:
```python
from vitruvyan_core.core.neural_engine import NeuralEngine
from vitruvyan_core.core.neural_engine.domain_examples import (
    MockDataProvider,
    MockScoringStrategy
)

# Initialize with mock domain
provider = MockDataProvider(num_entities=10)
strategy = MockScoringStrategy()
engine = NeuralEngine(data_provider=provider, scoring_strategy=strategy)

# Run pipeline
results = engine.run(
    profile='balanced',
    stratification_mode='global',
    top_k=5
)

print(results['ranked_entities'])
```

2. **Output**:
```
   rank entity_id  composite_score  percentile bucket
0     1      E007             1.85        90.0    top
1     2      E003             1.42        80.0    top
2     3      E009             0.97        70.0    top
3     4      E001             0.53        60.0 middle
4     5      E005            -0.12        50.0 middle
```

---

## 📖 Implementing Your Domain (Step-by-Step)

### Phase 1: Create Domain Package Structure
```bash
mkdir -p vitruvyan_core/domains/your_domain
touch vitruvyan_core/domains/your_domain/__init__.py
```

### Phase 2: Implement Data Provider
```bash
# Copy mock as starting point
cp vitruvyan_core/core/neural_engine/domain_examples/mock_data_provider.py \
   vitruvyan_core/domains/your_domain/data_provider.py

# Edit file:
# 1. Rename class: MockDataProvider → YourDomainDataProvider
# 2. Replace __init__ with real connection (PostgreSQL, API, file)
# 3. Replace get_universe with real query
# 4. Replace get_features with real query
# 5. Update get_metadata with real info
```

### Phase 3: Implement Scoring Strategy
```bash
# Copy mock as starting point
cp vitruvyan_core/core/neural_engine/domain_examples/mock_scoring_strategy.py \
   vitruvyan_core/domains/your_domain/scoring_strategy.py

# Edit file:
# 1. Rename class: MockScoringStrategy → YourDomainScoringStrategy
# 2. Load real profiles (YAML, database, config)
# 3. Implement domain-specific composite logic
# 4. Implement domain-specific risk adjustment
```

### Phase 4: Test Your Domain
```python
# tests/test_your_domain_integration.py
from vitruvyan_core.core.neural_engine import NeuralEngine
from vitruvyan_core.domains.your_domain import (
    YourDomainDataProvider,
    YourDomainScoringStrategy
)

# Initialize with real domain
provider = YourDomainDataProvider(connection_string="...")
strategy = YourDomainScoringStrategy(config_path="...")
engine = NeuralEngine(data_provider=provider, scoring_strategy=strategy)

# Run pipeline
results = engine.run(profile='your_profile', top_k=10)
assert len(results['ranked_entities']) == 10
```

---

## 🔍 Key Implementation Patterns

### Pattern 1: Handle Missing Features Gracefully
Mock implementations show how to handle missing features with **dynamic weight normalization**:

```python
# If profile expects 5 features but only 3 available:
weights = {'A': 0.2, 'B': 0.3, 'C': 0.2, 'D': 0.2, 'E': 0.1}
available = ['A', 'B', 'C']  # D and E missing

# Dynamic normalization: adjust weights to sum to 1.0
active_weights = {f: weights[f] for f in available}  # {'A': 0.2, 'B': 0.3, 'C': 0.2}
weight_sum = sum(active_weights.values())  # 0.7
normalized = {f: w / weight_sum for f, w in active_weights.items()}  # {'A': 0.29, 'B': 0.43, 'C': 0.29}
```

### Pattern 2: Stratification Groups
Mock implementations assign entities to groups for **stratified z-score calculation**:

```python
# Finance example: group by sector
universe['group'] = universe['sector']  # ['Technology', 'Healthcare', 'Finance']

# Healthcare example: group by risk category
universe['group'] = universe['diagnosis_category']  # ['High Risk', 'Moderate', 'Low']

# Logistics example: group by region
universe['group'] = universe['region']  # ['North America', 'Europe', 'Asia-Pacific']
```

Neural Engine computes z-scores **within each group** (stratified mode) or **across all entities** (global mode).

### Pattern 3: Risk Adjustment Integration
Mock strategy shows **no-op risk adjustment** (returns scores unchanged). Real domains integrate risk engines:

```python
# Finance example: VARE risk engine
def apply_risk_adjustment(self, scores, risk_data, risk_tolerance):
    from core.logic.vitruvyan_proprietary import VAREEngine
    vare = VAREEngine()
    
    # Get multi-dimensional risk scores (0-100)
    risk_scores = vare.assess_risk(scores.index.tolist())
    
    # Apply tolerance-based penalty
    penalties = {'low': 0.40, 'medium': 0.20, 'high': 0.08}
    penalty_factor = penalties[risk_tolerance]
    
    # Penalize high-risk entities
    adjusted = scores * (1 - risk_scores / 100 * penalty_factor)
    return adjusted
```

---

## ✅ Checklist for Production-Ready Domain

Before deploying your domain implementation, verify:

- [ ] **IDataProvider implemented**
  - [ ] `get_universe()` queries real data source
  - [ ] `get_features()` returns all required features
  - [ ] `get_metadata()` returns accurate domain info
  - [ ] `validate_entity_ids()` checks real entity existence
  - [ ] Error handling for database/API failures

- [ ] **IScoringStrategy implemented**
  - [ ] `get_profile_weights()` loads from config/database
  - [ ] Profiles have valid weights (sum to 1.0)
  - [ ] `compute_composite_score()` handles missing features
  - [ ] `apply_risk_adjustment()` integrates real risk logic
  - [ ] `get_available_profiles()` returns active profiles only

- [ ] **Testing complete**
  - [ ] Unit tests for data provider (mock database)
  - [ ] Unit tests for scoring strategy (mock z-scores)
  - [ ] Integration test with real data (small sample)
  - [ ] Performance test (<100ms for 100 entities)

- [ ] **Documentation added**
  - [ ] README in domain package
  - [ ] Docstrings for all methods
  - [ ] Example usage in domain README

---

## 🎓 Learning Resources

- **Contracts Documentation**: `vitruvyan_core/contracts/README.md` - Contract specifications
- **Neural Engine README**: `vitruvyan_core/core/neural_engine/README.md` - Core architecture
- **Architecture Doc**: `docs/NEURAL_ENGINE_ARCHITECTURE.md` - Design decisions and patterns
- **Finance Domain Example**: `vitruvyan/core/logic/neural_engine/engine_core.py` (lines 1-2860) - Original monolithic implementation (reference only, being refactored)

---

## 🤝 Contributing Your Domain

If you implement a domain that could benefit others, consider contributing:

1. **Create pull request** with your domain package
2. **Add to `vitruvyan_core/domains/`**:
   - `your_domain/data_provider.py`
   - `your_domain/scoring_strategy.py`
   - `your_domain/README.md`
   - `your_domain/config/profiles.yaml` (if applicable)

3. **Update main docs**:
   - Add your domain to `neural_engine/README.md` examples
   - Document any domain-specific requirements

---

**Status**: ✅ Production Ready (Mock implementations for testing)  
**Last Updated**: February 8, 2026  
**Maintainer**: Vitruvyan Core Team
