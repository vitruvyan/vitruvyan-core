# api_conclave - Refactoring Required (Feb 6, 2026)

## Status
⚠️ **BLOCKED** - Uses deprecated Pub/Sub API, needs full migration to Streams

## Problem
`services/governance/api_conclave/` still uses legacy Cognitive Bus Pub/Sub API that was removed in FASE 4:

**File**: `services/governance/api_conclave/main.py` (line 24-27)
```python
from vitruvyan_core.core.foundation.cognitive_bus import (
    get_heart, get_herald, get_pulse, get_scribe, get_lexicon,
    publish_event, subscribe_to_domain, start_system_pulse
)
```

**File**: `services/governance/api_conclave/api_conclave/main_conclave.py`
- Same deprecated imports

## Why This is Complex
- Not just changing import path
- Entire service architected around Pub/Sub (synchronous)
- Needs migration to Streams (asynchronous, consumer groups)
- Requires understanding service's role in system (appears to be central hub/router)

## Migration Requirements

### 1. Replace Factory Functions
```python
# OLD (Pub/Sub)
heart = get_heart()
herald = get_herald()
scribe = get_scribe()
heart.publish(event)
heart.subscribe(channel, handler)

# NEW (Streams)
from core.cognitive_bus.transport.streams import StreamBus
bus = StreamBus(redis_url="redis://vitruvyan_redis:6379")
bus.emit(channel, event_data)
# For consumption: create streams_listener.py wrapper
```

### 2. Create Listener
Pattern: `services/governance/api_conclave/streams_listener.py`
- Use ListenerAdapter like vault_keepers/orthodoxy_wardens
- Define sacred channels for conclave
- Wrap existing logic in async handler

### 3. Update Docker
- Add streams_listener container to docker-compose
- Remove Pub/Sub-specific environment variables
- Update health checks for Streams

## Recommended Approach
1. **Audit**: Understand conclave's role (central router? message broker?)
2. **Extract handlers**: Identify all heart.subscribe() callbacks
3. **Create listener**: Wrap handlers with ListenerAdapter
4. **Parallel run**: Deploy Streams alongside Pub/Sub temporarily
5. **Cutover**: Switch to Streams, keep Pub/Sub as fallback
6. **Remove legacy**: Delete Pub/Sub code after 1 week validation

## Alternative: Deprecate Service
If conclave is no longer needed (Streams handle routing natively), consider:
- Mark service as deprecated
- Migrate functionality to other services
- Remove from docker-compose

## Priority
**LOW** - Service appears isolated, not blocking other work
**Timeframe**: Q1 2026 (after listener migration Phase 2 complete)

## Related Files
- `services/governance/api_conclave/main.py`
- `services/governance/api_conclave/api_conclave/main_conclave.py`
- `scripts/cleanup/02_remove_crewai_imports.py` (mentions conclave, low priority)

---
**Created**: Feb 6, 2026
**Last Updated**: Feb 6, 2026
