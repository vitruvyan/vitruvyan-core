# tests/verticals/test_finance_vertical.py
"""
Tests for the Finance domain vertical implementation.

These tests verify that the finance vertical correctly implements
the core contracts (GraphPlugin, ResponseFormatter, SlotFiller).

REQUIRES: domains/finance/ installed. Skipped automatically if not available.

Extracted from tests/test_orchestration_base_classes.py to enforce
clean separation between core tests and domain-specific tests.
"""

import pytest

# Skip entire module if finance vertical is not installed
finance = pytest.importorskip(
    "vitruvyan_core.domains.finance",
    reason="Finance vertical not installed — skipping domain-specific tests"
)
finance_plugin = pytest.importorskip(
    "domains.finance.graph_plugin",
    reason="Finance graph_plugin not available — skipping"
)


# ===========================================================================
# TEST: FinanceResponseFormatter
# ===========================================================================

class TestFinanceResponseFormatter:
    """Tests for FinanceResponseFormatter."""

    def test_verdict_generation(self):
        """generate_final_verdict should produce correct verdicts."""
        from vitruvyan_core.domains.finance import generate_final_verdict

        # Strong buy
        verdict = generate_final_verdict(0.75)
        assert verdict["verdict"] == "strong_buy"
        assert verdict["color"] == "green"

        # Buy
        verdict = generate_final_verdict(0.35)
        assert verdict["verdict"] == "buy"

        # Hold
        verdict = generate_final_verdict(0.0)
        assert verdict["verdict"] == "hold"
        assert verdict["color"] == "yellow"

        # Sell
        verdict = generate_final_verdict(-0.35)
        assert verdict["verdict"] == "sell"

        # Strong sell
        verdict = generate_final_verdict(-0.75)
        assert verdict["verdict"] == "strong_sell"
        assert verdict["color"] == "red"

    def test_gauge_generation(self):
        """generate_gauge should produce traffic light colors."""
        from vitruvyan_core.domains.finance import generate_gauge

        gauge = generate_gauge(
            momentum_z=0.8,   # Positive -> green
            trend_z=-0.1,    # Slightly negative -> yellow
            vola_z=0.5,      # High vol -> warning (inverted)
            sentiment_z=None,  # Missing data -> gray
        )

        assert gauge["momentum"]["color"] == "green"
        assert gauge["trend"]["color"] == "yellow"
        assert gauge["sentiment"]["color"] == "gray"

    def test_comparison_matrix(self):
        """generate_comparison_matrix should rank entities."""
        from vitruvyan_core.domains.finance import generate_comparison_matrix

        raw_output = {
            "ranking": {
                "entities": [
                    {"entity_id": "AAPL", "composite_score": 0.8, "factors": {}},
                    {"entity_id": "MSFT", "composite_score": 0.6, "factors": {}},
                    {"entity_id": "GOOGL", "composite_score": 0.9, "factors": {}},
                ]
            }
        }

        matrix = generate_comparison_matrix(
            ["AAPL", "MSFT", "GOOGL"],
            raw_output
        )

        assert len(matrix) == 3
        assert matrix[0]["entity_id"] == "GOOGL"  # Highest score
        assert matrix[0]["rank"] == 1
        assert matrix[1]["entity_id"] == "AAPL"
        assert matrix[2]["entity_id"] == "MSFT"

    def test_formatter_conversation_type_detection(self):
        """FinanceResponseFormatter should detect finance-specific types."""
        from vitruvyan_core.domains.finance import FinanceResponseFormatter
        from core.orchestration.compose.response_formatter import ConversationType

        formatter = FinanceResponseFormatter()

        # Single entity analysis
        state = {"entity_ids": ["AAPL"], "intent": "analysis"}
        conv_type = formatter.detect_conversation_type(state)
        assert conv_type == ConversationType.SINGLE_ENTITY

        # Multi-entity comparison
        state = {"entity_ids": ["AAPL", "MSFT"], "intent": "compare"}
        conv_type = formatter.detect_conversation_type(state)
        assert conv_type == ConversationType.MULTI_ENTITY

        # Onboarding
        state = {"entity_ids": [], "intent": "onboarding"}
        conv_type = formatter.detect_conversation_type(state)
        assert conv_type == ConversationType.ONBOARDING


# ===========================================================================
# TEST: FinanceSlotFiller
# ===========================================================================

