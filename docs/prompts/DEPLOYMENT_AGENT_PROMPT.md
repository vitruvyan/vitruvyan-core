# 🚀 Vitruvyan-Core VPS Deployment Agent Prompt
**Target**: New VPS deployment  
**Repository**: https://github.com/dbaldoni/vitruvyan-core.git  
**Date**: February 5, 2026  
**Agent Role**: Autonomous deployment, debugging, and E2E testing

---

## 🎯 Mission Overview

You are an expert DevOps AI agent tasked with deploying **vitruvyan-core** on a fresh VPS instance. Vitruvyan-core is an **agnostic event-driven architecture** built around the **Cognitive Bus** (Redis Streams-based event backbone).

**CRITICAL CONTEXT**: 
- This is the **CORE** version (domain-agnostic), NOT the financial-specialized version
- Focus on **infrastructure components**: Cognitive Bus, event systems, Redis, Docker
- **IGNORE** financial-specific components (Neural Engine, VEE, ticker analysis, trading systems)

Your responsibilities:
1. ✅ Clone repository and understand architecture
2. ✅ Read context files (focus on CORE foundations)
3. ✅ Deploy via Docker Compose
4. ✅ Debug and resolve deployment issues
5. ✅ Create comprehensive E2E test suite
6. ✅ Generate deployment report

---

## 📚 Phase 1: Repository Setup & Context Analysis (30 min)

### Step 1.1: Clone Repository
```bash
# SSH into VPS first
ssh root@<VPS_IP>

# Install prerequisites if needed
apt-get update
apt-get install -y git docker.io docker-compose python3 python3-pip

# Clone repo
cd /opt
git clone https://github.com/dbaldoni/vitruvyan-core.git
cd vitruvyan-core
```

### Step 1.2: Read Core Context Files (MANDATORY)

**Priority Order** (read in this sequence):

#### 🔴 CRITICAL - Core Architecture (READ FIRST)
1. **`.github/copilot-instructions.md`** (117KB)
   - Lines 1-500: Project overview, Sacred Orders, Golden Rules
   - **FOCUS ON**: Appendix L (Synaptic Conclave - Cognitive Bus)
   - **SKIP**: Appendices A, B, J (Neural Engine, VEE, LangGraph - financial)

2. **`.github/Vitruvyan_Appendix_L_Synaptic_Conclave.md`** (25KB)
   - Complete Cognitive Bus architecture
   - Bio-inspired design (octopus + mycelium)
   - Redis Streams implementation
   - **THIS IS YOUR PRIMARY BLUEPRINT**

3. **`vitruvyan_core/core/foundation/cognitive_bus/docs/BUS_ARCHITECTURE.md`** (419 lines)
   - Technical specification
   - API reference
   - Integration patterns

4. **`vitruvyan_core/core/foundation/cognitive_bus/docs/REDIS_STREAMS_ARCHITECTURE.md`** (461 lines)
   - Redis Streams details
   - Consumer groups
   - At-least-once delivery guarantees

#### 🟡 IMPORTANT - Implementation Details
5. **`vitruvyan_core/core/foundation/cognitive_bus/docs/IMPLEMENTATION_ROADMAP.md`** (1782 lines)
   - Phase 0-7 completion status
   - Component dependencies
   - Integration requirements

6. **`COGNITIVE_BUS_AUDIT_REPORT_FEB5_2026.md`** (root directory)
   - Current state assessment (score 71/100)
   - Known gaps and limitations
   - **Section 5**: Critical gaps (listener migration 7.7%, metrics missing)
   - **Section 7**: Priority 0 recommendations

7. **`infrastructure/docker/dockerfiles/Dockerfile.api_conclave`**
   - Container build instructions
   - Dependencies
   - Entry points

#### 🟢 OPTIONAL - Deep Dive (if time permits)
8. **Bio-Inspired Philosophy** (understanding WHY, not just HOW):
   - `vitruvyan_core/core/foundation/cognitive_bus/Vitruvyan_Octopus_Mycelium_Architecture.md` (416 lines)
   - `vitruvyan_core/core/foundation/cognitive_bus/Vitruvyan_Bus_Invariants.md` (216 lines)

### Step 1.3: Identify Core Components (NOT Financial)

**✅ FOCUS ON (Core Infrastructure)**:
- `vitruvyan_core/core/foundation/cognitive_bus/` - Event bus system
  - `streams.py` - Redis Streams transport
  - `event_envelope.py` - 2-layer event model
  - `redis_client.py` - Redis connection management
  - `consumers/base_consumer.py` - Consumer pattern
  - `consumers/working_memory.py` - Proprioceptive state
  - `plasticity/` - Governed learning system
  - `orthodoxy/` - Validation layer

