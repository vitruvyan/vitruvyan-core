# Phase 3D: Neural Engine Integration Pattern
## Canonical Approach for Vertical Orchestration

**Date:** December 30, 2025  
**Purpose:** Establish the canonical pattern for integrating Neural Engine with VEE/VARE/VWRE in vertical implementations  

---

## 🎯 Integration Doctrine

### Core Principles

1. **Boundary Preservation:** Neural Engine remains pure computational substrate. No explainability, no business logic, no domain semantics.

2. **Vertical Responsibility:** Integration orchestration happens at vertical level, not core level. Core provides the tools; verticals build the workflows.

3. **Provider Essentiality:** VEE/VARE/VWRE require their respective providers for incarnation. No "optional" providers - they are essential for domain-specific operation.

4. **Data Flow Direction:** Always NE → VWRE → VARE → VEE. Neural Engine feeds quantitative results to attribution, which feeds to risk, which feeds to explainability.

### Architectural Boundaries

```
NEURAL ENGINE (Phase 1E)
├── Pure quantitative evaluation
├── Domain-agnostic scoring
├── No business logic
└── No explainability

CORE ENGINES (Phase 3)
├── VEE: Explainability (requires ExplainabilityProvider)
├── VARE: Risk Assessment (requires RiskProvider)
├── VWRE: Attribution (requires AggregationProvider)
└── All accept domain incarnation via providers

VERTICAL LAYER (Phase 3D/4)
├── Domain-specific orchestration
├── Business logic implementation
├── Provider implementations
└── End-to-end pipeline coordination
```

---

## 🔧 Integration Pattern

### Step 1: Vertical Incarnation Setup

```python
from vitruvyan_core.domains import (
    AbstractFactor, AggregationProvider, RiskProvider, ExplainabilityProvider
)
from vitruvyan_core.core.cognitive.vitruvyan_proprietary import (
    NeuralEngine, VWREngine, VAREngine, VEEEngine
)

# 1. Define domain factors (Neural Engine incarnation)
class FinanceFactor(AbstractFactor):
    """Domain-specific factor implementation"""
    def evaluate(self, entity_data: Dict[str, Any]) -> float:
        # Domain logic here
        pass

# 2. Implement required providers
class FinanceAggregationProvider(AggregationProvider):
    """Finance-specific attribution logic"""
    def get_aggregation_profile(self, entity_id: str) -> AggregationProfile:
        # Return appropriate weighting scheme
        pass

class FinanceRiskProvider(RiskProvider):
    """Finance-specific risk assessment"""
    def assess_risk(self, attribution_result: VWREResult) -> VAREResult:
        # Risk logic based on attribution
        pass

class FinanceExplainabilityProvider(ExplainabilityProvider):
    """Finance-specific explanations"""
    def explain(self, risk_result: VAREResult) -> VEEResult:
        # Generate human-understandable explanations
        pass
```

### Step 2: Pipeline Orchestration

```python
class VerticalOrchestrator:
    """Domain-specific pipeline coordinator"""

    def __init__(self):
        # Initialize Neural Engine with domain factors
        self.neural_engine = NeuralEngine(
            factors=[FinanceFactor(), ...],
            normalizers=[ZScoreNormalizer(), ...]
        )

        # Initialize core engines with domain providers
        self.vwre = VWREngine(aggregation_provider=FinanceAggregationProvider())
        self.vare = VAREngine(risk_provider=FinanceRiskProvider())
        self.vee = VEEEngine(explainability_provider=FinanceExplainabilityProvider())

    def process_entity(self, entity_id: str, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete cognitive pipeline: NE → VWRE → VARE → VEE

        Args:
            entity_id: Entity identifier
            entity_data: Raw entity data

        Returns:
            Complete analysis results
        """

        # Step 1: Neural Engine evaluation (pure quantitative)
        ne_result = self.neural_engine.evaluate_entity(entity_id, entity_data)

        # Step 2: VWRE attribution analysis
        vwre_result = self.vwre.analyze_attribution(
            entity_id=entity_id,
            neural_scores=ne_result.scores,
            factor_contributions=ne_result.factor_contributions
        )

        # Step 3: VARE risk assessment
        vare_result = self.vare.assess_risk(
            entity_id=entity_id,
            attribution_result=vwre_result
        )

        # Step 4: VEE explainability
        vee_result = self.vee.generate_explanation(
            entity_id=entity_id,
            risk_result=vare_result
        )

        # Return complete analysis
        return {
            'entity_id': entity_id,
            'neural_evaluation': ne_result,
            'attribution_analysis': vwre_result,
            'risk_assessment': vare_result,
            'explanation': vee_result,
            'timestamp': datetime.now().isoformat()
        }
```

