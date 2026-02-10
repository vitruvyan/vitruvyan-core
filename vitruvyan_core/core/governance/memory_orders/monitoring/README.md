# monitoring/

> **Metric name constants. NO collection logic.**

## Constraints

- Define metric NAMES only, not collectors
- NO `prometheus_client` imports
- NO `Gauge()` / `Counter()` / `Histogram()` instantiation
- Service layer (LIVELLO 2) handles Prometheus integration

---

## Contents

| File | Description |
|------|-------------|
| `metrics.py` | Metric name constants for Memory Orders |

---

## Usage Pattern (Service Layer)

```python
from vitruvyan_core.core.governance.memory_orders.monitoring import (
    COHERENCE_DRIFT_PCT,
    HEALTH_STATUS,
)
from prometheus_client import Gauge

# Service layer creates collectors
coherence_gauge = Gauge(COHERENCE_DRIFT_PCT, "Drift percentage between PostgreSQL and Qdrant")
health_gauge = Gauge(HEALTH_STATUS, "Overall RAG system health status (0=unhealthy, 1=healthy)")

# Update metrics
coherence_gauge.set(report.drift_percentage)
health_gauge.set(1 if health.overall_status == "healthy" else 0)
```

---

**Sacred Order**: Memory & Coherence  
**Layer**: Foundational (LIVELLO 1 — monitoring)
