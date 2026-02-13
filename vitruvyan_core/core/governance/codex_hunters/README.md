# Codex Hunters

> **Structured Data Acquisition & Canonicalization Order**  
> **Epistemic Layer**: PERCEPTION (Ingestion)  
> **LIVELLO 1**: Pure Domain — Domain-Agnostic Knowledge Discovery

This page follows the shared documentation template:
`docs/foundational/TEMPLATE_SACRED_ORDER_COMPONENT.md`.

---

## 📜 Charter

Codex Hunters are responsible for **acquiring and normalizing external knowledge** from disparate sources. Like medieval scholars traveling to remote monasteries seeking forgotten manuscripts, the Hunters discover, validate, and preserve data with unwavering precision.

**Sacred Mandate**: No codex left unfound, no data corrupted, no truth lost.

### Non-goals (boundaries)

- Not a risk engine (scoring/forecasting belongs to Reason-layer engines).
- Not a UI, not an auth boundary (enforce access at reverse-proxy).
- LIVELLO 1 is **pure**: no HTTP, no DB, no Redis I/O.

---

## 🎯 Quick Start

```python
from vitruvyan_core.core.governance.codex_hunters.domain.config import (
    CodexConfig, SourceConfig, QualityConfig
)
from vitruvyan_core.core.governance.codex_hunters.consumers import (
    TrackerConsumer, RestorerConsumer, BinderConsumer
)

# Configure (domain-agnostic)
config = CodexConfig(
    sources={
        "primary_api": SourceConfig(
            name="primary_api",
            rate_limit_per_minute=100,
            timeout_seconds=30
        )
    },
    quality=QualityConfig(
        threshold_valid=0.6,  # Minimum quality score
        penalty_per_error=0.1
    )
)

# Discovery Pipeline: Track → Restore → Bind
tracker = TrackerConsumer(config)
restorer = RestorerConsumer(config)
binder = BinderConsumer(config)

# Step 1: Discover entity
result = tracker.process({
    "entity_id": "entity_001",
    "source": "primary_api",
    "raw_data": {"name": "Example", "value": 123}
})
discovered = result.data["entity"]

# Step 2: Restore (normalize + validate)
result = restorer.process({"entity": discovered})
restored = result.data["entity"]
print(f"Quality score: {restored.quality_score}")  # 0.0-1.0

# Step 3: Bind (prepare for storage)
result = binder.process({"entity": restored})
bound = result.data["bound_entity"]
print(f"Dedupe key: {bound.dedupe_key}")  # Deterministic hash
```

---

## 🧭 Code Map (Where to Read)

### LIVELLO 1 (Pure Domain)

- `vitruvyan_core/core/governance/codex_hunters/domain/config.py` — `CodexConfig` (sources, streams, quality, storage targets)
- `vitruvyan_core/core/governance/codex_hunters/consumers/tracker.py` — discovery request validation + `DiscoveredEntity` + deterministic `dedupe_key`
- `vitruvyan_core/core/governance/codex_hunters/consumers/restorer.py` — normalization + validation + `quality_score` → `RestoredEntity`
- `vitruvyan_core/core/governance/codex_hunters/consumers/binder.py` — bind metadata + dedupe + optional embedding id → `BoundEntity`
- `vitruvyan_core/core/governance/codex_hunters/docs/CODEX_HUNTERS_REFACTOR_PLAN.md` — roadmap + boundary enforcement targets

### LIVELLO 2 (Service / Adapters)

- `services/api_codex_hunters/main.py` — FastAPI service entrypoint
- `services/api_codex_hunters/adapters/bus_adapter.py` — orchestrates LIVELLO 1 consumers + emits Streams events
- `services/api_codex_hunters/streams_listener.py` — Streams consumer that dispatches requests to the API
- `vitruvyan_core/core/orchestration/langgraph/node/codex_hunters_node.py` — current LangGraph integration (API-trigger)
- `vitruvyan_core/core/orchestration/langgraph/codex_trigger.py` — helper to trigger expeditions from graph/system

---

## 🏛️ Architecture

### Two-Level Pattern (SACRED_ORDER_PATTERN)

| Layer | Location | Dependencies | Purpose |
|-------|----------|--------------|---------|
| **LIVELLO 1** | `vitruvyan_core/core/governance/codex_hunters/` | **None** (stdlib only) | Pure domain logic |
| **LIVELLO 2** | `services/api_codex_hunters/` | Postgres, Qdrant, Redis | Infrastructure + I/O |

**Direction: `services/` → `core/`** (ONE-WAY)

### Sacred Invariants

