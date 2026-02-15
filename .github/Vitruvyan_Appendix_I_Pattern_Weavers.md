# Appendix I — Pattern Weavers: Universal Ontology Resolution Engine

**Version**: 2.0.0 (Phase 1 - Ontological Purification Complete)  
**Last Updated**: February 14, 2026  
**Status**: Production Ready (Phase 1 Complete, Phase 2 Planned)  
**Epistemic Order**: REASON (Semantic Contextualization Layer)  
**Sacred Order**: REASON (peer to Babel Gardens, Memory Orders, Vault Keepers, Orthodoxy Wardens)

---

## 1. Executive Summary

Pattern Weavers is Vitruvyan OS's **universal ontology resolution engine**—a domain-agnostic system that transforms unstructured queries ("analyze European banks", "ESG renewable energy", "cardiac arrest protocols") into **structured semantic context** by mapping text to taxonomy categories through embedding-based similarity search and keyword matching.

**Phase 1 Refactoring** (February 10-11, 2026) eliminated **epistemic boundary violations** that plagued v1.x. The critical issue: Pattern Weavers contained a `_aggregate_risk()` method (41 lines) that computed risk scores by interpreting sector metadata—a form of **semantic reasoning** forbidden at the ontology layer. Risk scoring belongs to the **Neural Engine** (downstream REASON consumer), not Pattern Weavers (PERCEPTION → REASON interface).

The v2.0 solution: **Pure ontology resolution**. Pattern Weavers now extracts **structure** (taxonomy matches, similarity scores, extracted concepts) without **interpretation** (risk aggregation, sentiment analysis, predictive inference). This separation is non-negotiable: violating it creates untraceable, unexplainable AI systems that fail Orthodoxy Wardens compliance.

**Key Capabilities**:
-   **Universal Taxonomy Resolution**: Support ANY domain (finance, healthcare, cybersecurity, maritime, legal) via YAML-driven taxonomy configuration
-   **Embedding-Based Similarity**: Semantic search using Qdrant (384D vectors from Babel Gardens)
-   **Keyword Fallback**: Graceful degradation when embedding services unavailable (70% accuracy baseline)
-   **Explainability by Design**: Every match includes similarity scores, match types, and metadata
-   **Sacred Order Integration**: Neural Engine (features), Vault Keepers (archival), Babel Gardens (embeddings)

**Phase 1 Achievements** (11 commits):
- ✅ **RiskProfile entity deleted** (18 lines removed from domain layer)

- ✅ **RiskProfile entity deleted** (18 lines removed from domain layer)
- ✅ **_aggregate_risk() method eliminated** (41 lines removed) — **CRITICAL epistemic boundary fix**
- ✅ **Charter updated** (pipeline diagram: removed "Risk Aggregation" step)
- ✅ **API surface purified** (no risk_profile in WeaveResult, schemas, route handlers)
- ✅ **Contract drift fixed** (3 key mismatches: query_text, categories, keyword_matcher)
- ✅ **Service deployed** (port 9017, healthy, main.py 62 lines < 100)

**Agnosticization Score**: 26/100 (v1.x) → **60-65/100** (v2.0 Phase 1) → Target 75-80/100 (Phase 2)

---

## 2. Architectural Overview (SACRED_ORDER_PATTERN)

Pattern Weavers follows the mandatory **SACRED_ORDER_PATTERN** with strict LIVELLO 1 (pure domain) and LIVELLO 2 (service infrastructure) separation.

### LIVELLO 1: Pure Domain Layer
**Location**: `vitruvyan_core/core/cognitive/pattern_weavers/domain/`  
**Characteristics**: Zero I/O, no external dependencies, pure Python dataclasses

**Directory Structure** (10 directories required):
```
vitruvyan_core/core/cognitive/pattern_weavers/
├── domain/              # Immutable dataclasses (entities.py 140 lines, config.py 220 lines)
├── consumers/           # Pure process() functions (weaver.py 204 lines, keyword_matcher.py 164 lines)
├── governance/          # Rules, classifiers, engines (empty - future)
├── events/              # Channel name constants (77 lines)
├── monitoring/          # Metric NAME constants ONLY (56 lines)
├── philosophy/          # charter.md (identity, mandate, invariants)
├── docs/                # Implementation notes
├── examples/            # Usage examples (pure Python)
├── tests/               # Unit tests (pytest, no Docker)
└── _legacy/             # Pre-refactoring code (frozen archive)
```

**Core Modules**:

**1. entities.py** (140 lines) — Immutable domain objects
```python
@dataclass(frozen=True)
class PatternMatch:
    """Single taxonomy match result."""
    category: str           # "concepts", "sectors", "regions", etc.
    name: str               # "Banking", "Europe", "Financials"
    score: float            # Similarity score [0, 1]
    match_type: MatchType   # SEMANTIC, KEYWORD, FUZZY, EXACT
    metadata: Dict[str, Any]  # Domain-specific data

@dataclass
class WeaveResult:
    """Output contract - NO risk_profile field (removed Phase 1)."""
    status: WeaveStatus
    matches: List[PatternMatch]
    extracted_concepts: List[str]  # Unique category values
    latency_ms: float
    error_message: Optional[str]
    processed_at: datetime
    
    # ❌ REMOVED Phase 1: risk_profile: Optional[RiskProfile]
```

**2. config.py** (220 lines) — Taxonomy configuration
```python
@dataclass
class TaxonomyCategory:
    """Single taxonomy category (e.g., 'concepts', 'sectors')."""
    name: str
    description: str
    entries: List[TaxonomyEntry]  # Individual items
    metadata: Dict[str, Any]
    
@dataclass
class TaxonomyConfig:
    """Container for domain taxonomy."""
    name: str              # "finance", "healthcare", "cyber"
    version: str
    categories: List[TaxonomyCategory]
    
    @staticmethod
    def from_yaml(path: str) -> "TaxonomyConfig":
        """Parse YAML → TaxonomyConfig (105 lines implementation)."""
        # Load YAML, validate structure, build dataclasses
```

**3. consumers/weaver.py** (204 lines) — Core weaving logic
```python
class WeaverConsumer:
    """Pure weaving orchestration (NO I/O)."""
    
    def process(self, request: dict) -> WeaveResult:
        """
        Pure function: dict → WeaveResult
        NO database calls, NO HTTP requests, NO file I/O
        """
        # 1. Preprocessing (normalize query)
        # 2. Embedding request (delegate to adapter)
        # 3. Similarity search (delegate to adapter)
        # 4. Result filtering (threshold, top-k)
        # 5. Concept extraction
        # 6. WeaveResult construction
        
        # ❌ REMOVED Phase 1: self._aggregate_risk(matches)
        #    Risk scoring belongs to Neural Engine
```

**Import Rules (LIVELLO 1)**:
- ✅ Relative imports ONLY: `from .domain import WeaveRequest`
- ✅ Core utilities (TYPE HINTS): `from core.agents.postgres_agent import PostgresAgent`
- ❌ FORBIDDEN: `import httpx`, `import psycopg2`, `import qdrant_client`
- ❌ FORBIDDEN: Instantiate agents in consumers (dependency injection required)
- ❌ FORBIDDEN: Cross-Sacred-Order imports: `from core.governance.memory_orders.*`

