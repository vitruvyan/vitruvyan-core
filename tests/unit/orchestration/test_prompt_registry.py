"""
Test PromptRegistry — Registro Prompt Domain-Agnostic
======================================================

Test unitari per il registro centralizzato dei prompt.

Copertura:
  - register_domain()         → registrazione domini con template
  - get_identity()            → template identity con variabili template
  - get_scenario()            → scenari specifici con variabili
  - get_combined()            → identity + scenario combinati
  - list_domains/scenarios()  → elenchi
  - Traduzioni                → override per lingua
  - Edge cases                → dominio mancante, scenario mancante, variabili mancanti
  - clear()                   → reset per testing
  - Default domain            → fallback automatico

Dipendenze: ZERO. PromptRegistry è pura configurazione Python.

ATTENZIONE: PromptRegistry usa classmethods con stato globale.
Ogni test deve chiamare clear() nel setup per isolamento.
"""

import pytest


# ── Skip se il modulo non è importabile ──────────────────────────────────

try:
    from core.llm.prompts.registry import PromptRegistry, PromptConfig
    HAS_PROMPT = True
except ImportError:
    HAS_PROMPT = False

pytestmark = [
    pytest.mark.unit,
    pytest.mark.orchestration,
    pytest.mark.skipif(not HAS_PROMPT, reason="PromptRegistry not importable"),
]


# ═══════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def clean_registry():
    """Reset del registry prima di ogni test."""
    PromptRegistry.clear()
    yield
    PromptRegistry.clear()


@pytest.fixture
def registered_domain():
    """Registra un dominio di test."""
    PromptRegistry.register_domain(
        domain="test_domain",
        identity_template="You are {assistant_name}, expert in {domain_description}.",
        scenario_templates={
            "analysis": "Analyze the following: {subject}.",
            "summary": "Summarize {subject} in {length} words.",
        },
        template_vars=["assistant_name", "domain_description", "subject", "length"],
        version="2.0",
        set_as_default=True,
    )
    return "test_domain"


@pytest.fixture
def registered_with_translations():
    """Registra un dominio con traduzioni."""
    PromptRegistry.register_domain(
        domain="multilingual",
        identity_template="You are an assistant for {domain_description}.",
        scenario_templates={
            "greeting": "Welcome to {domain_description}.",
        },
        translations={
            "it": {
                "identity": "Sei un assistente per {domain_description}.",
                "scenario_greeting": "Benvenuto in {domain_description}.",
            },
        },
    )
    return "multilingual"


# ═══════════════════════════════════════════════════════════════════
# TEST: register_domain()
# ═══════════════════════════════════════════════════════════════════

class TestRegisterDomain:
    """Test per la registrazione di domini."""

    def test_register_domain(self, registered_domain):
        """Un dominio registrato deve essere listato."""
        assert "test_domain" in PromptRegistry.list_domains()

    def test_register_sets_default(self, registered_domain):
        """set_as_default=True deve impostare il dominio di default."""
        assert PromptRegistry.get_default_domain() == "test_domain"

    def test_first_domain_is_auto_default(self):
        """Il primo dominio registrato diventa automaticamente default."""
        PromptRegistry.register_domain(
            domain="first",
            identity_template="First",
            scenario_templates={},
        )
        assert PromptRegistry.get_default_domain() == "first"

    def test_register_overwrites(self):
        """Registrare lo stesso dominio sovrascrive la registrazione precedente."""
        PromptRegistry.register_domain(
            domain="x", identity_template="V1", scenario_templates={})
        PromptRegistry.register_domain(
            domain="x", identity_template="V2", scenario_templates={})
        identity = PromptRegistry.get_identity("x")
        assert identity == "V2"

    def test_list_scenarios(self, registered_domain):
        """list_scenarios() deve restituire gli scenari registrati."""
        scenarios = PromptRegistry.list_scenarios("test_domain")
        assert "analysis" in scenarios
        assert "summary" in scenarios


# ═══════════════════════════════════════════════════════════════════
# TEST: get_identity()
# ═══════════════════════════════════════════════════════════════════

class TestGetIdentity:
    """Test per get_identity()."""

    def test_identity_with_vars(self, registered_domain):
        """Le variabili template devono essere sostituite."""
        identity = PromptRegistry.get_identity(
            "test_domain",
            assistant_name="TestBot",
            domain_description="testing",
        )
        assert "TestBot" in identity
        assert "testing" in identity

    def test_identity_missing_var(self, registered_domain):
        """Con variabile mancante, il template resta non sostituito (no crash)."""
        identity = PromptRegistry.get_identity("test_domain")
        # Il template contiene {assistant_name} non sostituito
        assert "{assistant_name}" in identity or "assistant_name" in identity

    def test_identity_unknown_domain_with_default(self, registered_domain):
        """Un dominio sconosciuto con default impostato usa il default."""
        identity = PromptRegistry.get_identity("nonexistent")
        assert identity  # deve restituire qualcosa (il template del default)

    def test_identity_unknown_domain_no_default(self):
        """Un dominio sconosciuto senza default solleva ValueError."""
        with pytest.raises(ValueError, match="not registered"):
            PromptRegistry.get_identity("nonexistent")


