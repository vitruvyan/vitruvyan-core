"""
Tests for contract_enforcement.py — @enforced decorator.

Pure Python, no I/O, no infrastructure dependencies.
"""

import os
import pytest
from unittest.mock import patch

# Must set env BEFORE import (import-time read)
# Each test that needs a specific mode re-imports with patch


def _import_fresh(mode: str = "warn"):
    """Import contract_enforcement with a specific mode (fresh module)."""
    import importlib
    os.environ["CONTRACT_ENFORCE_MODE"] = mode
    import vitruvyan_core.core.orchestration.contract_enforcement as mod
    importlib.reload(mod)
    return mod


class TestEnforcedWarnMode:
    """Tests with CONTRACT_ENFORCE_MODE=warn (default)."""

    def setup_method(self):
        self.mod = _import_fresh("warn")
        self.mod.reset_violation_count()

    def test_happy_path_no_violations(self):
        """Node satisfies all requires/produces — no violation."""
        @self.mod.enforced(requires=["input_text"], produces=["intent"])
        def my_node(state):
            return {**state, "intent": "greeting"}

        result = my_node({"input_text": "hello"})
        assert result["intent"] == "greeting"
        assert self.mod.get_violation_count() == 0

    def test_missing_required_field_warns(self):
        """Missing required field logs warning, does not raise."""
        @self.mod.enforced(requires=["input_text"], produces=["intent"])
        def my_node(state):
            return {**state, "intent": "unknown"}

        result = my_node({})  # input_text missing
        assert result["intent"] == "unknown"
        assert self.mod.get_violation_count() == 1

    def test_missing_produced_field_warns(self):
        """Node omits a declared produced field — warns."""
        @self.mod.enforced(requires=[], produces=["intent", "route"])
        def my_node(state):
            return {**state, "intent": "greeting"}  # route missing

        result = my_node({"input_text": "hello"})
        assert self.mod.get_violation_count() == 1

    def test_none_required_field_warns(self):
        """Field present but None counts as missing."""
        @self.mod.enforced(requires=["input_text"], produces=[])
        def my_node(state):
            return state

        my_node({"input_text": None})
        assert self.mod.get_violation_count() == 1

    def test_type_check_warns_on_mismatch(self):
        """Wrong type in required field — warns."""
        @self.mod.enforced(
            requires=["input_text"],
            produces=[],
            validate_types={"input_text": str},
        )
        def my_node(state):
            return state

        my_node({"input_text": 42})  # int instead of str
        assert self.mod.get_violation_count() == 1

    def test_violations_accumulate(self):
        """Multiple calls accumulate violation count."""
        @self.mod.enforced(requires=["x"], produces=[])
        def my_node(state):
            return state

        my_node({})
        my_node({})
        my_node({"x": "ok"})
        assert self.mod.get_violation_count() == 2

    def test_contract_metadata_attached(self):
        """Wrapped function has _contract attribute for introspection."""
        @self.mod.enforced(requires=["a"], produces=["b"])
        def my_node(state):
            return state

        assert hasattr(my_node, "_contract")
        assert my_node._contract.requires == ["a"]
        assert my_node._contract.produces == ["b"]

    def test_node_name_from_function(self):
        """Node name defaults to function name."""
        @self.mod.enforced(requires=["x"], produces=[])
        def intent_detection_node(state):
            return state

        # The wrapper should preserve function name via functools.wraps
        assert intent_detection_node.__name__ == "intent_detection_node"

    def test_custom_node_name(self):
        """Explicit node_name overrides function name in logs."""
        @self.mod.enforced(
            requires=["x"], produces=[], node_name="custom_name"
        )
        def my_fn(state):
            return state

        # Just ensure it doesn't crash — name used internally for logging
        my_fn({})
        assert self.mod.get_violation_count() == 1


class TestEnforcedStrictMode:
    """Tests with CONTRACT_ENFORCE_MODE=strict."""

    def setup_method(self):
        self.mod = _import_fresh("strict")
        self.mod.reset_violation_count()

    def test_missing_required_raises(self):
        """Missing required field raises ContractViolationError."""
        @self.mod.enforced(requires=["input_text"], produces=[])
        def my_node(state):
            return state

        with pytest.raises(self.mod.ContractViolationError) as exc_info:
            my_node({})

        assert exc_info.value.phase == "pre"
        assert "input_text" in exc_info.value.missing_fields

    def test_missing_produced_raises(self):
        """Missing produced field raises ContractViolationError."""
        @self.mod.enforced(requires=[], produces=["result"])
        def my_node(state):
            return state  # "result" not in return

        with pytest.raises(self.mod.ContractViolationError) as exc_info:
            my_node({})

        assert exc_info.value.phase == "post"
        assert "result" in exc_info.value.missing_fields

    def test_type_error_raises(self):
        """Type mismatch in strict mode raises."""
        @self.mod.enforced(
            requires=["input_text"],
            produces=[],
            validate_types={"input_text": str},
        )
        def my_node(state):
            return state

        with pytest.raises(self.mod.ContractViolationError) as exc_info:
            my_node({"input_text": 123})

        assert exc_info.value.phase == "pre"
        assert "input_text" in exc_info.value.type_errors

    def test_happy_path_no_raise(self):
        """Conformant node does not raise even in strict mode."""
        @self.mod.enforced(
            requires=["input_text"],
            produces=["intent"],
            validate_types={"input_text": str, "intent": str},
        )
        def my_node(state):
            return {**state, "intent": "greeting"}

        result = my_node({"input_text": "hello"})
        assert result["intent"] == "greeting"


class TestEnforcedOffMode:
    """Tests with CONTRACT_ENFORCE_MODE=off."""

    def setup_method(self):
        self.mod = _import_fresh("off")
        self.mod.reset_violation_count()

    def test_off_returns_original_function(self):
        """Off mode returns the original function — zero wrapping."""
        def my_node(state):
            return state

        wrapped = self.mod.enforced(requires=["x"], produces=["y"])(my_node)
        assert wrapped is my_node  # same object, no wrapper

    def test_off_no_violations(self):
        """Off mode does not track violations."""
        @self.mod.enforced(requires=["x"], produces=["y"])
        def my_node(state):
            return state

        my_node({})
        assert self.mod.get_violation_count() == 0


class TestContractViolationError:
    """Test the exception class itself."""

    def test_error_message_format(self):
        err = _import_fresh("warn").ContractViolationError(
            "test_node", "pre", missing_fields=["a", "b"]
        )
        assert "test_node" in str(err)
        assert "pre" in str(err)
        assert "a" in str(err)

    def test_error_with_type_errors(self):
        err = _import_fresh("warn").ContractViolationError(
            "node_x", "post", type_errors={"field1": "expected str, got int"}
        )
        assert "type_errors" in str(err)
        assert "field1" in str(err)


class TestNodeContractSpec:
    """Test the NodeContractSpec dataclass."""

    def test_frozen(self):
        mod = _import_fresh("warn")
        spec = mod.NodeContractSpec(
            requires=["a"], produces=["b"]
        )
        with pytest.raises(AttributeError):
            spec.requires = ["c"]

    def test_defaults(self):
        mod = _import_fresh("warn")
        spec = mod.NodeContractSpec()
        assert spec.requires == []
        assert spec.produces == []
        assert spec.validate_types == {}