1. **Source Agnosticism**: No hardcoded data sources (all configured via `CodexConfig`)
2. **Pure Processing**: LIVELLO 1 consumers = pure functions (no I/O)
3. **Quality Scores**: Every restored entity has `quality_score` (0.0-1.0)
4. **Deduplication**: Deterministic `dedupe_key` = `hash(entity_id + source + data_hash)`
5. **Event-Driven**: All operations emit domain-agnostic events

---

## 📦 Domain Model

```
External Data ─┬─→ Track   → DiscoveredEntity
               │   (locate)
               │
               ├─→ Restore → RestoredEntity
               │   (normalize + validate)
               │
               └─→ Bind    → BoundEntity
                   (prepare for storage)
```

### Core Entities

#### `DiscoveredEntity`
```python
@dataclass(frozen=True)
class DiscoveredEntity:
    entity_id: str              # Domain identifier
    source: str                 # Configured source name
    discovered_at: datetime
    raw_data: Dict[str, Any]    # Unprocessed payload
    metadata: Dict[str, Any]
    status: EntityStatus        # DISCOVERED
```

#### `RestoredEntity`
```python
@dataclass(frozen=True)
class RestoredEntity:
    entity_id: str
    source: str
    restored_at: datetime
    normalized_data: Dict[str, Any]  # Cleaned payload
    quality_score: float             # 0.0 (invalid) to 1.0 (perfect)
    validation_errors: List[str]
    status: EntityStatus             # RESTORED | INVALID
```

#### `BoundEntity`
```python
@dataclass(frozen=True)
class BoundEntity:
    entity_id: str
    source: str
    bound_at: datetime
    storage_refs: Dict[str, str]     # {"relational": "entities", "vector": "embeddings"}
    embedding_id: Optional[str]      # If embedding provided
    dedupe_key: str                  # Deterministic hash
    status: EntityStatus             # BOUND
```

---

## ⚙️ Configuration

### CodexConfig (Domain-Agnostic)

```python
@dataclass
class CodexConfig:
    # Storage targets (abstract, no provider assumptions)
    entity_table: TableConfig = TableConfig(name="entities")
    embedding_collection: CollectionConfig = CollectionConfig(name="entity_embeddings")
    
    # Data sources (configured at deployment)
    sources: Dict[str, SourceConfig] = field(default_factory=dict)
    
    # Quality scoring (config-driven, no hardcoded thresholds)
    quality: QualityConfig = QualityConfig(
        threshold_valid=0.5,       # Minimum score for VALID status
        penalty_per_error=0.1,     # Score deduction per error
        penalty_null_ratio=0.3     # Score deduction for null fields
    )
    
    # Event streams
    streams: StreamConfig = StreamConfig(prefix="codex")
    
    # Embedding settings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
```

### YAML Configuration

```yaml
# config/deployment.yaml
entity_table:
  name: "medical_records"
  schema: "healthcare"

embedding_collection:
  name: "patient_embeddings"
  vector_size: 384

sources:
  ehr_system:
    name: "Electronic Health Records"
    rate_limit_per_minute: 50
    timeout_seconds: 45
  lab_results:
    name: "Laboratory Results API"
    rate_limit_per_minute: 100

quality:
  threshold_valid: 0.7
  penalty_per_error: 0.15
```

```python
# Load from YAML
from pathlib import Path
config = CodexConfig.from_yaml(Path("config/deployment.yaml"))
```

---

## 🔧 Consumers (Pure Functions)

### TrackerConsumer

**Purpose**: Discover entities from configured sources  
**Input**: `{entity_id, source, raw_data}`  
**Output**: `DiscoveredEntity` + deterministic `dedupe_key`

**Key Features**:
- ✅ Validates source is configured
- ✅ Generates hash-based dedupe key (NOT date-based)
- ✅ No I/O (delegates fetch to LIVELLO 2 adapters)

### RestorerConsumer

**Purpose**: Normalize and validate data quality  
**Input**: `{entity: DiscoveredEntity}`  
**Output**: `RestoredEntity` with `quality_score`

**Quality Scoring** (config-driven):
```python
score = 1.0
score -= len(validation_errors) * config.quality.penalty_per_error
score -= null_field_ratio * config.quality.penalty_null_ratio
score = clamp(score, 0.0, 1.0)
```

**Status Assignment**:
- `quality_score >= threshold_valid` → `RESTORED`
- `quality_score < threshold_valid` → `INVALID`

### BinderConsumer

**Purpose**: Prepare entity for permanent storage  
**Input**: `{entity: RestoredEntity, embedding: Optional[List[float]]}`  
**Output**: `BoundEntity` + `normalized_data`

**CRITICAL**: Returns domain-agnostic data. LIVELLO 2 adapter constructs provider-specific payloads (Postgres JSONB, Qdrant points).

---

## 📡 Events

### Channel Naming (Domain-Neutral)

