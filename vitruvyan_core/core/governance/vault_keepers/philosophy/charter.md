# Vault Keepers — Sacred Charter

> "Memoria non moritur. La verità preservata è verità eterna."

**Sacred Order:** Truth (Memory & Archival)  
**Founded:** Genesis  
**Sphere:** Integrity, Backup, Recovery, Audit

---

## Mission

The Vault Keepers are the **custodians of memory** in Vitruvyan OS. We guard the integrity of all stored knowledge, ensure data can be recovered from catastrophe, and maintain an immutable audit trail of all vault operations.

Our sacred duty: **Nothing is lost. Everything is recoverable. All actions are recorded.**

---

## Sacred Tenets

### 1. Integrity Above All
Data without integrity is noise. We validate perpetually, detect corruption early, and alert the system when truth is compromised.

**Practices:**
- Continuous integrity monitoring of PostgreSQL and Qdrant
- Cross-system coherence validation
- Blessing or cursing: every check yields a judgment

### 2. Redundancy is Reverence
A single copy is faith. Multiple copies are wisdom. We maintain snapshots, backups, and archives to ensure no knowledge is ever truly lost.

**Practices:**
- Full backups (PostgreSQL + Qdrant)
- Incremental backups for efficiency
- Long-term archival with retention policies

### 3. Recovery is Sacred Right
When corruption strikes, we restore order. Every snapshot is a lifeline; every restore is a resurrection.

**Practices:**
- Dry-run validation before real restores
- Guardian approval for critical restores
- Pre-restore integrity checks

### 4. Audit Trail is Eternal
Every vault operation leaves a mark. The Chamberlain records all actions, all decisions, all outcomes. History cannot be rewritten.

**Practices:**
- Immutable audit records for all operations
- Metadata-rich logs for compliance
- Retention: 2 years minimum

---

## Our Roles

### The Guardian
The **orchestrator**. The Guardian decides which roles to invoke, in what order, and with what priority. It sees the big picture and coordinates responses.

**Responsibilities:**
- Workflow orchestration
- Priority assessment
- Approval gates for critical operations

### The Sentinel
The **integrity validator**. The Sentinel judges the health of PostgreSQL, Qdrant, and their coherence. It blesses the sacred and curses the corrupted.

**Responsibilities:**
- Data integrity validation
- Corruption detection
- Health status judgments

### The Archivist
The **memory keeper**. The Archivist plans backups, creates snapshots, and stores archives. It knows what to save, when to save it, and how long to keep it.

**Responsibilities:**
- Backup planning
- Archive creation
- Retention policy enforcement

### The Chamberlain
The **record keeper**. The Chamberlain creates audit trails for every vault operation. Nothing escapes its ledger.

**Responsibilities:**
- Audit record creation
- Metadata tracking
- Compliance documentation

---

## Governance Rules

### Retention Policies
- **Snapshots:** 30 days (regular), 60 days (critical)
- **Archives:** 90 days (default), 365 days (critical/compliance)
- **Audit Records:** 730 days (2 years for compliance)

### Integrity Thresholds
- **Coherence Ratio:** ≥95% for "sacred" status, ≥85% for "blessed with concerns", <85% is "corruption detected"
- **Backup Priority:** High volatility + long time since backup = higher priority
- **Approval Requirements:** Real restores always require Guardian approval

### Backup Scheduling
- **Full Backups:** Every 24 hours
- **Incremental Backups:** Every 6 hours
- **Integrity Checks:** Before high-priority backups

---

## Integration with Other Orders

### Orthodoxy Wardens
We archive their judgments and decisions. Their verdicts are sacred; we ensure they are never lost.

### Codex Hunters
We backup their discoveries. Every mapped entity, every scraped news article, is preserved in our vaults.

### Memory Orders
We validate coherence between their RAG corpus and our Qdrant collections. We are the guardians of their long-term memory.

### Synaptic Conclave
We listen to the cognitive bus. Events flow through the Conclave, but memories are stored in our vaults.

---

## Sacred Channels

We emit events to the Synaptic Conclave on these channels:

- `vault.integrity.validated` — Integrity check completed
- `vault.backup.completed` — Snapshot created
- `vault.restore.completed` — Recovery executed
- `vault.archive.stored` — Content archived
- `vault.audit.recorded` — Audit trail updated

We listen for requests on:
- `vault.integrity.check.requested`
- `vault.backup.requested`
- `vault.restore.requested`
- `vault.archive.requested`

---

## Philosophy

Memory is not passive; it is **active guardianship**. We do not simply store data—we **validate it, protect it, and resurrect it when needed**.

Corruption is not failure; it is **signal**. When we detect corruption, we sound the alarm and guide recovery.

Audit trails are not bureaucracy; they are **epistemology**. Every action has consequences. Every consequence must be traceable.

**We are the watchers. We are the rememberers. We are the Vault Keepers.**

---

## Production Readiness Checklist

- ✅ LIVELLO 1 consumers implemented (Guardian, Sentinel, Archivist, Chamberlain)
- ✅ LIVELLO 1 governance rules defined (retention, thresholds, workflows)
- ✅ LIVELLO 2 bus adapter fully integrated with consumers
- ✅ LIVELLO 2 persistence layer with production operations
- ✅ Docker container validated and healthy
- ✅ StreamBus event emission working
- ✅ Audit trail creation functional
- ✅ Philosophy and charter documented

---

*Version: 2.0.0*  
*Aligned with SERVICE_PATTERN and SACRED_ORDER_PATTERN*  
*Production ready: February 2026*
