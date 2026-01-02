# Neural Engine - Optional Patterns

**⚠️ IMPORTANT**: These are OPTIONAL utilities, not core identity.

The Neural Engine Core provides only:
- Contracts (AbstractFactor, NormalizerStrategy, AggregationProfile)  
- Orchestration (EvaluationOrchestrator)
- Data structures (EvaluationContext, EvaluationResult)
- One reference normalizer (ZScoreNormalizer)

Everything in this document lives in `vitruvyan_core.patterns.neural_engine` and represents **one possible approach**, not a required pattern.

Use these if helpful. Ignore if not. Implement your own if needed.

---

## Import Optional Patterns

```python
# Core substrate (always needed)
from vitruvyan_core.core.cognitive.neural_engine import (
    # Abstract Interfaces
    AbstractFactor,
    NormalizerStrategy,
    AggregationProfile,
    
    # Data Structures
    EvaluationContext,
    EvaluationResult,
    EntityEvaluation,
    FactorContribution,
    
    # Orchestrator
    EvaluationOrchestrator,
    
    # Reference normalizer
    ZScoreNormalizer,
)

# Optional patterns (use if helpful)
from vitruvyan_core.patterns.neural_engine import (
    # Registry pattern (optional organization)
    FactorRegistry,
    ProfileRegistry,
    NormalizerRegistry,
    
    # Additional normalizers (optional alternatives)
    MinMaxNormalizer,
    RankNormalizer,
    
    # Math utilities (optional helpers)
    winsorize,
    time_decay,
    safe_divide,
)
```

---

## 1. Implement a Factor

```python
class MyFactor(AbstractFactor):
    @property
    def name(self) -> str:
        return "my_factor_name"
    
    @property
    def higher_is_better(self) -> bool:
        return True  # or False if lower is better
    
    def compute(self, entities: pd.DataFrame, context: EvaluationContext) -> pd.Series:
        # Your domain logic here
        # entities has at least 'entity_id' column
        # Return pd.Series indexed by entity_id
        return pd.Series({"entity1": 10.0, "entity2": 20.0})
```

### Optional: Stratified Normalization

```python
@property
def requires_stratification(self) -> bool:
    return True

@property
def stratification_field(self) -> Optional[str]:
    return "group_column"  # column name in entities DataFrame
```

---

## 2. Implement an Aggregation Profile

```python
class MyProfile(AggregationProfile):
    @property
    def name(self) -> str:
        return "my_profile_name"
    
    def get_weights(self, available_factors: List[str]) -> Dict[str, float]:
        # Define weights (must sum to 1.0)
        weights = {
            "factor1": 0.6,
            "factor2": 0.4,
        }
        
        # Filter and recalibrate for available factors
        weights = {f: weights.get(f, 0.0) for f in available_factors}
        total = sum(weights.values())
        if total > 0:
            weights = {f: w/total for f, w in weights.items()}
        return weights
    
    def aggregate(self, factor_scores: Dict[str, pd.Series]) -> pd.Series:
        weights = self.get_weights(list(factor_scores.keys()))
        
        composite = None
        for factor_name, scores in factor_scores.items():
            weight = weights[factor_name]
            if composite is None:
                composite = scores * weight
            else:
                composite = composite + (scores * weight)
        
        return composite
```

---

## 3. Evaluate Entities

```python
# Prepare data
entities = pd.DataFrame({
    'entity_id': ['A', 'B', 'C'],
    # ... other columns your factors need
})

# Setup context
context = EvaluationContext(
    entity_ids=['A', 'B', 'C'],
    profile_name="my_profile",
    normalizer_name="zscore",
    mode="evaluate",
    options={}  # optional parameters
)

# Execute evaluation
orchestrator = EvaluationOrchestrator()
result = orchestrator.evaluate(
    entities=entities,
    context=context,
    factors=[MyFactor()],
    normalizer=ZScoreNormalizer(),
    profile=MyProfile()
)

# Access results
for eval in result.evaluations:
    print(f"{eval.entity_id}: score={eval.composite_score}, rank={eval.rank}")
    
    for contrib in eval.factor_contributions:
        print(f"  {contrib.factor_name}: {contrib.contribution}")
```

---

## Pattern 1: Registry (Optional Organization Mechanism)

The registry pattern provides a centralized place to register and retrieve factors, profiles, and normalizers by name.

**This is ONE way to organize components. You might prefer:**
- Direct instantiation
- Dependency injection
- Factory pattern
- Configuration-driven loading

### Usage

```python
from vitruvyan_core.patterns.neural_engine import (
    FactorRegistry,
    ProfileRegistry,
    NormalizerRegistry
)

# Register factors
factor_registry = FactorRegistry()
factor_registry.register(MyFactor())

# Register profiles
profile_registry = ProfileRegistry()
profile_registry.register(MyProfile())

# Register normalizers  
normalizer_registry = NormalizerRegistry()
normalizer_registry.register(ZScoreNormalizer())

# Retrieve by name
my_factor = factor_registry.get("my_factor_name")
my_profile = profile_registry.get("my_profile_name")
normalizer = normalizer_registry.get("zscore")
```

**Note**: This is helpful for name-based lookup but adds indirection. Consider whether you need it.

---

## Pattern 2: Additional Normalizers (Optional Alternatives)

The core includes **only ZScoreNormalizer** as a reference.

The patterns library provides two additional implementations:

### MinMaxNormalizer
- Scales to [0, 1] range
- Use when: bounded data with known min/max
- Import: `from vitruvyan_core.patterns.neural_engine import MinMaxNormalizer`

### RankNormalizer
- Converts to percentile ranks
- Use when: ordinal data or robust to outliers
- Import: `from vitruvyan_core.patterns.neural_engine import RankNormalizer`

**These are examples, not recommendations.** Your domain may need completely different strategies.

---

## Pattern 3: Math Utilities (Optional Helpers)

Some common mathematical operations are provided as utilities:

```python
from vitruvyan_core.patterns.neural_engine import (
    winsorize,
    time_decay,
    safe_divide
)

# Clip outliers
series = winsorize(raw_series, lower=0.01, upper=0.99)

# Apply exponential decay
decayed = time_decay(values, timestamps, half_life_days=30)

# Safe division with fallback
ratio = safe_divide(numerator, denominator, default=0.0)
```

**These are conveniences, not requirements.** Implement your own if these don't fit.

---

## See Also

- [NEURAL_ENGINE_PHILOSOPHY.md](NEURAL_ENGINE_PHILOSOPHY.md) - Why substrate, not framework
- [NEURAL_ENGINE_CONTRACTS.md](NEURAL_ENGINE_CONTRACTS.md) - Core interfaces and flow
- [examples/neural_engine_usage.py](examples/neural_engine_usage.py) - Complete example
- [tests/test_neural_engine_core.py](tests/test_neural_engine_core.py) - Unit tests
