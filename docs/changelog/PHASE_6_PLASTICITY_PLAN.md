# Phase 6: Plasticity System — Implementation Plan
**Vitruvyan Cognitive Bus Adaptive Learning**

---

## Executive Summary

**Date**: January 24, 2026 12:00 UTC  
**Duration**: 2-3 hours (4 sub-phases)  
**Objective**: Implement governed learning system with bounded adjustments  
**Status**: 🚧 PLANNING

---

## Philosophy

> *"A system that cannot learn from its mistakes is brittle. A system that learns without governance is dangerous. We build the middle path."*

Vitruvyan's Plasticity System enables **bounded, auditable, reversible** learning from operational outcomes. Unlike traditional ML systems with unbounded optimization, Plasticity enforces:

1. **Bounded Adjustments**: All parameters have explicit (min, max) bounds
2. **Event-Driven Audit**: Every adjustment is a logged event
3. **Reversibility**: Rollback restores exact previous state
4. **Opt-In**: Consumers explicitly declare adjustable parameters
5. **Governance**: Orthodoxy validates all adjustments before application

---

## Current State (Pre-Phase 6)

**Phase 5 Complete**:
- ✅ NarrativeEngine (559 lines, 5 routing handlers)
- ✅ RiskGuardian (604 lines, 4 risk detection methods)
- ✅ EventAdapter integration (TransportEvent ↔ CognitiveEvent)
- ✅ ProcessResult pattern (emit/escalate/silence)
- ✅ 6/6 tests passing (100%)

**What's Missing**:
- ❌ No outcome tracking (decisions → results linkage)
- ❌ No parameter adjustment mechanism
- ❌ No learning feedback loop
- ❌ No adaptation governance

**Example Scenarios** (that Phase 6 will enable):

1. **NarrativeEngine Confidence Adaptation**:
   - Current: Fixed confidence threshold 0.6
   - After Phase 6: Threshold adapts based on escalation outcomes
   - If 80% of escalations are unnecessary → increase threshold 0.6 → 0.65
   - If 20% of low-confidence outputs are correct → decrease threshold 0.6 → 0.55

2. **RiskGuardian Threshold Tuning**:
   - Current: Concentration threshold fixed at 0.40 (40%)
   - After Phase 6: Threshold adapts based on alert outcomes
   - If 90% of 40% concentration alerts are false positives → increase to 0.45
   - If missed concentration risks below 40% → decrease to 0.38

3. **Working Memory Retention**:
   - Current: Fixed 30-day retention window
   - After Phase 6: Retention adapts based on context usage
   - If recent conversations referenced frequently → extend to 45 days
   - If old conversations never accessed → reduce to 21 days

---

## Implementation Plan

### Phase 6.1: Outcome Tracker (45 min)
**File**: `core/cognitive_bus/plasticity/outcome_tracker.py`

**Objective**: Link decisions (events) to their outcomes for learning.

**Schema** (PostgreSQL):
```sql
CREATE TABLE plasticity_outcomes (
    id SERIAL PRIMARY KEY,
    decision_event_id TEXT NOT NULL,           -- CognitiveEvent.id that made decision
    outcome_type TEXT NOT NULL,                -- 'escalation_resolved', 'false_positive', 'missed_risk'
    outcome_value FLOAT,                       -- Numeric outcome (0.0-1.0 success rate)
    outcome_metadata JSONB,                    -- Additional context
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    consumer_name TEXT NOT NULL,               -- Which consumer made decision
    parameter_name TEXT,                       -- Which parameter was used (e.g., 'confidence_threshold')
    parameter_value FLOAT,                     -- Value at decision time
    
    INDEX idx_plasticity_decision (decision_event_id),
    INDEX idx_plasticity_consumer (consumer_name, recorded_at),
    INDEX idx_plasticity_parameter (consumer_name, parameter_name, recorded_at)
);
```

