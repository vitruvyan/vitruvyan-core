# Pattern Weavers — Governance Layer

## Purpose

Contains **domain-agnostic rules and quality thresholds** for ontology resolution.

**Design Principle**: Rules are DATA (from taxonomy YAML), not behavior.
- Similarity thresholds configurable per domain
- Taxonomy validation (no hardcoded categories)
- Match quality classification

## Contents (Future)

- `similarity_rules.py`: Confidence thresholds for semantic/keyword/fuzzy matches
- `taxonomy_validator.py`: Ensure taxonomy structure integrity
- `match_classifier.py`: Classify match quality (EXACT, SEMANTIC, KEYWORD, FUZZY)

## Sacred Invariants

1. **No Risk Aggregation**: Extract structure (taxonomy matches), not interpretation (risk scores)
2. **Config-Driven**: All taxonomies from `taxonomy.yaml` (finance, healthcare, legal, etc.)
3. **Generic Thresholds**: Similarity scores [0,1] work for ANY domain
4. **Explainable**: Every match includes `similarity_score`, `match_type`, `metadata`

## Example

```python
from .similarity_rules import SimilarityRules

rules = SimilarityRules(
    semantic_threshold=0.75,  # Generic for all domains
    keyword_threshold=0.60
)

# Applies to finance sectors OR healthcare specialties OR legal categories
assert rules.classify_match(similarity=0.82) == MatchType.SEMANTIC
```

---

**Last Updated**: Feb 12, 2026 (SACRED_ORDER_PATTERN conformance, Phase 1 epistemic boundary fix)
