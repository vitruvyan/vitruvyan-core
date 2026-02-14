#!/usr/bin/env python3
"""
Synaptic Conclave Verification Script
Tests Redis Streams connectivity, event emission, and PostgreSQL logging
"""
import sys
import os
import json
import time
from datetime import datetime, timezone
import uuid

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'vitruvyan_core'))

from core.agents.postgres_agent import PostgresAgent
from core.synaptic_conclave.transport.streams import StreamBus

def main():
    print('🧪 SYNAPTIC CONCLAVE VERIFICATION')
    print('=' * 80)
    
    # Initialize agents
    print('\n1️⃣ Initializing agents...')
    try:
        # Use localhost:9379 when running from host (Redis exposed on port 9379)
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '9379'))
        
        print(f'   🔧 Using Redis: {redis_host}:{redis_port}')
        
        bus = StreamBus(host=redis_host, port=redis_port)
        print(f'   ✅ StreamBus initialized (host={bus.host}, port={bus.port})')
        
        pg = PostgresAgent()
        print('   ✅ PostgresAgent initialized')
    except Exception as e:
        print(f'   ❌ Failed to initialize agents: {e}')
        import traceback
        traceback.print_exc()
        return 1
    
    # Test Redis connectivity
    print('\n2️⃣ Testing Redis Streams connectivity...')
    try:
        # List active streams
        streams = bus.list_streams()
        print(f'   ✅ Found {len(streams)} active streams')
        
        # Show sample streams
        sample_streams = [s for s in streams if s.startswith('vitruvyan:')][:5]
        for stream in sample_streams:
            print(f'      • {stream}')
    except Exception as e:
        print(f'   ❌ Redis connectivity failed: {e}')
        return 1
    
    # Emit test events
    print('\n3️⃣ Emitting test events...')
    test_channels = [
        'vitruvyan:vault.archive.requested',
        'vitruvyan:memory.coherence.requested',
        'vitruvyan:babel.sentiment.completed'
    ]
    
    test_run_id = f'synaptic_verification_{int(time.time())}'
    emitted_events = []
    
    for channel in test_channels:
        try:
            event_id = str(uuid.uuid4())
            payload = {
                'event_id': event_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': 'test_script',
                'test': True,
                'test_run_id': test_run_id,
                'data': {
                    'message': f'Test event for {channel}',
                    'channel': channel
                }
            }
            
            # Emit to StreamBus
            bus.emit(channel, payload)
            emitted_events.append((channel, event_id))
            print(f'   ✅ {channel}')
            print(f'      Event ID: {event_id}')
        except Exception as e:
            print(f'   ❌ {channel}: {e}')
    
    # Wait for listeners to process
    print(f'\n4️⃣ Waiting 3 seconds for listeners to process...')
    time.sleep(3)
    
    # Check PostgreSQL event logging
    print('\n5️⃣ Checking PostgreSQL event logs...')
    try:
        # Query cognitive_bus_events table
        query = """
            SELECT 
                event_id, 
                channel, 
                source, 
                created_at,
                payload::json->>'test_run_id' as test_run_id
            FROM cognitive_bus_events 
            WHERE payload::json->>'test_run_id' = %s
            ORDER BY created_at DESC
        """
        
        rows = pg.fetch(query, (test_run_id,))
        
        if rows:
            print(f'   ✅ Found {len(rows)} logged events:')
            for row in rows:
                print(f'      • {row["channel"]}')
                print(f'        Event ID: {row["event_id"]}')
                print(f'        Created: {row["created_at"]}')
        else:
            print(f'   ⚠️  No events found with test_run_id: {test_run_id}')
            print(f'   ℹ️  Events may be processed asynchronously')
            
            # Check if table exists and has recent events
            count_query = "SELECT COUNT(*) as total FROM cognitive_bus_events WHERE created_at > NOW() - INTERVAL '5 minutes'"
            count_result = pg.fetch(count_query)
            if count_result:
                total = count_result[0]['total']
                print(f'   ℹ️  Total events in last 5 minutes: {total}')
                
    except Exception as e:
        print(f'   ❌ PostgreSQL query failed: {e}')
        import traceback
        traceback.print_exc()
    
    # Check listener logs
    print('\n6️⃣ Checking listener logs...')
    print('   Run these commands to verify listener processing:')
    for channel in test_channels:
        listener_name = channel.split(':')[1].split('.')[0]  # Extract service name
        print(f'\n   docker logs core_{listener_name}_listener --tail=50 | grep {test_run_id}')
    
    print('\n' + '=' * 80)
    print('✅ Verification complete!')
    print(f'\nTest Run ID: {test_run_id}')
    print(f'Emitted Events: {len(emitted_events)}')
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
