# Cleanup Scripts

Python scripts for automated cleanup of vitruvyan-core.

## Usage

```bash
# Full cleanup (all phases)
python scripts/cleanup/run_cleanup.py

# Dry run (see what would happen)
python scripts/cleanup/run_cleanup.py --dry-run

# Run specific phase only
python scripts/cleanup/run_cleanup.py --phase 1

# Skip confirmation
python scripts/cleanup/run_cleanup.py -y
```

## Phases

| Phase | Script | Description |
|-------|--------|-------------|
| 1 | `01_delete_crewai.py` | Delete CrewAI folder and backup files |
| 2 | `02_remove_crewai_imports.py` | Remove `from crewai import` statements |
| 3 | `03_delete_financial_specific.py` | Delete Mercator-specific files |
| 4 | `04_replace_terminology.py` | Replace ticker→entity_id, etc. |

## Terminology Mapping

| Financial Term | Domain-Agnostic |
|----------------|-----------------|
| `ticker` | `entity_id` |
| `tickers` | `entity_ids` |
| `stock` | `entity` |
| `portfolio` | `collection` |
| `AAPL` | `EXAMPLE_ENTITY_1` |

## After Cleanup

1. **Review changes**: `git diff`
2. **Run tests**: `pytest`
3. **Use Grok** for remaining decisions (edge cases)
4. **Commit**: `git add -A && git commit -m "chore: Core cleanup"`

## What's NOT Automated

These require human/LLM judgment:
- Deciding if a file should be abstracted vs deleted
- Fixing broken imports after deletion
- Updating tests to match new terminology
- Architectural decisions
