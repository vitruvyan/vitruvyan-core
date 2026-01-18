# 🕸️ Pattern Weavers — Semantic Contextualization Layer

**Epistemic Order**: REASON (Semantic)  
**Status**: ✅ PRODUCTION READY (Nov 9, 2025)  
**Sacred Order**: #5 (peer to Babel Gardens, Codex Hunters, Memory Orders, Vault Keepers)

---

## Purpose

Pattern Weavers enriches financial analysis with **semantic understanding** by connecting:
- **Concepts** (Banking, Technology, Clean Energy)
- **Sectors** (Financials, Healthcare, Consumer Discretionary)
- **Regions** (Europe, North America, Asia-Pacific)
- **Risk Profiles** (Volatility, Liquidity, Concentration)

---

## Architecture

```
User Query → LangGraph (intent_detection) → Pattern Weavers (weaver_node) → 
EntityId Resolver → Neural Engine → VEE → Response
```

**Integration Point**: `core/langgraph/graph_flow.py`
- Node: `weaver_node` (between intent_detection and entity_resolver)
- State key: `state["weaver_context"]` (concepts + patterns)

---

## Components

### Core Logic
- `weaver_engine.py` — Main Pattern Weaver engine (QdrantAgent + cooperative embedding)
- `weaver_client.py` — REST client for API calls

### LangGraph Integration
- `weaver_node.py` — LangGraph node for semantic enrichment

### Configuration
- `config/weave_rules.yaml` — Sectors, regions, risk profiles mapping

### Modules
- `modules/concept_mapper.py` — Extract concepts from query text
- `modules/risk_profiler.py` — Match risk patterns
- `modules/pattern_matcher.py` — Semantic similarity matching

### Schemas
- `schemas/weaver_request.py` — Pydantic request models
- `schemas/weaver_response.py` — Pydantic response models

---

## API Service

**Port**: 8011  
**Container**: `vitruvyan_api_weavers`  
**Health**: `http://localhost:8011/health`

### Endpoints
- `POST /weave` — Main weaving endpoint
- `GET /health` — Service health check
- `GET /metrics` — Prometheus metrics

---

## Qdrant Collection

**Name**: `weave_embeddings`  
**Dimensions**: 384 (MiniLM-L6-v2)  
**Points**: Base concepts from `weave_rules.yaml`  
**Metric**: Cosine similarity

### Point Schema
```json
{
  "id": "uuid-v5-deterministic",
  "vector": [384 floats],
  "payload": {
    "name": "Banking",
    "type": "concept",
    "sector": "Financials",
    "region": "Global",
    "risk_level": "medium",
    "keywords": ["bank", "financial", "credit", "lending"],
    "created_at": "2025-11-09T17:30:00Z"
  }
}
```

---

## PostgreSQL Logging

**Table**: `weaver_queries`

```sql
CREATE TABLE weaver_queries (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    query_text TEXT NOT NULL,
    concepts JSONB,
    patterns JSONB,
    latency_ms FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Usage Example

```python
from vitruvyan_os.core.cognitive.pattern_weavers.weaver_engine import PatternWeaverEngine

# Initialize
weaver = PatternWeaverEngine()

# Weave query
result = weaver.weave(
    query_text="analizza i titoli bancari europei",
    user_id="test_user"
)

# Result
{
    "concepts": ["Banking", "Europe"],
    "patterns": [
        {"type": "sector", "value": "Financials", "confidence": 0.92},
        {"type": "region", "value": "Europe", "confidence": 0.89}
    ],
    "risk_profile": {"volatility": "medium", "liquidity": "high"}
}
```

---

## Observability

### Prometheus Metrics
- `weaver_queries_total` — Total queries processed
- `weaver_query_duration_seconds` — Query latency histogram
- `weaver_concepts_found_total` — Concepts extracted

### Logs
- All queries logged to PostgreSQL (`weaver_queries` table)
- All errors logged via `PostgresAgent` audit trail

---

## Testing

### E2E Test
```bash
curl -X POST http://localhost:8004/run \
  -H "Content-Type: application/json" \
  -d '{"input_text": "analizza i titoli bancari europei", "user_id": "test"}'
```

**Expected**:
- `state["weaver_context"]` populated
- `concepts: ["Banking", "Europe"]`
- `patterns: [{type: "sector", value: "Financials"}, {type: "region", value: "Europe"}]`

### Unit Tests
```bash
pytest tests/unit/test_pattern_weavers.py -v
```

---

## Deployment

```bash
# Initialize Qdrant collection
python scripts/init_weave_collection.py

# Build and run API service
docker compose up -d --build vitruvyan_api_weavers

# Rebuild LangGraph with weaver_node
docker compose up -d --build vitruvyan_api_graph

# Verify health
curl http://localhost:8011/health
```

---

## Roadmap

- **Q4 2025**: Base implementation (sectors, regions, concepts)
- **Q1 2026**: Risk profiling integration with VARE
- **Q2 2026**: Dynamic concept learning (user feedback)
- **Q3 2026**: Multi-hop reasoning (concept chaining)
- **Q4 2026**: Cross-lingual semantic expansion

---

**Last Updated**: November 9, 2025  
**Author**: Sacred Orders — Pattern Weavers  
**Status**: ✅ PRODUCTION READY
