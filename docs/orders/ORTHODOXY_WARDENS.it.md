# Orthodoxy Wardens

- **Livello epistemico**: Truth & Governance
- **Mandato**: validare output e rendere verdetti epistemici (blessed / heretical / non_liquet)
- **Confine**: il giudice non esegue correzioni (solo richieste/reporting)

## Charter (Mandato + Non-goals)

### Mandato
Tribunale epistemico: riceve confessioni (audit), esamina evidenze, rende verdetti, archivia decisioni.

### Non-goals
- Nessun restart, nessuna scrittura DB, nessun “fix” in LIVELLO 1.
- Non sostituisce la logica di dominio: valuta qualità/compliance epistemica.

## Interfacce

### Contratto eventi (Cognitive Bus)
Definiti in `vitruvyan_core/core/governance/orthodoxy_wardens/events/orthodoxy_events.py` (estratto):

- lifecycle: `orthodoxy.confession.received`, `orthodoxy.examination.started`, `orthodoxy.examination.completed`
- verdetti: `orthodoxy.verdict.rendered`, `orthodoxy.verdict.heretical`, `orthodoxy.verdict.non_liquet`
- richieste: `orthodoxy.purification.requested`, `orthodoxy.archive.requested`

### Servizio (LIVELLO 2)
- `services/api_orthodoxy_wardens/`

## Pipeline (happy path)

1. Confessione → `Confession`
2. Findings → aggregazione
3. Verdict → output + eventuale richiesta purificazione
4. Archival (integrazione Vault Keepers)

## Mappa codice

### LIVELLO 1 (pure)
- `vitruvyan_core/core/governance/orthodoxy_wardens/domain/`
- `vitruvyan_core/core/governance/orthodoxy_wardens/consumers/`
- `vitruvyan_core/core/governance/orthodoxy_wardens/governance/`

### LIVELLO 2 (adapters)
- `services/api_orthodoxy_wardens/`

## Verticalizzazione (pilota finanza)

Il dominio contribuisce regole/constraint come evidenze (numeri, unità, compliance, posture istituzionale).

