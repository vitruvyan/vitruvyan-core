#!/usr/bin/env python3
"""
Synaptic Bus Simulator — Event Traffic Generator
Simulates realistic event traffic across all Sacred Orders to populate Grafana dashboard.

Usage:
    python synaptic_bus_simulator.py --duration 300 --intensity medium
    python synaptic_bus_simulator.py --continuous --intensity high
"""

import argparse
import asyncio
import json
import logging
import random
import time
import uuid
from datetime import datetime
from typing import Dict, List

import redis

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# EVENT TEMPLATES — Realistic payloads for each Sacred Order
# =============================================================================

MEMORY_EVENTS = [
    {
        "channel": "memory.coherence.requested",
        "template": {
            "event_type": "coherence.analysis",
            "entity_id": lambda: f"entity_{random.randint(1000, 9999)}",
            "context": lambda: random.choice([
                "market_analysis", "portfolio_review", "risk_assessment",
                "trend_detection", "sentiment_analysis", "news_digest"
            ]),
            "vector_count": lambda: random.randint(10, 500),
        }
    },
    {
        "channel": "memory.write.completed",
        "template": {
            "event_type": "memory.persisted",
            "entity_id": lambda: f"entity_{random.randint(1000, 9999)}",
            "vectors_written": lambda: random.randint(5, 200),
            "archivarium_status": "success",
        }
    },
]

VAULT_EVENTS = [
    {
        "channel": "vault.archive.requested",
        "template": {
            "event_type": "archival.request",
            "entity_type": lambda: random.choice(["conversation", "analysis", "verdict", "snapshot"]),
            "size_bytes": lambda: random.randint(1024, 1048576),
            "retention_policy": lambda: random.choice(["permanent", "long", "medium", "short"]),
        }
    },
    {
        "channel": "vault.snapshot.created",
        "template": {
            "event_type": "snapshot.persisted",
            "snapshot_id": lambda: f"snap_{uuid.uuid4().hex[:12]}",
            "entity_count": lambda: random.randint(10, 1000),
        }
    },
]

ORTHODOXY_EVENTS = [
    {
        "channel": "orthodoxy.audit.requested",
        "template": {
            "event_type": "audit.confession",
            "confession_type": lambda: random.choice(["code_review", "data_validation", "compliance_check"]),
            "severity": lambda: random.choice(["low", "medium", "high", "critical"]),
            "source": lambda: random.choice(["neural_engine", "babel_gardens", "pattern_weavers"]),
        }
    },
    {
        "channel": "orthodoxy.validation.requested",
        "template": {
            "event_type": "validation.request",
            "target": lambda: random.choice(["hallucination_check", "epistemic_audit", "architectural_review"]),
        }
    },
]

BABEL_EVENTS = [
    {
        "channel": "babel.sentiment.completed",
        "template": {
            "event_type": "sentiment.analyzed",
            "entity_id": lambda: f"news_{random.randint(1000, 9999)}",
            "sentiment_score": lambda: round(random.uniform(-1.0, 1.0), 3),
            "language": lambda: random.choice(["en", "it", "es", "fr", "de"]),
        }
    },
    {
        "channel": "babel.translation.completed",
        "template": {
            "event_type": "translation.done",
            "source_lang": lambda: random.choice(["en", "it", "es"]),
            "target_lang": lambda: random.choice(["en", "it", "es"]),
            "word_count": lambda: random.randint(50, 2000),
        }
    },
]

CODEX_EVENTS = [
    {
        "channel": "codex.discovery.mapped",
        "template": {
            "event_type": "entity.discovered",
            "entity_id": lambda: f"ticker_{random.choice(['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'META', 'AMZN'])}",
            "discovery_method": lambda: random.choice(["text_extraction", "api_fetch", "semantic_search"]),
        }
    },
    {
        "channel": "codex.enrichment.completed",
        "template": {
            "event_type": "entity.enriched",
            "entity_id": lambda: f"entity_{random.randint(1000, 9999)}",
            "fields_added": lambda: random.randint(3, 15),
        }
    },
]