**OutcomeTracker Class**:
```python
@dataclass
class Outcome:
    decision_event_id: str
    outcome_type: str
    outcome_value: float          # 0.0-1.0 (0 = failure, 1 = success)
    consumer_name: str
    parameter_name: Optional[str] = None
    parameter_value: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class OutcomeTracker:
    """
    Links decisions to outcomes for learning feedback.
    PostgreSQL backend, async interface.
    """
    def __init__(self, postgres: PostgresAgent):
        self.postgres = postgres
    
    async def record_outcome(self, outcome: Outcome) -> None:
        """Save outcome to PostgreSQL."""
        query = """
            INSERT INTO plasticity_outcomes 
            (decision_event_id, outcome_type, outcome_value, consumer_name, 
             parameter_name, parameter_value, outcome_metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        await asyncio.to_thread(
            self.postgres.execute_query,
            query,
            (outcome.decision_event_id, outcome.outcome_type, 
             outcome.outcome_value, outcome.consumer_name,
             outcome.parameter_name, outcome.parameter_value,
             json.dumps(outcome.metadata))
        )
    
    async def get_outcomes_for_parameter(
        self, 
        consumer_name: str, 
        parameter_name: str, 
        lookback_hours: int = 168  # 7 days default
    ) -> List[Outcome]:
        """Get recent outcomes for a specific parameter."""
        query = """
            SELECT decision_event_id, outcome_type, outcome_value, 
                   parameter_value, outcome_metadata
            FROM plasticity_outcomes
            WHERE consumer_name = %s 
              AND parameter_name = %s
              AND recorded_at > NOW() - INTERVAL '%s hours'
            ORDER BY recorded_at DESC
        """
        rows = await asyncio.to_thread(
            self.postgres.execute_query,
            query,
            (consumer_name, parameter_name, lookback_hours)
        )
        return [Outcome(...) for row in rows]
    
    async def get_success_rate(
        self, 
        consumer_name: str, 
        parameter_name: str, 
        lookback_hours: int = 168
    ) -> float:
        """Calculate success rate for parameter (0.0-1.0)."""
        outcomes = await self.get_outcomes_for_parameter(
            consumer_name, parameter_name, lookback_hours
        )
        if not outcomes:
            return 0.5  # Neutral if no data
        
        return sum(o.outcome_value for o in outcomes) / len(outcomes)
```

**Integration Points**:
- NarrativeEngine: Record outcome when escalation resolved/dismissed
- RiskGuardian: Record outcome when alert validated/false positive
- BaseConsumer: Generic hook for outcome recording

**Deliverable**: OutcomeTracker class (150 lines) + PostgreSQL migration (50 lines)

---

### Phase 6.2: Plasticity Manager (60 min)
**File**: `core/cognitive_bus/plasticity/manager.py`

**Objective**: Govern parameter adjustments with bounds enforcement.

**PlasticityConfig Dataclass**:
```python
@dataclass
class ParameterBounds:
    """Define adjustable parameter with bounds."""
    name: str
    min_value: float
    max_value: float
    step_size: float           # Minimum adjustment increment
    default_value: float
    description: str
    
@dataclass
class Adjustment:
    """Record of a parameter adjustment."""
    timestamp: datetime
    parameter: str
    old_value: float
    new_value: float
    reason: str
    success_rate: float        # Trigger metric (e.g., 0.85)
    event_id: str              # CognitiveEvent ID for adjustment
```