**Sacred Laws** (from charter.md):
1. "Extract, never invent" — Discover patterns in taxonomy, never hallucinate
2. "Domain agnostic by design" — Taxonomy from configuration, not code
3. "Graceful degradation" — Keyword fallback when embedding unavailable
4. "Semantic precision" — Fewer high-confidence matches over many low-confidence

---

### LIVELLO 2: Service Layer
**Location**: `services/api_pattern_weavers/`  
**Characteristics**: Orchestration, I/O boundary, HTTP endpoints, Docker

**Directory Structure**:
```
services/api_pattern_weavers/
├── main.py              # 62 lines ✅ (< 100 target)
├── config.py            # Environment variables (ALL os.getenv() centralized)
├── adapters/
│   ├── bus_adapter.py   # Orchestrates consumers + StreamBus
│   └── persistence.py   # PostgresAgent, QdrantAgent (ONLY I/O point)
├── api/
│   └── routes.py        # HTTP endpoints (validate → delegate → return)
├── models/
│   └── schemas.py       # Pydantic models (NO RiskProfile ✅)
├── monitoring/
│   └── health.py        # Health checks, Prometheus metrics
└── _legacy/             # Pre-refactoring code (frozen)
```

**main.py** (62 lines) — Minimal FastAPI bootstrap
```python
"""Pattern Weavers API — Port 9017 (REASON / Semantic Layer)."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from .api import routes
from .monitoring import health

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan (startup/shutdown)."""
    config = get_config()
    logger.info(f"Pattern Weavers starting (v{config.VERSION})")
    yield
    logger.info("Pattern Weavers shutting down")

app = FastAPI(title="Pattern Weavers", version="2.0.0", lifespan=lifespan)
app.include_router(routes.router)
app.include_router(health.router)
```

**Import Rules (LIVELLO 2)**:
- ✅ Import LIVELLO 1: `from core.cognitive.pattern_weavers.consumers import WeaverConsumer`
- ✅ Import agents: `from core.agents.postgres_agent import PostgresAgent`
- ✅ Import bus: `from core.synaptic_conclave.transport.streams import StreamBus`
- ❌ FORBIDDEN: LIVELLO 1 imports LIVELLO 2 (one-way dependency)
- ❌ FORBIDDEN: Cross-service imports: `from api_babel_gardens.*`

**Containerization**:
- Docker: `core_pattern_weavers` (port 9017 → 8011 internal)
- Dependencies: PostgreSQL (audit), Qdrant (similarity), Redis (bus), Babel Gardens (embeddings)
- Health: `/health` endpoint (postgres/qdrant/redis/embedding status checks)

---

## 3. Weaving Strategy (Two-Stage Pipeline)

Pattern Weavers uses a **hybrid resolution strategy** that balances accuracy and availability:

### Stage 1: Embedding-Based Similarity Search (Primary)
**Accuracy**: ~95% | **Latency**: 120-200ms | **Dependency**: Babel Gardens + Qdrant

**Pipeline**:
1. **Query Preprocessing**: Normalize text (lowercase, strip punctuation, detect language)
2. **Embedding Request**: Call Babel Gardens `/embed` → 384D vector (MiniLM-L6-v2)
3. **Qdrant Search**: Similarity search on `weave_embeddings` collection (cosine distance)
4. **Result Filtering**: Apply similarity_threshold (default 0.4), top_k limit (default 10)
5. **Match Construction**: Map Qdrant hits → `PatternMatch` objects

**Output Example**:
```python
PatternMatch(
    category="concepts",
    name="Banking",
    score=0.87,                        # Cosine similarity
    match_type=MatchType.SEMANTIC,
    metadata={"sector": "Financials", "region": "Global"}
)
```

### Stage 2: Keyword Fallback (Secondary)
**Accuracy**: ~70% | **Latency**: 40-60ms | **Dependency**: None (pure domain)

**Pipeline** (when embedding service unavailable):
1. **Keyword Extraction**: Tokenize query → lowercase keywords
2. **Taxonomy Scanning**: Match keywords against taxonomy.keywords (Levenshtein distance)
3. **Match Construction**: Create `PatternMatch` with `match_type=MatchType.KEYWORD`

**Fallback guarantees**:
- 100% availability (no external dependencies)
- Lower accuracy but functional
- Same WeaveResult schema (transparent to consumers)

### Stage 3: Result Aggregation
1. **Deduplication**: Remove duplicate matches (same category + name)
2. **Concept Extraction**: Collect unique category values → `extracted_concepts`
3. **Latency Tracking**: Record total processing time → `latency_ms`
4. **WeaveResult Construction**: Immutable result object

**Sacred Invariant**: Pattern Weavers ONLY resolves structure. It does NOT:
- ❌ Aggregate risk scores (removed _aggregate_risk, Feb 10 2026)
- ❌ Compute sentiment (belongs to Babel Gardens)
- ❌ Predict outcomes (belongs to Neural Engine)
- ❌ Generate strategies (belongs to vertical execution layers)

---

## 4. YAML Taxonomy Configuration

Pattern Weavers is **100% configuration-driven**. To add a new vertical (healthcare, legal, maritime), create a YAML file—**NO code changes required**.

**Example**: Finance Taxonomy (`config/taxonomy_finance.yaml`)
```yaml
name: "finance"
version: "2.0.0"
description: "Financial market taxonomy (GICS sectors, regions, concepts)"

categories:
  - name: "concepts"
    description: "High-level financial concepts"
    entries:
      - name: "Banking"
        keywords: ["bank", "banking", "financial institution", "credit"]
        metadata:
          sector: "Financials"
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
        keywords: ["bank", "insurance", "asset management"]
        metadata:
          gics_code: "40"
      
      - name: "Information Technology"
        keywords: ["software", "hardware", "semiconductors"]
        metadata:
          gics_code: "45"

  - name: "regions"
    description: "Geographic coverage"
    entries:
      - name: "Europe"
        keywords: ["europe", "european", "eu", "eurozone"]
        metadata:
          countries: ["IT", "FR", "DE", "ES", "UK", "NL", "CH"]

# Metadata is domain-specific and NOT interpreted by Pattern Weavers.
# Risk scoring, sentiment, predictions belong to downstream consumers.
```

**Adding New Domain** (e.g., Healthcare):
1. Create `config/taxonomy_healthcare.yaml` with medical taxonomy (ICD-10, procedures)
2. Load via `TaxonomyConfig.from_yaml("config/taxonomy_healthcare.yaml")`
3. Pattern Weavers resolves healthcare queries → structured context
4. **NO code changes** to Pattern Weavers core

---

## 5. API Surface

**Base URL**: `http://localhost:9017` (Docker: `core_pattern_weavers`)

