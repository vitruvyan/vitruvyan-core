#!/usr/bin/env python3
"""
02_initiate_audit.py
Initiate audit confession and poll for results

Usage: python3 02_initiate_audit.py
Expected: Async audit workflow with polling until completion
"""

import requests
import time
import json
from typing import Dict

BASE_URL = "http://localhost:9006"

def initiate_audit(service: str, event_data: Dict) -> str:
    """
    Initiate audit confession.
    
    Returns:
        confession_id: Unique ID for polling
    """
    response = requests.post(
        f"{BASE_URL}/confession/initiate",
        json={
            "service": service,
            "event_type": "test_audit",
            "payload": event_data
        }
    )
    response.raise_for_status()
    result = response.json()
    return result["confession_id"]

def poll_status(confession_id: str, timeout: int = 60, interval: int = 2) -> Dict:
    """
    Poll audit status until completion or timeout.
    
    Returns:
        Final status dict
    """
    elapsed = 0
    while elapsed < timeout:
        response = requests.get(
            f"{BASE_URL}/confession/{confession_id}/status"
        )
        response.raise_for_status()
        status = response.json()
        
        if status["status"] in ["blessed", "heretical", "failed"]:
            return status
        
        print(f"⏳ Status: {status['status']}... (elapsed: {elapsed}s)")
        time.sleep(interval)
        elapsed += interval
    
    raise TimeoutError(f"Audit did not complete within {timeout}s")

def main():
    print("🏛️ Orthodoxy Wardens - Audit Workflow Test")
    print("=" * 50)
    
    # Step 1: Initiate confession
    print("\n📤 Triggering audit confession...")
    test_payload = {
        "action": "neural_engine_screening",
        "profile": "balanced",
        "tickers": ["AAPL", "NVDA"],
        "timestamp": time.time()
    }
    
    try:
        confession_id = initiate_audit("test_service", test_payload)
        print(f"✅ Confession initiated: ID={confession_id}")
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to Orthodoxy Wardens at http://localhost:9006")
        print("   Make sure the container is running: docker compose up vitruvyan_api_orthodoxy_wardens")
        return
    except Exception as e:
        print(f"❌ Error initiating confession: {e}")
        return
    
    # Step 2: Poll for completion
    print("\n⏳ Polling audit status...")
    try:
        final_status = poll_status(confession_id, timeout=60, interval=2)
        
        # Step 3: Display results
        print("\n📊 Audit Results:")
        print(f"   Status: {final_status['status']}")
        print(f"   Orthodoxy Points: {final_status.get('orthodoxy_score', 'N/A')}")
        
        if "findings" in final_status:
            print("\n🔍 Findings:")
            for finding in final_status["findings"][:5]:  # Show top 5
                print(f"   • {finding}")
        
        if final_status["status"] == "blessed":
            print("\n✅ Audit PASSED - All Sacred Orders compliance maintained")
        elif final_status["status"] == "heretical":
            print("\n⚠️  Audit FAILED - Violations detected")
        else:
            print(f"\n❌ Audit ERROR - Status: {final_status['status']}")
    
    except TimeoutError as e:
        print(f"\n❌ {e}")
    except Exception as e:
        print(f"\n❌ Error during polling: {e}")

if __name__ == "__main__":
    main()
