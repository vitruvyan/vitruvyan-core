"""
Test IntentRegistry — Registro Intent Domain-Agnostic
======================================================

Test unitari per il registro di intent configurabile.

Copertura:
  - Registrazione intent       → register_intent(), _register_core_intents()
  - Registrazione filtri       → register_filter()
  - Normalizzazione            → normalize_intent() con sinonimi e direct match
  - Costruzione prompt         → build_classification_prompt(), build_intent_list_for_prompt()
  - Parsing risposta           → parse_classification_response()
  - Edge cases                 → intent sconosciuti, filtri "null", collisioni sinonimi

Dipendenze: ZERO. IntentRegistry è pura configurazione Python.
"""

import pytest
from unittest.mock import MagicMock


# ── Skip se il modulo non è importabile ──────────────────────────────────

try:
    from core.orchestration.intent_registry import (
        IntentRegistry, IntentDefinition, ScreeningFilter,
        create_generic_registry,
    )
    HAS_INTENT = True
except ImportError:
    HAS_INTENT = False

pytestmark = [
    pytest.mark.unit,
    pytest.mark.orchestration,
    pytest.mark.skipif(not HAS_INTENT, reason="IntentRegistry not importable"),
]


# ═══════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def registry():
    """Registry generico con intent core (soft, unknown)."""
    return IntentRegistry(domain_name="test_domain")


@pytest.fixture
def registry_with_intents():
    """Registry con intent personalizzati."""
    reg = IntentRegistry(domain_name="test_domain")
    reg.register_intent(IntentDefinition(
        name="analyze",
        description="Deep analysis of an entity",
        examples=["Analyze entity X", "Show me analysis of Y"],
        synonyms=["study", "review", "examine"],
        requires_entities=True,
    ))
    reg.register_intent(IntentDefinition(
        name="compare",
        description="Compare two entities",
        examples=["Compare A vs B", "A versus B"],
        synonyms=["versus", "vs"],
        requires_entities=True,
    ))
    return reg


@pytest.fixture
def registry_with_filters():
    """Registry con filtri."""
    reg = IntentRegistry(domain_name="test_domain")
    reg.register_filter(ScreeningFilter(
        name="priority",
        description="Priority level",
        value_type="enum",
        enum_values=["low", "medium", "high"],
        keywords=["urgent", "important"],
    ))
    reg.register_filter(ScreeningFilter(
        name="detailed",
        description="Include details",
        value_type="bool",
        keywords=["detailed", "full", "complete"],
    ))
    return reg


# ═══════════════════════════════════════════════════════════════════
# TEST: Core intents (auto-registrati)
# ═══════════════════════════════════════════════════════════════════

class TestCoreIntents:
    """Test per gli intent registrati automaticamente."""

    def test_soft_intent_exists(self, registry):
        """L'intent 'soft' deve essere auto-registrato."""
        assert registry.get_intent("soft") is not None

    def test_unknown_intent_exists(self, registry):
        """L'intent 'unknown' deve essere auto-registrato."""
        assert registry.get_intent("unknown") is not None

    def test_core_intent_labels(self, registry):
        """get_intent_labels() deve includere soft e unknown."""
        labels = registry.get_intent_labels()
        assert "soft" in labels
        assert "unknown" in labels

    def test_soft_has_synonyms(self, registry):
        """L'intent 'soft' deve avere sinonimi (greeting, emotion)."""
        intent = registry.get_intent("soft")
        assert "greeting" in intent.synonyms or "emotion" in intent.synonyms


# ═══════════════════════════════════════════════════════════════════
# TEST: register_intent()
# ═══════════════════════════════════════════════════════════════════

