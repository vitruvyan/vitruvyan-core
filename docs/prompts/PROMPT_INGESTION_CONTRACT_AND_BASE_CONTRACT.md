# Copilot Implementation Prompt — Ingestion Contract + BaseContract

> **Last updated**: February 28, 2026 19:30 UTC
> **Target repo**: `vitruvyan-core` (`/home/vitruvyan/vitruvyan-core`)
> **Branch**: `main`
> **Prerequisites**: v1.7.0 (contract enforcement FASE 1-8 complete)

---

## Objective

Implement **two interconnected deliverables** in `vitruvyan_core/contracts/`:

1. **`BaseContract`** — Abstract foundation that ALL existing and future contracts inherit from. Provides: versioning, schema identity, validation hooks, enforcement integration, serialization. Makes contracts **binding** (runtime-enforced, not just documentation).

2. **`IngestionContract`** — First contract built on `BaseContract`. Governs data ingestion into the Vitruvyan epistemic OS (Sacred Order: Perception — Babel Gardens + Codex Hunters). Defines: source validation, payload normalization schema, metadata requirements, quality gates, provenance tracking.

**Execution order**: BaseContract FIRST (foundation), then IngestionContract (first consumer).

---

## PART 1: BaseContract

### 1.1 Problem Statement

The current `vitruvyan_core/contracts/` package contains **7 independent contract modules** with no shared base:

| Module | Style | Versioned? | Enforced? |
|--------|-------|------------|-----------|
| `graph_response.py` | Pydantic BaseModel | No | Via `@enforced` (node-level) |
| `pattern_weavers.py` | Pydantic + ABC | `schema_version` field | `extra="forbid"` on models |
| `comprehension.py` | Pydantic + ABC | `schema_version` field | `extra="forbid"` on models |
| `rag.py` | dataclass + Enum | Contract Version in docstring | `__post_init__` validators |
| `llm_provider.py` | Protocol | No | `@runtime_checkable` |
| `orchestration.py` | Re-export shim | No | No |
| `neural_engine/` | ABC | No | Duck-typing |

**Gap**: No schema registry, no contract versioning lifecycle, no unified validation hooks, no enforcement metadata. Each contract reinvents basic patterns.

### 1.2 Design Specification

Create `vitruvyan_core/contracts/base.py` (~120-150 lines):

```python
"""
BaseContract — Vitruvyan Contract Foundation
=============================================

All contracts in vitruvyan_core/contracts/ MUST inherit from BaseContract
(for data contracts) or IContractPlugin (for plugin/interface contracts).

Provides:
  - Schema versioning (semver string, immutable per instance)
  - Contract identity (unique name, owner Sacred Order)
  - Validation hooks (pre/post with override points)
  - Enforcement metadata (mode, timestamp, violations)
  - Serialization (to_dict / from_dict with version checking)
  - Registry integration (auto-registration on class creation)

LIVELLO 1 compliance: Pure Python + Pydantic. No I/O.

Author: Vitruvyan Core Team
Created: <today>
"""
```

#### 1.2.1 Core Classes

```python
from pydantic import BaseModel, ConfigDict, Field
from abc import ABC, abstractmethod
from typing import ClassVar, Dict, Any, Optional, List
from datetime import datetime, timezone


class ContractMeta(BaseModel):
    """Immutable metadata attached to every contract instance."""
    contract_name: str                          # e.g. "ingestion", "graph_response"
    contract_version: str                       # semver: "1.0.0"
    owner: str = "core"                         # Sacred Order or "core"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    schema_hash: str = ""                       # Auto-computed from model schema


class BaseContract(BaseModel):
    """
    Foundation for ALL data contracts in Vitruvyan Core.
    
    Subclasses MUST set:
      - CONTRACT_NAME: ClassVar[str]
      - CONTRACT_VERSION: ClassVar[str]  (semver)
      - CONTRACT_OWNER: ClassVar[str]    (Sacred Order name or "core")
    
    Subclasses MAY override:
      - validate_invariants() — domain-specific validation beyond Pydantic
      - on_violation() — custom violation handling (default: log + optional raise)
    """
    model_config = ConfigDict(extra="forbid")
    
    # --- Class-level identity (subclasses MUST override) ---
    CONTRACT_NAME: ClassVar[str] = "base"
    CONTRACT_VERSION: ClassVar[str] = "0.0.0"
    CONTRACT_OWNER: ClassVar[str] = "core"
    
    # --- Instance metadata ---
    _meta: Optional[ContractMeta] = None  # Populated on first access
    
    @classmethod
    def contract_id(cls) -> str:
        """Unique identifier: '{name}@{version}'"""
        return f"{cls.CONTRACT_NAME}@{cls.CONTRACT_VERSION}"
    
    def validate_invariants(self) -> List[str]:
        """
        Override to add domain-specific invariants beyond Pydantic field validation.
        
        Returns:
            List of violation messages. Empty list = all invariants satisfied.
        """
        return []
    
    def enforce(self, *, strict: bool = False) -> "BaseContract":
        """
        Run validate_invariants(). In strict mode, raise on violations.
        In warn mode, log warnings.
        
        Returns self for chaining: payload = MyContract(**data).enforce(strict=True)
        """
        # Implementation: call validate_invariants(), handle violations
        ...
        return self
    
    def get_meta(self) -> ContractMeta:
        """Return contract metadata (lazy-created)."""
        ...
    
    def to_dict(self, *, include_meta: bool = False) -> Dict[str, Any]:
        """Serialize to dict, optionally including __contract_meta__."""
        ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], *, version_check: bool = True) -> "BaseContract":
        """
        Deserialize from dict.
        If version_check=True, warn/raise if data was produced by a different contract version.
        """
        ...
```

