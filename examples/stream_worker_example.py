#!/usr/bin/env python3
"""
REDIS STREAMS WORKER EXAMPLE
============================

This example demonstrates how a vertical (domain-specific service) uses
the Cognitive Bus Streams for durable event processing.

Architecture:
    Producer (any service) → Stream → Consumer Group → Worker (this file)
    
Key principles:
    1. The bus (Level 1) only transports — it doesn't interpret
    2. The worker (vertical) interprets — it assigns meaning to events
    3. Events are durable — workers can crash and resume
    4. Consumer groups enable horizontal scaling

Usage:
    # Terminal 1 - Start worker
    python3 examples/stream_worker_example.py
    
    # Terminal 2 - Produce events
    python3 examples/stream_producer_example.py

Author: Vitruvyan Core Team
Created: 2026-01-18
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vitruvyan_core.core.foundation.cognitive_bus import StreamBus, StreamEvent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# VERTICAL-SPECIFIC LOGIC (This is where interpretation happens)
# ============================================================================

class EntityIndexer:
    """
    Example vertical service that processes entity update events.
    
    This is Level 2+ logic — interpretation, not transport.
    The bus doesn't know what an "entity" is.
    """
    
    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
    
    def process_entity_update(self, event: StreamEvent) -> bool:
        """
        Process entity update event.
        
        This is where the vertical assigns MEANING to the opaque payload.
        The bus just transported bytes — we interpret them as "entity update".
        """
        try:
            payload = event.payload
            entity_id = payload.get('entity_id', 'unknown')
            action = payload.get('action', 'unknown')
            
            # Simulate processing
            logger.info(
                f"📦 Processing entity {entity_id}: action={action}, "
                f"emitter={event.emitter}, id={event.event_id}"
            )
            
            # Here a real vertical would:
            # - Update database
            # - Update search index
            # - Trigger downstream events
            # - Update vector embeddings
            # etc.
            
            time.sleep(0.1)  # Simulate work
            
            self.processed_count += 1
            logger.info(f"✅ Processed entity {entity_id} (total: {self.processed_count})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing event {event.event_id}: {e}")
            self.error_count += 1
            return False


# ============================================================================
# WORKER LOOP (Connects Level 1 transport to Level 2+ interpretation)
# ============================================================================

class StreamWorker:
    """
    Worker that consumes from a Redis Stream.
    
    This demonstrates the clean separation:
    - Bus (Level 1): Delivers events durably
    - Worker: Interprets events according to vertical logic
    """
    
    def __init__(
        self,
        stream_channel: str,
        consumer_group: str,
        consumer_name: str,
        processor,
        redis_host: str = 'localhost',
        redis_port: int = 9379
    ):
        self.stream_channel = stream_channel
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.processor = processor
        
        self.bus = StreamBus(host=redis_host, port=redis_port)
        self.running = False
        
        # Stats
        self.start_time = datetime.utcnow()
        self.events_processed = 0
        self.events_failed = 0
    
    def start(self):
        """Start consuming events."""
        self.running = True
        
        logger.info("=" * 60)
        logger.info("🚀 STREAM WORKER STARTING")
        logger.info(f"   Channel: {self.stream_channel}")
        logger.info(f"   Group: {self.consumer_group}")
        logger.info(f"   Consumer: {self.consumer_name}")
        logger.info("=" * 60)
        
        # Ensure consumer group exists
        created = self.bus.create_consumer_group(
            self.stream_channel,
            self.consumer_group,
            start_id="0"  # Process from beginning (for demo)
        )
        if created:
            logger.info(f"✅ Created consumer group '{self.consumer_group}'")
        else:
            logger.info(f"ℹ️  Consumer group '{self.consumer_group}' already exists")
        
        logger.info(f"👂 Listening for events... (Ctrl+C to stop)")
        
        try:
            # Consume loop (blocking generator)
            for event in self.bus.consume(
                channel=self.stream_channel,
                group=self.consumer_group,
                consumer=self.consumer_name,
                count=10,      # Batch size
                block_ms=5000  # 5 second timeout
            ):
                if not self.running:
                    break
                
                # Process event (vertical-specific logic)
                success = self.processor.process_entity_update(event)
                
                if success:
                    # ACK the event (Level 1 operation)
                    self.bus.ack(event, self.consumer_group)
                    self.events_processed += 1
                else:
                    # Don't ACK — event will be redelivered
                    self.events_failed += 1
                    logger.warning(f"⚠️  Event {event.event_id} not ACKed (will retry)")
                
                # Show stats every 10 events
                if self.events_processed % 10 == 0:
                    self._show_stats()
        
        except KeyboardInterrupt:
            logger.info("\n⏸️  Received interrupt signal")
        except Exception as e:
            logger.error(f"❌ Worker error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop consuming."""
        self.running = False
        self._show_stats()
        logger.info("👋 Worker stopped gracefully")
    
    def _show_stats(self):
        """Display processing statistics."""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        rate = self.events_processed / uptime if uptime > 0 else 0
        
        logger.info(
            f"📊 Stats: {self.events_processed} processed, "
            f"{self.events_failed} failed, "
            f"{rate:.1f} events/sec"
        )


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run example worker."""
    
    # Configuration (in production, use env vars)
    STREAM_CHANNEL = os.getenv('STREAM_CHANNEL', 'codex:entity_updated')
    CONSUMER_GROUP = os.getenv('CONSUMER_GROUP', 'entity-indexer-group')
    CONSUMER_NAME = os.getenv('CONSUMER_NAME', f'worker-{os.getpid()}')
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '9379'))
    
    # Initialize processor (vertical-specific)
    processor = EntityIndexer()
    
    # Create and start worker
    worker = StreamWorker(
        stream_channel=STREAM_CHANNEL,
        consumer_group=CONSUMER_GROUP,
        consumer_name=CONSUMER_NAME,
        processor=processor,
        redis_host=REDIS_HOST,
        redis_port=REDIS_PORT
    )
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info(f"\n⚠️  Received signal {sig}")
        worker.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start consuming
    worker.start()


if __name__ == '__main__':
    main()
