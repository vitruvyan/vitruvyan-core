# VSGS — Vitruvyan Semantic Grounding System v2.0

**Domain-agnostic semantic context enrichment engine.**

VSGS transforms user queries into semantically grounded context by searching
historical conversation embeddings. It contains **zero domain knowledge** —
all it does is: embed text, search vectors, classify matches, return results.

---

## What is VSGS?

VSGS is one of the proprietary algorithms in VPAR (Vitruvyan Proprietary Algorithms Repository).
It answers the question: **"What relevant context exists for this query?"**

Given any text input, VSGS:
1. Generates a 384-dimensional embedding (via MiniLM-L6-v2 API)
2. Searches Qdrant for the top-k semantically similar past interactions
3. Classifies each match as "high", "medium", or "low" quality
4. Returns a structured `GroundingResult` with typed `SemanticMatch` objects

---

## Architecture

VSGS follows the two-level VPAR pattern:

```
LIVELLO 1: Pure Engine (this module)
  core/vpar/vsgs/
  ├── types.py          Pure dataclasses (zero I/O)
  ├── vsgs_engine.py    VSGSEngine: embed → search → classify → return
  └── __init__.py       Public exports

LIVELLO 2: Thin Adapter (LangGraph node)
  orchestration/langgraph/node/semantic_grounding_node.py
  └── Reads state → calls VSGSEngine.ground() → writes state

Related Infrastructure:
  governance/semantic_sync/vsgs_sync.py   PostgreSQL ↔ Qdrant sync
  monitoring/vsgs_metrics.py              Prometheus metric definitions
```

### Pipeline

```
  Input text + user_id
        │
        ▼
┌──────────────────┐
│  Phase 1: Embed  │  HTTP POST → embedding API (MiniLM-L6-v2, 384-dim)
│  (httpx, lazy)   │  Timeout: 3s (configurable)
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Phase 2: Search │  Qdrant top-k search, filtered by user_id
│  (QdrantAgent)   │  Collection: semantic_states (configurable)
└──────┬───────────┘
       │
       ▼
┌────────────────────┐
│  Phase 3: Classify │  Score thresholds → "high" / "medium" / "low"
│  (pure logic)      │  Configurable: high=0.8, medium=0.6
└──────┬─────────────┘
       │
       ▼
  GroundingResult
    .matches: List[SemanticMatch]
    .status:  "enabled" | "disabled" | "error" | "skipped"
    .elapsed_ms: float
```

### File Map

| File | Lines | Responsibility |
|------|------:|----------------|
| `types.py` | 80 | `GroundingConfig`, `SemanticMatch`, `GroundingResult` — pure dataclasses |
| `vsgs_engine.py` | 184 | `VSGSEngine` — embed, search, classify, format |
| `__init__.py` | 23 | Public API exports |

---

## Data Types

### GroundingConfig

```python
@dataclass
class GroundingConfig:
    enabled: bool = False             # Feature flag (VSGS_ENABLED env var)
    top_k: int = 3                    # Max results to return
    collection: str = "semantic_states"  # Qdrant collection name
    high_threshold: float = 0.8       # Score > this → "high" quality
    medium_threshold: float = 0.6     # Score > this → "medium" quality
    prompt_budget_chars: int = 800    # Max chars for context injection
    embedding_timeout: float = 3.0    # Embedding API timeout (seconds)
    search_timeout: float = 5.0       # Qdrant search timeout (seconds)
```

### SemanticMatch

```python
@dataclass
class SemanticMatch:
    text: str                  # Original query text
    score: float               # Cosine similarity (0.0–1.0)
    quality: str               # "high", "medium", "low"
    intent: Optional[str]      # Detected intent of matched query
    language: Optional[str]    # Language of matched query
    timestamp: Optional[str]   # When the matched query was made
    trace_id: Optional[str]    # Trace ID for audit
    metadata: Dict[str, Any]   # Full Qdrant payload
```

### GroundingResult

```python
@dataclass
class GroundingResult:
    matches: List[SemanticMatch]  # Ordered by score descending
    status: str                   # "enabled", "disabled", "error", "skipped"
    elapsed_ms: float             # Total processing time
    error: Optional[str]          # Error message (if status == "error")

    # Convenience properties
    top_score → float             # Highest match score (0.0 if empty)
    match_count → int             # Number of matches
    to_state_dict() → Dict        # Convert to LangGraph state fields
```