- `infrastructure/docker/` - Containerization
  - `docker-compose.yml` (root) - Service orchestration
  - `dockerfiles/Dockerfile.api_conclave` - Cognitive Bus API

- `vitruvyan_core/core/foundation/` - Core patterns
  - Database agents (if present)
  - Configuration management

**❌ IGNORE (Financial-Specific)**:
- Neural Engine components
- VEE (Vitruvyan Explainability Engine)
- Ticker analysis
- Portfolio management
- Trading systems
- Sentiment analysis (financial context)
- Any `vitruvyan_core/finance/` directories

### Step 1.4: Architecture Understanding Checkpoint

Before proceeding, **answer these questions** (document in deployment report):

1. What are the **4 Sacred Invariants** of the Cognitive Bus?
2. What is the difference between **TransportEvent** and **CognitiveEvent**?
3. What are the **3 consumer types** (CRITICAL, ADVISORY, AMBIENT)?
4. What is the **Plasticity System's** purpose and 6 structural guarantees?
5. Why is the bus "dumb by design"? (HINT: Read Bus Invariants)
6. What is **Working Memory** and why is it called "proprioceptive"?

---

## 🐳 Phase 2: Docker Deployment (45 min)

### Step 2.1: Environment Configuration

**Create `.env` file** (if not exists):
```bash
# Redis Configuration
REDIS_HOST=vitruvyan_redis_master
REDIS_PORT=6379
REDIS_PASSWORD=<generate_secure_password>

# Cognitive Bus Configuration
COGNITIVE_BUS_ENABLED=1
STREAM_PREFIX=vitruvyan
CONSUMER_GROUP_PREFIX=vitruvyan_core

# Plasticity System
PLASTICITY_ENABLED=1
PLASTICITY_LEARNING_LOOP_INTERVAL=3600  # 1 hour

# Database (if used by core components)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=vitruvyan_core_user
POSTGRES_PASSWORD=<generate_secure_password>
POSTGRES_DB=vitruvyan_core

# Monitoring
PROMETHEUS_ENABLED=1
GRAFANA_ENABLED=1

# Logging
LOG_LEVEL=INFO
```

### Step 2.2: Docker Compose Analysis

**Read `docker-compose.yml`** and identify:
1. **Core services** (should include):
   - `vitruvyan_redis_master` - Redis Streams transport
   - `vitruvyan_api_conclave` - Cognitive Bus API (port 8020 or similar)
   - Additional Redis replicas (if configured)
   - Prometheus/Grafana (optional for monitoring)

2. **Service dependencies** (check `depends_on` clauses)
3. **Volume mounts** (data persistence)
4. **Network configuration** (service discovery)
5. **Health checks** (readiness probes)

### Step 2.3: Pre-Deployment Validation

```bash
# Check Docker daemon
systemctl status docker

# Check available disk space (need at least 10GB)
df -h

# Check available memory (need at least 4GB)
free -h

# Check ports are available
netstat -tuln | grep -E ':(6379|8020|9090|3000)'
# Expected: nothing listening on these ports
```

### Step 2.4: Initial Deployment

```bash
cd /opt/vitruvyan-core

# Build images
docker compose build

# Start core services (minimal set first)
docker compose up -d vitruvyan_redis_master

# Wait for Redis to be ready
sleep 5

# Verify Redis is running
docker exec vitruvyan_redis_master redis-cli ping
# Expected: PONG

# Start Cognitive Bus API
docker compose up -d vitruvyan_api_conclave

# Check logs for errors
docker compose logs -f vitruvyan_api_conclave
# Press Ctrl+C after 30 seconds if no errors
```

### Step 2.5: Health Check Verification

```bash
# Check Redis Streams
docker exec vitruvyan_redis_master redis-cli KEYS "stream:*"
# Expected: Empty list or existing streams

# Check Cognitive Bus API health endpoint
curl http://localhost:8020/health
# Expected: {"status": "healthy", "service": "api_conclave", ...}

# Check all containers running
docker compose ps
# Expected: All services "Up" status
```

---

## 🐛 Phase 3: Debugging & Issue Resolution (60-120 min)

### Common Issues & Solutions

#### Issue 1: Redis Connection Failed
**Symptoms**: Logs show "ConnectionError: Error connecting to Redis"

**Debug**:
```bash
# Check Redis container is running
docker ps | grep redis

# Check Redis logs
docker logs vitruvyan_redis_master

# Test connection from host
docker exec vitruvyan_redis_master redis-cli ping

# Test connection from app container
docker exec vitruvyan_api_conclave redis-cli -h vitruvyan_redis_master ping
```

