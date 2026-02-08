# 🐙 Migration Guide: Pub/Sub → Redis Streams

## Overview

This guide explains how to migrate existing `redis_listener.py` files from pub/sub to Redis Streams using the **ListenerAdapter** pattern.

---

## Current Architecture (Pub/Sub)

```python
# docker/services/api_vault_keepers/redis_listener.py
class VaultKeepersCognitiveBusListener:
    def __init__(self):
        self.sacred_channels = [
            "vault.archive.requested",
            "vault.restore.requested",
            "vault.snapshot.requested"
        ]
        self.pubsub = self.redis_client.pubsub()
    
    async def begin_sacred_listening(self):
        await self.pubsub.subscribe(*self.sacred_channels)
        async for message in self.pubsub.listen():
            await self.handle_sacred_message(message)
    
    async def handle_sacred_message(self, message):
        if message["type"] == "message":
            channel = message["channel"].decode()
            data = message["data"]
            
            if channel == "vault.archive.requested":
                await self.handle_archive_request(data)
            # ... other handlers
```

---

## Target Architecture (Streams)

### Option 1: Adapter Pattern (Zero Code Change)

Use `ListenerAdapter` to wrap existing listener:

```python
# docker/services/api_vault_keepers/main.py (updated startup)
from core.cognitive_bus.consumers import wrap_legacy_listener

# Existing listener (no changes needed!)
vault_listener = VaultKeepersCognitiveBusListener()

# Wrap with adapter
adapter = wrap_legacy_listener(
    listener_instance=vault_listener,
    name="vault_keepers",
    sacred_channels=vault_listener.sacred_channels,
    handler_method="handle_sacred_message"
)

# Start consuming from streams
await adapter.start()
```

**Benefits**:
- ✅ Zero changes to existing listener code
- ✅ Gradual migration (run both pub/sub and streams during transition)
- ✅ Same handler methods, same message format

**What it does**:
1. Consumes events from Redis Streams (`stream:vault.archive.requested`)
2. Converts stream event → pub/sub message format
3. Calls original `handle_sacred_message()` method
4. Acknowledges event to stream (enables retry on failure)

---

### Option 2: Native Streams (Rewrite)

Inherit from `StreamsEnabledListener`:

```python
# docker/services/api_vault_keepers/redis_listener_v2.py (NEW)
from core.cognitive_bus.consumers import StreamsEnabledListener

class VaultKeepersListener(StreamsEnabledListener):
    def __init__(self):
        super().__init__(
            name="vault_keepers",
            sacred_channels=[
                "vault.archive.requested",
                "vault.restore.requested",
                "vault.snapshot.requested"
            ]
        )
    
    async def handle_event(self, channel: str, event_data: dict):
        """
        Handle stream event directly.
        
        Args:
            channel: "vault.archive.requested"
            event_data: {
                "emitter": "conclave",
                "timestamp": "2026-01-18T21:30:00Z",
                "payload": {...}
            }
        """
        if channel == "vault.archive.requested":
            await self.handle_archive_request(event_data["payload"])
        elif channel == "vault.restore.requested":
            await self.handle_restore_request(event_data["payload"])
        # ... other handlers
```

**Benefits**:
- ✅ Native streams support (no adapter overhead)
- ✅ Access to stream metadata (emitter, timestamp)
- ✅ Cleaner event structure

**When to use**:
- New listeners (no legacy code)
- Listeners that need stream-specific features (replay, position tracking)

---

## Migration Steps

### Phase 1: Dual Mode (Pub/Sub + Streams)

Herald already supports broadcasting to BOTH pub/sub and Streams:

```python
# Herald broadcasts to both
await herald.broadcast(
    domain="vault",
    intent="archive.requested",
    payload=data,
    prefer_streams=True  # Try streams first, fallback to pub/sub
)
```

Run listeners in BOTH modes during transition:

```python
# docker/services/api_vault_keepers/main.py
import asyncio

# Old pub/sub listener (keep running)
old_listener = VaultKeepersCognitiveBusListener()
task1 = asyncio.create_task(old_listener.begin_sacred_listening())

# New streams adapter (run in parallel)
adapter = wrap_legacy_listener(old_listener, "vault_keepers", old_listener.sacred_channels)
task2 = asyncio.create_task(adapter.start())

# Both running in parallel
await asyncio.gather(task1, task2)
```

