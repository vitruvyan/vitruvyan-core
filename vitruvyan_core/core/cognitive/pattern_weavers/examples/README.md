# Pattern Weavers — Usage Examples

## Purpose

Standalone executable scripts demonstrating Pattern Weavers functionality.

**Requirement**: Examples run with ZERO infrastructure (no Postgres, Qdrant, Redis, Docker).
Use in-memory data structures and mock dependencies.

## Available Examples (Future)

### Basic Usage
- `basic_taxonomy_matching.py`: Load taxonomy YAML, match query text to categories
- `keyword_fallback.py`: Demonstrate graceful degradation when embeddings unavailable

### Advanced Patterns
- `multi_taxonomy_fusion.py`: Combine finance + healthcare taxonomies for hybrid domains
- `custom_similarity_threshold.py`: Configure thresholds for different use cases

### Domain-Specific
- `finance_sector_resolution.py`: Map query to financial sectors
- `healthcare_specialty_matching.py`: Map symptoms to medical specialties
- `legal_jurisdiction_classifier.py`: Map case descriptions to legal categories

## Running Examples

```bash
# No dependencies needed (pure Python)
cd vitruvyan_core/core/cognitive/pattern_weavers/
python examples/basic_taxonomy_matching.py
```

---

**Last Updated**: Feb 12, 2026
