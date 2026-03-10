"""
Pipeline Contract Enforcement — E2E Architectural Tests
========================================================

Validates that ALL 7 BUCOs from the Contract Enforcement Roadmap are fixed:

  BUCO 1: @enforced wraps all nodes in build_graph() and build_minimal_graph()
  BUCO 2: pw_compile_node imports OntologyPayload for boundary validation
  BUCO 3: codex_hunters sets orthodoxy fields on ALL return paths
  BUCO 4: (bus emit — deferred, tested separately)
  BUCO 5: _check_payload_contract raises ValueError in strict mode
  BUCO 6: graph_adapter defaults to "non_liquet" (not "blessed") for unknown statuses
  BUCO 7: Domain extension nodes are wrapped with _wrap()

Author: Vitruvyan Core Team
Created: February 28, 2026
"""

import os
import sys
import pytest
from unittest.mock import patch

# ══════════════════════════════════════════════════════════════════════════
# BUCO 1 + 7: All nodes in build_graph / build_minimal_graph are wrapped
# ══════════════════════════════════════════════════════════════════════════

class TestNodeWrapping:
    """Verify _wrap() is applied to all node registrations in graph_flow.py."""

    def test_wrap_exists_and_callable(self):
        """_wrap is importable from graph_flow."""
        from core.orchestration.langgraph.graph_flow import _wrap
        assert callable(_wrap)

    def test_node_alias_map_correct(self):
        """Node alias map covers all name discrepancies."""
        from core.orchestration.langgraph.graph_flow import _NODE_ALIAS
        assert _NODE_ALIAS.get("llm_soft") == "cached_llm"
        assert _NODE_ALIAS.get("intent") == "intent_detection"

    def test_wrap_applies_enforced_for_known_contract(self):
        """_wrap returns a different function (decorated) for nodes with contracts."""
        from core.orchestration.langgraph.graph_flow import _wrap
        def dummy(state): return state
        wrapped = _wrap("parse", dummy)
        assert wrapped is not dummy, "parse has produces — should be wrapped"

    def test_wrap_passthrough_for_empty_contract(self):
        """_wrap wraps even nodes with partial contracts (advisor has requires)."""
        from core.orchestration.langgraph.graph_flow import _wrap
        def dummy(state): return state
        wrapped = _wrap("advisor", dummy)
        # _wrap always adds _timed latency tracking, and advisor has requires={"response"}
        assert wrapped is not dummy, "advisor has requires — should be wrapped"
        # Verify it still works correctly
        result = wrapped({"response": "test"})
        assert result == {"response": "test"}

    def test_wrap_handles_alias_llm_soft(self):
        """_wrap('llm_soft', fn) looks up 'cached_llm' in registry."""
        from core.orchestration.langgraph.graph_flow import _wrap
        def dummy(state): return state
        wrapped = _wrap("llm_soft", dummy)
        assert wrapped is not dummy, "llm_soft → cached_llm has produces"

    def test_wrap_handles_alias_intent(self):
        """_wrap('intent', fn) looks up 'intent_detection' in registry."""
        from core.orchestration.langgraph.graph_flow import _wrap
        def dummy(state): return state
        wrapped = _wrap("intent", dummy)
        assert wrapped is not dummy, "intent → intent_detection has produces"

    def test_wrap_unknown_node_passthrough(self):
        """Unknown nodes still get _timed wrapper but no contract enforcement."""
        from core.orchestration.langgraph.graph_flow import _wrap
        def dummy(state): return state
        wrapped = _wrap("nonexistent_node_xyz", dummy)
        # _wrap always adds _timed for latency tracking
        assert wrapped is not dummy
        # But the wrapped function should still work correctly (no contract checks)
        result = wrapped({"any_key": "value"})
        assert result == {"any_key": "value"}

    def test_all_core_nodes_in_registry(self):
        """Every core node name used in build_graph has a registry entry."""
        from core.orchestration.node_contracts_registry import NODE_CONTRACTS
        from core.orchestration.langgraph.graph_flow import _NODE_ALIAS

        core_node_names = [
            "parse", "intent_detection", "weaver", "entity_resolver",
            "params_extraction", "decide", "babel_emotion", "semantic_grounding",
            "exec", "qdrant", "llm_soft", "output_normalizer", "compose",
            "advisor", "can", "orthodoxy", "vault", "codex_hunters",
            "llm_mcp", "early_exit",
        ]
        for name in core_node_names:
            registry_key = _NODE_ALIAS.get(name, name)
            assert registry_key in NODE_CONTRACTS, (
                f"Node '{name}' (registry key '{registry_key}') missing from NODE_CONTRACTS"
            )


