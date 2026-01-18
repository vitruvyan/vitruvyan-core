# 🏛️ VITRUVYAN-CORE PHASE 3: VEE/VARE/VWRE ABSTRACTION
## Domain-Agnostic Explainability & Risk Engines

**Date**: December 30, 2025  
**Target AI**: Grok (Code Fast 1)  
**Context**: Continuation of vitruvyan-os → vitruvyan-core migration  
**Previous Work**: Phase 1E Neural Engine Core (✅ Complete), Phase 1D Boot Test (✅ Complete)

---

## 📋 PROJECT CONTEXT

### What Has Been Done
✅ **Phase 1E - Neural Engine Core** (Complete)
- Domain-agnostic evaluation substrate implemented
- Abstract contracts: `AbstractFactor`, `NormalizerStrategy`, `AggregationProfile`
- Orchestration pipeline: compute → normalize → aggregate
- 550 lines core + 400 lines patterns library
- Full test suite (390 lines)
- Documentation: Philosophy → Contracts → Patterns

✅ **Phase 1D - Boot Test** (Complete)
- All 6 MCP services running successfully
- PostgreSQL + Docker infrastructure operational
- Zero blockers identified

✅ **Domain Contracts** (Partial)
- `base_domain.py` implemented with abstract interfaces
- `EntitySchema`, `SignalSchema`, `ScoringFactor`, `DomainPolicy` defined
- Domain registration pattern established

### What Needs Work
⚠️ **Phase 3 - VEE/VARE/VWRE Abstraction** (This Task)
- VEE Engine: Currently 516 lines, finance-specific
- VARE Engine: Currently 752 lines, finance-specific
- VWRE Engine: Currently 612 lines, finance-specific
- **Total: ~1880 lines** of domain-coupled code

---

## 🎯 YOUR MISSION

Transform VEE/VARE/VWRE from **finance-specific implementations** into **domain-agnostic explainability/risk/attribution engines** that work for ANY vertical (finance, logistics, defense, healthcare, etc.).

### Core Principle
These engines should NOT know about:
- ❌ EntityIds, entities, collections, trading
- ❌ yfinance, market data, financial APIs
- ❌ RSI, MACD, momentum, volatility (as domain concepts)
- ❌ "Investment advice", "buy/sell signals"

They SHOULD provide:
- ✅ Generic explainability framework (multi-level narratives)
- ✅ Generic risk assessment (dimension-based scoring)
- ✅ Generic attribution analysis (factor contribution breakdown)
- ✅ Domain-agnostic templates that verticals customize

---

## 📁 FILES TO REFACTOR

### 1. VEE Engine (Vitruvyan Explainability Engine)
**Current Location**: `vitruvyan_core/core/cognitive/vitruvyan_proprietary/vee/`
- `vee_engine.py` (516 lines) - Main orchestrator
- `vee_analyzer.py` - KPI analysis
- `vee_generator.py` - Multi-level explanation generation
- `vee_memory_adapter.py` - Historical context integration

**Current Issues**:
```python
# Line 90: Finance-specific terminology
def explain_entity(self, entity_id: str, kpi: Dict[str, Any], ...

# Hardcoded financial knowledge
"market_risk", "volatility_risk", "momentum signals"
```

**Target State**:
```python
# Domain-agnostic interface
def explain_entity(
    self, 
    entity_id: str, 
    metrics: Dict[str, Any],
    domain_context: DomainContext,  # NEW: inject domain knowledge
    explanation_template: ExplanationTemplate  # NEW: domain provides templates
) -> ExplanationResult:
    """
    Generate multi-level explanations for ANY domain entity.
    
    Domain provides:
    - Entity schema (what is being explained)
    - Metric definitions (what signals mean)
    - Narrative templates (how to phrase explanations)
    - Risk factors (what dimensions to highlight)
    """
```

### 2. VARE Engine (Vitruvyan Adaptive Risk Engine)
**Current Location**: `vitruvyan_core/core/cognitive/vitruvyan_proprietary/vare_engine.py` (752 lines)

**Current Issues**:
```python
# Line 82: Hardcoded financial concepts
def analyze_ticker(self, entity_id: str, benchmark_ticker: Optional[str] = None)

# Line 52-59: Finance-specific risk dimensions
market_risk: float
volatility_risk: float
liquidity_risk: float
correlation_risk: float
```

**Target State**:
```python
@dataclass
class RiskDimension:
    """Generic risk dimension that domains customize"""
    name: str
    description: str
    calculation_method: Callable
    threshold_low: float
    threshold_high: float

def assess_risk(
    self,
    entity_id: str,
    metrics: pd.DataFrame,
    risk_dimensions: List[RiskDimension],  # Domain-provided
    risk_profile: RiskProfile  # Domain-provided
) -> RiskAssessment:
    """
    Multi-dimensional risk assessment for ANY entity type.
    
    Examples:
    - Finance: market_risk, liquidity_risk, volatility_risk
    - Logistics: delay_risk, cost_risk, reliability_risk
    - Healthcare: readmission_risk, complication_risk, mortality_risk
    """
```

