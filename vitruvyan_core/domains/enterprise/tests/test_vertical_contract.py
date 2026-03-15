"""
Enterprise Domain — Contract Conformance Tests
================================================

Minimal contract conformance tests per VERTICAL_CONTRACT_V1.

MUST:
- intent_config.py exists with create_enterprise_registry
- vertical_manifest.yaml exists
- README.md exists
- Registry loads without errors
- All declared intents are registered

Vertical: Enterprise
Contract: VERTICAL_CONTRACT_V1
"""

from importlib import import_module
from pathlib import Path


DOMAIN = "enterprise"
DOMAIN_PATH = Path(__file__).parent.parent


def test_intent_registry_factory_exists():
    """MUST: create_enterprise_registry factory function exists."""
    module = import_module(f"vitruvyan_core.domains.{DOMAIN}.intent_config")
    assert hasattr(module, f"create_{DOMAIN}_registry")


def test_intent_registry_loads():
    """MUST: Registry loads without errors and has intents."""
    module = import_module(f"vitruvyan_core.domains.{DOMAIN}.intent_config")
    factory = getattr(module, f"create_{DOMAIN}_registry")
    registry = factory()
    assert registry.domain_name == DOMAIN
    assert len(list(registry.get_all_intents())) > 0


def test_manifest_exists():
    """MUST: vertical_manifest.yaml exists."""
    manifest = DOMAIN_PATH / "vertical_manifest.yaml"
    assert manifest.exists(), f"Missing {manifest}"


def test_readme_exists():
    """MUST: README.md exists."""
    readme = DOMAIN_PATH / "README.md"
    assert readme.exists(), f"Missing {readme}"


def test_context_keywords_defined():
    """SHOULD: CONTEXT_KEYWORDS dict is defined for professional boundary enforcement."""
    module = import_module(f"vitruvyan_core.domains.{DOMAIN}.intent_config")
    assert hasattr(module, "CONTEXT_KEYWORDS")
    ctx = module.CONTEXT_KEYWORDS
    assert isinstance(ctx, dict)
    assert len(ctx) > 0


def test_ambiguous_patterns_defined():
    """SHOULD: AMBIGUOUS_PATTERNS list is defined for out-of-scope detection."""
    module = import_module(f"vitruvyan_core.domains.{DOMAIN}.intent_config")
    assert hasattr(module, "AMBIGUOUS_PATTERNS")
    patterns = module.AMBIGUOUS_PATTERNS
    assert isinstance(patterns, list)


def test_manifest_domain_name_matches():
    """MUST: domain_name in manifest matches folder name."""
    import yaml
    manifest_path = DOMAIN_PATH / "vertical_manifest.yaml"
    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)
    assert manifest["domain_name"] == DOMAIN


def test_governance_rules_loadable():
    """SHOULD: governance_rules.py loads and returns rules list."""
    module = import_module(f"vitruvyan_core.domains.{DOMAIN}.governance_rules")
    assert hasattr(module, "get_domain_rules")
    rules = module.get_domain_rules()
    assert isinstance(rules, list)


def test_graph_plugin_loadable():
    """SHOULD: graph_plugin.py loads and returns a GraphPlugin."""
    module = import_module(f"vitruvyan_core.domains.{DOMAIN}.graph_plugin")
    assert hasattr(module, f"get_{DOMAIN}_plugin")
    plugin = getattr(module, f"get_{DOMAIN}_plugin")()
    assert plugin.get_domain_name() == DOMAIN
