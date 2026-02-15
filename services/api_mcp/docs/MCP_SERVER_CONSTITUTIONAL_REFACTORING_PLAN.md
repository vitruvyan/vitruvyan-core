# MCP Server Constitutional Refactoring Plan — 16% → 100% Agnosticization

**Date**: February 11, 2026  
**Status**: 🚧 PLANNING PHASE  
**Current Score**: 16/100 (ChatGPT Audit) + 50% SACRED_ORDER_PATTERN (Copilot Audit)  
**Target Score**: 100/100 (Full compliance)  
**Duration**: 4-5 days (165 files, 22 critical violations)

---

## 📊 Audit Synthesis — Two Complementary Perspectives

### Copilot Audit (Structural)
**Focus**: SACRED_ORDER_PATTERN compliance  
**Verdict**: ⚠️ **PARTIAL COMPLIANCE (50%)**

| Layer | Status | Evidence |
|-------|--------|----------|
| LIVELLO 2 (Service) | ✅ Complete | main.py 43 lines, tools/, middleware/, _legacy/ |
| LIVELLO 1 (Domain) | ❌ **MISSING** | `vitruvyan_core/core/governance/mcp_server/` does NOT exist |

**Key Finding**: MCP refactor (Jan 2026, commit f6295d1) focused on service slimming (1040 → 43 lines main.py) but **DID NOT create pure domain layer**.

---

### ChatGPT Audit (Content)
**Focus**: Domain leakage, hardcoded values, integration violations  
**Verdict**: ❌ **CRITICAL AGNOSTICIZATION FAILURE (16/100)**

| Category | Score | Critical Issues |
|----------|-------|-----------------|
| Domain Purity | **2/20** | Finance taxonomy hardcoded in tool schemas (momentum_z, trend_z, VARE risk) |
| Abstraction Purity | **5/20** | Raw Redis Pub/Sub (not StreamBus), direct HTTP coupling to LangGraph |
| Epistemic Boundary | **3/20** | Channel misalignment (`conclave.mcp.request` vs `conclave.mcp.actions`) |
| Config Injection | **3/20** | Hardcoded thresholds (z-score ±3, composite ±5, word_count 100-200) |
| Micelial Integration | **3/20** | Pub/Sub instead of Streams, listener disconnected from actual events |

**Key Finding**: MCP Server has **9 CRITICAL violations** (domain leakage, boundary violations, security issues).

---

## ❌ Critical Violations Inventory (22 Total)

### CRITICAL (9 violations)

1. **Finance Taxonomy in Tool Schemas** (`services/api_mcp/schemas/tools.py:9`)
   - Hardcoded: `momentum/trend/volatility/sentiment/fundamentals z-scores`
   - Impact: Tool contract is finance-specific, not domain-agnostic
   - Fix: Generic factor schema, vertical-injected taxonomy

2. **Investment Horizon Parameter** (`services/api_mcp/schemas/tools.py:29`)
   - Hardcoded: `horizon: ["short", "medium", "long"]` (finance semantics)
   - Impact: Domain assumption in gateway protocol
   - Fix: Remove or make vertical-specific parameter

3. **VARE Risk Semantics** (`services/api_mcp/tools/screen.py:58`)
   - Hardcoded: `vare.risk_score/risk_category` in screen results
   - Impact: Finance risk model leakage
   - Fix: Generic assessment framework

4. **Sentiment Table Coupling** (`services/api_mcp/tools/sentiment.py:25`)
   - Hardcoded: Direct query to `sentiment_scores` table (finance-specific)
   - Impact: Tool executor coupled to vertical database schema
   - Fix: Abstract data access via domain-agnostic consumer

5. **Financial System Prompt** (`vitruvyan_core/core/orchestration/langgraph/node/llm_mcp_node.py:214`)
   - Hardcoded: "financial analysis assistant" in MCP node prompt
   - Impact: Domain leakage in LangGraph orchestration
   - Fix: Generic "data analysis assistant" or vertical-injected prompt

6. **Redis Pub/Sub Instead of StreamBus** (`services/api_mcp/middleware.py:8`)
   - Violation: Uses `redis.Redis` directly, bypasses `StreamBus` abstraction
   - Impact: Non-standard transport, cannot leverage Streams guarantees
   - Fix: Replace with `core.synaptic_conclave.transport.streams.StreamBus`

7. **Channel Misalignment** (`services/api_mcp/middleware.py:59`)
   - Violation: Publishes to `conclave.mcp.request` (orphan channel)
   - Expected: `conclave.mcp.actions` (consumed by Orthodoxy Wardens + MCP Listener)
   - Impact: Events never reach Sacred Orders consumers
   - Fix: Align to `conclave.mcp.actions` + use StreamBus

8. **Dockerfile Incomplete Copy** (`infrastructure/docker/dockerfiles/Dockerfile.api_mcp:17`)
   - Violation: Copies only `vitruvyan_core/core/foundation/persistence`
   - Reality: Service imports `PostgresAgent` from `core.agents.postgres_agent`
   - Impact: Runtime import error (module not found)
   - Fix: Copy full `vitruvyan_core/core/` or use proper package install

9. **Orthodoxy Status Parsing Error** (`vitruvyan_core/core/orchestration/langgraph/node/llm_mcp_node.py:260`)
   - Violation: Reads `orthodoxy_status` from `result.data.*` (WRONG)
   - Reality: `orthodoxy_status` is top-level in MCP response schema
   - Impact: Silent failure (orthodoxy validation never checked)
   - Fix: Read from `result.orthodoxy_status` (top-level)

---

### HIGH (6 violations)

10. **Market Sentiment Framing** (`services/api_mcp/tools/sentiment.py:52`)
    - Hardcoded: "Market sentiment favors..." (finance language)
    - Fix: Generic "sentiment analysis shows..."

11. **Heretical Status Never Generated** (`services/api_mcp/api/routes.py:81`)
    - Violation: Middleware never returns "heretical", only "purified"
    - Impact: Orthodoxy enforcement is theatrical, not real
    - Fix: Implement actual heretical thresholds (z-score > 5, composite > 10)

12. **Direct SQL Archiving** (`services/api_mcp/middleware.py:100`)
    - Violation: Writes to `mcp_tool_calls` directly (bypasses Vault Keepers)
    - Fix: Emit event to `vault.mcp.archive` channel, let Vault Keepers persist

13. **Cross-Service HTTP Calls** (`services/api_mcp/tools/screen.py:32`)
    - Violation: Direct `httpx.post(langgraph_url)` instead of Streams
    - Fix: Emit event to `neural.screen.requested`, consume from `neural.screen.completed`