**PlasticityManager Class**:
```python
class PlasticityManager:
    """
    Governed learning manager with bounded adjustments.
    
    Principles:
    1. All adjustments bounded by (min, max)
    2. All adjustments logged as events
    3. All adjustments reversible
    4. Adjustments require governance approval (optional)
    """
    def __init__(
        self, 
        consumer: BaseConsumer, 
        bounds: Dict[str, ParameterBounds],
        outcome_tracker: OutcomeTracker,
        require_approval: bool = False  # If True, emit governance request
    ):
        self.consumer = consumer
        self.bounds = bounds
        self.tracker = outcome_tracker
        self.require_approval = require_approval
        self.history: List[Adjustment] = []
        self.disabled_parameters: Set[str] = set()
    
    async def propose_adjustment(
        self, 
        parameter: str, 
        delta: float,
        reason: str,
        success_rate: float
    ) -> ProcessResult:
        """
        Propose parameter adjustment.
        
        Returns:
        - ProcessResult.emit() if applied
        - ProcessResult.escalate() if approval required
        - ProcessResult.silence() if rejected (out of bounds)
        """
        # 1. Validate parameter exists
        if parameter not in self.bounds:
            logger.warning(f"Unknown parameter: {parameter}")
            return ProcessResult.silence(f"Parameter {parameter} not adjustable")
        
        if parameter in self.disabled_parameters:
            logger.info(f"Plasticity disabled for {parameter}")
            return ProcessResult.silence(f"Plasticity disabled for {parameter}")
        
        # 2. Calculate new value
        bound = self.bounds[parameter]
        current = getattr(self.consumer, parameter)
        new_value = current + delta
        
        # Snap to step_size
        new_value = round(new_value / bound.step_size) * bound.step_size
        
        # 3. Check bounds
        if not (bound.min_value <= new_value <= bound.max_value):
            logger.warning(
                f"Adjustment rejected: {parameter} {current} → {new_value} "
                f"out of bounds [{bound.min_value}, {bound.max_value}]"
            )
            return ProcessResult.silence(
                f"Adjustment out of bounds: {new_value} not in "
                f"[{bound.min_value}, {bound.max_value}]"
            )
        
        # 4. Record adjustment
        adjustment = Adjustment(
            timestamp=datetime.utcnow(),
            parameter=parameter,
            old_value=current,
            new_value=new_value,
            reason=reason,
            success_rate=success_rate,
            event_id=str(uuid.uuid4())
        )
        self.history.append(adjustment)
        
        # 5. Apply adjustment
        setattr(self.consumer, parameter, new_value)
        
        # 6. Emit adjustment event
        event = CognitiveEvent(
            id=adjustment.event_id,
            type="plasticity.adjustment",
            correlation_id=str(uuid.uuid4()),
            causation_id="",
            trace_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            source=self.consumer.__class__.__name__,
            payload={
                "parameter": parameter,
                "old_value": current,
                "new_value": new_value,
                "delta": delta,
                "reason": reason,
                "success_rate": success_rate,
                "bounds": {
                    "min": bound.min_value,
                    "max": bound.max_value
                }
            },
            metadata={}
        )
        
        logger.info(
            f"✅ Plasticity adjustment applied: {self.consumer.__class__.__name__}.{parameter} "
            f"{current:.3f} → {new_value:.3f} (reason: {reason})"
        )
        
        # 7. Return result
        if self.require_approval:
            return ProcessResult.escalate(
                reason=f"Plasticity adjustment requires approval: {parameter} {current} → {new_value}",
                confidence=0.8,
                events=[event]
            )
        else:
            return ProcessResult.emit(events=[event])
    
    async def rollback(self, steps: int = 1) -> ProcessResult:
        """
        Undo the last N adjustments.
        
        Returns ProcessResult with rollback events.
        """
        rollback_events = []
        
        for _ in range(steps):
            if not self.history:
                break
            
            adj = self.history.pop()
            setattr(self.consumer, adj.parameter, adj.old_value)
            
            event = CognitiveEvent(
                id=str(uuid.uuid4()),
                type="plasticity.rollback",
                correlation_id=adj.event_id,  # Link to original adjustment
                causation_id=adj.event_id,
                trace_id=adj.event_id,
                timestamp=datetime.utcnow(),
                source=self.consumer.__class__.__name__,
                payload={
                    "parameter": adj.parameter,
                    "restored_value": adj.old_value,
                    "discarded_value": adj.new_value,
                    "original_reason": adj.reason
                },
                metadata={}
            )
            rollback_events.append(event)
            
            logger.info(
                f"↩️ Rollback: {self.consumer.__class__.__name__}.{adj.parameter} "
                f"{adj.new_value:.3f} → {adj.old_value:.3f}"
            )
        
        return ProcessResult.emit(events=rollback_events)
    
    def disable_plasticity(self, parameter: str) -> None:
        """Disable plasticity for specific parameter."""
        self.disabled_parameters.add(parameter)
        logger.info(f"🚫 Plasticity disabled for {parameter}")
    
    def enable_plasticity(self, parameter: str) -> None:
        """Re-enable plasticity for parameter."""
        self.disabled_parameters.discard(parameter)
        logger.info(f"✅ Plasticity enabled for {parameter}")
```

