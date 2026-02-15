# tests/test_orchestration_base_classes.py
"""
Unit tests for LangGraph orchestration base classes.

Tests the domain-agnostic abstractions created during refactoring:
- BaseGraphState
- GraphPlugin ABC
- ResponseFormatter ABC
- SlotFiller ABC
- BaseComposer
- LLMAgent

Follows Vitruvyan testing guidelines:
- Diverse test inputs (no biased fixtures)
- Explicit assertions
- Clear test isolation
"""

import pytest
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch


# ===========================================================================
# TEST: BaseGraphState
# ===========================================================================

class TestBaseGraphState:
    """Tests for BaseGraphState TypedDict structure."""
    
    def test_base_state_can_be_instantiated(self):
        """BaseGraphState should be usable as a TypedDict."""
        from vitruvyan_core.core.orchestration.base_state import BaseGraphState
        
        state: BaseGraphState = {
            "input_text": "Test query",
            "user_id": "user_123",
            "session_id": "session_456",
        }
        
        assert state["input_text"] == "Test query"
        assert state["user_id"] == "user_123"
    
    def test_base_state_has_required_fields(self):
        """BaseGraphState should define core fields."""
        from vitruvyan_core.core.orchestration.base_state import BaseGraphState
        
        # Check annotations exist (TypedDict fields)
        annotations = BaseGraphState.__annotations__
        
        # Core input fields
        assert "input_text" in annotations
        assert "user_id" in annotations
        
        # Intent/routing fields
        assert "intent" in annotations
        assert "route" in annotations
        
        # UX fields (Babel Gardens)
        assert "language_detected" in annotations
        assert "emotion_detected" in annotations
    
    def test_base_state_total_false(self):
        """BaseGraphState should allow partial initialization."""
        from vitruvyan_core.core.orchestration.base_state import BaseGraphState
        
        # Should not raise - total=False allows partial dict
        state: BaseGraphState = {}
        assert isinstance(state, dict)


# ===========================================================================
# TEST: GraphPlugin ABC
# ===========================================================================

class TestGraphPlugin:
    """Tests for GraphPlugin abstract base class."""
    
    def test_plugin_requires_abstract_methods(self):
        """GraphPlugin should require implementation of abstract methods."""
        from vitruvyan_core.core.orchestration.graph_engine import GraphPlugin
        
        # Should not be directly instantiable
        with pytest.raises(TypeError):
            GraphPlugin()
    
    def test_plugin_contract(self):
        """GraphPlugin should define the full plugin contract."""
        from vitruvyan_core.core.orchestration.graph_engine import GraphPlugin
        import inspect
        
        abstract_methods = set()
        for name, method in inspect.getmembers(GraphPlugin, predicate=inspect.isfunction):
            if getattr(method, '__isabstractmethod__', False):
                abstract_methods.add(name)
        
        # Core contract methods
        assert "get_domain_name" in abstract_methods
        assert "get_nodes" in abstract_methods
        assert "get_route_map" in abstract_methods
        assert "get_intents" in abstract_methods
        assert "get_state_extensions" in abstract_methods
    
    def test_concrete_plugin_implementation(self):
        """A concrete plugin should implement all abstract methods."""
        from vitruvyan_core.core.orchestration.graph_engine import GraphPlugin
        from typing import Callable, Tuple
        
        class TestPlugin(GraphPlugin):
            def get_domain_name(self) -> str:
                return "test"
            
            def get_nodes(self) -> Dict[str, Callable]:
                return {"test_node": lambda x: x}
            
            def get_route_map(self) -> Dict[str, str]:
                return {"test_intent": "test_route"}
            
            def get_intents(self) -> List[str]:
                return ["test_intent"]
            
            def get_state_extensions(self) -> Dict[str, Any]:
                return {"test_field": None}
            
            def get_entry_pipeline(self) -> List[str]:
                return []
            
            def get_post_routing_edges(self) -> List[Tuple[str, str]]:
                return []
        
        plugin = TestPlugin()
        assert plugin.get_domain_name() == "test"
        assert "test_node" in plugin.get_nodes()
        assert plugin.get_route_map()["test_intent"] == "test_route"


# ===========================================================================
# TEST: ResponseFormatter ABC
# ===========================================================================

class TestResponseFormatter:
    """Tests for ResponseFormatter abstract base class."""
    
    def test_formatter_requires_abstract_methods(self):
        """ResponseFormatter should require implementation of abstract methods."""
        from vitruvyan_core.core.orchestration.compose.response_formatter import ResponseFormatter
        
        with pytest.raises(TypeError):
            ResponseFormatter()
    
    def test_conversation_type_enum(self):
        """ConversationType should define base types."""
        from vitruvyan_core.core.orchestration.compose.response_formatter import ConversationType
        
        assert ConversationType.SINGLE_ENTITY.value == "single_entity"
        assert ConversationType.MULTI_ENTITY.value == "multi_entity"
        assert ConversationType.ONBOARDING.value == "onboarding"
        assert ConversationType.CONVERSATIONAL.value == "conversational"
        assert ConversationType.NO_DATA.value == "no_data"
    
    def test_formatted_response_dataclass(self):
        """FormattedResponse should be a proper dataclass."""
        from vitruvyan_core.core.orchestration.compose.response_formatter import (
            FormattedResponse, ConversationType
        )
        
        response = FormattedResponse(
            conversation_type=ConversationType.SINGLE_ENTITY,
            narrative="Test narrative",
            verdict={"label": "Buy"},
            gauge={"momentum": {"color": "green"}},
        )
        
        assert response.conversation_type == ConversationType.SINGLE_ENTITY
        assert response.narrative == "Test narrative"
        assert response.verdict["label"] == "Buy"
    
    def test_generic_formatter_works(self):
        """GenericResponseFormatter should work without domain logic."""
        from vitruvyan_core.core.orchestration.compose.response_formatter import (
            GenericResponseFormatter, ConversationType
        )
        
        formatter = GenericResponseFormatter()
        
        # Single entity detection
        state = {"entity_ids": ["entity_1"]}
        conv_type = formatter.detect_conversation_type(state)
        assert conv_type == ConversationType.SINGLE_ENTITY
        
        # Multi entity detection
        state = {"entity_ids": ["entity_1", "entity_2"]}
        conv_type = formatter.detect_conversation_type(state)
        assert conv_type == ConversationType.MULTI_ENTITY
        
        # No entities = conversational
        state = {"entity_ids": []}
        conv_type = formatter.detect_conversation_type(state)
        assert conv_type == ConversationType.CONVERSATIONAL


