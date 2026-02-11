# Codex Hunters - Sacred Order Charter

## Identity

**Name**: Codex Hunters  
**Epistemic Order**: PERCEPTION (Ingestion)  
**Sacred Number**: #3  
**Motto**: "No codex left unfound"

## Mandate

The Codex Hunters are responsible for the **acquisition and normalization of external knowledge**. Like medieval scholars who traveled to remote monasteries seeking forgotten manuscripts, the Hunters discover, validate, and preserve data from disparate sources.

## Core Responsibilities

1. **Discovery (Tracker)**: Locate and fetch data from configured sources
2. **Restoration (Restorer)**: Normalize and validate data quality
3. **Binding (Binder)**: Prepare data for permanent storage
4. **Verification (Inspector)**: Audit data integrity and completeness

## Sacred Invariants

### 1. Source Agnosticism
Hunters MUST NOT hardcode specific data sources. All sources are configured at runtime through `CodexConfig`. The core is domain-agnostic.

### 2. Pure Processing
LIVELLO 1 consumers MUST be pure functions:
- NO I/O operations (network, database, filesystem)
- NO external dependencies (Redis, PostgreSQL, Qdrant)
- Input → Processing → Output

### 3. Quality Scores
Every restored entity MUST have a quality score (0.0 to 1.0). Entities with score < 0.5 are marked INVALID.

### 4. Deduplication
Every bound entity MUST have a dedupe_key for duplicate detection. The key is deterministic based on entity_id + source + data hash.

### 5. Event-Driven
All significant operations emit events via configured channels. Events are domain-agnostic (entity.discovered, entity.bound, etc.).

## Architecture Layers

### LIVELLO 1: Pure Domain (`core/governance/codex_hunters/`)
- `domain/`: Configuration and entity dataclasses
- `consumers/`: Pure processing logic
- `events/`: Channel constants
- `monitoring/`: Metric name constants

### LIVELLO 2: Service (`services/api_codex_hunters/`)
- `adapters/`: I/O operations (database, network, bus)
- `api/`: HTTP endpoints
- `main.py`: FastAPI bootstrap

## Integration Points

- **StreamBus**: Emit discovery/binding events
- **PostgresAgent**: Store entity data
- **QdrantAgent**: Store embeddings
- **Embedding Model**: Generate vectors (configured, not hardcoded)

## Configuration Philosophy

All domain-specific values are provided through `CodexConfig`:

```python
# Domain-agnostic (core default)
config = CodexConfig()  # Uses defaults: "entities", "entity_embeddings"

# Healthcare domain deployment
config = CodexConfig(
    entity_table=TableConfig(name="patients"),
    embedding_collection=CollectionConfig(name="patient_embeddings"),
    sources={"ehr": SourceConfig(...), "labs": SourceConfig(...)},
    streams=StreamConfig(prefix="codex.healthcare")
)

# E-commerce domain deployment
config = CodexConfig.from_yaml("deployments/ecommerce_config.yaml")
# YAML defines: products, product_embeddings, inventory+catalog sources
```

The core never knows what domain it's serving. That knowledge lives in configuration.

---

*"In the pursuit of knowledge, let no source be ignored, no data be corrupted, no truth be lost."*

— The Hunter's Creed
