"""
Vault Keepers + Babel Gardens Integration Test

Tests signal timeseries archival end-to-end.
Requires Docker containers running (vault_keepers service + PostgreSQL).
"""

import requests
import json
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════
# Test Configuration
# ═══════════════════════════════════════════════════════════════════════

VAULT_KEEPERS_API = "http://localhost:9007"  # api_vault_keepers port
BABEL_GARDENS_API = "http://localhost:9009"  # api_babel_gardens port (if available)

def test_direct_signal_archival():
    """
    Test direct signal archival (bypass Babel Gardens for now).
    Simulates Babel Gardens signal extraction results.
    """
    print("=" * 80)
    print("TEST 1: Direct Signal Timeseries Archival")
    print("=" * 80)
    
    # Simulate Babel Gardens output (finance vertical)
    signal_results_finance = [
        {
            "signal_name": "sentiment_valence",
            "value": 0.65,
            "confidence": 0.88,
            "extraction_trace": {
                "method": "model:finbert",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "model_version": "finbert-0.4"
            },
            "source_text": "Apple announced record earnings for Q4 2025..."
        },
        {
            "signal_name": "sentiment_valence",
            "value": 0.72,
            "confidence": 0.91,
            "extraction_trace": {
                "method": "model:finbert",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "model_version": "finbert-0.4"
            },
            "source_text": "Strong iPhone 15 demand drives revenue growth..."
        }
    ]
    
    payload = {
        "entity_id": "AAPL",
        "signal_results": signal_results_finance,
        "vertical": "finance",
        "schema_version": "2.1",
        "retention_days": 365
    }
    
    print(f"Archiving {len(signal_results_finance)} signal data points for AAPL (finance)...")
    
    # Note: This endpoint needs to be added to api/routes.py
    # For now, we'll test the adapter directly
    print("⚠️  Note: POST /signal_timeseries endpoint needs to be added to api/routes.py")
    print(f"Expected payload: {json.dumps(payload, indent=2)}")
    
    return payload