#### 1.2.2 Contract Registry

```python
class ContractRegistry:
    """
    In-memory registry of all known contract classes.
    
    Contracts auto-register on class definition via __init_subclass__.
    Registry enables:
      - Runtime introspection of available contracts
      - Version compatibility checks
      - Schema diff between versions (future)
    """
    _contracts: ClassVar[Dict[str, type]] = {}   # contract_id → class
    
    @classmethod
    def register(cls, contract_class: type) -> None: ...
    
    @classmethod
    def get(cls, contract_id: str) -> Optional[type]: ...
    
    @classmethod
    def list_all(cls) -> Dict[str, str]: ...
    
    @classmethod
    def is_registered(cls, name: str) -> bool: ...
```

#### 1.2.3 Plugin Contract Base (for ABC/Protocol contracts)

```python
class IContractPlugin(ABC):
    """
    Base for plugin/interface contracts (ISemanticPlugin, IComprehensionPlugin, etc.).
    
    Adds contract identity metadata to ABC interfaces.
    Cannot use BaseContract (which is BaseModel) since plugins are ABCs.
    """
    PLUGIN_CONTRACT_NAME: ClassVar[str] = "base_plugin"
    PLUGIN_CONTRACT_VERSION: ClassVar[str] = "0.0.0"
    
    @classmethod
    def plugin_contract_id(cls) -> str:
        return f"{cls.PLUGIN_CONTRACT_NAME}@{cls.PLUGIN_CONTRACT_VERSION}"
```

### 1.3 Migration Plan — Existing Contracts

After creating `BaseContract`, refactor existing contracts to inherit from it. **DO NOT break existing imports.**

| Contract | Migration | ClassVars |
|----------|-----------|-----------|
| `OntologyPayload` | `class OntologyPayload(BaseContract)` | `CONTRACT_NAME="pattern_weavers.ontology"`, `CONTRACT_VERSION="3.0.0"`, `CONTRACT_OWNER="pattern_weavers"` |
| `ComprehensionResult` | `class ComprehensionResult(BaseContract)` | `CONTRACT_NAME="comprehension.result"`, `CONTRACT_VERSION="1.0.0"`, `CONTRACT_OWNER="babel_gardens"` |
| `GraphResponseMin` | `class GraphResponseMin(BaseContract)` | `CONTRACT_NAME="graph_response.min"`, `CONTRACT_VERSION="1.0.0"`, `CONTRACT_OWNER="core"` |
| `SessionMin` | `class SessionMin(BaseContract)` | `CONTRACT_NAME="session.min"`, `CONTRACT_VERSION="1.0.0"`, `CONTRACT_OWNER="core"` |
| `RAGPayload` | Keep as `@dataclass` for now (RAG uses dataclass pattern) — future migration | — |
| `ISemanticPlugin` | `class ISemanticPlugin(IContractPlugin)` | `PLUGIN_CONTRACT_NAME="semantic_plugin"`, `PLUGIN_CONTRACT_VERSION="3.0.0"` |
| `IComprehensionPlugin` | `class IComprehensionPlugin(IContractPlugin)` | `PLUGIN_CONTRACT_NAME="comprehension_plugin"`, `PLUGIN_CONTRACT_VERSION="1.0.0"` |
| `ILLMProvider` | Keep as `Protocol` (structural typing) — `IContractPlugin` integration optional | — |

