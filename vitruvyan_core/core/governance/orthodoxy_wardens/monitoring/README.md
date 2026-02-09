# monitoring/

> Prometheus metric name constants and label definitions.

## Contents

| File | Description |
|------|-------------|
| `metrics.py` | Metric name constants + label value tuples |

## Architecture

This package defines metric **names** and **labels** only.
The service layer instantiates actual Prometheus counters/histograms.

```
Foundational (this package)        Service layer
─────────────────────────          ─────────────────────
VERDICTS_TOTAL = "..."      →     Counter(VERDICTS_TOTAL, ...)
SEVERITY_LABELS = (...)     →     labels=SEVERITY_LABELS
```

## Naming Convention

Follows Prometheus best practices:
```
<sacred_order>_<domain>_<metric>_<unit>
```

Examples:
- `orthodoxy_confessions_received_total`
- `orthodoxy_verdicts_by_status_total`
- `orthodoxy_examinations_duration_seconds`

## Constraints

- **Definitions only** — no `prometheus_client` import
- No collection, no exposure — that's service layer responsibility
- Labels use tuples (frozen, hashable)
