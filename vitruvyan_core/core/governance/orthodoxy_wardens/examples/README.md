# examples/

> Usage examples and integration test fixtures for Orthodoxy Wardens.

## Planned Contents

| File | Description |
|------|-------------|
| `example_confession_to_verdict.py` | Full pipeline: Confession → Findings → Verdict |
| `example_verdict_statuses.py` | All 5 verdict statuses with factory methods |
| `example_log_decision.py` | Chronicler LogDecision patterns |
| `example_sacred_role.py` | Implementing a custom SacredRole consumer |

## Purpose

Every example must:
1. Run standalone (`python examples/example_*.py`)
2. Require NO infrastructure (no Redis, no PostgreSQL, no Docker)
3. Demonstrate ONE concept clearly
4. Print human-readable output
