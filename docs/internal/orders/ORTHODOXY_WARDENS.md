# Orthodoxy Wardens

> **Last Updated**: March 08, 2026 — v1.13.0 (Gate informativo + Shadow Mode)

<p class="kb-subtitle">Epistemic tribunal: findings, verdicts, corrections plans (advisory), and audit directives.</p>

## What it does

- **Intake and structure**: turns raw events/requests into structured cases (`Confession`)
- **Audit and judge**: produces findings and renders a `Verdict` (including `non_liquet`)
- **Declare actions**: outputs correction plans (advisory) and logging/archive directives (service executes I/O)

Orthodoxy Wardens is the **epistemic governance tribunal**: it audits events/outputs, produces findings, renders verdicts, and declares what should be logged or corrected.

## Code map

- **LIVELLO 1 (pure governance, no I/O)**: `vitruvyan_core/core/governance/orthodoxy_wardens/`
  - Consumers (Sacred Roles): `consumers/confessor.py`, `consumers/inquisitor.py`, `consumers/penitent.py`, `consumers/chronicler.py`
  - Static analysis helper: `consumers/code_analyzer.py`
  - Verdict engine: `governance/verdict_engine.py`
  - Domain objects: `domain/*` (Confession, Finding, Verdict, LogDecision, …)
  - Events schema: `events/orthodoxy_events.py`