### POST `/weave` — Resolve Query to Taxonomy
**Request**:
```json
{
  "query_text": "analyze European banks with ESG focus",
  "top_k": 10,
  "similarity_threshold": 0.4,
  "categories": ["concepts", "sectors", "regions"],  // Optional filter
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
      "metadata": {"sector": "Financials", "region": "Global"}
    },
    {
      "category": "concepts",
      "name": "ESG",
      "score": 0.82,
      "match_type": "semantic",
      "metadata": {"sector": "Diversified"}
    },
    {
      "category": "regions",
      "name": "Europe",
      "score": 0.91,
      "match_type": "semantic",
      "metadata": {"countries": ["IT", "FR", "DE", "ES"]}
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
*Note: Keyword fallback should prevent 503. Check Babel Gardens health.*

### GET `/health` — Service Health Check
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
```prometheus
# Total queries processed
pattern_weavers_queries_total{status="completed"} 1234
pattern_weavers_queries_total{status="failed"} 12

# Latency histogram
pattern_weavers_latency_seconds_bucket{le="0.1"} 450
pattern_weavers_latency_seconds_bucket{le="0.5"} 890

# Match statistics
pattern_weavers_matches_total 5678
pattern_weavers_concepts_extracted_total 2340
```

---

## 6. Integration with Sacred Orders

Pattern Weavers is a **service consumer**, not a data source. It orchestrates other Sacred Orders:

### Babel Gardens (Embedding Generation)
**Channel**: HTTP REST (`POST /embed`)  
**Purpose**: Convert query_text → 384D semantic vector  
**Contract**:
```json
Request:  {"texts": ["analyze European banks"], "model": "MiniLM-L6-v2"}
Response: {"embeddings": [[0.023, -0.145, ...]], "dimensions": 384}
```

### Qdrant (Similarity Search)
**Channel**: gRPC (`/collections/weave_embeddings/points/search`)  
**Purpose**: Find nearest neighbors in taxonomy embedding space  
**Contract**:
```json
Request:  {"vector": [...], "limit": 10, "score_threshold": 0.4}
Response: [{"id": "uuid", "score": 0.87, "payload": {"category": "concepts", ...}}]
```

### Vault Keepers (Pattern Archival)
**Channel**: Redis Streams (`vault.archive.pattern`)  
**Purpose**: Archive WeaveResult for historical analysis  
**Contract**:
```json
{
  "event_type": "pattern.weave.completed",
  "payload": {
    "weave_result": {...},
    "query_text": "...",
    "user_id": "...",
    "correlation_id": "..."
  }
}
```

### Neural Engine (Feature Engineering)
**Channel**: Redis Streams (`neural.features.request`)  
**Purpose**: Neural Engine consumes extracted_concepts for feature generation  
**Contract**:
```json
{
  "event_type": "neural.features.request",
  "payload": {
    "concepts": ["Banking", "ESG", "Europe"],
    "correlation_id": "req_abc123"
  }
}
```

**Sacred Invariant**: StreamBus is **payload-blind**. Pattern Weavers emits events but does NOT inspect/correlate/synthesize events from other Orders.

---

## 7. Phase 1 Refactoring (February 10-11, 2026)

### Problem Statement
Pattern Weavers v1.x violated **epistemic boundaries** by computing risk scores:

**Violation**: `_aggregate_risk()` method (41 lines, consumers/weaver.py)
```python
# ❌ REMOVED Feb 10, 2026 - Epistemic boundary violation
def _aggregate_risk(self, matches: List[PatternMatch]) -> RiskProfile:
    """
    Aggregate sector metadata → risk_level (high/medium/low)
    
    PROBLEM: Risk scoring is SEMANTIC INTERPRETATION, not ontology resolution.
             This logic belongs in Neural Engine (REASON layer), not Pattern Weavers.
    """
    # Extract sectors from matches
    sectors = [m.metadata.get("sector") for m in matches if m.category == "sectors"]
    
    # Map sectors to risk levels (hardcoded heuristics)
    risk_scores = {"Information Technology": 0.8, "Financials": 0.6, ...}
    
    # Aggregate risk
    avg_risk = sum(risk_scores.get(s, 0.5) for s in sectors) / len(sectors)
    risk_level = "high" if avg_risk > 0.7 else "medium" if avg_risk > 0.4 else "low"
    
    return RiskProfile(level=risk_level, score=avg_risk, dimensions={...})
```

**Why this is wrong**:
1. **Semantic Interpretation**: Mapping sectors → risk is REASONING, not ontology resolution
2. **Hardcoded Heuristics**: Risk scores baked into ontology layer (finance-biased)
3. **Untraceable**: Neural Engine cannot audit risk computation (hidden in Pattern Weavers)
4. **Violates Charter**: "Extract, never invent" — risk is INVENTED, not EXTRACTED

### Solution: Ontological Purification
**Delete `_aggregate_risk()` + RiskProfile entity** → Risk scoring deferred to Neural Engine

**New contract**:
```python
# ✅ CORRECT: Pure ontology resolution
WeaveResult(
    status=WeaveStatus.COMPLETED,
    matches=[
        PatternMatch("sectors", "Financials", 0.85, metadata={"gics_code": "40"}),
        PatternMatch("concepts", "Banking", 0.87, metadata={"sector": "Financials"}),
    ],
    extracted_concepts=["Financials", "Banking"],  # Structure only
    latency_ms=124.5
    
    # ❌ REMOVED: risk_profile=RiskProfile(level="medium", score=0.6)
)

# Neural Engine (downstream) consumes extracted_concepts:
# extracted_concepts=["Financials", "Banking"]
#   → Feature lookup: sector_volatility[Financials] = 0.6
#   → Risk computation: composite_risk = f(sector_volatility, market_regime, ...)
#   → Result: risk_score=0.68 (medium)
#   → Traceable: Neural Engine audit log records feature sources
```

### Changes Applied (11 commits)
**Commit 0**: Contract drift bugfix
- `"query"` → `"query_text"` (routes.py L89)
- `taxonomy.entries` → `taxonomy.categories` (routes.py L145)
- `"text"` → `"query_text"` (routes.py L165)

**Commits 1-6**: Risk purification
1. RiskProfile entity deleted (domain/entities.py, 18 lines)
2. WeaveResult.risk_profile field removed (domain/entities.py)
3. WeaverConsumer: removed _aggregate_risk() call (consumers/weaver.py)
4. _aggregate_risk() method deleted (consumers/weaver.py, 41 lines)
5. Domain exports cleaned (domain/__init__.py, RiskProfile removed)
6. API surface purified (schemas.py, routes.py: no RiskProfile)

**Commits 7-11**: Documentation + deployment
7. Charter updated (philosophy/charter.md: pipeline diagram, NO risk step)
8. Config de-biased (config.py: risk_level examples → generic metadata)
9. Docker rebuild + deployment (service healthy on port 9017)
10. Import verification (grep RiskProfile → zero matches)
11. Final stale reference cleanup (domain/__init__.py docstring)

### Verification
```bash
# 1. RiskProfile purged
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
**Before**: Ontology layer performed semantic reasoning → Untraceable, unexplainable risk scores  
**After**: Ontology layer resolves structure ONLY → Neural Engine performs traceable risk computation

