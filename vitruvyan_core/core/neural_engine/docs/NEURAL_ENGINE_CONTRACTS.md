# Neural Engine Core - Contracts & Flow

## The Three Contracts

The Neural Engine Core defines three abstract interfaces. These are **contracts**, not implementations.

Your vertical implements these contracts to define domain-specific evaluation logic.

---

## 1. AbstractFactor

**Purpose**: Compute a single dimension of quality for entities.

```python
from abc import ABC, abstractmethod
import pandas as pd
from vitruvyan_core.core.cognitive.neural_engine import EvaluationContext

class AbstractFactor(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this factor."""
        ...
    
    @property
    def higher_is_better(self) -> bool:
        """Whether higher raw values indicate better performance."""
        return True
    
    @property
    def requires_stratification(self) -> bool:
        """Whether to normalize within groups (e.g., by industry)."""
        return False
    
    @property
    def stratification_field(self) -> Optional[str]:
        """Column name for stratification groups."""
        return None
    
    @abstractmethod
    def compute(
        self, 
        entities: pd.DataFrame, 
        context: EvaluationContext
    ) -> pd.Series:
        """
        Compute raw factor values.
        
        Args:
            entities: DataFrame with 'entity_id' column + domain data
            context: Evaluation parameters and options
        
        Returns:
            Series indexed by entity_id with raw values
        """
        ...
```

### Implementation Responsibilities

A factor implementation must:
- **Compute raw values** from entity data
- Return a pandas Series indexed by `entity_id`
- Handle missing data gracefully (NaN, empty values)
- Define directionality (higher/lower is better)
- Optionally specify stratification needs

A factor implementation must NOT:
- Normalize values (that's the normalizer's job)
- Apply weights (that's the profile's job)
- Query databases (data comes from caller)
- Generate explanations (just return numbers)

### Example (Finance Domain)

```python
class MomentumFactor(AbstractFactor):
    @property
    def name(self) -> str:
        return "momentum_12m"
    
    @property
    def higher_is_better(self) -> bool:
        return True
    
    def compute(self, entities: pd.DataFrame, context: EvaluationContext) -> pd.Series:
        # Assume entities has 'price_current' and 'price_12m_ago'
        momentum = (entities['price_current'] - entities['price_12m_ago']) / entities['price_12m_ago']
        return pd.Series(momentum.values, index=entities['entity_id'])
```

---

## 2. NormalizerStrategy

**Purpose**: Convert raw factor values to comparable scores.

```python
from abc import ABC, abstractmethod
import pandas as pd

class NormalizerStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this normalizer."""
        ...
    
    @abstractmethod
    def normalize(
        self,
        raw_values: pd.Series,
        higher_is_better: bool = True,
        stratification_groups: Optional[pd.Series] = None
    ) -> pd.Series:
        """
        Normalize raw values to comparable scores.
        
        Args:
            raw_values: Series of raw factor values
            higher_is_better: Whether to invert scores
            stratification_groups: Optional groups for within-group normalization
        
        Returns:
            Series of normalized values (same index)
        """
        ...
```

### Implementation Responsibilities

A normalizer implementation must:
- **Transform raw values** to a comparable scale
- Preserve the index from raw values
- Handle edge cases (zero variance, empty input)
- Support optional stratification (normalize within groups)
- Respect directionality (invert if `higher_is_better=False`)

