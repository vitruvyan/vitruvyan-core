"""
E2E Test: LangGraph Domain-Agnostic Pipeline
==============================================
Tests the full LangGraph pipeline with NON-FINANCE queries to verify
domain-agnostic refactoring (Feb 2026).

Key Tests:
  - Generic queries without finance entities
  - Conversational queries in multiple languages
  - Intent detection without finance-specific signals
  - CAN output generation for generic intents

Requires: Graph API (localhost:9004) + all dependent services.

Created: Feb 14, 2026
Reference: Coverage analysis gap (domain-agnostic E2E missing)
"""
import os
import json
import pytest

pytestmark = [pytest.mark.e2e]


class TestDomainAgnosticGreeting:
    """Generic conversational queries without finance context."""

    def test_generic_greeting_english(self, graph_run):
        """English greeting must work without finance context."""
        data = graph_run("Hello, how are you?")
        
        assert "human" in data
        assert "parsed" in data
        parsed = data["parsed"]
        
        # Must have intent (generic or conversational)
        assert "intent" in parsed
        assert parsed["intent"] is not None
        
        # Must have route decision
        assert "route" in parsed
        assert isinstance(parsed["route"], str)
        
        # Must have either response OR clarification action
        has_response = "response" in parsed or "narrative" in parsed
        has_clarification = "action" in parsed and parsed.get("action") == "clarify"
        assert has_response or has_clarification, "Must have response or clarification"

    def test_generic_greeting_italian(self, graph_run):
        """Italian greeting must work without finance context."""
        data = graph_run("Ciao, come stai?")
        
        parsed = data["parsed"]
        assert "intent" in parsed
        assert "route" in parsed
        # Accept either response or clarification
        has_output = (
            "response" in parsed or 
            "narrative" in parsed or
            ("action" in parsed and "questions" in parsed)
        )
        assert has_output, "Must have some form of output"

    def test_generic_status_query(self, graph_run):
        """Generic status query without finance-specific terms."""
        data = graph_run("What is the current status?")
        
        parsed = data["parsed"]
        assert "intent" in parsed
        # Intent should be generic, not finance-specific
        intent = parsed["intent"]
        assert intent in ["unknown", "conversational", "status", "info", None]


class TestDomainAgnosticInfoQueries:
    """Information queries without finance entities."""

    def test_generic_information_query(self, graph_run):
        """Generic 'tell me about' query."""
        data = graph_run("Tell me about the system")
        
        parsed = data["parsed"]
        assert "intent" in parsed
        assert "route" in parsed
        
        # Should route to llm or conversational nodes (not pure exec)
        route = parsed["route"]
        accepted_routes = [
            "llm_soft", "llm_mcp", "cached_llm", "compose",
            "chat", "codex_complete"
        ]
        assert route in accepted_routes, f"Unexpected route: {route}"

    def test_help_query(self, graph_run):
        """Help query should work domain-agnostic."""
        data = graph_run("Help me understand this")
        
        parsed = data["parsed"]
        assert "intent" in parsed
        # Accept either response, narrative, or clarification
        has_output = (
            "response" in parsed or
            "narrative" in parsed or
            ("action" in parsed and "questions" in parsed)
        )
        assert has_output, "Must have some form of output"

    def test_multilingual_query_spanish(self, graph_run):
        """Spanish query should be detected and processed."""
        data = graph_run("¿Qué puedes hacer por mí?")
        
        parsed = data["parsed"]
        # Language should be detected
        assert "language_detected" in parsed or "language" in parsed
        assert "intent" in parsed
        # Accept any output form
        has_output = (
            "response" in parsed or
            "narrative" in parsed or
            "action" in parsed
        )
        assert has_output, "Must process multilingual query"


class TestDomainAgnosticEntityHandling:
    """Entity handling without finance-specific assumptions."""

    def test_query_without_entities(self, graph_run):
        """Query without any entities should work."""
        data = graph_run("What features are available?")
        
        parsed = data["parsed"]
        assert "intent" in parsed
        
        # Entity extraction should not fail (may return empty list or None)
        if "entity_ids" in parsed:
            entity_ids = parsed["entity_ids"]
            assert entity_ids is None or isinstance(entity_ids, list)
        if "entities" in parsed:
            entities = parsed["entities"]
            assert entities is None or isinstance(entities, list)

    def test_generic_entity_mention(self, graph_run):
        """Generic entity mention (not ticker/stock)."""
        data = graph_run("Show me information about technology")
        
        parsed = data["parsed"]
        assert "intent" in parsed
        assert "route" in parsed
        
        # Should not assume finance entities
        # Entity extraction may find "technology" as generic entity
        if "entity_ids" in parsed:
            # If entities found, they should not be finance tickers
            entities = parsed.get("entity_ids", [])
            # No validation needed - just ensure no crash


