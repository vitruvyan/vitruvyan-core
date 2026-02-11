# Codex Hunters — Domain-Agnostic Refactoring Plan
**Epistemic Re-Foundation: From Finance-Locked to Universal Data Acquisition**

**Date**: February 11, 2026  
**Status**: Planning Phase  
**Objective**: Transform Codex Hunters from finance-specific ingestion layer to domain-agnostic data acquisition & normalization engine

---

## Executive Summary

**Current State (95% Conformance — INCOMPLETE)**:
- ✅ SACRED_ORDER_PATTERN structure (10 directories)
- ✅ LIVELLO 1/2 separation (main.py: 75 lines ✅)
- ❌ **Domain leakage**: Finance-specific channels, ticker assumptions, yfinance defaults
- ❌ **Boundary violations**: Risk analysis inside ingestion layer (VARE/Cassandra)
- ❌ **Micelial violations**: Pub/Sub legacy, direct HTTP cross-service calls
- ❌ **Config violations**: Hardcoded thresholds, non-deterministic dedupe
- ❌ **Provider coupling**: Qdrant shape assumptions in LIVELLO 1

**Target State (100% Domain-Agnostic)**:
- **Pure Epistemic Mandate**: "Canonical Data Acquisition & Normalization Order"
- **YAML-Driven Configuration**: entity → entity_id, source → configurable, data_category → pluggable
- **Streams-Only Communication**: Zero Pub/Sub, zero HTTP cross-service, micelial-native
- **Deterministic Operations**: Hash-based dedupe (no date-based keys)
- **Provider-Agnostic Core**: LIVELLO 1 returns CanonicalEntityRecord, NOT Qdrant upsert payload

---

## Critical Violations Identified (From Due Diligence)

### 1. Domain Leakage (Finance Contamination)

**LIVELLO 1 (Core Domain)**:
```python
# ❌ VIOLATION: vitruvyan_core/core/governance/codex_hunters/domain/config.py:76
config = CodexConfig(
    entity_table=TableConfig(name="tickers"),  # ❌ finance-specific
    embedding_collection=CollectionConfig(name="ticker_embeddings"),  # ❌
    streams=StreamConfig(prefix="codex.finance")  # ❌
)
```

**LIVELLO 2 (Service Layer)**:
```python
# ❌ VIOLATION: services/api_codex_hunters/streams_listener.py:11
self.sacred_channels = [
    "codex.technical.momentum.requested",   # ❌ finance taxonomy
    "codex.technical.trend.requested",      # ❌
    "codex.fundamentals.refresh.requested", # ❌
]
```

**Legacy Listener**:
```python
# ❌ VIOLATION: vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py:161
payload = json.loads(data.decode('utf-8'))
tickers = payload.get('tickers', [])        # ❌ privileged entity type
sources = payload.get('sources', ['yfinance'])  # ❌ finance default
```

### 2. Epistemic Boundary Violations

**Risk Analysis Inside Ingestion Layer**:
```python
# ❌ VIOLATION: listeners/codex_hunters.py:60
"codex.risk.refresh.requested"  # ❌ Risk scoring ≠ data acquisition

# ❌ VIOLATION: listeners/codex_hunters.py:234
async def handle_vare_risk_analysis(self, data: bytes):
    from core.codex_hunters.cassandra import Cassandra  # ❌ WRONG ORDER
    cassandra = Cassandra()
    result = cassandra.execute(tickers=tickers)  # ❌ Risk scoring in Codex Hunters
```

**Sacred Order Epistemic Layers** (must not overlap):
- **Codex Hunters** → Data Acquisition & Normalization (Perception)
- **Neural Engine** → Scoring & Interpretation (Reason)
- **Pattern Weavers** → Ontology Resolution (Reason)
- **Babel Gardens** → Signal Extraction (Perception)

**Violation**: Codex Hunters performs VARE risk scoring (Neural Engine responsibility)

### 3. Micelial Integration Violations