**Agnosticization Score**:
- **Before Phase 1**: 26/100 (finance-biased risk logic hardcoded)
- **After Phase 1**: 60-65/100 (ontology pure, risk removed, some provider coupling remains)
- **Target Phase 2**: 75-80/100 (provider coupling removed, config injection enforced)

---

## 8. Data Layer

### Qdrant Collection: `weave_embeddings`
**Purpose**: Store taxonomy category embeddings for similarity search

**Schema**:
```json
{
  "collection_name": "weave_embeddings",
  "vector_size": 384,
  "distance": "Cosine",
  "points": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",  // UUID v5(namespace, "Banking")
      "vector": [0.023, -0.145, 0.089, ...],  // 384D MiniLM-L6-v2
      "payload": {
        "category": "concepts",
        "name": "Banking",
        "keywords": ["bank", "banking", "financial institution"],
        "metadata": {
          "sector": "Financials",
          "region": "Global"
        }
      }
    }
  ]
}
```

**Initialization**:
```bash
# Script: scripts/init_weave_collection.py
python3 scripts/init_weave_collection.py \
  --taxonomy config/taxonomy_finance.yaml \
  --collection weave_embeddings \
  --force  # Recreate if exists
```

### PostgreSQL Table: `weaver_queries`
**Purpose**: Audit trail for all weave operations

**Schema**:
```sql
CREATE TABLE weaver_queries (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    query_text TEXT NOT NULL,
    concepts JSONB NOT NULL,           -- extracted_concepts list
    patterns JSONB NOT NULL,           -- Full WeaveResult.matches
    latency_ms NUMERIC(10,2) NOT NULL,
    method VARCHAR(50) NOT NULL,       -- "semantic" | "keyword"
    correlation_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_weaver_concepts ON weaver_queries USING GIN(concepts);
CREATE INDEX idx_weaver_correlation ON weaver_queries(correlation_id);
```

**Example Row**:
```json
{
  "id": 12345,
  "user_id": "user_123",
  "query_text": "analyze European banks",
  "concepts": ["Banking", "Europe", "Financials"],
  "patterns": [{
    "category": "concepts",
    "name": "Banking",
    "score": 0.87,
    "match_type": "semantic"
  }],
  "latency_ms": 124.5,
  "method": "semantic",
  "correlation_id": "req_abc123",
  "created_at": "2026-02-11T10:45:23"
}
```

---

## 9. Observability

### Prometheus Metrics
```python
# Query metrics
pattern_weavers_queries_total{status="completed|failed"}
pattern_weavers_queries_by_method_total{method="semantic|keyword"}

# Latency histogram
pattern_weavers_latency_seconds{quantile="0.5|0.95|0.99"}

# Match statistics
pattern_weavers_matches_total
pattern_weavers_concepts_extracted_total

# Error tracking
pattern_weavers_errors_total{error_type="embedding_unavailable|qdrant_timeout|..."}
```

### Structured Logging (JSON)
```json
{
  "timestamp": "2026-02-11T10:45:23.456Z",
  "level": "INFO",
  "event": "weave_completed",
  "query_text": "European banking ESG",
  "matches_count": 4,
  "concepts": ["Banking", "ESG", "Europe"],
  "latency_ms": 124.5,
  "method": "semantic",
  "correlation_id": "req_abc123"
}
```

### Debugging Checklist
**Issue**: `/weave` returns 503 "Embedding service unavailable"
- ✅ Check Babel Gardens: `curl http://localhost:9009/health`
- ✅ Check network: `docker network inspect vitruvyan_network`
- ✅ Verify keyword fallback triggered: `grep "Fallback" docker logs core_pattern_weavers`

**Issue**: Matches have low similarity scores (< 0.4)
- ✅ Check taxonomy: Verify keywords match query domain
- ✅ Check embeddings: `curl http://localhost:6333/collections/weave_embeddings`
- ✅ Lower threshold (test only): `similarity_threshold: 0.2`

**Issue**: `ImportError: cannot import name 'RiskProfile'`
- ✅ Check git: `git log --oneline -5` (should show Phase 1 commits)
- ✅ Rebuild: `docker compose build --no-cache pattern_weavers`
- ✅ Verify: `docker exec core_pattern_weavers python3 -c "from core.cognitive.pattern_weavers.domain import WeaveResult; print('OK')"`

---

## 10. Phase 2 Roadmap (Deferred)

**Remaining Issues** (from due diligence report):

1. **Provider Coupling** (P1)
   - `EmbeddingConfig.api_url` hardcoded in LIVELLO 1
   - **Fix**: Move to LIVELLO 2 adapter, LIVELLO 1 receives embeddings as function parameter

2. **Config Injection** (P1)
   - No enforcement of `set_config()` boundaries (direct config mutation possible)
   - **Fix**: Make config immutable after set_config(), runtime validation

3. **Streams Naming** (P2)
   - Channel names inconsistent: `pattern.*` vs `pattern_weavers.*`
   - **Fix**: Align to convention (`{service}.{domain}.{action}`)

4. **Qdrant Abstraction** (P2)
   - Direct dependency on `ScoredPoint` (Qdrant-specific shape)
   - **Fix**: Generic similarity hit structure (provider-agnostic)

**Expected Impact**:
- **Agnosticization Score**: 60-65/100 (Phase 1) → **75-80/100** (Phase 2)
- **Provider Flexibility**: Support multiple vector DBs (Weaviate, Pinecone, Milvus)
- **Config Safety**: Prevent runtime config corruption

**Timeline**: Q2 2026 (not blocking production deployment)

---

## 11. Development Setup

### Local Development (LIVELLO 1)
```bash
# Clone repository
git clone https://github.com/vitruvyan/vitruvyan-core.git
cd vitruvyan-core

# Install core dependencies (NO service dependencies)
python3.11 -m venv venv
source venv/bin/activate
pip install dataclasses-json pydantic pyyaml pytest

# Run unit tests (no Docker)
pytest vitruvyan_core/core/cognitive/pattern_weavers/tests/ -v

# Test pure imports
python3 -c "from vitruvyan_core.core.cognitive.pattern_weavers.domain import WeaveResult; print('✅')"
```

### Service Deployment (LIVELLO 2)
```bash
# Build + start services
cd infrastructure/docker
docker compose build pattern_weavers
docker compose up -d postgres qdrant redis babel_gardens pattern_weavers

# Check health
curl http://localhost:9017/health | jq

# Test weaving
curl -X POST http://localhost:9017/weave \
  -H "Content-Type: application/json" \
  -d '{"query_text": "analyze European banks", "top_k": 5}' | jq
```

---

## 12. Testing Strategy

