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
            "confession_type": "system_compliance",
            "sacred_scope": "complete_realm",
            "urgency": "divine_routine",
            "penitent_service": service
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
        
        # sacred_status can be: confessing, purifying, blessed, heretical, failed
        if status["sacred_status"] in ["blessed", "heretical", "failed"]:
            return status
        
        print(f"⏳ Status: {status['sacred_status']}... (elapsed: {elapsed}s)")
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
        final_status= poll_status(confession_id, timeout=60, interval=2)
        
        # Step 3: Display results
        print("\n📊 Audit Results:")
        print(f"   Status: {final_status['sacred_status']}")
        print(f"   Penance Progress: {final_status.get('penance_progress', 'N/A')}")
        print(f"   Assigned Warden: {final_status.get('assigned_warden', 'N/A')}")
        
        if "divine_results" in final_status and final_status["divine_results"]:
            print("\n🔍 Divine Results:")
            results = final_status["divine_results"]
            for key, value in list(results.items())[:5]:  # Show top 5
                print(f"   • {key}: {value}")
        
        if final_status["sacred_status"] == "blessed":
            print("\n✅ Audit PASSED - All Sacred Orders compliance maintained")
        elif final_status["sacred_status"] == "heretical":
            print("\n⚠️  Audit FAILED - Violations detected")
        else:
            print(f"\n❌ Audit ERROR - Status: {final_status['sacred_status']}")
    
    except TimeoutError as e:
        print(f"\n❌ {e}")
    except Exception as e:
        print(f"\n❌ Error during polling: {e}")

if __name__ == "__main__":
    main()
