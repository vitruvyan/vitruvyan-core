# Redis Streams Architecture — Vitruvyan Core

**Status**: ✅ Operational (2026-01-18)  
**Repositories**: `vitruvyan-core`, `vitruvyan` (mercator)

---

## Overview

Redis Streams provides **durable, replayable event transport** for the Vitruvyan Cognitive Bus. This is **Level 1 architecture** — pure transport with zero interpretation.

### When to Use Pub/Sub vs Streams

| Feature | Pub/Sub | Streams |
|---------|---------|---------|
| **Persistence** | ❌ Fire-and-forget | ✅ Durable |
| **Replay** | ❌ No history | ✅ Full history |
| **Consumer Groups** | ❌ No | ✅ Yes |
| **Acknowledgment** | ❌ No | ✅ At-least-once |
| **Latency** | <1ms | ~5ms |
| **Use Case** | Real-time notifications | Critical events, audit trail |

**Rule of Thumb**:
- **Pub/Sub**: Health checks, metrics, real-time dashboards
- **Streams**: Data ingestion, audit logs, event sourcing

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 0: Redis Infrastructure                              │
│  - Redis 7.2+ (Streams support)                             │
│  - Persistence: AOF + RDB                                   │
│  - Replication: Optional (master-replica)                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 1: Cognitive Bus (streams.py)                        │
│  - StreamBus class (transport only)                         │
│  - emit(): Publish events                                   │
│  - consume(): Subscribe with consumer groups                │
│  - ack(): Acknowledge processing                            │
│  INVARIANT: The bus NEVER interprets payload content        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 2+: Vertical Services (domain-specific)              │
│  - Entity Indexer                                           │
│  - Codex Hunters                                            │
│  - Memory Orders                                            │
│  - Audit Engine                                             │
│  RESPONSIBILITY: Assign meaning to events                   │
└─────────────────────────────────────────────────────────────┘
```

---

## API Reference

### Produce Events

```python
from core.foundation.cognitive_bus import StreamBus

bus = StreamBus(host='localhost', port=6379)

# Emit event (opaque payload to the bus)
event_id = bus.emit(
    channel="codex:entity_updated",
    payload={"entity_id": "E123", "action": "create"},
    emitter="codex-hunter",
    correlation_id="batch-42"  # Optional chain tracking
)

# Returns: "1768750948214-0" (Redis-assigned ID)
```

### Consume Events (Consumer Groups)

```python
from core.foundation.cognitive_bus import StreamBus

bus = StreamBus(host='localhost', port=6379)

# Create consumer group (idempotent)
bus.create_consumer_group("codex:entity_updated", "indexer-group")

# Consume in blocking loop
for event in bus.consume(
    channel="codex:entity_updated",
    group="indexer-group",
    consumer="worker-1",
    count=10,       # Batch size
    block_ms=5000   # Timeout
):
    # Process event (vertical-specific logic)
    process_entity(event.payload)
    
    # ACK after successful processing
    bus.ack(event, "indexer-group")
```

### Replay Historical Events

```python
# Read without consumer group (for debugging/backfilling)
events = bus.replay(
    channel="codex:entity_updated",
    start_id="0",   # Beginning
    end_id="+",     # Latest
    count=100
)

for event in events:
    print(event.event_id, event.payload)
```

---

## StreamEvent Structure

```python
@dataclass
class StreamEvent:
    stream: str                    # "vitruvyan:codex:entity_updated"
    event_id: str                  # "1768750948214-0"
    emitter: str                   # "codex-hunter"
    payload: Dict[str, Any]        # Opaque data
    timestamp: str                 # ISO 8601
    correlation_id: Optional[str]  # Optional chain tracking
```

**CRITICAL**: The bus sees `payload` as opaque bytes. Only the vertical assigns meaning.

---

## Consumer Groups

Consumer groups enable **cooperative consumption** — multiple workers process events in parallel, each event delivered to ONE worker.

```
Stream: codex:entity_updated
├─ Group: entity-indexer-group
│  ├─ Consumer: worker-1 (PID 1234)
│  ├─ Consumer: worker-2 (PID 1235)
│  └─ Consumer: worker-3 (PID 1236)
│
└─ Group: audit-logger-group
   └─ Consumer: logger-1 (PID 1300)
```

**Key Points**:
- Each group maintains its own read position
- Events are delivered to ONE consumer per group
- Un-ACKed events are redelivered after timeout
- Groups can start from `"0"` (beginning) or `"$"` (new only)

---

## Durability Guarantees

### At-Least-Once Delivery

```python
for event in bus.consume(...):
    try:
        process(event)
        bus.ack(event, group)  # ✅ Success, remove from pending
    except Exception as e:
        # ❌ Don't ACK — event will be redelivered
        logger.error(f"Failed: {e}")
```

### Exactly-Once (Idempotency Pattern)

```python
def process_idempotent(event):
    # Check if already processed (external deduplication)
    if db.exists(event.event_id):
        return  # Skip duplicate
    
    # Process
    result = do_work(event.payload)
    
    # Mark as processed
    db.save(event.event_id, result)
```

---

## Stream Management

### Check Stream Health

```python
info = bus.stream_info("codex:entity_updated")
print(f"Length: {info['length']}")
print(f"Groups: {len(info['groups'])}")
```

### Monitor Pending Events

```python
pending = bus.pending("codex:entity_updated", "indexer-group")
print(f"Unacked: {pending['pending_count']}")
```

### Trim Old Events

```python
# Keep last 100K events (approximate)
removed = bus.trim("codex:entity_updated", max_len=100_000)
```

### Delete Stream (Danger!)

```python
# Only for testing/cleanup
bus.delete_stream("test:entity_updated")
```

---

## Examples

### Producer

```bash
cd vitruvyan-core

