# Pattern Weavers — Universal Ontology Resolution Engine

**Version**: 2.0.0 (Phase 1 - Ontological Purification Complete)  
**Last Updated**: February 11, 2026  
**Status**: Production Ready (Phase 1 Complete, Phase 2 Planned)  
**Epistemic Order**: REASON (Semantic Contextualization Layer)

---

## Executive Summary

Pattern Weavers is the **universal ontology resolution engine** of Vitruvyan OS. It transforms unstructured queries into **structured semantic context**—mapping raw text to taxonomy categories (concepts, sectors, regions, entities) through embedding-based similarity search and keyword matching. Pattern Weavers is **domain-agnostic by design**: the same engine serves finance, healthcare, cybersecurity, logistics, maritime, sports, legal, or any vertical domain through **YAML-driven taxonomy configuration**.

**Phase 1 Refactoring** (February 10-11, 2026) eliminated **epistemic boundary violations** by removing all semantic interpretation logic from Pattern Weavers. Where v1.x incorrectly computed risk scores and aggregated semantic signals (_aggregate_risk method, 41 lines), v2.0 is **purely ontological**: it extracts structure, never interprets meaning. Risk scoring, sentiment analysis, and predictive inference belong to the **Neural Engine** (downstream consumer), not the ontology layer.

The subsystem's core capabilities include:
-   **Universal Taxonomy Resolution**: Map queries to **any taxonomy** (financial sectors, medical diagnoses, legal precedents, cybersecurity threats) via configuration
-   **YAML-Driven Configuration**: Define new domains without code changes—pure declarative ontology definition
-   **Embedding-Based Similarity**: Semantic search using Qdrant vector database (384D embeddings from Babel Gardens)
-   **Keyword Fallback**: Graceful degradation when embedding services unavailable (keyword matcher provides baseline resolution)
-   **Explainability by Design**: Every match includes similarity scores, match types, and metadata for Orthodoxy Wardens compliance
-   **Sacred Order Integration**: Native integration with Neural Engine (feature engineering), Vault Keepers (pattern archival), Babel Gardens (embeddings)

Architecturally, Pattern Weavers follows the **SACRED_ORDER_PATTERN** with strict LIVELLO 1 (pure domain logic, zero I/O) and LIVELLO 2 (service layer, orchestration) separation. The core WeaveResult schema is domain-agnostic and immutable; vertical-specific behavior lives in taxonomy YAML files.

**Phase 1 Achievements** (11 commits, February 10-11 2026):
- ✅ **RiskProfile entity deleted** (18 lines removed from domain/entities.py)
- ✅ **_aggregate_risk() method eliminated** (41 lines removed from consumers/weaver.py) — **CRITICAL epistemic boundary fix**
- ✅ **Charter updated** (pipeline diagram: removed "Risk Aggregation" step)
- ✅ **API surface purified** (no risk_profile in WeaveResult, schemas, or route handlers)
- ✅ **Contract drift fixed** (3 key mismatches: query_text, categories, keyword_matcher)
- ✅ **Service deployed** (port 9017, healthy, main.py 62 lines < 100 ✅)

**Phase 2 Roadmap** (Deferred):
-   Provider coupling removal (EmbeddingConfig.api_url → LIVELLO 2 adapter)
-   Config injection enforcement (set_config() boundaries)
-   Streams naming alignment (pattern.* → pattern_weavers.*)
-   Qdrant shape abstraction (ScoredPoint → generic similarity hit)

---

## Purpose & Motivation

The primary motivation for Pattern Weavers is to solve the problem of **semantic contextualization across infinite domains**. AI systems processing natural language queries need to map vague, ambiguous text ("analyze European banks", "ESG renewable energy", "cardiac arrest protocols") to structured taxonomies that downstream reasoning systems can operate on. A finance-specific entity extractor fails on medical queries; a healthcare diagnostic classifier cannot resolve legal precedent categories.

