#!/usr/bin/env python3
"""
REDIS STREAMS PRODUCER EXAMPLE
==============================

This example shows how any service can emit events to Redis Streams.

The producer doesn't need to know:
- Who will consume the events
- When they will be processed
- How many workers exist

This is the beauty of Level 1 — pure transport, decoupled.

Usage:
    # Emit 10 events
    python3 examples/stream_producer_example.py
    
    # Emit 100 events with custom channel
    python3 examples/stream_producer_example.py --count 100 --channel test:entity

Author: Vitruvyan Core Team
Created: 2026-01-18
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vitruvyan_core.core.synaptic_conclave import StreamBus

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Emit events to Redis Streams')
    parser.add_argument('--count', type=int, default=10, help='Number of events to emit')
    parser.add_argument('--channel', default='codex:entity_updated', help='Stream channel')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between events (seconds)')
    parser.add_argument('--redis-host', default='localhost', help='Redis host')
    parser.add_argument('--redis-port', type=int, default=9379, help='Redis port')
    
    args = parser.parse_args()
    
    # Connect to bus
    bus = StreamBus(host=args.redis_host, port=args.redis_port)
    
    logger.info("=" * 60)
    logger.info("📤 STREAM PRODUCER")
    logger.info(f"   Channel: {args.channel}")
    logger.info(f"   Count: {args.count}")
    logger.info(f"   Delay: {args.delay}s")
    logger.info("=" * 60)
    
    # Check health
    health = bus.health()
    if health['status'] != 'healthy':
        logger.error(f"❌ Redis unhealthy: {health}")
        sys.exit(1)
    
    logger.info(f"✅ Connected to Redis: {health['host']}")
    
    # Emit events
    actions = ['create', 'update', 'delete', 'archive', 'restore']
    start_time = time.time()
    
    for i in range(1, args.count + 1):
        # Create payload (opaque to the bus)
        payload = {
            'entity_id': f'E{i:05d}',
            'action': actions[i % len(actions)],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'metadata': {
                'source': 'producer_example',
                'batch': i
            }
        }
        
        # Emit (Level 1 operation — no interpretation)
        event_id = bus.emit(
            channel=args.channel,
            payload=payload,
            emitter='stream-producer-example',
            correlation_id=f'batch-{i//10}'
        )
        
        logger.info(f"📤 [{i}/{args.count}] Emitted {payload['entity_id']}: {event_id}")
        
        # Rate limiting
        if i < args.count:
            time.sleep(args.delay)
    
    # Final stats
    elapsed = time.time() - start_time
    rate = args.count / elapsed
    
    logger.info("=" * 60)
    logger.info(f"✅ Emitted {args.count} events in {elapsed:.1f}s ({rate:.1f} events/sec)")
    
    # Show stream info
    info = bus.stream_info(args.channel)
    logger.info(f"📊 Stream length: {info.get('length', 0)}")
    logger.info(f"📊 Consumer groups: {len(info.get('groups', []))}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
