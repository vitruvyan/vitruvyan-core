# Pattern Weavers Charter - Sacred Order #5

## Identity

**Pattern Weavers** is the semantic contextualization engine of Vitruvyan OS.
We extract structured knowledge from unstructured queries, connecting concepts
to taxonomies through embedding-based similarity and keyword matching.

*"From raw intent, structured meaning emerges."*

## Epistemic Order

**REASON** — We belong to the computational reasoning layer, transforming
raw perception (user queries) into structured semantic representations.

## Sacred Mandate

1. **Extract, never invent** — We discover patterns that exist in the taxonomy,
   never hallucinate categories that don't belong.

2. **Domain agnostic by design** — Taxonomy comes from configuration, not code.
   The same engine serves healthcare, finance, logistics, or any domain.

3. **Graceful degradation** — When embedding services fail, keyword matching
   provides fallback. We never leave a query unanswered.

4. **Semantic precision** — We prefer fewer high-confidence matches over many
   low-confidence ones. Quality over quantity.

## Architectural Invariants

### LIVELLO 1 (This Layer) — Pure Domain

- **Zero I/O**: No database/network/file operations in consumers
- **Taxonomy via config**: All categories loaded from configuration
- **Stateless processing**: Each weave is independent
- **Testable standalone**: Unit tests require no infrastructure

### LIVELLO 2 (Service Layer) — I/O Orchestration

- **Adapters for I/O**: Embedding API, Qdrant, PostgreSQL via adapters
- **Config from env**: All URLs/credentials from environment
- **Thin handlers**: HTTP routes delegate to consumers

## Processing Pipeline

```
Query Text → Preprocessing → Embedding Request (adapter)
                                    ↓
                            Similarity Search (adapter)
                                    ↓
         Result Processing ← Match Filtering ← Threshold
                 ↓
      Risk Aggregation → Concept Extraction → Response
```

## Key Abstractions

| Abstraction | Purpose |
|-------------|---------|
| `PatternConfig` | All configuration (collections, tables, thresholds) |
| `TaxonomyConfig` | Domain taxonomy (loaded from YAML) |
| `WeaverConsumer` | Main weaving logic (pure) |
| `KeywordMatcherConsumer` | Keyword fallback (pure) |
| `PatternMatch` | Single match result |
| `WeaveResult` | Complete operation result |

## Constraints

- **Similarity threshold**: Configurable, default 0.4 (never hardcode)
- **Top-K results**: Configurable, default 10
- **Embedding dimension**: Matches service config (default 384)
- **Query max length**: Configurable, prevents abuse

## Integration Points

| System | Channel | Purpose |
|--------|---------|---------|
| Babel Gardens | HTTP | Embedding generation |
| Qdrant | gRPC | Similarity search |
| StreamBus | Redis Streams | Event communication |
| PostgreSQL | SQL | Audit logging |

## Versioning

- **v1.0.0**: Original finance-specific implementation (legacy)
- **v2.0.0**: Domain-agnostic refactoring (February 2026)
  - SACRED_ORDER_PATTERN compliance
  - Pure consumers in LIVELLO 1
  - Configurable taxonomy
  - No hardcoded domain values

---

*Pattern Weavers — Sacred Order #5*
*"From chaos, patterns. From patterns, understanding."*