# Emit 10 events
python3 examples/stream_producer_example.py --count 10

# Custom channel and rate
python3 examples/stream_producer_example.py \
  --channel "test:entity" \
  --count 100 \
  --delay 0.1
```

### Consumer

```bash
# Start worker (blocks until Ctrl+C)
python3 examples/stream_worker_example.py

# Environment variables
export STREAM_CHANNEL="codex:entity_updated"
export CONSUMER_GROUP="my-indexer-group"
export CONSUMER_NAME="worker-$(hostname)"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"

python3 examples/stream_worker_example.py
```

### Multiple Workers (Horizontal Scaling)

```bash
# Terminal 1
CONSUMER_NAME=worker-1 python3 examples/stream_worker_example.py

# Terminal 2
CONSUMER_NAME=worker-2 python3 examples/stream_worker_example.py

# Terminal 3
CONSUMER_NAME=worker-3 python3 examples/stream_worker_example.py

# Now produce 100 events — they'll be distributed across 3 workers
python3 examples/stream_producer_example.py --count 100
```

---

## Level 1 Enforcement — Invariants

### ✅ ALLOWED (Level 1 Operations)

- `emit(channel, payload)` — Transport bytes
- `consume(channel, group, consumer)` — Deliver bytes
- `ack(event, group)` — Mark delivered
- `replay(channel)` — Retrieve history
- `stream_info(channel)` — Get metadata

### ❌ FORBIDDEN (Level 2+ Operations)

The bus MUST NOT:
- Inspect payload content
- Filter events by payload fields
- Transform payload structure
- Correlate events
- Route based on payload values
- Validate business logic

**Rationale**: The bus is "humble" — it doesn't know what the data means. Only verticals interpret.

---

## Configuration

### Environment Variables

```bash
# Producer/Consumer config
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_PASSWORD="secret"  # Optional
export REDIS_DB="0"

# Stream config
export STREAM_CHANNEL="codex:entity_updated"
export CONSUMER_GROUP="entity-indexer-group"
export CONSUMER_NAME="worker-$(hostname)-$(date +%s)"
```

### Stream Retention

Default retention (defined in `streams.py`):

```python
DEFAULT_MAX_LEN = 100_000         # Keep last 100K events
DEFAULT_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000  # 7 days
```

Override per-stream:

```python
bus.emit(channel, payload, max_len=50_000)  # Custom retention
```

---

## Performance

### Latency

| Operation | Latency |
|-----------|---------|
| `emit()` | ~5ms |
| `consume()` (batch of 10) | ~10ms |
| `ack()` | ~1ms |
| `replay()` | ~50ms for 100 events |

### Throughput

- **Single producer**: ~200 events/sec
- **Single consumer**: ~100 events/sec (with processing)
- **3 consumers**: ~300 events/sec (linear scaling)

### Memory

- ~500 bytes per event (average)
- 100K events ≈ 50 MB RAM

---

## Troubleshooting

### Events Not Being Consumed

```bash
# Check if consumer group exists
redis-cli XINFO GROUPS vitruvyan:codex:entity_updated

# Check pending events
redis-cli XPENDING vitruvyan:codex:entity_updated entity-indexer-group
```

### Worker Crashed — Resume Processing

No action needed! Un-ACKed events automatically redelivered after timeout.

```python
# Just restart the worker
python3 examples/stream_worker_example.py
```

### Clear Stuck Consumer

```bash
# If a consumer died and left pending events
redis-cli XGROUP DELCONSUMER \
  vitruvyan:codex:entity_updated \
  entity-indexer-group \
  dead-worker-name
```

### Reset Consumer Group

```bash
# Start from beginning (re-process all)
redis-cli XGROUP SETID vitruvyan:codex:entity_updated entity-indexer-group 0

# Start from latest (skip history)
redis-cli XGROUP SETID vitruvyan:codex:entity_updated entity-indexer-group $
```

---

## Migration from Pub/Sub

### Before (Pub/Sub)

```python
from core.cognitive_bus import get_redis_bus

bus = get_redis_bus()
bus.publish("codex:entity_updated", {"entity_id": "E123"})

# Subscriber must be online to receive
```

### After (Streams)

```python
from core.cognitive_bus import StreamBus

bus = StreamBus()
bus.emit("codex:entity_updated", {"entity_id": "E123"})

# Events persist — subscribers can be offline
```

**Migration Strategy**:
1. Keep Pub/Sub for real-time notifications
2. Add Streams for critical events
3. Gradually migrate audit-critical channels to Streams

---

## Future Enhancements

### Q1 2026
- [ ] Dead letter queue (DLQ) for failed events
- [ ] Automatic retry with exponential backoff
- [ ] Prometheus metrics integration
- [ ] Stream mirroring (multi-datacenter)

### Q2 2026
- [ ] Event schema validation (Orthodoxy Wardens integration)
- [ ] Event versioning support
- [ ] Time-travel replay (point-in-time recovery)
- [ ] Cross-vertical event correlation (Level 2)

---

## References

- **Redis Streams Docs**: https://redis.io/docs/data-types/streams/
- **Vitruvyan Bus Invariants**: `Vitruvyan_Bus_Invariants.md`
- **Vitruvyan Epistemic Charter**: `Vitruvyan_Epistemic_Charter.md`
- **Examples**: `examples/stream_*_example.py`

---

**Last Updated**: 2026-01-18  
**Implemented By**: Vitruvyan Core Team  
**Status**: ✅ Production Ready
