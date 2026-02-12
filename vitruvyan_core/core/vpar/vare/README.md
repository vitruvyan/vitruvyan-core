# VARE — Vitruvyan Adaptive Risk Engine v2.0

**Domain-agnostic multi-dimensional risk profiling.**

VARE computes composite risk scores by evaluating multiple risk dimensions
defined by a domain-specific `RiskProvider`. No data fetching logic, no
finance assumptions — pure computation driven by provider contracts.

## Architecture

```
LIVELLO 1 (this module)              LIVELLO 2 (adapter)
┌──────────────────────┐             ┌──────────────────────┐
│  types.py            │             │  LangGraph node or   │
│  · RiskConfig        │             │  service endpoint    │
│  · RiskDimensionScore│             │                      │
│  · RiskResult        │◄────────────│  Reads state,        │
│                      │  imports    │  calls engine,       │
│  vare_engine.py      │             │  writes results      │
│  · VAREEngine        │             └──────────────────────┘
│    .assess_risk()    │
│    .batch_assess()   │             ┌──────────────────────┐
│    .adjust()         │             │  RiskProvider        │
│                      │◄────────────│  (domain contract)   │
└──────────────────────┘  delegates  │  risk_contract.py    │
                                     └──────────────────────┘
```

## Contract

`RiskProvider` (from `vitruvyan_core/domains/risk_contract.py`):

| Method | Purpose |
|--------|---------|
| `get_risk_dimensions()` | Define risk dimensions with calculation functions |
| `get_risk_profiles()` | Define weighting schemes (conservative, aggressive, …) |
| `prepare_entity_data()` | Convert raw data to DataFrame for dimension calculations |
| `get_risk_thresholds()` | Domain-specific LOW/MODERATE/HIGH/EXTREME thresholds |
| `format_risk_explanation()` | Generate domain-specific explanation strings |

## Quick Start

```python
from core.vpar.vare import VAREEngine, RiskConfig

# Any domain provider implementing RiskProvider
provider = MyDomainRiskProvider()
engine = VAREEngine(provider, domain_tag="energy")

result = engine.assess_risk(
    entity_id="turbine_42",
    raw_data={"readings": [...], "maintenance_log": [...]},
    config=RiskConfig(profile="conservative"),
)

print(result.risk_category)      # "HIGH"
print(result.overall_risk)       # 72.3
print(result.primary_risk_factor)  # "outage_risk"
print(result.explanation["summary"])
```

## Batch Assessment

```python
entities = [
    {"entity_id": "turbine_42", "raw_data": {...}},
    {"entity_id": "turbine_43", "raw_data": {...}},
]
results = engine.batch_assess(entities, config)
```

## RiskResult Fields

| Field | Type | Description |
|-------|------|-------------|
| `entity_id` | `str` | Entity identifier |
| `dimension_scores` | `Dict[str, RiskDimensionScore]` | Per-dimension breakdown |
| `overall_risk` | `float` | 0-100 weighted composite |
| `risk_category` | `str` | LOW / MODERATE / HIGH / EXTREME |
| `primary_risk_factor` | `str` | Dimension with highest score |
| `explanation` | `Dict[str, str]` | summary, technical, detailed |
| `confidence` | `float` | 0.0-1.0 assessment confidence |
| `profile` | `str` | Risk profile used |
| `domain_tag` | `Optional[str]` | Safety marker |

## EPOCH V Adaptation

```python
engine.adjust("MODERATE", delta=-5.0)  # Lower moderate threshold
print(engine.adaptation_history)
```

Adaptation records are in-memory; persistent storage is handled by the
LIVELLO 2 adapter (via `PostgresAgent`).

## Domain Examples

### Finance
- Dimensions: market_risk, volatility_risk, liquidity_risk, correlation_risk
- Profiles: conservative, balanced, aggressive

### Healthcare
- Dimensions: readmission_risk, complication_risk, mortality_risk
- Profiles: acute_care, preventive, chronic

### Logistics
- Dimensions: delay_risk, cost_overrun_risk, reliability_risk
- Profiles: express, standard, economy

## File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `types.py` | ~80 | Frozen dataclasses (RiskConfig, RiskDimensionScore, RiskResult) |
| `vare_engine.py` | ~240 | VAREEngine: provider-driven risk assessment |
| `__init__.py` | ~25 | Package exports |
| `_legacy_vare_engine.py` | 753 | Archived finance-coupled v1 (yfinance + psycopg2) |

## Invariants

1. **Zero data fetching** — Engine never calls yfinance, APIs, or databases
2. **Provider required** — No default provider; each domain must implement `RiskProvider`
3. **Score range 0-100** — All dimension scores and overall_risk normalized to [0, 100]
4. **Frozen results** — `RiskResult` is immutable (`@dataclass(frozen=True)`)
5. **Graceful degradation** — Failed dimensions default to 50 (neutral), confidence drops
