#!/usr/bin/env python3
"""
Compare Screening Profiles Example
Compares ranking results between balanced and aggressive profiles.

Usage:
    python3 05_compare_profiles.py
    
    # Or with custom base URL
    BASE_URL=http://production-ip:8003 python3 05_compare_profiles.py
"""

import os
import sys
import json
import requests
from typing import Dict, List, Any

BASE_URL = os.getenv("BASE_URL", "http://localhost:8003")


def screen(profile: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Call Neural Engine /screen endpoint.
    
    Args:
        profile: Profile name (e.g., "balanced", "aggressive")
        top_k: Number of top entities to return
        
    Returns:
        Screening response JSON
    """
    response = requests.post(
        f"{BASE_URL}/screen",
        json={
            "profile": profile,
            "top_k": top_k
        },
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def print_ranked_entities(entities: List[Dict[str, Any]], profile_name: str):
    """Print ranked entities in formatted table."""
    print(f"\n{'=' * 70}")
    print(f"  {profile_name.upper()} PROFILE")
    print(f"{'=' * 70}")
    print(f"{'Rank':<6} {'Entity':<12} {'Composite':<12} {'Percentile':<12} {'Bucket':<10}")
    print(f"{'-' * 70}")
    
    for entity in entities:
        rank = entity['rank']
        entity_id = entity['entity_id']
        composite = entity['composite_score']
        percentile = entity['percentile']
        bucket = entity['bucket']
        
        print(f"{rank:<6} {entity_id:<12} {composite:<12.3f} {percentile:<12.1f} {bucket:<10}")


def compare_rankings(balanced: List[Dict], aggressive: List[Dict]):
    """Analyze ranking differences between profiles."""
    print(f"\n{'=' * 70}")
    print(f"  RANKING COMPARISON")
    print(f"{'=' * 70}")
    
    balanced_order = {e['entity_id']: e['rank'] for e in balanced}
    aggressive_order = {e['entity_id']: e['rank'] for e in aggressive}
    
    all_entities = set(balanced_order.keys()) | set(aggressive_order.keys())
    
    print(f"{'Entity':<12} {'Balanced Rank':<15} {'Aggressive Rank':<15} {'Δ Rank':<10}")
    print(f"{'-' * 70}")
    
    for entity_id in sorted(all_entities):
        bal_rank = balanced_order.get(entity_id, "—")
        agg_rank = aggressive_order.get(entity_id, "—")
        
        if bal_rank != "—" and agg_rank != "—":
            delta = bal_rank - agg_rank
            delta_str = f"{delta:+d}"
        else:
            delta_str = "—"
        
        print(f"{entity_id:<12} {str(bal_rank):<15} {str(agg_rank):<15} {delta_str:<10}")


def main():
    print("🔬 Neural Engine Profile Comparison")
    print(f"Endpoint: {BASE_URL}")
    print("=" * 70)
    
    try:
        # Test health first
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print(f"❌ Service unhealthy: {health_response.status_code}")
            sys.exit(1)
        
        print("✅ Service health check passed")
        
        # Screen with balanced profile
        print("\n📊 Screening with BALANCED profile...")
        balanced_result = screen("balanced", top_k=5)
        balanced_entities = balanced_result['ranked_entities']
        balanced_time = balanced_result['processing_time_ms']
        
        # Screen with aggressive profile
        print("📊 Screening with AGGRESSIVE profile...")
        aggressive_result = screen("aggressive", top_k=5)
        aggressive_entities = aggressive_result['ranked_entities']
        aggressive_time = aggressive_result['processing_time_ms']
        
        # Print results
        print_ranked_entities(balanced_entities, "Balanced")
        print(f"\n⏱️  Processing time: {balanced_time:.2f}ms")
        
        print_ranked_entities(aggressive_entities, "Aggressive")
        print(f"\n⏱️  Processing time: {aggressive_time:.2f}ms")
        
        # Compare rankings
        compare_rankings(balanced_entities, aggressive_entities)
        
        # Print profile weights comparison
        print(f"\n{'=' * 70}")
        print(f"  PROFILE WEIGHTS")
        print(f"{'=' * 70}")
        print(f"{'Factor':<20} {'Balanced':<15} {'Aggressive':<15}")
        print(f"{'-' * 70}")
        
        balanced_weights = balanced_result['profile_weights']
        aggressive_weights = aggressive_result['profile_weights']
        
        all_factors = set(balanced_weights.keys()) | set(aggressive_weights.keys())
        for factor in sorted(all_factors):
            bal_w = balanced_weights.get(factor, 0.0)
            agg_w = aggressive_weights.get(factor, 0.0)
            print(f"{factor:<20} {bal_w:<15.3f} {agg_w:<15.3f}")
        
        print("\n✅ Comparison completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection error: Cannot reach {BASE_URL}")
        print("   Make sure Neural Engine container is running:")
        print("   docker compose up neural_engine")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"\n❌ Timeout: Service took too long to respond")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP error: {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"\n❌ Unexpected response format: Missing key {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