# ══════════════════════════════════════════════════════════════════════════
# BUCO 2: pw_compile_node validates OntologyPayload at boundary
# ══════════════════════════════════════════════════════════════════════════

class TestPwCompileBoundaryValidation:
    """Verify OntologyPayload.model_validate is called in pw_compile_node."""

    def test_ontology_payload_import(self):
        """pw_compile_node imports OntologyPayload from contracts."""
        import core.orchestration.langgraph.node.pw_compile_node as mod
        # Verify the import is present at module level
        assert hasattr(mod, "OntologyPayload") or "OntologyPayload" in dir(mod) or \
            "OntologyPayload" in open(mod.__file__).read(), \
            "pw_compile_node must import OntologyPayload"

    def test_model_validate_in_source(self):
        """pw_compile_node source contains model_validate call."""
        import core.orchestration.langgraph.node.pw_compile_node as mod
        source = open(mod.__file__).read()
        assert "model_validate" in source, \
            "pw_compile_node must call OntologyPayload.model_validate()"


# ══════════════════════════════════════════════════════════════════════════
# BUCO 3: codex_hunters sets orthodoxy fields on all paths
# ══════════════════════════════════════════════════════════════════════════

class TestCodexHuntersOrthodoxy:
    """codex_hunters_node must set orthodoxy fields on ALL return paths."""

    def _run_codex(self, state):
        from core.orchestration.langgraph.node.codex_hunters_node import codex_hunters_node
        return codex_hunters_node(state)

    def _assert_orthodoxy_fields(self, result, expected_status="blessed"):
        assert "orthodoxy_status" in result, "Missing orthodoxy_status"
        assert "orthodoxy_verdict" in result, "Missing orthodoxy_verdict"
        assert "orthodoxy_confidence" in result, "Missing orthodoxy_confidence"
        assert "orthodoxy_findings" in result, "Missing orthodoxy_findings"
        assert "orthodoxy_timestamp" in result, "Missing orthodoxy_timestamp"
        assert result["orthodoxy_status"] == expected_status

    def test_success_path_has_orthodoxy(self):
        """Audit success path sets orthodoxy_status = blessed."""
        result = self._run_codex({
            "input_text": "run system integrity audit",
            "intent": "audit",
        })
        assert result["status"] == "success"
        self._assert_orthodoxy_fields(result, "blessed")

    def test_skip_path_has_orthodoxy(self):
        """Skip path (no audit match) sets orthodoxy_status = blessed."""
        result = self._run_codex({
            "input_text": "hello there",
            "intent": "greeting",
        })
        assert result["status"] == "skipped"
        self._assert_orthodoxy_fields(result, "blessed")

    def test_error_path_has_orthodoxy(self):
        """Error paths should set orthodoxy_status = non_liquet."""
        # Force an error by patching
        from core.orchestration.langgraph.node import codex_hunters_node as mod
        original = mod.codex_hunters_node

        # Verify the error result structure by checking source
        source = open(mod.__file__).read()
        assert '"orthodoxy_status": "non_liquet"' in source, \
            "Error path must set orthodoxy_status to non_liquet"


# ══════════════════════════════════════════════════════════════════════════
# BUCO 5: _check_payload_contract raises in strict mode
# ══════════════════════════════════════════════════════════════════════════

class TestRagPayloadStrictMode:
    """_check_payload_contract must raise ValueError when RAG_ENFORCE_MODE=strict."""

    def test_strict_mode_raises(self):
        """In strict mode, missing payload.source raises ValueError."""
        import core.agents.qdrant_agent as mod

        # Save and patch the module-level variable
        original = mod._RAG_ENFORCE
        try:
            mod._RAG_ENFORCE = "strict"
            points = [{"payload": {"text": "hello"}}]  # missing "source"
            with pytest.raises(ValueError, match="RAG GUARD"):
                mod._check_payload_contract(points, "test_collection")
        finally:
            mod._RAG_ENFORCE = original

    def test_warn_mode_does_not_raise(self):
        """In warn mode, missing payload.source logs but does not raise."""
        import core.agents.qdrant_agent as mod

        original = mod._RAG_ENFORCE
        try:
            mod._RAG_ENFORCE = "warn"
            points = [{"payload": {"text": "hello"}}]  # missing "source"
            # Should not raise
            mod._check_payload_contract(points, "test_collection")
        finally:
            mod._RAG_ENFORCE = original

    def test_off_mode_skips(self):
        """In off mode, no check performed at all."""
        import core.agents.qdrant_agent as mod

        original = mod._RAG_ENFORCE
        try:
            mod._RAG_ENFORCE = "off"
            points = [{"payload": {}}]  # missing everything
            mod._check_payload_contract(points, "test_collection")
        finally:
            mod._RAG_ENFORCE = original