### Step 3: Usage in Vertical Implementation

```python
# Example: Finance Vertical (Mercator)
class MercatorVertical:
    """Finance domain vertical implementation"""

    def __init__(self):
        self.orchestrator = VerticalOrchestrator()

    def analyze_portfolio(self, portfolio_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze entire portfolio using cognitive stack"""
        results = []

        for position in portfolio_data:
            entity_id = position['ticker']  # or position['entity_id']
            analysis = self.orchestrator.process_entity(entity_id, position)
            results.append(analysis)

        return results

    def get_risk_exposure_report(self, portfolio_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate domain-specific risk report"""
        # Business logic for aggregating portfolio-level insights
        pass
```

---

## 📊 Data Flow Specification

### Input Requirements

**Neural Engine Input:**
- `entity_id`: String identifier
- `entity_data`: Dict containing factor-relevant data
- Domain factors must be pre-configured

**Core Engine Inputs:**
- All engines require their respective providers at initialization
- VWRE needs NE scores and factor contributions
- VARE needs VWRE attribution results
- VEE needs VARE risk results

### Output Structure

```python
{
    "entity_id": "AAPL",
    "neural_evaluation": {
        "scores": {"overall": 0.85, "factors": {...}},
        "factor_contributions": {...},
        "confidence": 0.92
    },
    "attribution_analysis": {
        "entity_id": "AAPL",
        "factor_weights": {...},
        "attribution_breakdown": {...},
        "aggregation_profile": "balanced_mid"
    },
    "risk_assessment": {
        "entity_id": "AAPL",
        "risk_profile": {...},
        "exposure_metrics": {...},
        "recommendations": [...]
    },
    "explanation": {
        "entity_id": "AAPL",
        "narrative": "Clear, actionable explanation...",
        "key_factors": [...],
        "confidence_intervals": {...}
    },
    "timestamp": "2025-12-30T10:30:00Z"
}
```

---

## ⚠️ Boundary Enforcement

### What Neural Engine CANNOT Do
- ❌ Generate explanations
- ❌ Make business decisions
- ❌ Implement domain logic
- ❌ Call VEE/VARE/VWRE directly

### What Core Engines Require
- ✅ VEE needs ExplainabilityProvider (always)
- ✅ VARE needs RiskProvider (always)
- ✅ VWRE needs AggregationProvider (always)
- ✅ All providers are domain-specific implementations

### What Verticals MUST Do
- ✅ Provide domain incarnation (factors + providers)
- ✅ Orchestrate the pipeline sequence
- ✅ Handle business logic and domain semantics
- ✅ Aggregate results for domain-specific insights

---

## 🧪 Testing Pattern

```python
def test_vertical_integration():
    """Test complete pipeline integration"""

    # Setup
    orchestrator = VerticalOrchestrator()
    test_entity = {"ticker": "AAPL", "price": 150.0, "volume": 1000000}

    # Execute pipeline
    result = orchestrator.process_entity("AAPL", test_entity)

    # Verify all components executed
    assert 'neural_evaluation' in result
    assert 'attribution_analysis' in result
    assert 'risk_assessment' in result
    assert 'explanation' in result

    # Verify data flow
    assert result['attribution_analysis']['entity_id'] == "AAPL"
    assert result['risk_assessment']['entity_id'] == "AAPL"
    assert result['explanation']['entity_id'] == "AAPL"
```

---

## 🚀 Implementation Guidelines

### For New Verticals
1. Implement domain factors extending `AbstractFactor`
2. Create provider implementations for Aggregation, Risk, Explainability
3. Build vertical orchestrator following the pattern above
4. Add domain-specific business logic and reporting
5. Test complete pipeline integration

### Performance Considerations
- Neural Engine evaluation is typically fastest
- VWRE attribution analysis is moderate
- VARE risk assessment varies by complexity
- VEE explanation generation can be most expensive
- Consider caching for repeated entity evaluations

### Error Handling
- Neural Engine failures should not prevent other analyses
- Provider failures should be handled gracefully
- Maintain pipeline integrity even with partial failures
- Log all errors with sufficient context for debugging

---

## 📚 Related Documentation

- `ARCHITECTURAL_SYNTHESIS_RESPONSE.md` - Core doctrine
- `NEURAL_ENGINE_ARCHITECTURAL_ANALYSIS.md` - NE boundaries
- `PHASE3_COMPLETE_REPORT.md` - Core engine contracts
- `examples/vertical_integration/` - Working examples

---

**Status:** Canonical integration pattern established. Ready for vertical implementation.