# examples/ — Usage Examples & Demos

> **Last Updated**: February 12, 2026  
> **Purpose**: Executable examples, demos, tutorials  
> **Type**: Python scripts, Jupyter notebooks, Streamlit apps

---

## 🎯 Cosa Contiene

`examples/` contiene **esempi eseguibili** che dimostrano come usare Vitruvyan Core:
- Minimal usage examples (quick start)
- End-to-end flow demos
- Integration examples (bus, database, LLM)
- Jupyter notebooks (data exploration)

**Caratteristiche**:
- ✅ **Executable**: Tutti gli esempi sono runnable
- ✅ **Self-Contained**: Dependencies chiare, setup documentato
- ✅ **Educational**: Spiegano pattern e best practices
- ✅ **Tested**: Esempi validati (no broken code)

---

## 📂 Struttura (Typical)

```
examples/
├── quickstart/                  # Minimal getting started examples
│   ├── 01_hello_vitruvyan.py    → Basic import and usage
│   ├── 02_entity_creation.py    → Create and store entity
│   └── 03_event_publish.py      → Publish event to bus
│
├── bus/                         # Cognitive Bus examples
│   ├── publish_consume.py       → Full publish-consume cycle
│   ├── consumer_groups.py       → Consumer group pattern
│   └── event_streaming.py       → Streaming event processing
│
├── database/                    # Database integration examples
│   ├── postgres_crud.py         → PostgresAgent CRUD operations
│   ├── qdrant_search.py         → QdrantAgent vector search
│   └── transaction_pattern.py   → Database transactions
│
├── sacred_orders/               # Sacred Orders usage
│   ├── memory_coherence.py      → Memory Orders coherence check
│   ├── vault_archive.py         → Vault Keepers archival
│   └── orthodoxy_validation.py  → Orthodoxy Wardens validation
│
├── langgraph/                   # LangGraph orchestration
│   ├── simple_flow.py           → Minimal LangGraph flow
│   ├── custom_node.py           → Create custom node
│   └── state_management.py      → State passing between nodes
│
├── notebooks/                   # Jupyter notebooks
│   ├── data_exploration.ipynb   → Explore Vitruvyan data
│   └── signal_analysis.ipynb    → Analyze signals over time
│
└── README.md                    → Examples overview & setup
```

---

## 🚀 Quick Start Examples

### 01_hello_vitruvyan.py

**Purpose**: Minimal usage example

```python
"""Minimal Vitruvyan usage example."""

from vitruvyan_core.core.agents.postgres_agent import PostgresAgent

# Initialize agent
pg = PostgresAgent()

# Simple query
result = pg.fetch("SELECT 1 AS hello")
print(f"✅ Vitruvyan is working: {result}")
```

**Run**:
```bash
python examples/quickstart/01_hello_vitruvyan.py
```

### 02_entity_creation.py

**Purpose**: Create and store domain entity

```python
"""Create and store an entity in PostgreSQL."""

from vitruvyan_core.core.agents.postgres_agent import PostgresAgent
import uuid
from datetime import datetime

pg = PostgresAgent()

# Create entity
entity_id = str(uuid.uuid4())
entity_data = {
    "entity_id": entity_id,
    "name": "Example Entity",
    "created_at": datetime.utcnow().isoformat()
}

# Store in database
pg.execute(
    "INSERT INTO entities (entity_id, name, created_at) VALUES (%s, %s, %s)",
    (entity_data["entity_id"], entity_data["name"], entity_data["created_at"])
)

print(f"✅ Entity created: {entity_id}")
```

### 03_event_publish.py

**Purpose**: Publish event to Cognitive Bus

```python
"""Publish event to Redis Streams (Cognitive Bus)."""

from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamBus

bus = StreamBus()

# Publish event
event_data = {
    "entity_id": "example_001",
    "action": "created",
    "timestamp": "2026-02-12T00:00:00Z"
}

bus.publish("examples.entity.created", event_data)
print(f"✅ Event published to examples.entity.created")
```

---

## 📡 Bus Examples

### publish_consume.py

**Purpose**: Full publish-consume cycle with acknowledgment

```python
"""Complete publish-consume pattern with Redis Streams."""

from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamBus

bus = StreamBus()
channel = "examples.test"
group = "example_consumers"
consumer_id = "consumer_1"

# 1. Publish event
bus.publish(channel, {"test": "data"})
print("✅ Event published")

# 2. Create consumer group
bus.create_consumer_group(channel, group)
print(f"✅ Consumer group '{group}' created")

# 3. Consume events
for event in bus.consume(channel, group, consumer_id):
    print(f"📨 Received: {event.payload}")
    
    # Process event
    # ...
    
    # Acknowledge
    bus.acknowledge(event.stream, group, event.event_id)
    print("✅ Event acknowledged")
    break
```

---

## 🗄️ Database Examples

### postgres_crud.py

**Purpose**: CRUD operations with PostgresAgent