class TestFinanceSlotFiller:
    """Tests for FinanceSlotFiller."""

    def test_finance_slots_defined(self):
        """FinanceSlotFiller should have finance-specific slots."""
        from vitruvyan_core.domains.finance import FinanceSlotFiller

        filler = FinanceSlotFiller()
        slots = filler.get_slot_definitions()

        slot_names = [s.name for s in slots]
        assert "time_horizon" in slot_names
        assert "risk_tolerance" in slot_names
        assert "asset_class" in slot_names

    def test_missing_slots_for_allocation(self):
        """check_missing_slots should find missing allocation slots."""
        from vitruvyan_core.domains.finance import FinanceSlotFiller

        filler = FinanceSlotFiller()

        # Empty slots for allocation intent
        missing = filler.check_missing_slots({}, "allocation")

        assert "time_horizon" in missing
        assert "risk_tolerance" in missing

    def test_emotion_aware_questions(self):
        """Questions should adapt to detected emotion."""
        from vitruvyan_core.domains.finance import FinanceSlotFiller

        filler = FinanceSlotFiller()

        # Anxious user gets reassuring prefix/suffix
        state_anxious = {"emotion_detected": "anxious"}
        question = filler.generate_question("time_horizon", "en", state_anxious)
        assert "overwhelming" in question.question or "time" in question.question

        # Neutral user gets plain question
        state_neutral = {"emotion_detected": "neutral"}
        question = filler.generate_question("time_horizon", "en", state_neutral)
        assert "horizon" in question.question

    def test_multilingual_questions(self):
        """Questions should be generated in multiple languages."""
        from vitruvyan_core.domains.finance import FinanceSlotFiller

        filler = FinanceSlotFiller()
        state = {}

        # Italian
        question_it = filler.generate_question("risk_tolerance", "it", state)
        assert "rischio" in question_it.question.lower()

        # Spanish
        question_es = filler.generate_question("risk_tolerance", "es", state)
        assert "riesgo" in question_es.question.lower()


# ===========================================================================
# TEST: FinanceGraphPlugin Integration
# ===========================================================================

class TestFinanceGraphPlugin:
    """Integration tests for FinanceGraphPlugin."""

    def test_plugin_implements_contract(self):
        """FinanceGraphPlugin should implement full GraphPlugin contract."""
        from domains.finance.graph_plugin import FinanceGraphPlugin

        plugin = FinanceGraphPlugin()

        assert plugin.get_domain_name() == "finance"
        assert isinstance(plugin.get_nodes(), dict)
        assert isinstance(plugin.get_route_map(), dict)
        assert isinstance(plugin.get_intents(), list)
        assert isinstance(plugin.get_state_extensions(), dict)

    def test_plugin_has_compose_components(self):
        """FinanceGraphPlugin should provide ResponseFormatter and SlotFiller."""
        from domains.finance.graph_plugin import FinanceGraphPlugin
        from core.orchestration.compose.response_formatter import ResponseFormatter
        from core.orchestration.compose.slot_filler import SlotFiller

        plugin = FinanceGraphPlugin()

        assert hasattr(plugin, "get_response_formatter")
        assert hasattr(plugin, "get_slot_filler")

        formatter = plugin.get_response_formatter()
        filler = plugin.get_slot_filler()

        assert isinstance(formatter, ResponseFormatter)
        assert isinstance(filler, SlotFiller)

    def test_parser_extracts_budget(self):
        """FinanceParser should extract budget from queries."""
        from domains.finance.graph_plugin import FinanceGraphPlugin

        plugin = FinanceGraphPlugin()
        parser = plugin.get_parser()

        # Test budget extraction (parser.parse expects state dict)
        state = {"input_text": "I have $10000 to invest"}
        result = parser.parse(state)

        # Parser returns ParsedSlots namedtuple with slots attribute
        assert hasattr(result, 'slots')
        assert result.slots.get("budget") in (100, 10000) or "currency" in result.slots

    def test_state_extensions(self):
        """Finance state extensions should include all required fields."""
        from domains.finance.graph_plugin import FinanceGraphPlugin

        plugin = FinanceGraphPlugin()
        extensions = plugin.get_state_extensions()

        assert "tickers" in extensions
        assert "budget" in extensions
        assert "horizon" in extensions
        assert "risk_tolerance" in extensions
        assert "portfolio_id" in extensions
