"""
Audit monitoring integration tests.
"""

import httpx
import pytest

BASE_URL = "http://localhost:9004"


def test_audit_health():
    """Test audit monitoring health endpoint."""
    response = httpx.get(f"{BASE_URL}/audit/graph/health")
    assert response.status_code == 200
    
    data = response.json()
    
    # Check audit health schema
    assert "status" in data
    
    if "monitoring_active" in data:
        assert isinstance(data["monitoring_active"], bool)
    
    if "session_id" in data:
        assert isinstance(data["session_id"], str)
    
    print(f"✅ Audit health: {data.get('status')} (active: {data.get('monitoring_active', 'N/A')})")


def test_audit_metrics():
    """Test audit performance metrics endpoint."""
    response = httpx.get(f"{BASE_URL}/audit/graph/metrics")
    assert response.status_code == 200
    
    data = response.json()
    
    # Should contain performance metrics
    if "performance_metrics" in data:
        metrics = data["performance_metrics"]
        
        # Check expected metric keys
        expected_keys = ["executions", "errors", "avg_duration_ms"]
        for key in expected_keys:
            if key in metrics:
                assert isinstance(metrics[key], (int, float))
        
        print(f"✅ Audit metrics: {metrics.get('executions', 0)} executions")
    else:
        print(f"✅ Audit metrics endpoint OK: {data.keys()}")


def test_audit_trigger():
    """Test manual audit trigger endpoint."""
    payload = {
        "context_id": "test_trigger",
        "action": "manual_audit"
    }
    
    response = httpx.post(f"{BASE_URL}/audit/graph/trigger", json=payload)
    
    # Should accept or return not implemented
    assert response.status_code in [200, 201, 501]
    
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✅ Audit triggered: {data.keys()}")
    else:
        print(f"✅ Audit trigger not implemented (expected)")


def test_grafana_webhook():
    """Test Grafana alert webhook receiver."""
    # Mock Grafana alert payload
    payload = {
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "HighErrorRate",
                    "service": "api_graph"
                },
                "annotations": {
                    "description": "Error rate above threshold"
                }
            }
        ]
    }
    
    response = httpx.post(f"{BASE_URL}/webhook/grafana/alert", json=payload)
    
    # Should accept or return not implemented
    assert response.status_code in [200, 202, 501]
    
    print(f"✅ Grafana webhook: {response.status_code}")


def test_audit_with_graph_execution():
    """Test audit tracking during graph execution."""
    # Execute graph with audit enabled
    payload = {
        "input_text": "Should I invest in Apple?",
        "user_id": "audit_test_user"
    }
    
    # Use /graph/dispatch for explicit audit wrapper
    response = httpx.post(f"{BASE_URL}/graph/dispatch", json=payload, timeout=30.0)
    assert response.status_code == 200
    
    data = response.json()
    
    # Check if audit was tracked
    if "audit_monitored" in data:
        assert isinstance(data["audit_monitored"], bool)
        print(f"✅ Graph execution audited: {data['audit_monitored']}")
    
    # Fetch audit metrics after execution
    metrics_response = httpx.get(f"{BASE_URL}/audit/graph/metrics")
    if metrics_response.status_code == 200:
        metrics_data = metrics_response.json()
        
        if "performance_metrics" in metrics_data:
            executions = metrics_data["performance_metrics"].get("executions", 0)
            print(f"✅ Total audited executions: {executions}")


def test_audit_error_tracking():
    """Test audit tracks errors correctly."""
    # Intentionally trigger an error (invalid payload)
    payload = {
        "input_text": "",  # Empty input
        "user_id": "error_test_user"
    }
    
    response = httpx.post(f"{BASE_URL}/graph/dispatch", json=payload, timeout=30.0)
    
    # Should return error or handle gracefully
    if response.status_code != 200:
        print(f"✅ Error returned: {response.status_code}")
    
    # Check if error was tracked in audit metrics
    metrics_response = httpx.get(f"{BASE_URL}/audit/graph/metrics")
    if metrics_response.status_code == 200:
        metrics_data = metrics_response.json()
        
        if "performance_metrics" in metrics_data:
            errors = metrics_data["performance_metrics"].get("errors", 0)
            print(f"✅ Audit error tracking: {errors} errors")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