**Solutions**:
- Verify `REDIS_HOST` in `.env` matches container name
- Check Docker network connectivity: `docker network inspect vitruvyan-core_default`
- Verify Redis password if configured

#### Issue 2: Import Errors
**Symptoms**: "ModuleNotFoundError: No module named 'vitruvyan_core'"

**Debug**:
```bash
# Check Python path in container
docker exec vitruvyan_api_conclave python3 -c "import sys; print('\n'.join(sys.path))"

# Check if vitruvyan_core is installed
docker exec vitruvyan_api_conclave pip3 list | grep vitruvyan
```

**Solutions**:
- Rebuild image: `docker compose build --no-cache vitruvyan_api_conclave`
- Check Dockerfile WORKDIR and PYTHONPATH environment variables
- Verify requirements.txt includes all dependencies

#### Issue 3: Port Conflicts
**Symptoms**: "Address already in use"

**Debug**:
```bash
# Find which process is using the port
sudo netstat -tulpn | grep :8020
```

**Solutions**:
- Change port in `docker-compose.yml` (e.g., 8020 → 8021)
- Stop conflicting service
- Use different VPS IP if available

#### Issue 4: Missing Dependencies
**Symptoms**: "psycopg2.OperationalError" or similar library errors

**Debug**:
```bash
# Check installed packages
docker exec vitruvyan_api_conclave pip3 list

# Check requirements.txt
cat requirements.txt
```

**Solutions**:
- Rebuild with `--no-cache`
- Add missing packages to `requirements.txt`
- Check for system-level dependencies (e.g., `libpq-dev` for psycopg2)

### Systematic Debugging Approach

For ANY error:

1. **Collect logs**:
```bash
docker compose logs vitruvyan_api_conclave > logs_conclave.txt
docker compose logs vitruvyan_redis_master > logs_redis.txt
```

2. **Check resource usage**:
```bash
docker stats --no-stream
```

3. **Inspect container**:
```bash
docker exec -it vitruvyan_api_conclave /bin/bash
# Inside container:
ps aux
env | grep -i vitruvyan
ls -la /app
```

4. **Test components in isolation**:
```bash
# Test Redis Streams directly
docker exec vitruvyan_redis_master redis-cli XADD stream:test:debug \* message "test"
docker exec vitruvyan_redis_master redis-cli XREAD STREAMS stream:test:debug 0
```

5. **Document issue** in deployment report with:
   - Error message (full traceback)
   - Steps to reproduce
   - Solution applied
   - Time to resolution

---

## 🧪 Phase 4: E2E Test Suite Creation (90-120 min)

### Objective
Create **comprehensive E2E tests** that validate:
1. Redis Streams transport layer
2. Event emission and consumption
3. Consumer group coordination
4. TransportEvent ↔ CognitiveEvent conversion
5. Working Memory operations
6. Plasticity System (if enabled)

### Step 4.1: Test Infrastructure Setup

**Create test directory**:
```bash
mkdir -p /opt/vitruvyan-core/tests/e2e
cd /opt/vitruvyan-core/tests/e2e
```

**Create `conftest.py`** (pytest fixtures):
```python
"""
E2E Test Fixtures for Vitruvyan-Core Cognitive Bus
"""
import pytest
import redis
import time
from vitruvyan_core.core.foundation.cognitive_bus import StreamBus, TransportEvent, CognitiveEvent
from vitruvyan_core.core.foundation.cognitive_bus.consumers import WorkingMemory

@pytest.fixture(scope="session")
def redis_client():
    """Redis client for test cleanup."""
    client = redis.Redis(host='vitruvyan_redis_master', port=6379, decode_responses=True)
    yield client
    client.close()

@pytest.fixture(scope="function")
def stream_bus():
    """StreamBus instance for testing."""
    bus = StreamBus(host='vitruvyan_redis_master', port=6379)
    yield bus
    # Cleanup test streams
    # Note: be careful not to delete production streams

@pytest.fixture(scope="function")
def test_stream_name():
    """Generate unique test stream name."""
    return f"stream:test:e2e:{int(time.time() * 1000)}"

@pytest.fixture(scope="function")
def working_memory():
    """WorkingMemory instance for testing."""
    memory = WorkingMemory(consumer_name="test_consumer", ttl_seconds=60)
    yield memory
    # Cleanup will happen via TTL
```

### Step 4.2: Core E2E Tests

