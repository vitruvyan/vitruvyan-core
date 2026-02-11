# Codex Hunters

> **Knowledge Acquisition Service — Pure Domain Layer (LIVELLO 1)**

Foundational module for discovering, validating, and normalizing external knowledge from disparate sources. The epistemic scholars that hunt for forgotten codices.

## Sacred Order

**Domain**: Perception (Ingestion)  
**Mandate**: Acquire and normalize external knowledge, ensure data quality and deduplication  
**Layer**: LIVELLO 1 (Pure Domain — No I/O, No Infrastructure)

---

## Quick Start

```python
from vitruvyan_core.core.governance.codex_hunters.domain.codex_config import CodexConfig, DataSource
from vitruvyan_core.core.governance.codex_hunters.consumers.tracker import Tracker
from vitruvyan_core.core.governance.codex_hunters.consumers.restorer import Restorer
from vitruvyan_core.core.governance.codex_hunters.consumers.binder import Binder

# Configure data sources
config = CodexConfig(
    sources=[
        DataSource(name="api_source", url="https://api.example.com", format="json"),
        DataSource(name="file_source", path="/data/input.csv", format="csv")
    ]
)

# Track and discover entities
tracker = Tracker()
discovery_input = {"config": config, "query": "AAPL"}
discovered_entities = tracker.process(discovery_input)

# Restore and validate data quality
restorer = Restorer()
for entity in discovered_entities:
    restored = restorer.process({"entity": entity, "config": config})
    print(f"Entity: {restored.entity_id}, Quality: {restored.quality_score}")

# Bind for storage
binder = Binder()
bound_entity = binder.process({"entity": restored, "config": config})
print(f"Bound entity: {bound_entity.dedupe_key}")
```

---

## Architecture

### Two-Level Pattern

| Level | Location | Purpose | Dependencies |
|-------|----------|---------|--------------|
| **LIVELLO 1** | `vitruvyan_core/core/governance/codex_hunters/` | Pure domain logic | None (stdlib only) |
| **LIVELLO 2** | `services/api_codex_hunters/` | Infrastructure, API, Docker | PostgreSQL, Qdrant, Redis |

**Direction: service → core** (ONE-WAY). LIVELLO 2 imports LIVELLO 1, never reverse.

### Domain Model

```
RawData ──track──▶ DiscoveredEntity ──restore──▶ RestoredEntity ──bind──▶ BoundEntity
```

### Core Components

- **Tracker**: Discovers and locates data from configured sources
- **Restorer**: Normalizes and validates data quality
- **Binder**: Prepares entities for permanent storage with deduplication
- **Inspector**: Audits data integrity and completeness

---

## Domain Objects

### CodexConfig
```python
@dataclass(frozen=True)
class CodexConfig:
    sources: tuple[DataSource, ...]
    quality_threshold: float = 0.5
    dedupe_enabled: bool = True
```

### DiscoveredEntity
```python
@dataclass(frozen=True)
class DiscoveredEntity:
    entity_id: str
    source_name: str
    raw_data: dict
    timestamp: str
    metadata: tuple
```

### RestoredEntity
```python
@dataclass(frozen=True)
class RestoredEntity:
    entity_id: str
    source_name: str
    normalized_data: dict
    quality_score: float  # 0.0 to 1.0
    validation_errors: tuple
    timestamp: str
```

### BoundEntity
```python
@dataclass(frozen=True)
class BoundEntity:
    entity_id: str
    dedupe_key: str  # Deterministic key for duplicate detection
    final_data: dict
    quality_score: float
    ready_for_storage: bool
    timestamp: str
```

---

## Consumers (Pure Functions)

All consumers implement the `CodexRole` interface:

```python
class CodexRole(ABC):
    @property
    def role_name(self) -> str: ...

    @property
    def description(self) -> str: ...

    def can_handle(self, event: Any) -> bool: ...

    def process(self, input_data: Any) -> Any: ...
```

### Available Roles
- **Tracker**: Data discovery and location from sources
- **Restorer**: Data normalization and quality validation
- **Binder**: Entity preparation and deduplication
- **Inspector**: Data integrity auditing

---

## Events & Channels

Codex operations emit events to the Cognitive Bus:

- `codex.entity.discovered` — New entity located
- `codex.entity.restored` — Entity normalized and validated
- `codex.entity.bound` — Entity prepared for storage
- `codex.quality.failed` — Entity failed quality check

---

## Philosophy

*"No codex left unfound."*

Codex Hunters embody five sacred tenets:

1. **Source Agnosticism** — No hardcoded data sources, all configured at runtime
2. **Pure Processing** — LIVELLO 1 consumers are pure functions with no I/O
3. **Quality Scores** — Every entity has a quality score (0.0-1.0)
4. **Deduplication** — Deterministic dedupe keys prevent duplicates
5. **Event-Driven** — All operations emit domain-agnostic events

---

## Testing

Run unit tests (no infrastructure required):
```bash
cd vitruvyan_core/core/governance/codex_hunters
pytest tests/
```

---

## Related Components

- **Service Layer**: `services/api_codex_hunters/` — REST API and infrastructure
- **Agents**: `core.agents.postgres_agent`, `core.agents.qdrant_agent` — Data persistence
- **Bus**: `core.synaptic_conclave.transport.streams.StreamBus` — Event publishing</content>
<parameter name="filePath">/home/vitruvyan/vitruvyan-core/vitruvyan_core/core/governance/codex_hunters/README.md