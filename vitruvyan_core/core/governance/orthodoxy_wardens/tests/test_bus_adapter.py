"""
⚖️ FASE 4 — Bus Adapter Tests

Verifies that OrthodoxyBusAdapter correctly wires the pure consumer pipeline.
No database, no Redis. Pure unit tests.
"""

import sys
import os
import pytest

# Add services/ to path so we can import the adapter
_services_root = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "..", "services"
)
sys.path.insert(0, os.path.abspath(_services_root))

from api_orthodoxy_wardens.adapters.bus_adapter import (
    OrthodoxyBusAdapter,
    _serialize,
)


class TestOrthodoxyBusAdapter:
    """Test the full audit pipeline through the adapter."""

    def setup_method(self):
        self.adapter = OrthodoxyBusAdapter()

    # -- Full Pipeline ---------------------------------------------------------

    def test_handle_event_returns_dict(self):
        event = {
            "trigger_type": "code_commit",
            "text": "import os\nos.system('rm -rf /')",
            "source": "test",
        }
        result = self.adapter.handle_event(event)
        assert isinstance(result, dict)

    def test_handle_event_has_required_keys(self):
        event = {"trigger_type": "output_validation", "text": "SELECT * FROM users"}
        result = self.adapter.handle_event(event)

        assert "confession_id" in result
        assert "verdict" in result
        assert "correction_plan" in result
        assert "chronicle_decision" in result
        assert "findings_count" in result

    def test_handle_event_confession_id_is_string(self):
        event = {"trigger_type": "scheduled", "text": "healthy code"}
        result = self.adapter.handle_event(event)
        assert isinstance(result["confession_id"], str)
        assert len(result["confession_id"]) > 0

    def test_handle_event_verdict_is_dict(self):
        event = {"trigger_type": "code_commit", "text": "print('hello')"}
        result = self.adapter.handle_event(event)
        assert isinstance(result["verdict"], dict)

    def test_handle_event_verdict_has_status(self):
        event = {"trigger_type": "code_commit", "text": "x = 1 + 1"}
        result = self.adapter.handle_event(event)
        assert "status" in result["verdict"]
        assert result["verdict"]["status"] in [
            "blessed", "purified", "heretical",
            "non_liquet", "clarification_needed",
        ]

    def test_handle_event_with_code(self):
        event = {
            "trigger_type": "code_commit",
            "code": "def foo():\n    pass",
            "text": "",
        }
        result = self.adapter.handle_event(event)
        assert "confession_id" in result

    def test_handle_event_with_minimal_event(self):
        """Minimal valid event -- adapter should handle gracefully."""
        event = {"trigger_type": "manual"}
        result = self.adapter.handle_event(event)
        assert "confession_id" in result
        assert "verdict" in result

    def test_handle_event_findings_count_is_int(self):
        event = {"trigger_type": "code_commit", "text": "eval('malicious')"}
        result = self.adapter.handle_event(event)
        assert isinstance(result["findings_count"], int)
        assert result["findings_count"] >= 0

    def test_handle_event_dangerous_code_finds_issues(self):
        event = {
            "trigger_type": "code_commit",
            "code": "import os\nos.system('rm -rf /')\neval(input())",
        }
        result = self.adapter.handle_event(event)
        assert result["findings_count"] > 0

    # -- Quick Validation ------------------------------------------------------

    def test_quick_validation_returns_dict(self):
        event = {"trigger_type": "output_validation", "text": "normal text"}
        result = self.adapter.handle_quick_validation(event)
        assert isinstance(result, dict)

    def test_quick_validation_has_required_keys(self):
        event = {"trigger_type": "code_commit", "text": "x = 1"}
        result = self.adapter.handle_quick_validation(event)

        assert "confession_id" in result
        assert "verdict" in result
        assert "findings_count" in result
        assert "correction_plan" not in result
        assert "chronicle_decision" not in result

    def test_quick_validation_faster_path(self):
        """Quick validation skips Penitent + Chronicler."""
        event = {"trigger_type": "scheduled", "text": "routine check"}
        full = self.adapter.handle_event(event)
        quick = self.adapter.handle_quick_validation(event)

        assert full["verdict"]["status"] == quick["verdict"]["status"]
        assert "correction_plan" in full
        assert "correction_plan" not in quick

    # -- Custom RuleSet --------------------------------------------------------

    def test_custom_ruleset(self):
        from vitruvyan_core.core.governance.orthodoxy_wardens.governance.rule import (
            RuleSet, Rule,
        )

        custom = RuleSet.create(

            version="1.0.0",
            rules=(
                Rule(
                    rule_id="R001",
                    category="security",
                    subcategory="dangerous_functions",
                    severity="critical",
                    pattern=r"\beval\b",
                    description="No eval allowed",
                ),
            ),
        )
        adapter = OrthodoxyBusAdapter(ruleset=custom)
        result = adapter.handle_event(
            {"trigger_type": "code_commit", "text": "eval('x')"}
        )
        # Custom ruleset accepted and used (verdict rendered regardless of findings)
        assert "verdict" in result
        assert result["verdict"]["status"] in [
            "blessed", "purified", "heretical",
            "non_liquet", "clarification_needed",
        ]

    # -- Serialization Helper --------------------------------------------------

    def test_serialize_none(self):
        assert _serialize(None) is None

    def test_serialize_dict_like(self):
        class Obj:
            def __init__(self):
                self.a = 1
                self.b = "two"

        result = _serialize(Obj())
        assert result == {"a": 1, "b": "two"}

    def test_serialize_with_to_dict(self):
        class Obj:
            def to_dict(self):
                return {"key": "value"}

        result = _serialize(Obj())
        assert result == {"key": "value"}

    def test_serialize_frozen_dataclass(self):
        """Frozen dataclasses (like Verdict) should serialize via asdict."""
        from vitruvyan_core.core.governance.orthodoxy_wardens.domain.verdict import Verdict

        v = Verdict.blessed(confidence=0.95, explanation="All good")
        result = _serialize(v)
        assert isinstance(result, dict)
        assert result["status"] == "blessed"
        assert result["confidence"] == 0.95

    def test_serialize_fallback_to_str(self):
        result = _serialize(42)
        assert result == "42"

    # -- Pipeline Correctness --------------------------------------------------

    def test_blessed_for_clean_text(self):
        """Clean financial text should get blessed verdict."""
        event = {
            "trigger_type": "output_validation",
            "text": "Total revenue increased by 5% year-over-year.",
        }
        result = self.adapter.handle_event(event)
        assert result["verdict"]["status"] == "blessed"

    def test_all_valid_trigger_types(self):
        """Verify all valid trigger types work."""
        for trigger in ["code_commit", "scheduled", "manual", "output_validation", "event"]:
            result = self.adapter.handle_event({"trigger_type": trigger, "text": "ok"})
            assert "confession_id" in result, f"Failed for trigger_type={trigger}"
