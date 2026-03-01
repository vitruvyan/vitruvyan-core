# Core Contracts

> **Last updated**: March 1, 2026 00:30 UTC
> **Namespace**: `vitruvyan_core/contracts/`
> **Version**: v1.0.0 (Core v1.8.0) · Pipeline Enforcement v1.0.0 (Core v1.7.0)
> **Status**: ✅ Production

---

## Overview

The Core Contract layer is the **typed boundary system** for all data flowing through Vitruvyan. Every data structure that crosses a Sacred Order boundary — or that is emitted onto the Synaptic Conclave bus — MUST inherit from `BaseContract`.

This ensures:

- **Schema versioning** — semver identity per class, auto-registered at import time
- **Invariant enforcement** — `enforce()` validates domain rules beyond Pydantic
- **Serialization safety** — `to_dict` / `from_dict` with version checks
- **Discoverability** — `ContractRegistry` knows every contract in the system
- **Pipeline enforcement** — `@enforced` decorator validates node I/O at runtime

---

## File Layout

```
vitruvyan_core/contracts/
├── base.py           ← BaseContract, ContractMeta, ContractRegistry, IContractPlugin
├── ingestion.py      ← IngestionContract (SourceDescriptor, IngestionQuality,
│                         NormalizedChunk, IngestionPayload, IIngestionPlugin)
├── pattern_weavers.py   OntologyPayload(BaseContract)
├── comprehension.py     ComprehensionResult(BaseContract)
├── graph_response.py    GraphResponseMin(BaseContract), SessionMin(BaseContract),
│                        ORTHODOXY_* canonical constants
└── orchestration/       BaseGraphState (TypedDict), NodeContract, GraphPlugin, …

vitruvyan_core/core/orchestration/
├── contract_enforcement.py       @enforced decorator, ContractViolationError
└── node_contracts_registry.py    NODE_CONTRACTS — 20 nodes audited
```

All contracts exported from `vitruvyan_core.contracts` (canonical namespace).

---

## Contract Inventory

| Contract | File | `CONTRACT_NAME` | Version | Owner |
|----------|------|-----------------|---------|-------|
| `BaseContract` | `base.py` | `base` | 0.0.0 | core |
| `SourceDescriptor` | `ingestion.py` | `ingestion.source` | 1.0.0 | perception |
| `IngestionQuality` | `ingestion.py` | `ingestion.quality` | 1.0.0 | perception |
| `IngestionPayload` | `ingestion.py` | `ingestion.payload` | 1.0.0 | perception |
| `OntologyPayload` | `pattern_weavers.py` | `pattern_weavers.ontology` | 3.0.0 | pattern_weavers |
| `ComprehensionResult` | `comprehension.py` | `comprehension.result` | 1.0.0 | babel_gardens |
| `GraphResponseMin` | `graph_response.py` | `graph_response.min` | 1.0.0 | core |
| `SessionMin` | `graph_response.py` | `session.min` | 1.0.0 | core |

---

## BaseContract

**File**: `vitruvyan_core/contracts/base.py`

Foundation for all data contracts. Every contract class declares three identity `ClassVar` fields:

```python
from typing import ClassVar
from vitruvyan_core.contracts import BaseContract

class MyEventPayload(BaseContract):
    CONTRACT_NAME:    ClassVar[str] = "myorder.event"
    CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    CONTRACT_OWNER:   ClassVar[str] = "my_sacred_order"

    entity_id: str
    score: float
```

### API Reference

| Method | Description |
|--------|-------------|
| `contract_id()` | Returns `"name@version"` — unique registry key |
| `validate_invariants() → List[str]` | Override for domain rules; return violations list |
| `enforce(strict=False) → self` | Runs invariants; `strict=True` raises, `False` warns. Chainable |
| `get_meta() → ContractMeta` | Metadata snapshot (name, version, owner, schema hash) |
| `to_dict(include_meta=False)` | Serialise; optionally embed `ContractMeta` |
| `from_dict(data, version_check=True)` | Deserialise with optional version guard |

### ContractRegistry

Contracts **auto-register** on class definition via `__init_subclass__` — no manual wiring:

```python
from vitruvyan_core.contracts.base import ContractRegistry

ContractRegistry.list_all()
# → {"ingestion.payload@1.0.0": "contracts.ingestion.IngestionPayload", ...}

ContractRegistry.get("ingestion.payload@1.0.0")       # → IngestionPayload class
ContractRegistry.is_registered("ingestion.payload")   # → True
```

### IContractPlugin

ABC base for plugin interfaces (extension points, not data):

```python
from vitruvyan_core.contracts import IContractPlugin

class IMyPlugin(IContractPlugin):
    PLUGIN_CONTRACT_NAME:    ClassVar[str] = "my_plugin"
    PLUGIN_CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    PLUGIN_CONTRACT_OWNER:   ClassVar[str] = "myorder"

    @abstractmethod
    def process(self, payload: BaseContract) -> BaseContract: ...
```

