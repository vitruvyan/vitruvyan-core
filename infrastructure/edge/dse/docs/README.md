# DSE — Design Space Exploration Engine

> **Last updated**: Feb 26, 2026 15:00 UTC

**Sacred Order**: REASON (Computation)  
**Layer**: LIVELLO 1 — Pure Domain (`infrastructure/edge/dse/`)  
**Service**: LIVELLO 2 — `services/api_edge_dse/`

---

## Overview

The DSE engine explores multi-dimensional parameter spaces for configuration
optimization. Given a context from Pattern Weavers, it:

1. **Samples** design points (LHS / Cartesian / Sobol)
2. **Scores** each point against KPI normalization profiles
3. **Computes** the Pareto frontier (multi-objective non-dominated set)
4. **Ranks** points via doctrine-weighted composite score (dottrinale ranking)
5. **Returns** a reproducible, audit-ready `RunArtifact`

---

## Directory Structure (LIVELLO 1)

```
infrastructure/edge/dse/
├── domain/          # Frozen dataclass schemas (DesignPoint, RunArtifact, ...)
├── consumers/       # Pure compute functions (sampling, pareto, engine)
├── governance/      # SamplingStrategySelector (heuristic + ML-injected)
├── events/          # DSEChannels — Redis stream channel constants
├── monitoring/      # DSEMetrics — Prometheus metric name constants
├── philosophy/      # charter.md
├── docs/            # Architecture, design decisions
├── examples/        # Standalone pure-Python usage examples
├── tests/           # Unit tests (pytest, no Docker)
└── _legacy/         # Archive of aegis-era implementation
```

---

## Quick Start (Pure Python, No Services)

```python
from infrastructure.edge.dse.domain import DesignPoint, NormalizationProfile
from infrastructure.edge.dse.domain import PolicySet, RunContext, KPIConfig
from infrastructure.edge.dse.domain import OptimizationDirection
from infrastructure.edge.dse.consumers import run_dse
from infrastructure.edge.dse.consumers import latin_hypercube_sampling

# 1. Build exploration space from Pattern Weavers context
context = {
    "sector": ["Banking", "Tech", "Healthcare"],
    "region": ["EU", "US", "APAC"],
    "risk_level": ["low", "medium", "high"],
}

raw_points = latin_hypercube_sampling(context, num_samples=50, seed=42)

design_points = [
    DesignPoint(
        design_id=i,
        knobs={
            "compliance_threshold": 0.5 + i * 0.01,
            "audit_frequency_days": 30 + (i % 5) * 15,
            "risk_tolerance": 0.2 + (i % 4) * 0.2,
        },
        tags={"sector": p["sector"], "region": p["region"]},
    )
    for i, p in enumerate(raw_points)
]

# 2. Define normalization profile
profile = NormalizationProfile(
    profile_name="default",
    kpi_configs=[
        KPIConfig("compliance_score", 0.0, 1.0, OptimizationDirection.MAXIMIZE),
        KPIConfig("cost_efficiency",  0.0, 1.0, OptimizationDirection.MAXIMIZE),
    ],
)

# 3. Define policy
policy = PolicySet(
    policy_name="default_policy",
    optimization_objective="maximize_compliance",
    doctrine_weights={"compliance_score": 0.7, "cost_efficiency": 0.3},
)

# 4. Run DSE
ctx = RunContext(user_id="u1", trace_id="t1", use_case="demo")
artifact = run_dse(design_points, policy, profile, ctx, seed=42)

print(f"Pareto: {artifact.pareto_count}/{artifact.total_design_points}")
print(f"Top rank: {artifact.ranking_dottrinale[0]['dottrinale_score']:.4f}")
```

---

## Architecture (Two-Level Pattern)

| Level | Location | Role |
|-------|----------|------|
| **LIVELLO 1** | `infrastructure/edge/dse/` | Pure domain logic — zero I/O |
| **LIVELLO 2** | `services/api_edge_dse/` | FastAPI + StreamBus + PostgresAgent |

### Import Rules
- LIVELLO 1 uses **relative imports only**: `from .consumers.engine import run_dse`
- LIVELLO 2 imports LIVELLO 1: `from infrastructure.edge.dse.consumers import run_dse`
- No cross-service imports; communicate via StreamBus events

---

## Event Flow

```
Pattern Weavers → [dse.sampling.completed] → Conclave (governance gate)
    ↓ [conclave.governance.approved]
DSE run_dse() → [dse.run.completed] → [vault.archive.requested]
```

---

## Configuration (LIVELLO 2 env vars)

| Variable | Default | Description |
|----------|---------|-------------|
| `DSE_API_PORT` | `8021` | Service HTTP port |
| `DSE_DEFAULT_SEED` | `42` | Default reproducibility seed |
| `DSE_DEFAULT_NUM_SAMPLES` | `50` | LHS default sample count |
| `REDIS_HOST` | `core_redis` | Redis Streams host |
| `REDIS_PORT` | `6379` | Redis Streams port |
| `POSTGRES_*` | — | PostgresAgent connection vars |

---

## Testing

```bash
# Unit tests (pure — no Docker)
cd /home/caravaggio/vitruvyan-core
pytest infrastructure/edge/dse/tests/ -v

# Service tests (requires Docker stack)
pytest services/api_edge_dse/ -v
```