```
codex.entity.discovered   → Entity tracked
codex.entity.restored     → Entity normalized
codex.entity.bound        → Entity ready for storage
codex.expedition.completed → Batch operation finished
```

### Event Envelope

```python
{
    "event_id": "evt_123",
    "channel": "codex.entity.discovered",
    "payload": {
        "entity_id": "entity_001",
        "source": "primary_api",
        "discovered_at": "2026-02-11T10:30:00Z"
    },
    "timestamp": "2026-02-11T10:30:00.123Z"
}
```

---

## 🧪 Testing

```bash
# Unit tests (no I/O, no Docker)
cd vitruvyan_core/core/governance/codex_hunters
pytest tests/

# Verify purity (no infrastructure imports)
python3 -c "from vitruvyan_core.core.governance.codex_hunters.consumers import *; print('✅ Pure')"
```

---

## 🧩 Verticalization (Domain Implementation Guide)

Codex Hunters is domain-agnostic by design. A **vertical domain** (finance, energy, healthcare, …) plugs in by providing a “domain pack” that defines:

1) **Vocabulary** (what `entity_id` means in that domain)  
2) **Sources** (where raw data comes from)  
3) **Normalization rules** (how to standardize raw payloads)  
4) **Routing hooks** (when to trigger an expedition in orchestration)

### 1) Vocabulary mapping (avoid confusion)

| Core primitive | Finance example | Energy example |
|---|---|---|
| `entity_id` | `ticker` (AAPL) | `plant_id` / `meter_id` |
| `source` | market data provider | SCADA / ISO feed |
| `normalized_data` | fundamentals/metrics | telemetry/forecasts |

### 2) Domain config (tables/collections/stream prefix/sources)

Use `CodexConfig` to re-bind storage targets, stream prefix, and enabled sources without changing core logic:

- `vitruvyan_core/core/governance/codex_hunters/domain/config.py` (`CodexConfig.from_yaml(...)`)

Practical rule:
- Keep **domain choices** (entity tables, stream prefixes, enabled sources) in config.
- Keep **core stages** (Track/Restore/Bind) unchanged.

### 3) Domain normalization (source-specific “normalizers”)

In LIVELLO 1, normalization is injected via `RestorerConsumer.register_normalizer(source, fn)`:

- `vitruvyan_core/core/governance/codex_hunters/consumers/restorer.py`

Pattern:
- For each enabled `source`, register a normalizer that converts vendor payload → canonical `normalized_data`.

### 4) Domain routing (when to trigger Codex expeditions)

The core orchestration supports domain plugins; finance is the reference pattern:

- `vitruvyan_core/domains/finance_plugin.py` (GraphPlugin + custom router → `"codex_expedition"`)
- `examples/verticals/README.md` (vertical extension philosophy)

Rule of thumb:
- Trigger Codex Hunters when the domain needs **discovery/mapping** (e.g., missing entity IDs) before execution.

---

## 🎨 Domain Deployment Examples (configuration-only)

### Healthcare

```python
CodexConfig(
    entity_table=TableConfig(name="patients"),
    embedding_collection=CollectionConfig(name="patient_embeddings"),
    sources={
        "ehr": SourceConfig(name="Electronic Health Records", ...),
        "labs": SourceConfig(name="Lab Results API", ...)
    }
)
```

### E-Commerce

```python
CodexConfig(
    entity_table=TableConfig(name="products"),
    embedding_collection=CollectionConfig(name="product_embeddings"),
    sources={
        "inventory": SourceConfig(name="Inventory Management", ...),
        "supplier": SourceConfig(name="Supplier API", ...)
    }
)
```

### Research

```python
CodexConfig(
    entity_table=TableConfig(name="papers"),
    embedding_collection=CollectionConfig(name="paper_embeddings"),
    sources={
        "arxiv": SourceConfig(name="ArXiv API", ...),
        "pubmed": SourceConfig(name="PubMed", ...)
    }
)
```

---

## ⚠️ Known issues / roadmap

Codex Hunters is being actively “de-financialized”. Track target state and boundary enforcement here:

- `vitruvyan_core/core/governance/codex_hunters/docs/CODEX_HUNTERS_REFACTOR_PLAN.md`

---

## 📚 Philosophy

See [charter.md](philosophy/charter.md) for Sacred Order identity, mandate, and invariants.

---

## 🔗 Integration

- **LIVELLO 2 Service**: `services/api_codex_hunters/` (FastAPI + Docker)
- **Adapters**: `services/api_codex_hunters/adapters/` (I/O bound

ary)
- **Examples**: `examples/` (usage patterns)
- **Tests**: `tests/` (unit tests)

---

*"In the pursuit of knowledge, let no source be ignored, no data be corrupted, no truth be lost."*  
— The Hunter's Creed