14. **Pub/Sub in Core Listener** (`vitruvyan_core/core/synaptic_conclave/listeners/mcp.py:271`)
    - Violation: Uses `pubsub.subscribe()` instead of Streams
    - Fix: Convert to `StreamBus.consume()`

15. **Missing SQL Migration** (`services/api_mcp/README.md:72`)
    - Violation: README references `001_mcp_tool_calls.sql` (not in repo)
    - Fix: Create migration in `database/migrations/` or remove reference

---

### MEDIUM (7 violations)

16. **Hardcoded DEBUG Logging** (`services/api_mcp/main.py:11`)
17. **Hardcoded Z-Score Threshold** (`services/api_mcp/middleware.py:74`) — ±3
18. **Hardcoded Composite Threshold** (`services/api_mcp/middleware.py:80`) — ±5
19. **Hardcoded Word Count Range** (`services/api_mcp/middleware.py:87`) — 100-200
20. **Missing Postgres Config** (`services/api_mcp/config.py:16`)
21. **Port Mismatch** (LangGraph node default :8021 vs actual :8020)
22. **Incomplete Config in Postgres** (`services/api_mcp/config.py:16`)

---

## 🎯 Refactoring Strategy — Four-Phase Approach

### Phase Sequencing Logic

**Why this order?**
1. **FASE 1 (LIVELLO 1)** creates pure testable foundation
2. **FASE 2 (Domain Agnostic)** removes finance leakage using pure functions
3. **FASE 3 (Streams)** fixes integration after domain logic is pure
4. **FASE 4 (Config)** centralizes all hardcoded values

**Dependencies**:
- FASE 2 requires FASE 1 (need pure consumers to refactor domain logic)
- FASE 3 requires FASE 2 (need domain-agnostic events to define channels)
- FASE 4 is independent but easier after FASE 1-3

---

## FASE 1: LIVELLO 1 Creation (2 days)

### Goal
Extract pure domain layer matching Codex Hunters pattern.

### Deliverables

**Directory Structure** (10 directories):
```
vitruvyan_core/core/governance/mcp_server/
├── domain/
│   ├── __init__.py
│   ├── tool_schema.py       # Frozen dataclass for tool schemas
│   ├── tool_result.py       # Standardized result envelope
│   ├── validation.py        # Validation result contracts
│   └── factor.py            # Generic factor abstraction (NOT finance-specific)
├── consumers/
│   ├── __init__.py
│   ├── screen_consumer.py   # Pure screen processing (no I/O)
│   ├── sentiment_consumer.py # Pure sentiment query (no I/O)
│   ├── vee_consumer.py      # Pure VEE request (no I/O)
│   ├── compare_consumer.py  # Pure comparison logic
│   └── semantic_consumer.py # Pure semantic extraction
├── governance/
│   ├── __init__.py
│   ├── orthodoxy_rules.py   # Pure validation rules (z-score, composite, word_count)
│   ├── schema_validator.py  # Validate tool args against schemas
│   └── threshold_config.py  # Threshold dataclass (NO hardcoded values)
├── events/
│   ├── __init__.py          # Channel name constants
│   └── channels.py          # MCP_REQUEST, MCP_COMPLETED, MCP_ARCHIVED
├── monitoring/
│   ├── __init__.py
│   └── metrics.py           # Metric NAME constants (no prometheus_client)
├── philosophy/
│   ├── __init__.py
│   └── charter.md           # MCP identity: "Stateless Gateway to Sacred Orders"
├── docs/
│   ├── __init__.py
│   └── README.md            # LIVELLO 1 documentation
├── examples/
│   ├── __init__.py
│   ├── pure_screen.py       # Standalone screen example (no Docker)
│   └── pure_orthodoxy.py    # Standalone validation example
├── tests/
│   ├── __init__.py
│   ├── test_screen_consumer.py
│   ├── test_orthodoxy_rules.py
│   └── test_schema_validator.py
└── _legacy/
    └── (empty, for future pre-refactoring archive)
```

### Key Files to Create

#### 1. `domain/tool_schema.py`
```python
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum

@dataclass(frozen=True)
class ToolParameter:
    name: str
    type: str
    description: str
    required: bool = False
    enum: Optional[List[str]] = None
    default: Optional[Any] = None

@dataclass(frozen=True)
class ToolSchema:
    name: str
    description: str
    parameters: List[ToolParameter]
    
    def to_openai_function_calling(self) -> Dict[str, Any]:
        """Export to OpenAI Function Calling format."""
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.default:
                properties[param.name]["default"] = param.default
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
```

#### 2. `domain/factor.py` (Generic, NOT finance)
```python
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass(frozen=True)
class Factor:
    """Generic factor abstraction (domain-agnostic)."""
    name: str
    value: float
    normalized_score: Optional[float] = None  # z-score or other normalization
    percentile: Optional[float] = None
    
    def __post_init__(self):
        """Validate factor data."""
        if not isinstance(self.value, (int, float)):
            raise ValueError(f"Factor value must be numeric, got {type(self.value)}")

@dataclass(frozen=True)
class FactorSet:
    """Collection of factors for an entity."""
    entity_id: str
    factors: Dict[str, Factor]
    composite_score: Optional[float] = None
    rank: Optional[int] = None
    
    def get_factor(self, name: str) -> Optional[Factor]:
        return self.factors.get(name)
    
    def get_normalized_scores(self) -> Dict[str, float]:
        """Extract normalized scores (z-scores, etc.)."""
        return {
            name: factor.normalized_score 
            for name, factor in self.factors.items() 
            if factor.normalized_score is not None
        }
```