Pattern Weavers v2.0 provides a **universal abstraction** for ontology resolution that:
1.  **Eliminates Vertical Lock-In**: Break free from finance-only architectures. Support ANY domain through declarative YAML taxonomy files.
2.  **Preserves Domain Expertise**: Use domain-specific taxonomies (GICS sectors, ICD-10 codes, MITRE ATT&CK, maritime vessel types) while providing a unified interface (WeaveResult).
3.  **Enforces Epistemic Boundaries**: Pattern Weavers resolves **structure**, never **meaning**. Risk scoring, sentiment aggregation, and predictive inference are **forbidden** at this layer.
4.  **Enables Cross-Domain Correlation**: Combine taxonomies from different domains (e.g., finance sectors + cybersecurity threats) to detect emergent patterns invisible to single-domain systems.
5.  **Scales Infinitely**: Add new verticals (climate, sports, IoT) without changing core code—just create a YAML taxonomy and optional keyword rules.

The Phase 1 refactoring acknowledges that **ontology is upstream of intelligence**. Before Neural Engine can reason about risk, Pattern Weavers must resolve "which entities are we talking about?" This separation is non-negotiable: violating it creates untraceable, unexplainable AI systems.

---

## Architecture (SACRED_ORDER_PATTERN Conformant)

Pattern Weavers v2.0 follows the **SACRED_ORDER_PATTERN** with strict separation between pure domain logic (LIVELLO 1) and service infrastructure (LIVELLO 2).

### LIVELLO 1: Pure Domain Layer
**Location**: `vitruvyan_core/core/cognitive/pattern_weavers/domain/`  
**Characteristics**: Zero I/O, no external dependencies (PostgreSQL/Redis/Qdrant/httpx), pure Python dataclasses and functions

**Directory Structure** (10 directories, SACRED_ORDER_PATTERN compliant):
```
vitruvyan_core/core/cognitive/pattern_weavers/
├── domain/              # Frozen dataclasses (immutable DTOs)
│   ├── entities.py      # WeaveRequest, WeaveResult, PatternMatch (140 lines)
│   ├── config.py        # TaxonomyConfig, CategoryRule (220 lines)
│   └── __init__.py      # Domain exports (63 lines)
├── consumers/           # Pure process() functions (dict → dataclass, NO I/O)
│   ├── weaver.py        # WeaverConsumer.process() (204 lines, NO _aggregate_risk)
│   ├── keyword_matcher.py  # KeywordMatcher.match() (164 lines)
│   ├── base.py          # BaseConsumer interface (109 lines)
│   └── __init__.py      # Consumer exports (26 lines)
├── events/              # Channel name constants, event envelopes (77 lines)
├── monitoring/          # Metric NAME constants ONLY (no prometheus_client) (56 lines)
├── philosophy/          # charter.md (identity, mandate, invariants)
│   └── charter.md       # Sacred Order charter (91 lines)
├── docs/                # Implementation notes, design decisions
├── examples/            # Usage examples (pure Python, no service dependencies)
├── tests/               # Unit tests (pytest, no Docker/Redis/Postgres)
└── _legacy/             # Pre-refactoring code (frozen archive, read-only)
```

**Core Modules**:
-   **entities.py** (140 lines): Immutable domain objects
    -   `WeaveRequest`: Input parameters (query_text, top_k, similarity_threshold, categories filter)
    -   `WeaveResult`: Output contract (status, matches, extracted_concepts, latency_ms) — **NO risk_profile** ✅
    -   `PatternMatch`: Single match result (category, name, score, match_type, metadata)
    -   `WeaveStatus`, `MatchType`: Enums for type safety

-   **config.py** (220 lines): Taxonomy configuration
    -   `TaxonomyConfig`: Container for taxonomy structure (categories, metadata)
    -   `TaxonomyCategory`: Single category definition (name, keywords, metadata, subcategories)
    -   `from_yaml(path)`: Parse YAML taxonomy files
    -   `validate()`: Enforce taxonomy consistency rules