```python
"""PostgreSQL CRUD operations via PostgresAgent."""

from vitruvyan_core.core.agents.postgres_agent import PostgresAgent

pg = PostgresAgent()

# CREATE
pg.execute("INSERT INTO entities (entity_id, name) VALUES (%s, %s)", ("001", "Test"))

# READ
rows = pg.fetch("SELECT * FROM entities WHERE entity_id = %s", ("001",))
print(f"Read: {rows}")

# UPDATE
pg.execute("UPDATE entities SET name = %s WHERE entity_id = %s", ("Updated", "001"))

# DELETE
pg.execute("DELETE FROM entities WHERE entity_id = %s", ("001",))

print("✅ CRUD operations complete")
```

### qdrant_search.py

**Purpose**: Vector search with QdrantAgent

```python
"""Vector similarity search via QdrantAgent."""

from vitruvyan_core.core.agents.qdrant_agent import QdrantAgent
import numpy as np

qdrant = QdrantAgent()

# Search for similar vectors
query_vector = np.random.rand(768).tolist()  # Example embedding
results = qdrant.search(
    collection_name="memory_vectors",
    query_vector=query_vector,
    limit=5
)

for hit in results:
    print(f"Match: {hit.id}, score: {hit.score}")
```

---

## 🏛️ Sacred Orders Examples

### memory_coherence.py

**Purpose**: Use Memory Orders for coherence check

```python
"""Memory Orders coherence check example."""

from vitruvyan_core.core.governance.memory_orders.consumers import CoherenceChecker

checker = CoherenceChecker()

text_a = "The market is volatile today"
text_b = "Today the market shows high volatility"

result = checker.calculate_coherence(text_a, text_b)

print(f"Coherence score: {result.score:.2f}")
print(f"Status: {result.status}")  # COHERENT, DIVERGENT, or CONTRADICTORY
```

---

## 📓 Jupyter Notebooks

### data_exploration.ipynb

**Purpose**: Interactive data exploration

**Contents**:
1. Connect to PostgreSQL
2. Load entities and signals
3. Visualize data distributions
4. Explore entity relationships

**Run**:
```bash
jupyter notebook examples/notebooks/data_exploration.ipynb
```

---

## 🎯 Running Examples

### Prerequisites

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start infrastructure (if needed)
cd infrastructure/docker
docker compose up -d postgres redis qdrant

# 3. Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=9432
export REDIS_HOST=localhost
export REDIS_PORT=9379
```

### Run Example

```bash
# From repository root
python examples/quickstart/01_hello_vitruvyan.py

# Or
cd examples/bus
python publish_consume.py
```

---

## 📚 Example Categories

### By Complexity

| Category | Level | Examples |
|----------|-------|----------|
| **Quickstart** | Beginner | Basic imports, entity creation, event publishing |
| **Integration** | Intermediate | Bus patterns, database CRUD, LLM calls |
| **Sacred Orders** | Intermediate | Memory coherence, vault archival, orthodoxy |
| **End-to-End** | Advanced | Full flows, multi-service orchestration |

### By Component

| Component | Examples |
|-----------|----------|
| **Cognitive Bus** | publish_consume.py, consumer_groups.py, event_streaming.py |
| **PostgresAgent** | postgres_crud.py, transaction_pattern.py |
| **QdrantAgent** | qdrant_search.py, vector_operations.py |
| **LangGraph** | simple_flow.py, custom_node.py, state_management.py |
| **Sacred Orders** | memory_coherence.py, vault_archive.py, orthodoxy_validation.py |

---

## 🎯 Design Principles

1. **Self-Contained**: Each example imports only what it needs
2. **Executable**: All examples can be run directly (`python example.py`)
3. **Documented**: Inline comments explain each step
4. **Realistic**: Use real patterns (not toy code)
5. **Tested**: Examples are validated (CI checks they run)

---

## 📖 Module-Specific Examples

**Note**: `examples/` contiene **cross-cutting examples**. 

**Module-specific examples** stanno nei rispettivi moduli (locality-first):

- `vitruvyan_core/core/governance/memory_orders/examples/`
- `vitruvyan_core/core/governance/vault_keepers/examples/`
- `vitruvyan_core/core/orchestration/langgraph/examples/`
- Ecc.

---

## 📖 Link Utili

- **[Vitruvyan Core](../vitruvyan_core/README_VITRUVYAN_CORE.md)** — Core library documentation
- **[Services](../services/README_SERVICES.md)** — Service usage patterns
- **[Tests](../tests/README_TESTS.md)** — Test patterns (similar to examples)
- **[Docs Portal](../docs/index.md)** — Entry point documentazione

---

**Purpose**: Demonstrate Vitruvyan usage patterns (bus, database, Sacred Orders, LangGraph).  
**Pattern**: Executable scripts, self-contained, documented.  
**Status**: Quickstart examples, bus patterns, database CRUD, Sacred Orders usage.