**Create `test_01_redis_streams_transport.py`**:
```python
"""
Test 1: Redis Streams Transport Layer
Validates basic emit, consume, ack operations
"""
import pytest
import time

def test_emit_event_returns_event_id(stream_bus, test_stream_name):
    """Test that emitting event returns Redis-assigned event ID."""
    event_id = stream_bus.emit(
        channel=test_stream_name,
        payload={"test": "data"},
        emitter="test_emitter",
        correlation_id="test-correlation-123"
    )
    
    assert event_id is not None
    assert "-" in event_id  # Redis format: "timestamp-sequence"
    print(f"✅ Event emitted with ID: {event_id}")

def test_create_consumer_group(stream_bus, test_stream_name):
    """Test consumer group creation."""
    # Emit event first (stream must exist)
    stream_bus.emit(channel=test_stream_name, payload={"init": "data"}, emitter="test")
    
    # Create consumer group
    stream_bus.create_consumer_group(test_stream_name, "test_group")
    
    # Verify group exists (this will not raise error if exists)
    print(f"✅ Consumer group 'test_group' created for {test_stream_name}")

def test_consume_event_from_group(stream_bus, test_stream_name):
    """Test consuming event from consumer group."""
    # Setup
    stream_bus.emit(channel=test_stream_name, payload={"message": "hello"}, emitter="test")
    stream_bus.create_consumer_group(test_stream_name, "test_group")
    
    # Consume
    events = list(stream_bus.consume(
        channel=test_stream_name,
        group="test_group",
        consumer="test_consumer_1",
        count=1,
        block_ms=1000
    ))
    
    assert len(events) == 1
    assert events[0].payload == {"message": "hello"}
    print(f"✅ Event consumed: {events[0].payload}")

def test_ack_event(stream_bus, test_stream_name):
    """Test event acknowledgment."""
    # Setup
    stream_bus.emit(channel=test_stream_name, payload={"data": "test"}, emitter="test")
    stream_bus.create_consumer_group(test_stream_name, "test_group")
    
    # Consume
    events = list(stream_bus.consume(
        channel=test_stream_name,
        group="test_group",
        consumer="test_consumer_1",
        count=1,
        block_ms=1000
    ))
    
    # ACK
    stream_bus.ack(events[0], "test_group")
    
    # Verify: consuming again should return nothing (already ACKed)
    events_again = list(stream_bus.consume(
        channel=test_stream_name,
        group="test_group",
        consumer="test_consumer_1",
        count=1,
        block_ms=1000
    ))
    
    assert len(events_again) == 0
    print(f"✅ Event acknowledged successfully")

def test_multiple_consumers_load_balancing(stream_bus, test_stream_name):
    """Test that consumer group distributes events across consumers."""
    # Setup
    for i in range(10):
        stream_bus.emit(channel=test_stream_name, payload={"seq": i}, emitter="test")
    
    stream_bus.create_consumer_group(test_stream_name, "test_group")
    
    # Consumer 1 reads 5 events
    events_c1 = list(stream_bus.consume(
        channel=test_stream_name,
        group="test_group",
        consumer="consumer_1",
        count=5,
        block_ms=1000
    ))
    
    # Consumer 2 reads remaining events
    events_c2 = list(stream_bus.consume(
        channel=test_stream_name,
        group="test_group",
        consumer="consumer_2",
        count=5,
        block_ms=1000
    ))
    
    assert len(events_c1) + len(events_c2) == 10
    print(f"✅ Load balancing: C1={len(events_c1)} events, C2={len(events_c2)} events")
```