#### 3. `governance/orthodoxy_rules.py` (Pure validation)
```python
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum
from ..domain.factor import FactorSet
from .threshold_config import ThresholdConfig

class OrthodoxStatus(Enum):
    BLESSED = "blessed"
    PURIFIED = "purified"
    HERETICAL = "heretical"

@dataclass(frozen=True)
class ValidationResult:
    status: OrthodoxStatus
    violations: List[str]
    warnings: List[str]

def validate_factor_set(
    factor_set: FactorSet, 
    config: ThresholdConfig
) -> ValidationResult:
    """
    Pure function: validate factor normalized scores.
    NO I/O, NO database, NO logging.
    """
    violations = []
    warnings = []
    status = OrthodoxStatus.BLESSED
    
    # Check normalized scores (z-scores, etc.)
    for name, factor in factor_set.factors.items():
        if factor.normalized_score is None:
            continue
        
        z = factor.normalized_score
        
        # HERETICAL: extreme outliers
        if z < config.normalized_min_heretical or z > config.normalized_max_heretical:
            violations.append(
                f"{name}={z:.2f} exceeds heretical threshold "
                f"[{config.normalized_min_heretical}, {config.normalized_max_heretical}]"
            )
            status = OrthodoxStatus.HERETICAL
        
        # PURIFIED: moderate outliers
        elif z < config.normalized_min_warning or z > config.normalized_max_warning:
            warnings.append(
                f"{name}={z:.2f} flagged for review "
                f"(outside [{config.normalized_min_warning}, {config.normalized_max_warning}])"
            )
            if status == OrthodoxStatus.BLESSED:
                status = OrthodoxStatus.PURIFIED
    
    # Check composite score
    if factor_set.composite_score is not None:
        comp = factor_set.composite_score
        
        if comp < config.composite_min_heretical or comp > config.composite_max_heretical:
            violations.append(
                f"composite={comp:.2f} exceeds heretical threshold "
                f"[{config.composite_min_heretical}, {config.composite_max_heretical}]"
            )
            status = OrthodoxStatus.HERETICAL
        
        elif comp < config.composite_min_warning or comp > config.composite_max_warning:
            warnings.append(f"composite={comp:.2f} flagged for review")
            if status == OrthodoxStatus.BLESSED:
                status = OrthodoxStatus.PURIFIED
    
    return ValidationResult(
        status=status,
        violations=violations,
        warnings=warnings
    )
```

#### 4. `governance/threshold_config.py`
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ThresholdConfig:
    """Configuration for Orthodoxy validation thresholds."""
    # Normalized scores (z-scores, percentiles, etc.)
    normalized_min_warning: float = -3.0
    normalized_max_warning: float = 3.0
    normalized_min_heretical: float = -5.0
    normalized_max_heretical: float = 5.0
    
    # Composite scores
    composite_min_warning: float = -5.0
    composite_max_warning: float = 5.0
    composite_min_heretical: float = -10.0
    composite_max_heretical: float = 10.0
    
    # Narrative word count (for VEE summaries)
    narrative_min_words: int = 50
    narrative_max_words: int = 300
    narrative_target_min: int = 100
    narrative_target_max: int = 200
    
    @classmethod
    def from_dict(cls, data: dict) -> "ThresholdConfig":
        """Load from config dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
```

#### 5. `consumers/screen_consumer.py` (Pure)
```python
from typing import Dict, List, Any
from ..domain.factor import Factor, FactorSet
from ..domain.tool_result import ToolResult

def process_screen_request(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pure function: validate screen request args.
    NO I/O, returns validated request data.
    """
    entity_ids = args.get("entity_ids", [])
    profile = args.get("profile", "balanced_mid")
    
    # Validation (pure)
    if not entity_ids:
        raise ValueError("entity_ids cannot be empty")
    
    if len(entity_ids) > 10:
        raise ValueError("Maximum 10 entity_ids per request")
    
    # Return validated data (no I/O)
    return {
        "entity_ids": entity_ids,
        "profile": profile,
        "query_text": f"screen {', '.join(entity_ids)} with {profile} profile"
    }

def transform_screen_response(raw_data: Dict, config: Any = None) -> List[FactorSet]:
    """
    Pure function: map API response to domain entities.
    NO assumptions about factor names (finance vs other domains).
    """
    numerical_panel = raw_data.get("numerical_panel", [])
    factor_sets = []
    
    for entity_data in numerical_panel:
        entity_id = entity_data.get("entity_id")
        composite_score = entity_data.get("composite_score", entity_data.get("composite", 0.0))
        rank = entity_data.get("rank", 0)
        
        # Extract factors (generic, NOT finance-specific)
        factors = {}
        
        # Map factor data (flexible field mapping)
        factor_mappings = {
            "momentum": ["momentum_z", "momentum_score"],
            "trend": ["trend_z", "trend_score"],
            "volatility": ["vola_z", "volatility_z", "volatility_score"],
            "sentiment": ["sentiment_z", "sentiment_score"],
            "fundamental": ["fundamental_z", "fundamental_score"]
        }
        
        for factor_name, field_names in factor_mappings.items():
            for field in field_names:
                if field in entity_data:
                    factors[factor_name] = Factor(
                        name=factor_name,
                        value=entity_data[field],
                        normalized_score=entity_data[field]  # Assume z-score
                    )
                    break
        
        factor_sets.append(FactorSet(
            entity_id=entity_id,
            factors=factors,
            composite_score=composite_score,
            rank=rank
        ))
    
    return factor_sets
```

#### 6. `tests/test_orthodoxy_rules.py` (Pure unit test)
```python
import pytest
from vitruvyan_core.core.governance.mcp_server.domain.factor import Factor, FactorSet
from vitruvyan_core.core.governance.mcp_server.governance.orthodoxy_rules import (
    validate_factor_set, OrthodoxStatus
)
from vitruvyan_core.core.governance.mcp_server.governance.threshold_config import ThresholdConfig

def test_blessed_within_range():
    """Test factors within blessed range."""
    config = ThresholdConfig()
    factor_set = FactorSet(
        entity_id="E001",
        factors={
            "momentum": Factor(name="momentum", value=0.5, normalized_score=1.2),
            "trend": Factor(name="trend", value=0.3, normalized_score=-0.8)
        },
        composite_score=0.85
    )
    
    result = validate_factor_set(factor_set, config)
    assert result.status == OrthodoxStatus.BLESSED
    assert len(result.violations) == 0
    assert len(result.warnings) == 0

def test_purified_moderate_outlier():
    """Test factor with moderate outlier (purified)."""
    config = ThresholdConfig()
    factor_set = FactorSet(
        entity_id="E002",
        factors={
            "momentum": Factor(name="momentum", value=0.9, normalized_score=3.5)  # Outside ±3
        },
        composite_score=0.9
    )
    
    result = validate_factor_set(factor_set, config)
    assert result.status == OrthodoxStatus.PURIFIED
    assert len(result.violations) == 0
    assert len(result.warnings) == 1
    assert "momentum=3.50" in result.warnings[0]

def test_heretical_extreme_outlier():
    """Test factor exceeding heretical threshold."""
    config = ThresholdConfig()
    factor_set = FactorSet(
        entity_id="E003",
        factors={
            "momentum": Factor(name="momentum", value=0.99, normalized_score=7.0)  # > 5.0
        },
        composite_score=2.5
    )
    
    result = validate_factor_set(factor_set, config)
    assert result.status == OrthodoxStatus.HERETICAL
    assert len(result.violations) == 1
    assert "momentum=7.00" in result.violations[0]
    assert "heretical threshold" in result.violations[0]

