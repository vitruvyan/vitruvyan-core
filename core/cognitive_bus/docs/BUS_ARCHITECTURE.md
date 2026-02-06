# Vitruvyan Cognitive Bus Architecture (v2.0)
**Sacred Order: Cognitive Substrate**  
**Last Updated**: January 24, 2026  
**Status**: Production-Ready

---

## Executive Summary

Vitruvyan's Cognitive Bus is a **Redis Streams-based event backbone** providing durable, ordered, and scalable event distribution across distributed Sacred Order services.

**Key Facts**:
- **Single Transport**: Redis Streams (Pub/Sub archived as of Jan 24, 2026)
- **2-Layer Event Model**: TransportEvent (bus level) + CognitiveEvent (consumer level)
- **Causal Event Chain**: Every event can spawn children with parent reference
- **4 Enforced Invariants**: No payload inspection, no correlation, no semantic routing, no synthesis
- **Durable Replay**: Full event history accessible via stream replay

---

## Architecture Diagram

```
Producer Service                          Consumer Service
       |                                         |
       | emit(channel, payload)        read_async(stream, group)
       v                                         ^
┌──────────────────────────────────────────────────────┐
│            StreamBus (Transport Layer)               │
│  - Redis Streams XADD / XREADGROUP                   │
│  - TransportEvent (immutable, frozen dataclass)      │
│  - Invariants enforced via _validate_invariants()    │
│  - ACK / NACK / Replay support                       │
└──────────────────────────────────────────────────────┘
               │                    │
          XADD │                    │ XREADGROUP
               v                    v
         Redis Streams (vitruvyan:*)
           - Durable storage
           - Consumer groups for load balancing
           - Pending entries list (PEL)
           - TTL 7 days (MAXLEN)

┌──────────────────────────────────────────────────────┐
│          EventAdapter (Conversion Layer)             │
│  - transport_to_cognitive(): Stream→Type mapping     │
│  - cognitive_to_transport(): Type→Stream mapping     │
│  - Extracts trace_id, causation_id from payload      │
└──────────────────────────────────────────────────────┘
               │                    │
               v                    v
         CognitiveEvent         CognitiveEvent
        (consumer layer)       (consumer layer)
               │                    │
               v                    v
        BaseConsumer.process()  BaseConsumer.emit()
               │                    │
               └────────────────────┘
                   Causal Chain
            (parent → child via event.id)
```

---

## Layer 1: TransportEvent (Bus Level)

**Purpose**: Immutable representation of events **AT REST** in Redis Streams.

**Dataclass** (`event_envelope.py` line 32-89):
```python
@dataclass(frozen=True)  # Immutable
class TransportEvent:
    stream: str               # "vitruvyan:domain:intent"
    event_id: str             # Redis-assigned "1737734400000-0"
    emitter: str              # Source service name
    payload: Dict[str, Any]   # OPAQUE to bus (JSON serializable)
    timestamp: str            # ISO 8601 UTC
    correlation_id: Optional[str]  # External session ID
```

**Key Methods**:
- `to_redis_fields() → Dict[str, str]`: Serialize for XADD
- `from_redis(stream, msg_id, fields) → TransportEvent`: Deserialize from XREADGROUP

**Constraints**:
- **Frozen dataclass** = once created, cannot mutate
- Bus NEVER inspects `payload` content (see INVARIANT 1)
- `stream` is namespace only, not semantic routing key

---

## Layer 2: CognitiveEvent (Consumer Level)

**Purpose**: Mutable representation with **CAUSAL CHAIN** semantics for consumers.

**Dataclass** (`event_envelope.py` line 95-172):
```python
@dataclass  # Mutable
class CognitiveEvent:
    id: str                    # UUID
    type: str                  # "babel.sentiment_detected"
    correlation_id: str        # Session/conversation ID
    causation_id: str          # Parent event ID
    trace_id: str              # Root event ID (distributed tracing)
    timestamp: datetime
    source: str                # Emitter service
    payload: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def child(self, type: str, payload: Dict) -> CognitiveEvent:
        """Create child event with causal chain preserved."""
        return CognitiveEvent(
            type=type,
            correlation_id=self.correlation_id,
            causation_id=self.id,  # Parent reference
            trace_id=self.trace_id,  # Root preserved
            source=self.source,
            payload=payload
        )
```

**Key Feature**: `child()` method preserves causal chain:
```
Event A (trace_id=ROOT)
  └─> Event B (causation_id=A.id, trace_id=ROOT)
       └─> Event C (causation_id=B.id, trace_id=ROOT)
```

---

## EventAdapter (Layer Conversion)

**Purpose**: Bidirectional conversion between TransportEvent and CognitiveEvent.

**Methods** (`event_envelope.py` line 180-269):