**Pub/Sub Legacy** (must be Streams-only):
```python
# ❌ VIOLATION: listeners/codex_hunters.py:93
self.pubsub = self.redis_client.pubsub()
await self.pubsub.subscribe(channel)  # ❌ Pub/Sub, not Streams

# ❌ VIOLATION: listeners/codex_hunters.py:289
await self.redis_client.publish(  # ❌ Pub/Sub emission
    "codex.expedition.completed",
    json.dumps(event)
)
```

**Direct HTTP Cross-Service Calls**:
```python
# ❌ VIOLATION: vitruvyan_core/core/orchestration/langgraph/node/codex_hunters_node.py:213
response = httpx.post(
    f"{CODEX_API_BASE}/expedition/run",  # ❌ Direct HTTP, not Streams
    json={"tickers": tickers}
)
```

### 4. Configuration Violations

**Hardcoded Thresholds**:
```python
# ❌ VIOLATION: consumers/restorer.py:129
quality_threshold = 0.5  # ❌ Hardcoded (not in CodexConfig)

# ❌ VIOLATION: consumers/restorer.py:240
quality_score -= len(errors) * 0.1  # ❌ Hardcoded weight
quality_score -= null_ratio * 0.3   # ❌ Hardcoded weight
```

**Non-Deterministic Dedupe**:
```python
# ❌ VIOLATION: consumers/tracker.py:159
# Charter says: "dedupe key is deterministic based on entity_id + source + data hash"
dedupe_key = f"{entity_id}:{source}:{datetime.now().date()}"  # ❌ Uses current date!
# This breaks determinism: same entity on different days = different key
```

### 5. Provider Coupling (LIVELLO 1)

**Qdrant Shape Assumptions**:
```python
# ❌ VIOLATION: consumers/binder.py:208
def _prepare_qdrant_payload(self, ...):
    return {
        "id": embedding_id,        # ❌ Qdrant-specific "point" structure
        "vector": embedding,       # ❌
        "payload": {...}           # ❌
    }
# LIVELLO 1 should return CanonicalEntityRecord, NOT Qdrant upsert dict
```

### 6. Contract Drift (LIVELLO 1 ↔ LIVELLO 2)

**Mismatched Field Names**:
```python
# ❌ VIOLATION: adapters/bus_adapter.py:113
event = {
    "source_type": source_type,  # Service layer sends "source_type"
}

# ❌ VIOLATION: consumers/tracker.py:64
source = data.get("source")  # LIVELLO 1 expects "source"
# Result: Pipeline fails at boundary
```

**Non-Existent Constants**:
```python
# ❌ VIOLATION: adapters/bus_adapter.py:129
self.bus.emit(Channels.DISCOVERED, result)  # ❌ Channels.DISCOVERED doesn't exist

# ✅ events/__init__.py:37 only has:
class Channels:
    DISCOVERY_REQUEST = "codex.discovery.request"
    # ... but NO "DISCOVERED" constant
```

---

## Refactoring Strategy (7-Phase Commit Plan)

### Phase 1: Remove Risk Path (Epistemic Boundary Enforcement)

**Objective**: Eliminate VARE/Cassandra risk analysis from Codex Hunters

**Files to modify**:
- `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py`
  - Remove `"codex.risk.refresh.requested"` from `sacred_channels` (line 60)
  - Delete `handle_vare_risk_analysis()` method (lines 234-251)
  - Delete `publish_vare_completed()` method (lines 253-274)

**Commit message**:
```
refactor(codex_hunters): remove risk scoring (epistemic boundary enforcement)

CRITICAL SEPARATION:
- Codex Hunters = Data Acquisition (Perception)
- Neural Engine = Risk Scoring (Reason)

Changes:
- Removed codex.risk.refresh.requested channel
- Deleted handle_vare_risk_analysis() (VARE/Cassandra)
- Deleted publish_vare_completed()

Rationale: Risk analysis violates Codex Hunters' epistemic mandate.
VARE scoring belongs in Neural Engine, communicated via Streams.

Test: Listener starts without risk channel subscriptions
```

### Phase 2: Eliminate Pub/Sub (Micelial Enforcement)

**Objective**: Convert ALL communication to Redis Streams (zero Pub/Sub)