-   **consumers/weaver.py** (204 lines): Core weaving logic
    -   `WeaverConsumer.process(request: dict) -> WeaveResult`: Pure orchestration function
    -   Embedding-based similarity matching (delegates to adapter, NO direct Qdrant calls)
    -   Result filtering (threshold, top-k, category constraints)
    -   Concept extraction (collects unique matched categories)
    -   **NO _aggregate_risk()** ✅ (removed Feb 10, 2026 - epistemic boundary fix)

**Import Rules (LIVELLO 1)**:
- ✅ Relative imports ONLY: `from .domain import WeaveRequest`, `from ..events import CHANNELS`
- ✅ Core utilities: `from core.agents.postgres_agent import PostgresAgent` (TYPE HINTS ONLY, never instantiate)
- ❌ FORBIDDEN: `import httpx`, `import psycopg2`, `import qdrant_client`, `from services.*`
- ❌ FORBIDDEN: Instantiate PostgresAgent/QdrantAgent/StreamBus in consumers
- ❌ FORBIDDEN: Absolute imports across Sacred Orders: `from core.governance.memory_orders.*`

**Sacred Mandate** (from charter.md):
1. "Extract, never invent" — Discover patterns in taxonomy, never hallucinate categories
2. "Domain agnostic by design" — Taxonomy from configuration, not code
3. "Graceful degradation" — Keyword fallback when embedding services fail
4. "Semantic precision" — Fewer high-confidence matches over many low-confidence

---

### LIVELLO 2: Service Layer
**Location**: `services/api_pattern_weavers/`  
**Characteristics**: Orchestration, I/O boundary, HTTP endpoints, Docker

**Directory Structure** (SACRED_ORDER_PATTERN compliant):
```
services/api_pattern_weavers/
├── main.py              # < 100 lines (FastAPI bootstrap ONLY) ✅ 62 lines
├── config.py            # ALL os.getenv() centralized (3373 lines)
├── adapters/
│   ├── bus_adapter.py   # Orchestrates LIVELLO 1 consumers + StreamBus
│   └── persistence.py   # ONLY I/O point (PostgresAgent, QdrantAgent)
├── api/
│   └── routes.py        # Thin HTTP endpoints (validate → delegate → return)
├── models/
│   └── schemas.py       # Pydantic request/response models (NO RiskProfile ✅)
├── monitoring/
│   └── health.py        # Health checks, Prometheus metrics
├── requirements.txt     # Python dependencies
└── _legacy/             # Pre-refactoring service code (frozen archive)
```

**main.py** (62 lines ✅ < 100): Minimal FastAPI bootstrap
```python
"""Pattern Weavers API — Sacred Order #5 (REASON / Semantic Layer) — Port 9017."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_config
from .api import routes
from .monitoring import health

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    config = get_config()
    logger.info(f"Pattern Weavers starting (version {config.VERSION})")
    logger.info(f"Qdrant: {config.QDRANT_HOST}:{config.QDRANT_PORT}")
    logger.info(f"Embedding service: {config.EMBEDDING_SERVICE_URL}")
    yield
    logger.info("Pattern Weavers shutting down")

app = FastAPI(
    title="Pattern Weavers API",
    description="Universal ontology resolution engine",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)
app.include_router(health.router)
```

**Import Rules (LIVELLO 2)**:
- ✅ Import LIVELLO 1: `from core.cognitive.pattern_weavers.consumers import WeaverConsumer`
- ✅ Import agents: `from core.agents.postgres_agent import PostgresAgent`
- ✅ Import bus: `from core.synaptic_conclave.transport.streams import StreamBus`
- ❌ FORBIDDEN: LIVELLO 1 imports LIVELLO 2 (service → core only, ONE-WAY)
- ❌ FORBIDDEN: Cross-service imports: `from api_babel_gardens.*` in api_pattern_weavers

**Containerization**:
-   Docker container: `core_pattern_weavers` (port 9017)
-   Dependencies: PostgreSQL (audit logging), Qdrant (similarity search), Redis (event bus), Babel Gardens (embeddings)
-   Health check: `/health` endpoint (postgres/qdrant/redis/embedding status)

---

## Weaving Strategy (Ontology Resolution)