### 3. VWRE Engine (Vitruvyan Weighted Reverse Engineering)
**Current Location**: `vitruvyan_core/core/cognitive/vitruvyan_proprietary/vwre_engine.py` (612 lines)

**Current Issues**:
```python
# Line 87: Hardcoded Neural Engine profile coupling
from core.cognitive.neural_engine.engine_core import PROFILE_WEIGHTS, FACTOR_MAP

# Line 100: Finance-specific factor names
{"momentum_z": 2.1, "trend_z": 1.5, "vola_z": -0.3, "sentiment_z": 0.8}
```

**Target State**:
```python
def analyze_attribution(
    self,
    entity_id: str,
    composite_score: float,
    factor_scores: Dict[str, float],  # Generic: {"factor1": 0.8, "factor2": -0.3}
    aggregation_profile: AggregationProfile  # From Neural Engine
) -> AttributionResult:
    """
    Decompose composite scores into factor contributions.
    
    Works with ANY factors defined by the vertical:
    - Finance: momentum, trend, volatility, sentiment
    - Logistics: cost, time, reliability, capacity
    - Defense: threat_level, resource_availability, strategic_value
    """
```

---

## 🔧 REFACTORING STRATEGY

### Phase 3A: VEE Abstraction (Priority 1)
**Objective**: Transform VEE into a domain-agnostic explanation engine

#### Step 1: Create Domain Contract Extensions
Create `vitruvyan_core/domains/explainability_contract.py`:
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class ExplanationTemplate:
    """Domain-specific narrative templates"""
    summary_template: str      # "Entity {entity_id} scores {score} due to..."
    technical_template: str    # "Factor breakdown: {factor1}: {value1}, ..."
    detailed_template: str     # Full mathematical explanation
    contextual_template: str   # Domain context and comparisons

@dataclass
class MetricDefinition:
    """What a metric means in domain terms"""
    name: str
    description: str
    unit: str
    interpretation: str  # "Higher is better" or "Lower indicates risk"
    normal_range: tuple  # (min, max) for domain

class ExplainabilityProvider(ABC):
    """Interface that domains implement to provide explanation context"""
    
    @abstractmethod
    def get_explanation_templates(self) -> ExplanationTemplate:
        """Return domain-specific narrative templates"""
        pass
    
    @abstractmethod
    def get_metric_definitions(self) -> Dict[str, MetricDefinition]:
        """Define what each metric means in this domain"""
        pass
    
    @abstractmethod
    def format_entity_reference(self, entity_id: str) -> str:
        """How to refer to entities in narratives (e.g., "AAPL entity" vs "Route NYC-LAX")"""
        pass
```

#### Step 2: Refactor VEE Engine
Modify `vee_engine.py`:
```python
from vitruvyan_core.domains.explainability_contract import ExplanationTemplate, ExplainabilityProvider

class VEEEngine:
    """Domain-Agnostic Explainability Engine"""
    
    def explain_entity(
        self,
        entity_id: str,
        metrics: Dict[str, Any],
        explainability_provider: ExplainabilityProvider,
        semantic_context: Optional[List[Dict]] = None
    ) -> ExplanationResult:
        """
        Generate multi-level explanations using domain-provided templates.
        
        Process:
        1. Extract metric values (domain-agnostic)
        2. Get metric definitions from domain
        3. Analyze patterns (domain-agnostic statistical analysis)
        4. Apply domain templates to generate narratives
        5. Return structured explanation result
        """
        
        # Step 1: Analyze metrics (domain-agnostic)
        analysis = self._analyze_metrics(metrics)
        
        # Step 2: Get domain context
        templates = explainability_provider.get_explanation_templates()
        metric_defs = explainability_provider.get_metric_definitions()
        
        # Step 3: Generate explanations using templates
        explanations = self._generate_from_templates(
            entity_id, analysis, templates, metric_defs
        )
        
        return ExplanationResult(
            entity_id=entity_id,
            summary=explanations["summary"],
            technical=explanations["technical"],
            detailed=explanations["detailed"],
            contextual=explanations["contextual"]
        )