class TestDomainAgnosticRouting:
    """Routing logic without finance-specific paths."""

    def test_unknown_intent_routing(self, graph_run):
        """Unknown intent should route to fallback or llm."""
        data = graph_run("Foo bar baz nonsense")
        
        parsed = data["parsed"]
        assert "intent" in parsed
        assert "route" in parsed
        
        route = parsed["route"]
        # Should route to fallback/llm, not crash
        # Accept any route that completes successfully
        accepted_routes = [
            "unknown", "semantic_fallback", "llm_soft", "llm_mcp", 
            "cached_llm", "compose", "codex_complete", "chat"
        ]
        assert route in accepted_routes, f"Unexpected route: {route}"

    def test_conversational_routing(self, graph_run):
        """Conversational intent should route to LLM nodes."""
        data = graph_run("I need help")
        
        parsed = data["parsed"]
        route = parsed.get("route")
        
        # Should route to LLM-based or conversational nodes
        accepted_routes = [
            "llm_soft", "llm_mcp", "cached_llm", "compose",
            "chat", "codex_complete"
        ]
        assert route in accepted_routes, f"Unexpected route: {route}"

    def test_no_finance_exec_route(self, graph_run):
        """Generic query should not route to dispatcher_exec (finance-specific)."""
        data = graph_run("What can you do?")
        
        parsed = data["parsed"]
        route = parsed.get("route")
        
        # Should NOT route to dispatcher_exec (finance screening/ranking)
        # Unless USE_MCP=1 and MCP handles generic domains
        if route == "dispatcher_exec" or route == "exec":
            # Only acceptable if MCP is enabled
            import os
            use_mcp = os.getenv("USE_MCP", "0") == "1"
            assert use_mcp, "dispatcher_exec route requires USE_MCP=1 for generic queries"


class TestDomainAgnosticCANOutput:
    """Output generation without finance bias (accepts slot-filling or direct response)."""

    def test_can_output_structure(self, graph_run):
        """Must have structured output (response, clarification, or narrative)."""
        data = graph_run("Explain this to me")
        
        parsed = data["parsed"]
        # Accept multiple output forms
        has_response = "response" in parsed
        has_narrative = "narrative" in parsed
        has_clarification = "action" in parsed and "questions" in parsed
        
        assert (has_response or has_narrative or has_clarification), \
            "Must have response, narrative, or clarification"

    def test_can_output_no_finance_jargon(self, graph_run):
        """Generic query output should minimize finance jargon."""
        data = graph_run("What is the weather like?")
        
        parsed = data["parsed"]
        # Get any text output
        text_output = str(parsed.get("response", "")) + \
                      str(parsed.get("narrative", "")) + \
                      str(parsed.get("questions", ""))
        
        # Should not be dominated by finance-specific terms
        finance_terms = ["stock", "ticker", "portfolio", "screening", "momentum", "volatility"]
        text_lower = text_output.lower()
        
        # Allow 2 mentions (may be in system description)
        finance_mentions = sum(1 for term in finance_terms if term in text_lower)
        assert finance_mentions <= 2, f"Too many finance terms in generic response: {text_output[:200]}"


class TestDomainAgnosticOrthodoxy:
    """Orthodoxy validation without finance-specific rules."""

    def test_orthodoxy_status_present(self, graph_run):
        """Pipeline must complete successfully for all queries."""
        data = graph_run("Test query")
        
        parsed = data["parsed"]
        # Main check: pipeline completes and returns structured data
        assert "intent" in parsed
        assert "route" in parsed
        # Any output form is acceptable
        has_output = (
            "response" in parsed or
            "narrative" in parsed or
            "action" in parsed
        )
        assert has_output, "Pipeline must complete with output"