Used by: `ISemanticPlugin` (Pattern Weavers), `IComprehensionPlugin` (Babel Gardens), `IIngestionPlugin` (Perception).

---

## IngestionContract

**File**: `vitruvyan_core/contracts/ingestion.py`  
**Sacred Order**: Perception (Babel Gardens + Codex Hunters)  
**Downstream**: Memory Orders, Vault Keepers, Pattern Weavers

Governs the boundary between external data sources and the epistemic kernel. ALL data entering the system MUST pass through this contract.

### Contract Guarantees

| # | Guarantee |
|---|-----------|
| 1 | **Source identity** — every item has a deterministic `source_id` |
| 2 | **Provenance** — full chain from raw source to normalised payload |
| 3 | **Quality gate** — minimum `quality_score` before Memory acceptance |
| 4 | **Schema stability** — consumers can depend on field presence |
| 5 | **Idempotency** — re-ingesting same `source_id` is safe (dedup by hash) |

### SourceType

| Value | Use |
|-------|-----|
| `FILE` | Local/remote file (PDF, CSV, TXT, MD, …) |
| `API` | External API response |
| `STREAM` | Real-time stream (Redis, Kafka, WebSocket) |
| `DATABASE` | External database query result |
| `USER_INPUT` | Direct user-provided text |
| `CRAWL` | Web crawler output |
| `SYNTHETIC` | System-generated (test, simulation) |

### SourceDescriptor

```python
SourceDescriptor(
    source_id="abc123...",          # hash(uri + content_hash) — dedup key
    source_type=SourceType.API,
    uri="https://api.example.com/data",
    content_hash="sha256:...",
    acquired_by="babel_gardens.rss_plugin",
)
```

### IngestionQuality

Quality gate assessed by Perception before handoff to Memory Orders.

```python
IngestionQuality(
    completeness=0.9,
    confidence=0.85,
    quality_score=0.87,
    gate_passed=True,       # invariant: True only if quality_score >= gate_threshold
    gate_threshold=0.3,
)
```

**Invariants**:

- `gate_passed=True` requires `quality_score >= gate_threshold`
- `gate_passed=True` forbidden when `duplicate_of` is set

### IngestionPayload

Canonical output from Perception → Memory Orders:

```python
payload = IngestionPayload(
    source=source_descriptor,
    quality=ingestion_quality,
    chunks=[chunk1, chunk2, chunk3],
    total_chunks=3,
    total_tokens=1500,
).enforce(strict=True)
```

**Invariants**: `total_chunks == len(chunks)` · `quality.gate_passed == True`

### Synaptic Conclave Channels

```python
from vitruvyan_core.contracts.ingestion import (
    CHANNEL_INGESTION_ACQUIRED,    # "perception.ingestion.acquired"
    CHANNEL_INGESTION_NORMALIZED,  # "perception.ingestion.normalized"
    CHANNEL_INGESTION_REJECTED,    # "perception.ingestion.rejected"
    CHANNEL_INGESTION_DUPLICATE,   # "perception.ingestion.duplicate"
)
```

### Helper Functions

```python
from vitruvyan_core.contracts.ingestion import (
    compute_content_hash,  # bytes → "sha256:<hex>"
    build_source_id,       # (uri, content_hash) → deterministic 32-char id
    build_chunk_id,        # (source_id, chunk_index) → deterministic 32-char id
)
```

---

## Pipeline Contract Enforcement

**File**: `vitruvyan_core/core/orchestration/contract_enforcement.py`  
**Shipped**: Core v1.7.0

The `@enforced` decorator validates that LangGraph nodes receive required state fields and produce declared output fields at runtime.

**Problem solved**: The pipeline (20 nodes, 19+ transitions) operated with zero runtime validation. `BaseGraphState` is `TypedDict(total=False)` — all fields optional, no enforcement.

### Implementation Status

| FASE | Description | Status |
|------|-------------|--------|
| 1 | `@enforced` decorator + `ContractViolationError` | ✅ DONE |
| 2 | `NODE_CONTRACTS` registry (20 nodes audited) | ✅ DONE |
| 3 | `_wrap()` in `build_graph()` + `build_minimal_graph()` | ✅ DONE |
| 4a | Orthodoxy canonical constants (`ORTHODOXY_BLESSED`, etc.) | ✅ DONE |
| 4 | codex_hunters orthodoxy fields (success/skip/error paths) | ✅ DONE |
| 4b | graph_adapter fallback `"blessed"` → `"non_liquet"` | ✅ DONE |
| 5 | Bus emit validation (opt-in) | ⏳ DEFERRED |
| 6 | `_check_payload_contract` strict raise | ✅ DONE |
| 7 | `OntologyPayload.model_validate()` at pw_compile boundary | ✅ DONE |
| 8 | E2E architectural tests (21 tests) | ✅ DONE |

