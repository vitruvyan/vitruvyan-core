# Slot-Filling Architecture Alignment

**Date**: Feb 24, 2026  
**Status**: LLM-FIRST IN VITRUVYAN-CORE  
**Decision**: Slot-filling removed from core orchestration flow

---

## Summary

Slot-filling is deprecated in upstream `vitruvyan` and is now aligned in `vitruvyan-core` for the same conversational reasons:

- Natural language cannot be constrained by static slot templates.
- Template-driven clarification degrades UX and increases forced turns.
- Ambiguous/nuanced user language should be handled by semantic LLM understanding.
- Structured validation is handled by MCP contracts/tool schemas, not by pre-LLM slot checks.

---

## Current Cross-Repository Alignment

| Aspect | Upstream (`vitruvyan`) | This Repo (`vitruvyan-core`) |
|--------|------------------------|------------------------------|
| Slot-filling strategy | Deprecated (LLM-first) | Removed from core flow |
| Unknown intent routing | Semantic/LLM path | `semantic_fallback` |
| Validation model | MCP tool contracts | MCP tool contracts |
| Clarification strategy | Conversational follow-up | Conversational follow-up |

---

## Core Changes Applied (Feb 24, 2026)

### 1. Base composer no longer performs slot checks

- `BaseComposer.compose()` no longer calls domain `slot_filler.check_missing_slots(...)`.
- Legacy `needed_slots/questions` fields are kept only for compatibility in response schema.

### 2. Finance route registry no longer routes unknown to slot_filler

- Removed `slot_filler` route registration from finance route registry.
- Updated mapping:
  - before: `intent=unknown -> slot_filler`
  - now: `intent=unknown -> semantic_fallback`

### 3. LangGraph route targets cleaned

- Removed `slot_filler` from graph route overrides/targets.
- Routing is now consistent with LLM-first orchestration.

---

## Architectural Principle

`vitruvyan-core` should be conversational-first at orchestration level:

1. LLM understanding first (intent + semantic extraction)
2. MCP structured validation/contract enforcement
3. Clarifying questions only when uncertainty remains

No hard slot template gating in core orchestration.

---

## Notes

- Existing `slot_filler` modules may remain in codebase as legacy artifacts during transition, but they are not part of the core orchestration path.
- Domain teams should migrate any remaining slot-template logic toward semantic extraction + MCP-validated execution.
