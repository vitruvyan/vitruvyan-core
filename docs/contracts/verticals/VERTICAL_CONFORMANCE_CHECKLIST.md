# Vertical Conformance Checklist

Status: active
Contract Version: Vertical Contract V1

## A. Structure

- [ ] `vitruvyan_core/domains/<domain_name>/intent_config.py` exists
- [ ] `vitruvyan_core/domains/<domain_name>/README.md` exists
- [ ] `vitruvyan_core/domains/<domain_name>/vertical_manifest.yaml` exists
- [ ] Optional production files are present when required (`graph_plugin.py`, `governance_rules.py`, etc.)

## B. Contract Usage

- [ ] Imports use `contracts` / `vitruvyan_core.contracts`
- [ ] No imports from deprecated contract namespaces
- [ ] Plugin interfaces are implemented where declared in manifest

## C. Architecture Boundary

- [ ] No domain business logic added to core modules
- [ ] Sacred Orders remain domain-agnostic
- [ ] LangGraph extension is plugin-based
- [ ] Neural Engine domain behavior is contract-based

## D. Governance

- [ ] Governance rules are defined for sensitive use-cases
- [ ] Orthodoxy/Vault boundaries are respected
- [ ] Data classification assumptions documented

## E. Testing

- [ ] Contract conformance tests pass
- [ ] Intent registry load test passes
- [ ] Manifest validation test passes
- [ ] Integration tests pass (if required by manifest)

## F. Manifest

- [ ] `domain_name` is set and consistent with folder name
- [ ] `contract_version` matches expected policy version
- [ ] `required_components` and `adapters` are complete
- [ ] `ownership` fields are complete
- [ ] `compliance.status` is updated

## G. Release Decision

- [ ] No open MUST violation
- [ ] No unresolved expired derogation
- [ ] CI conformance gate is green

