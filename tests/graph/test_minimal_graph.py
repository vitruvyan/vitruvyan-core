"""
Phase 1 Minimal Graph Test

Verifies build_minimal_graph() compiles and executes.
"""

import os
os.environ["ENABLE_MINIMAL_GRAPH"] = "true"

from core.orchestration.langgraph.graph_flow import build_minimal_graph


def test_minimal_graph_compiles():
    """Test that minimal graph compiles."""
    graph = build_minimal_graph()
    assert graph is not None
    assert type(graph).__name__ == "CompiledStateGraph"


def test_minimal_graph_invoke():
    """Test that minimal graph executes."""
    graph = build_minimal_graph()
    
    result = graph.invoke({
        "input_text": "test",
        "user_id": "x"
    })
    
    assert result is not None
    assert "input_text" in result
    assert "user_id" in result
    assert result["input_text"] == "test"
    assert result["user_id"] == "x"


if __name__ == "__main__":
    test_minimal_graph_compiles()
    print("✅ Minimal graph compiles")
    
    test_minimal_graph_invoke()
    print("✅ Minimal graph invoke works")
    
    print("\n✅ ALL TESTS PASSED")