**Files to modify**:
- `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py`
  - Replace `redis.pubsub()` with `StreamBus` consumer groups
  - Replace `await self.pubsub.subscribe()` with `bus.create_consumer_group()`
  - Replace `await self.redis_client.publish()` with `bus.emit()`
  - Use generator pattern: `for event in bus.consume(...)`

**Before**:
```python
# ❌ Pub/Sub
self.pubsub = self.redis_client.pubsub()
await self.pubsub.subscribe("codex.data.refresh.requested")
await self.redis_client.publish("codex.expedition.completed", json.dumps(event))
```

**After**:
```python
# ✅ Streams
from core.synaptic_conclave.transport.streams import StreamBus

bus = StreamBus()
bus.create_consumer_group("codex.data.refresh", "codex_hunters", mkstream=True)

for event in bus.consume("codex.data.refresh", "codex_hunters", "worker_1"):
    handle(event)
    bus.acknowledge(event.stream, "codex_hunters", event.event_id)

# Emit
bus.emit("codex.expedition.completed", {"status": "success"})
```

**Commit message**:
```
refactor(codex_hunters): Pub/Sub → Redis Streams (micelial enforcement)

MICELIAL INTEGRATION:
- Replaced redis.pubsub() with StreamBus consumer groups
- Replaced publish() with bus.emit()
- Generator consumption pattern with acknowledge()

Changes:
- listeners/codex_hunters.py: StreamBus integration (Pub/Sub eliminated)
- streams_listener.py: Streams-native event consumption

Test: Grafana Synaptic Conclave dashboard shows Streams activity
```

### Phase 3: Remove Direct HTTP Calls (Event-Driven Dispatch)

**Objective**: Replace HTTP cross-service calls with event emission

**Files to modify**:
- `vitruvyan_core/core/orchestration/langgraph/node/codex_hunters_node.py`
  - Replace `httpx.post(f"{CODEX_API_BASE}/expedition/run")` with event emission
  - Remove `CODEX_API_BASE` env var dependency

**Before**:
```python
# ❌ Direct HTTP
response = httpx.post(
    f"{CODEX_API_BASE}/expedition/run",
    json={"tickers": tickers}
)
```

**After**:
```python
# ✅ Event emission
from core.synaptic_conclave.transport.streams import StreamBus

bus = StreamBus()
bus.emit("codex.expedition.request", {
    "entities": entities,  # NOT "tickers"
    "sources": sources,
    "correlation_id": state.get("correlation_id")
})

# Wait for response via Streams (optional: use consume() with timeout)
```

**Commit message**:
```
refactor(langgraph): remove HTTP calls to Codex Hunters (event-driven dispatch)

INTER-ORDER COMMUNICATION:
- LangGraph → Codex Hunters via Redis Streams ONLY
- Eliminated direct HTTP POST to /expedition/run

Changes:
- node/codex_hunters_node.py: emit codex.expedition.request event
- Removed CODEX_API_BASE dependency

Test: LangGraph orchestration completes without HTTP calls
```

### Phase 4: Generalize Entity Identity (Domain-Agnostic Primitives)

**Objective**: Replace finance-specific terminology with neutral primitives

**Vocabulary Mapping**:
| Finance Term | Neutral Primitive |
|--------------|-------------------|
| `tickers` | `entity_ids` |
| `ticker` | `entity_id` |
| `yfinance` | `source` (configurable) |
| `fundamentals` | `structured_attributes` |
| `technical.*` | `metric_type` |
| `codex.finance.*` | `codex.*` (domain as metadata) |

**Files to modify**:
- `vitruvyan_core/core/governance/codex_hunters/domain/config.py`
  - Remove "Finance domain override" example (lines 76-81)
  - Update docstrings to reference "entities" not "tickers"

- `vitruvyan_core/core/governance/codex_hunters/README.md`
  - Change Quick Start example: `AAPL` → `entity_123`
  - Replace "ticker" references with "entity_id"

- `vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py`
  - Rename `tickers` parameter → `entity_ids`
  - Remove `yfinance` default → require `sources` in config

