# Masterplan Core Update/Upgrade 🚀

## Obiettivo 🎯

Definire un sistema di aggiornamento del Core Vitruvyan in stile distro:

- notifica quando un update e disponibile 🔔
- un comando unico per aggiornare ⚙️
- verifica compatibilita verticale prima e dopo l'upgrade ✅
- rollback automatico in caso di errore 🛟

Risultato atteso: **zero fork del Core tra i verticali** e update ripetibili.

## Stato Finale (End State) 🧭

Quando un team verticale esegue:

```bash
vitruvyan update check
vitruvyan update apply
```

la piattaforma deve:

1. rilevare l'ultima release del Core
2. validare compatibilita via manifest verticale + versione contracts
3. generare un piano upgrade (cosa cambia, rischi, test richiesti)
4. applicare upgrade in modalita transazionale
5. eseguire smoke test verticali
6. confermare l'upgrade oppure fare rollback automatico

## Principi Non Negoziabili 🧱

- I verticali importano solo da `contracts`, mai dagli internals Core.
- Nessuna release Core viene pubblicata senza compatibility checks.
- Ogni upgrade deve essere tracciabile via audit log e report.
- Le rotture contrattuali richiedono major version + deprecation policy.

## Architettura Logica 🏗️

Componenti principali:

- `Release Registry`
- `Compatibility Engine`
- `Update Manager CLI`
- `Notification Engine`
- `Safety Layer` (snapshot, test, rollback)
- `Policy & Governance` (versioning, deprecazioni, finestra supporto)

### 1) Release Registry 📦

Fonte di verita delle release Core (inizio: GitHub Releases).

Metadati minimi per release:

- versione Core
- versione contracts supportata
- canale (`stable`, `canary`, `lts`)
- changelog machine-readable
- checksum artifact
- migration notes

### 2) Compatibility Engine 🧠

Legge:

- metadati release
- `vertical_manifest.yaml`

Produce:

- `compatible`
- `compatible_with_warnings`
- `blocked`

Motivi tipici di blocco:

- versione Core fuori range supportato
- mismatch contracts major
- capability richiesta non piu disponibile

### 3) Update Manager CLI 🛠️

Comandi target:

- `vitruvyan update check`
- `vitruvyan update plan`
- `vitruvyan update apply`
- `vitruvyan update rollback`
- `vitruvyan update status`

Comportamento minimo:

- output leggibile per umano
- exit code robusti per CI/CD
- modalita non interattiva (`--yes`) per automazione

### 4) Notification Engine 🔔

Canali minimi:

- notifica all'avvio servizio
- check periodico schedulato

Canali opzionali:

- Slack/Webhook
- dashboard interna

### 5) Safety Layer 🛡️

Durante `update apply`:

- snapshot dello stato corrente (commit/tag/deps/manifest)
- applica update
- esegue smoke suite minima
- se fallisce: rollback automatico + report

### 6) Policy & Governance 📜

- SemVer del Core
- versioning separato per Contracts
- policy deprecazioni con finestra supporto
- policy canali release (`stable/canary/lts`)

## Tracklist Implementativa 🧭

## Fase 0 - Fondazioni (Settimana 1) 🧱

Obiettivo: fissare regole base e schema dati.

Task:

- formalizzare policy versioning Core/Contracts
- estendere `vertical_manifest.yaml` con campi compatibilita
- definire schema release metadata
- definire matrice compatibilita iniziale

Deliverable:

- documento policy (`docs/contracts/...`)
- template manifest aggiornato
- esempio release metadata JSON/YAML

Definition of Done:

- policy approvata
- schema manifest validato
- un verticale esempio compilato con nuovo schema

## Fase 1 - Compatibility Engine (Settimana 2) 🧠

Obiettivo: bloccare update rischiosi prima dell'applicazione.

Task:

- implementare parser manifest verticale
- implementare validazione version range Core
- implementare validazione contracts major
- generare report compatibilita con motivazioni

Deliverable:

- modulo `compatibility_engine`
- comando `vitruvyan update check`
- report testuale + JSON

Definition of Done:

- 100% casi happy-path passano
- casi incompatibili restituiscono `blocked` con motivo esplicito