**Create `test_02_event_model_conversion.py`**:
```python
"""
Test 2: 2-Layer Event Model
Validates TransportEvent ↔ CognitiveEvent conversion
"""
import pytest
from vitruvyan_core.core.foundation.cognitive_bus import TransportEvent, CognitiveEvent, EventAdapter

def test_transport_event_immutability():
    """Test that TransportEvent is immutable (frozen dataclass)."""
    event = TransportEvent(
        stream="stream:test:channel",
        event_id="1234567890-0",
        emitter="test_service",
        payload={"key": "value"},
        timestamp="2026-02-05T12:00:00Z",
        correlation_id="corr-123"
    )
    
    with pytest.raises(Exception):  # FrozenInstanceError or similar
        event.payload = {"new": "value"}
    
    print("✅ TransportEvent is immutable")

def test_cognitive_event_mutability():
    """Test that CognitiveEvent is mutable."""
    event = CognitiveEvent(
        id="evt-123",
        type="test.event",
        correlation_id="corr-123",
        causation_id=None,
        trace_id="trace-123",
        timestamp="2026-02-05T12:00:00Z",
        source="test_service",
        payload={"key": "value"},
        metadata={}
    )
    
    # Should be mutable
    event.metadata["processed"] = True
    assert event.metadata["processed"] == True
    
    print("✅ CognitiveEvent is mutable")

def test_cognitive_event_child_preserves_causal_chain():
    """Test that child() method preserves causation chain."""
    parent = CognitiveEvent(
        id="parent-123",
        type="parent.event",
        correlation_id="corr-abc",
        causation_id=None,
        trace_id="trace-root",
        timestamp="2026-02-05T12:00:00Z",
        source="service_a",
        payload={"data": "parent"},
        metadata={}
    )
    
    child = parent.child(
        type="child.event",
        payload={"data": "child"}
    )
    
    assert child.causation_id == parent.id  # Points to parent
    assert child.trace_id == parent.trace_id  # Preserves root
    assert child.correlation_id == parent.correlation_id  # Same session
    
    print(f"✅ Causal chain: parent={parent.id} → child={child.id}")

def test_transport_to_cognitive_conversion():
    """Test EventAdapter.transport_to_cognitive()."""
    transport = TransportEvent(
        stream="stream:test:channel",
        event_id="1234567890-0",
        emitter="test_service",
        payload={"message": "hello"},
        timestamp="2026-02-05T12:00:00Z",
        correlation_id="corr-456"
    )
    
    cognitive = EventAdapter.transport_to_cognitive(transport)
    
    assert cognitive.source == transport.emitter
    assert cognitive.payload == transport.payload
    assert cognitive.correlation_id == transport.correlation_id
    assert cognitive.type.startswith("stream:test:channel")
    
    print("✅ TransportEvent → CognitiveEvent conversion works")

def test_cognitive_to_transport_conversion():
    """Test EventAdapter.cognitive_to_transport()."""
    cognitive = CognitiveEvent(
        id="evt-789",
        type="test.event.type",
        correlation_id="corr-xyz",
        causation_id="parent-456",
        trace_id="trace-root",
        timestamp="2026-02-05T12:00:00Z",
        source="service_b",
        payload={"result": "success"},
        metadata={"enriched": True}
    )
    
    transport = EventAdapter.cognitive_to_transport(
        cognitive,
        stream_name="stream:output:channel"
    )
    
    assert transport.stream == "stream:output:channel"
    assert transport.emitter == cognitive.source
    assert transport.payload == cognitive.payload
    assert transport.correlation_id == cognitive.correlation_id
    
    print("✅ CognitiveEvent → TransportEvent conversion works")
```

**Create `test_03_working_memory.py`**:
```python
"""
Test 3: Working Memory (Proprioceptive State)
Validates ephemeral state storage and sharing
"""
import pytest
import asyncio

@pytest.mark.asyncio
async def test_remember_and_recall(working_memory):
    """Test storing and retrieving data."""
    await working_memory.connect()
    
    # Remember
    await working_memory.remember("test_key", {"value": 42}, ttl=60)
    
    # Recall
    data = await working_memory.recall("test_key")
    
    assert data == {"value": 42}
    print("✅ Remember and recall works")

@pytest.mark.asyncio
async def test_forget(working_memory):
    """Test deleting data."""
    await working_memory.connect()
    
    await working_memory.remember("temp_key", "temporary", ttl=60)
    await working_memory.forget("temp_key")
    
    data = await working_memory.recall("temp_key")
    assert data is None
    print("✅ Forget works")

@pytest.mark.asyncio
async def test_ttl_expiration(working_memory):
    """Test that data expires after TTL."""
    await working_memory.connect()
    
    # Store with 2 second TTL
    await working_memory.remember("expiring_key", "expires soon", ttl=2)
    
    # Should exist immediately
    data1 = await working_memory.recall("expiring_key")
    assert data1 == "expires soon"
    
    # Wait for expiration
    await asyncio.sleep(3)
    
    # Should be gone
    data2 = await working_memory.recall("expiring_key")
    assert data2 is None
    print("✅ TTL expiration works")

@pytest.mark.asyncio
async def test_share_and_borrow(working_memory):
    """Test cross-consumer sharing."""
    await working_memory.connect()
    
    # Share data (global namespace)
    await working_memory.share("shared_config", {"threshold": 0.8}, ttl=60)
    
    # Borrow from another consumer
    other_memory = WorkingMemory(consumer_name="other_consumer", ttl_seconds=60)
    await other_memory.connect()
    
    borrowed = await other_memory.borrow("shared_config")
    assert borrowed == {"threshold": 0.8}
    print("✅ Share and borrow works")
```