**Deliverable**: PlasticityManager class (250 lines) + Adjustment dataclasses (50 lines)

---

### Phase 6.3: Consumer Integration (45 min)

**Objective**: Integrate plasticity into existing consumers (NarrativeEngine, RiskGuardian).

**6.3.1 BaseConsumer Plasticity Support**:

Add to `base_consumer.py`:
```python
class BaseConsumer:
    def __init__(self, config: ConsumerConfig):
        # ... existing code ...
        self.plasticity: Optional[PlasticityManager] = None
        self.outcome_tracker: Optional[OutcomeTracker] = None
    
    def enable_plasticity(
        self, 
        bounds: Dict[str, ParameterBounds],
        outcome_tracker: OutcomeTracker,
        require_approval: bool = False
    ) -> None:
        """Enable plasticity with defined parameter bounds."""
        self.plasticity = PlasticityManager(
            consumer=self,
            bounds=bounds,
            outcome_tracker=outcome_tracker,
            require_approval=require_approval
        )
        self.outcome_tracker = outcome_tracker
        logger.info(f"Plasticity enabled for {self.__class__.__name__}")
    
    async def record_outcome(self, outcome: Outcome) -> None:
        """Record outcome for learning (if tracker enabled)."""
        if self.outcome_tracker:
            await self.outcome_tracker.record_outcome(outcome)
```

**6.3.2 NarrativeEngine Plasticity**:

Add to `narrative_engine.py`:
```python
class NarrativeEngine(BaseConsumer):
    def __init__(self):
        super().__init__(config)
        
        # Adjustable parameters
        self.confidence_threshold = 0.6
        self.min_narrative_length = 100
        self.max_narrative_length = 500
        
        # Enable plasticity
        bounds = {
            "confidence_threshold": ParameterBounds(
                name="confidence_threshold",
                min_value=0.4,
                max_value=0.9,
                step_size=0.05,
                default_value=0.6,
                description="Minimum confidence for non-escalation"
            ),
            "min_narrative_length": ParameterBounds(
                name="min_narrative_length",
                min_value=50,
                max_value=200,
                step_size=10,
                default_value=100,
                description="Minimum words in narrative"
            )
        }
        
        # Initialize plasticity (if outcome tracker available)
        if hasattr(self, 'outcome_tracker'):
            self.enable_plasticity(
                bounds=bounds,
                outcome_tracker=self.outcome_tracker,
                require_approval=False  # NarrativeEngine can self-adjust
            )
```

**6.3.3 RiskGuardian Plasticity**:

Add to `risk_guardian.py`:
```python
class RiskGuardian(BaseConsumer):
    def __init__(self):
        super().__init__(config)
        
        # Adjustable parameters
        self.concentration_threshold = 0.40  # 40%
        self.extreme_z_threshold = 3.0
        
        bounds = {
            "concentration_threshold": ParameterBounds(
                name="concentration_threshold",
                min_value=0.30,   # Min 30%
                max_value=0.60,   # Max 60%
                step_size=0.05,
                default_value=0.40,
                description="Portfolio concentration alert threshold"
            ),
            "extreme_z_threshold": ParameterBounds(
                name="extreme_z_threshold",
                min_value=2.0,
                max_value=4.0,
                step_size=0.5,
                default_value=3.0,
                description="Z-score for extreme signal detection"
            )
        }
        
        if hasattr(self, 'outcome_tracker'):
            self.enable_plasticity(
                bounds=bounds,
                outcome_tracker=self.outcome_tracker,
                require_approval=True  # RiskGuardian needs approval (CRITICAL)
            )
```

**Deliverable**: BaseConsumer plasticity methods (80 lines) + Consumer integrations (60 lines)

