# Pattern Weavers — Unit Tests

## Purpose

Pure unit tests for LIVELLO 1 domain logic (no infrastructure dependencies).

**Requirements**:
- ✅ Run standalone: `pytest pattern_weavers/tests/`
- ❌ NO Docker, Postgres, Qdrant, Redis
- ✅ Mock external dependencies (embeddings, databases)
- ✅ Test pure functions: consumers, domain objects, governance rules

## Test Structure

```
tests/
├── test_domain.py              # Frozen dataclasses validation
├── test_consumers.py           # WeaveConsumer, KeywordMatcher
├── test_governance.py          # Similarity rules, taxonomy validation
├── test_config.py              # YAML loading, multi-taxonomy merge
└── fixtures/                   # Test data (YAML taxonomies, sample queries)
    ├── test_taxonomy.yaml
    └── sample_queries.json
```

## Running Tests

```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest vitruvyan_core/core/cognitive/pattern_weavers/tests/

# With coverage
pytest --cov=vitruvyan_core.core.cognitive.pattern_weavers \
       --cov-report=html \
       vitruvyan_core/core/cognitive/pattern_weavers/tests/
```

## Test Coverage Goals

- **Domain objects**: 100% (immutable dataclasses, validation)
- **Consumers (pure logic)**: 95%+
- **Governance rules**: 90%+
- **Config loading**: 85%+

---

**Last Updated**: Feb 12, 2026