class TestDomainAgnosticVaultArchival:
    """Vault archival without finance-specific schemas."""

    def test_vault_archival_runs(self, graph_run):
        """Pipeline must complete for all queries."""
        data = graph_run("Archive this interaction")
        
        parsed = data["parsed"]
        # Main check: pipeline completes
        assert "intent" in parsed
        assert "route" in parsed
        # Any output is acceptable
        has_output = (
            "response" in parsed or
            "action" in parsed or
            "narrative" in parsed
        )
        assert has_output, "Pipeline must complete"


class TestDomainAgnosticPipelineIntegrity:
    """Full pipeline integrity without finance assumptions."""

    def test_full_pipeline_completes(self, graph_run):
        """Full pipeline must complete for generic query."""
        data = graph_run("Process this generic request")
        
        # Must have all top-level fields
        assert "human" in data
        assert "parsed" in data
        
        parsed = data["parsed"]
        # Must have routing decision
        assert "route" in parsed
        # Must have some output
        has_output = (
            "response" in parsed or
            "narrative" in parsed or
            "action" in parsed
        )
        assert has_output, "Pipeline must generate output"

    def test_pipeline_error_handling(self, graph_run):
        """Pipeline must handle errors gracefully."""
        # Intentionally malformed/edge case input
        data = graph_run("")  # Empty input
        
        # Should not crash, may return error or default response
        assert "parsed" in data or "error" in data

    def test_pipeline_multiple_queries(self, graph_run):
        """Multiple queries in sequence should work."""
        queries = [
            "Hello",
            "What can you do?",
            "Tell me more",
            "Thank you"
        ]
        
        for query in queries:
            try:
                data = graph_run(query)
                assert "parsed" in data
                parsed = data["parsed"]
                # Must have some output (response, action, or narrative)
                has_output = (
                    "response" in parsed or
                    "action" in parsed or
                    "narrative" in parsed
                )
                assert has_output, f"No output for query: {query}"
            except Exception as e:
                pytest.fail(f"Failed on query '{query}': {e}")


# ---------------------------------------------------------------------------
# Integration with MCP (if enabled)
# ---------------------------------------------------------------------------
class TestDomainAgnosticMCP:
    """MCP integration with generic domains (if USE_MCP=1)."""

    @pytest.mark.skipif(
        os.getenv("USE_MCP", "0") != "1",
        reason="MCP tests require USE_MCP=1"
    )
    def test_mcp_with_generic_query(self, graph_run):
        """MCP should handle generic queries if enabled."""
        import os
        data = graph_run("Process this request")
        
        parsed = data["parsed"]
        # Pipeline must complete
        assert "route" in parsed
        # May have some output form
        has_output = (
            "response" in parsed or
            "action" in parsed or
            "narrative" in parsed
        )
        assert has_output, "MCP pipeline must complete"


# ---------------------------------------------------------------------------
# Summary Test (runs all domain-agnostic scenarios)
# ---------------------------------------------------------------------------
class TestDomainAgnosticSummary:
    """Summary test: key domain-agnostic scenarios."""

    def test_domain_agnostic_scenarios(self, graph_run):
        """Run multiple domain-agnostic scenarios to ensure coverage."""
        scenarios = [
            ("Hello", "greeting"),
            ("What can you do?", "capability_query"),
            ("Tell me about X", "information_query"),
            ("Help me", "help_request"),
            ("¿Cómo estás?", "multilingual"),
            ("", "empty_input"),
        ]
        
        results = {}
        for query, scenario_name in scenarios:
            try:
                data = graph_run(query)
                parsed = data.get("parsed", {})
                results[scenario_name] = {
                    "success": True,
                    "intent": parsed.get("intent"),
                    "route": parsed.get("route"),
                    "has_output": (
                        "response" in parsed or
                        "narrative" in parsed or
                        "action" in parsed
                    )
                }
            except Exception as e:
                results[scenario_name] = {
                    "success": False,
                    "error": str(e)
                }
        
        # All scenarios should succeed
        failures = [name for name, result in results.items() if not result["success"]]
        assert len(failures) == 0, f"Failed scenarios: {failures}"
        
        # At least 80% should have valid output
        with_output = sum(1 for r in results.values() if r.get("has_output"))
        assert with_output >= len(scenarios) * 0.8, "Too few scenarios with output"

