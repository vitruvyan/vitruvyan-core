# Orthodoxy Wardens Implementation Guide

**Last Updated**: February 8, 2026  
**Target Audience**: Developers working on compliance, governance, and event-driven systems  
**Prerequisites**: Familiarity with FastAPI, Redis Streams, event-driven architecture

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Concepts](#core-concepts)
3. [Sacred Roles Architecture](#sacred-roles-architecture)
4. [Event Handlers](#event-handlers)
5. [Synaptic Conclave Integration](#synaptic-conclave-integration)
6. [Agent Backend](#agent-backend)
7. [API Implementation](#api-implementation)
8. [Testing Strategy](#testing-strategy)
9. [Deployment](#deployment)
10. [Best Practices](#best-practices)

---

## 1. System Overview

### Purpose
Orthodoxy Wardens is a **governance layer** that validates system compliance and orchestrates auto-correction workflows through event-driven architecture. It acts as the "immune system" of Vitruvyan, detecting and remediating architectural violations.

### Position in Ecosystem
```
LangGraph/Neural Engine/Babel → Emit completion events → Redis Streams
                                                              ↓
                                          Orthodoxy Wardens (this service)
                                                              ↓
                                  Validate + Log + Auto-correct → PostgreSQL
```

### Key Responsibilities
1. **Audit Orchestration**: Coordinate multi-agent workflows (Inquisitor → Confessor → Abbot)
2. **Heresy Detection**: Identify architectural violations in real-time
3. **Auto-Correction**: Execute remediation via AutoCorrector agent
4. **Event Logging**: Persist all compliance events to PostgreSQL
5. **Risk Assessment**: Analyze system health and compliance drift

---

## 2. Core Concepts

### 2.1 Theological Metaphor → Functional Mapping

**Why theological naming?**
- **Mnemonic**: Easier to remember "Confessor orchestrates audits" than "Class A coordinates validation"
- **Domain clarity**: Clear separation of concerns (each role has specific purp function)
- **Cultural consistency**: Vitruvyan uses epistemic metaphors throughout (Sacred Orders, Synaptic Conclave)

**Pragmatic equivalents**:
| Theological | Functional | Purpose |
|-------------|------------|---------|
| Confessor | AuditOrchestrator | Coordinates validation workflows |
| Penitent | AutoCorrector | Executes remediation actions |
| Chronicler | EventLogger | Persists events to database |
| Inquisitor | ComplianceValidator | Investigates violations |
| Abbot | AuditFinalizer | Approves/rejects audit verdicts |

**Alias Methods**: All roles provide functional aliases (e.g., `validate()` alongside theological `confess()`).

```python
# Theological (internal API)
confessor.confess(audit_request)

# Functional (external API) - SAME METHOD
confessor.validate(audit_request)
```

### 2.2 Event-Driven Architecture

**Pattern**: Event Sourcing + CQRS (Command Query Responsibility Segregation)

**Flow**:
```
Event Published (Redis Streams) → Consumer Group → Event Handler → Sacred Role → Agent Backend → Result Logged
```

**Benefits**:
- **Decoupling**: Services don't call each other directly
- **Scalability**: Multiple consumers can process same stream
- **Auditability**: All events persisted, full history available
- **Resilience**: Consumer failures don't affect publishers

**Trade-offs**:
- **Complexity**: Harder to debug than synchronous calls
- **Consistency**: Eventual consistency model
- **Latency**: Asynchronous processing adds delay

---

## 3. Sacred Roles Architecture

### 3.1 Base Class: SacredRole

**Location**: `core/roles.py` (lines 29-85)

**Purpose**: Shared infrastructure for all roles (Redis Streams connection, logging, event emission)

**Key Methods**:
```python
class SacredRole:
    def __init__(self):
        self.bus = StreamBus(host=..., port=...)  # Redis Streams client
        self.logger = structlog.get_logger(...)
        self.postgres = PostgresAgent()            # Database client
    
    def emit_event(self, channel: str, event_type: str, data: Dict) -> str:
        """Publish event to Redis Streams"""
        event = CognitiveEvent(event_type=event_type, payload=data)
        self.bus.publish(channel, event.to_transport_event())
        return event.event_id
    
    def log_action(self, action: str, details: Dict) -> None:
        """Log to PostgreSQL via postgres_agent"""
        self.postgres.log_orthodoxy_action(action=action, details=details)
```

**Design Decision**: Base class provides plumbing, subclasses implement business logic. This avoids code duplication while maintaining role-specific behavior.

### 3.2 OrthodoxConfessor (Audit Orchestrator)

**Location**: `core/roles.py` (lines 87-135)

**Functional Alias**: `validate()`, `orchestrate_audit()`

**Purpose**: Coordinates multi-step audit workflows using AutonomousAuditAgent (LangGraph)

**Workflow**:
```
1. Receive audit request via event or API
2. Call AutonomousAuditAgent.run(scope=request.scope)
3. Parse LangGraph output (compliance status, findings)
4. Emit completion event with results
5. Log to PostgreSQL
```

**Example Usage**:
```python
from core.roles import OrthodoxConfessor

confessor = OrthodoxConfessor()

# Audit request
result = confessor.confess({
    "scope": "neural_engine",
    "urgency": "high",
    "requested_by": "admin"
})

# Result structure
{
    "status": "completed",
    "compliance_level": 0.85,
    "findings": [
        {"severity": "warning", "message": "Stale cache detected"},
        {"severity": "info", "message": "Performance within thresholds"}
    ],
    "recommendations": ["Clear cache", "Monitor memory usage"]
}
```

**Integration with AutonomousAuditAgent**:
```python
# core/roles.py (lines 110-120)
from core.governance.orthodoxy_wardens.confessor_agent import AutonomousAuditAgent

class OrthodoxConfessor(SacredRole):
    def __init__(self):
        super().__init__()
        self.agent = AutonomousAuditAgent(config={...})
    
    def confess(self, request: Dict) -> Dict:
        # Delegate to LangGraph workflow
        audit_result = self.agent.run(request)
        
        # Emit completion event
        self.emit_event("orthodoxy.audit.completed", "audit.finished", audit_result)
        
        return audit_result
```

### 3.3 OrthodoxPenitent (Auto-Corrector)

**Location**: `core/roles.py` (lines 137-180)

**Functional Alias**: `remediate()`, `auto_correct()`

**Purpose**: Execute remediation actions when heresies (violations) detected

**Workflow**:
```
1. Receive heresy event (violation detected)
2. Analyze severity and scope
3. Call AutoCorrector.fix(issue=violation)
4. Verify correction applied
5. Emit purification event
6. Log remediation to PostgreSQL
```

**Example Usage**:
```python
from core.roles import OrthodoxPenitent

penitent = OrthodoxPenitent()

# Remediation request
result = penitent.purify({
    "heresy_type": "stale_cache",
    "affected_service": "neural_engine",
    "severity": "medium",
    "auto_fix": True
})

# Result structure
{
    "status": "purified",
    "actions_taken": ["cache_cleared", "service_restarted"],
    "verification": "passed",
    "duration_ms": 1250
}
```

**AutoCorrector Integration**:
```python
# core/roles.py (lines 155-165)
from core.governance.orthodoxy_wardens.penitent_agent import AutoCorrector

class OrthodoxPenitent(SacredRole):
    def __init__(self):
        super().__init__()
        self.corrector = AutoCorrector()
    
    def purify(self, heresy: Dict) -> Dict:
        # Execute correction
        correction_result = self.corrector.fix(issue=heresy)
        
        # Verify fix applied
        verified = self._verify_correction(correction_result)
        
        # Emit purification event
        self.emit_event("orthodoxy.purification.completed", "heresy.purified", {
            "original_heresy": heresy,
            "correction": correction_result,
            "verified": verified
        })
        
        return correction_result
```

### 3.4 OrthodoxChronicler (Event Logger)

**Location**: `core/roles.py` (lines 182-220)

**Functional Alias**: `log()`, `record_event()`

**Purpose**: Persist all compliance events to PostgreSQL via SystemMonitor

**Workflow**:
```
1. Receive system event (any completion from other services)
2. Extract metadata (timestamp, service, event_type)
3. Call SystemMonitor.log_event(event_data)
4. Persist to PostgreSQL orthodoxy_logs table
5. Emit logging confirmation
```

**Example Usage**:
```python
from core.roles import OrthodoxChronicler

chronicler = OrthodoxChronicler()

# Log event
chronicler.record({
    "event_type": "neural_engine.screening.completed",
    "service": "neural_engine",
    "tickers": ["AAPL", "NVDA"],
    "composite_z": 1.85,
    "timestamp": "2026-02-08T18:48:00Z"
})
```

**SystemMonitor Integration**:
```python
# core/roles.py (lines 200-210)
from core.governance.orthodoxy_wardens.chronicler_agent import SystemMonitor

class OrthodoxChronicler(SacredRole):
    def __init__(self):
        super().__init__()
        self.monitor = SystemMonitor()
    
    def record(self, event: Dict) -> None:
        # Persist to PostgreSQL
        self.monitor.log_event(
            service=event["service"],
            event_type=event["event_type"],
            payload=event,
            timestamp=event.get("timestamp")
        )
        
        # Emit confirmation
        self.emit_event("orthodoxy.logging.completed", "event.logged", {
            "original_event_id": event.get("event_id"),
            "logged_at": datetime.now().isoformat()
        })
```

### 3.5 OrthodoxInquisitor (Compliance Investigator)

**Location**: `core/roles.py` (lines 222-270)

**Functional Alias**: `investigate()`, `validate_compliance()`

**Purpose**: Deep-dive compliance investigations using ComplianceValidator

**Workflow**:
```
1. Receive investigation request (triggered by suspicious events)
2. Gather evidence (logs, metrics, code analysis)
3. Call ComplianceValidator.analyze(scope=request.scope)
4. Generate compliance report with findings
5. Emit investigation results
6. Log to PostgreSQL
```

**Example Usage**:
```python
from core.roles import OrthodoxInquisitor

inquisitor = OrthodoxInquisitor()

# Initiate investigation
report = inquisitor.investigate({
    "scope": "babel_gardens",
    "suspicion": "unusual_sentiment_scores",
    "timeframe": "last_24h"
})

# Report structure
{
    "compliance_status": "warning",
    "findings": [
        {
            "category": "data_quality",
            "severity": "medium",
            "description": "35% of sentiment scores are neutral (expected: <20%)",
            "evidence": {"neutral_count": 3500, "total": 10000}
        }
    ],
    "recommendations": [
        "Review sentiment model calibration",
        "Check for input data bias"
    ]
}
```

**ComplianceValidator Integration**:
```python
# core/roles.py (lines 245-260)
from core.governance.orthodoxy_wardens.inquisitor_agent import ComplianceValidator

class OrthodoxInquisitor(SacredRole):
    def __init__(self):
        super().__init__()
        self.validator = ComplianceValidator(llm_interface=...)
    
    def investigate(self, request: Dict) -> Dict:
        # Gather evidence
        evidence = self._gather_evidence(request["scope"])
        
        # Analyze compliance
        analysis = self.validator.analyze(
            scope=request["scope"],
            evidence=evidence,
            context=request
        )
        
        # Generate report
        report = self._format_compliance_report(analysis)
        
        # Emit results
        self.emit_event("orthodoxy.investigation.completed", "investigation.finished", report)
        
        return report
```

### 3.6 OrthodoxAbbot (Audit Finalizer)

**Location**: `core/roles.py` (lines 272-320)

**Functional Alias**: `finalize()`, `approve_audit()`

**Purpose**: Review and approve/reject audit verdicts

**Workflow**:
```
1. Receive audit results from Confessor
2. Review findings and recommendations
3. Apply business rules (e.g., auto-approve if compliance >90%)
4. Generate final verdict
5. Emit verdict event
6. Log to PostgreSQL
```

**Example Usage**:
```python
from core.roles import OrthodoxAbbot

abbot = OrthodoxAbbot()

# Finalize audit
verdict = abbot.approve({
    "audit_id": "audit_20260208_184800",
    "compliance_level": 0.85,
    "findings_count": 3,
    "severity_max": "warning"
})

# Verdict structure
{
    "verdict": "approved",
    "rationale": "Compliance within acceptable range (85%), no critical findings",
    "action_required": False,
    "next_audit_date": "2026-02-15T00:00:00Z"
}
```

---

## 4. Event Handlers

### 4.1 Dependency Injection Pattern

**Problem**: Circular imports if event_handlers imports roles directly.

**Solution**: Inject Sacred Roles during startup.

**Implementation** (`core/event_handlers.py`, lines 15-35):
```python
# Global references (injected during startup)
sacred_confessor = None
sacred_penitent = None
sacred_chronicler = None
sacred_inquisitor = None
sacred_abbot = None

def inject_sacred_roles(confessor, penitent, chronicler, inquisitor, abbot):
    """
    Dependency injection for Sacred Roles.
    Called during FastAPI startup to avoid circular imports.
    """
    global sacred_confessor, sacred_penitent, sacred_chronicler, sacred_inquisitor, sacred_abbot
    
    sacred_confessor = confessor
    sacred_penitent = penitent
    sacred_chronicler = chronicler
    sacred_inquisitor = inquisitor
    sacred_abbot = abbot
    
    logger.info("✅ Sacred Roles injected into event handlers")
```

**Usage in main.py** (lines 283-294):
```python
@app.on_event("startup")
async def sacred_initialization():
    # Initialize Sacred Roles
    sacred_confessor = OrthodoxConfessor()
    sacred_penitent = OrthodoxPenitent()
    sacred_chronicler = OrthodoxChronicler()
    sacred_inquisitor = OrthodoxInquisitor()
    sacred_abbot = OrthodoxAbbot()
    
    # Inject into event handlers
    event_handlers.inject_sacred_roles(
        confessor=sacred_confessor,
        penitent=sacred_penitent,
        chronicler=sacred_chronicler,
        inquisitor=sacred_inquisitor,
        abbot=sacred_abbot
    )
```

### 4.2 handle_audit_request

**Location**: `core/event_handlers.py` (lines 40-80)

**Purpose**: Orchestrate Inquisitor → Confessor → Abbot workflow for audit requests

**Workflow**:
```
1. Receive audit request event
2. Parse request payload
3. Call Inquisitor.investigate() (evidence gathering)
4. Call Confessor.confess() (audit execution)
5. Call Abbot.approve() (verdict finalization)
6. Emit final audit result
```

**Implementation**:
```python
async def handle_audit_request(event: CognitiveEvent):
    """
    Handle orthodoxy.audit.requested events.
    
    Orchestrates multi-agent audit workflow:
    1. Inquisitor gathers evidence
    2. Confessor executes audit
    3. Abbot finalizes verdict
    """
    try:
        request = event.payload
        logger.info(f"🏛️ Audit requested: {request.get('scope', 'unknown')}")
        
        # Phase 1: Investigation (evidence gathering)
        investigation = sacred_inquisitor.investigate(request)
        logger.info(f"🔍 Investigation complete: {investigation['compliance_status']}")
        
        # Phase 2: Audit (validation)
        audit_result = sacred_confessor.confess({
            **request,
            "evidence": investigation
        })
        logger.info(f"⚖️ Audit complete: compliance={audit_result['compliance_level']}")
        
        # Phase 3: Finalization (verdict)
        verdict = sacred_abbot.approve({
            "audit_id": event.event_id,
            "audit_result": audit_result,
            "investigation": investigation
        })
        logger.info(f"✅ Verdict: {verdict['verdict']}")
        
        # Emit final result
        sacred_confessor.emit_event(
            "orthodoxy.audit.completed",
            "audit.finalized",
            {
                "audit_id": event.event_id,
                "investigation": investigation,
                "audit": audit_result,
                "verdict": verdict
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Audit workflow failed: {e}")
        # Emit failure event for observability
        sacred_confessor.emit_event(
            "orthodoxy.audit.failed",
            "audit.error",
            {"error": str(e), "audit_id": event.event_id}
        )
```

### 4.3 handle_heresy_detection

**Location**: `core/event_handlers.py` (lines 85-110)

**Purpose**: Trigger Penitent + Chronicler when heresy (violation) detected

**Workflow**:
```
1. Receive heresy event
2. Call Penitent.purify() (auto-correction)
3. Call Chronicler.record() (logging)
4. Emit purification result
```

**Implementation**:
```python
async def handle_heresy_detection(event: CognitiveEvent):
    """
    Handle heresy detection events (architectural violations).
    
    Triggers auto-correction via Penitent and logging via Chronicler.
    """
    try:
        heresy = event.payload
        logger.warning(f"⚠️ Heresy detected: {heresy.get('type', 'unknown')}")
        
        # Auto-correction
        correction = sacred_penitent.purify(heresy)
        logger.info(f"🧹 Purification complete: {correction['status']}")
        
        # Log heresy + correction
        sacred_chronicler.record({
            "event_type": "orthodoxy.heresy.purified",
            "heresy": heresy,
            "correction": correction,
            "timestamp": datetime.now().isoformat()
        })
        
        # Emit result
        sacred_penitent.emit_event(
            "orthodoxy.purification.completed",
            "heresy.purified",
            {
                "original_event_id": event.event_id,
                "heresy": heresy,
                "correction": correction
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Heresy handling failed: {e}")
```

### 4.4 handle_system_events

**Location**: `core/event_handlers.py` (lines 115-136)

**Purpose**: Log completion events from other services (Neural Engine, Babel, VEE, etc.)

**Workflow**:
```
1. Receive system event (e.g., neural_engine.screening.completed)
2. Call Chronicler.record() (persist to PostgreSQL)
3. No response emitted (fire-and-forget logging)
```

**Implementation**:
```python
async def handle_system_events(event: CognitiveEvent):
    """
    Handle system completion events from other services.
    
    Pure logging - no response emitted.
    """
    try:
        logger.debug(f"📝 System event received: {event.event_type}")
        
        # Log to PostgreSQL
        sacred_chronicler.record({
            "event_type": event.event_type,
            "service": event.payload.get("service", "unknown"),
            "payload": event.payload,
            "timestamp": event.timestamp
        })
        
    except Exception as e:
        logger.error(f"❌ System event logging failed: {e}")
        # Non-critical failure - don't block other processing
```

---

## 5. Synaptic Conclave Integration

### 5.1 Redis Streams Architecture

**Why Streams over Pub/Sub?**
- **Durability**: Events persist until acknowledged
- **Consumer groups**: Multiple consumers can process same stream
- **Ordering**: FIFO within single stream
- **Acknowledgments**: Exactly-once processing guarantees

**See**: `vitruvyan_core/core/synaptic_conclave/docs/COGNITIVE_BUS_GUIDE.md` for complete architecture.

### 5.2 Channel Configuration

**Location**: `main.py` (lines 120-128)

```python
sacred_channels = {
    "orthodoxy.audit.requested": handle_audit_request,
    "orthodoxy.validation.requested": handle_audit_request,  # Reuse handler
    "neural_engine.screening.completed": handle_system_events,
    "babel.sentiment.completed": handle_system_events,
    "memory.write.completed": handle_system_events,
    "vee.explanation.completed": handle_system_events,
    "langgraph.response.completed": handle_system_events
}
```

**Design Decision**: Map channels to handlers at startup, not hardcoded in consumer loop. Easier to add/remove channels.

### 5.3 Consumer Group Creation

**Location**: `main.py` (lines 133-143)

```python
group_name = "group:orthodoxy_main"
consumer_id = "orthodoxy_main:worker_1"

for channel, handler in sacred_channels.items():
    try:
        bus.create_consumer_group(channel, group_name)
        logger.info(f"⚖️ Created consumer group '{group_name}' on {channel}")
    except Exception as e:
        # Consumer group may already exist (idempotent operation)
        logger.debug(f"Consumer group '{group_name}' on {channel}: {e}")
```

**Idempotency**: `create_consumer_group()` is idempotent - safe to call even if group exists.

### 5.4 Background Listener Thread

**Problem**: `asyncio.create_task()` inside `@app.on_event("startup")` blocks FastAPI startup (startup never completes).

**Solution**: Run consumers in separate daemon thread with own event loop.

**Implementation** (`main.py`, lines 148-170):
```python
def start_listeners_thread():
    """Launch all consumption loops in a background thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    tasks = []
    for channel, handler in sacred_channels.items():
        task = loop.create_task(_consume_channel(bus, channel, group_name, consumer_id, handler))
        tasks.append(task)
    
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down Synaptic Conclave listeners")
    finally:
        for task in tasks:
            task.cancel()
        loop.close()

# Start in daemon thread (won't block shutdown)
listener_thread = threading.Thread(target=start_listeners_thread, daemon=True, name="OrthodoxyListenerThread")
listener_thread.start()
logger.info("🔥 Synaptic Conclave listeners thread started (background processing active)")
```

**Benefits**:
- FastAPI startup completes immediately
- Listeners run forever in background
- Daemon thread auto-terminates on container shutdown
- No zombie processes

### 5.5 Event Consumption Loop

**Location**: `main.py` (lines 145-175)

```python
async def _consume_channel(bus: StreamBus, channel: str, group: str, consumer: str, handler):
    """Background task to consume events from a sacred channel"""
    logger.info(f"👂 Starting consumption: {channel} (group: {group}, consumer: {consumer})")
    
    try:
        for event in bus.consume(channel, group, consumer, block_ms=5000):
            try:
                # Convert TransportEvent to CognitiveEvent for backward compatibility
                cognitive_event = CognitiveEvent(
                    event_id=event.event_id,
                    event_type=event.data.get("event_type", "system.event"),
                    payload=event.data,
                    correlation_id=event.data.get("correlation_id"),
                    timestamp=event.timestamp
                )
                
                # Call handler
                await handler(cognitive_event)
                
                # Acknowledge event
                bus.acknowledge(event.stream, group, event.event_id)
                logger.debug(f"✅ Processed and acknowledged event {event.event_id} from {channel}")
                
            except Exception as e:
                logger.error(f"❌ Error processing event from {channel}: {e}")
                # Don't acknowledge on error - event will be retried
                
    except Exception as e:
        logger.error(f"💀 Fatal error in consumption loop for {channel}: {e}")
        # TODO: Implement reconnection logic
```

**Acknowledgment Strategy**: Only acknowledge after successful processing. On failure, event remains pending for retry.

---

## 6. Agent Backend

### 6.1 AutonomousAuditAgent (LangGraph)

**Location**: `vitruvyan_core/core/governance/orthodoxy_wardens/confessor_agent.py`

**Purpose**: Multi-step workflow orchestration using LangGraph

**Nodes**:
1. **parse_scope** → Parse audit request scope
2. **gather_evidence** → Collect relevant logs/metrics
3. **analyze_compliance** → LLM-based analysis
4. **generate_recommendations** → Actionable next steps
5. **format_report** → Structure final audit report

**Integration**:
```python
# core/roles.py
from core.governance.orthodoxy_wardens.confessor_agent import AutonomousAuditAgent

confessor_agent = AutonomousAuditAgent(config={
    "llm_interface": llm_interface,
    "db_manager": postgres_agent
})

audit_result = confessor_agent.run(scope="neural_engine")
```

### 6.2 AutoCorrector

**Location**: `vitruvyan_core/core/governance/orthodoxy_wardens/penitent_agent.py`

**Purpose**: Execute remediation actions (cache clearing, service restarts, config updates)

**Methods**:
- `fix(issue: Dict) -> Dict`: Main entry point
- `clear_cache(service: str)`: Redis cache invalidation
- `restart_service(service: str)`: Docker container restart (if permissions allow)
- `update_config(service: str, config: Dict)`: Hot-reload configuration

**Integration**:
```python
# core/roles.py
from core.governance.orthodoxy_wardens.penitent_agent import AutoCorrector

penitent_agent = AutoCorrector()

correction_result = penitent_agent.fix(issue={
    "type": "stale_cache",
    "service": "neural_engine",
    "severity": "medium"
})
```

### 6.3 SystemMonitor

**Location**: `vitruvyan_core/core/governance/orthodoxy_wardens/chronicler_agent.py`

**Purpose**: Persist events to PostgreSQL `orthodoxy_logs` table

**Schema**:
```sql
CREATE TABLE orthodoxy_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(255),
    service VARCHAR(100),
    payload JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_orthodoxy_logs_service ON orthodoxy_logs(service);
CREATE INDEX idx_orthodoxy_logs_timestamp ON orthodoxy_logs(timestamp);
CREATE INDEX idx_orthodoxy_logs_event_type ON orthodoxy_logs(event_type);
```

**Integration**:
```python
# core/roles.py
from core.governance.orthodoxy_wardens.chronicler_agent import SystemMonitor

chronicler_agent = SystemMonitor()

chronicler_agent.log_event(
    service="neural_engine",
    event_type="screening.completed",
    payload={"tickers": ["AAPL"], "composite_z": 1.85}
)
```

### 6.4 ComplianceValidator

**Location**: `vitruvyan_core/core/governance/orthodoxy_wardens/inquisitor_agent.py`

**Purpose**: Deep-dive compliance analysis using LLM + rules engine

**Validation Categories**:
1. **Data Quality**: Missing fields, outliers, inconsistencies
2. **Architectural Compliance**: Service boundaries, dependency violations
3. **Performance**: Latency, throughput, resource usage
4. **Security**: Authentication, authorization, data exposure

**Integration**:
```python
# core/roles.py
from core.governance.orthodoxy_wardens.inquisitor_agent import ComplianceValidator

inquisitor_agent = ComplianceValidator(llm_interface=llm_interface)

analysis = inquisitor_agent.analyze(
    scope="babel_gardens",
    evidence={"logs": [...], "metrics": {...}}
)
```

---

## 7. API Implementation

### 7.1 FastAPI App Structure

**Location**: `main.py` (lines 60-817)

**Key Sections**:
1. **Imports** (lines 1-60): Dependencies, Sacred Roles, event handlers
2. **Pydantic Models** (lines 188-210): Request/response schemas
3. **Startup Event** (lines 213-310): Initialize Sacred Roles + listeners
4. **Health Check** (lines 315-345): `/divine-health` endpoint
5. **Audit Endpoints** (lines 350-500): `/confession/initiate`, `/confession/status`

### 7.2 Health Check Endpoint

**Endpoint**: `GET /divine-health`

**Implementation** (lines 315-345):
```python
@app.get("/divine-health", response_model=DivineHealthResponse)
async def divine_health_check():
    """Sacred health check - Verify the divine council's spiritual status"""
    divine_council_status = {
        "confessor": "blessed" if confessor_agent else "absent_from_prayers",
        "penitent": "blessed" if penitent_agent else "absent_from_prayers",
        "chronicler": "blessed" if chronicler_agent else "absent_from_prayers",
        "inquisitor": "blessed" if inquisitor_agent else "absent_from_prayers",
        "abbot": "blessed" if abbot_agent else "absent_from_prayers",
        "sacred_interface": "blessed" if llm_interface else "silent",
        "orthodoxy_db": "blessed" if orthodoxy_db_manager else "corrupted",
        "sacred_guardrails": "blessed" if sacred_guardrails else "unprotected"
    }
    
    blessed_count = sum(1 for status in divine_council_status.values() if status == "blessed")
    total_count = len(divine_council_status)
    blessing_level = blessed_count / total_count
    
    if blessing_level >= 0.9:
        sacred_status = "blessed"
    elif blessing_level >= 0.7:
        sacred_status = "purifying"
    else:
        sacred_status = "cursed"
        
    return DivineHealthResponse(
        sacred_status=sacred_status,
        divine_council=divine_council_status,
        timestamp=datetime.now().isoformat(),
        blessing_level=blessing_level
    )
```

**Response Interpretation**:
- `blessed` (90%+): All critical components operational
- `purifying` (70-90%): Some non-critical components missing
- `cursed` (<70%): Major failures, service degraded

### 7.3 Audit Endpoints

**Endpoint**: `POST /confession/initiate`

**Request Schema**:
```python
class ConfessionRequest(BaseModel):
    confession_type: str = "system_compliance"
    sacred_scope: Optional[str] = "complete_realm"
    urgency: Optional[str] = "divine_routine"
    penitent_service: Optional[str] = None
```

**Implementation** (lines 350-400):
```python
@app.post("/confession/initiate")
async def initiate_confession(request: ConfessionRequest, background_tasks: BackgroundTasks):
    """🏛️ Initiate sacred confession ritual for system compliance"""
    
    if not confessor_agent:
        raise HTTPException(status_code=503, detail="Confessor is absent from sacred duties")
    
    try:
        # Generate sacred confession ID
        confession_id = f"confession_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Emit audit request event
        sacred_confessor.emit_event(
            "orthodoxy.audit.requested",
            "audit.initiated",
            {
                "confession_id": confession_id,
                "scope": request.sacred_scope,
                "urgency": request.urgency,
                "service": request.penitent_service
            }
        )
        
        return {
            "confession_id": confession_id,
            "sacred_status": "confessing",
            "assigned_warden": "Confessor",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"💀 Failed to initiate confession: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Design Decision**: Audit runs asynchronously via event emission. API returns immediately with `confession_id` for polling status.

---

## 8. Testing Strategy

### 8.1 Unit Tests (No Docker Required)

**Test Sacred Roles in isolation**:
```python
# tests/test_sacred_roles.py
from services.governance.api_orthodoxy_wardens.core.roles import OrthodoxConfessor
import pytest

def test_confessor_initialization():
    """Test Confessor can be instantiated"""
    confessor = OrthodoxConfessor()
    assert confessor is not None
    assert hasattr(confessor, 'confess')
    assert hasattr(confessor, 'validate')  # Functional alias

def test_confessor_event_emission(mock_redis):
    """Test Confessor emits events correctly"""
    confessor = OrthodoxConfessor()
    
    event_id = confessor.emit_event(
        "test.channel",
        "test.event_type",
        {"test_data": "value"}
    )
    
    assert event_id is not None
    assert len(event_id) > 0
```

### 8.2 Integration Tests (Docker Required)

**Test API endpoints**:
```python
# tests/test_api_integration.py
import requests
import pytest

@pytest.fixture
def base_url():
    return "http://localhost:9006"

def test_health_check(base_url):
    """Test /divine-health endpoint"""
    response = requests.get(f"{base_url}/divine-health")
    
    assert response.status_code == 200
    data = response.json()
    assert "sacred_status" in data
    assert "blessing_level" in data
    assert data["blessing_level"] >= 0.7  # At least purifying

def test_audit_initiation(base_url):
    """Test /confession/initiate endpoint"""
    response = requests.post(
        f"{base_url}/confession/initiate",
        json={
            "confession_type": "system_compliance",
            "sacred_scope": "neural_engine"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "confession_id" in data
    assert data["sacred_status"] == "confessing"
```

### 8.3 E2E Tests (Full Stack)

**Test event consumption**:
```bash
# Emit event → Verify consumption
curl -X POST http://localhost:9012/emit/orthodoxy.audit.requested \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "audit.test",
    "data": {"scope": "test_service"}
  }'

# Check logs
docker logs omni_api_orthodoxy_wardens --tail=50 | grep "Audit requested"

# Verify acknowledgment
docker exec omni_redis redis-cli XPENDING \
  "vitruvyan:stream:orthodoxy.audit.requested" \
  "group:orthodoxy_main"
# Expected: 0 pending (all acknowledged)
```

---

## 9. Deployment

### 9.1 Docker Build

```bash
cd /home/vitruvyan/vitruvyan-core/infrastructure/docker
docker compose build vitruvyan_api_orthodoxy_wardens
```

**Dockerfile**: `infrastructure/docker/dockerfiles/Dockerfile.orthodoxy_wardens`

**Key Steps**:
1. Base image: `python:3.11-slim`
2. Install dependencies from `requirements.orthodoxy_wardens.txt`
3. Copy service code to `/app/api_orthodoxy_wardens/`
4. Copy core modules to `/app/core/`
5. Set `PYTHONPATH=/app`
6. Expose port 8006
7. Run uvicorn

### 9.2 Container Start

```bash
docker compose up -d vitruvyan_api_orthodoxy_wardens
```

**Startup Sequence**:
1. Uvicorn starts FastAPI app
2. `sacred_initialization()` event fires
3. Sacred Roles instantiated
4. Event handlers injected
5. Consumer groups created (7 channels)
6. Background listener thread launched
7. Startup completes (`Application startup complete.`)

**Verification**:
```bash
docker logs omni_api_orthodoxy_wardens --tail=100 | grep -E "startup complete|Uvicorn running|listeners thread started"
```

Expected output:
```
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8006
INFO: 🔥 Synaptic Conclave listeners thread started (background processing active)
```

### 9.3 Health Monitoring

```bash
# Container status
docker ps | grep orthodoxy
# Expected: Up X minutes (healthy)

# API health
curl http://localhost:9006/divine-health | jq '.sacred_status'
# Expected: "blessed" or "purifying"

# Redis consumer groups
docker exec omni_redis redis-cli XINFO GROUPS "vitruvyan:stream:orthodoxy.audit.requested"
# Expected: group:orthodoxy_main present
```

---

## 10. Best Practices

### 10.1 Adding New Sacred Roles

**Steps**:
1. Create subclass of `SacredRole` in `core/roles.py`
2. Implement business logic methods
3. Add functional aliases
4. Update `core/__init__.py` exports
5. Inject in `main.py` startup event
6. Update documentation

**Example**:
```python
# core/roles.py
class OrthodoxGuardian(SacredRole):
    """
    Guardian - Monitors system boundaries and prevents external threats.
    Functional alias: monitor_boundaries(), protect()
    """
    def __init__(self):
        super().__init__()
        self.guardian_agent = BoundaryMonitor()
    
    def guard(self, threat: Dict) -> Dict:
        """Theological method - Guard sacred boundaries"""
        return self.monitor_boundaries(threat)
    
    def monitor_boundaries(self, threat: Dict) -> Dict:
        """Functional alias"""
        analysis = self.guardian_agent.analyze_threat(threat)
        
        if analysis["severity"] == "critical":
            self.emit_event("orthodoxy.threat.critical", "threat.detected", analysis)
        
        return analysis
```

### 10.2 Adding New Event Channels

**Steps**:
1. Add channel → handler mapping in `sacred_channels` dict (`main.py`, line 120)
2. Create handler function in `core/event_handlers.py` if needed
3. Restart container
4. Verify consumer group created

**Example**:
```python
# main.py
sacred_channels = {
    # ... existing channels ...
    "new_service.completion.event": handle_new_service_events
}

# core/event_handlers.py
async def handle_new_service_events(event: CognitiveEvent):
    """Handle events from new service"""
    try:
        logger.info(f"📝 New service event: {event.event_type}")
        
        # Custom processing logic
        result = process_new_service_data(event.payload)
        
        # Log to PostgreSQL
        sacred_chronicler.record({
            "event_type": event.event_type,
            "service": "new_service",
            "payload": result
        })
        
    except Exception as e:
        logger.error(f"❌ New service event handling failed: {e}")
```

### 10.3 Error Handling Patterns

**Log but don't crash**:
```python
try:
    risky_operation()
except Exception as e:
    logger.error(f"❌ Operation failed: {e}")
    # Don't raise - let other events continue processing
```

**Emit failure events for observability**:
```python
try:
    audit_result = perform_audit()
except Exception as e:
    logger.error(f"💀 Audit failed: {e}")
    
    # Emit failure event
    sacred_confessor.emit_event(
        "orthodoxy.audit.failed",
        "audit.error",
        {"error": str(e), "audit_id": audit_id}
    )
```

**Don't acknowledge on failure** (enables retry):
```python
for event in bus.consume(channel, group, consumer):
    try:
        await handler(event)
        bus.acknowledge(event.stream, group, event.event_id)  # ✅ Only on success
    except Exception as e:
        logger.error(f"❌ Processing failed: {e}")
        # Don't acknowledge - event remains pending for retry
```

### 10.4 Performance Optimization

**Batch PostgreSQL writes**:
```python
# ❌ Bad: N+1 queries
for event in events:
    postgres.log_event(event)

# ✅ Good: Batch insert
postgres.batch_insert_events(events)
```

**Cache Redis connections**:
```python
# ❌ Bad: New connection per operation
def emit_event():
    bus = StreamBus(...)  # Creates new connection
    bus.publish(...)

# ✅ Good: Reuse connection (base class pattern)
class SacredRole:
    def __init__(self):
        self.bus = StreamBus(...)  # Cached connection
```

**Async database operations**:
```python
# Use asyncpg for PostgreSQL (10x faster than psycopg2)
import asyncpg

pool = await asyncpg.create_pool(...)
async with pool.acquire() as conn:
    await conn.execute(query)
```

### 10.5 Security Considerations

**Input validation**:
```python
# Use Pydantic for automatic validation
class AuditRequest(BaseModel):
    scope: str = Field(..., max_length=100)
    urgency: str = Field(..., regex="^(low|medium|high|critical)$")
```

**Secret management**:
```bash
# Use environment variables, not hardcoded secrets
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}  # From .env or Kubernetes secrets
```

**Rate limiting** (TODO - not implemented yet):
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/confession/initiate")
@limiter.limit("10/minute")  # Max 10 audits per minute per IP
async def initiate_confession(...):
    ...
```

---

## Conclusion

Orthodoxy Wardens implements a **theological-functional hybrid architecture** that balances domain clarity (theological metaphors) with engineering pragmatism (event-driven, testable, scalable).

**Key Takeaways**:
1. Sacred Roles = Event-driven business logic wrappers
2. Event Handlers = Pure orchestration (no business logic)
3. Dependency Injection = Avoid circular imports
4. Background Thread = Non-blocking listener startup
5. Acknowledge-after-success = Automatic retry on failure

**Next Steps**:
- Read [API_REFERENCE.md](./API_REFERENCE.md) for complete endpoint docs
- Read [ARCHITECTURAL_DECISIONS.md](./ARCHITECTURAL_DECISIONS.md) for design rationale
- Explore agent implementations in `vitruvyan_core/core/governance/orthodoxy_wardens/`

**Questions?** Open an issue or contact the Vitruvyan Core Team.

---

**Last Updated**: February 8, 2026  
**Document Version**: 1.0.0  
**Author**: Vitruvyan Core Team