PATTERN_EVENTS = [
    {
        "channel": "pattern_weavers.pattern.detected",
        "template": {
            "event_type": "pattern.found",
            "pattern_type": lambda: random.choice(["trend", "anomaly", "correlation", "seasonality"]),
            "confidence": lambda: round(random.uniform(0.5, 1.0), 3),
            "entity_count": lambda: random.randint(5, 100),
        }
    },
    {
        "channel": "pattern_weavers.analysis.completed",
        "template": {
            "event_type": "analysis.done",
            "dataset_size": lambda: random.randint(100, 10000),
            "patterns_found": lambda: random.randint(0, 20),
        }
    },
]

NEURAL_ENGINE_EVENTS = [
    {
        "channel": "engine.eval.completed",
        "template": {
            "event_type": "screening.result",
            "entities_screened": lambda: random.randint(10, 500),
            "top_ranked": lambda: random.randint(5, 50),
        }
    },
]

ALL_EVENT_TEMPLATES = (
    MEMORY_EVENTS + VAULT_EVENTS + ORTHODOXY_EVENTS + 
    BABEL_EVENTS + CODEX_EVENTS + PATTERN_EVENTS + NEURAL_ENGINE_EVENTS
)


# =============================================================================
# EVENT SIMULATOR
# =============================================================================

