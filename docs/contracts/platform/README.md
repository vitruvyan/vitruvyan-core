# Platform Contracts

Platform-level contracts (update system, telemetry, health).

## Active Contracts

- [UPDATE_SYSTEM_CONTRACT_V1.md](UPDATE_SYSTEM_CONTRACT_V1.md) - Core update/upgrade system (vit CLI)
- [DOCS_FEDERATION_CONTRACT_V1.md](DOCS_FEDERATION_CONTRACT_V1.md) - Cross-VPS docs routing + MkDocs indexing contract

---

**Purpose**: Enforce platform behavior guarantees across Core and Verticals.

**Enforcement**: CI/CD gates, runtime validation (`vit` tool).