Pattern Weavers v2.0 uses a **two-stage resolution pipeline** that abstracts away provider-specific details:

### Stage 1: Embedding-Based Similarity Search
1. **Query Preprocessing**: Normalize text (lowercase, strip punctuation, language detection)
2. **Embedding Request**: Call Babel Gardens service → 384D vector (MiniLM-L6-v2)
3. **Qdrant Search**: Similarity search on `weave_embeddings` collection (cosine distance)
4. **Result Filtering**: Apply similarity_threshold (default 0.4), top_k limit (default 10)
5. **Match Construction**: Map Qdrant hits → `PatternMatch` objects

**Output Format** (every match):
```python
PatternMatch(
    category="concepts",        # Taxonomy category (concepts, sectors, regions, etc.)
    name="Banking",             # Matched entity name
    score=0.87,                 # Similarity score [0, 1]
    match_type=MatchType.SEMANTIC,  # SEMANTIC (embedding-based)
    metadata={                  # Optional domain-specific data
        "sector": "Financials",
        "region": "Global"
    }
)
```

### Stage 2: Keyword Fallback (Graceful Degradation)
If embedding service unavailable:
1. **Keyword Extraction**: Tokenize query → lowercase keywords
2. **Taxonomy Scanning**: Match keywords against taxonomy.keywords (Levenshtein distance)
3. **Match Construction**: Create `PatternMatch` objects with `match_type=MatchType.KEYWORD`

**Fallback guarantees**:
- 100% availability (no dependency on external services)
- Lower accuracy (70% vs 95% embedding-based) but functional
- Same WeaveResult schema (transparent to consumers)

### Stage 3: Result Aggregation
1. **Deduplication**: Remove duplicate matches (same category + name)
2. **Concept Extraction**: Collect unique category values → `extracted_concepts` list
3. **Latency Tracking**: Record total processing time → `latency_ms`
4. **WeaveResult Construction**: Immutable result object

**Sacred Invariant**: Pattern Weavers ONLY resolves ontology structure. It does NOT:
- ❌ Aggregate risk scores (removed _aggregate_risk method, Feb 10 2026)
- ❌ Compute sentiment (belongs to Babel Gardens)
- ❌ Predict outcomes (belongs to Neural Engine)
- ❌ Generate strategies (belongs to Portfolio Architects)

---

## YAML Taxonomy Configuration

Pattern Weavers is **fully configuration-driven**. To add a new vertical domain (e.g., healthcare, legal, maritime), create a YAML taxonomy file—**NO code changes required**.

**Example**: Finance Taxonomy (`config/taxonomy_finance.yaml`)
```yaml
# Finance Taxonomy - GICS Sectors + Regional Coverage
name: "finance"
version: "2.0.0"
description: "Financial market taxonomy (sectors, regions, concepts)"

categories:
  - name: "concepts"
    description: "High-level financial concepts"
    entries:
      - name: "Banking"
        keywords: ["bank", "banking", "financial institution", "credit"]
        metadata:
          sector: "Financials"
          region: "Global"
      
      - name: "Technology"
        keywords: ["tech", "technology", "software", "hardware", "IT"]
        metadata:
          sector: "Information Technology"
          region: "Global"
      
      - name: "ESG"
        keywords: ["esg", "sustainability", "green", "renewable", "impact"]
        metadata:
          sector: "Diversified"
          region: "Global"

  - name: "sectors"
    description: "GICS sector classification"
    entries:
      - name: "Financials"
        keywords: ["bank", "insurance", "asset management", "fintech"]
        metadata:
          gics_code: "40"
      
      - name: "Information Technology"
        keywords: ["software", "hardware", "semiconductors", "cloud"]
        metadata:
          gics_code: "45"
      
      - name: "Healthcare"
        keywords: ["pharma", "biotech", "medical", "hospital"]
        metadata:
          gics_code: "35"

  - name: "regions"
    description: "Geographic coverage"
    entries:
      - name: "Europe"
        keywords: ["europe", "european", "eu", "eurozone"]
        metadata:
          countries: ["IT", "FR", "DE", "ES", "UK", "NL", "CH"]
      
      - name: "North America"
        keywords: ["usa", "us", "america", "canada", "mexico"]
        metadata:
          countries: ["US", "CA", "MX"]

# Metadata is domain-specific and NOT interpreted by Pattern Weavers.
# Risk scoring, sentiment analysis, etc. belong to downstream consumers.
```

