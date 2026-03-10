"""
Test — Contract enforcement modes (warn / strict / off).

Verifies the @enforced decorator respects the ENFORCE_CONTRACTS env var.

Markers: unit
"""

import pytest
import logging
from unittest.mock import patch

from core.orchestration.contract_enforcement import (
    enforced,
    ContractViolationError,
)


def _make_node(requires=None, produces=None, name="test"):
    """Build a decorated identity node."""

    @enforced(requires=requires, produces=produces, node_name=name)
    def node(state):
        return state

    return node


class TestWarnMode:
    """Default mode — log warnings, do not raise."""

    @patch.dict("os.environ", {"ENFORCE_CONTRACTS": "warn"})
    def test_missing_requires_logs_warning(self, caplog):
        node = _make_node(requires={"input_text"}, name="parse")
        with caplog.at_level(logging.WARNING):
            result = node({"other_key": "v"})
        assert result == {"other_key": "v"}
        assert "REQUIRES missing keys" in caplog.text

    @patch.dict("os.environ", {"ENFORCE_CONTRACTS": "warn"})
    def test_missing_produces_logs_warning(self, caplog):
        node = _make_node(produces={"route"}, name="decide")
        with caplog.at_level(logging.WARNING):
            result = node({"something": "else"})
        assert "PRODUCES missing keys" in caplog.text

    @patch.dict("os.environ", {"ENFORCE_CONTRACTS": "warn"})
    def test_satisfied_contract_no_warning(self, caplog):
        node = _make_node(requires={"a"}, produces={"a"}, name="ok")
        with caplog.at_level(logging.WARNING):
            node({"a": 1})
        assert "missing keys" not in caplog.text


class TestStrictMode:
    """Strict mode — raise ContractViolationError on violations."""

    @patch.dict("os.environ", {"ENFORCE_CONTRACTS": "strict"})
    def test_missing_requires_raises(self):
        node = _make_node(requires={"input_text"}, name="parse")
        with pytest.raises(ContractViolationError, match="REQUIRES missing keys"):
            node({"other": "v"})

    @patch.dict("os.environ", {"ENFORCE_CONTRACTS": "strict"})
    def test_missing_produces_raises(self):
        node = _make_node(produces={"route"}, name="decide")
        with pytest.raises(ContractViolationError, match="PRODUCES missing keys"):
            node({"other": "v"})

    @patch.dict("os.environ", {"ENFORCE_CONTRACTS": "strict"})
    def test_satisfied_contract_passes(self):
        node = _make_node(requires={"a"}, produces={"a"}, name="ok")
        result = node({"a": 1})
        assert result == {"a": 1}


class TestOffMode:
    """Off mode — disable all checks, zero overhead."""

    @patch.dict("os.environ", {"ENFORCE_CONTRACTS": "off"})
    def test_missing_requires_ignored(self):
        node = _make_node(requires={"input_text"}, name="parse")
        result = node({"other": "v"})
        assert result == {"other": "v"}

    @patch.dict("os.environ", {"ENFORCE_CONTRACTS": "off"})
    def test_missing_produces_ignored(self):
        node = _make_node(produces={"route"}, name="decide")
        result = node({"other": "v"})
        assert result == {"other": "v"}


class TestEmptyContracts:
    """Empty requires/produces — decorator is a no-op."""

    def test_no_requires_no_produces_returns_original(self):
        @enforced()
        def node(state):
            return state

        # With empty sets, decorator returns the original function
        result = node({"any": "state"})
        assert result == {"any": "state"}
