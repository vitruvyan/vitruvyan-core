# Vitruvyan Cognitive Bus - Complete Implementation Guide

**Version**: 2.0  
**Last Updated**: February 5, 2026  
**Status**: Production  
**Architecture**: Redis Streams (canonical since Jan 24, 2026)

---

## Table of Contents

1. [Philosophy & Vision](#1-philosophy--vision)
2. [Core Architecture](#2-core-architecture)
3. [Implementation Guide](#3-implementation-guide)
4. [Common Patterns & Recipes](#4-common-patterns--recipes)
5. [Troubleshooting](#5-troubleshooting)

---

## 1. Philosophy & Vision

### 1.1 Why This Architecture Exists

Vitruvyan's Cognitive Bus is inspired by **two biological systems** that achieve resilience without centralized control:

1. **Octopus Neural System**: 2/3 of neurons are in the arms, not the brain
   - Arms can act autonomously (catch prey while brain focuses elsewhere)
   - If one arm is damaged, the rest continue functioning
   - No single point of failure

2. **Fungal Mycelial Networks**: No central processor
   - Self-organizing routing (nutrients flow to where they're needed)
   - Topological resilience (cut a path, network reroutes around it)
   - Emergent intelligence from simple local rules

**Mapping to Vitruvyan**:
- **Consumers** = Octopus arms (autonomous, self-initializing)
- **Bus** = Mycelial network (dumb transport, no intelligence)
- **Events** = Nutrients (payload opaque to network)

### 1.2 The 4 Sacred Invariants

These are **architectural laws** that MUST NEVER be violated:

```
❌ FORBIDDEN #1: Bus NEVER inspects payload content
   - Bus is semantically blind
   - No "if event.data.ticker == 'AAPL'" logic in bus code

❌ FORBIDDEN #2: Bus NEVER correlates events
   - No "wait for event B before delivering event A"
   - Consumer handles correlation, not bus

❌ FORBIDDEN #3: Bus NEVER does semantic routing
   - Routing by namespace only (e.g., "codex.discovery.mapped")
   - No "route financial events to service X" logic

❌ FORBIDDEN #4: Bus NEVER creates events autonomously
   - Bus is passive transport only
   - Only consumers/publishers emit events
```

**Why These Exist**:
- Keep bus simple and fast (no complex logic)
- Intelligence belongs in consumers (octopus arms), not network
- Easier to debug (bus is predictable, dumb layer)

### 1.3 Key Principle: Consumer Autonomy

**CRITICAL DECISION** (February 5, 2026):

```python
# ✅ CORRECT: Consumers create infrastructure when needed
self.client.xgroup_create(stream, group, mkstream=True)

# ❌ WRONG: Wait for publisher to create stream
self.client.xgroup_create(stream, group, mkstream=False)  # Fails if stream doesn't exist
```

**Rationale**:
- **Octopus Model**: Arms don't wait for brain permission to initialize
- **Mycelial Model**: Network self-organizes, nodes create connections when needed
- **Engineering**: Eliminates chicken-and-egg problem (consumers wait for publishers, publishers never emit)

**Exception**: Read-only replicas can't create streams. Fallback to `mkstream=False` in this case.

---

## 2. Core Architecture

### 2.1 Redis Streams (Canonical Architecture)

**Technology Stack**:
- **Redis Streams**: Durable, ordered, at-least-once delivery
- **Consumer Groups**: Load balancing across multiple consumers
- **Master + Replicas**: High availability (write to master, read from any)

**Why Not Pub/Sub?**:
- ❌ No durability (message lost if consumer offline)
- ❌ No replay (can't reprocess past events)
- ❌ No load balancing (all consumers get all messages)
- ✅ Streams solve all 3 problems

### 2.2 The 2-Layer Event Model

```
┌─────────────────────────────────────────────────────────┐
│ CONSUMER LAYER (CognitiveEvent)                         │
│ - Mutable                                               │
│ - Causal chain (causation_id references parent)        │
│ - Domain semantics (e.g., ticker="AAPL")               │
└─────────────────────────────────────────────────────────┘
                          ↕️
             EventAdapter.to_transport()
                          ↕️
┌─────────────────────────────────────────────────────────┐
│ BUS LAYER (TransportEvent)                              │
│ - Immutable (frozen dataclass)                          │
│ - Opaque payload (bus never inspects)                   │
│ - Metadata only (stream, event_id, timestamp)           │
└─────────────────────────────────────────────────────────┘
```

**Key Classes**:

1. **TransportEvent** (bus level):
```python
@dataclass(frozen=True)
class TransportEvent:
    stream: str           # e.g., "vitruvyan:stream:codex.discovery.mapped"
    event_id: str         # Redis Streams ID (e.g., "1234567890-0")
    payload: bytes        # JSON-encoded, opaque to bus
    timestamp: datetime
```

2. **CognitiveEvent** (consumer level):
```python
@dataclass
class CognitiveEvent:
    event_id: str
    event_type: str       # e.g., "ticker_mapped"
    data: Dict[str, Any]  # Domain data (ticker, score, etc.)
    causation_id: Optional[str]  # Parent event ID for causal chain
    metadata: Dict[str, Any]
```

3. **EventAdapter** (bridge):
```python
class EventAdapter:
    @staticmethod
    def to_transport(cognitive: CognitiveEvent) -> TransportEvent:
        """Convert consumer event to bus event (serialize)"""
        payload = json.dumps(cognitive.__dict__).encode('utf-8')
        return TransportEvent(stream=..., payload=payload, ...)
    
    @staticmethod
    def from_transport(transport: TransportEvent) -> CognitiveEvent:
        """Convert bus event to consumer event (deserialize)"""
        data = json.loads(transport.payload.decode('utf-8'))
        return CognitiveEvent(**data)
```

### 2.3 Core Components

#### StreamBus (Production Interface)

**File**: `core/cognitive_bus/streams.py`

```python
from core.cognitive_bus.streams import StreamBus

bus = StreamBus(redis_url="redis://localhost:6379")

# Publish event
bus.publish(
    stream="codex.discovery.mapped",
    event={"ticker": "AAPL", "sector": "Technology"}
)

# Consume events (blocking)
for event in bus.consume(
    stream="codex.discovery.mapped",
    consumer_group="vault_keepers",
    consumer_name="vault_1"
):
    print(f"Received: {event.data}")
    bus.acknowledge(stream, consumer_group, event.event_id)
```

**Key Methods**:
- `publish(stream, event)`: Emit event to stream
- `consume(stream, group, consumer)`: Read events (blocking generator)
- `acknowledge(stream, group, event_id)`: Mark event as processed
- `create_consumer_group(stream, group)`: Initialize consumer group (with `mkstream=True`)

#### Herald (Convenience Wrapper)

**File**: `core/cognitive_bus/herald.py`

```python
from core.cognitive_bus.herald import Herald

herald = Herald(service_name="vault_keepers")

# Publish with auto-prefixing
herald.announce("codex.discovery.mapped", {"ticker": "AAPL"})

# Subscribe to channel (legacy Pub/Sub compatibility)
herald.enable_streams()  # Use Streams instead of Pub/Sub
```

**When to Use**:
- ✅ Service needs simple publish interface
- ✅ Want auto-prefixing (service_name prepended to event_type)
- ❌ Need fine-grained control (use StreamBus directly)

#### Scribe (Logger Interface)

**File**: `core/cognitive_bus/scribe.py`

```python
from core.cognitive_bus.scribe import Scribe

scribe = Scribe(service_name="vault_keepers")

# Log with automatic enrichment
scribe.record_event(
    event_type="archive.completed",
    data={"ticker": "AAPL", "rows": 100}
)
```

**What It Does**:
- Logs to PostgreSQL (audit trail)
- Embeds to Qdrant (semantic search)
- Publishes to Cognitive Bus (event distribution)

**When to Use**: All significant service events (archiving, data refresh, etc.)

---

## 3. Implementation Guide

### 3.1 Step-by-Step: Creating a Listener

**Goal**: Implement a listener that consumes events from Cognitive Bus and performs actions.

**Example**: Vault Keepers listener that archives data when codex discovers new tickers.

#### Step 1: Create Directory Structure

```bash
docker/services/api_vault_keepers/
├── main.py                     # FastAPI service (existing)
├── streams_listener.py         # NEW: Listener implementation
└── requirements.txt            # Add redis dependency
```

#### Step 2: Implement Listener Class

**File**: `docker/services/api_vault_keepers/streams_listener.py`

```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from core.cognitive_bus.streams import StreamBus
from core.cognitive_bus.event_envelope import CognitiveEvent
from core.leo.postgres_agent import PostgresAgent
import structlog
import signal

logger = structlog.get_logger()

class VaultKeepersListener:
    def __init__(self):
        self.bus = StreamBus(
            redis_url=os.getenv("REDIS_URL", "redis://vitruvyan_redis_master:6379")
        )
        self.pg = PostgresAgent()
        self.running = True
        
        # Graceful shutdown
        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)
    
    def _shutdown(self, signum, frame):
        logger.info("Shutting down listener")
        self.running = False
    
    def start(self):
        """Main listener loop"""
        logger.info("Vault Keepers listener starting")
        
        # Subscribe to channels
        channels = [
            "codex.discovery.mapped",      # New tickers discovered
            "neural_engine.screen.completed",  # Screening completed
        ]
        
        for event in self.bus.consume(
            streams=channels,
            consumer_group="vault_keepers",
            consumer_name="vault_1"
        ):
            if not self.running:
                break
            
            try:
                self._handle_event(event)
                # CRITICAL: Acknowledge after processing
                self.bus.acknowledge(
                    event.stream, 
                    "vault_keepers", 
                    event.event_id
                )
            except Exception as e:
                logger.error("Error handling event", error=str(e), event=event)
    
    def _handle_event(self, event: CognitiveEvent):
        """Route event to handler based on type"""
        if "codex.discovery" in event.stream:
            self._handle_discovery(event)
        elif "neural_engine.screen" in event.stream:
            self._handle_screening(event)
    
    def _handle_discovery(self, event: CognitiveEvent):
        """Archive newly discovered ticker data"""
        ticker = event.data.get("ticker")
        sector = event.data.get("sector")
        
        logger.info("Archiving ticker", ticker=ticker, sector=sector)
        
        # Save to PostgreSQL
        with self.pg.connection.cursor() as cur:
            cur.execute(
                "INSERT INTO ticker_archive (ticker, sector, archived_at) VALUES (%s, %s, NOW())",
                (ticker, sector)
            )
        self.pg.connection.commit()
    
    def _handle_screening(self, event: CognitiveEvent):
        """Archive screening results"""
        tickers = event.data.get("tickers", [])
        logger.info("Archiving screening results", ticker_count=len(tickers))
        # Implementation...

if __name__ == "__main__":
    listener = VaultKeepersListener()
    listener.start()
```

#### Step 3: Add to Dockerfile

**File**: `docker/services/api_vault_keepers/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy entire codebase (need core/ modules)
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r docker/services/api_vault_keepers/requirements.txt

# Run listener (separate process from FastAPI)
CMD ["python3", "docker/services/api_vault_keepers/streams_listener.py"]
```

#### Step 4: Add to docker-compose.yml

```yaml
services:
  vitruvyan_vault_keepers_listener:
    build:
      context: .
      dockerfile: docker/services/api_vault_keepers/Dockerfile
    container_name: vitruvyan_vault_keepers_listener
    environment:
      - REDIS_URL=redis://vitruvyan_redis_master:6379
      - POSTGRES_HOST=${POSTGRES_HOST}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    depends_on:
      - vitruvyan_redis_master
    networks:
      - vitruvyan_sacred_network
    restart: unless-stopped
```

#### Step 5: Test

```bash
# Build and start
docker compose up -d --build vitruvyan_vault_keepers_listener

# Check logs
docker logs vitruvyan_vault_keepers_listener

# Expected output:
# Vault Keepers listener starting
# Subscribed to: codex.discovery.mapped, neural_engine.screen.completed

# Emit test event
docker exec vitruvyan_redis_master redis-cli XADD stream:vitruvyan:codex.discovery.mapped '*' ticker AAPL sector Technology

# Check listener processed it
docker logs vitruvyan_vault_keepers_listener | grep "Archiving ticker"
```

### 3.2 Consumer Autonomy Pattern

**CRITICAL**: Consumers create infrastructure when needed (mkstream=True).

```python
# StreamBus.create_consumer_group() implementation
def create_consumer_group(self, stream: str, group: str):
    """
    Create consumer group with autonomous initialization.
    
    ARCHITECTURAL DECISION (Feb 5, 2026):
    - mkstream=True: Consumer creates stream if missing (octopus autonomy)
    - Fallback: mkstream=False on read-only replicas
    """
    full_stream = self._namespace(stream)
    
    try:
        # ✅ Autonomous consumer: create stream if missing
        self.client.xgroup_create(full_stream, group, id='0', mkstream=True)
        logger.info("Consumer group created", stream=full_stream, group=group)
    except ResponseError as e:
        if "BUSYGROUP" in str(e):
            # Group already exists, OK
            pass
        elif "READONLY" in str(e):
            # Read-only replica, try without mkstream
            self.client.xgroup_create(full_stream, group, id='0', mkstream=False)
        else:
            raise
```

**Why This Works**:
- Consumers don't wait for publishers (autonomous initialization)
- Stream created empty if missing (no data loss)
- Respects Sacred Invariants (creating empty stream ≠ inspecting payload)

### 3.3 Channel Naming Convention

**Format**: `<service>.<domain>.<action>`

**Examples**:
- `codex.discovery.mapped` - Codex discovered/mapped ticker
- `neural_engine.screen.completed` - Neural Engine completed screening
- `vault_keepers.archive.created` - Vault created archive
- `babel_gardens.sentiment.analyzed` - Babel analyzed sentiment

**Rules**:
- Use dot notation (not underscores)
- Lowercase only
- Past tense for completed actions
- Present tense for ongoing states

### 3.4 Event Payload Structure

**Standard Fields** (all events should include):

```python
{
    "event_id": "abc123",           # Unique event ID
    "event_type": "ticker_mapped",  # Action type
    "causation_id": "xyz789",       # Parent event ID (optional, for causal chains)
    "timestamp": "2026-02-05T10:30:00Z",
    "data": {                       # Domain-specific data
        "ticker": "AAPL",
        "sector": "Technology",
        "composite_score": 1.85
    },
    "metadata": {                   # Optional metadata
        "user_id": "test_user",
        "request_id": "req_123"
    }
}
```

**Anti-Pattern** (avoid unstructured payloads):

```python
# ❌ WRONG: Flat structure, hard to extend
{"ticker": "AAPL", "score": 1.85, "user": "test"}

# ✅ CORRECT: Nested structure, clear hierarchy
{
    "event_type": "screening_completed",
    "data": {"ticker": "AAPL", "score": 1.85},
    "metadata": {"user_id": "test"}
}
```

---

## 4. Common Patterns & Recipes

### 4.1 Pattern: Request-Response

**Problem**: Service A needs result from Service B.

**Solution**: Correlation via `causation_id` field.

```python
# Service A: Publish request
request_id = str(uuid.uuid4())
bus.publish("neural_engine.screen.request", {
    "event_id": request_id,
    "data": {"tickers": ["AAPL", "NVDA"]}
})

# Service B: Process and respond
for event in bus.consume("neural_engine.screen.request", ...):
    result = process_screening(event.data["tickers"])
    bus.publish("neural_engine.screen.completed", {
        "event_id": str(uuid.uuid4()),
        "causation_id": event.event_id,  # Link back to request
        "data": {"tickers": result}
    })

# Service A: Correlate response
for event in bus.consume("neural_engine.screen.completed", ...):
    if event.causation_id == request_id:
        print("Got my response!")
```

### 4.2 Pattern: Scatter-Gather

**Problem**: Broadcast event to multiple consumers, wait for all responses.

```python
# Publisher: Broadcast
request_id = str(uuid.uuid4())
bus.publish("synaptic.conclave.broadcast", {
    "event_id": request_id,
    "data": {"action": "health_check"}
})

# Multiple consumers respond
responses = []
timeout = time.time() + 5  # 5 second timeout

for event in bus.consume("synaptic.conclave.responses", ...):
    if event.causation_id == request_id:
        responses.append(event)
    if time.time() > timeout:
        break

print(f"Received {len(responses)} responses")
```

### 4.3 Pattern: Saga (Multi-Step Transaction)

**Problem**: Multi-step process with compensating actions if failure.

```python
# Step 1: Allocate resources
bus.publish("portfolio.allocation.started", {
    "event_id": saga_id,
    "data": {"user_id": "test", "amount": 10000}
})

# Step 2: Call Neural Engine
bus.publish("neural_engine.screen.request", {
    "event_id": str(uuid.uuid4()),
    "causation_id": saga_id,
    "data": {"profile": "momentum_focus"}
})

# Step 3a: Success path
bus.publish("portfolio.allocation.completed", {
    "causation_id": saga_id,
    "data": {"trades": [...]}
})

# Step 3b: Failure path (compensate)
bus.publish("portfolio.allocation.failed", {
    "causation_id": saga_id,
    "data": {"error": "Insufficient liquidity"}
})
```

### 4.4 Pattern: Dead Letter Queue

**Problem**: Events that fail processing repeatedly.

```python
MAX_RETRIES = 3

def handle_with_retry(event):
    retry_count = event.metadata.get("retry_count", 0)
    
    try:
        process(event)
    except Exception as e:
        if retry_count < MAX_RETRIES:
            # Retry with backoff
            bus.publish(event.stream, {
                **event.data,
                "metadata": {"retry_count": retry_count + 1}
            })
        else:
            # Send to dead letter queue
            bus.publish("dead_letter.queue", {
                "event_id": event.event_id,
                "original_stream": event.stream,
                "error": str(e),
                "data": event.data
            })
```

### 4.5 Recipe: Health Check Listener

**Use Case**: Service monitors own health, publishes to Cognitive Bus.

```python
import time
import psutil

class HealthMonitor:
    def __init__(self, service_name: str):
        self.service = service_name
        self.bus = StreamBus()
    
    def start(self):
        while True:
            health = {
                "service": self.service,
                "cpu_percent": psutil.cpu_percent(),
                "memory_mb": psutil.virtual_memory().used / 1024 / 1024,
                "timestamp": time.time()
            }
            
            self.bus.publish("synaptic.conclave.health", health)
            time.sleep(30)  # Every 30 seconds

if __name__ == "__main__":
    monitor = HealthMonitor("vault_keepers")
    monitor.start()
```

---

## 5. Troubleshooting

### 5.1 XGROUP "key to exist" Error

**Error**:
```
redis.exceptions.ResponseError: XGROUP subcommand requires the key to exist. 
Note that for CREATE you may want to use the MKSTREAM option
```

**Cause**: Consumer tried to create group on non-existent stream with `mkstream=False`.

**Solution**: Ensure `StreamBus.create_consumer_group()` uses `mkstream=True`.

```python
# ✅ CORRECT (Feb 5, 2026 fix)
self.client.xgroup_create(stream, group, mkstream=True)

# ❌ WRONG (pre-Feb 5, 2026)
self.client.xgroup_create(stream, group, mkstream=False)
```

**Verification**:
```bash
# Check if stream exists
docker exec vitruvyan_redis_master redis-cli KEYS "stream:*"

# Check if consumer group created
docker exec vitruvyan_redis_master redis-cli XINFO GROUPS stream:vitruvyan:codex.discovery.mapped
```

### 5.2 ReadOnlyError

**Error**:
```
redis.exceptions.ReadOnlyError: You can't write against a read only replica
```

**Cause**: Consumer connected to read-only replica, tried to create stream with `mkstream=True`.

**Solution**: Fallback to `mkstream=False` on replicas.

```python
try:
    self.client.xgroup_create(stream, group, mkstream=True)
except ResponseError as e:
    if "READONLY" in str(e):
        # Replica can't create streams, assume publisher already did
        self.client.xgroup_create(stream, group, mkstream=False)
    else:
        raise
```

**Prevention**: Connect to master for writes, replicas for reads only.

```python
# ✅ CORRECT: Master for consumer group creation
StreamBus(redis_url="redis://vitruvyan_redis_master:6379")

# ❌ WRONG: Replica for consumer group creation
StreamBus(redis_url="redis://vitruvyan_redis_replica_1:6379")
```

### 5.3 Events Not Being Consumed

**Symptom**: Publisher emits events, no errors, but consumer never receives them.

**Diagnosis**:

```bash
# 1. Check if stream exists
docker exec vitruvyan_redis_master redis-cli KEYS "stream:*"

# 2. Check stream has events
docker exec vitruvyan_redis_master redis-cli XLEN stream:vitruvyan:codex.discovery.mapped

# 3. Check consumer group exists
docker exec vitruvyan_redis_master redis-cli XINFO GROUPS stream:vitruvyan:codex.discovery.mapped

# 4. Check pending events
docker exec vitruvyan_redis_master redis-cli XPENDING stream:vitruvyan:codex.discovery.mapped vault_keepers
```

**Common Causes**:

1. **Namespace mismatch**:
```python
# Publisher: stream:vitruvyan:codex.discovery.mapped
bus.publish("codex.discovery.mapped", {...})

# Consumer: stream:vitruvyan:codex_discovery_mapped (wrong!)
bus.consume("codex_discovery_mapped", ...)

# ✅ FIX: Use exact same channel name
```

2. **Consumer group not created**:
```python
# ✅ FIX: Create consumer group before consuming
bus.create_consumer_group("codex.discovery.mapped", "vault_keepers")
bus.consume("codex.discovery.mapped", "vault_keepers", "vault_1")
```

3. **Events already processed**:
```bash
# Check consumer group offset
docker exec vitruvyan_redis_master redis-cli XINFO GROUPS stream:vitruvyan:codex.discovery.mapped

# If last-delivered-id is recent, consumer is caught up
# Emit new test event to verify
docker exec vitruvyan_redis_master redis-cli XADD stream:vitruvyan:codex.discovery.mapped '*' ticker TEST
```

### 5.4 Container Crash Loop

**Symptom**: Listener container starts, crashes after 1-3 seconds, restarts infinitely.

**Logs**:
```bash
docker logs vitruvyan_vault_keepers_listener

# Look for:
# - Import errors (missing module)
# - Connection errors (Redis unavailable)
# - XGROUP errors (stream creation issues)
```

**Common Fixes**:

1. **Missing dependency**:
```bash
# Check requirements.txt includes redis
cat docker/services/api_vault_keepers/requirements.txt | grep redis

# Should see: redis==5.0.1
```

2. **Redis not ready**:
```yaml
# Add depends_on in docker-compose.yml
depends_on:
  vitruvyan_redis_master:
    condition: service_healthy
```

3. **Path import issues**:
```python
# Ensure sys.path setup at top of listener
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
```

### 5.5 Memory Leak in Consumer

**Symptom**: Consumer memory grows over time, eventually crashes with OOM.

**Cause**: Events acknowledged but never removed from local queue.

**Solution**: Use generator pattern with acknowledgment inside loop.

```python
# ❌ WRONG: Load all events into memory
events = list(bus.consume("codex.discovery.mapped", ...))
for event in events:
    process(event)

# ✅ CORRECT: Generator pattern
for event in bus.consume("codex.discovery.mapped", ...):
    process(event)
    bus.acknowledge(event.stream, "vault_keepers", event.event_id)
```

### 5.6 Debugging Checklist

When implementing a new listener, verify:

- [ ] Stream name uses dot notation (not underscores)
- [ ] Consumer group created with `mkstream=True`
- [ ] Listener connected to master (not replica)
- [ ] Events acknowledged after processing
- [ ] Graceful shutdown handler (SIGTERM, SIGINT)
- [ ] Dependencies in requirements.txt (redis, structlog)
- [ ] Error logging with structlog
- [ ] Dockerfile copies entire codebase (need core/)
- [ ] docker-compose.yml includes environment variables
- [ ] Test event can be consumed end-to-end

---

## Appendix A: Migration History

**Key Milestones**:

- **Jan 24, 2026**: Pub/Sub → Streams migration (Phase 0 Bus Hardening)
- **Jan 26, 2026**: ReadOnlyError fix (mkstream=False decision)
- **Feb 5, 2026**: Consumer autonomy fix (mkstream=True decision)

**Why Migrations Happened**:
- Pub/Sub: No durability, no replay, no load balancing
- Streams: All 3 problems solved + ordered delivery
- mkstream=False: Assumed publisher creates streams (didn't work - silent publishers)
- mkstream=True: Autonomous consumers (octopus model)

**For detailed history**: See `core/cognitive_bus/docs/history/PHASE_*.md`

---

## Appendix B: Performance Characteristics

**Redis Streams**:
- Throughput: ~50K events/second (single thread)
- Latency: <1ms (local), <10ms (network)
- Storage: ~1KB per event (depends on payload)
- Retention: Infinite (trim manually if needed)

**Consumer Group Performance**:
- Load balancing: Round-robin across consumers
- Failure handling: Pending list + XCLAIM after timeout
- Acknowledgment: O(1) operation

**Scaling**:
- Vertical: More CPU/RAM to Redis master
- Horizontal: More consumers in group (N consumers = N× throughput)
- Sharding: Multiple Redis masters with consistent hashing (future)

---

## Appendix C: Quick Reference

### StreamBus API

```python
from core.cognitive_bus.streams import StreamBus

bus = StreamBus(redis_url="redis://localhost:6379")

# Publish
bus.publish(stream="codex.discovery.mapped", event={"ticker": "AAPL"})

# Consume (blocking generator)
for event in bus.consume(
    stream="codex.discovery.mapped",
    consumer_group="vault_keepers",
    consumer_name="vault_1",
    block_ms=5000,
    count=10
):
    process(event)
    bus.acknowledge(event.stream, "vault_keepers", event.event_id)

# Create consumer group
bus.create_consumer_group("codex.discovery.mapped", "vault_keepers")

# Batch operations
events = bus.batch_publish([
    ("stream1", {"data": "a"}),
    ("stream2", {"data": "b"}),
])
```

### Redis CLI Commands

```bash
# List all streams
redis-cli KEYS "stream:*"

# Stream info
redis-cli XINFO STREAM stream:vitruvyan:codex.discovery.mapped

# Consumer groups
redis-cli XINFO GROUPS stream:vitruvyan:codex.discovery.mapped

# Consumers in group
redis-cli XINFO CONSUMERS stream:vitruvyan:codex.discovery.mapped vault_keepers

# Read events
redis-cli XRANGE stream:vitruvyan:codex.discovery.mapped - + COUNT 10

# Pending events
redis-cli XPENDING stream:vitruvyan:codex.discovery.mapped vault_keepers

# Add test event
redis-cli XADD stream:vitruvyan:codex.discovery.mapped '*' ticker AAPL sector Technology
```

---

## Questions?

**If this guide doesn't answer your question**:

1. Check `API_REFERENCE.md` for detailed method signatures
2. Check `ARCHITECTURAL_DECISIONS.md` for historical context
3. Check `core/cognitive_bus/docs/history/` for phase reports
4. Ask on #cognitive-bus Slack channel

**Contributing**: If you find a gap in this guide, please submit a PR to add it.

---

**End of Guide** | Version 2.0 | February 5, 2026
