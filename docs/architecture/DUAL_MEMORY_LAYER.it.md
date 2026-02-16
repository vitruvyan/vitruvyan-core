---
tags:
  - architecture
  - memory
  - governance
  - sacred-orders
---

# 🧠 Dual Memory Layer in Vitruvyan

**PostgreSQL + Qdrant coordinati dagli ordini di governance**

## 🧭 1) Cos’è

Il Dual Memory Layer è il substrato di memoria di Vitruvyan:

- 🧱 **Archivarium (PostgreSQL)** conserva la verità canonica strutturata
- 🌐 **Mnemosyne (Qdrant)** conserva la rappresentazione semantica vettoriale
- ⚖️ **Memory Orders** mantiene allineati i due layer nel tempo
- 🏛️ **Vault Keepers** registra evidenze di audit e tracciabilità
- 🛡️ **Orthodoxy Wardens** registra verdetti epistemici e governance

In sintesi: una memoria deterministica, una memoria semantica, e una governance che ne preserva la coerenza.

---

## 🧱 2) Cosa fa ogni layer

### Archivarium — memoria strutturata

PostgreSQL è la sorgente autorevole per entità, versioni e stato relazionale.
Supporta query deterministiche, controlli di consistenza e collegamento con l’audit.

### Mnemosyne — memoria semantica

Qdrant conserva vettori e payload semantici usati per retrieval e pattern correlation.
Abilita similarity search ed espansione contestuale su input multilingue/non strutturati.

---

## ⚖️ 3) Ruolo di Memory Orders

Memory Orders è l’ordine di coordinamento e integrità tra le due memorie.
Svolge tre funzioni centrali:

1. **Drift calculation**: rileva divergenze tra stato canonico e stato semantico
2. **Health aggregation**: produce una vista unica di salute del sottosistema memoria
3. **Sync/reconciliation planning**: genera e, quando consentito, esegue operazioni di riallineamento

Memory Orders non definisce la verità di dominio: protegge l’allineamento tra verità e rappresentazione.

---

## 🛡️ 4) Modello di riconciliazione ed enforcement

La riconciliazione segue un modello di policy controllato:

- `dry_run`: genera solo il piano, senza mutazioni
- `assisted` / `autonomous`: consente l’esecuzione quando richiesta

La sicurezza operativa è garantita da:

- **Idempotency key** (`idempotency_key`) per evitare esecuzioni duplicate
- **Lock di run** per coppia (`table` + `collection`) contro conflitti concorrenti
- **Guardrail mass-delete** (soglia di sicurezza, override esplicito richiesto)
- **Retry + dead-letter** per operazioni fallite (`memory.reconciliation.dead_letter`)

Il modello mantiene PostgreSQL autorevole e riconcilia lo stato derivato su Qdrant.

---

## 🔗 5) Accoppiamento con la governance

Gli ordini sono connessi ma separati:

```text
Memory Orders
  ├─ calcola coerenza/health/riconciliazione
  └─ emette audit.vault.requested

Vault Keepers
  └─ persiste evidenze di audit in vault_audit_log

Orthodoxy Wardens
  └─ persiste verdetti epistemici in audit_findings
```

Questa separazione mantiene responsabilità chiare:
- Integrità memoria (Memory Orders)
- Accountability (Vault Keepers)
- Disciplina epistemica (Orthodoxy Wardens)

---

## 🚀 6) Perché è importante

Il Dual Memory Layer non è solo “Postgres + vettori”.  
Il valore è architetturale:

- mantiene il retrieval semantico agganciato alla verità canonica
- rende il drift visibile e governabile
- impone riconciliazioni sicure invece di fix ad-hoc
- fornisce auditabilità e accountability epistemica per contesti regolamentati

Questo rende Vitruvyan una **infrastruttura cognitiva governata**, non uno stack RAG generico.