---

## Usage

### Standalone (REPL, script, test)

```python
from core.vpar.vsgs import VSGSEngine, GroundingConfig

config = GroundingConfig(enabled=True, top_k=3)
engine = VSGSEngine(config=config, embedding_url="http://localhost:8010")

result = engine.ground("analyze recent trends", user_id="user_42")

print(result.status)        # "enabled"
print(result.match_count)   # 3
print(result.top_score)     # 0.87

for match in result.matches:
    print(f"  [{match.quality}] {match.score:.3f} — {match.text}")
```

### As LangGraph Node (production)

The node is a thin adapter — it reads state, calls `VSGSEngine.ground()`,
and writes the result back to state:

```python
# In graph_flow.py
from core.orchestration.langgraph.node.semantic_grounding_node import semantic_grounding_node

g.add_node("semantic_grounding", semantic_grounding_node)
g.add_edge("babel_emotion", "semantic_grounding")
g.add_edge("semantic_grounding", "params_extraction")
```

The node reads these state fields:
- `input_text` — text to ground
- `user_id` — user context filter
- `intent` — detected intent (for metrics)
- `language` — detected language (for metrics)

And writes:
- `semantic_matches` — `List[Dict]` (serialized `SemanticMatch` objects)
- `vsgs_status` — `"enabled"` / `"disabled"` / `"error"` / `"skipped"`
- `vsgs_elapsed_ms` — processing time in milliseconds

### Embedding Only (ingestion)

```python
embedding = engine.embed_only("store this text for future retrieval")
# Returns List[float] (384 dimensions)
# Use this to ingest into Qdrant without searching
```

---

## Configuration (Environment Variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `VSGS_ENABLED` | `0` | Master feature flag (`0` = disabled, `1` = enabled) |
| `VSGS_GROUNDING_TOPK` | `3` | Number of semantic matches to return |
| `VSGS_COLLECTION_NAME` | `semantic_states` | Qdrant collection to search |
| `VSGS_PROMPT_BUDGET_CHARS` | `800` | Max context chars for downstream nodes |
| `EMBEDDING_API_URL` | (from `api_config`) | Embedding service endpoint |

---

## Downstream Usage

Downstream LangGraph nodes use `state["semantic_matches"]` to:

| Use Case | Example |
|----------|---------|
| **Infer missing parameters** | "E SHOP?" → check context for previous intent |
| **Preserve intent** | "anche" → same intent as previous query |
| **Adapt language** | Italian context → continue in Italian |
| **Enrich explanations** | Reference past analysis in VEE narratives |

---

## Differences from v1.0

| Aspect | v1.0 (Nov 2025) | v2.0 (Feb 2026) |
|--------|-----------------|-----------------|
| **Location** | Embedded in 432-line node | Extracted to `vpar/vsgs/` engine |
| **Node size** | 432 lines (fat node) | 99 lines (thin adapter) |
| **Reusability** | LangGraph-only | Any context (API, batch, REPL) |
| **Thresholds** | Hardcoded 0.8 / 0.6 | Configurable via `GroundingConfig` |
| **Types** | Raw dicts | Typed `SemanticMatch`, `GroundingResult` |
| **Dependencies** | `core.foundation.persistence` (dead path) | `core.agents.qdrant_agent` (correct) |
| **Error handling** | Exception propagation | Graceful `GroundingResult(status="error")` |
| **Testing** | Required Docker + Qdrant + Embedding API | Engine mockable, types pure Python |

---

## Invariants

1. **VSGSEngine contains zero domain knowledge.** It embeds, searches, classifies. Period.
2. **All thresholds are configurable.** No magic numbers in the engine.
3. **Infrastructure is lazy-loaded.** `httpx.Client` and `QdrantAgent` are created on first use.
4. **The LangGraph node is a thin adapter.** All logic lives in `VSGSEngine`.
5. **Graceful degradation.** Disabled → `GroundingResult(status="disabled")`. Error → `status="error"` with message. Never crashes the pipeline.
6. **QdrantAgent only** for vector operations — no raw `qdrant_client` in the engine.
