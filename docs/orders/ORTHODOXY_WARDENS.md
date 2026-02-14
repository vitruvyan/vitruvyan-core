# Orthodoxy Wardens

> **Last Updated**: February 14, 2026

## What it does

- Turns audit triggers into structured cases
- Produces findings and renders verdicts (including `non_liquet`)
- Declares correction/logging directives (service executes I/O)

- **Epistemic Layer**: Truth & Governance
- **Mandate**: validate outputs and render epistemic verdicts (blessed / heretical / non_liquet)
- **Hard boundary**: the judge never executes corrections (only requests/reporting)

## Charter (Mandate + Non-goals)

### Mandate
Act as an epistemic tribunal: receive confessions (audit requests), examine evidence, render verdicts, and archive decisions.

### Non-goals
- No service restarts, no DB writes, no “fixes” inside LIVELLO 1.
- Does not replace domain logic: it evaluates epistemic quality/compliance.

## Interfaces

### Event contract (Cognitive Bus)
Defined in `vitruvyan_core/core/governance/orthodoxy_wardens/events/orthodoxy_events.py` (selected):

- lifecycle: `orthodoxy.confession.received`, `orthodoxy.examination.started`, `orthodoxy.examination.completed`
- verdicts: `orthodoxy.verdict.rendered`, `orthodoxy.verdict.heretical`, `orthodoxy.verdict.non_liquet`
- outbound requests: `orthodoxy.purification.requested`, `orthodoxy.archive.requested`

### Service (LIVELLO 2)
- `services/api_orthodoxy_wardens/` — subscriptions, persistence, HTTP endpoints

## Pipeline (happy path)

1. Confession received → normalized `Confession`
2. Findings recorded (`Finding`) → aggregated
3. Verdict rendered (`Verdict`) + optional purification request
4. Decision archived (Vault Keepers integration)

## Code map

### LIVELLO 1 (pure)
- `vitruvyan_core/core/governance/orthodoxy_wardens/domain/` — `Confession`, `Finding`, `Verdict`
- `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/` — confessor/inquisitor/penitent/chronicler
- `vitruvyan_core/core/governance/orthodoxy_wardens/governance/` — rulesets/classifiers

### LIVELLO 2 (adapters)
- `services/api_orthodoxy_wardens/`

## Verticalization (finance pilot)

Finance contributes domain-specific validation rules as **evidence** (not authority):

- numeric hallucination checks (prices, returns, units)
- compliance constraints (disclaimers, uncertainty, provenance)
- allowed actions and forbidden claims (institutional posture)