**Migration rules**:
- `extra="forbid"` is ALREADY on `BaseContract.model_config` — remove duplicate declarations from subclasses
- `schema_version` instance field → replaced by `CONTRACT_VERSION` ClassVar (remove field, keep backward compat via property if needed)
- All existing tests must pass without modification
- All existing `from contracts import X` must still work

### 1.4 Files to Create/Modify

**Create**:
- `vitruvyan_core/contracts/base.py` (~150L) — BaseContract, ContractMeta, ContractRegistry, IContractPlugin

**Modify** (after base.py is stable):
- `vitruvyan_core/contracts/pattern_weavers.py` — OntologyPayload inherits BaseContract
- `vitruvyan_core/contracts/comprehension.py` — ComprehensionResult inherits BaseContract
- `vitruvyan_core/contracts/graph_response.py` — GraphResponseMin, SessionMin inherit BaseContract
- `vitruvyan_core/contracts/__init__.py` — export BaseContract, ContractMeta, ContractRegistry, IContractPlugin

**Create tests**:
- `tests/unit/contracts/test_base_contract.py` (~200L) — Test BaseContract inheritance, versioning, registry, enforce(), serialization, invariant hooks

### 1.5 Integration with `@enforced` Decorator

The `@enforced` decorator (`core/orchestration/contract_enforcement.py`) works at **node level** (state dict field checking). `BaseContract` works at **data level** (payload schema validation). They are complementary:

- `@enforced(produces=["ontology"])` — ensures the node produces a field named `ontology`
- `OntologyPayload.enforce(strict=True)` — ensures the CONTENT of that field is valid

**Integration point**: In `_check_payload_contract()` (already in `qdrant_agent.py`) and `model_validate()` calls, replace raw Pydantic validation with `BaseContract.enforce()` to get unified violation tracking.

---

## PART 2: Ingestion Contract

### 2.1 Problem Statement

The Sacred Order of Perception (Babel Gardens + Codex Hunters) acquires and normalizes external inputs, but there is **no formal contract** defining:
- What constitutes a valid ingestion source
- What metadata MUST accompany ingested data
- What normalization guarantees the pipeline provides
- What quality gates data must pass before entering Memory
- How provenance is tracked from source to embedding

Currently, ingestion is ad-hoc: Codex Hunters discover files, Babel Gardens comprehend text, but the handoff contract between them and downstream Sacred Orders (Memory Orders, Vault Keepers) is implicit.

### 2.2 Design Specification

Create `vitruvyan_core/contracts/ingestion.py` (~200-250 lines):

```python
"""
Ingestion Contract — Data Acquisition & Normalization
======================================================

Governs the boundary between external data sources and the
Vitruvyan epistemic kernel. ALL data entering the system MUST
pass through this contract.

Sacred Order: Perception (Babel Gardens + Codex Hunters)
Downstream consumers: Memory Orders, Vault Keepers, Pattern Weavers

Contract guarantees:
  1. Source identity: every ingested item has a deterministic source_id
  2. Provenance: full chain from raw source to normalized payload
  3. Quality gate: minimum quality score before Memory acceptance
  4. Schema stability: consumers can depend on field presence
  5. Idempotency: re-ingesting same source_id is safe (dedup by hash)

LIVELLO 1: Pure Python + Pydantic. No I/O, no external dependencies.

Author: Vitruvyan Core Team
Created: <today>
Contract Version: 1.0.0
"""
```

#### 2.2.1 Source Identity

