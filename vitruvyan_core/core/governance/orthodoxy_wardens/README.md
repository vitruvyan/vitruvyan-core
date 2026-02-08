# Orthodoxy Wardens - System Governance & Audit

**Purpose**: Automated compliance monitoring, system health validation, and autonomous error correction for the Vitruvyan platform.

**Architecture**: Event-driven audit system using Redis Streams (Synaptic Conclave) with 5 specialized agents that work together to maintain system integrity.

---

## 🧩 Core Agents

### 1. AutonomousAuditAgent (`confessor_agent.py`)

**What it does**: Orchestrates full system audits by coordinating all other agents. Analyzes code changes, validates compliance, and decides whether issues require manual review or can be auto-corrected.

**How it works**: Uses LangGraph workflow to execute a 9-step audit pipeline:
1. Trigger Analysis → 2. Code Analysis → 3. System Monitoring → 4. Compliance Check → 
5. Decision Engine → 6. Auto-Correction → 7. System Healing → 8. Notifications → 9. Learning

**When to use**: 
- After code commits (Git hooks trigger)
- Scheduled system health checks (every 10 minutes)
- Manual audit requests via API (`POST /confess`)

**Output**: AuditState with compliance_score (0-1), healing_actions, auto_corrections, and learning_insights.

**Dependencies**: Requires all other agents (SystemMonitor, ComplianceValidator, AutoCorrector).

---

### 2. SystemMonitor (`chronicler_agent.py`)

**What it does**: Collects real-time system health metrics (CPU, memory, disk, network, processes) and detects anomalies.

**How it works**: Uses `psutil` library to query OS-level metrics every 60 seconds. Compares current values against historical baselines to flag degradations (>80% resource usage = warning, >95% = critical).

**When to use**:
- Continuous background monitoring (always running)
- On-demand health checks via API (`GET /divine-health`)
- Before/after risky operations (deployments, database migrations)

**Output**: Health metrics dict with CPU%, memory%, disk%, process counts, and anomaly flags.

**Integration**: Called by AutonomousAuditAgent's `monitor_system_health()` node.

---

### 3. ComplianceValidator (`inquisitor_agent.py`)

**What it does**: Scans system outputs (API responses, logs, database entries) for regulatory violations using pattern matching + LLM-based semantic analysis.

**How it works**: 
1. **Pattern-based scan**: Regex rules detect prescriptive language ("buy now", "guaranteed profit")
2. **LLM semantic check**: GPT-4o-mini analyzes context to catch nuanced violations
3. **Risk scoring**: Each violation assigned severity (critical/high/medium/low)

**When to use**:
- Before serving responses to users (real-time validation)
- After VEE narrative generation (ensures compliance)
- Batch validation of stored analysis results

**Output**: Compliance report with violations list, severity scores, and suggested corrections.

**Integration**: Called by AutonomousAuditAgent's `validate_compliance()` node.

---

### 4. AutoCorrector (`penitent_agent.py`)

**What it does**: Applies automated fixes for detected issues without human intervention. Handles service restarts, disk cleanup, compliance text rewrites, and configuration updates.

**How it works**: 
1. **Immediate fixes** (auto_execute=True): Container restarts, disk space cleanup, compliance rewrites
2. **Scheduled fixes** (auto_execute=False): Database optimizations, major config changes (logged for review)
3. **Rollback support**: All corrections logged with before/after snapshots for undo

**When to use**:
- After AutonomousAuditAgent identifies fixable issues
- Triggered by system health alerts (disk >90%, memory leaks)
- Manual correction requests via API (`POST /confess` with auto_correction=true)

**Output**: Correction report with applied_fixes, rollback_instructions, and success/failure status.

**Integration**: Called by AutonomousAuditAgent's `execute_auto_corrections()` node.

---

### 5. Sacred Roles (Theological Wrappers)

**Purpose**: Provide event-driven interfaces for the agents above. These are FastAPI + Synaptic Conclave (Redis Streams) wrappers that emit/consume events.

**Classes** (defined in `services/governance/api_orthodoxy_wardens/main.py`):
- **OrthodoxConfessor**: Emits audit requests → calls AutonomousAuditAgent
- **OrthodoxPenitent**: Emits correction requests → calls AutoCorrector  
- **OrthodoxChronicler**: Logs events to PostgreSQL → calls SystemMonitor
- **OrthodoxInquisitor**: Emits investigation requests → calls ComplianceValidator
- **OrthodoxAbbot**: Emits final verdicts (audit approved/rejected)

**Why they exist**: Decouple business logic (agents) from infrastructure (FastAPI/Redis). Agents can be tested in isolation.