A normalizer implementation must NOT:
- Know about factor semantics (momentum, volatility, etc.)
- Apply weights (that's the profile's job)
- Filter or cap values (that's pre-processing)

### Reference Implementation (ZScoreNormalizer)

The core includes **one** normalizer as a reference:

```python
class ZScoreNormalizer(NormalizerStrategy):
    """
    Z-score normalization: (x - mean) / std
    
    This is a REFERENCE IMPLEMENTATION.
    Your domain may require different strategies:
    - Industry-relative normalization
    - Quantile transformation
    - Domain-specific scaling
    """
    
    @property
    def name(self) -> str:
        return "zscore"
    
    def normalize(self, raw_values, higher_is_better=True, stratification_groups=None):
        # Global normalization
        mean = raw_values.mean()
        std = raw_values.std()
        
        if std == 0:
            return pd.Series(0.0, index=raw_values.index)
        
        z_scores = (raw_values - mean) / std
        
        if not higher_is_better:
            z_scores = -z_scores
        
        return z_scores
```

**Note**: This is ONE approach. You might need:
- Min-max scaling → See `vitruvyan_core.patterns.neural_engine.MinMaxNormalizer`
- Rank-based → See `vitruvyan_core.patterns.neural_engine.RankNormalizer`
- Custom domain logic → Implement your own

---

## 3. AggregationProfile

**Purpose**: Combine normalized factor scores into a composite score.

```python
from abc import ABC, abstractmethod
from typing import List, Dict
import pandas as pd

class AggregationProfile(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this profile."""
        ...
    
    @abstractmethod
    def get_weights(self, available_factors: List[str]) -> Dict[str, float]:
        """
        Return weights for available factors (must sum to 1.0).
        
        Args:
            available_factors: List of factor names that have values
        
        Returns:
            Dictionary mapping factor_name → weight
        """
        ...
    
    @abstractmethod
    def aggregate(self, factor_scores: Dict[str, pd.Series]) -> pd.Series:
        """
        Combine normalized factor scores into composite.
        
        Args:
            factor_scores: Dict of factor_name → normalized Series
        
        Returns:
            Series of composite scores (indexed by entity_id)
        """
        ...
```

### Implementation Responsibilities

A profile implementation must:
- **Define weights** for each factor
- Ensure weights sum to 1.0
- Handle missing factors gracefully (recalibrate weights)
- Combine scores into a single composite value

A profile implementation must NOT:
- Compute raw factor values (that's done already)
- Normalize scores (that's done already)
- Know about entity data (works with abstract scores)

### Example (Finance Domain)

```python
class BalancedProfile(AggregationProfile):
    @property
    def name(self) -> str:
        return "balanced"
    
    def get_weights(self, available_factors: List[str]) -> Dict[str, float]:
        # Define ideal weights
        ideal_weights = {
            "momentum_12m": 0.4,
            "trend_strength": 0.3,
            "volatility": 0.3,
        }
        
        # Recalibrate for available factors
        weights = {f: ideal_weights.get(f, 0.0) for f in available_factors}
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

## The Evaluation Flow

The orchestrator coordinates the three contracts:

```
EvaluationOrchestrator.evaluate()
│
├─ 1. COMPUTE (for each factor)
│   └─ factor.compute(entities, context) → raw_values
│
├─ 2. NORMALIZE (for each factor)
│   └─ normalizer.normalize(raw_values, ...) → normalized_scores
│
├─ 3. AGGREGATE
│   ├─ profile.get_weights(available_factors) → weights
│   └─ profile.aggregate(normalized_scores) → composite_scores
│
└─ 4. PACKAGE
    └─ Build EvaluationResult with scores, ranks, contributions
```

### Data Structures

**Input**: `EvaluationContext`
```python
@dataclass
class EvaluationContext:
    entity_ids: List[str]          # Entities to evaluate
    profile_name: str               # Which profile to use
    normalizer_name: str = "zscore" # Which normalizer to use
    mode: str = "evaluate"          # Mode (evaluate, rank, compare)
    options: Dict[str, Any] = {}    # Custom options for factors
    request_id: str = uuid4()       # Unique request ID
    timestamp: datetime = now()     # When requested
```

**Output**: `EvaluationResult`
```python
@dataclass
class EvaluationResult:
    context: EvaluationContext               # Original context
    evaluations: List[EntityEvaluation]      # Per-entity results
    factors_used: List[str]                  # Which factors computed
    normalizer_used: str                     # Which normalizer used
    profile_used: str                        # Which profile used
    entity_count: int                        # How many entities
    duration_ms: float                       # Execution time

@dataclass
class EntityEvaluation:
    entity_id: str                           # Entity identifier
    composite_score: float                   # Final aggregated score
    rank: int                                # Relative rank (1 = best)
    factor_contributions: List[FactorContribution]  # Breakdown

@dataclass
class FactorContribution:
    factor_name: str                         # Factor identifier
    raw_value: float                         # Raw computed value
    normalized_value: float                  # After normalization
    weight: float                            # From profile
    contribution: float                      # weight * normalized_value
```

---

## Usage Pattern

```python
from vitruvyan_core.core.cognitive.neural_engine import (
    EvaluationContext,
    EvaluationOrchestrator,
    ZScoreNormalizer
)
import pandas as pd

# 1. Prepare entity data
entities = pd.DataFrame({
    'entity_id': ['A', 'B', 'C'],
    # ... domain-specific columns
})

# 2. Instantiate your factors and profile
factors = [
    MyFactor1(),
    MyFactor2(),
]
profile = MyProfile()
normalizer = ZScoreNormalizer()

# 3. Create evaluation context
context = EvaluationContext(
    entity_ids=['A', 'B', 'C'],
    profile_name="my_profile"
)

# 4. Execute evaluation
orchestrator = EvaluationOrchestrator()
result = orchestrator.evaluate(
    entities=entities,
    context=context,
    factors=factors,
    normalizer=normalizer,
    profile=profile
)

# 5. Access results
for eval in result.evaluations:
    print(f"{eval.entity_id}: {eval.composite_score:.2f} (rank {eval.rank})")
    
    for contrib in eval.factor_contributions:
        print(f"  {contrib.factor_name}: {contrib.contribution:.3f}")
```

---

## Key Principles

1. **Separation of Concerns**
   - Factors compute
   - Normalizers transform
   - Profiles aggregate
   - Orchestrator coordinates

2. **Data Flow is Unidirectional**
   - Caller provides entity data
   - Factors produce raw values
   - Normalizer produces comparable scores
   - Profile produces composite
   - Result is returned (not persisted)

3. **No Side Effects**
   - No database writes
   - No file I/O
   - No global state
   - Pure function evaluation

4. **Domain Agnosticism**
   - Core never mentions: entity, patient, route, etc.
   - Only generic: entity, factor, score, weight

---

## What Comes Next

Now that you understand the contracts and flow:

1. **Define your domain's factors** (What matters?)
2. **Define your aggregation profile** (How to combine?)
3. **Choose or implement normalizer** (How to compare?)
4. **Implement and test** with your data

The core provides structure.  
Your vertical provides meaning.

See also:
- [NEURAL_ENGINE_PHILOSOPHY.md](NEURAL_ENGINE_PHILOSOPHY.md) - Why substrate, not framework
- [NEURAL_ENGINE_PATTERNS.md](NEURAL_ENGINE_PATTERNS.md) - Optional utilities
