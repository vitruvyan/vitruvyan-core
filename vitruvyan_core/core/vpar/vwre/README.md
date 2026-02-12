# VWRE — Vitruvyan Weighted Reverse Engineering v2.0

**Domain-agnostic attribution analysis.**

VWRE decomposes composite scores into weighted factor contributions, answering:
*"Why did entity X score higher than entity Y?"*

Delegates domain-specific profile weights and factor mappings to an
`AggregationProvider` contract. Pure math — no Neural Engine imports, no raw DB.

## Architecture

```
LIVELLO 1 (this module)              LIVELLO 2 (adapter)
┌──────────────────────┐             ┌──────────────────────┐
│  types.py            │             │  LangGraph node or   │
│  · AttributionConfig │             │  service endpoint    │
│  · FactorAttribution │             │                      │
│  · AttributionResult │◄────────────│  Reads state,        │
│  · ComparisonResult  │  imports    │  calls engine,       │
│                      │             │  writes results      │
│  vwre_engine.py      │             └──────────────────────┘
│  · VWREEngine        │
│    .analyze()        │             ┌──────────────────────┐
│    .compare()        │             │  AggregationProvider │
│    .batch_analyze()  │◄────────────│  (domain contract)   │
│                      │  delegates  │  aggregation_        │
└──────────────────────┘             │  contract.py         │
                                     └──────────────────────┘
```

## Contract

`AggregationProvider` (from `vitruvyan_core/domains/aggregation_contract.py`):

| Method | Purpose |
|--------|---------|
| `get_aggregation_profiles()` | Define weighting profiles (name → factor_weights) |
| `get_factor_mappings()` | Map raw factor keys to weight keys |
| `calculate_contribution()` | Compute single factor contribution (default: z × weight) |
| `validate_factors()` | Validate and clean input factors |
| `format_attribution_explanation()` | Domain-specific explanation strings |

## Quick Start

```python
from core.vpar.vwre import VWREEngine, AttributionConfig

provider = MyDomainAggregationProvider()
engine = VWREEngine(provider, domain_tag="finance")

result = engine.analyze(
    entity_id="AAPL",
    composite_score=1.85,
    factors={
        "momentum_z": 2.1,
        "trend_z": 1.5,
        "volatility_z": -0.3,
        "sentiment_z": 0.8,
    },
    config=AttributionConfig(profile="short_spec"),
)

print(result.primary_driver)       # "momentum"
print(result.rank_explanation)     # "Score driven by momentum (39.7% weight, +0.735 contribution)"
print(result.verification_status)  # "verified"
```

## Contrastive Analysis

```python
result_a = engine.analyze("entity_A", 1.85, factors_a)
result_b = engine.analyze("entity_B", 0.95, factors_b)

comparison = engine.compare(result_a, result_b)
print(comparison.explanation)
# "entity_A scores higher than entity_B primarily due to superior momentum (+0.8)."
print(comparison.primary_difference)  # "momentum"
```

## Batch Analysis

```python
entries = [
    {"entity_id": "A", "composite_score": 1.85, "factors": {...}},
    {"entity_id": "B", "composite_score": 0.95, "factors": {...}},
]
results = engine.batch_analyze(entries, config)
```

## AttributionResult Fields

| Field | Type | Description |
|-------|------|-------------|
| `entity_id` | `str` | Entity identifier |
| `composite_score` | `float` | Original score being decomposed |
| `factors` | `Dict[str, FactorAttribution]` | Per-factor breakdown |
| `primary_driver` | `str` | Factor with highest contribution |
| `primary_contribution` | `float` | Contribution value of primary driver |
| `secondary_drivers` | `List[str]` | Supporting factors |
| `sum_contributions` | `float` | Sum of all contributions (should ≈ composite_score) |
| `residual` | `float` | composite_score - sum_contributions |
| `verification_status` | `str` | verified / warning / error |
| `rank_explanation` | `str` | One-line human-readable summary |
| `technical_summary` | `str` | Full mathematical breakdown |

## FactorAttribution Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Factor identifier |
| `z_score` | `float` | Raw input value |
| `weight` | `float` | Profile weight |
| `contribution` | `float` | z_score × weight |
| `percentage` | `float` | % of total contributions |
| `rank` | `str` | primary driver / secondary support / minor / negligible |
| `narrative` | `str` | "strong signal (z=2.10, weight=35.00%, contribution=+0.735)" |

## Domain Examples

### Finance
- Profiles: short_spec (momentum-heavy), balanced_mid, long_value
- Factors: momentum_z, trend_z, volatility_z, sentiment_z, fundamentals_z

### Healthcare
- Profiles: acute_care (symptoms-heavy), preventive (risk-factors-heavy)
- Factors: symptoms_score, lab_results, risk_factors, medication_response

### IoT / Manufacturing
- Profiles: real_time (sensor-heavy), predictive (history-heavy)
- Factors: sensor_anomaly_z, vibration_z, temperature_z, maintenance_z

## File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `types.py` | ~95 | Frozen dataclasses |
| `vwre_engine.py` | ~295 | VWREEngine: provider-driven attribution |
| `__init__.py` | ~30 | Package exports |
| `_legacy_vwre_engine.py` | 613 | Archived finance-coupled v1 (Neural Engine imports) |

## Invariants

1. **Zero hardcoded weights** — All weights come from provider profiles
2. **Mathematical verification** — Engine checks sum(contributions) ≈ composite_score
3. **Provider required** — No default provider; domain must implement `AggregationProvider`
4. **Frozen results** — All result types are immutable (`@dataclass(frozen=True)`)
5. **Graceful degradation** — Missing/null factors are skipped, not error