- `services/api_codex_hunters/streams_listener.py`
  - Remove finance-specific channel names:
    - `codex.technical.momentum.requested` → `codex.metric.request` (generic)
    - `codex.fundamentals.refresh.requested` → `codex.attributes.request`

**Commit message**:
```
refactor(codex_hunters): generalize entity identity (domain-agnostic primitives)

VOCABULARY TRANSFORMATION:
- tickers → entity_ids
- yfinance → configurable source
- fundamentals → structured_attributes
- technical.* → metric_type (YAML-driven)

Changes:
- domain/config.py: Removed finance example
- README.md: Entity-neutral quick start
- listeners/*.py: Neutral terminology
- streams_listener.py: Generic channel names

Test: Examples run with non-finance entities (medical_record_789, vessel_ABC123)
```

### Phase 5: Fix Dedupe Determinism (Charter Compliance)

**Objective**: Honor charter invariant: "dedupe key is deterministic based on entity_id + source + data hash"

**Files to modify**:
- `vitruvyan_core/core/governance/codex_hunters/consumers/tracker.py:159`

**Before**:
```python
# ❌ NON-DETERMINISTIC (uses current date)
dedupe_key = f"{entity_id}:{source}:{datetime.now().date()}"
```

**After**:
```python
# ✅ DETERMINISTIC (hash-based)
import hashlib
import json

data_hash = hashlib.sha256(
    json.dumps(raw_data, sort_keys=True, default=str).encode()
).hexdigest()[:16]

dedupe_key = f"{entity_id}:{source}:{data_hash}"
```

**Commit message**:
```
fix(codex_hunters): deterministic dedupe key (charter compliance)

CHARTER INVARIANT:
"Dedupe key is deterministic based on entity_id + source + data hash."

VIOLATION:
Current implementation uses datetime.now().date() → non-deterministic.
Same entity on different days = different keys = duplicates.

FIX:
Hash-based key using SHA256(raw_data) → stable across time.

Changes:
- consumers/tracker.py:159: data hash-based dedupe key

Test: Same entity + source + data = same dedupe key (any timestamp)
```

### Phase 6: Decouple Provider Shape (Abstract Storage Contract)

**Objective**: LIVELLO 1 returns domain objects, NOT provider-specific payloads

**Files to modify**:
- `vitruvyan_core/core/governance/codex_hunters/consumers/binder.py`

**Current (VIOLATION)**:
```python
# ❌ LIVELLO 1 returns Qdrant-specific dict
def _prepare_qdrant_payload(self, ...):
    return {
        "id": embedding_id,    # Qdrant "point" schema
        "vector": embedding,
        "payload": {...}
    }
```

**Refactored**:
```python
# ✅ LIVELLO 1 returns domain object
@dataclass(frozen=True)
class CanonicalEntityRecord:
    entity_id: str
    source: str
    attributes: Dict[str, Any]
    embedding: Optional[List[float]]
    quality_score: float
    storage_metadata: Dict[str, str]  # Generic, NOT Qdrant-specific

def process(self, data) -> ProcessResult:
    return ProcessResult(
        success=True,
        data={"canonical_record": CanonicalEntityRecord(...)}
    )

# LIVELLO 2 adapters/persistence.py converts to provider shape:
def store_entity(self, record: CanonicalEntityRecord):
    # PostgreSQL insert
    self.pg.execute(...)
    
    # Qdrant upsert (shape conversion in adapter, NOT consumer)
    self.qdrant.upsert(
        collection_name=self.config.collection,
        points=[{
            "id": record.entity_id,
            "vector": record.embedding,
            "payload": record.attributes
        }]
    )
```

**Commit message**:
```
refactor(codex_hunters): decouple Qdrant shape from LIVELLO 1 (provider-agnostic core)

ABSTRACTION VIOLATION:
LIVELLO 1 (pure domain) returned Qdrant-specific "point" dict.
This couples core logic to a specific vector DB provider.

FIX:
- LIVELLO 1: Returns CanonicalEntityRecord (domain object)
- LIVELLO 2: adapters/persistence.py converts to provider shape

Changes:
- domain/entities.py: CanonicalEntityRecord dataclass
- consumers/binder.py: Returns domain object, NOT Qdrant dict
- adapters/persistence.py: Provider shape conversion

Test: LIVELLO 1 consumers import without Qdrant dependency
```