```

#### Step 3: Remove Finance-Specific Code
Search and replace patterns:
- `entity_id` → `entity_id`
- `entity_data` → `entity_metrics`
- `analyze_ticker()` → `explain_entity()`
- Remove hardcoded "market", "entity", "collection" references
- Remove `yfinance` imports and financial API calls

#### Step 4: Update Sub-Modules
- `vee_analyzer.py`: Make pattern detection domain-agnostic
- `vee_generator.py`: Use templates instead of hardcoded financial narratives
- `vee_memory_adapter.py`: Store generic entity explanations

### Phase 3B: VARE Abstraction (Priority 2)
**Objective**: Transform VARE into a domain-agnostic risk assessment engine

#### Step 1: Create Risk Contract
Create `vitruvyan_core/domains/risk_contract.py`:
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

@dataclass
class RiskDimension:
    """A single dimension of risk assessment"""
    name: str
    description: str
    calculation_fn: Callable[[pd.DataFrame], float]  # Domain-specific calculation
    threshold_low: float      # Below this = low risk
    threshold_moderate: float # Below this = moderate risk
    threshold_high: float     # Below this = high risk
    # Above high = extreme risk

@dataclass
class RiskProfile:
    """How to combine risk dimensions"""
    name: str
    dimension_weights: Dict[str, float]  # {"dimension1": 0.3, "dimension2": 0.7}
    
class RiskProvider(ABC):
    """Interface that domains implement for risk assessment"""
    
    @abstractmethod
    def get_risk_dimensions(self) -> List[RiskDimension]:
        """Define what risk dimensions exist in this domain"""
        pass
    
    @abstractmethod
    def get_risk_profiles(self) -> Dict[str, RiskProfile]:
        """Predefined risk weighting schemes"""
        pass
```

#### Step 2: Refactor VARE Engine
Transform current finance-specific code:
```python
# BEFORE (finance-specific)
market_risk = self._calculate_market_risk(entity_data, benchmark_data)
volatility_risk = self._calculate_volatility_risk(entity_data)

# AFTER (domain-agnostic)
risk_scores = {}
for dimension in risk_provider.get_risk_dimensions():
    risk_scores[dimension.name] = dimension.calculation_fn(entity_metrics)
```

#### Step 3: Remove Financial Dependencies
- Remove `yfinance` imports
- Remove `SPY` benchmark hardcoding
- Remove `risk_free_rate` (domain-specific)
- Generalize data fetching to accept `pd.DataFrame` from vertical

### Phase 3C: VWRE Abstraction (Priority 3)
**Objective**: Make attribution analysis work with Neural Engine's abstract factors

#### Step 1: Decouple from Neural Engine Internals
```python
# BEFORE (tightly coupled)
from core.cognitive.neural_engine.engine_core import PROFILE_WEIGHTS, FACTOR_MAP

# AFTER (use Neural Engine's public API)
def analyze_attribution(
    self,
    entity_id: str,
    composite_score: float,
    factor_contributions: Dict[str, float],  # From Neural Engine result
    profile: AggregationProfile  # From Neural Engine
) -> AttributionResult:
    """
    Works with ANY factors - no hardcoded factor names.
    Uses AggregationProfile.get_weights() to determine contribution.
    """
```

#### Step 2: Remove Finance Terminology
- `entity_id` → `entity_id`
- `momentum_z`, `trend_z` → generic factor names from profile
- Remove financial narrative templates

---

## 📊 SUCCESS CRITERIA

### Minimum Viable Product (MVP)
- [ ] VEE Engine accepts `ExplainabilityProvider` from domain
- [ ] VEE generates explanations without knowing domain (finance, logistics, etc.)
- [ ] VARE Engine accepts `RiskProvider` from domain
- [ ] VARE calculates risk using domain-provided dimensions
- [ ] VWRE Engine works with abstract `AggregationProfile` (no hardcoded factors)
- [ ] All three engines have zero imports from `yfinance` or finance-specific modules
- [ ] Existing finance vertical can still work by implementing provider interfaces

### Testing Strategy
1. **Unit Tests**: Mock domain providers to test engines in isolation
2. **Example Domain**: Create a simple logistics example
3. **Finance Compatibility**: Verify old finance code still works via adapter

### Validation Commands
```bash
# Check for finance-specific terms
cd /home/caravaggio/projects/vitruvyan-core
rg -i "(entity_id|entity|market|collection|trading|yfinance)" \
  vitruvyan_core/core/cognitive/vitruvyan_proprietary/

# Should return 0 matches in core engines (allowed in adapters/examples)
```

---

## 🚫 WHAT NOT TO DO

### Don't Delete Working Code
- Keep original finance code in `vitruvyan-os` project (reference)
- Create abstractions, don't remove implementations
- Preserve backward compatibility via adapters if needed

### Don't Over-Engineer
- Start with simple domain contracts
- Add complexity only when needed
- 2-3 interfaces maximum (ExplainabilityProvider, RiskProvider)

### Don't Mix Concerns
- VEE = Explainability ONLY (not risk, not scoring)
- VARE = Risk assessment ONLY (not recommendations)
- VWRE = Attribution ONLY (not explanation narratives)

