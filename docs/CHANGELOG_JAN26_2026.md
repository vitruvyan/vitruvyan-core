# vitruvyan-core Changelog - Jan 26, 2026

## ListenerAdapter ReadOnlyError Fix (Phase 2 Migration Complete)

**Date**: January 25-26, 2026  
**Status**: ✅ PRODUCTION READY  
**Migration Phase**: 2 of 3 (38% complete)

### Problem Summary

All 4 ListenerAdapter-based listeners (Vault Keepers, Memory Orders, Codex Hunters, Babel Gardens) were failing with:

```
redis.exceptions.ReadOnlyError: You can't write against a read only replica.
```

### Root Cause

**Dual Stream Name Bug** in `listener_adapter.py`:
- Line 113: Removed `stream:` prefix before calling `StreamBus.consume()`
- This caused duplicate consumer group creation on two different stream names:
  - `vitruvyan:stream:vault.archive.requested` (correct)
  - `vitruvyan:vault.archive.requested` (legacy, wrong)

### Solution

**2-line fix in `core/cognitive_bus/consumers/listener_adapter.py`**:

1. **Line 113**: Don't remove prefix before consume()
   ```python
   # ❌ BEFORE: channel = stream_name.replace("stream:", "")
   # ✅ AFTER:  channel = stream_name
   ```

2. **Line 152**: Remove BOTH prefixes for legacy handler
   ```python
   # ❌ BEFORE: channel = event.stream.replace("vitruvyan:", "")
   # ✅ AFTER:  channel = event.stream.replace("vitruvyan:", "").replace("stream:", "")
   ```

### Test Results (Jan 25, 2026 20:56 UTC)

| Listener | Event ID | Status | Handler Response |
|----------|----------|--------|------------------|
| Vault Keepers | 1769374415897-0 | ✅ | Archive request received |
| Memory Orders | 1769374613388-0 | ✅ | Memory write requested |
| Codex Hunters | 1769374613389-0 | ✅ | Data refresh expedition started |
| Babel Gardens | 1769374613390-0 | ✅ | Event handled |

**ReadOnlyError Count**: 0/4 listeners (100% clean) ✅

### Migration Progress

**Phase 1 - Native Streams** (1/1): ✅ COMPLETE
- LangGraph listener

**Phase 2 - ListenerAdapter** (4/4): ✅ COMPLETE (Jan 25, 2026)
- Vault Keepers
- Memory Orders
- Codex Hunters
- Babel Gardens

**Phase 3 - Remaining** (8 services): ⏳ PENDING
- Shadow Traders, MCP Server, Gemma, Orthodoxy, Neural, Pattern Weavers, etc.

**Overall**: 5/13 listeners (38% complete)

### Files Updated

**vitruvyan-core**:
- `core/cognitive_bus/consumers/listener_adapter.py` (340 lines, 2 fixes)
- `docs/LISTENER_ADAPTER_READONLYERROR_FIX_JAN25.md` (175 lines)
- `docs/CHANGELOG_JAN26_2026.md` (this file)

**Architecture Principles Validated**:
1. ✅ Stream name normalization must preserve prefixes until handler invocation
2. ✅ ListenerAdapter = zero-code-change bridge (pub/sub → streams)
3. ✅ Consumer groups must use unified namespace with `stream:` prefix
4. ✅ Legacy handlers receive clean channel names (no prefixes)

### References

**Full Documentation**:
- `LISTENER_ADAPTER_READONLYERROR_FIX_JAN25.md` - Complete fix analysis
- `COGNITIVE_BUS_MIGRATION_ROADMAP.md` - Migration strategy
- Appendix L (Copilot Instructions) - Production status

**Git Commit**: Pending sync from vitruvyan → vitruvyan-core

---

**Next Steps**: Phase 3 migration (8 remaining listeners, estimated 2 weeks)
