# Vitruvyan Cognitive Bus Hardening Plan
**Date**: January 24, 2026  
**Objective**: Transform from "conceptual architecture" to "technically demonstrable bus core"

---

## AUDIT FINDINGS (Verified)

### ✅ A. BaseConsumer assumes non-existent async methods
**Evidence**: `base_consumer.py` line 368-378
```python
bus = StreamBus()
await bus.connect()  # ❌ Method does not exist
events = await bus.read(...)  # ❌ Method does not exist
```
**Impact**: `_consume_loop()` is dead code - cannot execute

### ✅ B. Four incompatible event models
**Evidence**:
1. `StreamEvent` in `streams.py` (line 61): `stream`, `event_id`, `emitter`, `payload`, `timestamp`, `correlation_id`
2. `StreamEvent` in `base_consumer.py` (line 114): `id`, `type`, `correlation_id`, `causation_id`, `trace_id`, `source`, `targets`, `payload`, `metadata`
3. `SemanticEvent` in `heart.py` (line 18): `domain`, `intent`, `payload`, `timestamp`, `event_id`
4. `CognitiveEvent` in `redis_client.py` (line 30): `event_type`, `emitter`, `target`, `payload`, `timestamp`, `correlation_id`

**Impact**: No interoperability, no single source of truth

### ✅ C. Pub/Sub actively used in runtime
**Evidence**:
- `heart.py` line 150: `await self.redis_client.publish()`
- `herald.py`: Entire module does semantic routing via Pub/Sub
- `redis_client.py` line 180, 227: `self.redis_client.publish()`
- `orthodoxy_adaptation_listener.py`: Pub/Sub listener

**Impact**: Two parallel transport systems, architectural ambiguity

### ✅ D. No E2E integration tests
**Evidence**: `tests/test_phase5_specialized_consumers.py` uses mock events only
**Impact**: Cannot verify real bus functionality

### ✅ E. Bus invariants violated
**Evidence**: `herald.py` line 73-100
```python
self.routing_rules = {
    "babel.sentiment.requested": {"babel"},  # Semantic routing!
    "memory.write.completed": {"orthodoxy", "compose"}
}
```
**Impact**: Herald inspects event types and routes semantically - violates "humble bus"

---

## EXECUTION PLAN

### PHASE 1: Archive Pub/Sub (30 min)
**Goal**: Remove all Pub/Sub from active runtime

**Actions**:
1. Create `/archive/pub_sub_legacy/` directory
2. Move files:
   - `heart.py` → archive
   - `heart_backup.py` → archive (already backup)
   - `herald.py` → archive
   - `redis_client.py` → archive
   - `scribe.py` → archive (depends on Pub/Sub)
   - `orthodoxy_adaptation_listener.py` → archive
3. Remove imports from all consumers
4. Verify no runtime dependencies remain

**Verification**:
```bash
grep -r "from.*heart import\|import.*herald\|from.*redis_client" core/cognitive_bus/consumers/
# Should return NOTHING
```

### PHASE 2: Canonical Event Envelope (45 min)
**Goal**: ONE event model for entire system