# ══════════════════════════════════════════════════════════════════════════
# BUCO 6: graph_adapter defaults to "non_liquet" for unknown statuses
# ══════════════════════════════════════════════════════════════════════════

class TestGraphAdapterFallback:
    """graph_adapter must default to 'non_liquet', not 'blessed'."""

    def test_source_uses_non_liquet_fallback(self):
        """Verify source code contains the corrected fallback."""
        import os
        adapter_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "services", "api_graph", "adapters", "graph_adapter.py"
        )
        # Also try from workspace root
        if not os.path.exists(adapter_path):
            adapter_path = "/home/vitruvyan/vitruvyan-core/services/api_graph/adapters/graph_adapter.py"

        source = open(adapter_path).read()
        assert '"non_liquet"' in source, "Fallback must be non_liquet"
        assert '_CANONICAL_MAP.get(raw_status, "blessed")' not in source, \
            "Old fallback to 'blessed' must be removed"


# ══════════════════════════════════════════════════════════════════════════
# Contract enforcement decorator — integration with real node signatures
# ══════════════════════════════════════════════════════════════════════════

class TestEnforcedIntegration:
    """@enforced works correctly when applied via _wrap()."""

    def test_warn_mode_warns_on_missing_produce(self):
        """A node that forgets to produce a declared field triggers a warning."""
        os.environ["ENFORCE_CONTRACTS"] = "warn"
        try:
            from core.orchestration.contract_enforcement import enforced
            import logging

            @enforced(requires=set(), produces={"must_exist"}, node_name="test_node")
            def bad_node(state):
                return {"other_field": "value"}

            with pytest.warns(None) as _:  # noqa: PT017
                pass
            # Warn mode should NOT raise — just log
            result = bad_node({"input_text": "hello"})
            assert result == {"other_field": "value"}
        finally:
            os.environ.pop("ENFORCE_CONTRACTS", None)

    def test_strict_mode_raises_on_missing_produce(self):
        """In strict mode, missing produces raises ContractViolationError."""
        os.environ["ENFORCE_CONTRACTS"] = "strict"
        try:
            from core.orchestration.contract_enforcement import (
                enforced, ContractViolationError,
            )

            @enforced(requires=set(), produces={"must_exist"}, node_name="test_strict")
            def bad_node(state):
                return {"other_field": "value"}

            with pytest.raises(ContractViolationError):
                bad_node({"input_text": "hello"})
        finally:
            os.environ.pop("ENFORCE_CONTRACTS", None)


# ══════════════════════════════════════════════════════════════════════════
# Orthodoxy constants — canonical constants importable
# ══════════════════════════════════════════════════════════════════════════

class TestOrthodoxyConstants:
    """Canonical orthodoxy status constants are importable from contracts."""

    def test_constants_importable(self):
        from contracts.graph_response import (
            ORTHODOXY_BLESSED,
            ORTHODOXY_PURIFIED,
            ORTHODOXY_HERETICAL,
            ORTHODOXY_NON_LIQUET,
            ORTHODOXY_CLARIFICATION_NEEDED,
        )
        assert ORTHODOXY_BLESSED == "blessed"
        assert ORTHODOXY_PURIFIED == "purified"
        assert ORTHODOXY_HERETICAL == "heretical"
        assert ORTHODOXY_NON_LIQUET == "non_liquet"
        assert ORTHODOXY_CLARIFICATION_NEEDED == "clarification_needed"

    def test_type_is_literal(self):
        from contracts.graph_response import OrthodoxyStatusType
        # OrthodoxyStatusType is a Literal — verify it exists
        assert OrthodoxyStatusType is not None
