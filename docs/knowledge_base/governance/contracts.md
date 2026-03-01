# Core Contracts — BaseContract & IngestionContract

> **Last updated**: March 1, 2026 00:00 UTC
> **Namespace**: `vitruvyan_core/contracts/`
> **Version**: v1.0.0 (shipped in Core v1.8.0)
> **Status**: ✅ Production

---

## Overview

The Core Contract layer is the **typed boundary system** for all data flowing through Vitruvyan. Every data structure that crosses a Sacred Order boundary — or that is emitted onto the Synaptic Conclave bus — MUST inherit from `BaseContract`.

This ensures:
- **Schema versioning** — semver identity per class, auto-registered at import time
- **Invariant enforcement** — `enforce()` validates domain rules beyond Pydantic
- **Serialization safety** — `to_dict` / `from_dict` with version checks
- **Discoverability** — `ContractRegistry` knows every contract in the system

---

## Architecture

```
contracts/
├── base.py          ← BaseContract, ContractMeta, ContractRegistry, IContractPlugin
├── ingestion.py     ← IngestionContract (SourceDescriptor, IngestionQuality,
│                        NormalizedChunk, IngestionPayload, IIngestionPlugin)
├── pattern_weavers.py  ← OntologyPayload(BaseContract)
├── comprehension.py    ← ComprehensionResult(BaseContract)
└── graph_response.py   ← GraphResponseMin(BaseContract), SessionMin(BaseContract)
```

All contracts are exported from `vitruvyan_core.contracts` (canonical namespace).

---

## BaseContract

**File**: `vitruvyan_core/contracts/base.py`

Foundation for all data contracts. Every contract class sets three `ClassVar` fields as its identity:

```python
from vitruvyan_core.contracts import BaseContract

class MyEventPayload(BaseContract):
    CONTRACT_NAME:    ClassVar[str] = "myorder.event"
    CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    CONTRACT_OWNER:   ClassVar[str] = "my_sacred_order"

    entity_id: str
    score: float
```

### Key APIs

| Method | Description |
|--------|-------------|
| `contract_id()` | Returns `"name@version"` — unique registry key |
| `validate_invariants()` | Override to add domain rules; returns `List[str]` violations |
| `enforce(strict=False)` | Runs invariants; `strict=True` raises, `False` warns. Returns `self` for chaining |
| `get_meta()` → `ContractMeta` | Metadata snapshot (name, version, owner, schema hash) |
| `to_dict(include_meta=False)` | Serialise to dict; optionally include `ContractMeta` |
| `from_dict(data, version_check=True)` | Deserialise with optional version guard |

### ContractRegistry

Contracts **auto-register** on class definition via `__init_subclass__` — no manual wiring:

```python
from vitruvyan_core.contracts.base import ContractRegistry

# After importing any module that defines BaseContract subclasses:
ContractRegistry.list_all()
# → {"ingestion.payload@1.0.0": "contracts.ingestion.IngestionPayload", ...}

ContractRegistry.get("ingestion.payload@1.0.0")  # → IngestionPayload class
ContractRegistry.is_registered("ingestion.payload")  # → True
```

### IContractPlugin

ABC base for **plugin interfaces** (not data, but extension points):

```python
from vitruvyan_core.contracts import IContractPlugin

class IMyPlugin(IContractPlugin):
    PLUGIN_CONTRACT_NAME:    ClassVar[str] = "my_plugin"
    PLUGIN_CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    PLUGIN_CONTRACT_OWNER:   ClassVar[str] = "myorder"

    @abstractmethod
    def process(self, payload: BaseContract) -> BaseContract:
        ...
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

### Classes

#### `SourceType` (Enum)

| Value | Use |
|-------|-----|
| `FILE` | Local/remote file (PDF, CSV, TXT, MD, …) |
| `API` | External API response |
| `STREAM` | Real-time stream (Redis, Kafka, WebSocket) |
| `DATABASE` | External database query result |
| `USER_INPUT` | Direct user-provided text |
| `CRAWL` | Web crawler output |
| `SYNTHETIC` | System-generated (test, simulation) |

#### `SourceDescriptor` — Source identity

```python
SourceDescriptor(
    source_id="abc123...",          # hash(uri + content_hash) — dedup key
    source_type=SourceType.API,
    uri="https://api.example.com/data",
    content_hash="sha256:...",
    mime_type="application/json",
    language="en",
    size_bytes=4096,
    acquired_by="babel_gardens.rss_plugin",
)
```

#### `IngestionQuality` — Quality gate

```python
IngestionQuality(
    completeness=0.9,
    confidence=0.85,
    noise_ratio=0.05,
    quality_score=0.87,
    gate_passed=True,       # invariant: True only if quality_score >= gate_threshold
    gate_threshold=0.3,
)
```

**Invariants** (enforced via `validate_invariants()`):
- `gate_passed=True` requires `quality_score >= gate_threshold`
- `gate_passed=True` is forbidden when `duplicate_of` is set

#### `NormalizedChunk` — Text chunk for embedding

Sub-model of `IngestionPayload` (does NOT inherit `BaseContract` — nested only):

```python
NormalizedChunk(
    chunk_id="chunk:abc123:0",
    chunk_index=0,
    text="Normalised content...",
    token_count=512,
    metadata={"page": 1, "section": "Introduction"},
)
```

#### `IngestionPayload` — Canonical Perception → Memory handoff

```python
payload = IngestionPayload(
    source=source_descriptor,
    quality=ingestion_quality,
    chunks=[chunk1, chunk2, chunk3],
    total_chunks=3,
    total_tokens=1500,
).enforce(strict=True)  # raises if invariants violated
```

**Invariants**:
- `source` and `quality` always present
- `total_chunks == len(chunks)`
- `quality.gate_passed == True` (only gated payloads reach Memory)

#### `IIngestionPlugin` — Extension point for Perception

```python
from vitruvyan_core.contracts import IIngestionPlugin, IngestionPayload

