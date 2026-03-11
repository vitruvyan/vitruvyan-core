"""
CAN Node - Context Integration Tests

Verifica che CAN integri correttamente context da:
- VSGS semantic grounding (semantic_matches)
- Pattern Weavers (weaver_context)
- Babel Gardens (emotion_detected)
- Intent detection (intent, conversation_type)
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def base_state():
    """State base per test CAN node."""
    return {
        "input_text": "explain vitruvyan architecture patterns",
        "user_id": "test_user",
        "intent": "unknown",
        "conversation_type": "chat",
        "language": "en",
        "emotion_detected": "curious",
        "emotion_confidence": 0.8,
        "semantic_matches": [],
        "weaver_context": {"status": "completed", "matches": []},
    }


@pytest.fixture
def state_with_vsgs_context(base_state):
    """State con semantic matches da VSGS."""
    base_state["semantic_matches"] = [
        {
            "text": "Sacred Orders cognitive architecture uses LangGraph...",
            "score": 0.85,
            "metadata": {"source": "docs/architecture.md"}
        },
        {
            "text": "Pattern Weavers extract ontology concepts...",
            "score": 0.78,
            "metadata": {"source": "docs/pattern_weavers.md"}
        },
        {
            "text": "Babel Gardens multilingual emotion detection...",
            "score": 0.72,
            "metadata": {"source": "docs/babel_gardens.md"}
        }
    ]
    return base_state


@pytest.fixture
def state_with_weaver_concepts(base_state):
    """State con concetti da Pattern Weavers."""
    base_state["weaver_context"] = {
        "status": "completed",
        "matches": [
            {"name": "cognitive_architecture", "score": 0.88},
            {"name": "sacred_orders", "score": 0.82},
            {"name": "semantic_enrichment", "score": 0.76}
        ]
    }
    return base_state


class TestCANContextIntegration:
    """Test context integration nel CAN node."""
    
    @patch('core.orchestration.langgraph.node.can_node.get_llm_agent')
    def test_vsgs_context_extraction(self, mock_llm_agent_factory, state_with_vsgs_context):
        """Verifica estrazione context da VSGS semantic matches."""
        # Mock LLM
        mock_agent = MagicMock()
        mock_agent.complete.return_value = "Sacred Orders architecture leverages..."
        mock_llm_agent_factory.return_value = mock_agent
        
        # Import can_node after mocking dependencies
        from core.orchestration.langgraph.node.can_node import can_node
        
        # Execute CAN node
        result = can_node(state_with_vsgs_context)
        
        # Assertions (test behavior, not implementation)
        assert "narrative" in result
        assert result["vsgs_context_used"] is True
        assert len(result["narrative"]) > 0  # Has narrative
        assert result["narrative"] == "Sacred Orders architecture leverages..."
    
    @patch('core.agents.llm_agent.get_llm_agent')
    def test_weaver_concepts_integration(self, mock_llm_agent_factory, state_with_weaver_concepts):
        """Verifica integrazione concetti da Pattern Weavers."""
        mock_agent = MagicMock()
        mock_agent.complete.return_value = "The cognitive architecture concept..."
        mock_llm_agent_factory.return_value = mock_agent
        
        # Import can_node after mocking
        from core.orchestration.langgraph.node.can_node import can_node
        
        result = can_node(state_with_weaver_concepts)
        
        assert "narrative" in result
        assert len(result["weaver_context"]["matches"]) == 3
        assert result["narrative"]  # Has generated narrative
    
    @patch('core.agents.llm_agent.get_llm_agent')
    def test_emotion_context_influence(self, mock_llm_agent_factory, base_state):
        """Verifica che l'emozione sia disponibile nel contesto."""
        mock_agent = MagicMock()
        mock_agent.complete.return_value = "Let me explain..."
        mock_llm_agent_factory.return_value = mock_agent
        
        # Import after mocking
        from core.orchestration.langgraph.node.can_node import can_node
        
        # Test con emozione curiosa
        base_state["emotion_detected"] = "curious"
        result = can_node(base_state.copy())
        
        # Verify emotion preserved in output
        assert result["emotion_detected"] == "curious"
        assert "narrative" in result
    
    @patch('core.agents.llm_agent.get_llm_agent')
    def test_no_context_fallback(self, mock_llm_agent_factory, base_state):
        """Verifica fallback quando manca context (no VSGS, no weaver)."""
        mock_agent = MagicMock()
        mock_agent.complete.return_value = "I understand you're asking about..."
        mock_llm_agent_factory.return_value = mock_agent
        
        # Import after mocking
        from core.orchestration.langgraph.node.can_node import can_node
        
        # Empty context
        base_state["semantic_matches"] = []
        base_state["weaver_context"] = {"status": "completed", "matches": []}
        
        result = can_node(base_state)
        
        assert "narrative" in result
        assert result["vsgs_context_used"] is False
        assert result["narrative"]  # Should still generate narrative
    
    @patch('core.agents.llm_agent.get_llm_agent')
    def test_multilingual_context(self, mock_llm_agent_factory, base_state):
        """Verifica context integration in lingue diverse."""
        mock_agent = MagicMock()
        mock_agent.complete.return_value = "L'architettura di Vitruvyan..."
        mock_llm_agent_factory.return_value = mock_agent
        
        # Import after mocking
        from core.orchestration.langgraph.node.can_node import can_node
        
        base_state["language"] = "it"
        base_state["input_text"] = "spiega l'architettura di vitruvyan"
        
        result = can_node(base_state)
        
        assert result["language"] == "it"
        assert "narrative" in result


@pytest.mark.integration
class TestCANContextEnrichment:
    """Test arricchimento context da multiple fonti."""
    
    @patch('core.agents.llm_agent.get_llm_agent')
    def test_combined_context_richness(self, mock_llm_agent_factory):
        """Verifica arricchimento con VSGS + Weaver + Emotion."""
        mock_agent = MagicMock()
        mock_agent.complete.return_value = "Based on the architectural patterns..."
        mock_llm_agent_factory.return_value = mock_agent
        
        # Import after mocking
        from core.orchestration.langgraph.node.can_node import can_node
        
        rich_state = {
            "input_text": "cognitive architecture patterns",
            "user_id": "test",
            "intent": "unknown",
            "conversation_type": "chat",
            "language": "en",
            "emotion_detected": "curious",
            "emotion_confidence": 0.85,
            "semantic_matches": [
                {"text": "Sacred Orders...", "score": 0.88}
            ],
            "weaver_context": {
                "status": "completed",
                "matches": [{"name": "architecture", "score": 0.90}]
            }
        }
        
        result = can_node(rich_state)
        
        # Check all context sources used
        assert result["vsgs_context_used"] is True
        assert len(result["weaver_context"]["matches"]) > 0
        assert result["emotion_detected"] == "curious"
        assert "narrative" in result
        assert len(result["narrative"]) > 0