### transport_to_cognitive()
Converts Redis Streams message → Consumer event.

**Logic**:
1. Extract `type` from stream name: `"vitruvyan:babel:sentiment"` → `"babel.sentiment"`
2. Extract causal fields (`trace_id`, `causation_id`) from payload
3. Generate UUID if not present
4. Return mutable CognitiveEvent

### cognitive_to_transport()
Converts Consumer event → Redis Streams message.

**Logic**:
1. Convert `type` to stream name: `"babel.sentiment"` → `"vitruvyan:babel:sentiment"`
2. Inject causal fields into payload
3. Return frozen TransportEvent

---

## StreamBus API

**File**: `core/cognitive_bus/streams.py` (522 lines)

### Core Methods

#### emit(channel, payload, emitter, correlation_id) → str
Publish event to Redis Streams.

**Redis Command**: `XADD vitruvyan:{channel} * emitter {emitter} payload {json} timestamp {iso8601}`

**Returns**: Event ID (`"1737734400000-0"`)

#### consume(stream_name, group, consumer, count, block_ms) → Generator[TransportEvent]
Pull events from stream (blocking).

**Redis Command**: `XREADGROUP GROUP {group} {consumer} STREAMS {stream} > COUNT {count} BLOCK {block_ms}`

**Yields**: TransportEvent instances

#### ack(event, group) → bool
Acknowledge processed event.

**Redis Command**: `XACK {stream} {group} {event_id}`

#### replay(stream_name, start_id, count) → List[TransportEvent]
Retrieve historical events.

**Redis Command**: `XRANGE {stream} {start_id} + COUNT {count}`

### Async Wrappers (Phase 3)

#### async connect() → bool
Async Redis connection via `asyncio.to_thread`.

#### async read_async(stream, group, consumer, count, block_ms) → List[TransportEvent]
Async wrapper for `consume()` generator.

**Used by**: BaseConsumer._consume_loop()

---

## BaseConsumer Integration

**File**: `core/cognitive_bus/consumers/base_consumer.py` (466 lines)

### _consume_loop() (lines 330-406)

**Flow** (fully integrated as of Phase 3):
1. `await bus.connect()` — Establish async Redis connection
2. `asyncio.to_thread(bus.create_consumer_group)` — Ensure group exists
3. `transport_events = await bus.read_async()` — Pull batch of TransportEvents
4. `cognitive_event = EventAdapter.transport_to_cognitive(te)` — Convert to CognitiveEvent
5. `result = await self.process(cognitive_event)` — Consumer business logic
6. `asyncio.to_thread(bus.ack, transport_event, group)` — ACK after success
7. Handle ProcessResult actions (emit, escalate, log)

**Key Integration Points**:
- Uses **real StreamBus methods** (no mocks)
- EventAdapter handles layer conversion
- ACK only after successful processing (at-least-once delivery)

---

## Bus Invariants (Enforced)

**Documented**: `streams.py` lines 86-117 + `Vitruvyan_Bus_Invariants.md`

### INVARIANT 1: Bus NEVER inspects payload content
- Payload is `Dict[str, Any]` — **OPAQUE** to bus
- Bus only serializes/deserializes JSON
- **NO** conditional logic based on payload keys/values

**Example Violation** (FORBIDDEN):
```python
if payload.get("priority") == "urgent":
    route_to_high_priority_queue()  # ❌ INVARIANT VIOLATION
```

### INVARIANT 2: Bus NEVER correlates events
- Bus doesn't understand causal chains
- `correlation_id`, `trace_id` are just strings to bus
- **Correlation logic lives in consumers** (Layer 2)

**Example Violation** (FORBIDDEN):
```python
if event.correlation_id == previous_event.correlation_id:
    merge_events()  # ❌ INVARIANT VIOLATION
```

### INVARIANT 3: Bus NEVER does semantic routing
- Stream names are **namespaces**, not routing keys
- Bus doesn't route based on event type
- **Consumers subscribe to streams they care about**

**Example Violation** (FORBIDDEN):
```python
if event.type == "babel.sentiment":
    route_to_babel_service()  # ❌ INVARIANT VIOLATION (this was herald.py's sin)
```

### INVARIANT 4: Bus NEVER synthesizes events
- Bus only transports what it receives
- **NO** automatic event generation
- **NO** event transformation

**Example Violation** (FORBIDDEN):
```python
if event.type == "risk.detected":
    emit_auto_hedging_event()  # ❌ INVARIANT VIOLATION
```

### Enforcement Mechanisms

1. **Code Review**: All StreamBus changes reviewed for invariant compliance
2. **Runtime Validation**: `_validate_invariants()` checks payload is dict
3. **Architectural Separation**: Herald.py (semantic routing) archived Jan 24, 2026
4. **Documentation**: Invariants in code comments + Markdown

