# Vertical Conformance Checklist

Status: active
Contract Version: Vertical Contract V1.1
Last Updated: 2026-03-15

## A. Structure

- [ ] `vitruvyan_core/domains/<domain_name>/intent_config.py` exists
- [ ] `vitruvyan_core/domains/<domain_name>/prompts/__init__.py` exists with `register_<domain>_prompts()`
- [ ] `vitruvyan_core/domains/<domain_name>/graph_nodes/registry.py` exists with `get_<domain>_graph_nodes()`
- [ ] `vitruvyan_core/domains/<domain_name>/governance_rules.py` exists
- [ ] `vitruvyan_core/domains/<domain_name>/README.md` exists
- [ ] `vitruvyan_core/domains/<domain_name>/vertical_manifest.yaml` exists
- [ ] `graph_plugin.py` is NOT used (deprecated, use `graph_nodes/registry.py`)

## B. Sacred Orders Domain Packs (Contract §13)

- [ ] `pattern_weavers/taxonomy_<domain>.yaml` exists and loads
- [ ] `pattern_weavers/weave_config.py` exists
- [ ] `babel_gardens/signals_<domain>.yaml` exists and loads
- [ ] `babel_gardens/<domain>_context.py` exists
- [ ] `orthodoxy_wardens/compliance_config.py` exists
- [ ] `memory_orders/<domain>_config.py` exists (if domain has persistent data)
- [ ] `vault_keepers/<domain>_config.py` exists (if domain has persistent data)
- [ ] Neural Engine contracts implemented (if domain has structured scoring)

## C. Contract Usage

- [ ] Imports use `contracts` / `vitruvyan_core.contracts`
- [ ] No imports from deprecated contract namespaces
- [ ] Plugin interfaces are implemented where declared in manifest

## D. Architecture Boundary

- [ ] No domain business logic added to core modules
- [ ] Sacred Orders remain domain-agnostic (domain logic in packs only)
- [ ] LangGraph extension is plugin-based via `graph_nodes/registry.py`
- [ ] Custom nodes are loaded through domain hook modules (not by editing core nodes)
- [ ] Neural Engine domain behavior is contract-based (if applicable)

## E. Governance

- [ ] Governance rules are defined for sensitive use-cases
- [ ] Orthodoxy/Vault boundaries are respected
- [ ] Data classification assumptions documented

## F. Testing

- [ ] Contract conformance tests pass
- [ ] Intent registry load test passes
- [ ] Manifest validation test passes
- [ ] Sacred Orders domain pack load tests pass (taxonomy, signals, rules)
- [ ] Integration tests pass (if required by manifest)
- [ ] If `graph_nodes` adapter is enabled, graph compile/runtime smoke test passes

## G. Manifest

- [ ] `domain_name` is set and consistent with folder name
- [ ] `contract_version` matches `1.1.0`
- [ ] `required_components` and `adapters` are complete
- [ ] `sacred_orders_packs` section is complete
- [ ] `ownership` fields are complete
- [ ] `compliance.status` is updated

## H. Release Decision

- [ ] No open MUST violation
- [ ] No unresolved expired derogation
- [ ] All Sacred Orders domain packs present and loadable
- [ ] CI conformance gate is green