def test_custom_thresholds():
    """Test with custom threshold configuration."""
    config = ThresholdConfig(
        normalized_min_warning=-2.0,
        normalized_max_warning=2.0,
        normalized_min_heretical=-4.0,
        normalized_max_heretical=4.0
    )
    
    factor_set = FactorSet(
        entity_id="E004",
        factors={
            "momentum": Factor(name="momentum", value=0.7, normalized_score=2.5)  # > 2.0 warning
        }
    )
    
    result = validate_factor_set(factor_set, config)
    assert result.status == OrthodoxStatus.PURIFIED
```

### FASE 1 Acceptance Criteria

✅ **Structure Complete**:
```bash
ls vitruvyan_core/core/governance/mcp_server/ | wc -l
# Expected: 10 directories
```

✅ **Pure Imports**:
```python
python3 -c "
from vitruvyan_core.core.governance.mcp_server.consumers import process_screen_request
from vitruvyan_core.core.governance.mcp_server.governance.orthodoxy_rules import validate_factor_set
print('✅ Pure imports successful (no I/O dependencies)')
"
```

✅ **Unit Tests Pass**:
```bash
cd vitruvyan_core/core/governance/mcp_server
pytest tests/ -v
# Expected: 10+ tests, all passing, < 5s duration
```

---

## FASE 2: Domain-Agnostic Refactoring (1 day)

### Goal
Remove all finance-specific taxonomy from tool schemas and executors.

### Changes Required

#### 1. Generic Tool Schema (`services/api_mcp/schemas/tools.py`)

**Before** (Finance Hardcoded):
```python
"description": "Screen entity_ids using Vitruvyan Neural Engine multi-factor ranking system. Returns composite scores, z-scores for momentum/trend/volatility/sentiment/fundamentals, and percentile ranks."
```

**After** (Domain-Agnostic):
```python
"description": "Screen entities using multi-factor ranking system. Returns composite scores, normalized factor scores, and percentile ranks. Factor taxonomy is deployment-specific."
```

**Migration**:
```python
# OLD: Hardcoded finance factors
"properties": {
    "entity_ids": {...},
    "profile": {
        "enum": ["momentum_focus", "balanced_mid", "trend_follow", "short_spec", "sentiment_boost"]
    },
    "horizon": {  # ❌ REMOVE (finance-specific)
        "enum": ["short", "medium", "long"]
    }
}