# ═══════════════════════════════════════════════════════════════════
# TEST: get_scenario()
# ═══════════════════════════════════════════════════════════════════

class TestGetScenario:
    """Test per get_scenario()."""

    def test_scenario_with_vars(self, registered_domain):
        """Le variabili devono essere sostituite nel template dello scenario."""
        result = PromptRegistry.get_scenario(
            "test_domain", "analysis",
            subject="entity X",
        )
        assert "entity X" in result

    def test_scenario_unknown_raises(self, registered_domain):
        """Uno scenario inesistente deve sollevare ValueError."""
        with pytest.raises(ValueError, match="Unknown scenario"):
            PromptRegistry.get_scenario("test_domain", "nonexistent")

    def test_scenario_missing_var(self, registered_domain):
        """Con variabile mancante, il template resta non sostituito."""
        result = PromptRegistry.get_scenario("test_domain", "summary")
        # {subject} e {length} non sostituiti
        assert "{subject}" in result or "subject" in result


# ═══════════════════════════════════════════════════════════════════
# TEST: get_combined()
# ═══════════════════════════════════════════════════════════════════

class TestGetCombined:
    """Test per get_combined() — identity + scenario."""

    def test_combined_contains_both(self, registered_domain):
        """Il combined deve contenere sia identity che scenario."""
        result = PromptRegistry.get_combined(
            "test_domain", "analysis",
            assistant_name="Bot",
            domain_description="testing",
            subject="entity X",
        )
        assert "Bot" in result
        assert "entity X" in result
        assert "SCENARIO" in result  # separatore

    def test_combined_unknown_scenario_raises(self, registered_domain):
        """Scenario inesistente in combined deve sollevare ValueError."""
        with pytest.raises(ValueError):
            PromptRegistry.get_combined("test_domain", "nonexistent")


# ═══════════════════════════════════════════════════════════════════
# TEST: Translations
# ═══════════════════════════════════════════════════════════════════

class TestTranslations:
    """Test per le traduzioni dei prompt."""

    def test_italian_identity(self, registered_with_translations):
        """Identity in italiano deve usare la traduzione."""
        result = PromptRegistry.get_identity(
            "multilingual", language="it",
            domain_description="test",
        )
        assert "Sei un assistente" in result

    def test_english_identity_default(self, registered_with_translations):
        """Identity in inglese deve usare il template base."""
        result = PromptRegistry.get_identity(
            "multilingual", language="en",
            domain_description="test",
        )
        assert "You are an assistant" in result

    def test_italian_scenario(self, registered_with_translations):
        """Scenario in italiano deve usare la traduzione."""
        result = PromptRegistry.get_scenario(
            "multilingual", "greeting", language="it",
            domain_description="test",
        )
        assert "Benvenuto" in result

    def test_unknown_language_falls_back(self, registered_with_translations):
        """Una lingua sconosciuta deve restituire il template base (en)."""
        result = PromptRegistry.get_identity(
            "multilingual", language="de",
            domain_description="test",
        )
        assert "You are an assistant" in result


# ═══════════════════════════════════════════════════════════════════
# TEST: clear()
# ═══════════════════════════════════════════════════════════════════

class TestClear:
    """Test per il reset del registry."""

    def test_clear_removes_domains(self, registered_domain):
        """clear() deve rimuovere tutti i domini."""
        assert len(PromptRegistry.list_domains()) > 0
        PromptRegistry.clear()
        assert PromptRegistry.list_domains() == []

    def test_clear_resets_default(self, registered_domain):
        """clear() deve resettare il default domain."""
        PromptRegistry.clear()
        assert PromptRegistry.get_default_domain() is None


# ═══════════════════════════════════════════════════════════════════
# TEST: PromptConfig immutability
# ═══════════════════════════════════════════════════════════════════

class TestPromptConfig:
    """Test per PromptConfig."""

    def test_prompt_config_frozen(self):
        """PromptConfig deve essere immutabile (frozen=True)."""
        config = PromptConfig(domain="test")
        with pytest.raises(AttributeError):
            config.domain = "changed"  # type: ignore
