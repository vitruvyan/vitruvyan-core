"""Minimal contract conformance test template."""

from importlib import import_module


def test_intent_registry_factory_exists():
    module = import_module("vitruvyan_core.domains.example.intent_config")
    assert hasattr(module, "create_example_registry")


def test_manifest_exists():
    from pathlib import Path

    manifest = Path("vitruvyan_core/domains/example/vertical_manifest.yaml")
    assert manifest.exists()

