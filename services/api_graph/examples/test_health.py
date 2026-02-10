"""
Health checks and monitoring tests for api_graph service.
"""

import httpx
import pytest

BASE_URL = "http://localhost:9004"


def test_health_endpoint():
    """Test basic health check endpoint."""
    response = httpx.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "api_graph"
    print(f"✅ Service healthy: {data}")


def test_health_schema():
    """Validate health response schema."""
    response = httpx.get(f"{BASE_URL}/health")
    data = response.json()
    
    # Required fields
    assert "status" in data
    assert "service" in data
    assert "version" in data
    
    # Optional audit fields
    if "audit_monitoring" in data:
        assert isinstance(data["audit_monitoring"], str)
    if "heartbeat_count" in data:
        assert isinstance(data["heartbeat_count"], int)
    
    print(f"✅ Health schema valid: {list(data.keys())}")


def test_pg_health():
    """Test PostgreSQL health endpoint (placeholder)."""
    response = httpx.get(f"{BASE_URL}/pg/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "postgres"
    print(f"✅ PostgreSQL health: {data}")


def test_qdrant_health():
    """Test Qdrant health endpoint (placeholder)."""
    response = httpx.get(f"{BASE_URL}/qdrant/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "qdrant"
    print(f"✅ Qdrant health: {data}")


def test_metrics_endpoint():
    """Test Prometheus metrics endpoint."""
    response = httpx.get(f"{BASE_URL}/metrics")
    assert response.status_code == 200
    
    # Should contain Prometheus-formatted metrics
    text = response.text
    assert "# HELP" in text  # Prometheus metric help text
    assert "# TYPE" in text  # Prometheus metric type declaration
    
    # Check for expected metrics
    assert "graph_requests_total" in text
    assert "graph_execution_duration_seconds" in text
    
    print(f"✅ Metrics endpoint exposed {len(text)} bytes")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