### Phase 7: YAML-Driven Thresholds & Configuration Injection

**Objective**: Move ALL hardcoded values to configuration (YAML-driven)

**Files to modify**:
- `vitruvyan_core/core/governance/codex_hunters/domain/config.py`
  - Add `quality_threshold`, `dedupe_enabled`, `quality_weights` to `CodexConfig`

- `vitruvyan_core/core/governance/codex_hunters/consumers/restorer.py`
  - Replace hardcoded `0.5`, `0.1`, `0.3` with `config.quality_*`

**CodexConfig additions**:
```python
@dataclass
class QualityConfig:
    threshold: float = 0.5
    error_weight: float = 0.1
    null_penalty_weight: float = 0.3

@dataclass
class CodexConfig:
    quality: QualityConfig = field(default_factory=QualityConfig)
    dedupe_enabled: bool = True
    # ...existing fields
```

**Consumer update**:
```python
# Before
quality_threshold = 0.5  # ❌ Hardcoded

# After
quality_threshold = self.config.quality.threshold  # ✅ Config-driven
```

**YAML example** (`config/codex_hunters_finance.yaml`):
```yaml
quality:
  threshold: 0.7  # Finance requires higher quality
  error_weight: 0.15
  null_penalty_weight: 0.25

sources:
  - name: yfinance
    rate_limit: 60
  - name: alpha_vantage
    rate_limit: 5

entity_table:
  name: tickers
  schema: finance

embedding_collection:
  name: ticker_embeddings
  vector_size: 384
```

**Commit message**:
```
refactor(codex_hunters): YAML-driven configuration (eliminate hardcoded values)

CONFIGURATION PARADIGM:
All domain-specific values → YAML configuration files.
No hardcoded thresholds, weights, or defaults in core consumers.

Changes:
- domain/config.py: QualityConfig, configurable thresholds
- consumers/restorer.py: Use config.quality.* (not hardcoded 0.5/0.1/0.3)
- examples/config_finance.yaml: Finance-specific configuration
- examples/config_healthcare.yaml: Healthcare-specific configuration

Test: Load different YAML configs → different behavior (no code changes)
```

---

## Domain-Agnostic Configuration Examples

### Finance Vertical
**config/codex_finance.yaml**:
```yaml
metadata:
  vertical: finance
  version: "2.0.0"

entity_table:
  name: tickers
  schema: finance
  primary_key: ticker_id

embedding_collection:
  name: ticker_embeddings
  vector_size: 384

sources:
  - name: yfinance
    rate_limit: 60
    timeout: 30
  - name: alpha_vantage
    rate_limit: 5
    timeout: 60

streams:
  prefix: codex.finance
  channels:
    - name: attributes.request
      description: "Fundamentals extraction"
    - name: metrics.request
      description: "Technical indicators"

quality:
  threshold: 0.7
  error_weight: 0.15
  null_penalty_weight: 0.25
```

### Healthcare Vertical
**config/codex_healthcare.yaml**:
```yaml
metadata:
  vertical: healthcare
  version: "2.0.0"

entity_table:
  name: medical_records
  schema: healthcare
  primary_key: record_id

embedding_collection:
  name: medical_embeddings
  vector_size: 768  # BioClinicalBERT

sources:
  - name: fhir_api
    rate_limit: 100
    timeout: 45
  - name: hl7_feed
    rate_limit: 1000
    timeout: 10

streams:
  prefix: codex.healthcare
  channels:
    - name: diagnoses.request
      description: "ICD-10 diagnosis extraction"
    - name: treatments.request
      description: "Treatment protocol retrieval"

quality:
  threshold: 0.95  # Healthcare requires higher confidence
  error_weight: 0.5  # Errors are critical
  null_penalty_weight: 0.8
```

