# Contracts Package

**Location**: `vitruvyan_core/contracts/`  
**Purpose**: System-wide abstract interfaces defining the contract between core components and domain implementations.

**Canonical import namespace**: `contracts` / `vitruvyan_core.contracts`

---

## 🎯 Why Contracts are at Root Level

### Architectural Decision
Contracts are positioned at the **root of `vitruvyan_core/`** (not inside individual components like `neural_engine/`) for the following reasons:

#### 1. **Multi-Component System**
vitruvyan-core is not a single-purpose library. It contains multiple subsystems:
- `core/cognitive/` - Babel Gardens, Pattern Weavers, VEE
- `core/governance/` - Orthodoxy Wardens, Vault Keepers, Memory Orders
- `core/orchestration/` - LangGraph flows
- `core/neural_engine/` - Scoring and ranking engine

**Rationale**: Contracts define boundaries that MULTIPLE components can depend on, not just Neural Engine.

#### 2. **Cross-Component Reusability**
Current contracts (`IDataProvider`, `IScoringStrategy`) were designed for Neural Engine, but:
- An **Allocation Engine** might use the same `IDataProvider` for portfolio data
- A **Risk Engine** might use the same `IScoringStrategy` for risk scoring
- A **Recommendation Engine** might implement custom strategies using the same interfaces

**Rationale**: Placing contracts at root enables **horizontal reuse** across engines.

#### 3. **Consistency with Existing Pattern**
The `domains/` folder already contains system-wide contracts:
- `aggregation_contract.py` - Data aggregation interface
- `explainability_contract.py` - VEE narrative generation
- `risk_contract.py` - Risk assessment interface

**Rationale**: `vitruvyan_core/contracts/` follows the same **"contracts as public API"** pattern.

#### 4. **Clear System Boundaries**
Contracts mark the **epistemic boundary** between:
- **Core Logic** (domain-agnostic algorithms) ← Lives in `core/`
- **Domain Implementations** (finance, healthcare, logistics) ← Lives in `domains/` or `verticals/`

**Rationale**: Root-level contracts signal "these are the system's public interfaces".

---

## 📦 Current Contracts

In addition to Neural Engine interfaces, this package also exposes:
- `ILLMProvider` (`llm_provider.py`)
- orchestration contracts (`orchestration.py`): `GraphPlugin`, `NodeContract`, `BaseGraphState`, `Parser`, `BaseParser`, `ParsedSlots`

### IDataProvider
**File**: `data_provider.py`  
**Purpose**: Abstract interface for domain-specific data acquisition.

**Methods**:
- `get_universe()` - Returns all entities (tickers, patients, shipments)
- `get_features()` - Returns metrics/features for entities
- `get_metadata()` - Returns domain-specific context
- `validate_entity_ids()` - Checks if entities exist

**Implementations**:
- Finance: `TickerDataProvider` (PostgreSQL queries for tickers, momentum, trend, volatility)
- Healthcare: `PatientDataProvider` (EHR queries for patients, vitals, labs)
- Logistics: `ShipmentDataProvider` (tracking data for shipments, routes)

---

### IScoringStrategy
**File**: `scoring_strategy.py`  
**Purpose**: Abstract interface for domain-specific scoring logic.

**Methods**:
- `get_profile_weights()` - Returns feature weights for a profile
- `get_available_profiles()` - Lists available scoring profiles
- `compute_composite_score()` - Calculates weighted composite score
- `apply_risk_adjustment()` - Optional risk penalty/boost

**Implementations**:
- Finance: `FinancialScoringStrategy` (profiles: short_spec, balanced_mid, trend_follow)
- Healthcare: `ClinicalScoringStrategy` (profiles: high_risk, moderate_risk, preventive)
- Logistics: `DeliveryScoringStrategy` (profiles: urgent, standard, bulk)

---

## 📖 Usage Pattern

### Consumer Perspective (Domain Implementer)
```python
# Finance domain implements contracts
from vitruvyan_core.contracts import IDataProvider, IScoringStrategy

class TickerDataProvider(IDataProvider):
    def get_universe(self, filters=None):
        # Query PostgreSQL tickers table
        return pd.DataFrame(...)
```