---

### Phase 6.4: Learning Loop & Tests (30 min)

**Objective**: Implement learning feedback loop + test suite.

**6.4.1 Learning Loop** (new file: `plasticity/learning_loop.py`):

```python
class PlasticityLearningLoop:
    """
    Periodic task that analyzes outcomes and proposes adjustments.
    Runs every N hours, checks success rates, proposes adaptations.
    """
    def __init__(
        self, 
        consumers: List[BaseConsumer],
        interval_hours: int = 24  # Daily by default
    ):
        self.consumers = consumers
        self.interval = interval_hours
        self.running = False
    
    async def run(self) -> None:
        """Start learning loop (runs in background)."""
        self.running = True
        while self.running:
            await asyncio.sleep(self.interval * 3600)
            await self._analyze_and_adapt()
    
    async def _analyze_and_adapt(self) -> None:
        """Analyze outcomes and propose adjustments."""
        for consumer in self.consumers:
            if not consumer.plasticity:
                continue
            
            for param_name, bound in consumer.plasticity.bounds.items():
                # Get success rate for last 7 days
                success_rate = await consumer.outcome_tracker.get_success_rate(
                    consumer_name=consumer.__class__.__name__,
                    parameter_name=param_name,
                    lookback_hours=168  # 7 days
                )
                
                # Propose adjustment if success rate extreme
                if success_rate < 0.4:  # Too many failures
                    # Relax threshold (increase for confidence, decrease for risk)
                    delta = bound.step_size if "threshold" in param_name else -bound.step_size
                    await consumer.plasticity.propose_adjustment(
                        parameter=param_name,
                        delta=delta,
                        reason=f"Low success rate: {success_rate:.2%}",
                        success_rate=success_rate
                    )
                elif success_rate > 0.9:  # Too permissive
                    # Tighten threshold
                    delta = -bound.step_size if "threshold" in param_name else bound.step_size
                    await consumer.plasticity.propose_adjustment(
                        parameter=param_name,
                        delta=delta,
                        reason=f"High success rate: {success_rate:.2%} (can be stricter)",
                        success_rate=success_rate
                    )
```

**6.4.2 Test Suite** (`tests/test_phase6_plasticity.py`):

```python
class TestPlasticitySystem:
    """Test suite for Phase 6 Plasticity."""
    
    def test_outcome_tracker_record():
        """Test outcome recording to PostgreSQL."""
        tracker = OutcomeTracker(PostgresAgent())
        outcome = Outcome(
            decision_event_id="123",
            outcome_type="escalation_resolved",
            outcome_value=1.0,
            consumer_name="NarrativeEngine",
            parameter_name="confidence_threshold",
            parameter_value=0.6
        )
        asyncio.run(tracker.record_outcome(outcome))
        # Assert: row in plasticity_outcomes table
    
    def test_plasticity_adjustment_within_bounds():
        """Test adjustment applies when within bounds."""
        consumer = MockConsumer()
        consumer.threshold = 0.6
        
        bounds = {
            "threshold": ParameterBounds("threshold", 0.4, 0.9, 0.05, 0.6, "Test")
        }
        manager = PlasticityManager(consumer, bounds, Mock())
        
        result = asyncio.run(manager.propose_adjustment(
            "threshold", 0.1, "test", 0.85
        ))
        
        assert result.action == "emit"
        assert consumer.threshold == 0.7  # 0.6 + 0.1
        assert len(manager.history) == 1
    
    def test_plasticity_adjustment_out_of_bounds():
        """Test adjustment rejected when out of bounds."""
        consumer = MockConsumer()
        consumer.threshold = 0.85
        
        bounds = {
            "threshold": ParameterBounds("threshold", 0.4, 0.9, 0.05, 0.6, "Test")
        }
        manager = PlasticityManager(consumer, bounds, Mock())
        
        result = asyncio.run(manager.propose_adjustment(
            "threshold", 0.1, "test", 0.95
        ))
        
        assert result.action == "silence"  # Rejected
        assert consumer.threshold == 0.85  # Unchanged
    
    def test_plasticity_rollback():
        """Test rollback restores previous value."""
        consumer = MockConsumer()
        consumer.threshold = 0.6
        
        manager = PlasticityManager(consumer, bounds, Mock())
        asyncio.run(manager.propose_adjustment("threshold", 0.1, "test", 0.8))
        assert consumer.threshold == 0.7
        
        asyncio.run(manager.rollback(steps=1))
        assert consumer.threshold == 0.6  # Restored
    
    def test_plasticity_disabled():
        """Test disabled parameter not adjustable."""
        consumer = MockConsumer()
        manager = PlasticityManager(consumer, bounds, Mock())
        manager.disable_plasticity("threshold")
        
        result = asyncio.run(manager.propose_adjustment("threshold", 0.1, "test", 0.8))
        assert result.action == "silence"
    
    def test_learning_loop_adapts():
        """Test learning loop proposes adjustments."""
        # Create consumer with low success rate outcomes
        # Run learning loop
        # Assert: adjustment proposed
        pass
```

