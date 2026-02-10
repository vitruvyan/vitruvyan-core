#!/usr/bin/env python3
"""
API Memory Orders — Usage Examples

This script demonstrates how to interact with the API Memory Orders service
for monitoring dual-memory coherence between PostgreSQL and Qdrant.

Prerequisites:
- API Memory Orders service running on localhost:8000
- Or adjust BASE_URL accordingly

Run with: python examples/example_api_usage.py
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def check_coherence(pg_count: int, qdrant_count: int) -> Dict[str, Any]:
    """Check coherence between PostgreSQL and Qdrant counts."""
    payload = {
        "pg_count": pg_count,
        "qdrant_count": qdrant_count
    }

    try:
        response = requests.post(f"{BASE_URL}/coherence/check", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error checking coherence: {e}")
        return {}

def get_health() -> Dict[str, Any]:
    """Get overall service health status."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting health: {e}")
        return {}

def get_coherence_history() -> Dict[str, Any]:
    """Get recent coherence check history."""
    try:
        response = requests.get(f"{BASE_URL}/coherence/history")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting history: {e}")
        return {}

def main():
    """Run example API calls."""
    print("🔍 API Memory Orders — Coherence Monitoring Examples")
    print("=" * 60)

    # Example 1: Healthy coherence
    print("\n1. Checking healthy coherence (1000 PG vs 980 Qdrant):")
    result = check_coherence(1000, 980)
    if result:
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Drift: {result.get('drift_percentage', 0):.2f}%")
        print(f"   Recommendation: {result.get('recommendation', 'none')}")

    # Example 2: Warning coherence
    print("\n2. Checking warning coherence (1000 PG vs 850 Qdrant):")
    result = check_coherence(1000, 850)
    if result:
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Drift: {result.get('drift_percentage', 0):.2f}%")
        print(f"   Recommendation: {result.get('recommendation', 'none')}")

    # Example 3: Critical coherence
    print("\n3. Checking critical coherence (1000 PG vs 500 Qdrant):")
    result = check_coherence(1000, 500)
    if result:
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Drift: {result.get('drift_percentage', 0):.2f}%")
        print(f"   Recommendation: {result.get('recommendation', 'none')}")

    # Example 4: Service health
    print("\n4. Checking service health:")
    health = get_health()
    if health:
        print(f"   Status: {health.get('status', 'unknown')}")
        print(f"   Timestamp: {health.get('timestamp', 'unknown')}")
        components = health.get('components', {})
        for comp, status in components.items():
            print(f"   {comp}: {status}")

    # Example 5: Coherence history
    print("\n5. Recent coherence history:")
    history = get_coherence_history()
    if history:
        checks = history.get('checks', [])
        print(f"   Found {len(checks)} recent checks")
        for i, check in enumerate(checks[:3]):  # Show first 3
            print(f"   Check {i+1}: {check.get('status', 'unknown')} "
                  f"({check.get('drift_percentage', 0):.2f}% drift)")

    print("\n✅ Examples completed!")
    print("\n💡 Tip: Start the service with:")
    print("   cd services/api_memory_orders && python main.py")
    print("   Or: docker compose up -d api_memory_orders")

if __name__ == "__main__":
    main()