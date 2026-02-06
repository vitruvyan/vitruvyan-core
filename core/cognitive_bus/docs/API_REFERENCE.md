# Cognitive Bus API Reference

**Version**: 2.0  
**Last Updated**: February 5, 2026

Quick reference for Cognitive Bus APIs. For conceptual understanding, see [COGNITIVE_BUS_GUIDE.md](COGNITIVE_BUS_GUIDE.md).

---

## Table of Contents

1. [StreamBus](#streambus) - Production Redis Streams interface
2. [Herald](#herald) - Convenience wrapper for publishing
3. [Scribe](#scribe) - Logger with bus integration
4. [Event Models](#event-models) - TransportEvent, CognitiveEvent
5. [EventAdapter](#eventadapter) - Serialization bridge
6. [Redis CLI Commands](#redis-cli-commands) - Common operations

---

## StreamBus

**File**: `core/cognitive_bus/streams.py`

### Constructor

```python
StreamBus(
    redis_url: str = "redis://localhost:6379",
    namespace: str = "vitruvyan",
    max_retries: int = 3,
    retry_delay: float = 1.0
)
```

**Parameters**:
- `redis_url`: Redis connection string (master for writes, replicas for reads)
- `namespace`: Prefix for all streams (default: "vitruvyan")
- `max_retries`: Retry count for transient failures
- `retry_delay`: Delay between retries (seconds)

**Example**:
```python
from core.cognitive_bus.streams import StreamBus

bus = StreamBus(redis_url="redis://vitruvyan_redis_master:6379")
```

---

### publish()

```python
publish(
    stream: str,
    event: Dict[str, Any],
    maxlen: Optional[int] = None,
    approximate: bool = True
) -> str
```

Emit event to stream.

**Parameters**:
- `stream`: Channel name (e.g., "codex.discovery.mapped"), auto-prefixed with namespace
- `event`: Event payload (dict, will be JSON-serialized)
- `maxlen`: Max stream length (trim old events if exceeded)
- `approximate`: Use ~ trim (faster, less precise)

**Returns**: Redis event ID (e.g., "1234567890-0")

**Raises**:
- `ConnectionError`: Redis unavailable
- `ResponseError`: Invalid stream name or data

**Example**:
```python
event_id = bus.publish(
    stream="codex.discovery.mapped",
    event={"ticker": "AAPL", "sector": "Technology"}
)
print(f"Published: {event_id}")
```

---

### consume()

```python
consume(
    stream: str,              # Single stream
    consumer_group: str,
    consumer_name: str,
    block_ms: int = 5000,
    count: int = 10,
    start_id: str = ">"
) -> Generator[CognitiveEvent, None, None]

# OR multiple streams

consume(
    streams: List[str],       # Multiple streams
    consumer_group: str,
    consumer_name: str,
    block_ms: int = 5000,
    count: int = 10
) -> Generator[CognitiveEvent, None, None]
```

Consume events from stream(s). **Blocking generator** that yields events.

**Parameters**:
- `stream` / `streams`: Channel name(s) to consume
- `consumer_group`: Consumer group name (load balancing unit)
- `consumer_name`: This consumer's name (unique within group)
- `block_ms`: Block timeout (0 = forever, >0 = milliseconds)
- `count`: Max events per batch
- `start_id`: Start position (">" = new events, "0" = from beginning)

**Yields**: `CognitiveEvent` objects

**Example**:
```python
# Single stream
for event in bus.consume(
    stream="codex.discovery.mapped",
    consumer_group="vault_keepers",
    consumer_name="vault_1"
):
    print(f"Received: {event.data}")
    bus.acknowledge(event.stream, "vault_keepers", event.event_id)

# Multiple streams
for event in bus.consume(
    streams=["codex.discovery.mapped", "neural_engine.screen.completed"],
    consumer_group="vault_keepers",
    consumer_name="vault_1"
):
    print(f"From {event.stream}: {event.data}")
```

---

### acknowledge()

```python
acknowledge(
    stream: str,
    consumer_group: str,
    event_id: str
) -> int
```

Mark event as processed. **CRITICAL**: Always acknowledge after processing to avoid redelivery.

**Parameters**:
- `stream`: Stream name (same as in consume())
- `consumer_group`: Consumer group name
- `event_id`: Event ID from CognitiveEvent.event_id

**Returns**: Number of events acknowledged (1 if successful, 0 if already acked)

**Example**:
```python
for event in bus.consume(...):
    try:
        process(event)
        bus.acknowledge(event.stream, "vault_keepers", event.event_id)
    except Exception as e:
        logger.error("Processing failed, not acknowledging", error=str(e))
```

---

### create_consumer_group()

```python
create_consumer_group(
    stream: str,
    consumer_group: str,
    start_id: str = "0"
) -> None
```

Create consumer group. **Auto-creates stream if missing** (mkstream=True, autonomous consumer pattern).

**Parameters**:
- `stream`: Stream name
- `consumer_group`: Group name
- `start_id`: Start position ("0" = beginning, "$" = end)

**Example**:
```python
# Create before consuming
bus.create_consumer_group("codex.discovery.mapped", "vault_keepers")

# Then consume
for event in bus.consume("codex.discovery.mapped", "vault_keepers", "vault_1"):
    ...
```

**Note**: Idempotent - safe to call multiple times (BUSYGROUP error ignored).

---

### batch_publish()

```python
batch_publish(
    events: List[Tuple[str, Dict[str, Any]]],
    pipeline: bool = True
) -> List[str]
```

Publish multiple events efficiently.

**Parameters**:
- `events`: List of (stream_name, event_dict) tuples
- `pipeline`: Use Redis pipeline (faster for bulk operations)

**Returns**: List of event IDs

**Example**:
```python
event_ids = bus.batch_publish([
    ("codex.discovery.mapped", {"ticker": "AAPL"}),
    ("codex.discovery.mapped", {"ticker": "NVDA"}),
    ("neural_engine.screen.request", {"profile": "momentum"})
])
print(f"Published {len(event_ids)} events")
```

---

### get_stream_info()

```python
get_stream_info(stream: str) -> Dict[str, Any]
```

Get stream metadata (length, consumer groups, etc.).

**Returns**:
```python
{
    "length": 1234,                    # Number of events
    "first-entry": {...},              # Oldest event
    "last-entry": {...},               # Newest event
    "groups": 3,                       # Number of consumer groups
    "radix-tree-keys": 5,              # Internal Redis metric
    "radix-tree-nodes": 10
}
```

**Example**:
```python
info = bus.get_stream_info("codex.discovery.mapped")
print(f"Stream has {info['length']} events")
```

---

## Herald

**File**: `core/cognitive_bus/herald.py`

Convenience wrapper for publishing with auto-prefixing.

### Constructor

```python
Herald(
    service_name: str,
    redis_url: str = "redis://localhost:6379"
)
```

**Parameters**:
- `service_name`: Prepended to event types (e.g., "vault_keepers")
- `redis_url`: Redis connection string

---

### announce()

```python
announce(
    event_type: str,
    data: Dict[str, Any],
    causation_id: Optional[str] = None
) -> str
```

Publish event with service name prefix.

**Parameters**:
- `event_type`: Event type (e.g., "archive.created")
- `data`: Event payload
- `causation_id`: Parent event ID (optional, for causal chains)

**Returns**: Event ID

**Example**:
```python
from core.cognitive_bus.herald import Herald

herald = Herald(service_name="vault_keepers")

# Publishes to: "vault_keepers.archive.created"
herald.announce(
    event_type="archive.created",
    data={"ticker": "AAPL", "rows": 100}
)
```

---

### enable_streams()

```python
enable_streams() -> None
```

Enable Redis Streams mode (default, no-op). Included for backward compatibility with Pub/Sub era.

---

## Scribe

**File**: `core/cognitive_bus/scribe.py`

Logger with triple integration: PostgreSQL + Qdrant + Cognitive Bus.

### Constructor

```python
Scribe(
    service_name: str,
    postgres_agent: Optional[PostgresAgent] = None,
    qdrant_agent: Optional[QdrantAgent] = None,
    redis_url: str = "redis://localhost:6379"
)
```

**Parameters**:
- `service_name`: Service identifier (e.g., "vault_keepers")
- `postgres_agent`: PostgreSQL connection (auto-created if None)
- `qdrant_agent`: Qdrant connection (auto-created if None)
- `redis_url`: Redis connection string

---

### record_event()

```python
record_event(
    event_type: str,
    data: Dict[str, Any],
    causation_id: Optional[str] = None,
    severity: str = "info"
) -> str
```

Log event to all 3 destinations.

**Parameters**:
- `event_type`: Event classification
- `data`: Event details
- `causation_id`: Parent event ID
- `severity`: Log level ("info", "warning", "error")

**Returns**: Event ID

**What It Does**:
1. Logs to PostgreSQL (`event_log` table)
2. Embeds to Qdrant (`semantic_states` collection)
3. Publishes to Cognitive Bus (`{service}.{event_type}` channel)

**Example**:
```python
from core.cognitive_bus.scribe import Scribe

scribe = Scribe(service_name="vault_keepers")

scribe.record_event(
    event_type="archive.completed",
    data={"ticker": "AAPL", "rows": 100, "duration_ms": 250},
    severity="info"
)
```

---

## Event Models

### TransportEvent (Bus Level)

**File**: `core/cognitive_bus/event_envelope.py`

```python
@dataclass(frozen=True)
class TransportEvent:
    stream: str           # Full stream name (e.g., "vitruvyan:stream:codex.discovery.mapped")
    event_id: str         # Redis Streams ID (e.g., "1234567890-0")
    payload: bytes        # JSON-encoded, opaque to bus
    timestamp: datetime   # When event was created
```

**Properties**:
- Immutable (frozen dataclass)
- Bus never inspects payload content
- Serialization/deserialization via EventAdapter

---

### CognitiveEvent (Consumer Level)

```python
@dataclass
class CognitiveEvent:
    event_id: str                      # Unique event ID
    event_type: str                    # Action type (e.g., "ticker_mapped")
    data: Dict[str, Any]               # Domain-specific data
    causation_id: Optional[str] = None # Parent event ID (causal chain)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    stream: str = ""                   # Filled by consumer
```

**Properties**:
- Mutable (consumers can modify)
- Rich domain semantics
- Supports causal chains via causation_id

**Example**:
```python
event = CognitiveEvent(
    event_id="abc123",
    event_type="ticker_mapped",
    data={"ticker": "AAPL", "sector": "Technology"},
    causation_id="xyz789",  # Parent event
    metadata={"user_id": "test"}
)
```

---

## EventAdapter

**File**: `core/cognitive_bus/event_envelope.py`

Bidirectional conversion between TransportEvent (bus) and CognitiveEvent (consumer).

### to_transport()

```python
@staticmethod
def to_transport(
    cognitive: CognitiveEvent,
    stream: str
) -> TransportEvent
```

Convert CognitiveEvent to TransportEvent (serialize for bus).

**Example**:
```python
cognitive = CognitiveEvent(event_id="123", event_type="test", data={"key": "value"})
transport = EventAdapter.to_transport(cognitive, "codex.discovery.mapped")
# transport.payload is JSON-encoded bytes
```

---

### from_transport()

```python
@staticmethod
def from_transport(transport: TransportEvent) -> CognitiveEvent
```

Convert TransportEvent to CognitiveEvent (deserialize from bus).

**Example**:
```python
# Consumer receives TransportEvent from bus
transport = bus.consume(...)
cognitive = EventAdapter.from_transport(transport)
print(cognitive.data)  # Dict[str, Any]
```

---

## Redis CLI Commands

### Stream Operations

```bash
# List all streams
redis-cli KEYS "stream:*"

# Stream length
redis-cli XLEN stream:vitruvyan:codex.discovery.mapped

# Stream info (metadata)
redis-cli XINFO STREAM stream:vitruvyan:codex.discovery.mapped

# Read events (range)
redis-cli XRANGE stream:vitruvyan:codex.discovery.mapped - + COUNT 10

# Read (newest first)
redis-cli XREVRANGE stream:vitruvyan:codex.discovery.mapped + - COUNT 10

# Add test event
redis-cli XADD stream:vitruvyan:codex.discovery.mapped '*' ticker AAPL sector Technology

# Trim stream (keep last 1000)
redis-cli XTRIM stream:vitruvyan:codex.discovery.mapped MAXLEN ~ 1000
```

### Consumer Group Operations

```bash
# List consumer groups
redis-cli XINFO GROUPS stream:vitruvyan:codex.discovery.mapped

# List consumers in group
redis-cli XINFO CONSUMERS stream:vitruvyan:codex.discovery.mapped vault_keepers

# Create consumer group
redis-cli XGROUP CREATE stream:vitruvyan:codex.discovery.mapped vault_keepers 0 MKSTREAM

# Delete consumer group
redis-cli XGROUP DESTROY stream:vitruvyan:codex.discovery.mapped vault_keepers

# Pending events (not acknowledged)
redis-cli XPENDING stream:vitruvyan:codex.discovery.mapped vault_keepers

# Detailed pending
redis-cli XPENDING stream:vitruvyan:codex.discovery.mapped vault_keepers - + 10

# Claim stuck event (if consumer died)
redis-cli XCLAIM stream:vitruvyan:codex.discovery.mapped vault_keepers vault_2 60000 1234567890-0
```

### Debugging Commands

```bash
# Check Redis connection
redis-cli PING

# Check memory usage
redis-cli INFO memory

# Check replication status
redis-cli INFO replication

# Monitor all commands (real-time)
redis-cli MONITOR

# Check slow queries
redis-cli SLOWLOG GET 10
```

---

## Environment Variables

```bash
# Redis connection
REDIS_URL=redis://vitruvyan_redis_master:6379

# PostgreSQL (for Scribe)
POSTGRES_HOST=161.97.140.157
POSTGRES_USER=vitruvyan_user
POSTGRES_PASSWORD=@Caravaggio971
POSTGRES_DB=vitruvyan

# Qdrant (for Scribe)
QDRANT_URL=http://vitruvyan_qdrant:6333

# Service name (for Herald/Scribe)
SERVICE_NAME=vault_keepers
```

---

## Error Codes

### ResponseError: BUSYGROUP

**Meaning**: Consumer group already exists.

**Action**: Ignore (idempotent operation).

```python
try:
    bus.create_consumer_group("stream", "group")
except ResponseError as e:
    if "BUSYGROUP" in str(e):
        pass  # Already exists, OK
    else:
        raise
```

---

### ResponseError: NOGROUP

**Meaning**: Consumer group doesn't exist.

**Action**: Create consumer group first.

```python
bus.create_consumer_group("stream", "group")
bus.consume("stream", "group", "consumer")
```

---

### ReadOnlyError

**Meaning**: Tried to write to read-only replica.

**Action**: Connect to master for writes.

```python
# ✅ CORRECT: Master
bus = StreamBus(redis_url="redis://vitruvyan_redis_master:6379")

# ❌ WRONG: Replica
bus = StreamBus(redis_url="redis://vitruvyan_redis_replica_1:6379")
```

---

### ConnectionError

**Meaning**: Redis unavailable.

**Action**: Check Redis container running, verify network connectivity.

```bash
docker ps | grep redis
docker logs vitruvyan_redis_master
ping vitruvyan_redis_master
```

---

## Performance Tips

1. **Batch Publishing**: Use `batch_publish()` for multiple events (faster than individual publish()).

2. **Consumer Count**: Tune `count` parameter (default 10). Higher = fewer roundtrips, but more memory.

3. **Block Timeout**: Set `block_ms=0` for infinite blocking (lowest latency), or >0 for periodic checks.

4. **Acknowledgment**: Acknowledge immediately after processing (not in batches) to avoid redelivery.

5. **Trim Streams**: Set `maxlen` in publish() or use XTRIM to prevent unbounded growth.

```python
# Trim to last 10,000 events (approximate)
bus.publish("stream", event, maxlen=10000, approximate=True)
```

---

## See Also

- **[COGNITIVE_BUS_GUIDE.md](COGNITIVE_BUS_GUIDE.md)**: Complete implementation guide with philosophy, patterns, and troubleshooting
- **[ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md)**: Historical decision log
- **[BUS_ARCHITECTURE.md](BUS_ARCHITECTURE.md)**: Deep dive into architecture
- **[Vitruvyan_Bus_Invariants.md](Vitruvyan_Bus_Invariants.md)**: Sacred Invariants explanation

---

**End of API Reference** | Version 2.0 | February 5, 2026
