# _legacy/

> **Pre-refactoring files — DO NOT IMPORT IN NEW CODE.**

These files were moved here during FASE 0 of the Sacred Orders refactoring.
They exist solely because other legacy files still depend on them.
They will be removed entirely after FASE 4 when all consumers are migrated.

## Contents

| File | Lines | Why Legacy | Remove After |
|------|-------|-----------|--------------|
| `docker_manager.py` | 678 | 100% execution (Docker API, container restarts). Violates "judge ≠ executioner" | FASE 4 |
| `git_monitor.py` | 596 | 100% execution (GitPython file scanning). Not a tribunal function | FASE 4 |
| `schema_validator.py` | 267 | 100% finance-specific (pandas, open/close/volume). Domain-specific, not epistemic | FASE 4 |
| `chronicler_agent.py` | 657 | SystemMonitor (psutil, CPU/memory). Wrong identity — Chronicler should be LogDecision engine | FASE 3 |

## Who Still Imports These

- `confessor_agent.py` → imports `docker_manager`, `git_monitor`, `chronicler_agent`
- `services/.../main.py` → imports `chronicler_agent`

These imports will be removed when Confessor is rewritten as a pure consumer (FASE 3).

## Rules

- **❌ DO NOT add new files here**
- **❌ DO NOT import from `_legacy` in new code**
- **❌ DO NOT modify these files** (they are frozen artifacts)
- **✅ These will be deleted** once all dependents are migrated