**Decision**: Use `streams.py` StreamEvent as base (it's correct for transport)

**Actions**:
1. Create `core/cognitive_bus/event_envelope.py`:
   - `TransportEvent`: Redis Streams level (immutable, minimal)
   - `CognitiveEvent`: Consumer level (adds causal chain)
   - `EventAdapter`: Bidirectional conversion
2. Update `streams.py` StreamEvent to be `TransportEvent`
3. Replace `base_consumer.py` StreamEvent with `CognitiveEvent`
4. Implement adapters:
   - `transport_to_cognitive()`
   - `cognitive_to_transport()`
5. Remove duplicate event classes

**Verification**:
```bash
# Only ONE event model per layer
grep -c "class.*Event" core/cognitive_bus/event_envelope.py  # Should be 2
grep -c "class.*Event" core/cognitive_bus/streams.py  # Should be 0 (uses envelope)
```

### PHASE 3: StreamBus ↔ BaseConsumer Integration (60 min)
**Goal**: Make BaseConsumer actually runnable

**Decision**: Implement async wrapper for StreamBus (preserve both sync/async patterns)

**Actions**:
1. Add `StreamBus.connect()` async method:
   ```python
   async def connect(self) -> bool:
       """Async connection wrapper"""
       return await asyncio.to_thread(self._connect)
   ```
2. Add `StreamBus.read_async()` method:
   ```python
   async def read_async(self, stream_name, group, consumer, count, block_ms):
       """Async wrapper for consume generator"""
       return await asyncio.to_thread(
           lambda: list(itertools.islice(
               self.consume(stream_name, group, consumer, count, block_ms),
               count
           ))
       )
   ```
3. Update `BaseConsumer._consume_loop()` to use real methods
4. Test with real Redis

**Verification**:
```python
# Unit test
bus = StreamBus()
assert await bus.connect() is True
events = await bus.read_async("test_stream", "test_group", "worker-1", 10, 1000)
```

### PHASE 4: Bus Invariants Enforcement (30 min)
**Goal**: Structurally prevent invariant violations

**Actions**:
1. Add `StreamBus._validate_invariants()`:
   - Check: no payload inspection
   - Check: no semantic routing
   - Check: no event synthesis
2. Add docstring warnings in StreamBus
3. Remove any remaining Herald-like logic
4. Document invariants in code comments

**Verification**:
```python
# StreamBus should NEVER call payload.get() or inspect payload keys
grep -n "payload\.get\|payload\[" core/cognitive_bus/streams.py
# Should return NOTHING (except in from_redis deserialization)
```

### PHASE 5: E2E Integration Test (45 min)
**Goal**: Prove the bus works end-to-end

**Actions**:
1. Create `tests/test_bus_integration_e2e.py`:
   - Start real Redis (docker or local)
   - Producer emits event to stream
   - Consumer group reads event
   - Consumer processes and ACKs
   - Restart consumer
   - Verify replay works
2. Test causal chain preservation
3. Test consumer group load balancing

**Example**:
```python
@pytest.mark.integration
def test_e2e_emit_consume_ack_replay():
    # Setup
    bus = StreamBus()
    bus.emit("test:event", {"data": "test"}, emitter="producer")
    
    # Consume
    consumer = TestConsumer()
    events = bus.consume("test:event", "test_group", "worker-1", count=1)
    event = next(events)
    
    # Process
    result = consumer.process(event)
    assert result.action == "emit"
    
    # ACK
    bus.ack(event, group="test_group")
    
    # Verify no pending
    pending = bus.pending("test:event", "test_group")
    assert pending['count'] == 0
    
    # Replay
    replayed = bus.replay("test:event", start_id="0")
    assert len(replayed) == 1
```

### PHASE 6: Documentation (15 min)
**Goal**: Make architecture explicit

**Actions**:
1. Update `Vitruvyan_Bus_Invariants.md`:
   - Add: "Redis Streams is the canonical bus"
   - Remove references to Pub/Sub
   - Document event envelope layers
2. Update `IMPLEMENTATION_ROADMAP.md`:
   - Add Phase 0: Bus Hardening (complete)
   - Update consumer integration examples
3. Add architecture diagram in ASCII art

---

## RISK MITIGATION

### Risk 1: Breaking existing consumers
**Mitigation**: 
- Archive, don't delete
- Provide adapter layer
- Test each consumer after migration

### Risk 2: Performance regression
**Mitigation**:
- async wrappers use `asyncio.to_thread` (no blocking)
- Redis Streams is MORE performant than Pub/Sub (persistence overhead is minimal)

### Risk 3: Missing Pub/Sub functionality
**Mitigation**:
- Audit: what does Pub/Sub provide that Streams doesn't?
- Answer: NOTHING for our use case (Streams is strictly superior)

---

## SUCCESS CRITERIA

- [ ] All Pub/Sub files in `/archive`, not importable
- [ ] ONE canonical event envelope per layer (Transport, Cognitive)
- [ ] BaseConsumer._consume_loop() executes successfully
- [ ] 1+ integration test passes with real Redis
- [ ] Bus invariants enforced structurally
- [ ] Documentation explicitly states: "Redis Streams is the canonical bus"

---

## TIMELINE

**Total Estimated Time**: 3.5 hours
- Phase 1: 30 min
- Phase 2: 45 min
- Phase 3: 60 min
- Phase 4: 30 min
- Phase 5: 45 min
- Phase 6: 15 min

**Buffer**: +30 min for unexpected issues

**Total**: 4 hours (realistic)

---

## POST-HARDENING

After this refactor:
- ✅ Single transport backbone (Redis Streams only)
- ✅ Canonical event model (2 layers, explicit adapters)
- ✅ BaseConsumer functional on real bus
- ✅ E2E testable
- ✅ Bus invariants preserved

**THEN** we can:
1. Resume Phase 5 VEE fixes (15 min)
2. Complete Phase 5 documentation
3. Move to Phase 6 with confidence

---

**Prepared by**: GitHub Copilot (Claude Sonnet 4.5)  
**Approved by**: [Pending user confirmation]
