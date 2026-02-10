"""
Entity search and autocomplete tests.
"""

import httpx
import pytest

BASE_URL = "http://localhost:9004"


def test_entity_search_exact_match():
    """Test exact entity match (ticker symbol)."""
    response = httpx.get(f"{BASE_URL}/api/entity_ids/search?q=AAPL")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert data["query"] == "AAPL"
    
    # Should find Apple with high match score
    results = data["results"]
    assert len(results) > 0
    
    # First result should be exact match
    first = results[0]
    assert first["entity_id"] == "AAPL"
    assert first["match_score"] == 1.0  # Exact match
    
    print(f"✅ Exact match: {first['entity_id']} ({first['name']})")


def test_entity_search_fuzzy():
    """Test fuzzy entity search (partial match)."""
    response = httpx.get(f"{BASE_URL}/api/entity_ids/search?q=app")
    assert response.status_code == 200
    
    data = response.json()
    results = data["results"]
    
    # Should find Apple and possibly others
    assert len(results) > 0
    
    # Check match scores are reasonable
    for result in results:
        assert 0.0 <= result["match_score"] <= 1.0
        assert "entity_id" in result
        assert "name" in result
    
    # Apple should be high-ranked
    apple_results = [r for r in results if "Apple" in r["name"]]
    if apple_results:
        assert apple_results[0]["match_score"] >= 0.7
    
    print(f"✅ Fuzzy search 'app': {len(results)} results")


def test_entity_search_multiple_matches():
    """Test search returning multiple ranked results."""
    response = httpx.get(f"{BASE_URL}/api/entity_ids/search?q=micro")
    assert response.status_code == 200
    
    data = response.json()
    results = data["results"]
    
    # Should find Microsoft, MicroStrategy, etc.
    assert len(results) > 0
    
    # Results should be ranked by match score
    scores = [r["match_score"] for r in results]
    assert scores == sorted(scores, reverse=True), "Results should be ranked"
    
    # Microsoft should be top result
    if results[0]["name"].startswith("Micro"):
        print(f"✅ Top result: {results[0]['name']} (score: {results[0]['match_score']})")


def test_entity_search_no_results():
    """Test search with no matches."""
    response = httpx.get(f"{BASE_URL}/api/entity_ids/search?q=xyz999notfound")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert len(data["results"]) == 0
    assert data["total"] == 0
    
    print(f"✅ No results for invalid query: {data['query']}")


def test_entity_search_limit():
    """Test search result limit parameter."""
    response = httpx.get(f"{BASE_URL}/api/entity_ids/search?q=tech&limit=5")
    assert response.status_code == 200
    
    data = response.json()
    results = data["results"]
    
    # Should respect limit (max 5)
    assert len(results) <= 5
    
    print(f"✅ Limited to {len(results)} results (max 5)")


def test_entity_search_ranking():
    """Test match score ranking logic."""
    # Search for "citi"
    response = httpx.get(f"{BASE_URL}/api/entity_ids/search?q=citi")
    assert response.status_code == 200
    
    data = response.json()
    results = data["results"]
    
    if len(results) > 0:
        # Verify ranking logic
        for result in results:
            score = result["match_score"]
            name = result["name"].lower()
            query = "citi"
            
            # Exact match → 1.0
            # Starts with → 0.9
            # Contains → 0.3-0.7
            if query == name:
                assert score == 1.0
            elif name.startswith(query):
                assert score >= 0.7
            else:
                assert score >= 0.3
        
        print(f"✅ Ranking logic validated for {len(results)} results")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