**Deliverable**: LearningLoop (100 lines) + test suite (200 lines, 6 tests)

---

## Success Metrics

### Completeness
- [ ] OutcomeTracker: Links decisions → outcomes (PostgreSQL backend)
- [ ] PlasticityManager: Bounded adjustments with governance
- [ ] BaseConsumer integration: enable_plasticity(), record_outcome()
- [ ] NarrativeEngine plasticity: confidence_threshold adjustable
- [ ] RiskGuardian plasticity: concentration_threshold adjustable
- [ ] Learning loop: Periodic analysis + adaptation
- [ ] Test suite: 6/6 tests passing

### Quality
- [ ] All adjustments bounded (min, max enforced)
- [ ] All adjustments logged as events (audit trail)
- [ ] Rollback restores exact state (reversibility)
- [ ] Plasticity can be disabled per-parameter
- [ ] Governance approval optional (CRITICAL consumers require it)
- [ ] No unbounded learning possible (structural guarantee)

### Timeline
- **Estimated**: 3 hours (4 sub-phases)
- **Phase 6.1**: 45 min (OutcomeTracker)
- **Phase 6.2**: 60 min (PlasticityManager)
- **Phase 6.3**: 45 min (Consumer integration)
- **Phase 6.4**: 30 min (Learning loop + tests)

---

## Architecture: Before vs After

### Before Phase 6 ❌

```
Consumer (NarrativeEngine)
    confidence_threshold = 0.6  ← HARDCODED
    
User Query → process() → 
    if confidence < 0.6:
        escalate()  ← FIXED THRESHOLD
    
No outcome tracking
No parameter adjustment
No learning from experience
```

### After Phase 6 ✅

```
Consumer (NarrativeEngine)
    confidence_threshold = 0.6  ← ADJUSTABLE (bounds: 0.4-0.9)
    plasticity: PlasticityManager
    outcome_tracker: OutcomeTracker
    
User Query → process() → 
    if confidence < self.confidence_threshold:
        escalate()
        
    # Record outcome
    outcome = Outcome(
        decision_event_id=event.id,
        outcome_type="escalation_resolved",
        outcome_value=1.0 if resolved else 0.0
    )
    await self.record_outcome(outcome)

Learning Loop (runs daily):
    success_rate = tracker.get_success_rate("NarrativeEngine", "confidence_threshold")
    
    if success_rate < 0.4:  # Too strict
        plasticity.propose_adjustment("confidence_threshold", -0.05)
        # 0.6 → 0.55 (more lenient)
    
    if success_rate > 0.9:  # Too permissive
        plasticity.propose_adjustment("confidence_threshold", +0.05)
        # 0.6 → 0.65 (stricter)

All adjustments:
    ✅ Bounded (0.4-0.9)
    ✅ Logged as events
    ✅ Reversible (rollback)
    ✅ Governed (approval for CRITICAL)
```

---

## Files to Create

