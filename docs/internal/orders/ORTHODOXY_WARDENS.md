# Orthodoxy Wardens

<p class="kb-subtitle">Epistemic tribunal: findings, verdicts, corrections plans (advisory), and audit directives.</p>

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
    - **PatternClassifier** for text
    - **ASTClassifier** for code (optional; emits a warning finding on `SyntaxError`)
  - produces `InquisitorResult` (frozen)

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