class SynapticBusSimulator:
    """Generates realistic event traffic for dashboard visualization."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.redis_client = redis.StrictRedis(
            host=host, port=port, db=db, decode_responses=False
        )
        self.event_templates = ALL_EVENT_TEMPLATES
        self.stats = {
            "events_published": 0,
            "errors": 0,
            "start_time": time.time(),
        }
        
    def generate_event(self, template: Dict) -> Dict:
        """Generate a single event from template with randomized values."""
        event = {
            "event_id": uuid.uuid4().hex,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "correlation_id": uuid.uuid4().hex[:16],
        }
        
        for key, value_func in template["template"].items():
            if callable(value_func):
                event[key] = value_func()
            else:
                event[key] = value_func
                
        return event
    
    def publish_event(self, channel: str, event: Dict) -> bool:
        """Publish event to Redis Streams."""
        try:
            payload = json.dumps(event).encode('utf-8')
            message_id = self.redis_client.xadd(
                channel, 
                {"payload": payload},
                maxlen=10000,  # Limit stream length
                approximate=True
            )
            self.stats["events_published"] += 1
            logger.debug(f"📤 {channel}: {event['event_type']} (id: {message_id.decode()})")
            return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"❌ Failed to publish to {channel}: {e}")
            return False
    
    def get_intensity_config(self, intensity: str) -> Dict:
        """Get event generation configuration based on intensity level."""
        configs = {
            "low": {
                "events_per_minute": 10,
                "burst_probability": 0.1,
                "burst_multiplier": 2,
            },
            "medium": {
                "events_per_minute": 60,
                "burst_probability": 0.2,
                "burst_multiplier": 3,
            },
            "high": {
                "events_per_minute": 200,
                "burst_probability": 0.3,
                "burst_multiplier": 5,
            },
            "extreme": {
                "events_per_minute": 500,
                "burst_probability": 0.5,
                "burst_multiplier": 10,
            },
        }
        return configs.get(intensity.lower(), configs["medium"])
    
    async def simulate_traffic(self, duration_seconds: int = 0, intensity: str = "medium"):
        """
        Simulate event traffic for specified duration.
        
        Args:
            duration_seconds: Duration in seconds (0 = continuous)
            intensity: Traffic intensity (low, medium, high, extreme)
        """
        config = self.get_intensity_config(intensity)
        base_interval = 60.0 / config["events_per_minute"]
        
        logger.info(f"🚀 Starting simulator — Intensity: {intensity.upper()}")
        logger.info(f"   Base rate: {config['events_per_minute']} events/min")
        logger.info(f"   Burst: {config['burst_probability']*100:.0f}% chance, {config['burst_multiplier']}x multiplier")
        if duration_seconds > 0:
            logger.info(f"   Duration: {duration_seconds}s")
        else:
            logger.info(f"   Duration: CONTINUOUS (Ctrl+C to stop)")
        
        start_time = time.time()
        
        try:
            while True:
                # Check duration
                if duration_seconds > 0 and (time.time() - start_time) >= duration_seconds:
                    logger.info(f"⏱️ Duration reached ({duration_seconds}s), stopping...")
                    break
                
                # Determine if this is a burst cycle
                is_burst = random.random() < config["burst_probability"]
                events_to_generate = 1
                
                if is_burst:
                    events_to_generate = config["burst_multiplier"]
                    logger.info(f"💥 BURST: Generating {events_to_generate} events")
                
                # Generate events
                for _ in range(events_to_generate):
                    template = random.choice(self.event_templates)
                    event = self.generate_event(template)
                    self.publish_event(template["channel"], event)
                
                # Print stats every 100 events
                if self.stats["events_published"] % 100 == 0:
                    elapsed = time.time() - self.stats["start_time"]
                    rate = self.stats["events_published"] / elapsed if elapsed > 0 else 0
                    logger.info(
                        f"📊 Stats: {self.stats['events_published']} events published, "
                        f"{rate:.1f} events/s, {self.stats['errors']} errors"
                    )
                
                # Wait before next event (with jitter)
                jitter = random.uniform(0.5, 1.5)
                await asyncio.sleep(base_interval * jitter)
                
        except KeyboardInterrupt:
            logger.info("⚠️ Interrupted by user")
        
        # Final stats
        elapsed = time.time() - self.stats["start_time"]
        rate = self.stats["events_published"] / elapsed if elapsed > 0 else 0
        logger.info(f"")
        logger.info(f"✅ Simulation Complete")
        logger.info(f"   Total events: {self.stats['events_published']}")
        logger.info(f"   Duration: {elapsed:.1f}s")
        logger.info(f"   Average rate: {rate:.1f} events/s")
        logger.info(f"   Errors: {self.stats['errors']}")
    
    def test_connectivity(self) -> bool:
        """Test Redis connection."""
        try:
            self.redis_client.ping()
            logger.info("✅ Redis connection successful")
            
            # Show existing streams
            streams = []
            for key in self.redis_client.scan_iter(match="*", count=1000):
                key_str = key.decode() if isinstance(key, bytes) else key
                key_type = self.redis_client.type(key)
                if key_type == b'stream' or key_type == 'stream':
                    length = self.redis_client.xlen(key)
                    streams.append((key_str, length))
            
            logger.info(f"📊 Found {len(streams)} existing streams:")
            for stream_name, length in sorted(streams, key=lambda x: x[1], reverse=True)[:10]:
                logger.info(f"   - {stream_name}: {length} messages")
            
            return True
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            return False


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Synaptic Bus Traffic Simulator — Populate Grafana Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run for 5 minutes with medium intensity
  python synaptic_bus_simulator.py --duration 300 --intensity medium
  
  # Run continuously with high intensity (Ctrl+C to stop)
  python synaptic_bus_simulator.py --continuous --intensity high
  
  # Test Redis connection only
  python synaptic_bus_simulator.py --test
  
  # Low intensity for 1 hour
  python synaptic_bus_simulator.py --duration 3600 --intensity low
        """
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        default=0,
        help="Simulation duration in seconds (0 = continuous)"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously (same as --duration 0)"
    )
    parser.add_argument(
        "--intensity",
        choices=["low", "medium", "high", "extreme"],
        default="medium",
        help="Event generation intensity"
    )
    parser.add_argument(
        "--redis-host",
        default="localhost",
        help="Redis host (default: localhost)"
    )
    parser.add_argument(
        "--redis-port",
        type=int,
        default=6379,
        help="Redis port (default: 6379)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test Redis connection and exit"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create simulator
    simulator = SynapticBusSimulator(
        host=args.redis_host,
        port=args.redis_port
    )
    
    # Test mode
    if args.test:
        simulator.test_connectivity()
        return
    
    # Determine duration
    duration = 0 if args.continuous else args.duration
    
    # Run simulation
    asyncio.run(simulator.simulate_traffic(
        duration_seconds=duration,
        intensity=args.intensity
    ))


if __name__ == "__main__":
    main()