---

## Migration: Pub/Sub → Redis Streams

**Date**: January 24, 2026 (Phase 0: Bus Hardening)

### Archived Modules (`/archive/pub_sub_legacy/`)
1. `heart.py`: ConclaveHeart (async Pub/Sub publishing)
2. `herald.py`: ConclaveHerald (semantic routing — **VIOLATED INVARIANT 3**)
3. `redis_client.py`: RedisBusClient (Pub/Sub wrapper)
4. `scribe.py`: Event persistence (depended on Pub/Sub)
5. `pulse.py`: System heartbeat monitor
6. `orthodoxy_adaptation_listener.py`: Pub/Sub listener

### Why Removed?
- **Herald violated invariants**: Inspected event types, routed based on meaning
- **Dual transport**: Pub/Sub + Streams caused architectural ambiguity
- **No durability**: Pub/Sub messages lost if consumer offline
- **No ordering**: Pub/Sub doesn't guarantee message order
- **No replay**: Cannot retrieve historical Pub/Sub messages

### Migration Path
**Old** (Pub/Sub):
```python
from core.cognitive_bus import heart
await heart.publish("babel.sentiment", payload)
```

**New** (Redis Streams):
```python
from core.cognitive_bus import StreamBus
bus = StreamBus()
bus.emit("vitruvyan:babel:sentiment", payload, emitter="my_service")
```

---

## E2E Testing

**File**: `tests/test_bus_integration_e2e.py` (302 lines)

**7 Integration Tests** (all passing as of Jan 24, 2026):

1. **test_bus_connection**: StreamBus connects to Redis
2. **test_async_connection**: Async wrapper functional
3. **test_emit_and_consume**: emit → consume → ACK flow
4. **test_replay**: Historical event retrieval
5. **test_baseconsumer_integration**: BaseConsumer uses real bus
6. **test_consumer_group_load_balancing**: Events distributed across workers
7. **test_event_adapter_bidirectional**: EventAdapter converts correctly both ways

**Run Tests**:
```bash
cd /home/caravaggio/vitruvyan
PYTHONPATH=$PWD:$PYTHONPATH python3 tests/test_bus_integration_e2e.py
```

**Expected Output**:
```
================================================================================
✅ ALL E2E TESTS PASSED (7/7)
================================================================================
```

---

## Performance Characteristics

- **Latency**: <10ms emit, <50ms consume (local Redis)
- **Throughput**: ~10K events/sec per stream (single Redis instance)
- **Durability**: Events persist until MAXLEN exceeded (7 days TTL)
- **Ordering**: Total order within single stream
- **Scalability**: Horizontal via consumer groups (multiple workers)
- **Replay Cost**: O(N) where N = count parameter (efficient range scan)

---

## Deployment

### Docker Compose
```yaml
vitruvyan_redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data
```

### Environment Variables
```bash
REDIS_HOST=vitruvyan_redis  # Docker service name
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=<optional>
```

---

## Troubleshooting

### Consumer not receiving events
**Check**:
1. Consumer group created? `bus.create_consumer_group(stream, group)`
2. Events in stream? `bus.replay(stream, "0", 10)`
3. Consumer stuck on old event? Check PEL: `XPENDING stream group`

### Events not ACKed
**Check**:
1. ACK called after processing? `bus.ack(event, group)`
2. Exception in process()? Check logs
3. Consumer crashed before ACK? Events in PEL, will be re-delivered

### Memory usage growing
**Check**:
1. MAXLEN configured? `XTRIM stream MAXLEN ~ 10000`
2. ACKs happening? Un-ACKed events stay in PEL
3. Too many consumer groups? Each group stores offset

---

## References

- **Event Envelope Design**: `core/cognitive_bus/event_envelope.py` (330 lines)
- **StreamBus Implementation**: `core/cognitive_bus/streams.py` (522 lines)
- **BaseConsumer Integration**: `core/cognitive_bus/consumers/base_consumer.py` (466 lines)
- **E2E Tests**: `tests/test_bus_integration_e2e.py` (302 lines)
- **Invariants**: `core/cognitive_bus/Vitruvyan_Bus_Invariants.md`
- **Migration Guide**: `/archive/pub_sub_legacy/README.md`

**Git Commit**: [Pending] "feat: Phase 0 - Bus Hardening (Redis Streams canonical)"

---

## Version History

- **v2.0** (Jan 24, 2026): Redis Streams canonical, Pub/Sub archived, 2-layer event model, BaseConsumer integration, E2E tests
- **v1.0** (Jan 19, 2026): Initial Pub/Sub + Streams hybrid implementation

---

**Status**: ✅ PRODUCTION READY  
**Last Validated**: January 24, 2026 (E2E tests 7/7 passing)