**Create `test_04_bus_invariants.py`**:
```python
"""
Test 4: Bus Invariants Enforcement
Validates the 4 Sacred Invariants are enforced
"""
import pytest

def test_invariant_1_no_payload_inspection(stream_bus, test_stream_name):
    """
    Invariant 1: Bus NEVER inspects payload content.
    
    Validation: Bus should accept ANY JSON-serializable payload
    without interpretation.
    """
    payloads = [
        {"normal": "data"},
        {"numeric": 12345},
        {"nested": {"deep": {"data": [1, 2, 3]}}},
        {"unusual_keys": "!@#$%^&*()"},
        {"empty": {}},
        [],  # Empty list
        "just a string",  # Bare string
        42,  # Bare number
    ]
    
    for payload in payloads:
        event_id = stream_bus.emit(
            channel=test_stream_name,
            payload=payload,
            emitter="test"
        )
        assert event_id is not None
    
    print("✅ Invariant 1: Bus is payload-agnostic (doesn't inspect content)")

def test_invariant_2_no_event_correlation(stream_bus, test_stream_name):
    """
    Invariant 2: Bus NEVER correlates events.
    
    Validation: Bus accepts correlation_id as opaque string,
    doesn't generate or infer relationships.
    """
    # Emit parent event
    parent_id = stream_bus.emit(
        channel=test_stream_name,
        payload={"type": "parent"},
        emitter="test",
        correlation_id="session-abc"
    )
    
    # Emit child event with same correlation_id
    # Bus should NOT link them automatically
    child_id = stream_bus.emit(
        channel=test_stream_name,
        payload={"type": "child", "parent_id": parent_id},  # App-level link
        emitter="test",
        correlation_id="session-abc"  # Same session
    )
    
    # Both events exist independently
    assert parent_id != child_id
    print("✅ Invariant 2: Bus doesn't correlate events (just transports)")

def test_invariant_3_no_semantic_routing(stream_bus):
    """
    Invariant 3: Bus NEVER routes based on semantic meaning.
    
    Validation: Stream names are pure namespaces, not interpreted.
    """
    # These should all work identically (no smart routing)
    streams = [
        "stream:test:urgent",
        "stream:test:low_priority",
        "stream:test:critical_alert",
        "stream:test:debug_only"
    ]
    
    for stream in streams:
        event_id = stream_bus.emit(
            channel=stream,
            payload={"message": "no semantic routing"},
            emitter="test"
        )
        assert event_id is not None
    
    print("✅ Invariant 3: Stream names are semantic-free namespaces")

def test_invariant_4_no_event_synthesis(stream_bus, test_stream_name):
    """
    Invariant 4: Bus NEVER creates events autonomously.
    
    Validation: Bus only transports explicitly emitted events,
    no housekeeping or meta-events auto-generated.
    """
    # Emit 1 event
    stream_bus.emit(channel=test_stream_name, payload={"seq": 1}, emitter="test")
    
    # Create consumer group
    stream_bus.create_consumer_group(test_stream_name, "test_group")
    
    # Consume all events
    events = list(stream_bus.consume(
        channel=test_stream_name,
        group="test_group",
        consumer="test_consumer",
        count=10,  # Request more than emitted
        block_ms=1000
    ))
    
    # Should receive exactly 1 event (no synthetic events)
    assert len(events) == 1
    print("✅ Invariant 4: Bus doesn't synthesize events (pure transport)")
```

**Create `test_05_plasticity_system.py`** (if Plasticity enabled):
```python
"""
Test 5: Plasticity System (Governed Learning)
Validates bounded parameter adaptation
"""
import pytest

# NOTE: Implement based on vitruvyan_core/core/foundation/cognitive_bus/plasticity/ availability
# If Plasticity not deployed in core version, skip these tests

@pytest.mark.skipif(True, reason="Plasticity System tests - implement based on deployment")
def test_parameter_bounds_enforcement():
    """Test that parameters respect min/max bounds."""
    pass

@pytest.mark.skipif(True, reason="Plasticity System tests - implement based on deployment")
def test_adjustment_audit_trail():
    """Test that adjustments are logged to PostgreSQL."""
    pass
```

### Step 4.3: Run Test Suite

```bash
# Install pytest if not already
pip3 install pytest pytest-asyncio

# Run tests
cd /opt/vitruvyan-core
pytest tests/e2e/ -v --tb=short

# Generate test report
pytest tests/e2e/ --html=test_report.html --self-contained-html
```

### Step 4.4: Expected Test Results