class TestRegisterIntent:
    """Test per la registrazione di intent personalizzati."""

    def test_register_intent(self, registry):
        """Un intent registrato deve essere recuperabile."""
        registry.register_intent(IntentDefinition(
            name="diagnose",
            description="System diagnosis",
            examples=["Check system health"],
        ))
        intent = registry.get_intent("diagnose")
        assert intent is not None
        assert intent.name == "diagnose"

    def test_register_with_synonyms(self, registry_with_intents):
        """I sinonimi devono essere indicizzati."""
        # "study" è sinonimo di "analyze"
        normalized = registry_with_intents.normalize_intent("study")
        assert normalized == "analyze"

    def test_register_overwrites_existing(self, registry):
        """Registrare un intent con lo stesso nome sovrascrive il precedente."""
        registry.register_intent(IntentDefinition(
            name="analyze", description="Version 1"))
        registry.register_intent(IntentDefinition(
            name="analyze", description="Version 2"))
        intent = registry.get_intent("analyze")
        assert intent.description == "Version 2"

    def test_get_nonexistent_intent(self, registry):
        """get_intent() per un intent inesistente deve restituire None."""
        assert registry.get_intent("nonexistent") is None


# ═══════════════════════════════════════════════════════════════════
# TEST: register_filter()
# ═══════════════════════════════════════════════════════════════════

class TestRegisterFilter:
    """Test per la registrazione di filtri."""

    def test_register_filter(self, registry_with_filters):
        """Un filtro registrato deve essere recuperabile."""
        f = registry_with_filters.get_filter("priority")
        assert f is not None
        assert f.value_type == "enum"

    def test_filter_names(self, registry_with_filters):
        """get_filter_names() deve elencare i filtri registrati."""
        names = registry_with_filters.get_filter_names()
        assert "priority" in names
        assert "detailed" in names

    def test_get_nonexistent_filter(self, registry):
        """get_filter() per un filtro inesistente deve restituire None."""
        assert registry.get_filter("nonexistent") is None


# ═══════════════════════════════════════════════════════════════════
# TEST: normalize_intent()
# ═══════════════════════════════════════════════════════════════════

class TestNormalizeIntent:
    """Test per la normalizzazione degli intent."""

    def test_direct_match(self, registry_with_intents):
        """Direct match per nome canonico."""
        assert registry_with_intents.normalize_intent("analyze") == "analyze"

    def test_synonym_match(self, registry_with_intents):
        """Match per sinonimo."""
        assert registry_with_intents.normalize_intent("study") == "analyze"
        assert registry_with_intents.normalize_intent("examine") == "analyze"

    def test_case_insensitive(self, registry_with_intents):
        """La normalizzazione deve essere case-insensitive."""
        assert registry_with_intents.normalize_intent("ANALYZE") == "analyze"
        assert registry_with_intents.normalize_intent("Study") == "analyze"

    def test_strips_whitespace(self, registry_with_intents):
        """La normalizzazione deve rimuovere spazi."""
        assert registry_with_intents.normalize_intent("  analyze  ") == "analyze"

    def test_unknown_intent_returns_unknown(self, registry_with_intents):
        """Un intent sconosciuto deve restituire 'unknown'."""
        assert registry_with_intents.normalize_intent("gibberish") == "unknown"

    def test_empty_string_returns_unknown(self, registry_with_intents):
        """Stringa vuota deve restituire 'unknown'."""
        assert registry_with_intents.normalize_intent("") == "unknown"

    def test_core_synonym_greeting(self, registry):
        """'greeting' deve normalizzarsi a 'soft'."""
        assert registry.normalize_intent("greeting") == "soft"


# ═══════════════════════════════════════════════════════════════════
# TEST: build_classification_prompt()
# ═══════════════════════════════════════════════════════════════════