### Producer Perspective (Core Component)
```python
# Neural Engine depends on contracts
from vitruvyan_core.contracts import IDataProvider, IScoringStrategy

class NeuralEngine:
    def __init__(self, data_provider: IDataProvider, scoring_strategy: IScoringStrategy):
        self.data_provider = data_provider
        self.scoring_strategy = scoring_strategy
```

**Key Insight**: Core components depend on **abstractions** (contracts), not **implementations** (domains). This is the **Dependency Inversion Principle**.

---

## 🔄 Alternative Considered (and Rejected)

### Option: Contracts Inside Neural Engine
```
vitruvyan_core/
  core/
    neural_engine/
      contracts/  ← Alternative location
        data_provider.py
        scoring_strategy.py
```

**Why Rejected**:
1. **Low cohesion**: If an Allocation Engine needs `IDataProvider`, it would import from `neural_engine/contracts/` (misleading)
2. **Portability issues**: If Neural Engine becomes standalone package, contracts would be artificially nested
3. **Breaks consistency**: Inconsistent with `domains/` contracts pattern

**Current approach is superior** for a multi-component ecosystem like vitruvyan-core.

---

## 🎓 Design Principles

### 1. Contracts are Stable
Contracts change **rarely**. Adding a method to `IDataProvider` affects all implementations.

**Golden Rule**: Think 10x before modifying a contract. Prefer extension over modification.

### 2. Contracts are Minimal
Each contract has **exactly the methods needed**, no more.

**Counter-example**: Don't add `get_historical_data()` if current implementations don't need it.

### 3. Contracts are Domain-Agnostic
Contracts use **generic terminology**: "entity" not "ticker", "feature" not "RSI".

**Why**: Finance uses "tickers", healthcare uses "patients", logistics uses "shipments". Contract terminology must be universal.

### 4. Contracts Have Exceptions
Each contract defines **custom exceptions** for failure modes.

**Example**:
```python
class DataProviderError(Exception): pass
class ValidationError(DataProviderError): pass
```

This enables precise error handling in core components.

---

## 🔮 Future Contracts (Roadmap)

As vitruvyan-core grows, expect new contracts:
- `IOptimizationStrategy` - Portfolio optimization, resource allocation
- `IExplainabilityEngine` - VEE-style narrative generation (generalization of current VEE)
- `IRiskAnalyzer` - VARE-style multi-dimensional risk assessment
- `IContextProvider` - Pattern Weavers-style semantic contextualization

All of these will live in `vitruvyan_core/contracts/` to maintain architectural consistency.

---

## 📚 References

- **Neural Engine README**: `core/neural_engine/README.md` - Primary consumer of these contracts
- **Neural Engine Architecture**: `docs/NEURAL_ENGINE_ARCHITECTURE.md` - Design decisions
- **Domain Contracts**: `domains/*.py` - Other system-wide contracts

---

## 🤝 Contributing

When adding a new contract:
1. **Check necessity**: Is this truly system-wide? Or component-specific?
2. **Use ABC**: All contracts inherit from `abc.ABC`
3. **Define exceptions**: Each contract should have its own exception hierarchy
4. **Document methods**: Every method needs docstring with Args, Returns, Raises
5. **Add to `__init__.py`**: Export new contract from `contracts/__init__.py`

**Example PR**:
```python
# vitruvyan_core/contracts/optimization_strategy.py
from abc import ABC, abstractmethod

class IOptimizationStrategy(ABC):
    """Contract for domain-specific optimization logic."""
    
    @abstractmethod
    def optimize(self, entities, constraints):
        """Optimize entity allocation given constraints."""
        pass
```

Then update `__init__.py`:
```python
from .optimization_strategy import IOptimizationStrategy
__all__ = [..., 'IOptimizationStrategy']
```

---

**Status**: ✅ Production (2 contracts in use by Neural Engine)  
**Last Updated**: February 8, 2026  
**Architecture Owner**: Vitruvyan Core Team