class MyIngestionPlugin(IIngestionPlugin):
    PLUGIN_CONTRACT_NAME = "my_ingestor"
    PLUGIN_CONTRACT_VERSION = "1.0.0"
    PLUGIN_CONTRACT_OWNER = "perception"

    def ingest(self, raw_data: bytes, source_type: SourceType) -> IngestionPayload:
        ...

    def normalize(self, raw_data: bytes) -> list[NormalizedChunk]:
        ...
```

---

## Synaptic Conclave Channel Constants

```python
from vitruvyan_core.contracts.ingestion import (
    CHANNEL_INGESTION_ACQUIRED,    # "perception.ingestion.acquired"
    CHANNEL_INGESTION_NORMALIZED,  # "perception.ingestion.normalized"
    CHANNEL_INGESTION_REJECTED,    # "perception.ingestion.rejected"
    CHANNEL_INGESTION_DUPLICATE,   # "perception.ingestion.duplicate"
)
```

Use these constants (never hardcode strings) when emitting/consuming ingestion events on the bus.

---

## Helper Functions

```python
from vitruvyan_core.contracts.ingestion import (
    compute_content_hash,  # bytes → "sha256:<hex>"
    build_source_id,       # (uri, content_hash) → deterministic 32-char id
    build_chunk_id,        # (source_id, chunk_index) → deterministic 32-char id
)

raw = b"document content..."
content_hash = compute_content_hash(raw)                  # "sha256:abc123..."
source_id    = build_source_id("https://example.com", content_hash)
chunk_id     = build_chunk_id(source_id, 0)
```

---

## Migrated Existing Contracts

As part of v1.8.0, existing contracts were migrated to `BaseContract`:

| Contract | File | `CONTRACT_NAME` | `CONTRACT_VERSION` |
|----------|------|-----------------|--------------------|
| `OntologyPayload` | `pattern_weavers.py` | `pattern_weavers.ontology` | `3.0.0` |
| `ComprehensionResult` | `comprehension.py` | `comprehension.result` | `1.0.0` |
| `GraphResponseMin` | `graph_response.py` | `graph_response.min` | `1.0.0` |
| `SessionMin` | `graph_response.py` | `session.min` | `1.0.0` |

All existing imports are fully backward-compatible — zero breaking changes.

---

## Testing

```bash
# Unit tests (84 tests, no I/O, no Docker)
PYTHONPATH=vitruvyan_core pytest tests/unit/contracts/ -v

# test_base_contract.py    — 40 tests (registry, enforce, meta, serialization)
# test_ingestion_contract.py — 44 tests (sources, quality gate invariants, payload)
```

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

## References

- Implementation: [`vitruvyan_core/contracts/base.py`](../../../vitruvyan_core/contracts/base.py)
- Implementation: [`vitruvyan_core/contracts/ingestion.py`](../../../vitruvyan_core/contracts/ingestion.py)
- Pipeline contract enforcement (runtime `@enforced`): [PIPELINE_CONTRACT_ENFORCEMENT.md](../../contracts/platform/PIPELINE_CONTRACT_ENFORCEMENT.md)
- Changelog: Core v1.8.0 — `feat(contracts): BaseContract + IngestionContract v1.0.0`