### Cybersecurity Vertical
**config/codex_cybersecurity.yaml**:
```yaml
metadata:
  vertical: cybersecurity
  version: "2.0.0"

entity_table:
  name: threat_indicators
  schema: security
  primary_key: ioc_id

embedding_collection:
  name: threat_embeddings
  vector_size: 384

sources:
  - name: misp_feed
    rate_limit: 1000
    timeout: 15
  - name: mitre_attack
    rate_limit: 60
    timeout: 30

streams:
  prefix: codex.cybersecurity
  channels:
    - name: cve.request
      description: "CVE data enrichment"
    - name: ioc.request
      description: "Indicator of Compromise extraction"

quality:
  threshold: 0.6
  error_weight: 0.1
  null_penalty_weight: 0.2
```

---

## Verification Checklist

**After each phase, run**:

### LIVELLO 1 (Pure Domain)
```bash
# 1. No finance-specific terms in code
rg "ticker|yfinance|fundamentals|technical\.(momentum|trend)" vitruvyan_core/core/governance/codex_hunters/ --glob "!_legacy/*" --glob "!*.md"
# Expected: 0 matches (only in docs/examples as EXAMPLES)

# 2. Pure consumer import (no I/O dependencies)
python3 -c "from core.governance.codex_hunters.consumers import TrackerConsumer, RestorerConsumer, BinderConsumer; print('✅ Pure')"
# Expected: ✅ Pure (no errors, no Qdrant/Postgres imports)

# 3. No Pub/Sub in listeners
rg "redis.*pubsub|\.subscribe\(|\.publish\(" vitruvyan_core/core/synaptic_conclave/listeners/codex_hunters.py
# Expected: 0 matches

# 4. Deterministic dedupe
python3 -c "
from core.governance.codex_hunters.consumers.tracker import TrackerConsumer
import hashlib, json

# Same entity, same data → same key
entity_id = 'test_entity'
source = 'test_source'
raw_data = {'field': 'value'}

tracker = TrackerConsumer()
result1 = tracker.process({'entity_id': entity_id, 'source': source, 'raw_data': raw_data})
result2 = tracker.process({'entity_id': entity_id, 'source': source, 'raw_data': raw_data})

assert result1.data['dedupe_key'] == result2.data['dedupe_key'], 'Dedupe NOT deterministic!'
print('✅ Dedupe deterministic')
"

# 5. No Qdrant shape in consumer output
rg "\"id\".*embedding_id|\"vector\".*embedding|\"payload\"" vitruvyan_core/core/governance/codex_hunters/consumers/binder.py
# Expected: 0 matches (returns CanonicalEntityRecord, not Qdrant dict)
```

### LIVELLO 2 (Service Layer)
```bash
# 1. main.py size < 100 lines
wc -l services/api_codex_hunters/main.py
# Expected: < 100

# 2. No HTTP calls in LangGraph
rg "httpx\.post|requests\.post" vitruvyan_core/core/orchestration/langgraph/node/codex_hunters_node.py
# Expected: 0 matches

# 3. StreamBus-only communication
rg "StreamBus|bus\.emit|bus\.consume" services/api_codex_hunters/adapters/bus_adapter.py
# Expected: Multiple matches (Streams-native)

# 4. No risk channels
rg "codex\.risk\." services/api_codex_hunters/streams_listener.py
# Expected: 0 matches
```

### Integration Tests
```bash
# 1. Load finance config
python3 -c "
from core.governance.codex_hunters.domain.config import CodexConfig
import yaml

with open('config/codex_finance.yaml') as f:
    config_data = yaml.safe_load(f)

# Config should load without errors
print('✅ Finance config loaded')
"

# 2. Load healthcare config (different vertical)
python3 -c "
from core.governance.codex_hunters.domain.config import CodexConfig
import yaml

with open('config/codex_healthcare.yaml') as f:
    config_data = yaml.safe_load(f)

print('✅ Healthcare config loaded')
"

# 3. Process non-finance entity
python3 -c "
from core.governance.codex_hunters.consumers import TrackerConsumer

tracker = TrackerConsumer()
result = tracker.process({
    'entity_id': 'medical_record_12345',
    'source': 'fhir_api',
    'raw_data': {'patient_id': 'P-001', 'diagnosis': 'J44.1'}
})

assert result.success, 'Healthcare entity processing failed!'
print('✅ Healthcare entity processed')
"
```

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Domain leakage (finance terms in core) | 47 matches | 0 matches |
| LIVELLO 1 provider coupling | Qdrant dict output | CanonicalEntityRecord |
| micelial compliance | Pub/Sub + HTTP | Streams-only ✅ |
| Dedupe determinism | Date-based (❌) | Hash-based ✅ |
| Config hardcoding | 7+ hardcoded values | 0 (YAML-driven) |
| Epistemic boundary violations | Risk in ingestion | Zero overlaps ✅ |
| Vertical flexibility | Finance-only | ANY (healthcare, cyber, maritime) |