```python
class SourceType(str, Enum):
    """Classification of ingestion sources."""
    FILE = "file"               # Local/remote file (PDF, CSV, TXT, MD, etc.)
    API = "api"                 # External API response
    STREAM = "stream"           # Real-time stream (Redis, Kafka, WebSocket)
    DATABASE = "database"       # External database query result
    USER_INPUT = "user_input"   # Direct user-provided text
    CRAWL = "crawl"             # Web crawler output
    SYNTHETIC = "synthetic"     # System-generated (test, simulation)


class SourceDescriptor(BaseContract):
    """
    Immutable descriptor for a data source.
    
    Every piece of data entering Vitruvyan MUST have a SourceDescriptor.
    The source_id is deterministic: same source → same id (enables dedup).
    """
    CONTRACT_NAME = "ingestion.source"
    CONTRACT_VERSION = "1.0.0"
    CONTRACT_OWNER = "perception"
    
    source_id: str              # Deterministic hash (content_hash or URI hash)
    source_type: SourceType
    uri: str = ""               # Original location (file path, URL, stream name)
    content_hash: str = ""      # SHA-256 of raw content (dedup key)
    mime_type: str = "text/plain"
    language: str = "auto"      # ISO 639-1 or "auto" for detection
    encoding: str = "utf-8"
    size_bytes: int = 0
    acquired_at: datetime       # When the data was acquired
    acquired_by: str = ""       # Service/order that acquired it
    
    # Provenance chain
    parent_source_id: Optional[str] = None  # If derived from another source
    provenance_chain: List[str] = Field(default_factory=list)
```

#### 2.2.2 Ingestion Payload

```python
class IngestionQuality(BaseContract):
    """
    Quality assessment of ingested data.
    
    Populated by Perception orders BEFORE handoff to Memory.
    Memory Orders MAY reject data below minimum quality thresholds.
    """
    CONTRACT_NAME = "ingestion.quality"
    CONTRACT_VERSION = "1.0.0"
    CONTRACT_OWNER = "perception"
    
    completeness: float = Field(default=0.0, ge=0.0, le=1.0)   # % of expected fields present
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)     # Extraction confidence
    noise_ratio: float = Field(default=0.0, ge=0.0, le=1.0)    # % noise/irrelevant content
    language_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    encoding_valid: bool = True
    duplicate_of: Optional[str] = None  # source_id of duplicate, if detected
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)  # Composite quality score
    gate_passed: bool = False           # True if quality_score >= threshold
    gate_threshold: float = 0.3        # Configurable minimum quality
    assessment_method: str = "auto"    # How quality was assessed
    
    def validate_invariants(self) -> List[str]:
        violations = []
        if self.gate_passed and self.quality_score < self.gate_threshold:
            violations.append(
                f"gate_passed=True but quality_score ({self.quality_score}) "
                f"< gate_threshold ({self.gate_threshold})"
            )
        if self.duplicate_of and self.gate_passed:
            violations.append("gate_passed=True for a detected duplicate")
        return violations


class NormalizedChunk(BaseModel):
    """A single normalized text chunk ready for embedding."""
    model_config = ConfigDict(extra="forbid")
    
    chunk_id: str               # Deterministic: hash(source_id + chunk_index)
    chunk_index: int = 0        # Position in source document
    text: str                   # Normalized text content
    token_count: int = 0        # Approximate token count
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Chunk-level metadata


class IngestionPayload(BaseContract):
    """
    The canonical ingestion output — what Perception hands to Memory.
    
    Contract guarantees:
      - source is ALWAYS populated (provenance)
      - quality is ALWAYS populated (gate decision)
      - chunks contains at least 1 NormalizedChunk (empty source = error, not empty payload)
      - extracted_metadata preserves domain-agnostic metadata from source
    
    Downstream consumers (Memory Orders, Vault Keepers) depend on this schema.
    """
    CONTRACT_NAME = "ingestion.payload"
    CONTRACT_VERSION = "1.0.0"
    CONTRACT_OWNER = "perception"
    
    # Identity
    ingestion_id: str           # UUID for this ingestion event
    
    # Source provenance
    source: SourceDescriptor
    
    # Quality assessment
    quality: IngestionQuality
    
    # Normalized output
    chunks: List[NormalizedChunk] = Field(default_factory=list)
    total_chunks: int = 0
    total_tokens: int = 0
    
    # Extracted metadata (domain-agnostic)
    extracted_metadata: Dict[str, Any] = Field(default_factory=dict)
    # Examples: {"title": "...", "author": "...", "date": "...", "tags": [...]}
    
    # Processing info
    processing_pipeline: List[str] = Field(default_factory=list)
    # e.g. ["codex_hunters.discover", "babel_gardens.comprehend", "chunker.split"]
    processing_time_ms: float = 0.0
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def validate_invariants(self) -> List[str]:
        violations = []
        if not self.chunks:
            violations.append("IngestionPayload must contain at least 1 chunk")
        if self.total_chunks != len(self.chunks):
            violations.append(
                f"total_chunks ({self.total_chunks}) != len(chunks) ({len(self.chunks)})"
            )
        if not self.source.source_id:
            violations.append("source.source_id must not be empty")
        if not self.quality.gate_passed:
            violations.append(
                f"quality gate not passed (score={self.quality.quality_score}, "
                f"threshold={self.quality.gate_threshold})"
            )
        return violations
```