class TestBuildPrompt:
    """Test per la costruzione del prompt GPT."""

    def test_prompt_contains_user_input(self, registry_with_intents):
        """Il prompt deve contenere l'input utente."""
        prompt = registry_with_intents.build_classification_prompt("what is entity X?")
        assert "what is entity X?" in prompt

    def test_prompt_contains_intent_list(self, registry_with_intents):
        """Il prompt deve elencare gli intent registrati."""
        prompt = registry_with_intents.build_classification_prompt("test")
        assert "analyze" in prompt
        assert "compare" in prompt
        assert "soft" in prompt

    def test_prompt_contains_domain_name(self, registry_with_intents):
        """Il prompt deve menzionare il nome del dominio."""
        prompt = registry_with_intents.build_classification_prompt("test")
        assert "test_domain" in prompt

    def test_prompt_with_filters(self, registry_with_filters):
        """Con filtri, il prompt deve contenere la sezione filtri."""
        prompt = registry_with_filters.build_classification_prompt("test")
        assert "priority" in prompt
        assert "detailed" in prompt

    def test_prompt_without_filters(self, registry_with_intents):
        """Senza filtri, il prompt non deve avere la sezione filtri."""
        prompt = registry_with_intents.build_classification_prompt(
            "test", include_filters=True
        )
        # No filters registered in registry_with_intents
        assert "EXTRACT FILTERS" not in prompt

    def test_prompt_with_examples(self, registry_with_intents):
        """Il prompt deve includere gli esempi degli intent."""
        prompt = registry_with_intents.build_classification_prompt(
            "test", include_examples=True
        )
        assert "Analyze entity X" in prompt

    def test_prompt_without_examples(self, registry_with_intents):
        """Senza esempi, la sezione EXAMPLES non ci deve essere o è vuota."""
        prompt = registry_with_intents.build_classification_prompt(
            "test", include_examples=False
        )
        assert "EXAMPLES:" not in prompt

    def test_prompt_json_format(self, registry_with_intents):
        """Il prompt deve richiedere output JSON."""
        prompt = registry_with_intents.build_classification_prompt("test")
        assert '"intent"' in prompt
        assert "JSON" in prompt


# ═══════════════════════════════════════════════════════════════════
# TEST: parse_classification_response()
# ═══════════════════════════════════════════════════════════════════

class TestParseResponse:
    """Test per il parsing della risposta GPT."""

    def test_parse_known_intent(self, registry_with_intents):
        """Un intent noto deve essere normalizzato correttamente."""
        intent, filters = registry_with_intents.parse_classification_response(
            {"intent": "analyze"}
        )
        assert intent == "analyze"
        assert filters == {}

    def test_parse_synonym(self, registry_with_intents):
        """Un sinonimo deve essere normalizzato all'intent canonico."""
        intent, filters = registry_with_intents.parse_classification_response(
            {"intent": "study"}
        )
        assert intent == "analyze"

    def test_parse_unknown_intent(self, registry_with_intents):
        """Un intent sconosciuto deve diventare 'unknown'."""
        intent, filters = registry_with_intents.parse_classification_response(
            {"intent": "xyz123"}
        )
        assert intent == "unknown"

    def test_parse_missing_intent_key(self, registry_with_intents):
        """Se manca la chiave 'intent', deve usare 'unknown'."""
        intent, filters = registry_with_intents.parse_classification_response({})
        assert intent == "unknown"

    def test_parse_extracts_filters(self, registry_with_filters):
        """I filtri nella risposta devono essere estratti."""
        intent, filters = registry_with_filters.parse_classification_response(
            {"intent": "soft", "priority": "high", "detailed": True}
        )
        assert filters["priority"] == "high"
        assert filters["detailed"] is True

    def test_parse_null_filter_excluded(self, registry_with_filters):
        """Filtri con valore None o "null" devono essere esclusi."""
        intent, filters = registry_with_filters.parse_classification_response(
            {"intent": "soft", "priority": None, "detailed": "null"}
        )
        assert "priority" not in filters
        assert "detailed" not in filters

    def test_parse_non_registered_filter_ignored(self, registry_with_filters):
        """Chiavi non registrate come filtri devono essere ignorate."""
        intent, filters = registry_with_filters.parse_classification_response(
            {"intent": "soft", "extra_field": "value"}
        )
        assert "extra_field" not in filters


# ═══════════════════════════════════════════════════════════════════
# TEST: Factory function
# ═══════════════════════════════════════════════════════════════════

class TestFactory:
    """Test per create_generic_registry()."""

    def test_factory_returns_registry(self):
        reg = create_generic_registry()
        assert isinstance(reg, IntentRegistry)

    def test_factory_has_core_intents(self):
        reg = create_generic_registry()
        assert reg.get_intent("soft") is not None
        assert reg.get_intent("unknown") is not None

    def test_factory_domain_name(self):
        reg = create_generic_registry()
        assert reg.domain_name == "generic"