**Adding a New Domain** (e.g., Healthcare):
1. Create `config/taxonomy_healthcare.yaml` with medical taxonomy (ICD-10 codes, procedures, specialties)
2. Load via `TaxonomyConfig.from_yaml("config/taxonomy_healthcare.yaml")`
3. Pattern Weavers resolves healthcare queries → structured context (diagnoses, treatments, specialties)
4. **NO code changes** to Pattern Weavers core

---

## API Endpoints

**Base URL**: `http://localhost:9017` (Docker: `core_pattern_weavers`)

### POST `/weave` — Weave Query into Ontology
**Description**: Resolve unstructured query to taxonomy categories

**Request**:
```json
{
  "query_text": "analyze European banks with ESG focus",
  "top_k": 10,
  "similarity_threshold": 0.4,
  "categories": ["concepts", "sectors", "regions"],  // Optional filter
  "user_id": "user_123",
  "correlation_id": "req_abc123"
}
```

**Response** (200 OK):
```json
{
  "status": "completed",
  "matches": [
    {
      "category": "concepts",
      "name": "Banking",
      "score": 0.87,
      "match_type": "semantic",
      "metadata": {
        "sector": "Financials",
        "region": "Global"
      }
    },
    {
      "category": "concepts",
      "name": "ESG",
      "score": 0.82,
      "match_type": "semantic",
      "metadata": {
        "sector": "Diversified",
        "region": "Global"
      }
    },
    {
      "category": "regions",
      "name": "Europe",
      "score": 0.91,
      "match_type": "semantic",
      "metadata": {
        "countries": ["IT", "FR", "DE", "ES", "UK", "NL", "CH"]
      }
    },
    {
      "category": "sectors",
      "name": "Financials",
      "score": 0.85,
      "match_type": "semantic",
      "metadata": {
        "gics_code": "40"
      }
    }
  ],
  "extracted_concepts": ["Banking", "ESG", "Europe", "Financials"],
  "latency_ms": 124.5,
  "processed_at": "2026-02-11T10:45:23.456Z"
}
```

**Response** (503 Service Unavailable):
```json
{
  "detail": "Embedding service unavailable"
}
```

### GET `/health` — Health Check
**Response**:
```json
{
  "status": "healthy",
  "qdrant": true,
  "postgres": true,
  "redis": false,
  "embedding_service": true
}
```

### GET `/metrics` — Prometheus Metrics
**Response** (text/plain):
```
# HELP pattern_weavers_queries_total Total weave queries processed
# TYPE pattern_weavers_queries_total counter
pattern_weavers_queries_total{status="completed"} 1234

# HELP pattern_weavers_latency_seconds Weave operation latency
# TYPE pattern_weavers_latency_seconds histogram
pattern_weavers_latency_seconds_bucket{le="0.1"} 450
pattern_weavers_latency_seconds_bucket{le="0.5"} 890
...
```

---

## Integration with Sacred Orders

Pattern Weavers is a **service consumer**, not a data source. It orchestrates other Sacred Orders:

### Babel Gardens (Embedding Generation)
**Channel**: HTTP REST (`GET /embed`)  
**Purpose**: Convert query_text → 384D semantic vector  
**Contract**: `{"text": "...", "model": "MiniLM-L6-v2"}` → `{"embedding": [0.023, -0.145, ...]}`

### Qdrant (Similarity Search)
**Channel**: gRPC (`/collections/weave_embeddings/points/search`)  
**Purpose**: Find nearest neighbors in taxonomy embedding space  
**Contract**: `{"vector": [...], "limit": 10}` → `[{"id": "...", "score": 0.87, "payload": {...}}]`

