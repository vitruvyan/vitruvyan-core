# Finance Vertical - Pattern Weavers Domain Pack

Last updated: 2026-02-23

## Scope

Finance domain pack for `api_pattern_weavers`.
Core Pattern Weavers remains domain-agnostic; this package contributes finance
taxonomy and finance-specific scoring helpers.

## Activation

- `PATTERN_DOMAIN=finance`
- Optional override: `PATTERN_TAXONOMY_PATH=/custom/path/taxonomy.yaml`
- Default taxonomy path:
  `vitruvyan_core/domains/finance/pattern_weavers/taxonomy_finance.yaml`

## Package Content

| File | Role |
|---|---|
| `taxonomy_finance.yaml` | Canonical finance ontology/taxonomy |
| `financial_context.py` | Finance query detection helper |
| `sector_resolver.py` | Multilingual sector alias resolver (`sector_mappings`) |
| `weave_config.py` | Finance thresholds and category score boosts |

## Runtime Notes

- Ontology execution lives in `services/api_pattern_weavers`; this package only
  provides domain configuration and helper logic.
- `SectorResolver` uses an injected DB fetch function and does not manage
  connections directly.
- Regex is used only for keyword tokenization in alias lookup; ontology classes
  are sourced from taxonomy and semantic pipeline, not from hardcoded templates.

## Tests

```bash
pytest -q vitruvyan_core/domains/finance/pattern_weavers/tests
```