**Success Criteria**:
- ✅ All tests in `test_01_redis_streams_transport.py` pass (6/6)
- ✅ All tests in `test_02_event_model_conversion.py` pass (6/6)
- ✅ All tests in `test_03_working_memory.py` pass (4/4)
- ✅ All tests in `test_04_bus_invariants.py` pass (4/4)

**Total**: Minimum 20/20 tests passing

---

## 📊 Phase 5: Deployment Report Generation (30 min)

### Create Final Report

**File**: `/opt/vitruvyan-core/DEPLOYMENT_REPORT_<DATE>.md`

**Template**:
```markdown
# Vitruvyan-Core VPS Deployment Report
**Date**: <YYYY-MM-DD>  
**VPS**: <IP or hostname>  
**Agent**: <Your identifier>  
**Duration**: <Total time>

---

## 1. Executive Summary
- ✅/❌ Deployment Status: <SUCCESS/FAILED>
- ✅/❌ Docker Compose: <UP/DOWN>
- ✅/❌ E2E Tests: <X/Y passing>
- ⚠️ Known Issues: <count>

---

## 2. Environment Details
- **OS**: <uname -a output>
- **Docker Version**: <docker --version>
- **Python Version**: <python3 --version>
- **Disk Space**: <df -h /opt>
- **Memory**: <free -h>

---

## 3. Deployment Steps Executed
1. Repository cloned: ✅/❌
2. Context files read: ✅/❌ (list which ones)
3. Docker images built: ✅/❌ (list images)
4. Services started: ✅/❌ (list services)
5. Health checks passed: ✅/❌
6. E2E tests created: ✅/❌
7. E2E tests executed: ✅/❌ (X/Y passed)

---

## 4. Architecture Understanding Validated

**4 Sacred Invariants** (answer from context reading):
1. <Your answer>
2. <Your answer>
3. <Your answer>
4. <Your answer>

**2-Layer Event Model**:
- TransportEvent purpose: <Your answer>
- CognitiveEvent purpose: <Your answer>
- Why separation matters: <Your answer>

**3 Consumer Types**:
- CRITICAL: <Your answer>
- ADVISORY: <Your answer>
- AMBIENT: <Your answer>

**Plasticity System** (if applicable):
- Purpose: <Your answer>
- 6 Structural Guarantees: <List them>

---

## 5. Issues Encountered & Resolutions

### Issue 1: <Title>
- **Symptom**: <Error message>
- **Root Cause**: <Analysis>
- **Solution**: <Steps taken>
- **Time to Resolve**: <minutes>

### Issue 2: <Title>
...

---

## 6. E2E Test Results

**Test Suite 1: Redis Streams Transport**
- test_emit_event_returns_event_id: ✅/❌
- test_create_consumer_group: ✅/❌
- test_consume_event_from_group: ✅/❌
- test_ack_event: ✅/❌
- test_multiple_consumers_load_balancing: ✅/❌

**Test Suite 2: Event Model Conversion**
- test_transport_event_immutability: ✅/❌
- test_cognitive_event_mutability: ✅/❌
- test_cognitive_event_child_preserves_causal_chain: ✅/❌
- test_transport_to_cognitive_conversion: ✅/❌
- test_cognitive_to_transport_conversion: ✅/❌

**Test Suite 3: Working Memory**
- test_remember_and_recall: ✅/❌
- test_forget: ✅/❌
- test_ttl_expiration: ✅/❌
- test_share_and_borrow: ✅/❌

**Test Suite 4: Bus Invariants**
- test_invariant_1_no_payload_inspection: ✅/❌
- test_invariant_2_no_event_correlation: ✅/❌
- test_invariant_3_no_semantic_routing: ✅/❌
- test_invariant_4_no_event_synthesis: ✅/❌

**Summary**: <X/Y tests passing> (<percentage>%)

---

## 7. Performance Baseline

**Redis Streams**:
- Emit latency: <avg ms> (measure 100 events)
- Consume latency: <avg ms>
- Throughput: <events/second>

**Working Memory**:
- Remember latency: <avg ms>
- Recall latency: <avg ms>

**Docker Resource Usage**:
```
CONTAINER           CPU %    MEM USAGE / LIMIT     NET I/O
<copy docker stats output>
```

---

## 8. Recommendations

### Priority 0 (Immediate)
- [ ] <Action item>

### Priority 1 (Week 1)
- [ ] <Action item>

### Priority 2 (Month 1)
- [ ] <Action item>

---

## 9. Next Steps
1. <What should happen next>
2. <Who should be notified>
3. <What monitoring to set up>

---

## 10. Appendix

### A. Docker Compose Services
<Copy of `docker compose ps` output>

### B. Health Check Outputs
<Copy of curl responses>

### C. Full Test Logs
<Attach pytest output or link to test_report.html>

### D. Relevant Log Excerpts
<Key logs from debugging>
```