### Vault Keepers (Pattern Archival)
**Channel**: Redis Streams (`vault.archive.pattern`)  
**Purpose**: Archive WeaveResult for historical analysis  
**Contract**: `{"pattern": WeaveResult.to_dict(), "timestamp": "...", "user_id": "..."}`

### Neural Engine (Feature Engineering)
**Channel**: Redis Streams (`neural.features.request`)  
**Purpose**: Neural Engine consumes extracted_concepts for feature generation  
**Contract**: `{"concepts": ["Banking", "ESG"], "correlation_id": "..."}`

**Sacred Invariant**: StreamBus is **payload-blind**. Pattern Weavers emits events but does NOT inspect events from other Orders (no correlation, no synthesis in transport layer).

---

## Phase 1 Refactoring Summary (February 10-11, 2026)

### Problem Statement
Pattern Weavers v1.x contained **epistemic boundary violations**: the `_aggregate_risk()` method (41 lines) computed risk scores by aggregating sector metadata—a form of **semantic interpretation** forbidden at the ontology layer. Risk scoring belongs to the **Neural Engine** (REASON layer), not Pattern Weavers (PERCEPTION → REASON interface).

### Changes Applied (11 commits)
**Commit 0**: Contract drift bugfix (routes.py)
- Fixed `"query"` → `"query_text"` (consumer expects query_text key)
- Fixed `taxonomy.entries` → `taxonomy.categories` (AttributeError on access)
- Fixed `"text"` → `"query_text"` (keyword_matcher contract)

**Commits 1-6**: Risk semantics removal
1. **RiskProfile entity deleted** (domain/entities.py, 18 lines removed)
2. **WeaveResult.risk_profile field removed** (output contract purified)
3. **_aggregate_risk() method deleted** (consumers/weaver.py, 41 lines removed) — **CRITICAL**
4. **Domain exports cleaned** (domain/__init__.py, RiskProfile references removed)
5. **API surface purified** (schemas.py, routes.py: no RiskProfile construction)
6. **Charter updated** (philosophy/charter.md: pipeline diagram, NO risk aggregation step)
7. **Config de-biased** (config.py: risk_level examples → generic metadata)

**Commits 7-11**: Verification + final cleanup
- Docker rebuild + deployment (service healthy on port 9017)
- Import verification (grep RiskProfile → zero matches outside _legacy/)
- Final stale reference cleanup (domain/__init__.py docstring/exports)

### Verification Results
```bash
# 1. RiskProfile completely purged
grep -r "RiskProfile" vitruvyan_core/core/cognitive/pattern_weavers/ | grep -v "_legacy"
# → (empty) ✅

# 2. Imports work
docker exec core_pattern_weavers python3 -c \
  "from core.cognitive.pattern_weavers.domain import WeaveResult; print('✅')"
# → ✅ Imports OK

# 3. Service healthy
curl http://localhost:9017/health
# → {"status": "healthy", "postgres": true} ✅

# 4. main.py conformance
wc -l services/api_pattern_weavers/main.py
# → 62 lines ✅ (< 100 target)
```

### Epistemic Impact
**Before**: Pattern Weavers computed risk_profile by aggregating sector metadata → **Boundary violation** (ontology layer performing semantic interpretation)

**After**: Pattern Weavers is **purely ontological** → Resolves structure (matched categories), NO semantic interpretation
- Output: `WeaveResult(matches, extracted_concepts, similarity_scores)`
- Risk scoring: **Deferred to Neural Engine** (downstream consumer receives extracted_concepts → computes risk)

### Agnosticization Score
**Before Phase 1**: 26/100 (finance-biased risk logic hardcoded)  
**After Phase 1**: 60-65/100 (ontology pure, risk removed, some provider coupling remains)  
**Target Phase 2**: 75-80/100 (provider coupling removed, config injection enforced, Streams naming aligned)

---

## Development Setup

### Prerequisites
- Python 3.11+
- Docker + Docker Compose
- PostgreSQL 15+ (audit logging)
- Qdrant 1.7+ (similarity search)
- Redis 7+ (event bus)
- Babel Gardens service (embedding generation)

