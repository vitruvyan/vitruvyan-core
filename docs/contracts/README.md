# Contracts

Canonical documentation for Vitruvyan contracts.

This section defines the stable interfaces used to keep core modules domain-agnostic and vertical modules pluggable.

## Scope

- Core contracts namespace: `vitruvyan_core/contracts/`
- Vertical contract model and templates
- Governance rules for contract-first development

## Core Contracts (v1.8.0)

| Contract | File | Version | Owner |
|----------|------|---------|-------|
| `BaseContract` | `contracts/base.py` | 1.0.0 | core |
| `ContractRegistry` | `contracts/base.py` | 1.0.0 | core |
| `IContractPlugin` | `contracts/base.py` | 1.0.0 | core |
| `SourceDescriptor` | `contracts/ingestion.py` | 1.0.0 | perception |
| `IngestionQuality` | `contracts/ingestion.py` | 1.0.0 | perception |
| `IngestionPayload` | `contracts/ingestion.py` | 1.0.0 | perception |
| `IIngestionPlugin` | `contracts/ingestion.py` | 1.0.0 | perception |
| `OntologyPayload` | `contracts/pattern_weavers.py` | 3.0.0 | pattern_weavers |
| `ComprehensionResult` | `contracts/comprehension.py` | 1.0.0 | babel_gardens |
| `GraphResponseMin` | `contracts/graph_response.py` | 1.0.0 | core |
| `SessionMin` | `contracts/graph_response.py` | 1.0.0 | core |

## References

- Python package: `vitruvyan_core/contracts/__init__.py`
- KB developer guide: `docs/knowledge_base/governance/contracts.md`
- Vertical contract docs: `docs/contracts/verticals/README.md`
- Platform contract docs: `docs/contracts/platform/README.md`
- Pipeline contract enforcement: `docs/contracts/platform/PIPELINE_CONTRACT_ENFORCEMENT.md`