---

## 📁 FOLDER STRUCTURE (Target State)

```
vitruvyan_core/
├── domains/
│   ├── base_domain.py              # ✅ Already exists
│   ├── explainability_contract.py  # NEW: Templates & providers
│   ├── risk_contract.py            # NEW: Risk dimensions & providers
│   └── attribution_contract.py     # NEW: (optional, VWRE may not need)
│
├── core/cognitive/vitruvyan_proprietary/
│   ├── vee/
│   │   ├── vee_engine.py          # REFACTOR: domain-agnostic
│   │   ├── vee_analyzer.py        # REFACTOR: generic metric analysis
│   │   ├── vee_generator.py       # REFACTOR: template-based generation
│   │   └── vee_memory_adapter.py  # REFACTOR: entity-agnostic
│   │
│   ├── vare_engine.py             # REFACTOR: domain-agnostic risk
│   └── vwre_engine.py             # REFACTOR: factor-agnostic attribution
│
├── examples/
│   ├── finance_vee_example.py     # NEW: Finance domain adapter
│   └── logistics_vee_example.py   # NEW: Example for other domain
│
└── tests/
    ├── test_vee_abstraction.py    # NEW: Test with mock domains
    ├── test_vare_abstraction.py   # NEW: Test risk with mock
    └── test_vwre_abstraction.py   # NEW: Test attribution
```

---

## 🏁 IMPLEMENTATION PHASES

### Phase 3A (Days 1-2): VEE Abstraction
1. Create `explainability_contract.py` with interfaces
2. Refactor `vee_engine.py` to use domain providers
3. Update `vee_analyzer.py`, `vee_generator.py`, `vee_memory_adapter.py`
4. Remove finance-specific imports and terminology
5. Create example finance domain adapter
6. Write unit tests with mock domain

### Phase 3B (Day 3): VARE Abstraction
1. Create `risk_contract.py` with risk dimension interfaces
2. Refactor `vare_engine.py` to accept risk dimensions from domain
3. Remove `yfinance`, financial API calls
4. Generalize risk calculations to work with arbitrary dimensions
5. Create finance risk adapter example
6. Write unit tests

### Phase 3C (Day 4): VWRE Abstraction
1. Decouple VWRE from Neural Engine internal imports
2. Use `AggregationProfile` public API for weights
3. Remove hardcoded factor name mappings
4. Test with Neural Engine's abstract factors
5. Write unit tests

### Phase 3D (Day 5): Testing & Documentation
1. Integration tests: VEE + VARE + VWRE working together
2. Create logistics domain example (end-to-end)
3. Update documentation (PHILOSOPHY, CONTRACTS, PATTERNS)
4. Verify finance vertical still works via adapters
5. Commit and push to main

---

## 🔍 BEFORE YOU START

### Step 1: Read Current Implementation
Please read these files to understand current state:
1. `vitruvyan_core/core/cognitive/vitruvyan_proprietary/vee/vee_engine.py`
2. `vitruvyan_core/core/cognitive/vitruvyan_proprietary/vare_engine.py`
3. `vitruvyan_core/core/cognitive/vitruvyan_proprietary/vwre_engine.py`
4. `vitruvyan_core/domains/base_domain.py` (already abstracted)

### Step 2: Identify Finance Coupling
Search for:
- `entity_id`, `entity`, `market`, `collection`
- `yfinance`, financial API imports
- Hardcoded factor names (`momentum_z`, `trend_z`, etc.)
- Finance-specific narrative templates

### Step 3: Propose Refactoring Plan
**Before coding**, describe:
- Which contracts you'll create
- How domains will provide context
- What changes to make in each engine
- Estimated scope (lines changed)

### Step 4: Wait for Approval
Don't start implementing until you get confirmation with "procedi" or "ok"

---

## 💡 COMMUNICATION STYLE

- **Explain clearly**: I'm not a coder, use simple terms
- **Show before/after**: Visual diffs help understanding
- **One phase at a time**: Complete 3A before starting 3B
- **Commit often**: After each sub-phase (analyzer, generator, etc.)
- **Ask when uncertain**: Better to clarify than break things

---

## 📞 READY TO START?

Please begin by:
1. Reading the three engine files (VEE, VARE, VWRE)
2. Identifying all finance-specific code patterns
3. Proposing the contract interfaces you'll create
4. Outlining your refactoring approach for Phase 3A (VEE)

Then wait for my approval before implementing.

---

**Current Status**: Phase 1E Complete ✅ | Phase 3 Ready to Start 🚀  
**Target**: Domain-agnostic explainability, risk, and attribution engines  
**Timeline**: 5 days (3A: 2 days, 3B: 1 day, 3C: 1 day, 3D: 1 day)