- **Automation agents (mixed purity / legacy)**: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/*_agent.py`
  - `confessor_agent.py` (LangGraph “Autonomous Audit Agent”, uses LLM + tools)
  - `inquisitor_agent.py` (`ComplianceValidator`, pattern scan + optional LLM semantic check)
  - `penitent_agent.py` (`AutoCorrector`, executes corrective actions; uses system tools)
- **LIVELLO 2 (service + adapters)**: `services/api_orthodoxy_wardens/`
  - API + bus integration + persistence (service responsibilities)

## Pipeline (internal)

As documented in `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/README.md`:

1. `Confessor.process(event)` → `Confession`
2. `Inquisitor.process({confession, text, code})` → `InquisitorResult(findings=...)`
3. `VerdictEngine.render(findings)` → `Verdict`
4. `Penitent.process(verdict)` → `CorrectionPlan` *(advisory; never executes)*
5. `Chronicler.process(verdict)` → `ChronicleDecision` *(logging + archive directives; never persists)*

---

## Sacred Roles (LIVELLO 1, pure)

### `Confessor` — intake officer (raw → structured case)

- File: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/confessor.py`
- Purpose:
  - accepts `OrthodoxyEvent` or dict
  - maps `event_type` to `trigger_type`, `scope`, `urgency`
  - emits a **frozen** `Confession` (structured case; the `confession_id` is unique, not deterministic)

**How it works (important details)**:

- `event_type` mapping tables:
  - `_EVENT_TO_TRIGGER`, `_EVENT_TO_SCOPE`, `_EVENT_TO_URGENCY` (defaults apply when missing)
- Dict inputs:
  - `metadata` is normalized to a frozen `tuple(...)` for immutability
- ID generation:
  - `confession_<timestamp>_<uuid>` (unique per intake)

### `Inquisitor` — examiner (case → findings)

- File: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/inquisitor.py`
- Purpose:
  - applies governance rules to produce `Finding` objects
  - combines:
    - **LLMClassifier** for text (primary, LLM-first semantic analysis)
    - **ASTClassifier** for code (optional; emits a warning finding on `SyntaxError`)
  - produces `InquisitorResult` (frozen)
  - Note: PatternClassifier (regex) is DEPRECATED — LLMClassifier replaced it

**How it works (important details)**:

- Inputs:
  - dict with `{confession, text, code}` OR a `Confession` (examines metadata as text)
- Outputs:
  - `InquisitorResult(findings=tuple[Finding, ...], rules_applied=int, text_examined=bool, code_examined=bool)`

### `Penitent` — correction advisor (verdict → correction plan)

- File: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/penitent.py`
- Purpose:
  - transforms a `Verdict` into a `CorrectionPlan`
  - advisory only: it never executes changes; service layer decides what to do

**How it works (important details)**:

- Strategy selection is rule-based (category → strategy; severity → priority)
- Human review is required for:
  - category in `{security, architectural}` OR severity `critical`

### `Chronicler` — logging strategist (verdict → archive directives)

- File: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/chronicler.py`
- Purpose:
  - decides *what to log* (via `LogDecision`)
  - declares *where to archive* (via `ArchiveDirective`)
  - supports destinations like `postgresql`, `qdrant`, `blockchain`, `cognitive_bus`
  - remains pure: no persistence, no bus I/O

**How it works (important details)**:

- Archive destinations are decided from `verdict.status`:
  - `heretical` → all destinations (includes blockchain anchoring + bus broadcast)
  - `purified` → `postgresql` + `qdrant` + `cognitive_bus`
  - `blessed` → `postgresql` only
  - `non_liquet` → `postgresql` + `qdrant`

---

## Supporting agent: `CodeAnalyzer` (static code analysis)

- File: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/code_analyzer.py`
- Purpose:
  - pure/static checks: compliance patterns, security patterns, perf patterns, quality checks
  - useful for auditing code diffs or source snippets before verdict rendering

---

## Automation agents (mixed purity / legacy)

These live under the same folder but **are not LIVELLO 1-pure** (they use LLM and/or system tools). Treat them as “experimental governance automation” that should eventually migrate behind LIVELLO 2 adapters.

### `AutonomousAuditAgent` (LangGraph)

- File: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/confessor_agent.py`
- What it does:
  - orchestrates an audit workflow as a graph (LangGraph)
  - uses the centralized LLM gateway (`core/agents/llm_agent.py`)
  - composes `CodeAnalyzer` + `ComplianceValidator` + `AutoCorrector`
- Important note:
  - the file explicitly documents that it violates purity (tool I/O must be injected/configured by LIVELLO 2)

### `ComplianceValidator` (pattern scan + optional LLM check)

- File: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/inquisitor_agent.py`
- What it does:
  - stage 1: regex/pattern scan for prescriptive advice / unsupported claims / disclaimer issues
  - stage 2: optional LLM semantic validation to reduce false positives
- Where it fits:
  - can be used before sending narratives/outputs to end-users (finance compliance gate)

### `AutoCorrector` (executes corrections)

- File: `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/penitent_agent.py`
- What it does:
  - executes corrective actions (e.g., restart containers, clean disk, rewrite compliance text)
  - includes rollback concepts and operational safety checks

## Domain notes

- Core objects:
  - `Confession`: the structured case entering the tribunal
  - `Finding`: an immutable piece of evidence
  - `Verdict`: the governance decision (`blessed`, `purified`, `heretical`, `non_liquet`, …)

### Domain governance hook (real contract)

- Hook registry:
  - `vitruvyan_core/core/governance/orthodoxy_wardens/governance/rule_registry.py`
  - `register_domain(domain)` dynamically imports:
    - `domains.<domain>.governance_rules`
    - expects `get_domain_rules() -> Tuple[Rule, ...]`
- Domain implementation example:
  - `vitruvyan_core/domains/finance/governance_rules.py`
  - exports `get_domain_rules()`

### Runtime status

- `STATUS: ENABLED (finance vertical wiring active)`
- Runtime behavior:
  - startup reads `ORTHODOXY_DOMAIN` (`generic` or `finance`)
  - when `ORTHODOXY_DOMAIN=finance`, LIVELLO 2 loads finance rules from:
    - `vitruvyan_core/domains/finance/governance_rules.py`
  - combined ruleset (generic + finance) is injected into `Inquisitor(ruleset=...)`
  - same finance-aware ruleset is used by API startup and Redis Streams listener
  - optional override via `ORTHODOXY_RULESET_VERSION`

### How to enable domain rules (ops)

Set environment variables in service and listener:

```bash
ORTHODOXY_DOMAIN=finance
ORTHODOXY_RULESET_VERSION=v1.1-finance
```

Finance-only HTTP endpoints are conditionally exposed under:

```text
/v1/finance/*
```

For end-to-end vertical implementation steps, use:

- `docs/knowledge_base/development/Vertical_Implementation_Guide.md`
- `docs/knowledge_base/development/verticals/Vertical_Sacred_Orders.md`
- `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`

---

## v1.13.0: Orthodoxy Gate + Shadow Mode

> Added Mar 08, 2026

### Gate Informativo (non-blocking)

`orthodoxy_node.py` (429 righe) implementa un **Gate informativo** nel pipeline LangGraph:

- Il verdetto è calcolato per ogni richiesta
- Il verdetto è scritto nello state come metadata (`state["orthodoxy_verdict"]`)
- La risposta **non viene mai bloccata** (Gate non-blocking)
- Ogni verdetto alimenta `OutcomeTracker.record_outcome()` → Plasticity self-learning loop
- Bus event (fire-and-forget) per audit async (complementare)

**Tre livelli Gate** (progressivi — solo livello 1 attivo in v1.13.0):
1. ✅ **Gate informativo** (v1.13.0): verdetto calcolato + logged, risposta mai bloccata
2. ⏳ **Gate soft** (futuro): `heretical` → disclaimer aggiunto alla risposta
3. ⏳ **Gate hard** (futuro): `heretical` → risposta sostituita con rifiuto

### Shadow Mode + ShadowEvaluator

- File: `services/api_graph/adapters/plasticity_adapter.py` (ShadowEvaluator class)
- Endpoint: `POST /shadow/evaluate`
- Scopo: confronto parallelo `LLMClassifier` vs `PatternClassifier` su input reale
- Uso: validazione della migrazione prima di abilitare Gate soft/hard
- Risultato: `{llm_findings, pattern_findings, agreement_score, discrepancies}`

### Plasticity Integration

Ogni verdetto Gate alimenta il ciclo di auto-apprendimento:

```python
# In orthodoxy_node.py, dopo ogni Gate verdict:
outcome = Outcome(
    decision_event_id=state["trace_id"],
    outcome_type=f"orthodoxy.{verdict.status}",
    outcome_value=VERDICT_TO_SCORE[verdict.status],  # blessed=1.0, heretical=0.0
    consumer_name="langgraph_pipeline",
    parameter_name="response_quality",
)
await outcome_tracker.record_outcome(outcome)
```

I punteggi fluiscono in `LearningLoop` (24h cycle) che adatta le soglie del `VerdictEngine` via `PlasticityManager`.
