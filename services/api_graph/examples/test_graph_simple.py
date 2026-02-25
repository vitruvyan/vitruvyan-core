"""
Simple graph execution tests (single intent, no slot filling).
"""

import httpx
import pytest
import json

BASE_URL = "http://localhost:9004"


def test_graph_run_investment_verdict():
    """Test /run endpoint with investment verdict intent."""
    payload = {
        "input_text": "Should I invest in Apple?",
        "user_id": "test_user"
    }
    
    response = httpx.post(f"{BASE_URL}/run", json=payload, timeout=30.0)
    assert response.status_code == 200
    
    data = response.json()
    
    # Check response structure
    assert "json" in data or "response" in data
    assert "human" in data or "message" in data
    
    # Check execution metadata
    if "execution_timestamp" in data:
        assert isinstance(data["execution_timestamp"], str)
    
    print(f"✅ Graph executed: {data.get('human', data.get('message', 'OK'))[:100]}")


def test_graph_dispatch():
    """Test /dispatch endpoint (backward compatibility)."""
    payload = {
        "input_text": "What is the sentiment for Microsoft?",
        "user_id": "test_user"
    }
    
    response = httpx.post(f"{BASE_URL}/dispatch", json=payload, timeout=30.0)
    assert response.status_code == 200
    
    data = response.json()
    assert "json" in data or "response" in data
    
    print(f"✅ Dispatch executed: {data.keys()}")


def test_graph_with_dispatch():
    """Test /graph/dispatch endpoint with audit monitoring."""
    payload = {
        "input_text": "Compare Apple and Microsoft",
        "user_id": "test_user",
        "validated_tickers": ["AAPL", "MSFT"]
    }
    
    response = httpx.post(f"{BASE_URL}/graph/dispatch", json=payload, timeout=30.0)
    assert response.status_code == 200
    
    data = response.json()
    
    # Check audit tracking
    if "audit_monitored" in data:
        assert isinstance(data["audit_monitored"], bool)
    
    print(f"✅ Graph/dispatch executed with audit: {data.get('audit_monitored', 'N/A')}")


def test_graph_timeout():
    """Test graph execution with realistic timeout."""
    payload = {
        "input_text": "Analyze portfolio diversification for my holdings",
        "user_id": "test_user"
    }
    
    # Use longer timeout for complex queries
    response = httpx.post(f"{BASE_URL}/run", json=payload, timeout=60.0)
    
    # Should either complete or return timeout error gracefully
    assert response.status_code in [200, 504, 408]
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Complex query completed: {data.keys()}")
    else:
        print(f"✅ Timeout handled gracefully: {response.status_code}")


def test_graph_with_prevalidated_tickers():
    """Test graph execution with pre-validated tickers (skip resolution)."""
    payload = {
        "input_text": "Should I invest?",
        "user_id": "test_user",
        "validated_tickers": ["AAPL", "GOOGL"]  # Skip entity resolution
    }
    
    response = httpx.post(f"{BASE_URL}/run", json=payload, timeout=30.0)
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify entities were used (not re-extracted)
    parsed_json = json.loads(data.get("json", "{}")) if "json" in data else data.get("response", {})
    if "entities" in parsed_json or "entity_ids" in parsed_json:
        entities = parsed_json.get("entities", parsed_json.get("entity_ids", []))
        # Should contain at least one of the pre-validated entities
        assert any(entity in ["AAPL", "GOOGL"] for entity in entities)
    
    print(f"✅ Pre-validated entities respected")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