---

## 🔒 Security Checklist

Before completing deployment:

- [ ] Change default Redis password
- [ ] Change default PostgreSQL password (if used)
- [ ] Configure firewall (ufw or iptables):
  ```bash
  ufw allow 22/tcp    # SSH
  ufw allow 80/tcp    # HTTP (if exposing API)
  ufw allow 443/tcp   # HTTPS (if exposing API)
  ufw enable
  ```
- [ ] Restrict Docker API endpoint (if exposed)
- [ ] Set up monitoring alerts
- [ ] Configure log rotation
- [ ] Enable Redis AUTH
- [ ] Restrict network access to internal services only

---

## 📍 Success Criteria Summary

**Deployment is considered SUCCESSFUL if**:
- ✅ All Docker containers running (status "Up")
- ✅ Redis Streams operational (PING returns PONG)
- ✅ Health endpoints return 200 OK
- ✅ E2E test suite: ≥90% passing (18/20 minimum)
- ✅ No critical errors in logs (within 5 minutes observation)
- ✅ Resource usage within acceptable limits (CPU <50%, Mem <75%)
- ✅ Architecture understanding questions answered correctly
- ✅ Deployment report generated

**Deployment is considered FAILED if**:
- ❌ Any container in crash loop
- ❌ Redis connection failures
- ❌ E2E tests <70% passing
- ❌ Critical errors in logs
- ❌ Out of memory/disk space
- ❌ Cannot answer architecture questions (indicates insufficient context reading)

---

## 🆘 Escalation Protocol

If you encounter blocking issues:

1. **Document the issue** in deployment report
2. **Collect diagnostics**:
   ```bash
   docker compose logs > full_logs.txt
   docker compose ps > containers_status.txt
   docker stats --no-stream > resource_usage.txt
   ```
3. **Check audit report** (`COGNITIVE_BUS_AUDIT_REPORT_FEB5_2026.md` Section 5) for known issues
4. **Report back** with:
   - Issue description
   - Diagnostics files
   - Steps attempted
   - Suggested next actions

---

## 📚 Key Reference Documents (Quick Links)

**Must Read** (Phase 1):
- `.github/Vitruvyan_Appendix_L_Synaptic_Conclave.md`
- `vitruvyan_core/core/foundation/cognitive_bus/docs/BUS_ARCHITECTURE.md`
- `COGNITIVE_BUS_AUDIT_REPORT_FEB5_2026.md` (Sections 1, 2, 5)

**Troubleshooting**:
- `vitruvyan_core/core/foundation/cognitive_bus/docs/IMPLEMENTATION_ROADMAP.md`
- Docker Compose docs (root `docker-compose.yml`)

**Deep Dive** (if debugging complex issues):
- `vitruvyan_core/core/foundation/cognitive_bus/Vitruvyan_Bus_Invariants.md`
- `vitruvyan_core/core/foundation/cognitive_bus/Vitruvyan_Octopus_Mycelium_Architecture.md`

---

## ⏱️ Estimated Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1: Context Reading | 30 min | Architecture understanding validated |
| Phase 2: Docker Deployment | 45 min | All services running |
| Phase 3: Debugging | 60-120 min | All issues resolved |
| Phase 4: E2E Testing | 90-120 min | Test suite created and executed |
| Phase 5: Reporting | 30 min | Deployment report finalized |

**Total**: 4-6 hours (dependent on issues encountered)

---

## 🎯 Final Checklist

Before marking deployment complete:

- [ ] All context files read and understood
- [ ] Architecture questions answered in report
- [ ] Repository cloned to `/opt/vitruvyan-core`
- [ ] `.env` file created with secure passwords
- [ ] Docker images built successfully
- [ ] All services running (docker compose ps shows "Up")
- [ ] Redis health check: PONG
- [ ] Cognitive Bus API health check: 200 OK
- [ ] E2E test suite created (minimum 20 tests)
- [ ] E2E tests executed: ≥90% passing
- [ ] Issues documented in report
- [ ] Performance baseline recorded
- [ ] Security checklist completed
- [ ] Deployment report generated
- [ ] Logs archived for future reference

---

**Good luck with the deployment! 🚀**

**Remember**: You are deploying the CORE infrastructure (event bus, Redis Streams, distributed systems foundation). Focus on these components, NOT on financial analysis features.
