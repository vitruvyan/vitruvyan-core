# Finance Neural Engine Domain Pack

Last updated: 2026-02-23

## Scope

Finance implementation package for `api_neural_engine`, loaded when
`DOMAIN=finance`.

## Components

| Component | Contract | Role |
|---|---|---|
| `TickerDataProvider` | `IDataProvider` | Loads finance universe/features from PostgreSQL |
| `FinancialScoringStrategy` | `IScoringStrategy` | Applies finance profile weights and risk adjustment |

## Data Sources (TickerDataProvider)

Primary tables used:
- `tickers`
- `momentum_logs`
- `trend_logs`
- `volatility_logs`
- `sentiment_scores`
- `fundamentals`
- `factor_scores`
- `vare_risk_analysis`
- `macro_outlook`

Feature notes:
- `debt_to_equity_inv` is computed as negative debt-to-equity.
- `academic_momentum` is sourced from factor scores.
- VARE metrics are exposed for risk-aware scoring.

## Profiles (FinancialScoringStrategy)

Canonical profiles:
- `short_spec`
- `balanced_mid`
- `trend_follow`
- `momentum_focus`
- `sentiment_boost`
- `low_risk`

Compatibility aliases:
- `balanced -> balanced_mid`
- `aggressive -> momentum_focus`
- `conservative -> low_risk`

Risk adjustment:
- Preferred path: VARE-based penalty from `vare_risk_score`.
- Fallback path: volatility z-score penalty when VARE data is missing.

## Activation

- `DOMAIN=finance`
- DB env vars: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`,
  `POSTGRES_USER`, `POSTGRES_PASSWORD`
- Optional engine tuning:
  - `NE_STRATIFICATION_MODE=global|stratified|composite`
  - `NE_CACHE_TTL_SECONDS=<seconds>`

## Contract Boundary

- Core engine remains in `vitruvyan_core/core/neural_engine`.
- This package contains only finance domain logic mapped to contracts.

## Tests

```bash
pytest -q vitruvyan_core/domains/finance/neural_engine/tests
```