**Functional aliases**: Each role has pragmatic method names:
- `hear_confession()` = `validate()`
- `apply_purification()` = `remediate()`
- `record_sacred_event()` = `log_event()`

---

## 🔄 Event Flow Example

**Scenario**: Neural Engine completes stock screening

```
1. Neural Engine → Redis Streams → "neural_engine.screening.completed"
2. Orthodoxy Wardens Listener → receives event
3. OrthodoxInquisitor.trigger_investigation() → calls ComplianceValidator
4. ComplianceValidator → scans for violations (e.g., "AAPL will definitely rise")
5. If violations found → OrthodoxConfessor.hear_confession() → calls AutonomousAuditAgent
6. AutonomousAuditAgent → decides: auto-correct or escalate?
7. If auto-correct → OrthodoxPenitent.apply_purification() → calls AutoCorrector
8. AutoCorrector → rewrites text: "AAPL will definitely rise" → "AAPL shows upward momentum"
9. OrthodoxChronicler.record_sacred_event() → logs to PostgreSQL
10. OrthodoxAbbot.grant_absolution() → emits "orthodoxy.audit.completed"
```

---

## 📡 API Endpoints

**Main Service** (port 8006):
- `GET /divine-health` - System health check (all agents status)
- `POST /confess` - Trigger full audit workflow
- `POST /conclave/audit-request` - Event-driven audit (via Synaptic Conclave)
- `GET /sacred-records/recent` - Recent audit logs from database

**Synaptic Conclave Channels** (Redis Streams):
- **Consumes**: `orthodoxy.audit.requested`, `neural_engine.screening.completed`, `babel.sentiment.completed`, etc.
- **Emits**: `orthodoxy.audit.completed`, `orthodoxy.purification.executed`, `orthodoxy.heresy.detected`

---

## 🧪 Testing

**Unit tests**:
```bash
pytest tests/unit/test_orthodoxy_wardens.py -v
```

**Integration test** (requires Redis + PostgreSQL):
```python
from core.governance.orthodoxy_wardens.confessor_agent import AutonomousAuditAgent

agent = AutonomousAuditAgent(config={
    "llm_interface": llm,
    "db_manager": db
})

# Trigger audit
result = await agent.audit_workflow.ainvoke({
    "audit_id": "test-001",
    "trigger_type": "manual"
})

assert result["compliance_score"] > 0.8
```

---

## 🚀 Quick Start

**1. Import the agent you need**:
```python
from core.governance.orthodoxy_wardens.inquisitor_agent import ComplianceValidator

validator = ComplianceValidator(llm_interface=llm)
report = await validator.validate_output(text="Check this for violations", output_type="vee_narrative")
```

**2. Or use the orchestrator**:
```python
from core.governance.orthodoxy_wardens.confessor_agent import AutonomousAuditAgent

agent = AutonomousAuditAgent(config={...})
audit_result = await agent.audit_workflow.ainvoke({
    "audit_id": "audit-123",
    "trigger_type": "code_commit"
})
```

**3. Or trigger via API**:
```bash
curl -X POST http://localhost:8006/confess \
  -H "Content-Type: application/json" \
  -d '{"confession_type": "system_compliance", "urgency": "divine_routine"}'
```

---

## 📋 Configuration

**Environment Variables**:
```bash
# Monitoring intervals
ORTHODOXY_MONITORING_INTERVAL=300  # seconds

# Auto-correction settings
DIVINE_AUTO_CORRECTION_ENABLED=true
SACRED_COMPLIANCE_THRESHOLD=0.8  # min score for auto-approval

# Database
POSTGRES_HOST=omni_postgres
POSTGRES_PORT=5432

# Redis Streams
REDIS_HOST=omni_redis
REDIS_PORT=6379
```

---

## 🔧 Utility Modules

- **`code_analyzer.py`**: Static code analysis for security/style violations
- **`docker_manager.py`**: Docker container management (status, restart, metrics)
- **`git_monitor.py`**: Git history analysis for audit trigger detection
- **`schema_validator.py`**: Data schema validation (events, database schemas)

---

## 📚 Further Reading

- **LangGraph Workflow**: See `confessor_agent.py` lines 70-120 for full workflow definition
- **Compliance Rules**: See `inquisitor_agent.py` lines 20-60 for pattern definitions  
- **Correction Strategies**: See `penitent_agent.py` lines 24-58 for fix types
- **Event Handlers**: See `services/governance/api_orthodoxy_wardens/main.py` lines 374-430

---

**Last Updated**: Feb 8, 2026  
**Maintainer**: Vitruvyan Core Team  
**Status**: ✅ Production Ready (P1 FASE 1 Complete)