# Vault Keepers

> **Memory Custodians — Pure Domain Layer (LIVELLO 1)**

Foundational module for data integrity, backup, recovery, and audit operations. Guards the sanctity of stored knowledge across PostgreSQL and Qdrant systems.

## Sacred Order

**Domain**: Truth (Memory & Archival)  
**Mandate**: Integrity monitoring, backup/recovery, immutable audit trails  
**Layer**: LIVELLO 1 (Pure Domain — No I/O, No Infrastructure)

---

## Quick Start

```python
from vitruvyan_core.core.governance.vault_keepers.domain.vault_objects import IntegrityReport, VaultSnapshot
from vitruvyan_core.core.governance.vault_keepers.consumers.sentinel import Sentinel
from vitruvyan_core.core.governance.vault_keepers.consumers.archivist import Archivist

# Pure integrity validation (no database required)
sentinel = Sentinel()
integrity_input = {
    "operation": "integrity_check",
    "target": "postgresql",
    "scope": "full",
    "sample_size": 1000
}
report = sentinel.process(integrity_input)

print(f"Status: {report.status}")  # 'blessed' or 'cursed'
print(f"Corruption detected: {report.corruption_detected}")  # False
print(f"Records checked: {report.records_checked}")  # 1000

# Pure backup metadata creation
archivist = Archivist()
backup_input = {
    "operation": "create_backup",
    "type": "full",
    "systems": ["postgresql", "qdrant"]
}
snapshot = archivist.process(backup_input)

print(f"Snapshot: {snapshot.snapshot_id}")  # 'snapshot_20260210_100000'
print(f"Scope: {snapshot.scope}")  # 'full'
print(f"Status: {snapshot.status}")  # 'completed'
```

---

## Architecture

### Two-Level Pattern

| Level | Location | Purpose | Dependencies |
|-------|----------|---------|--------------|
| **LIVELLO 1** | `vitruvyan_core/core/governance/vault_keepers/` | Pure domain logic | None (stdlib only) |
| **LIVELLO 2** | `services/api_vault_keepers/` | Infrastructure, API, Docker | PostgreSQL, Qdrant, Redis |

**Direction: service → core** (ONE-WAY). LIVELLO 2 imports LIVELLO 1, never reverse.

### Domain Model

```
IntegrityCheck ──validate──▶ IntegrityReport
BackupRequest ──create──▶ VaultSnapshot
RecoveryPlan ──execute──▶ RecoveryResult
```

### Core Components

- **Sentinel**: Validates data integrity, detects corruption
- **Archivist**: Creates and manages backup snapshots
- **Guardian**: Oversees recovery operations
- **Chamberlain**: Maintains immutable audit trails

---

## Domain Objects

### IntegrityReport
```python
@dataclass(frozen=True)
class IntegrityReport:
    report_id: str
    target_system: str
    scope: str
    records_checked: int
    corruption_detected: bool
    corruption_rate: float
    status: str  # 'blessed' or 'cursed'
    timestamp: str
    evidence: tuple
```

### VaultSnapshot
```python
@dataclass(frozen=True)
class VaultSnapshot:
    snapshot_id: str
    timestamp: str
    scope: str
    postgresql_backup_path: Optional[str]
    qdrant_backup_path: Optional[str]
    size_bytes: int
    status: str
    metadata: tuple
```

---

## Consumers (Pure Functions)

All consumers implement the `VaultRole` interface:

```python
class VaultRole(ABC):
    @property
    def role_name(self) -> str: ...
    
    @property  
    def description(self) -> str: ...
    
    def can_handle(self, event: Any) -> bool: ...
    
    def process(self, input_data: Any) -> Any: ...
```

### Available Roles
- **Sentinel**: Integrity validation and corruption detection
- **Archivist**: Backup creation and snapshot management
- **Guardian**: Recovery planning and validation
- **Chamberlain**: Audit logging and trail maintenance

---

## Events & Channels

Vault operations emit events to the Cognitive Bus:

- `vault.integrity.checked` — Integrity validation completed
- `vault.backup.created` — Backup snapshot created
- `vault.recovery.completed` — Recovery operation finished
- `vault.audit.logged` — Audit entry recorded

---

## Philosophy

*"Memoria non moritur. La verità preservata è verità eterna."*

Vault Keepers embody four sacred tenets:

1. **Integrity Above All** — Perpetual validation, early corruption detection
2. **Redundancy is Reverence** — Multiple copies ensure nothing is lost
3. **Recovery is Sacred Right** — Resurrection from catastrophe
4. **Audit Trail is Eternal** — Immutable record of all operations

---

## Testing

Run unit tests (no infrastructure required):
```bash
cd vitruvyan_core/core/governance/vault_keepers
pytest tests/
```

---

## Related Components

- **Service Layer**: `services/api_vault_keepers/` — REST API and infrastructure
- **Agents**: `core.agents.postgres_agent`, `core.agents.qdrant_agent` — Data persistence
- **Bus**: `core.synaptic_conclave.transport.streams.StreamBus` — Event publishing</content>
<parameter name="filePath">/home/vitruvyan/vitruvyan-core/vitruvyan_core/core/governance/vault_keepers/README.md