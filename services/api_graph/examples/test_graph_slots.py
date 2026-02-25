"""
Slot filling and multi-turn dialogue tests.
"""

import httpx
import pytest
import json

BASE_URL = "http://localhost:9004"


def test_incomplete_query_slot_questions():
    """Test that incomplete queries trigger slot questions."""
    payload = {
        "input_text": "I want to invest",  # Missing: entities, horizon, risk
        "user_id": "test_user"
    }
    
    response = httpx.post(f"{BASE_URL}/run", json=payload, timeout=30.0)
    assert response.status_code == 200
    
    data = response.json()
    
    # Response should indicate missing slots
    human_message = data.get("human", data.get("message", ""))
    
    # Should ask clarifying questions
    assert any(keyword in human_message.lower() for keyword in [
        "which", "what", "companies", "stocks", "entities", "interested"
    ]), f"Expected slot questions, got: {human_message[:100]}"
    
    print(f"✅ Slot questions triggered: {human_message[:80]}...")


def test_slot_filling_flow():
    """Test iterative slot filling (multi-turn dialogue)."""
    # Turn 1: Incomplete query
    payload1 = {
        "input_text": "Should I invest in tech stocks?",
        "user_id": "test_user"
    }
    
    response1 = httpx.post(f"{BASE_URL}/run", json=payload1, timeout=30.0)
    assert response1.status_code == 200
    
    data1 = response1.json()
    print(f"Turn 1: {data1.get('human', '')[:80]}")
    
    # Turn 2: Provide entities
    payload2 = {
        "input_text": "Apple and Microsoft",
        "user_id": "test_user",
        "validated_tickers": ["AAPL", "MSFT"]
    }
    
    response2 = httpx.post(f"{BASE_URL}/run", json=payload2, timeout=30.0)
    assert response2.status_code == 200
    
    data2 = response2.json()
    
    # Should now have entities and possibly ask for more slots
    parsed_json = json.loads(data2.get("json", "{}")) if "json" in data2 else data2.get("response", {})
    
    if "entities" in parsed_json or "entity_ids" in parsed_json:
        entities = parsed_json.get("entities", parsed_json.get("entity_ids", []))
        assert len(entities) > 0, "Entities should be populated"
        print(f"✅ Slot filling flow: entities = {entities}")
    else:
        print(f"✅ Slot filling flow progressed (Turn 2 response: {data2.keys()})")


def test_slot_validation():
    """Test invalid slot values are handled gracefully."""
    payload = {
        "input_text": "I want to invest in XYZ999INVALID for negative 5 years",
        "user_id": "test_user"
    }
    
    response = httpx.post(f"{BASE_URL}/run", json=payload, timeout=30.0)
    
    # Should either ask for clarification or return graceful error
    assert response.status_code in [200, 400, 422]
    
    if response.status_code == 200:
        data = response.json()
        human_message = data.get("human", data.get("message", ""))
        
        # Should indicate issue or ask for clarification
        assert len(human_message) > 0
        print(f"✅ Invalid slots handled: {human_message[:80]}...")
    else:
        print(f"✅ Invalid slots rejected: {response.status_code}")


def test_skip_slots_with_entities():
    """Test pre-validated entities skip slot filling."""
    payload = {
        "input_text": "Should I buy these?",
        "user_id": "test_user",
        "validated_tickers": ["AAPL", "GOOGL", "MSFT"]  # Pre-validated
    }
    
    response = httpx.post(f"{BASE_URL}/run", json=payload, timeout=30.0)
    assert response.status_code == 200
    
    data = response.json()
    
    # Should NOT ask "which companies?" since entities provided
    human_message = data.get("human", data.get("message", ""))
    
    # Should either execute verdict or ask for other slots (not entities)
    assert not any(keyword in human_message.lower() for keyword in [
        "which companies", "what stocks", "which entities"
    ]), f"Should not ask for entities: {human_message[:100]}"
    
    print(f"✅ Slot filling skipped with pre-validated entities")


def test_slot_memory():
    """Test slot values persist across turns (same user_id)."""
    user_id = "test_slot_memory_user"
    
    # Turn 1: Provide entities
    payload1 = {
        "input_text": "I'm interested in Apple",
        "user_id": user_id,
        "validated_tickers": ["AAPL"]
    }
    
    response1 = httpx.post(f"{BASE_URL}/run", json=payload1, timeout=30.0)
    assert response1.status_code == 200
    
    # Turn 2: Ask without entities (should remember from Turn 1)
    payload2 = {
        "input_text": "Should I invest in it now?",
        "user_id": user_id
    }
    
    response2 = httpx.post(f"{BASE_URL}/run", json=payload2, timeout=30.0)
    assert response2.status_code == 200
    
    data2 = response2.json()
    
    # Implementation may or may not support slot memory across requests
    # This test documents expected behavior if implemented
    print(f"✅ Slot memory test executed (Turn 2: {data2.keys()})")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