#### 2.2.3 Ingestion Plugin (Domain Extension Point)

```python
class IIngestionPlugin(IContractPlugin):
    """
    Domain plugin for ingestion customization.
    
    Domains implement this to:
      - Define domain-specific source types
      - Add domain-specific metadata extraction
      - Customize quality gates (e.g., finance requires ticker validation)
      - Add domain-specific normalization rules
    """
    PLUGIN_CONTRACT_NAME = "ingestion_plugin"
    PLUGIN_CONTRACT_VERSION = "1.0.0"
    
    @abstractmethod
    def get_domain_name(self) -> str: ...
    
    @abstractmethod
    def get_accepted_source_types(self) -> List[SourceType]: ...
    
    @abstractmethod
    def extract_domain_metadata(self, raw_text: str, source: SourceDescriptor) -> Dict[str, Any]:
        """Extract domain-specific metadata from raw text."""
        ...
    
    @abstractmethod
    def get_quality_threshold(self) -> float:
        """Return minimum quality_score for this domain (default 0.3)."""
        ...
    
    def validate_source(self, source: SourceDescriptor) -> List[str]:
        """Optional domain-specific source validation. Returns violation messages."""
        return []
    
    def normalize_text(self, raw_text: str) -> str:
        """Optional domain-specific text normalization. Default: return unchanged."""
        return raw_text
```

#### 2.2.4 Helper Functions

```python
def build_source_id(uri: str, content_hash: str) -> str:
    """Deterministic source_id from URI + content hash."""
    ...

def build_chunk_id(source_id: str, chunk_index: int) -> str:
    """Deterministic chunk_id from source_id + index."""
    ...

def compute_content_hash(content: bytes) -> str:
    """SHA-256 of raw content bytes."""
    ...
```

### 2.3 Stream Events (Synaptic Conclave Integration)

Define channel constants for ingestion events (following dot notation convention):

```python
# In vitruvyan_core/contracts/ingestion.py or a dedicated events section

CHANNEL_INGESTION_ACQUIRED  = "perception.ingestion.acquired"    # SourceDescriptor
CHANNEL_INGESTION_NORMALIZED = "perception.ingestion.normalized" # IngestionPayload
CHANNEL_INGESTION_REJECTED  = "perception.ingestion.rejected"    # quality gate failed
CHANNEL_INGESTION_DUPLICATE = "perception.ingestion.duplicate"   # dedup detected
```

### 2.4 Files to Create/Modify

**Create**:
- `vitruvyan_core/contracts/ingestion.py` (~250L) — SourceType, SourceDescriptor, IngestionQuality, NormalizedChunk, IngestionPayload, IIngestionPlugin, helpers, channel constants

**Modify**:
- `vitruvyan_core/contracts/__init__.py` — export all ingestion types in `__all__`

**Create tests**:
- `tests/unit/contracts/test_ingestion_contract.py` (~250L):
  - Test SourceDescriptor creation and validation
  - Test IngestionQuality invariants (gate logic)
  - Test IngestionPayload invariants (chunks, source_id, quality gate)
  - Test NormalizedChunk strict schema (extra="forbid")
  - Test helper functions (build_source_id, build_chunk_id, compute_content_hash)
  - Test IIngestionPlugin default implementations
  - Test serialization roundtrip (to_dict → from_dict)
  - Test contract registry integration (auto-registration)
  - Test BaseContract.enforce() in strict and warn modes

---

## PART 3: Implementation Constraints

### 3.1 Non-Negotiable Rules

1. **LIVELLO 1 compliance**: ALL code in `vitruvyan_core/contracts/` is pure Python + Pydantic. NO `import httpx`, NO `import psycopg2`, NO `import redis`. Zero I/O.
2. **Backward compatibility**: Every existing `from contracts import X` MUST continue to work. Migration to BaseContract MUST NOT break existing code.
3. **`extra="forbid"` on BaseContract**: Inherited by all subclasses. Prevents field drift.
4. **Imports**: Use `from .base import BaseContract, ContractMeta, ContractRegistry, IContractPlugin` (relative imports within contracts/).
5. **No cross-Sacred-Order imports**: Contracts package MUST NOT import from `core.governance.*` or `services/`.
6. **Tests must pass**: Run `pytest tests/unit/contracts/ -v` — all green.