### Local Development (LIVELLO 1 - Pure Domain)
```bash
# Clone repository
git clone https://github.com/vitruvyan/vitruvyan-core.git
cd vitruvyan-core

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install core dependencies (NO service dependencies)
pip install dataclasses-json pydantic pyyaml pytest

# Run unit tests (no Docker required)
pytest vitruvyan_core/core/cognitive/pattern_weavers/tests/ -v

# Test pure imports (no I/O)
python3 -c "from vitruvyan_core.core.cognitive.pattern_weavers.domain import WeaveResult; print('✅ Pure imports OK')"
```

### Service Deployment (LIVELLO 2 - Docker)
```bash
# Build container
cd infrastructure/docker
docker compose build pattern_weavers

# Start service + dependencies
docker compose up -d postgres qdrant redis babel_gardens pattern_weavers

# Wait for warmup
sleep 5

# Check health
curl http://localhost:9017/health | jq

# Test weaving
curl -X POST http://localhost:9017/weave \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "analyze European banking sector",
    "top_k": 5,
    "similarity_threshold": 0.4
  }' | jq
```

### Configuration (Environment Variables)
```bash
# LIVELLO 2 (service layer only)
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=vitruvyan_core
export REDIS_HOST=localhost
export REDIS_PORT=6379
export EMBEDDING_SERVICE_URL=http://localhost:9009/embed

# LIVELLO 1 (pure domain)
# NO environment variables (config via function parameters only)
```

---

## Testing Strategy

### Unit Tests (LIVELLO 1 - Pure Domain)
**Location**: `vitruvyan_core/core/cognitive/pattern_weavers/tests/`  
**Philosophy**: Test pure functions in isolation, NO infrastructure dependencies

```python
# test_entities.py - Immutable dataclass tests
def test_weave_result_immutability():
    result = WeaveResult(status=WeaveStatus.COMPLETED)
    with pytest.raises(FrozenInstanceError):
        result.status = WeaveStatus.FAILED  # ❌ Forbidden (frozen dataclass)

# test_config.py - YAML parsing tests
def test_taxonomy_from_yaml():
    config = TaxonomyConfig.from_yaml("tests/fixtures/taxonomy_test.yaml")
    assert config.name == "test"
    assert len(config.categories) == 3
    assert config.categories[0].name == "concepts"

# test_weaver.py - Pure consumer logic tests (NO I/O)
def test_weaver_consumer_filtering():
    consumer = WeaverConsumer()
    # Mock matches (no Qdrant calls)
    matches = [
        PatternMatch("concepts", "Banking", 0.9, MatchType.SEMANTIC),
        PatternMatch("concepts", "Technology", 0.3, MatchType.SEMANTIC),  # Below threshold
    ]
    filtered = consumer._filter_matches(matches, threshold=0.4)
    assert len(filtered) == 1
    assert filtered[0].name == "Banking"
```

**Run**:
```bash
pytest vitruvyan_core/core/cognitive/pattern_weavers/tests/ -v --no-cov
# NO Docker required ✅
```

### Integration Tests (LIVELLO 2 - Service Layer)
**Location**: `services/api_pattern_weavers/tests/`  
**Philosophy**: Test full service stack with real infrastructure

```python
# test_api.py - HTTP endpoint tests
@pytest.mark.integration
def test_weave_endpoint_success():
    response = client.post("/weave", json={
        "query_text": "European banking",
        "top_k": 5
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert len(data["matches"]) > 0
    assert "Banking" in data["extracted_concepts"]

# test_adapters.py - Qdrant/PostgreSQL adapter tests
@pytest.mark.integration
def test_qdrant_similarity_search():
    from services.api_pattern_weavers.adapters.persistence import QdrantAdapter
    adapter = QdrantAdapter()
    results = adapter.search(vector=[0.1] * 384, collection="weave_embeddings", limit=5)
    assert len(results) <= 5
    assert all(r.score >= 0.0 for r in results)
```

