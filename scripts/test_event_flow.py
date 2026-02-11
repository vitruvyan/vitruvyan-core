#!/usr/bin/env python3
"""
Test Event Flow — Synthetic Event Test

Publishes a test event and verifies delivery + acknowledgment.
"""

import redis
import json
import time
import sys
import os

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

def test_event_flow():
    """Test synthetic event flow through the bus"""
    
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=False)
    
    print("=" * 80)
    print("SYNAPTIC BUS EVENT FLOW TEST")
    print("=" * 80)
    print()
    
    # Test event
    test_channel = "memory.coherence.requested"
    test_stream = f"vitruvyan:{test_channel}"
    test_group = "memory_orders_group"
    
    # 1. Check current state
    print(f"📊 Stream: {test_stream}")
    try:
        info = r.execute_command("XINFO", "STREAM", test_stream)
        length = info[1]
        print(f"   Current length: {length} events")
    except redis.ResponseError:
        print(f"   ⚠️  Stream does not exist yet")
        length = 0
    
    # 2. Check consumer group
    try:
        groups = r.execute_command("XINFO", "GROUPS", test_stream)
        print(f"   Consumer groups: {len(groups) // 12}")
        
        # Parse group info
        i = 0
        while i < len(groups):
            if groups[i] in [b'name', 'name']:
                name = groups[i+1]
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                consumers_count = groups[i+3] if isinstance(groups[i+3], int) else 0
                pending = groups[i+5] if isinstance(groups[i+5], int) else 0
                print(f"     - {name}: {consumers_count} consumers, {pending} pending")
                i += 12
            else:
                i += 1
    except redis.ResponseError:
        print(f"   ⚠️  No consumer groups")
    
    print()
    
    # 3. Publish test event
    print("📤 Publishing test event...")
    
    payload = {
        "test": True,
        "message": "Synaptic Bus health check",
        "timestamp": time.time()
    }
    
    fields = {
        'emitter': 'audit_script',
        'payload': json.dumps(payload),
        'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    event_id = r.xadd(test_stream, fields)
    print(f"   ✅ Event published: {event_id}")
    print()
    
    # 4. Wait and check if consumed
    print("⏳ Waiting 5 seconds for consumer processing...")
    time.sleep(5)
    
    # 5. Check pending messages
    try:
        groups = r.execute_command("XINFO", "GROUPS", test_stream)
        print(f"\n📬 Consumer group status after event:")
        
        i = 0
        while i < len(groups):
            if groups[i] in [b'name', 'name']:
                name = groups[i+1]
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                pending = groups[i+5] if len(groups) > i+5 and isinstance(groups[i+5], int) else 0
                
                if name == test_group:
                    if pending == 0:
                        print(f"   ✅ {name}: Event processed (0 pending)")
                    else:
                        print(f"   ⚠️  {name}: {pending} pending (not yet processed)")
                
                i += 12
            else:
                i += 1
    except Exception as e:
        print(f"   ❌ Error checking status: {e}")
    
    print()
    
    # 6. Check stream length
    try:
        info = r.execute_command("XINFO", "STREAM", test_stream)
        new_length = info[1]
        print(f"📊 Stream length: {length} → {new_length} (+{new_length - length})")
    except:
        pass
    
    print()
    print("=" * 80)
    print("✅ Event flow test complete")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_event_flow()
    except redis.ConnectionError:
        print(f"❌ Cannot connect to Redis at {REDIS_HOST}:{REDIS_PORT}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