### 3.2 Existing Code to Read First

Before implementing, READ these files for context (import patterns, naming conventions, existing tests):

- `vitruvyan_core/contracts/__init__.py` (200L — current exports and lazy imports)
- `vitruvyan_core/contracts/pattern_weavers.py` (200L — best example of data + plugin contract)
- `vitruvyan_core/contracts/comprehension.py` (349L — most complex contract, 3-layer architecture)
- `vitruvyan_core/contracts/rag.py` (794L — dataclass-based, extensive validation)
- `vitruvyan_core/contracts/graph_response.py` (150L — channel-agnostic response contract)
- `vitruvyan_core/core/orchestration/contract_enforcement.py` (232L — @enforced decorator, NODE_CONTRACT_SPEC)
- `vitruvyan_core/core/orchestration/node_contracts_registry.py` (260L — NODE_CONTRACTS registry)

### 3.3 Style Guide

- Docstrings: Module-level (3-5 lines), class-level (purpose + invariants), method-level (Args/Returns/Raises)
- Type hints: ALL parameters and return types
- Constants: UPPER_SNAKE_CASE
- ClassVars: UPPER_SNAKE_CASE
- Pydantic models: `model_config = ConfigDict(extra="forbid")`
- Enums: `class X(str, Enum)` (string-serializable)
- `Field()` with `description=` for all non-obvious fields
- `default_factory=list` / `default_factory=dict` (never mutable defaults)

### 3.4 Implementation Order

```
Step 1: Create vitruvyan_core/contracts/base.py
         - BaseContract, ContractMeta, ContractRegistry, IContractPlugin
         - Unit tests: tests/unit/contracts/test_base_contract.py
         - Verify: pytest tests/unit/contracts/test_base_contract.py -v → all green

Step 2: Create vitruvyan_core/contracts/ingestion.py
         - SourceType, SourceDescriptor, IngestionQuality, NormalizedChunk
         - IngestionPayload, IIngestionPlugin, helpers, channels
         - ALL inheriting from BaseContract / IContractPlugin
         - Unit tests: tests/unit/contracts/test_ingestion_contract.py
         - Verify: pytest tests/unit/contracts/test_ingestion_contract.py -v → all green

Step 3: Update vitruvyan_core/contracts/__init__.py
         - Add exports for base.py and ingestion.py types
         - Verify: python3 -c "from contracts.base import BaseContract; print('✅')"
         - Verify: python3 -c "from contracts.ingestion import IngestionPayload; print('✅')"

Step 4: Migrate ONE existing contract to BaseContract (pattern_weavers.OntologyPayload)
         - Change: class OntologyPayload(BaseModel) → class OntologyPayload(BaseContract)
         - Add ClassVars: CONTRACT_NAME, CONTRACT_VERSION, CONTRACT_OWNER
         - Remove duplicate model_config (inherited from BaseContract)
         - Handle schema_version field → property that returns CONTRACT_VERSION
         - Verify: ALL existing tests still pass
         - Verify: pytest tests/ -k "pattern_weavers or ontology" -v → all green

Step 5: Migrate remaining contracts (graph_response, comprehension) to BaseContract
         - Same pattern as Step 4
         - Verify: pytest tests/ -v → all green (full suite)

Step 6: Commit
         git add -A
         git commit -m "feat(contracts): BaseContract + IngestionContract v1.0.0

         BaseContract:
         - Abstract foundation for all data contracts
         - ContractMeta, ContractRegistry, IContractPlugin
         - Auto-registration, versioning, enforce(), serialization

         IngestionContract:
         - SourceType, SourceDescriptor, IngestionQuality
         - NormalizedChunk, IngestionPayload, IIngestionPlugin
         - Quality gates, provenance chain, dedup by content hash
         - Stream channel constants (perception.ingestion.*)

         Migration:
         - OntologyPayload → BaseContract (backward compatible)
         - GraphResponseMin, SessionMin → BaseContract
         - ComprehensionResult → BaseContract

         Tests: N unit tests, all green"
```

### 3.5 Verification Checklist