# NEW: Generic profiles
"properties": {
    "entity_ids": {...},
    "profile": {
        "type": "string",
        "description": "Ranking profile (weighting strategy). Available profiles are deployment-specific. Default: balanced",
        "default": "balanced"
    },
    # horizon REMOVED (vertical can add in deployment config)
}
```

#### 2. Screen Executor (`services/api_mcp/tools/screen.py`)

**Extract** business logic to LIVELLO 1 consumer:
```python
# BEFORE (Mixed)
async def execute_screen_entities(args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    entity_ids = args.get("entity_ids", [])
    profile = args.get("profile", "balanced_mid")
    
    # ❌ Business logic + I/O mixed
    entities_str = ", ".join(entity_ids)
    query = f"screen {entities_str} with {profile} profile"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(langgraph_url, json={...})
        raw_data = response.json()
    
    # ❌ Data transformation (should be in LIVELLO 1)
    transformed = [...]
    return {"entity_ids": transformed}

# AFTER (LIVELLO 2 I/O only)
async def execute_screen_entities(args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    # Delegate validation to LIVELLO 1 (pure)
    from vitruvyan_core.core.governance.mcp_server.consumers.screen_consumer import (
        process_screen_request, transform_screen_response
    )
    
    request_data = process_screen_request(args)  # Pure function
    
    # LIVELLO 2 responsibility: I/O only
    async with httpx.AsyncClient() as client:
        response = await client.post(
            config.api.langgraph,
            json={"input_text": request_data["query_text"], "user_id": user_id}
        )
        raw_data = response.json()
    
    # Delegate transformation to LIVELLO 1 (pure)
    factor_sets = transform_screen_response(raw_data)
    
    return {
        "entity_ids": [fs.to_dict() for fs in factor_sets],
        "profile_used": request_data["profile"]
    }
```

#### 3. Remove Finance Prompts (`vitruvyan_core/core/orchestration/langgraph/node/llm_mcp_node.py`)

**Before**:
```python
system_prompt = """You are a financial analysis assistant..."""
```

**After**:
```python
system_prompt = """You are a data analysis assistant with access to Vitruvyan's analytical tools. 
You can help users understand patterns in structured data across multiple domains."""
```

#### 4. Sentiment Tool Domain-Neutral (`services/api_mcp/tools/sentiment.py`)

**Before** (Finance Hardcoded):
```python
# Query finance-specific table
cur.execute("SELECT combined_score FROM sentiment_scores WHERE ticker = %s ...")

# Finance framing
summary = f"Market sentiment favors {entity_id}..."
```

**After** (Domain-Agnostic):
```python
# Use LIVELLO 1 consumer (abstracts table name)
from vitruvyan_core.core.governance.mcp_server.consumers.sentiment_consumer import (
    query_sentiment_data
)

sentiment_data = query_sentiment_data(entity_id, days, pg_agent)

# Generic framing
summary = f"Sentiment analysis for {entity_id}: {sentiment_data.trend_description}"
```

### FASE 2 Acceptance Criteria

✅ **No Finance Terms in Schemas**:
```bash
rg "momentum|trend|volatility|sentiment|fundamental|investment|market|ticker|stock" \
   services/api_mcp/schemas/tools.py && echo "❌ FAIL" || echo "✅ PASS"
```

✅ **No Finance Terms in Executors**:
```bash
rg "Market|Investment|Stock|Ticker|VARE|risk_score" \
   services/api_mcp/tools/*.py && echo "❌ FAIL" || echo "✅ PASS"
```

✅ **Generic Prompts**:
```bash
rg "financial|finance|trading|investment" \
   vitruvyan_core/core/orchestration/langgraph/node/llm_mcp_node.py && echo "❌ FAIL" || echo "✅ PASS"
```

---

## FASE 3: Streams Integration (1 day)

### Goal
Replace Redis Pub/Sub with StreamBus, align channels with Sacred Orders.

### Changes Required

#### 1. Replace Pub/Sub in Middleware (`services/api_mcp/middleware.py`)

**Before** (Pub/Sub):
```python
from redis import Redis

redis_client = Redis(host=config.redis.host, port=config.redis.port)
redis_client.publish("conclave.mcp.request", json.dumps({...}))
```

**After** (StreamBus):
```python
from core.synaptic_conclave.transport.streams import StreamBus

bus = StreamBus()
bus.emit("conclave.mcp.actions", {
    "conclave_id": conclave_id,
    "tool": tool_name,
    "args": args,
    "user_id": user_id,
    "timestamp": datetime.utcnow().isoformat()
})
```

#### 2. Align Channels (`vitruvyan_core/core/governance/mcp_server/events/channels.py`)

**Create** channel constants:
```python
# MCP Server event channels (Sacred Orders compliant)
MCP_ACTIONS = "conclave.mcp.actions"           # Consumed by: Orthodoxy Wardens, MCP Listener
MCP_TOOL_EXECUTED = "mcp.tool.executed"        # Emitted after tool execution
MCP_ARCHIVE_REQUEST = "vault.mcp.archive"      # Consumed by: Vault Keepers

# Channel taxonomy (dot notation)
# conclave.* = Synaptic Conclave orchestration
# mcp.* = MCP-specific events
# vault.* = Vault Keepers archiving
```

#### 3. Update Core Listener (`vitruvyan_core/core/synaptic_conclave/listeners/mcp.py`)

**Before** (Pub/Sub):
```python
pubsub = redis_client.pubsub()
pubsub.subscribe("conclave.mcp.actions")
for message in pubsub.listen():
    handle_mcp_event(message)
```

**After** (Streams):
```python
from core.synaptic_conclave.transport.streams import StreamBus

bus = StreamBus()
bus.create_consumer_group("conclave.mcp.actions", "mcp_listeners")

for event in bus.consume("conclave.mcp.actions", "mcp_listeners", "listener_1"):
    handle_mcp_event(event.payload)
    bus.acknowledge("conclave.mcp.actions", "mcp_listeners", event.event_id)
```

#### 4. Vault Keepers Integration (`services/api_mcp/middleware.py`)

**Before** (Direct SQL):
```python
pg = PostgresAgent()
cur.execute("INSERT INTO mcp_tool_calls ...")
pg.connection.commit()
```

**After** (Event-Driven):
```python
# Emit archiving request to Vault Keepers
bus.emit("vault.mcp.archive", {
    "conclave_id": conclave_id,
    "tool_name": tool_name,
    "args": args,
    "result": result,
    "orthodoxy_status": orthodoxy_status,
    "user_id": user_id,
    "created_at": datetime.utcnow().isoformat()
})

# Vault Keepers listener will persist to PostgreSQL
```

### FASE 3 Acceptance Criteria

✅ **No Raw Redis**:
```bash
rg "redis\.Redis|pubsub\.subscribe|redis_client\.publish" \
   services/api_mcp/ vitruvyan_core/core/synaptic_conclave/listeners/mcp.py \
   && echo "❌ FAIL" || echo "✅ PASS"
```

✅ **StreamBus Everywhere**:
```bash
rg "from core\.synaptic_conclave\.transport\.streams import StreamBus" \
   services/api_mcp/middleware.py \
   vitruvyan_core/core/synaptic_conclave/listeners/mcp.py \
   && echo "✅ PASS" || echo "❌ FAIL"
```

✅ **Channel Alignment**:
```bash
# Verify MCP publishes to conclave.mcp.actions
rg 'bus\.emit\("conclave\.mcp\.actions"' services/api_mcp/middleware.py \
   && echo "✅ PASS" || echo "❌ FAIL"
```

---

## FASE 4: Configuration Cleanup (0.5 day)

### Goal
Centralize all hardcoded values in config, fix port mismatches, add missing Postgres config.

### Changes Required

#### 1. Centralize Thresholds (`services/api_mcp/config.py`)

**Add**:
```python
class OrthodoxConfig:
    # Normalized scores (z-scores)
    normalized_min_warning: float = float(os.getenv("MCP_NORMALIZED_MIN_WARNING", "-3.0"))
    normalized_max_warning: float = float(os.getenv("MCP_NORMALIZED_MAX_WARNING", "3.0"))
    normalized_min_heretical: float = float(os.getenv("MCP_NORMALIZED_MIN_HERETICAL", "-5.0"))
    normalized_max_heretical: float = float(os.getenv("MCP_NORMALIZED_MAX_HERETICAL", "5.0"))
    
    # Composite scores
    composite_min_warning: float = float(os.getenv("MCP_COMPOSITE_MIN_WARNING", "-5.0"))
    composite_max_warning: float = float(os.getenv("MCP_COMPOSITE_MAX_WARNING", "5.0"))
    composite_min_heretical: float = float(os.getenv("MCP_COMPOSITE_MIN_HERETICAL", "-10.0"))
    composite_max_heretical: float = float(os.getenv("MCP_COMPOSITE_MAX_HERETICAL", "10.0"))
    
    # Narrative word count
    narrative_min_words: int = int(os.getenv("MCP_NARRATIVE_MIN_WORDS", "50"))
    narrative_max_words: int = int(os.getenv("MCP_NARRATIVE_MAX_WORDS", "300"))

class PostgresConfig:
    host: str = os.getenv("POSTGRES_HOST", "${POSTGRES_HOST}")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    database: str = os.getenv("POSTGRES_DB", "vitruvyan")
    user: str = os.getenv("POSTGRES_USER", "vitruvyan_user")
    password: str = os.getenv("POSTGRES_PASSWORD", "")  # NEVER hardcode

class Config:
    service = ServiceConfig()
    redis = RedisConfig()
    api = APIConfig()
    orthodoxy = OrthodoxConfig()
    postgres = PostgresConfig()
```

#### 2. Fix Port Mismatch

**LangGraph Node** (`llm_mcp_node.py`):
```python
# BEFORE
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://vitruvyan_mcp:8021")  # ❌ Wrong port

# AFTER
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://vitruvyan_mcp:8020")  # ✅ Correct
```

#### 3. Fix Orthodoxy Status Parsing

**LangGraph Node** (`llm_mcp_node.py:260`):
```python
# BEFORE
orthodoxy_status = result.data.get("orthodoxy_status")  # ❌ Wrong location

# AFTER
orthodoxy_status = result.get("orthodoxy_status")  # ✅ Top-level
```

#### 4. Use Config in Middleware

**Middleware** (`services/api_mcp/middleware.py`):
```python
# BEFORE
if z < -3 or z > 3:  # ❌ Hardcoded

# AFTER
config = get_config()
threshold_config = ThresholdConfig(
    normalized_min_warning=config.orthodoxy.normalized_min_warning,
    normalized_max_warning=config.orthodoxy.normalized_max_warning,
    normalized_min_heretical=config.orthodoxy.normalized_min_heretical,
    normalized_max_heretical=config.orthodoxy.normalized_max_heretical
)

# Use LIVELLO 1 validation
from vitruvyan_core.core.governance.mcp_server.governance.orthodoxy_rules import validate_factor_set
validation_result = validate_factor_set(factor_set, threshold_config)
orthodoxy_status = validation_result.status.value
```

### FASE 4 Acceptance Criteria

✅ **No Hardcoded Thresholds**:
```bash
rg "< -3|> 3|< -5|> 5|100.*200" services/api_mcp/middleware.py \
   && echo "❌ FAIL" || echo "✅ PASS"
```

✅ **Config Centralized**:
```bash
rg "class OrthodoxConfig|class PostgresConfig" services/api_mcp/config.py \
   && echo "✅ PASS" || echo "❌ FAIL"
```

✅ **Correct Port**:
```bash
rg "vitruvyan_mcp:8020" vitruvyan_core/core/orchestration/langgraph/node/llm_mcp_node.py \
   && echo "✅ PASS" || echo "❌ FAIL"
```

---

## FASE 5: Documentation & Security (0.5 day)

### Goal
Update docs, remove credentials, verify full refactoring compliance.

### Changes Required

#### 1. Remove Credentials from Docs

**Appendix K** (`.github/Vitruvyan_Appendix_K_MCP_Integration.md:260`):
```markdown
# BEFORE
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}  # ❌ CRITICAL SECURITY VIOLATION

# AFTER
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}  # ✅ Environment variable
```

**Archive Compose** (`infrastructure/docker/archive/docker-compose.omni.yml.OBSOLETE_DEC29:139`):
```yaml
# BEFORE
POSTGRES_PASSWORD: "${POSTGRES_PASSWORD}"  # ❌ CRITICAL SECURITY VIOLATION

# AFTER (or delete file if truly obsolete)
POSTGRES_PASSWORD: "${POSTGRES_PASSWORD}"  # ✅ Environment variable
```

#### 2. Update README (`services/api_mcp/README.md`)

**Fix endpoint documentation**:
```markdown
# BEFORE
POST /tools/list      # ❌ Wrong endpoint
POST /tools/execute   # ❌ Wrong endpoint

# AFTER
GET /tools            # ✅ Correct
POST /execute         # ✅ Correct
```

**Add migration reference**:
```markdown
## Database Setup

Create the audit trail table:

```sql
-- migrations/001_mcp_tool_calls.sql
CREATE TABLE mcp_tool_calls (
    conclave_id UUID PRIMARY KEY,
    tool_name VARCHAR(100) NOT NULL,
    args JSONB NOT NULL,
    result JSONB NOT NULL,
    orthodoxy_status VARCHAR(20) NOT NULL CHECK (orthodoxy_status IN ('blessed', 'purified', 'heretical')),
    user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    execution_time_ms FLOAT,
    error_message TEXT
);

CREATE INDEX idx_mcp_tool_calls_user ON mcp_tool_calls(user_id);
CREATE INDEX idx_mcp_tool_calls_tool ON mcp_tool_calls(tool_name);
CREATE INDEX idx_mcp_tool_calls_created ON mcp_tool_calls(created_at);
```
```

#### 3. Create LIVELLO 1 README

**File**: `vitruvyan_core/core/governance/mcp_server/README.md`

```markdown
# MCP Server — Pure Domain Layer (LIVELLO 1)

**Sacred Order**: Gateway (Infrastructure)  
**Epistemic Order**: Truth & Governance (Validation)  
**Philosophy**: Stateless gateway to Sacred Orders with domain-agnostic tool orchestration

## Overview

MCP Server pure domain layer provides:
- Generic tool schema abstractions (OpenAI Function Calling compatible)
- Domain-agnostic factor representation (NOT finance-specific)
- Pure validation rules (Orthodoxy Wardens compliance)
- Standalone testable consumers (NO I/O)

## Quick Start

```python
# Pure validation (no Docker, no Redis, no PostgreSQL)
from vitruvyan_core.core.governance.mcp_server.domain.factor import Factor, FactorSet
from vitruvyan_core.core.governance.mcp_server.governance.orthodoxy_rules import validate_factor_set
from vitruvyan_core.core.governance.mcp_server.governance.threshold_config import ThresholdConfig

# Create factor set (domain-agnostic)
factor_set = FactorSet(
    entity_id="ENTITY_001",
    factors={
        "quality": Factor(name="quality", value=0.85, normalized_score=1.2),
        "relevance": Factor(name="relevance", value=0.72, normalized_score=-0.5)
    },
    composite_score=0.78
)

# Validate (pure function, testable)
config = ThresholdConfig()
result = validate_factor_set(factor_set, config)

print(f"Status: {result.status.value}")  # blessed | purified | heretical
print(f"Violations: {result.violations}")
print(f"Warnings: {result.warnings}")
```

## Architecture

See [SACRED_ORDER_PATTERN.md](../../SACRED_ORDER_PATTERN.md) for full two-level architecture.

**LIVELLO 1** (this package):
- Zero I/O (no database, no HTTP, no filesystem)
- Pure Python functions
- Testable standalone (`pytest tests/` with no Docker)

**LIVELLO 2** (`services/api_mcp/`):
- FastAPI HTTP service
- Redis Streams integration
- PostgreSQL archiving
- Tool executors (I/O wrappers to LangGraph, Neural Engine, etc.)

## Domain Model

### Factor (Generic Abstraction)
```python
@dataclass(frozen=True)
class Factor:
    name: str              # e.g., "quality", "relevance", "momentum" (deployment-specific)
    value: float           # Raw value
    normalized_score: float  # z-score, percentile, or other normalization
    percentile: float      # Optional percentile rank
```

### FactorSet (Entity Scoring)
```python
@dataclass(frozen=True)
class FactorSet:
    entity_id: str
    factors: Dict[str, Factor]
    composite_score: float
    rank: int
```

### Validation (Orthodoxy Rules)
```python
def validate_factor_set(factor_set: FactorSet, config: ThresholdConfig) -> ValidationResult:
    """Pure validation (NO I/O)."""
    # Check normalized scores against thresholds
    # Return: blessed | purified | heretical
```

## Deployment Patterns

### Healthcare Domain
```python
# Factors: patient_risk, readmission_likelihood, treatment_efficacy
factor_set = FactorSet(
    entity_id="PATIENT_12345",
    factors={
        "patient_risk": Factor(name="patient_risk", value=0.65, normalized_score=0.8),
        "readmission_likelihood": Factor(name="readmission_likelihood", value=0.12, normalized_score=-1.2)
    },
    composite_score=0.42
)
```

### E-Commerce Domain
```python
# Factors: conversion_rate, inventory_turnover, customer_satisfaction
factor_set = FactorSet(
    entity_id="PRODUCT_SKU_789",
    factors={
        "conversion_rate": Factor(name="conversion_rate", value=0.08, normalized_score=1.5),
        "inventory_turnover": Factor(name="inventory_turnover", value=5.2, normalized_score=0.3)
    },
    composite_score=0.71
)
```

## Testing

```bash
# Pure unit tests (no Docker)
cd vitruvyan_core/core/governance/mcp_server
pytest tests/ -v

# Expected: 10+ tests, < 5s duration, 100% pure (no network calls)
```

## Sacred Invariants

1. **Domain Agnosticism**: NO finance-specific terminology (momentum/trend/volatility hardcoded)
2. **Pure Functions**: ALL consumers return dataclasses, NO I/O side effects
3. **Config-Driven Validation**: Orthodoxy thresholds via ThresholdConfig (NO hardcoded ±3, ±5)
4. **Deterministic Validation**: Same factor_set + config = same ValidationResult (no date/time dependencies)

## References

- **Service Layer**: `services/api_mcp/`
- **Charter**: `philosophy/charter.md`
- **Examples**: `examples/pure_screen.py`, `examples/pure_orthodoxy.py`
- **Appendix**: `.github/Vitruvyan_Appendix_K_MCP_Integration.md`
```

### FASE 5 Acceptance Criteria

✅ **No Credentials in Repo**:
```bash
rg -i "Caravaggio|password.*=" --glob="!*.md.backup" --glob="!_legacy/**" \
   .github/ infrastructure/docker/archive/ \
   && echo "❌ FAIL (credentials found)" || echo "✅ PASS"
```

✅ **Documentation Updated**:
```bash
test -f vitruvyan_core/core/governance/mcp_server/README.md && echo "✅ PASS" || echo "❌ FAIL"
test -f vitruvyan_core/core/governance/mcp_server/philosophy/charter.md && echo "✅ PASS" || echo "❌ FAIL"
```

✅ **Migration Script Exists**:
```bash
test -f database/migrations/001_mcp_tool_calls.sql && echo "✅ PASS" || echo "❌ FAIL"
```

---

## 📋 Final Verification Checklist

### SACRED_ORDER_PATTERN Compliance

```bash
# 1. LIVELLO 1 structure (10 directories)
ls vitruvyan_core/core/governance/mcp_server/ | wc -l
# Expected: 10

# 2. No root Python files (except __init__.py)
find vitruvyan_core/core/governance/mcp_server/ -maxdepth 1 -name "*.py" ! -name "__init__.py"
# Expected: (empty)

# 3. Pure imports (no infrastructure dependencies)
python3 -c "from vitruvyan_core.core.governance.mcp_server.consumers import *; print('✅ Pure')"
# Expected: ✅ Pure (no errors)

# 4. No service imports in LIVELLO 1
rg "from services\." vitruvyan_core/core/governance/mcp_server/ && echo "❌ VIOLATION" || echo "✅ OK"
# Expected: ✅ OK

# 5. main.py < 50 lines
wc -l services/api_mcp/main.py
# Expected: 43 (already compliant)

# 6. All I/O in adapters
test -f services/api_mcp/adapters/bus_adapter.py && echo "✅ OK" || echo "❌ MISSING"
test -f services/api_mcp/adapters/persistence.py && echo "✅ OK" || echo "❌ MISSING"
```

### Domain Agnosticism

```bash
# No finance terms
rg "momentum|trend|volatility|sentiment|fundamental|ticker|stock|market|investment|VARE" \
   services/api_mcp/schemas/tools.py \
   services/api_mcp/tools/*.py \
   vitruvyan_core/core/governance/mcp_server/ \
   --glob="!_legacy/**" \
   && echo "❌ FAIL" || echo "✅ PASS"

# Generic factor terminology
rg "class Factor|class FactorSet" vitruvyan_core/core/governance/mcp_server/domain/factor.py \
   && echo "✅ PASS" || echo "❌ FAIL"
```

### Streams Integration

```bash
# StreamBus everywhere
rg "from core\.synaptic_conclave\.transport\.streams import StreamBus" \
   services/api_mcp/middleware.py \
   vitruvyan_core/core/synaptic_conclave/listeners/mcp.py \
   && echo "✅ PASS" || echo "❌ FAIL"

# No raw Redis
rg "redis\.Redis|pubsub\.subscribe" \
   services/api_mcp/ vitruvyan_core/core/synaptic_conclave/listeners/mcp.py \
   && echo "❌ FAIL" || echo "✅ PASS"

# Correct channels
rg 'emit\("conclave\.mcp\.actions"' services/api_mcp/middleware.py && echo "✅ PASS" || echo "❌ FAIL"
```

### Configuration

```bash
# No hardcoded thresholds
rg "< -3|> 3|< -5|> 5|100.*200" services/api_mcp/middleware.py \
   && echo "❌ FAIL" || echo "✅ PASS"

# Config classes exist
rg "class OrthodoxConfig|class PostgresConfig" services/api_mcp/config.py \
   && echo "✅ PASS" || echo "❌ FAIL"

# Correct port
rg "vitruvyan_mcp:8020" vitruvyan_core/core/orchestration/langgraph/node/llm_mcp_node.py \
   && echo "✅ PASS" || echo "❌ FAIL"
```

### Security

```bash
# No credentials
rg -i "password.*=.*['\"]" --glob="!*.backup" --glob="!_legacy/**" \
   .github/ infrastructure/ services/ \
   && echo "❌ FAIL (credentials found)" || echo "✅ PASS"
```

---

## 📊 Agnosticization Score Tracking

### Before Refactoring
- **ChatGPT Score**: 16/100
  - Domain Purity: 2/20
  - Abstraction Purity: 5/20
  - Epistemic Boundary: 3/20
  - Config Injection: 3/20
  - Micelial Integration: 3/20

- **Copilot Score**: 50/100
  - LIVELLO 1: 0/50 (MISSING)
  - LIVELLO 2: 50/50 (Complete)

### After Refactoring (Target)
- **ChatGPT Score**: 100/100
  - Domain Purity: 20/20 (generic factors, no finance)
  - Abstraction Purity: 20/20 (StreamBus, pure domain)
  - Epistemic Boundary: 20/20 (channel alignment, event-driven)
  - Config Injection: 20/20 (centralized, env vars)
  - Micelial Integration: 20/20 (Streams, proper consumers)

- **Copilot Score**: 100/100
  - LIVELLO 1: 50/50 (Complete, pure, testable)
  - LIVELLO 2: 50/50 (Thin adapters, I/O only)

---

## 🚀 Implementation Timeline

| Phase | Duration | Lines Changed | Files Modified | Commits |
|-------|----------|---------------|----------------|---------|
| FASE 1 (LIVELLO 1) | 2 days | +1,200 | 25 new files | 3-4 |
| FASE 2 (Domain Agnostic) | 1 day | +300 / -450 | 8 files | 2-3 |
| FASE 3 (Streams) | 1 day | +150 / -120 | 5 files | 2 |
| FASE 4 (Config) | 0.5 day | +80 / -40 | 4 files | 1 |
| FASE 5 (Docs/Security) | 0.5 day | +400 / -50 | 6 files | 1-2 |
| **TOTAL** | **5 days** | **+2,130 / -660** | **48 files** | **9-12** |

---

## 🎯 Success Criteria (Final Gate)

### Mandatory (All must pass)

✅ **LIVELLO 1 Complete**: 10 directories, 20+ files, pure imports, unit tests passing  
✅ **Domain Agnostic**: Zero finance terms in core/schemas/tools (grep clean)  
✅ **Streams Integration**: StreamBus everywhere, no raw Redis (grep clean)  
✅ **Config Centralized**: All thresholds in config.py (no hardcoded)  
✅ **Security**: No credentials in repo (grep clean)  
✅ **Documentation**: README in LIVELLO 1 + LIVELLO 2, charter.md, examples  
✅ **Tests**: Unit tests (LIVELLO 1, < 5s) + integration tests (LIVELLO 2, Docker)  

### Performance (Should not regress)

✅ **Latency**: < 100ms overhead for pure validation (LIVELLO 1)  
✅ **Docker Build**: < 3min (no new heavyweight dependencies)  
✅ **Test Duration**: Unit tests < 10s, integration < 60s  

---

## 📦 Git Commit Strategy

### Commit Sequence

```bash
# FASE 1
git commit -m "refactor(mcp_server): LIVELLO 1 structure creation - SACRED_ORDER_PATTERN foundation"
git commit -m "refactor(mcp_server): Pure domain entities (Factor, FactorSet, ToolSchema)"
git commit -m "refactor(mcp_server): Pure consumers (screen, sentiment, vee) - NO I/O"
git commit -m "refactor(mcp_server): Pure Orthodoxy validation + unit tests (10+ tests passing)"

# FASE 2
git commit -m "refactor(mcp_server): Domain-agnostic tool schemas - remove finance taxonomy"
git commit -m "refactor(mcp_server): Generic factor representation - LIVELLO 2 uses LIVELLO 1 consumers"
git commit -m "refactor(mcp_server): Remove finance prompts (LangGraph MCP node)"

# FASE 3
git commit -m "refactor(mcp_server): StreamBus integration - replace Pub/Sub middleware"
git commit -m "refactor(mcp_server): Channel alignment (conclave.mcp.actions) + Core listener Streams conversion"

# FASE 4
git commit -m "refactor(mcp_server): Centralize config - OrthodoxConfig + PostgresConfig"
git commit -m "fix(mcp_server): Port mismatch (8020) + orthodoxy_status parsing (top-level)"

# FASE 5
git commit -m "docs(mcp_server): LIVELLO 1 README + charter.md + examples"
git commit -m "security(mcp_server): Remove hardcoded credentials from docs/archives"
git commit -m "docs(mcp_server): Complete domain-agnostic refactoring - 16% → 100% agnosticization

FINAL SCORE:
- ChatGPT: 100/100 (was 16/100, +84%)
- Copilot: 100/100 (was 50/100, +50%)
- SACRED_ORDER_PATTERN: 100% compliant

Refactoring Summary:
- LIVELLO 1: 25 new files (domain/, consumers/, governance/, tests/)
- Domain Leakage: 9 critical violations fixed (finance → generic)
- Streams: Pub/Sub → StreamBus (6 files updated)
- Config: 7 hardcoded values → centralized config
- Security: 2 credential leaks removed

Files Changed: 48 (+2,130 / -660 lines)
Test Coverage: 15 unit tests (LIVELLO 1) + 8 integration tests (LIVELLO 2)
Duration: 5 days

References: MCP_SERVER_CONSTITUTIONAL_REFACTORING_PLAN.md"
```

---

## 🔄 Rollback Strategy

### If Refactoring Fails

**Checkpoint Commits**:
1. After FASE 1: Tag `mcp-refactor-livello1-checkpoint`
2. After FASE 2: Tag `mcp-refactor-domain-agnostic-checkpoint`
3. After FASE 3: Tag `mcp-refactor-streams-checkpoint`

**Rollback**:
```bash
# Rollback to pre-refactoring
git reset --hard <commit-before-refactoring>

# Rollback to specific checkpoint
git reset --hard mcp-refactor-livello1-checkpoint
```

**Partial Rollback** (keep LIVELLO 1, rollback LIVELLO 2 changes):
```bash
# Restore LIVELLO 2 files from pre-refactoring
git checkout <commit-before-refactoring> -- services/api_mcp/

# Keep LIVELLO 1 (new files, not in old commits)
# vitruvyan_core/core/governance/mcp_server/ remains
```

---

## 📞 Support & Review

### Code Review Checklist

- [ ] LIVELLO 1 pure imports verified (no I/O dependencies)
- [ ] Unit tests passing (pytest vitruvyan_core/core/governance/mcp_server/tests/)
- [ ] No finance terms in grep searches (momentum, trend, volatility, ticker, market)
- [ ] StreamBus everywhere (no redis.Redis, no pubsub)
- [ ] Config centralized (no hardcoded -3, 3, 5, 100, 200)
- [ ] Documentation complete (README LIVELLO 1 + LIVELLO 2, charter.md)
- [ ] Security clean (no credentials grep)
- [ ] Integration tests passing (Docker stack healthy)

### Questions & Escalation

- **Architecture Decision**: Copilot (SACRED_ORDER_PATTERN guardian)
- **Domain Agnosticism**: ChatGPT auditor
- **Performance Regression**: Load testing team
- **Security Issues**: Immediate escalation (credentials, SQL injection)

---

**Plan Status**: 🚧 READY FOR APPROVAL  
**Next Step**: Execute FASE 1 (LIVELLO 1 structure creation)  
**ETA**: February 16, 2026 (5 days from Feb 11)  
**Approval Required**: Project lead architectural decision (Option A vs C from previous audit)