### Unit Tests (LIVELLO 1)
```python
# test_entities.py - Immutable dataclass tests
def test_weave_result_immutability():
    result = WeaveResult(status=WeaveStatus.COMPLETED)
    with pytest.raises(FrozenInstanceError):
        result.status = WeaveStatus.FAILED  # ❌ Frozen

# test_config.py - YAML parsing
def test_taxonomy_from_yaml():
    config = TaxonomyConfig.from_yaml("tests/fixtures/taxonomy_test.yaml")
    assert config.name == "test"
    assert len(config.categories) == 3

# test_weaver.py - Pure consumer logic (NO I/O)
def test_weaver_filtering():
    consumer = WeaverConsumer()
    matches = [
        PatternMatch("concepts", "Banking", 0.9, MatchType.SEMANTIC),
        PatternMatch("concepts", "Technology", 0.3, MatchType.SEMANTIC),  # Below threshold
    ]
    filtered = consumer._filter_matches(matches, threshold=0.4)
    assert len(filtered) == 1
```

**Run**: `pytest vitruvyan_core/core/cognitive/pattern_weavers/tests/ -v`

### Integration Tests (LIVELLO 2)
```python
# test_api.py - HTTP endpoint tests
@pytest.mark.integration
def test_weave_endpoint():
    response = client.post("/weave", json={"query_text": "European banking"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "Banking" in data["extracted_concepts"]

# test_adapters.py - Qdrant/PostgreSQL tests
@pytest.mark.integration
def test_qdrant_search():
    adapter = QdrantAdapter()
    results = adapter.search(vector=[0.1] * 384, limit=5)
    assert len(results) <= 5
```

**Run**: `pytest services/api_pattern_weavers/tests/ -v -m integration`

---

## 13. License & Credits

**License**: Proprietary (Vitruvyan AI Inc.)  
**Authors**: Vitruvyan Core Team  
**Version**: 2.0.0 (Phase 1 Complete)  
**Last Updated**: February 11, 2026

**Sacred Orders Integration**:
- Babel Gardens (Embedding Generation)
- Vault Keepers (Pattern Archival)
- Neural Engine (Risk Scoring - downstream)
- Memory Orders (Coherence Analysis)
- Orthodoxy Wardens (Explainability Compliance)

**Phase 1 Refactoring Credits**:
- Epistemic boundary enforcement (risk removal)
- SACRED_ORDER_PATTERN conformance (LIVELLO 1/2)
- Contract drift bugfixes
- Service deployment verification

---

*"From raw intent, structured meaning emerges."*  
— Pattern Weavers Charter, February 2026
- **FastAPI** with 3 endpoints: `/weave`, `/health`, `/metrics`
- **Prometheus Metrics**: `queries_total`, `latency_histogram`, `concepts_found`, `llm_queries_total` ✅ **NEW**
- **Dual-Process Architecture**: API (PID 16) + Redis Listener (PID 7)
- **Startup Script**: `start.sh` launches both services with graceful shutdown
- **LLM Dependency**: openai==1.12.0, structlog==24.1.0 ✅ **NEW**

**4. Redis Cognitive Bus** (`core/pattern_weavers/redis_listener.py`, 250 lines)
- **Subscribe**: `pattern_weavers:weave_request` (consume weave requests)
- **Publish**: `pattern_weavers:weave_response` (return weave results)
- **Broadcast**: `cognitive_bus:events` (Sacred Orders event stream)
- **Performance**: 43.80ms average latency (E2E Redis pub/sub)

**5. LangGraph Node** (`core/langgraph/node/weaver_node.py`, 180 lines) ✅ **MOVED** (Dec 24, 2025)
- **State Key**: `state["weaver_context"]` (populated by weaver_node)
- **Integration Point**: Between `intent_detection_node` and `ticker_resolver_node`
- **Fallback Strategy**: If weaving fails, continue with empty context (non-blocking)
- **Observability**: Prometheus metrics (calls, success, latency, concepts_found) ✅ **ADDED** (Dec 24, 2025)
- **Configuration**: Env vars (WEAVER_TOP_K, WEAVER_SIMILARITY_THRESHOLD) ✅ **ADDED** (Dec 24, 2025)

**6. Configuration** (`core/pattern_weavers/config/weave_rules.yaml`)
```yaml
concepts:
  - name: "Technology"
    sector: "Information Technology"
    region: "Global"
  - name: "Banking"
    sector: "Financials"
    region: "Global"
  - name: "ESG"  # ✅ NEW - LLM can extract, YAML cannot
    sector: "Diversified"
    region: "Global"
  - name: "Sustainability"  # ✅ NEW - LLM semantic understanding
    sector: "Utilities"
    region: "Global"
  # ... (7 base concepts + LLM dynamic extraction)

regions:
  - name: "Europe"
    countries: [IT, FR, DE, ES, UK, NL, CH]
  - name: "North America"
    countries: [US, CA, MX]
  # ... (4 total)

sectors:
  - name: "Information Technology"
    risk_level: "high"
  - name: "Healthcare"
    risk_level: "medium"
  # ... (8 total)

risk_profiles:
  - name: "Conservative"
    dimensions: [low_volatility, dividend_yield, stable_earnings]
  # ... (5 total)
```

---

## 📊 Data Layer

### Qdrant Collection: `weave_embeddings`
- **Points**: 24 (7 concepts + 4 regions + 8 sectors + 5 risk profiles)
- **Dimensions**: 384 (MiniLM-L6-v2 embeddings)
- **Distance**: Cosine similarity
- **Initialization**: `scripts/init_weave_collection.py`
- **Update Strategy**: Append-only (no overwrites, UUID v5 ensures uniqueness)

