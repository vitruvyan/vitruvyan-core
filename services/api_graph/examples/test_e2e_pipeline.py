"""
End-to-end pipeline tests (full conversational flow).
"""

import httpx
import pytest
import json
import time

BASE_URL = "http://localhost:9004"


def test_pipeline_simple_verdict():
    """Test full pipeline: query → intent → verdict."""
    # User query
    payload = {
        "input_text": "Should I buy Apple stock?",
        "user_id": "pipeline_test_user"
    }
    
    response = httpx.post(f"{BASE_URL}/run", json=payload, timeout=45.0)
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify graph execution
    assert "json" in data or "response" in data
    assert "human" in data or "message" in data
    
    # Parse result
    parsed_json = json.loads(data.get("json", "{}")) if "json" in data else data.get("response", {})
    
    # Check intent was classified
    if "intent" in parsed_json:
        assert parsed_json["intent"] in [
            "investment_verdict", "stock_analysis", "buy_signal"
        ]
    
    # Check entities were resolved
    if "entities" in parsed_json or "entity_ids" in parsed_json:
        entities = parsed_json.get("entities", parsed_json.get("entity_ids", []))
        assert "AAPL" in entities or len(entities) > 0
    
    print(f"✅ Simple pipeline: {data.get('human', '')[:100]}")


def test_pipeline_with_entity_search():
    """Test full pipeline: autocomplete → graph execution."""
    # Step 1: Entity search (autocomplete)
    search_response = httpx.get(f"{BASE_URL}/api/entity_ids/search?q=app")
    assert search_response.status_code == 200
    
    search_data = search_response.json()
    results = search_data["results"]
    assert len(results) > 0
    
    # User selects first result
    selected_entity = results[0]["entity_id"]
    print(f"Step 1: Autocomplete selected {selected_entity}")
    
    # Step 2: Execute graph with selected entity
    payload = {
        "input_text": f"Should I invest in {selected_entity}?",
        "user_id": "pipeline_autocomplete_user",
        "validated_entities": [selected_entity]
    }
    
    graph_response = httpx.post(f"{BASE_URL}/run", json=payload, timeout=45.0)
    assert graph_response.status_code == 200
    
    graph_data = graph_response.json()
    print(f"✅ Autocomplete → Graph pipeline: {graph_data.get('human', '')[:80]}")


def test_pipeline_slot_filling():
    """Test full pipeline: incomplete → clarify → execute."""
    # Step 1: Incomplete query (missing entities)
    payload1 = {
        "input_text": "I want to invest in tech",
        "user_id": "pipeline_slots_user"
    }
    
    response1 = httpx.post(f"{BASE_URL}/run", json=payload1, timeout=30.0)
    assert response1.status_code == 200
    
    data1 = response1.json()
    print(f"Step 1 (slots needed): {data1.get('human', '')[:80]}")
    
    # Step 2: Provide missing entities
    payload2 = {
        "input_text": "Apple and Microsoft",
        "user_id": "pipeline_slots_user",
        "validated_entities": ["AAPL", "MSFT"]
    }
    
    response2 = httpx.post(f"{BASE_URL}/run", json=payload2, timeout=45.0)
    assert response2.status_code == 200
    
    data2 = response2.json()
    
    # Verify entities were used
    parsed_json = json.loads(data2.get("json", "{}")) if "json" in data2 else data2.get("response", {})
    
    if "entities" in parsed_json or "entity_ids" in parsed_json:
        entities = parsed_json.get("entities", parsed_json.get("entity_ids", []))
        assert any(e in ["AAPL", "MSFT"] for e in entities)
    
    print(f"✅ Slot filling pipeline: {data2.get('human', '')[:80]}")


def test_pipeline_comparison():
    """Test full pipeline: comparison matrix generation."""
    payload = {
        "input_text": "Compare Apple vs Microsoft",
        "user_id": "pipeline_comparison_user",
        "validated_entities": ["AAPL", "MSFT"]
    }
    
    response = httpx.post(f"{BASE_URL}/run", json=payload, timeout=60.0)
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify comparison intent
    parsed_json = json.loads(data.get("json", "{}")) if "json" in data else data.get("response", {})
    
    if "intent" in parsed_json:
        assert "comparison" in parsed_json["intent"].lower() or "compare" in parsed_json["intent"].lower()
    
    # Should have both entities
    if "entities" in parsed_json or "entity_ids" in parsed_json:
        entities = parsed_json.get("entities", parsed_json.get("entity_ids", []))
        assert "AAPL" in entities or "MSFT" in entities or len(entities) >= 2
    
    print(f"✅ Comparison pipeline: {data.get('human', '')[:100]}")


def test_pipeline_portfolio_gauge():
    """Test full pipeline: portfolio health analysis."""
    payload = {
        "input_text": "How is my portfolio doing?",
        "user_id": "pipeline_portfolio_user"
    }
    
    response = httpx.post(f"{BASE_URL}/run", json=payload, timeout=45.0)
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify portfolio-related intent
    parsed_json = json.loads(data.get("json", "{}")) if "json" in data else data.get("response", {})
    
    if "intent" in parsed_json:
        assert any(keyword in parsed_json["intent"].lower() for keyword in [
            "portfolio", "diversification", "health"
        ])
    
    print(f"✅ Portfolio pipeline: {data.get('human', '')[:100]}")


def test_pipeline_with_audit():
    """Test full pipeline with audit monitoring enabled."""
    # Check if audit is available
    audit_health = httpx.get(f"{BASE_URL}/audit/graph/health")
    audit_available = audit_health.status_code == 200
    
    payload = {
        "input_text": "Should I invest in Google?",
        "user_id": "pipeline_audit_user"
    }
    
    # Use /graph/dispatch for explicit audit wrapper
    response = httpx.post(f"{BASE_URL}/graph/dispatch", json=payload, timeout=45.0)
    assert response.status_code == 200
    
    data = response.json()
    
    # Check execution metadata
    if "audit_monitored" in data:
        print(f"✅ Pipeline audited: {data['audit_monitored']}")
    
    if "execution_timestamp" in data:
        print(f"   Timestamp: {data['execution_timestamp']}")
    
    # Verify audit metrics updated
    if audit_available:
        time.sleep(0.5)  # Brief delay for metric update
        metrics_response = httpx.get(f"{BASE_URL}/audit/graph/metrics")
        
        if metrics_response.status_code == 200:
            metrics_data = metrics_response.json()
            
            if "performance_metrics" in metrics_data:
                executions = metrics_data["performance_metrics"].get("executions", 0)
                print(f"✅ Audit tracked {executions} total executions")


def test_pipeline_semantic_clusters():
    """Test semantic clusters endpoint (documentation structure)."""
    response = httpx.get(f"{BASE_URL}/clusters/semantic")
    assert response.status_code == 200
    
    data = response.json()
    
    # Should return cluster structure
    if "clusters" in data or "results" in data:
        clusters = data.get("clusters", data.get("results", []))
        print(f"✅ Semantic clusters: {len(clusters)} clusters found")
        
        # Verify cluster schema
        if len(clusters) > 0:
            first_cluster = clusters[0]
            assert "cluster_name" in first_cluster or "name" in first_cluster
    else:
        print(f"✅ Semantic clusters endpoint OK: {data.keys()}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