1. **`core/cognitive_bus/plasticity/__init__.py`** (exports)
2. **`core/cognitive_bus/plasticity/outcome_tracker.py`** (150 lines)
3. **`core/cognitive_bus/plasticity/manager.py`** (300 lines)
4. **`core/cognitive_bus/plasticity/learning_loop.py`** (100 lines)
5. **`tests/test_phase6_plasticity.py`** (200 lines)
6. **`migrations/006_plasticity_outcomes.sql`** (50 lines)

## Files to Modify

1. **`core/cognitive_bus/consumers/base_consumer.py`** (add plasticity methods)
2. **`core/cognitive_bus/consumers/narrative_engine.py`** (add bounds config)
3. **`core/cognitive_bus/consumers/risk_guardian.py`** (add bounds config)
4. **`core/cognitive_bus/IMPLEMENTATION_ROADMAP.md`** (update Phase 6 status)

**Total**: 10 files (6 create, 4 modify)

---

## Testing Strategy

### Unit Tests (tests/test_phase6_plasticity.py)
1. `test_outcome_tracker_record`: PostgreSQL insert/query
2. `test_plasticity_adjustment_within_bounds`: Apply adjustment
3. `test_plasticity_adjustment_out_of_bounds`: Reject adjustment
4. `test_plasticity_rollback`: Undo adjustment
5. `test_plasticity_disabled`: Disabled parameter unchanged
6. `test_learning_loop_adapts`: Periodic adaptation

### Integration Tests
1. NarrativeEngine with plasticity enabled
2. RiskGuardian with approval required
3. Learning loop analyzing real outcomes
4. Rollback after bad adjustment

### E2E Validation
1. Generate 100 escalations
2. Record outcomes (80% resolved successfully)
3. Run learning loop
4. Verify threshold adjusted
5. Generate 100 more escalations
6. Verify improved success rate

---

## Risks & Mitigation

### Risk 1: Unbounded Learning
**Mitigation**: 
- Structural bounds enforcement (min, max checked)
- Step size limits (0.05 increments)
- Rollback capability (undo bad adjustments)
- Disable plasticity per-parameter

### Risk 2: Oscillation
**Mitigation**:
- Learning loop runs daily (not real-time)
- Lookback window 7 days (smooths variance)
- Step size small (0.05, not 0.5)
- Success rate thresholds (0.4-0.9, not 0.3-0.95)

### Risk 3: Bad Adjustments
**Mitigation**:
- All adjustments logged as events (audit trail)
- Governance approval for CRITICAL consumers
- Rollback restores exact state
- Disable plasticity if needed

### Risk 4: PostgreSQL Bottleneck
**Mitigation**:
- Async queries via asyncio.to_thread
- Indexed columns (consumer_name, parameter_name, recorded_at)
- Optional Redis caching (future)

---

## Next Steps

### Immediate (This Session)
1. **Create directory structure** (2 min)
2. **Implement Phase 6.1** (OutcomeTracker, 45 min)
3. **Implement Phase 6.2** (PlasticityManager, 60 min)
4. **Implement Phase 6.3** (Consumer integration, 45 min)
5. **Implement Phase 6.4** (Learning loop + tests, 30 min)
6. **Run tests** (5 min)
7. **Commit Phase 6** (5 min)

### Post-Phase 6
- Monitor adjustment frequency (daily)
- Validate no unbounded adjustments (code review)
- Add Prometheus metrics (adjustment_total, rollback_total)
- Create admin CLI for manual adjustments

---

## Conclusion

**Phase 6: Plasticity System** enables **governed, bounded, reversible learning** from operational outcomes. Unlike unbounded ML systems, Vitruvyan's plasticity:

✅ Enforces parameter bounds (min, max)  
✅ Logs all adjustments as events  
✅ Enables rollback (exact restoration)  
✅ Requires governance for CRITICAL consumers  
✅ Prevents unbounded learning (structural guarantee)

The system learns from experience while remaining **auditable, safe, and reversible** — the Socratic middle path.

---

**Plan Date**: January 24, 2026 12:00 UTC  
**Author**: Vitruvyan Core Team  
**Status**: 🚧 READY FOR IMPLEMENTATION