**Example Point**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",  // UUID v5(namespace, "Banking")
  "vector": [0.023, -0.145, 0.089, ...],  // 384D
  "payload": {
    "type": "concept",
    "value": "Banking",
    "sector": "Financials",
    "region": "Global",
    "risk_level": null
  }
}
```

### PostgreSQL Table: `weaver_queries`
```sql
CREATE TABLE weaver_queries (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    query_text TEXT NOT NULL,
    concepts JSONB NOT NULL,           -- Extracted concepts (["Banking", "Technology"])
    patterns JSONB NOT NULL,           -- Full pattern details (regions, sectors, risk)
    latency_ms NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_weaver_concepts ON weaver_queries USING GIN(concepts);  -- JSONB queries
```

**Example Row**:
```json
{
  "user_id": "ux_test",
  "query_text": "analizza banche europee",
  "concepts": ["Banking"],
  "patterns": [
    {"type": "region", "value": "Europe", "confidence": 0.466, "countries": ["IT", "FR", "DE"]},
    {"type": "concept", "value": "Banking", "confidence": 0.259, "sector": "Financials"}
  ],
  "latency_ms": 38.82
}
```

---

## 🔄 Integration Flow

### LangGraph Integration with LLM Ontology (graph_flow.py)
```
User Query: "renewable energy ESG North America"
  ↓
intent_detection_node → intent='trend', tickers=[]
  ↓
weaver_node → Priority Cascade:
  PRIORITY 1: LLM Ontology (GPT-4o-mini)
    - Call llm_ontology_engine.recognize(query_text)
    - Extract: concepts=["ESG", "Sustainability"], sector="Utilities", region="North America"
    - Latency: 3.8s, Cost: $0.00028, Accuracy: 95%+
  PRIORITY 2: YAML Fallback (if LLM fails)
    - QdrantAgent.search(query_text, top_k=5, threshold=0.25)
    - Extract: concepts=["Energy"], sector="Utilities", region="North America"
    - Latency: 45ms, Cost: $0, Accuracy: 70%
  ↓
state["weaver_context"] = {
  "concepts": ["ESG", "Sustainability"],  # LLM extracted (YAML would miss)
  "regions": ["North America"],
  "countries": ["US", "CA", "MX"],
  "sectors": ["Utilities"],
  "risk": "medium",
  "method": "llm_ontology"  # ✅ Tracking which method used
}
  ↓
ticker_resolver_node → Query Qdrant with weaver_context boost
  - "ESG + sustainability + utilities + north america"
  - Returns: NEE (NextEra Energy), DUK (Duke Energy), SO (Southern Company)
  ↓
Response: "Analisi trend renewable energy ESG (3 tickers, ESG-compliant)"
```

### Redis Cognitive Bus Integration
```
Synaptic Conclave → Publish: pattern_weavers:weave_request
  ↓
Redis Listener (PID 7) → PatternWeaversListener.listen()
  ↓
_handle_weave_request → weaver.weave(query_text, user_id, top_k, threshold)
  ↓
QdrantAgent.search(query_embedding, collection="weave_embeddings")
  ↓
_log_query → PostgreSQL INSERT (weaver_queries table)
  ↓
_publish_event → cognitive_bus:events (broadcast to all Sacred Orders)
  ↓
Redis Listener → Publish: pattern_weavers:weave_response
```

---

## 🚀 UX Improvement

### Before Pattern Weavers (Multi-Turn Slot-Filling)
```
User: "analizza banche europee"
  ↓
System: "Quali ticker vuoi analizzare? (es: AAPL, NVDA)"  ← FRICTION
  ↓
User: "Intesa, UniCredit, BBVA"  ← 2nd message required
  ↓
System: "Analisi trend banche europee (3 tickers)"
```
**Messages**: 3 (User → System → User → System)  
**Friction**: High (explicit slot-filling)

### After Pattern Weavers (Single-Message Resolution)
```
User: "analizza banche europee"
  ↓
Weaver: Extract concepts (Banking) + regions (Europe) + countries (IT, FR, DE, ES)
  ↓
System: "Analisi trend banche europee (5 tickers trovati automaticamente)"
```
**Messages**: 2 (User → System)  
**Friction**: Low (semantic contextualization)

**Friction Reduction**: 50-66% (1-2 fewer messages)

### Test Results (Jan 3, 2026 - LLM Ontology)
```bash
# Test 1: Italian ESG banking query (LLM)
curl -X POST http://localhost:8017/weave \
  -H "Content-Type: application/json" \
  -d '{"query_text": "analizza banche europee con focus ESG sostenibilità", "user_id": "test"}'

# Result:
# Concepts: ["ESG", "Sustainability"] ✅ (YAML would miss these)
# Sector: Financials (0.95 confidence)
# Region: Europe (0.82 confidence)
# Method: llm_ontology
# Latency: 4783ms
# Cost: $0.00027825

# Test 2: English tech momentum query (LLM)
curl -X POST http://localhost:8017/weave \
  -H "Content-Type: application/json" \
  -d '{"query_text": "tech stocks momentum Asia-Pacific innovation", "user_id": "test"}'

# Result:
# Concepts: ["Innovation"] ✅ (YAML would miss)
# Sector: Information Technology (0.92 confidence)
# Region: Asia-Pacific (0.88 confidence)
# Method: llm_ontology
# Latency: 3359ms
# Cost: $0.00028

# Test 3: Renewable energy ESG (LLM)
curl -X POST http://localhost:8017/weave \
  -H "Content-Type: application/json" \
  -d '{"query_text": "renewable energy companies North America with high ESG score", "user_id": "test"}'

# Result:
# Concepts: ["ESG", "Sustainability"] ✅
# Sector: Utilities (0.90 confidence)
# Region: North America (0.95 confidence)
# Method: llm_ontology
# Latency: 3800ms
# Cost: $0.00028163
```

**Accuracy Improvement**:
- ✅ ESG concept extraction: 0% (YAML) → 100% (LLM)
- ✅ Sustainability recognition: 0% (YAML) → 100% (LLM)
- ✅ Innovation detection: 0% (YAML) → 100% (LLM)
- ✅ Multilingual: 100% (both YAML and LLM)
- ✅ Multi-sector: 100% (both YAML and LLM)

---

## 🛠️ API Reference

### POST /weave
**Purpose**: Extract semantic context from conversational query

**Request**:
```json
{
  "query_text": "analizza banche europee",
  "user_id": "user123",
  "top_k": 5,
  "similarity_threshold": 0.25
}
```

**Response**:
```json
{
  "concepts": ["Banking"],
  "patterns": [
    {
      "type": "region",
      "value": "Europe",
      "confidence": 0.466,
      "countries": ["IT", "FR", "DE", "ES", "UK", "NL", "CH"]
    },
    {
      "type": "concept",
      "value": "Banking",
      "confidence": 0.259,
      "sector": "Financials",
      "region": "Global"
    }
  ],
  "risk_profile": {
    "sector_risk": "medium",
    "dimensions": []
  },
  "latency_ms": 38.82,
  "status": "success",
  "error": null
}
```

**HTTP Codes**:
- `200 OK`: Weaving successful (even if concepts=[], patterns=[])
- `400 Bad Request`: Invalid query_text or missing user_id
- `500 Internal Server Error`: QdrantAgent or PostgreSQL failure

---

## 🔧 Configuration

### Environment Variables
```bash
# Pattern Weavers API
PATTERN_WEAVERS_API_URL=http://vitruvyan_api_weavers:8017

# Redis Cognitive Bus
REDIS_HOST=vitruvyan_redis
REDIS_PORT=6379

# Qdrant
QDRANT_HOST=vitruvyan_qdrant
QDRANT_PORT=6333

# PostgreSQL (Golden Rule: use PostgresAgent, NOT direct connection)
POSTGRES_HOST=172.17.0.1
POSTGRES_PORT=5432
POSTGRES_DB=vitruvyan

# Embedding API (cooperative embedding)
EMBEDDING_API_URL=http://vitruvyan_api_embedding:8010

# Weaver Configuration (✅ ADDED Dec 24, 2025)
WEAVER_TOP_K=5                   # Number of patterns to return (configurable via env)
WEAVER_SIMILARITY_THRESHOLD=0.4  # Minimum cosine similarity (was hardcoded, now configurable)
WEAVER_COLLECTION=weave_embeddings
```

### Docker Compose Service
```yaml
vitruvyan_api_weavers:
  build:
    context: .
    dockerfile: docker/services/api_pattern_weavers/Dockerfile
  ports:
    - "8017:8017"
  environment:
    - REDIS_HOST=vitruvyan_redis
    - REDIS_PORT=6379
    - QDRANT_HOST=vitruvyan_qdrant
    - QDRANT_PORT=6333
    - EMBEDDING_API_URL=http://vitruvyan_api_embedding:8010
    - POSTGRES_HOST=172.17.0.1
    - POSTGRES_PORT=5432
  depends_on:
    - redis
    - qdrant
    - vitruvyan_api_embedding
  networks:
    - vitruvyan-network
  restart: unless-stopped
```

---

## 🧪 Testing

### Unit Tests
```bash
# Test weaver engine (QdrantAgent, cooperative embedding, logging)
pytest tests/unit/test_weaver_engine.py

# Test schemas (WeaverRequest, WeaverResponse validation)
pytest tests/unit/test_weaver_schemas.py
```

### E2E Tests
```bash
# Test UX improvement (friction reduction)
python3 tests/test_weaver_ux_improvement.py

# Test Redis Cognitive Bus integration
docker exec vitruvyan_redis redis-cli PUBLISH "pattern_weavers:weave_request" \
  '{"request_id":"test123","query_text":"analizza banche europee","user_id":"test","top_k":5,"similarity_threshold":0.25}'

# Check PostgreSQL logging
PGPASSWORD='${POSTGRES_PASSWORD}' psql -h 172.17.0.1 -U vitruvyan_user -d vitruvyan \
  -c "SELECT user_id, query_text, concepts, latency_ms FROM weaver_queries ORDER BY created_at DESC LIMIT 5;"
```

### Health Checks
```bash
# API health
curl http://localhost:8017/health

# Prometheus metrics
curl http://localhost:8017/metrics | grep weaver

# Docker logs
docker logs vitruvyan_api_weavers --tail 50

# Redis listener status
docker logs vitruvyan_api_weavers 2>&1 | grep "Pattern Weavers Listener"
```

---

### Performance Metrics

### Latency Benchmarks (Jan 3, 2026 - LLM vs YAML)
**LLM Ontology (Priority 1)**:
- **Typical**: 3.3-4.8 seconds (GPT-4o-mini API roundtrip)
- **Min**: 3.0s (simple queries, low token count)
- **Max**: 5.5s (complex multi-concept queries)
- **Cost**: $0.00027-0.00028 per query (742-751 tokens average)
- **Accuracy**: 95%+ (ESG, sustainability, innovation extraction)

**YAML Fallback (Priority 2)**:
- **Cache Hit**: 3.57-3.91ms (Redis cached embeddings)
- **Cache Miss**: 33.55-49.83ms (cooperative embedding API call)
- **E2E (Redis pub/sub)**: 43.80ms (listener processing)
- **Cost**: $0 (no external API calls)
- **Accuracy**: 70% (limited to 7 base concepts)

**PostgreSQL Logging**: <5ms (cursor() pattern, non-blocking)

### Accuracy Benchmarks (Jan 3, 2026 - LLM vs YAML)
**LLM Ontology**:
- **Concept Extraction**: 95%+ (ESG, Sustainability, Innovation, Risk-Adjusted)
- **Region Extraction**: 90%+ (semantic understanding of "Europe", "North America")
- **Sector Mapping**: 92%+ (GICS sector classification)
- **Multilingual**: 100% (IT, EN, ES, FR supported)
- **Multi-Concept**: 100% ("ESG + sustainability" both extracted)

**YAML Templates (Fallback)**:
- **Concept Extraction**: 50% (3/6 tests) ⚠️ Limited to base 7 concepts
- **Region Extraction**: 83% (5/6 tests) ✅
- **Multilingual**: 100% (1/1 tests) ✅
- **Multi-Sector**: 100% (1/1 tests) ✅

**Cost Analysis**:
- LLM: $0.00028/query × 10K queries/month = **$2.80/month**
- YAML: $0/query (cached) = **$0/month**
- **Trade-off**: +$2.80/month for +45% accuracy gain (worth it for professional use)

---

## 🔄 Integration Guidelines

### Adding Pattern Weavers to LangGraph

**Step 1: Import weaver_node**
```python
# core/langgraph/graph_flow.py
from core.langgraph.node.weaver_node import weaver_node  # ✅ UPDATED Dec 24, 2025 (was: core.pattern_weavers.weaver_node)
```

**Step 2: Add node to graph**
```python
# Add after intent_detection_node
graph.add_node("weavers", weaver_node)
```

**Step 3: Update edges**
```python
# Old routing: intent_detection → ticker_resolver
graph.add_edge("intent_detection", "ticker_resolver")

# New routing: intent_detection → weavers → ticker_resolver
graph.add_edge("intent_detection", "weavers")
graph.add_edge("weavers", "ticker_resolver")
```

**Step 4: Use weaver_context in ticker_resolver**
```python
# core/langgraph/node/ticker_resolver_node.py
def ticker_resolver_node(state: Dict[str, Any]) -> Dict[str, Any]:
    weaver_context = state.get("weaver_context", {})
    
    if weaver_context:
        # Boost query with semantic context
        enriched_query = f"{state['input_text']} {' '.join(weaver_context.get('concepts', []))}"
        tickers = qdrant_agent.search_tickers(enriched_query, filter_regions=weaver_context.get('countries'))
    else:
        # Fallback to original query
        tickers = qdrant_agent.search_tickers(state['input_text'])
    
    return {"tickers": tickers}
```

**Step 5: Rebuild vitruvyan_api_graph**
```bash
docker compose up -d --build vitruvyan_api_graph
```

---

## 🔐 Golden Rules (Copilot Guidance)

### Architecture Rules
✅ **Always use cooperative embedding** - Call `vitruvyan_api_embedding:8010`, NEVER load SentenceTransformer locally  
✅ **Always use PostgresAgent** - `from core.leo.postgres_agent import PostgresAgent`, NEVER `psycopg2.connect()`  
✅ **Always use QdrantAgent** - `from core.leo.qdrant_agent import QdrantAgent`, NEVER `qdrant_client.QdrantClient()`  
✅ **Always use cursor() pattern** - `with self.postgres.connection.cursor() as cur:`, NEVER `self.postgres.connection.execute()`  
✅ **Always log to PostgreSQL** - Every weave operation audited in `weaver_queries` table with method tracking (llm_ontology/yaml_templates)  
✅ **Always broadcast to Cognitive Bus** - Publish events to `cognitive_bus:events` channel  
✅ **LLM-first cascade** - Priority 1: LLM ontology (95% accuracy), Priority 2: YAML fallback (70% accuracy) ✅ **NEW (Jan 3, 2026)**  
✅ **OpenAI dependency** - Ensure openai==1.12.0 in requirements.txt for LLM ontology ✅ **NEW (Jan 3, 2026)**  

### UX Rules
✅ **Non-blocking operation** - If weaving fails, continue with empty context (don't break query flow)  
✅ **Threshold tuning** - Start with 0.25, lower to 0.15 for broader matching  
✅ **Top-K balance** - Default 5 patterns, increase to 10 for multi-sector queries  
✅ **State key consistency** - Always use `state["weaver_context"]`, NEVER `state["patterns"]` or `state["concepts"]`  

### Testing Rules
✅ **Test with diverse queries** - Use `test_weaver_ux_improvement.py`, NOT hardcoded FAANG tickers  
✅ **Test multilingual** - Validate IT/EN/ES/FR support  
✅ **Test Redis pub/sub** - Verify Cognitive Bus integration with real messages  
✅ **Test PostgreSQL logging** - Check `weaver_queries` table for audit trail  

---

### Known Limitations (Jan 3, 2026)
1. **LLM Latency**: 3-5s per query (acceptable for accuracy, but slower than YAML 45ms)
2. **Cost**: $0.00028/query adds $2.80/month for 10K queries (vs $0 for YAML)
3. **API Dependency**: Requires OpenAI API key and internet connection (YAML is local)
4. **Qdrant Collection**: Still 24 base points (LLM extracts dynamically, YAML needs more embeddings)
5. **No Multi-Language Synonyms in YAML**: "Tech" vs "Technology" vs "Tecnologia" not deduplicated (LLM handles this automatically)
6. **Static Risk Profiles**: No dynamic risk calculation (hardcoded high/medium/low in both LLM and YAML)

### Q1 2026 Status — ✅ PHASE 1 COMPLETED (Feb 10-11, 2026)
- ✅ **RiskProfile entity deleted** (epistemic boundary violation fixed)
- ✅ **_aggregate_risk() method eliminated** (41 lines removed)
- ✅ **Charter updated** (pipeline diagram purified)
- ✅ **API surface purified** (no risk_profile in WeaveResult, schemas, routes)
- ✅ **Contract drift fixed** (3 key mismatches resolved)
- ✅ **Service deployed** (port 9017, healthy, main.py 62 lines)
- ✅ **Agnosticization Score**: 26/100 → 60-65/100

### Planned Improvements (Q2 2026 — Phase 2)
- **LLM Caching**: Redis cache for common queries (reduce latency to <500ms for cache hits)
- **Dynamic Risk Scoring**: Integrate with Neural Engine volatility metrics (LLM only, no Pattern Weavers risk logic)
- **Batch Processing**: LLM `batch_recognize()` for multiple queries (reduce cost by 30%)
- **Temporal Context**: "banche nel 2024" → time-aware filtering
- **User Personalization**: Learn user-specific concept mappings (LLM fine-tuning)
- **Target Agnosticization Score**: 75-80/100

---

## 📚 References

### Key Files
- `core/pattern_weavers/llm_ontology_engine.py` (403 lines) - LLM semantic understanding ✅ **NEW (Jan 3, 2026)**
- `core/pattern_weavers/weaver_engine.py` (485 lines) - Core logic with LLM priority cascade ✅ **MODIFIED (Jan 3, 2026)**
- `core/pattern_weavers/redis_listener.py` (250 lines) - Cognitive Bus integration
- `core/langgraph/node/weaver_node.py` (220 lines) - LangGraph node ✅ **MOVED + ENHANCED** (Dec 24, 2025)
- `docker/services/api_pattern_weavers/main.py` (100 lines) - FastAPI service
- `docker/services/api_pattern_weavers/requirements.txt` (12 lines) - Dependencies with openai==1.12.0 ✅ **MODIFIED (Jan 3, 2026)**
- `scripts/init_weave_collection.py` (140 lines) - Qdrant initialization
- `scripts/test_llm_ontology_comparison.py` (280 lines) - LLM vs YAML comparison ✅ **NEW (Jan 3, 2026)**
- `tests/test_weaver_ux_improvement.py` (280 lines) - UX validation suite

### Documentation
- Sacred Orders Pattern: `.github/copilot-instructions.md` (Appendix B)
- RAG System: `.github/Vitruvyan_Appendix_E_RAG_System.md`
- Conversational Architecture: `.github/Vitruvyan_Appendix_G_Conversational_Architecture_V1.md`

### Git History
- Commit: `[TBD]` (Feb 10-11, 2026) - Phase 1 Refactoring (RiskProfile removal, epistemic boundary fix) ✅ **CRITICAL**
- Commit: `[pending]` (Jan 3, 2026) - LLM Ontology Engine integration (403 lines, openai dependency) ✅ **NEW**
- Commit: `43c78e29` (Nov 9, 2025) - Pattern Weavers Sacred Order: REASON (initial implementation)
- Branch: `big-refactor` (7 commits ahead of main)
- Files: 20 changed, 2,344 insertions (403 LLM engine + 1,941 original)

---

## 🎯 Status Summary

**Production Readiness**: ✅ **PRODUCTION-READY + LLM ENHANCED** (Jan 3, 2026)

**What Works**:
- ✅ LLM Ontology Engine (GPT-4o-mini, 95%+ accuracy, $0.00028/query) ✅ **NEW (Jan 3, 2026)**
- ✅ Priority Cascade (LLM → YAML fallback, non-blocking) ✅ **NEW (Jan 3, 2026)**
- ✅ API service (port 8017, FastAPI, dual-process)
- ✅ Redis Cognitive Bus integration (43.80ms latency)
- ✅ PostgreSQL logging (cursor() pattern, audit trail with method tracking)
- ✅ Qdrant collection (24 points, 384D embeddings)
- ✅ Multilingual support (IT/EN/ES/FR)
- ✅ Multi-sector detection (banche + assicurazioni)
- ✅ LangGraph integration (weaver_node in core/langgraph/node/)
- ✅ Prometheus metrics (calls, success, latency, concepts, llm_queries) ✅ **ENHANCED (Jan 3, 2026)**
- ✅ Env vars configuration (WEAVER_TOP_K, WEAVER_SIMILARITY_THRESHOLD, PATTERN_WEAVERS_USE_LLM)
- ✅ Production logging (logger.info/error with context)

**What's New (Jan 3, 2026)**:
- ✅ ESG concept extraction (0% → 100%)
- ✅ Sustainability recognition (0% → 100%)
- ✅ Innovation detection (0% → 100%)
- ✅ Risk-adjusted returns understanding (0% → 100%)
- ✅ Automatic fallback to YAML if LLM fails (resilience)

**Trade-offs**:
- ⚠️ Latency: 3-5s (LLM) vs 45ms (YAML) - acceptable for accuracy
- ⚠️ Cost: $2.80/month (LLM, 10K queries) vs $0 (YAML) - worth it for 95% accuracy
- ⚠️ API dependency: Requires OpenAI API key (YAML is local)

**Next Steps** (Q2 2026 — Phase 2):
1. **Agnosticization Target**: 75-80/100 score (remove remaining finance-specific logic)
2. **LLM Caching**: Redis cache for common queries (reduce latency to <500ms)
3. **Batch Processing**: Optimize LLM batch_recognize() (reduce cost by 30%)
4. **Healthcare Vertical**: Create taxonomy_healthcare.yaml (ICD-10, medical procedures)
5. **Monitor Production**: LLM vs YAML fallback ratio (target 95% LLM, 5% YAML)
6. **YAML Expansion**: 100+ concepts for YAML fallback robustness

---

**Last Updated**: February 14, 2026 (Phase 1 Refactoring Complete — Epistemic Purification)  
**Author**: Vitruvyan Sacred Orders Team  
**Sacred Order**: REASON (Pattern Weavers) — PRODUCTION-READY + LLM ENHANCED
