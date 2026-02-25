"""Tests for finance taxonomy YAML loading."""

from pathlib import Path

from core.cognitive.pattern_weavers.domain.config import TaxonomyConfig


def test_taxonomy_finance_yaml_loads():
    yaml_path = Path(__file__).resolve().parents[1] / "taxonomy_finance.yaml"
    taxonomy = TaxonomyConfig.from_yaml(yaml_path)
    assert taxonomy.categories


def test_taxonomy_contains_expected_categories():
    yaml_path = Path(__file__).resolve().parents[1] / "taxonomy_finance.yaml"
    taxonomy = TaxonomyConfig.from_yaml(yaml_path)
    assert "sectors" in taxonomy.categories
    assert "instruments" in taxonomy.categories
    assert "regions" in taxonomy.categories


def test_technology_keywords_present():
    yaml_path = Path(__file__).resolve().parents[1] / "taxonomy_finance.yaml"
    taxonomy = TaxonomyConfig.from_yaml(yaml_path)
    sectors = taxonomy.get_category("sectors")
    technology = next((item for item in sectors if item.name == "Technology"), None)
    assert technology is not None
    assert "tech" in [kw.lower() for kw in technology.keywords]
