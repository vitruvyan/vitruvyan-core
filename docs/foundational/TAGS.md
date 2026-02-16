# 🏷️ Tags

Use tags to quickly filter content by topic and audience.

## Suggested taxonomy

- `overview` — high-level concept pages
- `getting-started` — onboarding and first steps
- `installation` — setup and deployment docs
- `architecture` — design, topology, system patterns
- `system-core` — orchestration, bus, agents, neural engine
- `sacred-orders` — governance orders and responsibilities
- `memory` — dual-memory layer, coherence, reconciliation
- `api` — service endpoints and contracts
- `governance` — audit, policy, epistemic controls
- `operations` — runbooks, monitoring, production concerns
- `admin` — internal/admin-only depth
- `public` — public-facing docs

## Tag index (initial set)

### `overview`
- [Vitruvyan Overview](VITRUVYAN_OVERVIEW.md)
- [Architecture Index](../architecture/README.md)
- [Sacred Orders Introduction](SACRED_ORDERS_INTRO.md)

### `getting-started`
- [Quick Start](QUICK_START.md)

### `architecture`
- [Architecture Index](../architecture/README.md)
- [Dual Memory Layer](../architecture/DUAL_MEMORY_LAYER.md)
- [Vitruvyan Overview](VITRUVYAN_OVERVIEW.md)

### `memory`
- [Dual Memory Layer](../architecture/DUAL_MEMORY_LAYER.md)
- [Memory Orders (Admin)](../internal/orders/MEMORY_ORDERS.md)
- [Memory Orders API (Admin)](../internal/services/MEMORY_ORDERS_API.md)

### `sacred-orders`
- [Sacred Orders Introduction](SACRED_ORDERS_INTRO.md)
- [Sacred Orders (Admin)](../internal/orders/README.md)
- [Memory Orders (Admin)](../internal/orders/MEMORY_ORDERS.md)

### `api`
- [Memory Orders API (Admin)](../internal/services/MEMORY_ORDERS_API.md)

### `governance`
- [Sacred Orders Introduction](SACRED_ORDERS_INTRO.md)
- [Dual Memory Layer](../architecture/DUAL_MEMORY_LAYER.md)
- [Sacred Orders (Admin)](../internal/orders/README.md)

## How to tag a page

```yaml
---
tags:
  - architecture
  - memory
---
```

> Note: this KB currently uses a curated tag index page to keep compatibility with the active theme and plugin set.