---

## Timeline

| Phase | Estimated Duration | Complexity |
|-------|-------------------|------------|
| Phase 1: Remove Risk Path | 30 min | LOW (delete code) |
| Phase 2: Eliminate Pub/Sub | 2 hours | MEDIUM (StreamBus migration) |
| Phase 3: Remove HTTP Calls | 1 hour | LOW (event emission) |
| Phase 4: Generalize Entity Identity | 1.5 hours | MEDIUM (vocabulary refactor) |
| Phase 5: Fix Dedupe Determinism | 30 min | LOW (hash implementation) |
| Phase 6: Decouple Provider Shape | 2 hours | HIGH (abstraction redesign) |
| Phase 7: YAML Configuration | 1.5 hours | MEDIUM (config injection) |

**Total**: ~9 hours (1-2 days with testing)

---

## Rollback Strategy

**If refactoring breaks production**:
1. **LIVELLO 2 rollback**: `docker compose down codex_hunters && docker compose up -d codex_hunters` (service restart uses old image)
2. **Git rollback**: `git revert <commit_sha>` (revert specific phase)
3. **Legacy activation**: Restore `_legacy/` files to main directory (temporary bridge)

**Canary deployment**:
- Phase 1-3: Deploy to staging ONLY
- Phase 4-5: Gradual rollout (50% traffic)
- Phase 6-7: Full production after 48h observation

---

## Post-Refactoring Validation

**Deploy new verticals to prove agnosticism**:

### Vertical 1: Healthcare (ICD-10 Diagnoses)
```yaml
# config/codex_healthcare.yaml
entity_table: {name: medical_records}
sources: [{name: fhir_api, rate_limit: 100}]
streams: {prefix: codex.healthcare}
```

**Test**: Process `medical_record_789` from `fhir_api` → verify PostgreSQL + Qdrant storage

### Vertical 2: Maritime (Vessel Tracking)
```yaml
# config/codex_maritime.yaml
entity_table: {name: vessels}
sources: [{name: ais_feed, rate_limit: 1000}]
streams: {prefix: codex.maritime}
```

**Test**: Process `vessel_IMO_9876543` from `ais_feed` → verify entity discovery

### Vertical 3: Cybersecurity (Threat Intel)
```yaml
# config/codex_cybersecurity.yaml
entity_table: {name: threat_indicators}
sources: [{name: misp_feed, rate_limit: 500}]
streams: {prefix: codex.cybersecurity}
```

**Test**: Process `CVE-2024-1234` from `misp_feed` → verify quality scoring

**Success Criteria**: All 3 verticals process entities WITHOUT code changes (config-only deployment)

---

## Conclusion

This refactoring transforms Codex Hunters from a **finance-specific data collector** to a **universal data acquisition engine**. The system becomes:

1. **Epistemically Pure**: Ingestion ≠ Interpretation (no risk scoring)
2. **Micelial-Native**: Streams-only communication (zero Pub/Sub, zero HTTP)
3. **Domain-Agnostic**: YAML-driven configuration (finance, healthcare, cybersecurity, maritime)
4. **Provider-Agnostic**: Core logic independent of PostgreSQL/Qdrant/embedding vendors
5. **Deterministic**: Hash-based dedupe, reproducible operations
6. **Testable**: LIVELLO 1 imports without I/O dependencies

**This is not a cleanup. This is an epistemic re-foundation.**