def test_cybersecurity_signal_archival():
    """Test cybersecurity vertical (threat_severity)"""
    print("\n" + "=" * 80)
    print("TEST 2: Cybersecurity Signal Archival")
    print("=" * 80)
    
    signal_results_cyber = [
        {
            "signal_name": "threat_severity",
            "value": 0.42,
            "confidence": 0.95,
            "extraction_trace": {
                "method": "model:secbert",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        },
        {
            "signal_name": "threat_severity",
            "value": 0.89,
            "confidence": 0.87,
            "extraction_trace": {
                "method": "model:secbert",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    ]
    
    payload = {
        "entity_id": "192.168.1.100",
        "signal_results": signal_results_cyber,
        "vertical": "cybersecurity",
        "schema_version": "2.1",
        "retention_days": 90  # 3 months for security logs
    }
    
    print(f"Archiving {len(signal_results_cyber)} threat signals for 192.168.1.100...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    return payload


def test_healthcare_signal_archival():
    """Test healthcare vertical (diagnostic_confidence)"""
    print("\n" + "=" * 80)
    print("TEST 3: Healthcare Signal Archival")
    print("=" * 80)
    
    signal_results_healthcare = [
        {
            "signal_name": "diagnostic_confidence",
            "value": 0.73,
            "confidence": 0.92,
            "extraction_trace": {
                "method": "model:bioclinicalbert",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        },
        {
            "signal_name": "diagnostic_confidence",
            "value": 0.81,
            "confidence": 0.94,
            "extraction_trace": {
                "method": "model:bioclinicalbert",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    ]
    
    payload = {
        "entity_id": "patient_12345",
        "signal_results": signal_results_healthcare,
        "vertical": "healthcare",
        "schema_version": "2.1",
        "retention_days": 2555  # 7 years (HIPAA compliance)
    }
    
    print(f"Archiving {len(signal_results_healthcare)} diagnostic signals for patient_12345...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    return payload


def test_adapter_directly():
    """
    Test VaultBusAdapter directly (bypassing HTTP API).
    This should work even without API routes.
    """
    print("\n" + "=" * 80)
    print("TEST 4: Direct Adapter Test (Bypassing HTTP)")
    print("=" * 80)
    
    try:
        from services.api_vault_keepers.adapters.bus_adapter import VaultBusAdapter
        
        print("✅ Initializing VaultBusAdapter...")
        adapter = VaultBusAdapter()
        
        # Test finance archival
        print("\n📊 Archiving finance signals (AAPL)...")
        result_finance = adapter.handle_signal_timeseries_archival(
            entity_id="AAPL",
            signal_results=[
                {
                    "signal_name": "sentiment_valence",
                    "value": 0.65,
                    "confidence": 0.88,
                    "extraction_trace": {
                        "method": "model:finbert",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "model_version": "finbert-0.4"
                    },
                    "source_text": "Apple announced record earnings..."
                }
            ],
            vertical="finance"
        )
        
        print(f"✅ Finance archival result:")
        print(f"   - Timeseries ID: {result_finance['timeseries_id']}")
        print(f"   - Entity: {result_finance['entity_id']}")
        print(f"   - Signal: {result_finance['signal_name']}")
        print(f"   - Data points: {result_finance['data_points_count']}")
        print(f"   - Status: {result_finance['status']}")
        
        # Test cybersecurity archival
        print("\n🔒 Archiving cybersecurity signals (192.168.1.100)...")
        result_cyber = adapter.handle_signal_timeseries_archival(
            entity_id="192.168.1.100",
            signal_results=[
                {
                    "signal_name": "threat_severity",
                    "value": 0.89,
                    "confidence": 0.87,
                    "extraction_trace": {
                        "method": "model:secbert",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                }
            ],
            vertical="cybersecurity",
            retention_days=90
        )
        
        print(f"✅ Cybersecurity archival result:")
        print(f"   - Timeseries ID: {result_cyber['timeseries_id']}")
        print(f"   - Entity: {result_cyber['entity_id']}")
        print(f"  - Signal: {result_cyber['signal_name']}")
        print(f"   - Status: {result_cyber['status']}")
        
        # Test query
        print("\n🔍 Querying signals for AAPL...")
        query_result = adapter.query_signal_timeseries(
            entity_id="AAPL",
            signal_name="sentiment_valence",
            vertical="finance"
        )
        
        print(f"✅ Query result:")
        print(f"   - Timeseries count: {query_result['timeseries_count']}")
        if query_result['timeseries_count'] > 0:
            first = query_result['timeseries'][0]
            print(f"   - Latest timeseries:")
            print(f"       - ID: {first['timeseries_id']}")
            print(f"       - Entity: {first['entity_id']}")
            print(f"       - Signal: {first['signal_name']}")
            print(f"       - Vertical: {first['vertical']}")
        
        print("\n🎉 ALL TESTS PASSED")
        print("   - Finance vertical archival: ✅")
        print("   - Cybersecurity vertical archival: ✅")
        print("   - Signal query: ✅")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║  Vault Keepers + Babel Gardens Integration Test                  ║")
    print("║  Signal Timeseries Archival (v2.1)                                ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Test payload generation
    payload_finance = test_direct_signal_archival()
    payload_cyber = test_cybersecurity_signal_archival()
    payload_healthcare = test_healthcare_signal_archival()
    
    # Test adapter directly
    success = test_adapter_directly()
    
    if success:
        print("\n✅ Integration test successful!")
        print("   Next steps:")
        print("   1. Add POST /signal_timeseries endpoint to api/routes.py")
        print("   2. Add GET /signal_timeseries/<entity_id> query endpoint")
        print("   3. Integrate with Babel Gardens signal extraction")
    else:
        print("\n❌ Integration test failed. Check logs above.")
        exit(1)