## Fase 2 - Apply + Rollback (Settimane 3-4) 🔁

Obiettivo: flusso upgrade transazionale sicuro.

Task:

- implementare `update plan`
- implementare `update apply`
- snapshot pre-upgrade
- smoke test post-upgrade
- rollback automatico

Deliverable:

- workflow end-to-end locale
- log esecuzione upgrade/rollback

Definition of Done:

- update compatibile applicato con successo
- test falliti attivano rollback automatico
- stato finale consistente e verificabile

## Fase 3 - CI/CD Gate (Settimana 5) 🚦

Obiettivo: impedire release Core che rompono verticali attive.

Task:

- pipeline CI di compatibilita multi-verticale
- regole gating su PR/release
- report compatibilita come artifact CI

Deliverable:

- pipeline CI aggiornata
- regola release-blocking attiva

Definition of Done:

- una release incompatibile viene bloccata automaticamente

## Fase 4 - Notification System (Settimana 6) 📣

Obiettivo: visibilita automatica degli update per i team.

Task:

- notifiche in `update check`
- notifiche schedulate periodiche
- (opzionale) webhook Slack

Deliverable:

- notifica locale + log
- configurazione canale notifiche

Definition of Done:

- i team verticali ricevono alert senza polling manuale

## Fase 5 - Hardening & Governance (Settimane 7-8) 🧰

Obiettivo: affidabilita production-grade.

Task:

- audit trail completo upgrade
- policy support window (N versioni supportate)
- test di resilienza rollback
- runbook incident per update falliti

Deliverable:

- runbook operativo
- checklist pre/post-upgrade
- dashboard stato versioni verticali (anche minima)

Definition of Done:

- processo upgrade ripetibile e auditabile in produzione

## Backlog Tecnico Minimo ✅

- [ ] estendere `vertical_manifest.yaml` (campi compatibilita)
- [ ] definire schema `release_metadata.json`
- [ ] implementare `update check`
- [ ] implementare `update plan`
- [ ] implementare `update apply`
- [ ] implementare `update rollback`
- [ ] creare smoke test pack per verticale
- [ ] generare report compatibilita JSON
- [ ] implementare CI compatibility gate
- [ ] aggiungere audit logging upgrade

## Campi Manifest Richiesti (Target) 📄

```yaml
domain_name: "example"
domain_version: "0.1.0"
status: "active"

compatibility:
  min_core_version: "1.2.0"
  max_core_version: "1.4.x"
  contracts_major: 1
  update_channel: "stable" # stable|canary|lts

ownership:
  team: "domain-team"
  tech_lead: "name.surname"
  contact: "team@example.com"
```

## Flusso Operativo Standard (SOP) 🔄

1. il team verticale esegue `vitruvyan update check`
2. se `compatible`, esegue `vitruvyan update plan`
3. approva e lancia `vitruvyan update apply`
4. la piattaforma esegue smoke test
5. se passano, upgrade confermato
6. se falliscono, rollback + ticket/report

## Rischi Principali & Mitigazioni ⚠️

- Rischio: il verticale importa internals Core invece dei contracts.
  Mitigazione: lint/policy CI che blocca import non autorizzati.

- Rischio: release metadata incompleti.
  Mitigazione: template metadata obbligatorio + validazione pre-release.

- Rischio: rollback non affidabile.
  Mitigazione: snapshot atomico + prove rollback periodiche.

## Ownership Consigliata 👥

- Team Platform/Core: release registry, contracts, update manager
- Team Verticali: manifest, smoke test, compliance verticale
- DevOps/SRE: CI gates, notifiche, observability, runbook

## KPI da Monitorare 📈

- upgrade riusciti (%)
- mean time to upgrade (MTTU)
- rollback rate (%)
- incompatibilita intercettate pre-deploy
- incident post-upgrade

## Ordine di Rollout Consigliato 🗺️

1. Fase 0 e Fase 1 per prime (prevenzione rotture)
2. Fase 2 subito dopo (apply + rollback)
3. Fase 3 prima di scalare il numero di verticali
4. Fase 4 e 5 per l'operativita continua

Questa sequenza minimizza il rischio architetturale prima dell'espansione verticale.