```bash
# 1. BaseContract importable
cd vitruvyan-core
PYTHONPATH=vitruvyan_core python3 -c "
from contracts.base import BaseContract, ContractMeta, ContractRegistry, IContractPlugin
print('✅ BaseContract imports OK')
"

# 2. IngestionContract importable
PYTHONPATH=vitruvyan_core python3 -c "
from contracts.ingestion import IngestionPayload, SourceDescriptor, IngestionQuality
print('✅ IngestionContract imports OK')
"

# 3. Registry populated
PYTHONPATH=vitruvyan_core python3 -c "
from contracts.base import ContractRegistry
from contracts.ingestion import IngestionPayload, SourceDescriptor
print(f'Registered: {ContractRegistry.list_all()}')
assert ContractRegistry.is_registered('ingestion.payload'), '❌ Not registered'
print('✅ Registry OK')
"

# 4. Existing contracts still work
PYTHONPATH=vitruvyan_core python3 -c "
from contracts import OntologyPayload, GraphResponseMin, ComprehensionResult
p = OntologyPayload()
print(f'OntologyPayload contract_id: {p.contract_id()}')
print('✅ Backward compat OK')
"

# 5. Tests
pytest tests/unit/contracts/ -v
pytest tests/ -v  # full suite — no regressions

# 6. No forbidden imports in contracts/
grep -r "import httpx\|import psycopg2\|import redis\|import qdrant" vitruvyan_core/contracts/ && echo "❌ VIOLATION" || echo "✅ No forbidden imports"
```

---

## PART 4: Architecture Diagram

```
vitruvyan_core/contracts/
├── __init__.py              # Unified public API (all exports)
├── base.py                  # NEW: BaseContract, ContractMeta, ContractRegistry, IContractPlugin
├── ingestion.py             # NEW: SourceType, SourceDescriptor, IngestionQuality,
│                            #      NormalizedChunk, IngestionPayload, IIngestionPlugin
├── graph_response.py        # MODIFIED: GraphResponseMin(BaseContract), SessionMin(BaseContract)
├── pattern_weavers.py       # MODIFIED: OntologyPayload(BaseContract), ISemanticPlugin(IContractPlugin)
├── comprehension.py         # MODIFIED: ComprehensionResult(BaseContract), IComprehensionPlugin(IContractPlugin)
├── rag.py                   # UNCHANGED (dataclass pattern — future migration)
├── llm_provider.py          # UNCHANGED (Protocol pattern)
├── orchestration.py         # UNCHANGED (re-export shim)
├── README.md                # UPDATED: document BaseContract pattern
└── neural_engine/           # UNCHANGED
    ├── __init__.py
    ├── data_provider.py
    ├── filter_strategy.py
    └── scoring_strategy.py

tests/unit/contracts/
├── test_base_contract.py    # NEW: ~200L
└── test_ingestion_contract.py # NEW: ~250L
```

### Data Flow After Implementation

```
External Source
      │
      ▼
[SourceDescriptor]         ← Perception acquires, creates provenance
      │
      ▼
[Normalization Pipeline]   ← Babel Gardens comprehend, Codex Hunters discover
      │
      ▼
[IngestionQuality]         ← Quality gate assessment
      │
      ├─ gate_passed=False → CHANNEL_INGESTION_REJECTED (stream event)
      │
      ▼
[IngestionPayload]         ← Canonical output: source + quality + chunks
      │
      ├─ duplicate_of != None → CHANNEL_INGESTION_DUPLICATE (stream event)
      │
      ▼
CHANNEL_INGESTION_NORMALIZED → Memory Orders receive, embed, store
```

---

## Notes for Copilot

- The `@enforced` decorator and `BaseContract.enforce()` are **complementary**, not competing patterns. `@enforced` guards node I/O (state dict fields). `BaseContract.enforce()` guards payload CONTENT (Pydantic model invariants). Both can fire on the same data flow.
- `IContractPlugin` is intentionally lighter than `BaseContract` — it only adds metadata, not Pydantic validation, because plugin interfaces are ABCs with method contracts, not data schemas.
- The `ContractRegistry` uses `__init_subclass__` for auto-registration. This means importing any module that defines a `BaseContract` subclass automatically registers it — no manual wiring needed.
- Channel constants (CHANNEL_INGESTION_*) follow the existing Synaptic Conclave dot notation: `<order>.<domain>.<action>`. "perception" is the order; "ingestion" is the domain.
- `NormalizedChunk` does NOT inherit from `BaseContract` — it's a sub-model (nested inside `IngestionPayload`). Only top-level contracts get `CONTRACT_NAME`/`CONTRACT_VERSION`.
