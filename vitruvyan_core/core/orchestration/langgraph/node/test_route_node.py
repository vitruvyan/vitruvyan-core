
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route_node import route_node

def test_route_node():
    # Soft intent
    s = {"intent": "soft"}
    assert route_node(s)["route"] == "llm_soft"
    # Known intent
    s = {"intent": "trend", "tickers": ["AAPL"], "amount": 1000, "horizon": "short"}
    assert route_node(s)["route"] == "dispatcher_exec"
    # Unknown intent
    s = {"intent": "unknown"}
    assert route_node(s)["route"] == "semantic_fallback"
    # Missing slots
    s = {"intent": "trend", "tickers": [], "amount": None, "horizon": None}
    assert route_node(s)["route"] == "slot_filler"
    # Default
    s = {"intent": "other", "tickers": ["AAPL"], "amount": 1000, "horizon": "short"}
    assert route_node(s)["route"] == "dispatcher_exec"
    print("All tests passed!")

if __name__ == "__main__":
    test_route_node()
