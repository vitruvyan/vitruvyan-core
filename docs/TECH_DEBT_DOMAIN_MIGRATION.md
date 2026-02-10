# Technical Debt: Domain-Specific Module Migration

**Created**: 2026-02-07  
**Priority**: Medium  
**Status**: Tracked (deprecation notices added)

---

## Overview

During the LangGraph domain-agnostic refactoring, we identified several modules in `core/` that contain finance-specific logic. These should be migrated to `domains/finance/` to maintain the "core stays generic" invariant.

## Identified Modules for Migration

### Synaptic Conclave Consumers
| Current Location | Target Location | Finance References |
|-----------------|-----------------|-------------------|
| `core/synaptic_conclave/consumers/narrative_engine.py` | `domains/finance/consumers/narrative_engine.py` | VEE integration, ticker narratives |
| `core/synaptic_conclave/consumers/risk_guardian.py` | `domains/finance/consumers/risk_guardian.py` | Portfolio volatility, concentration risk |

### Synaptic Conclave Listeners  
| Current Location | Target Location | Finance References |
|-----------------|-----------------|-------------------|
| `core/synaptic_conclave/listeners/shadow_traders.py` | `domains/finance/listeners/shadow_traders.py` | Trading events, portfolio updates |
| `core/synaptic_conclave/listeners/codex_hunters.py` | `domains/finance/listeners/codex_hunters.py` | Ticker data collection, fundamentals |
| `core/synaptic_conclave/listeners/vault_keepers.py` | `domains/finance/listeners/vault_keepers.py` | Screening archives, ticker snapshots |

### LLM Prompts (Deprecation Notice Added)
| Current Location | Action |
|-----------------|--------|
| `core/llm/prompts/scenario_prompts.py` | Finance-specific prompts - marked deprecated |
| `core/llm/conversational_llm.py` | Portfolio methods - marked deprecated |

## What Stays in Core

These modules are **domain-agnostic infrastructure** and should remain:

- `core/synaptic_conclave/consumers/base_consumer.py` - ABC for all consumers
- `core/synaptic_conclave/consumers/registry.py` - Consumer registration
- `core/synaptic_conclave/consumers/working_memory.py` - Memory abstraction
- `core/synaptic_conclave/listeners/listener_adapter.py` - Adapter pattern
- `core/synaptic_conclave/listeners/babel_gardens.py` - Language/emotion (domain-agnostic)
- `core/synaptic_conclave/listeners/langgraph.py` - Graph orchestration
- `core/synaptic_conclave/listeners/mcp.py` - MCP integration
- `core/synaptic_conclave/transport/` - All transport layer
- `core/synaptic_conclave/events/event_envelope.py` - Event contracts

## Migration Strategy

When migrating these modules:

1. **Create target directory structure**:
   ```
   domains/finance/
   ├── consumers/
   │   ├── __init__.py
   │   ├── narrative_engine.py
   │   └── risk_guardian.py
   └── listeners/
       ├── __init__.py
       ├── shadow_traders.py
       ├── codex_hunters.py
       └── vault_keepers.py
   ```

2. **Update imports in moved modules**:
   - Core infrastructure imports remain: `from core.synaptic_conclave.consumers.base_consumer import BaseConsumer`
   - Finance-specific imports become relative: `from ..events import FinanceEvent`

3. **Create backward-compatible shims** (optional for gradual migration):
   ```python
   # core/synaptic_conclave/consumers/narrative_engine.py
   import warnings
   warnings.warn(
       "Import from domains.finance.consumers.narrative_engine instead",
       DeprecationWarning,
       stacklevel=2
   )
   from domains.finance.consumers.narrative_engine import *
   ```

4. **Update service registrations** to use new paths

## Dependencies to Consider

Before migration, audit these dependencies:

- **PostgresAgent / QdrantAgent**: Core agents, imports stay unchanged
- **EventHunter**: Finance-specific, may need co-migration  
- **VEEEngine**: Finance-specific, already referenced from domain
- **StreamBus**: Core transport, imports stay unchanged

## Completed Cleanup (Pre-Migration)

Already cleaned during refactoring:

- ✅ Removed `create_finance_registry()` from `core/orchestration/intent_registry.py`
- ✅ Removed `create_finance_registry()` from `core/orchestration/route_registry.py`
- ✅ Cleaned AAPL/MSFT references in `core/neural_engine/scoring.py`
- ✅ Cleaned AAPL/MSFT references in `core/neural_engine/engine.py`
- ✅ Created `domains/finance_plugin.py` with `FinanceGraphPlugin`
- ✅ Created `domains/finance/` with ResponseFormatter, SlotFiller

## Success Criteria

Migration is complete when:

1. No finance-specific logic in `core/synaptic_conclave/consumers/` (except base classes)
2. No finance-specific logic in `core/synaptic_conclave/listeners/` (except adapters and domain-agnostic listeners)
3. All finance consumers/listeners work from `domains/finance/`
4. Tests pass with new import paths
5. Deprecation warnings removed from shim files (if used)

---

## References

- [copilot-instructions.md](../.github/copilot-instructions.md) - "Core stays generic" invariant
- [Synaptic Conclave Architecture](../.github/Vitruvyan_Appendix_L_Synaptic_Conclave.md)
- [LangGraph Refactoring Analysis](../LANGGRAPH_AGNOSTIC_REFACTORING_ANALYSIS.md)
