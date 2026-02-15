
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route_node import route_node

def test_route_node():
    # Soft intent
    s = {"intent": "soft"}
    assert route_node(s)["route"] == "llm_soft"
    # Known technical intent
    s = {"intent": "trend", "entity_ids": ["ENTITY_1"], "amount": 1000, "horizon": "short"}
    assert route_node(s)["route"] == "dispatcher_exec"
    # Unknown intent → slot filler
    s = {"intent": "unknown"}
    assert route_node(s)["route"] == "slot_filler"
    # Unrecognized intent → semantic fallback
    s = {"intent": "other", "entity_ids": ["ENTITY_1"], "amount": 1000, "horizon": "short"}
    assert route_node(s)["route"] == "semantic_fallback"
    print("All tests passed!")

if __name__ == "__main__":
    test_route_node()