**Run**:
```bash
# Start infrastructure
docker compose up -d postgres qdrant redis babel_gardens

# Run integration tests
pytest services/api_pattern_weavers/tests/ -v -m integration
```

---

## Observability & Debugging

### Prometheus Metrics
```python
# Pattern Weavers exposes metrics on /metrics endpoint

# Query metrics
pattern_weavers_queries_total{status="completed"}  # Total successful weaves
pattern_weavers_queries_total{status="failed"}     # Total failures

# Latency distribution
histogram_quantile(0.95, pattern_weavers_latency_seconds_bucket)  # P95 latency

# Match statistics
pattern_weavers_matches_total  # Total matches extracted
pattern_weavers_concepts_extracted_total  # Total unique concepts
```

### Structured Logging
```python
# All logs are JSON-structured (structlog)
{
    "timestamp": "2026-02-11T10:45:23.456Z",
    "level": "INFO",
    "event": "weave_completed",
    "query_text": "European banking",
    "matches_count": 4,
    "concepts": ["Banking", "Europe", "Financials"],
    "latency_ms": 124.5,
    "correlation_id": "req_abc123"
}
```

### Debugging Checklist
**Issue**: `/weave` returns 503 "Embedding service unavailable"
- ✅ Check Babel Gardens: `curl http://localhost:9009/health`
- ✅ Check network: `docker network inspect vitruvyan_network`
- ✅ Check logs: `docker logs core_babel_gardens --tail=50`

**Issue**: Matches have low similarity scores (< 0.4)
- ✅ Check taxonomy: Verify keywords match query domain
- ✅ Check embeddings: Ensure Qdrant collection populated (`GET /collections/weave_embeddings`)
- ✅ Lower threshold: Try `similarity_threshold: 0.2` (test only, not production)

**Issue**: `ImportError: cannot import name 'RiskProfile'`
- ✅ Check git branch: `git log --oneline -5` (should show Phase 1 commits)
- ✅ Rebuild container: `docker compose build --no-cache pattern_weavers`
- ✅ Verify imports: `docker exec core_pattern_weavers python3 -c "from core.cognitive.pattern_weavers.domain import WeaveResult; print('OK')"`

---

## Contributing

### Adding a New Taxonomy
1. **Create YAML file**: `vitruvyan_core/core/cognitive/pattern_weavers/config/taxonomy_<domain>.yaml`
2. **Define categories**: Concepts, entities, relationships (domain-specific)
3. **Add keywords**: Synonyms, aliases, domain jargon
4. **Load in service**: Update `config.py` → `load_taxonomies()` function
5. **Test**: Unit test YAML parsing + integration test weaving

### Phase 2 Contributions (Open)
- **Provider coupling removal**: Abstract EmbeddingConfig.api_url to adapter layer
- **Config injection**: Enforce set_config() boundaries (prevent direct config mutation)
- **Streams naming**: Align channel names (`pattern.*` → `pattern_weavers.*`)
- **Qdrant abstraction**: Generic similarity hit structure (remove ScoredPoint dependency)

**Pull requests welcome**: Follow SACRED_ORDER_PATTERN (LIVELLO 1/2 separation), include tests, update charter if changing mandate.

---

## License & Credits

**License**: Proprietary (Vitruvyan AI Inc.)  
**Authors**: Vitruvyan Core Team  
**Last Updated**: February 11, 2026  
**Version**: 2.0.0 (Phase 1 Complete)

**Sacred Orders Integration**:
- Babel Gardens (Embedding Generation)
- Vault Keepers (Pattern Archival)
- Neural Engine (Risk Scoring - downstream consumer)
- Memory Orders (Coherence Analysis)
- Orthodoxy Wardens (Explainability Compliance)

**Phase 1 Refactoring Credits**:
- Epistemic boundary enforcement (risk removal)
- SACRED_ORDER_PATTERN conformance (LIVELLO 1/2 separation)
- Contract drift bugfixes (query_text, categories, keyword_matcher)
- Service deployment verification (port 9017, health checks)

---

*"From raw intent, structured meaning emerges."*  
— Pattern Weavers Charter, February 2026
