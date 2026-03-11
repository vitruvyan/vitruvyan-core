
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vitruvyan_core'))
from core.orchestration.langgraph.node.route_node import route_node, configure

def test_route_node():
    # Configure exec intents for this test
    configure(exec_intents=["trend"], soft_intents=["soft"])
    # Soft intent
    s = {"intent": "soft"}
    assert route_node(s)["route"] == "llm_soft"
    # Known technical intent (configured as exec)
    s = {"intent": "trend", "entity_ids": ["ENTITY_1"], "amount": 1000, "horizon": "short"}
    assert route_node(s)["route"] == "dispatcher_exec"
    # Unknown intent → semantic_fallback (RAG + LLM-first)
    s = {"intent": "unknown"}
    assert route_node(s)["route"] == "semantic_fallback"
    # Unrecognized intent → semantic fallback
    s = {"intent": "other", "entity_ids": ["ENTITY_1"], "amount": 1000, "horizon": "short"}
    assert route_node(s)["route"] == "semantic_fallback"
    print("All tests passed!")

if __name__ == "__main__":
    test_route_node()