# ===========================================================================
# TEST: SlotFiller ABC
# ===========================================================================

class TestSlotFiller:
    """Tests for SlotFiller abstract base class."""
    
    def test_slot_filler_requires_abstract_methods(self):
        """SlotFiller should require implementation of abstract methods."""
        from vitruvyan_core.core.orchestration.compose.slot_filler import SlotFiller
        
        with pytest.raises(TypeError):
            SlotFiller()
    
    def test_slot_question_dataclass(self):
        """SlotQuestion should capture question details."""
        from vitruvyan_core.core.orchestration.compose.slot_filler import SlotQuestion
        
        question = SlotQuestion(
            slot_name="time_horizon",
            question="What's your investment horizon?",
            options=["short", "medium", "long"],
            is_required=True,
        )
        
        assert question.slot_name == "time_horizon"
        assert len(question.options) == 3
        assert question.is_required is True
    
    def test_slot_definition(self):
        """SlotDefinition should capture slot metadata."""
        from vitruvyan_core.core.orchestration.compose.slot_filler import SlotDefinition
        
        slot = SlotDefinition(
            name="risk_tolerance",
            display_name="Risk Profile",
            description="User's risk preference",
            valid_values=["low", "medium", "high"],
            required_for_intents=["allocation"],
        )
        
        assert slot.name == "risk_tolerance"
        assert "allocation" in slot.required_for_intents
    
    def test_generic_slot_filler_works(self):
        """GenericSlotFiller should work without domain logic."""
        from vitruvyan_core.core.orchestration.compose.slot_filler import GenericSlotFiller
        
        filler = GenericSlotFiller()
        
        # No predefined slots
        assert filler.get_slot_definitions() == []
        
        # No missing slots
        assert filler.check_missing_slots({}, "any_intent") == []
        
        # Can generate basic question
        question = filler.generate_question("test_slot", "en", {})
        assert "test_slot" in question.question


# ===========================================================================
# TEST: BaseComposer
# ===========================================================================

class TestBaseComposer:
    """Tests for BaseComposer orchestration class."""
    
    def test_composer_result_to_dict(self):
        """ComposerResult should convert to dictionary."""
        from vitruvyan_core.core.orchestration.compose.base_composer import ComposerResult
        
        result = ComposerResult(
            action="answer",
            narrative="Test response",
            conversation_type="single_entity",
            entity_ids=["entity_1"],
        )
        
        d = result.to_dict()
        assert d["action"] == "answer"
        assert d["narrative"] == "Test response"
        assert d["entity_ids"] == ["entity_1"]
    
    def test_generic_composer_works(self):
        """GenericComposer should work without domain-specific logic."""
        from vitruvyan_core.core.orchestration.compose.base_composer import GenericComposer
        
        composer = GenericComposer()
        
        state = {
            "input_text": "Test query",
            "entity_ids": ["entity_1"],
            "intent": "analyze",
            "detected_language": "en",
        }
        
        result = composer.compose(state)
        
        assert result.action == "answer"
        assert result.conversation_type == "single_entity"


# ===========================================================================
# TEST: LLMAgent
# ===========================================================================

class TestLLMAgent:
    """Tests for LLMAgent centralized gateway."""
    
    def test_llm_agent_is_singleton(self):
        """LLMAgent should be a singleton."""
        from vitruvyan_core.core.agents.llm_agent import LLMAgent
        
        agent1 = LLMAgent()
        agent2 = LLMAgent()
        
        assert agent1 is agent2
    
    def test_rate_limiter(self):
        """RateLimiter should track requests."""
        from vitruvyan_core.core.agents.llm_agent import RateLimiter
        
        limiter = RateLimiter(rpm=5, tpm=500)  # Very low limits for testing
        
        # Should allow requests initially (acquire returns True)
        assert limiter.acquire(estimated_tokens=100) is True
        
        # Fill up to the limit (5 requests)
        for _ in range(4):  # Already did 1 above
            limiter.acquire(estimated_tokens=100)
        
        # Should be at limit now (5 requests)
        # Next acquire should fail due to RPM limit
        assert limiter.acquire(estimated_tokens=100) is False
    
    def test_circuit_breaker(self):
        """CircuitBreaker should open after failures."""
        from vitruvyan_core.core.agents.llm_agent import CircuitBreaker
        
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        
        assert breaker.can_execute() is True
        
        # Record failures
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        
        # Should be open now
        assert breaker.state == CircuitBreaker.OPEN
        assert breaker.can_execute() is False