### Key Files

| File | Lines | Role |
|------|-------|------|
| `core/orchestration/contract_enforcement.py` | ~190 | `@enforced`, `ContractViolationError`, `NodeContractSpec` |
| `core/orchestration/node_contracts_registry.py` | ~260 | `NODE_CONTRACTS` — 20 nodes, verified requires/produces |
| `core/orchestration/langgraph/graph_flow.py` | ~615 | `_wrap()` — all `add_node()` calls wrapped |
| `contracts/graph_response.py` | ~150 | `ORTHODOXY_*` canonical constants |
| `tests/unit/orchestration/test_contract_enforcement.py` | ~190 | 19 unit tests (warn/strict/off modes) |
| `tests/architectural/test_pipeline_contract_enforcement.py` | ~230 | 21 E2E tests |

### Environment Variable

```bash
CONTRACT_ENFORCE_MODE=warn    # default — log WARNING on violation
CONTRACT_ENFORCE_MODE=strict  # raise ContractViolationError (staging/test)
CONTRACT_ENFORCE_MODE=off     # zero overhead — original function returned
```

### Usage in build_graph()

```python
from core.orchestration.contract_enforcement import enforced
from core.orchestration.node_contracts_registry import NODE_CONTRACTS

_NODE_ALIAS = {"llm_soft": "cached_llm", "intent": "intent_detection"}

def _wrap(name, fn):
    registry_key = _NODE_ALIAS.get(name, name)
    spec = NODE_CONTRACTS.get(registry_key)
    if spec and (spec.requires or spec.produces):
        return enforced(requires=spec.requires, produces=spec.produces, node_name=name)(fn)
    return fn

g.add_node("parse",      _wrap("parse",      parse_node))
g.add_node("orthodoxy",  _wrap("orthodoxy",  orthodoxy_node))
```

### Domain Plugin Integration

```python
from core.orchestration.contract_enforcement import NodeContractSpec
from core.orchestration.node_contracts_registry import merge_domain_contracts

# In domains/<domain>/graph_nodes/registry.py:
def get_my_node_contracts():
    return {
        "my_node": NodeContractSpec(
            requires=["input_text"],
            produces=["my_result"]
        )
    }
```

### Design Decisions

1. **Decorator, not Agent** — contracts are pure Python (no I/O). Agents wrap external systems.
2. **Applied in build_graph()** — nodes are unaware of wrapping.
3. **Only critical requires** — fields accessed via `.get(default)` are not listed.
4. **Only guaranteed produces** — conditional outputs not listed.
5. **LIVELLO 1 compliant** — no prometheus_client in enforcement layer.

---

## Adding a New Contract

1. Inherit from `BaseContract`
2. Set `CONTRACT_NAME`, `CONTRACT_VERSION`, `CONTRACT_OWNER` as `ClassVar[str]`
3. Override `validate_invariants()` for domain rules
4. Export from `vitruvyan_core/contracts/__init__.py`
5. Add unit tests in `tests/unit/contracts/`

```python
# contracts/myorder_result.py
from typing import ClassVar, List
from vitruvyan_core.contracts.base import BaseContract

class MyOrderResult(BaseContract):
    CONTRACT_NAME:    ClassVar[str] = "myorder.result"
    CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    CONTRACT_OWNER:   ClassVar[str] = "my_sacred_order"

    entity_id: str
    score: float

    def validate_invariants(self) -> List[str]:
        if not 0.0 <= self.score <= 1.0:
            return [f"score must be in [0, 1], got {self.score}"]
        return []
```

---

## Testing

```bash
# Contract unit tests (84 tests, pure Python, no Docker)
PYTHONPATH=vitruvyan_core pytest tests/unit/contracts/ -v

# Pipeline enforcement tests
PYTHONPATH=vitruvyan_core pytest tests/unit/orchestration/test_contract_enforcement.py
PYTHONPATH=vitruvyan_core pytest tests/architectural/test_pipeline_contract_enforcement.py
```

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| Core v1.8.0 | Feb 28, 2026 | `BaseContract`, `IngestionContract` v1.0.0; all existing contracts migrated |
| Core v1.7.0 | Feb 28, 2026 | Pipeline `@enforced` decorator + `NODE_CONTRACTS` registry (20 nodes) |

---

## See Also

- Vertical contracts: [`docs/contracts/verticals/`](../contracts/verticals/README.md)
- RAG governance contract: [`docs/contracts/rag/`](../contracts/rag/README.md)
- Platform/update contract: [`docs/contracts/platform/UPDATE_SYSTEM_CONTRACT_V1.md`](../contracts/platform/UPDATE_SYSTEM_CONTRACT_V1.md)
- Implementation source: `vitruvyan_core/contracts/`
- Historical roadmap (archived): `docs/planning/CONTRACT_ENFORCEMENT_ROADMAP.md`
