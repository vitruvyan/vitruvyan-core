#!/usr/bin/env python3
"""
05_compare_profiles.py
Compare screening results between balanced and aggressive profiles

Usage: python3 05_compare_profiles.py
Expected: Side-by-side comparison showing how profile weights affect ranking
"""

import requests
import json
from typing import Dict, List

BASE_URL = "http://localhost:9003"

def screen(profile: str, top_k: int = 5) -> Dict:
    """Execute screening request"""
    response = requests.post(
        f"{BASE_URL}/screen",
        json={
            "profile": profile,
            "top_k": top_k,
            "stratification_mode": "global"
        }
    )
    response.raise_for_status()
    return response.json()

def main():
    print("🧠 Neural Engine Profile Comparison")
    print("=" * 60)
    
    # Screen with both profiles
    print("\n⏳ Screening with balanced profile...")
    balanced = screen("balanced")
    
    print("⏳ Screening with aggressive profile...")
    aggressive = screen("aggressive")
    
    # Display results side-by-side
    print("\n📊 Top 3 Results Comparison:\n")
    
    print(f"{'Rank':<6} {'Balanced Profile':<25} {'Aggressive Profile':<25}")
    print("-" * 60)
    
    for i in range(min(3, len(balanced["ranked_entities"]))):
        b_entity = balanced["ranked_entities"][i]
        a_entity = aggressive["ranked_entities"][i]
        
        print(f"{i+1:<6} "
              f"{b_entity['entity_id']:<10} (score: {b_entity['composite_score']:>6.2f}) "
              f"{a_entity['entity_id']:<10} (score: {a_entity['composite_score']:>6.2f})")
    
    # Analyze differences
    print("\n💡 Key Insights:")
    
    b_top1 = balanced["ranked_entities"][0]["entity_id"]
    a_top1 = aggressive["ranked_entities"][0]["entity_id"]
    
    if b_top1 == a_top1:
        print(f"   ✓ Both profiles agree on top entity: {b_top1}")
    else:
        print(f"   ⚠ Different top entities: {b_top1} (balanced) vs {a_top1} (aggressive)")
    
    # Check rank correlation
    b_ids = [e["entity_id"] for e in balanced["ranked_entities"][:5]]
    a_ids = [e["entity_id"] for e in aggressive["ranked_entities"][:5]]
    
    overlap = len(set(b_ids) & set(a_ids))
    print(f"   • Top-5 overlap: {overlap}/5 entities")
    
    print("\n✅ Comparison complete")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to Neural Engine at http://localhost:9003")
        print("   Make sure the container is running: docker compose up neural_engine")
    except Exception as e:
        print(f"❌ Error: {e}")