**Monitor**: Check that streams adapter receives events correctly.

---

### Phase 2: Streams Only

Once validated, disable pub/sub:

```python
# Herald: prefer_streams=True (default)
# Listener: Only adapter running

adapter = wrap_legacy_listener(...)
await adapter.start()  # Pub/sub listener removed
```

---

### Phase 3: Native Streams (Optional)

Rewrite listener to inherit from `StreamsEnabledListener` (see Option 2 above).

---

## Event Format Differences

### Pub/Sub Format (Old)

```python
message = {
    "type": "message",
    "channel": b"vault.archive.requested",
    "data": b'{"ticker": "AAPL", ...}'
}
```

### Streams Format (New)

```python
event = {
    "emitter": "conclave",
    "timestamp": "2026-01-18T21:30:00Z",
    "payload": b'{"ticker": "AAPL", ...}',
    "event_id": "1737236400000-0"
}
```

**ListenerAdapter** converts streams format → pub/sub format automatically.

---

## Benefits of Streams

| Feature | Pub/Sub | Streams |
|---------|---------|---------|
| **Persistence** | No (ephemeral) | Yes (durable) |
| **Replay** | No | Yes (rewind to any position) |
| **Acknowledgment** | No | Yes (retry on failure) |
| **Consumer Groups** | No | Yes (load balancing) |
| **Message Loss** | Possible (if consumer offline) | Impossible (persisted) |
| **Audit Trail** | No | Yes (full event history) |

---

## Testing Checklist

- [ ] Listener receives events from streams
- [ ] Handler methods called correctly
- [ ] Event acknowledgment works (no duplicates)
- [ ] Failure recovery (consumer restart resumes from last ack)
- [ ] Consumer groups work (multiple workers share load)
- [ ] Metrics exposed (events consumed, latency, errors)

---

## Troubleshooting

### Events not received

Check consumer group created:

```python
# Adapter creates group automatically, verify:
redis-cli XINFO GROUPS stream:vault.archive.requested
```

Expected: `group:vault_keepers` exists

### Duplicate events

Ensure events acknowledged:

```python
# Adapter calls this automatically after handler succeeds:
self.stream_bus.ack(stream_name, group_name, event_id)
```

Check pending messages:

```bash
redis-cli XPENDING stream:vault.archive.requested group:vault_keepers
```

### Listener crashes

Events will be retried automatically (not acknowledged).

View pending events:

```bash
redis-cli XREADGROUP GROUP group:vault_keepers consumer1 COUNT 10 STREAMS stream:vault.archive.requested 0
```

---

## Example: Vault Keepers Migration

**Before** (`docker/services/api_vault_keepers/main.py`):

```python
async def start_listener():
    listener = VaultKeepersCognitiveBusListener()
    await listener.begin_sacred_listening()

if __name__ == "__main__":
    asyncio.run(start_listener())
```

**After** (adapter migration):

```python
from core.cognitive_bus.consumers import wrap_legacy_listener

async def start_listener():
    # Keep existing listener code
    listener = VaultKeepersCognitiveBusListener()
    
    # Wrap with adapter
    adapter = wrap_legacy_listener(
        listener_instance=listener,
        name="vault_keepers",
        sacred_channels=listener.sacred_channels
    )
    
    # Start consuming from streams
    await adapter.start()

if __name__ == "__main__":
    asyncio.run(start_listener())
```

**Changes**: 4 lines added, 1 line changed. Zero changes to listener class.

---

## Next Steps

1. **Vault Keepers** (easiest migration)
2. **Codex Hunters**
3. **Babel Gardens**
4. **Memory Orders**
5. **Orthodoxy Wardens** (add `non_liquet` verdict while migrating)

---

## Questions?

See:
- `core/cognitive_bus/consumers/listener_adapter.py` (adapter implementation)
- `core/cognitive_bus/streams.py` (StreamBus API)
- `tests/test_socratic_bus.py` (example consumer test)
