#!/usr/bin/env python3
"""
Redis Streams Prometheus Exporter
Monitors all Redis Streams and exposes metrics for Grafana dashboard visualization.

Exposes:
- stream_length: Number of messages in each stream
- stream_consumer_lag: Lag between last message ID and consumer group last read ID
- stream_pending_messages: Number of pending (unacknowledged) messages per consumer group
- cognitive_bus_events_total: Total events published/consumed per channel
- listener_consumed_total: Total events consumed by consumer group
"""

import logging
import os
import time
from typing import Dict, List, Set

import redis
from flask import Flask, Response
from prometheus_client import Counter, Gauge, generate_latest, REGISTRY

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("redis_streams_exporter")

# =============================================================================
# CONFIGURATION
# =============================================================================

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
EXPORTER_PORT = int(os.getenv("EXPORTER_PORT", "9121"))
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "15"))  # seconds

# =============================================================================
# PROMETHEUS METRICS
# =============================================================================

# Stream length (total messages in stream)
stream_length_gauge = Gauge(
    'stream_length',
    'Total messages in Redis Stream',
    ['stream']
)

# Consumer lag (difference between stream last ID and consumer last read ID)
stream_consumer_lag_gauge = Gauge(
    'stream_consumer_lag',
    'Lag between stream head and consumer group read position',
    ['stream', 'consumer_group']
)

# Pending messages (PEL size per consumer group)
stream_pending_messages_gauge = Gauge(
    'stream_pending_messages',
    'Number of pending (unacknowledged) messages per consumer group',
    ['stream', 'consumer_group']
)

# Events published (approximation from stream lengths)
cognitive_bus_events_published_counter = Counter(
    'cognitive_bus_events_total',
    'Total events published to each stream',
    ['channel', 'event_type']
)

# Events consumed (approximation from consumer group read positions)
listener_consumed_counter = Counter(
    'listener_consumed_total',
    'Total events consumed by consumer group',
    ['consumer_group', 'stream']
)

# Event rates (for graph visualization)
cognitive_bus_event_rate_gauge = Gauge(
    'cognitive_bus_event_rate',
    'Current event publishing rate per stream',
    ['stream', 'job']
)

# Consumer health status
consumer_group_health_gauge = Gauge(
    'consumer_group_health',
    'Health status of consumer group (1=healthy, 0=unhealthy)',
    ['consumer_group', 'stream']
)

# Stream to stream connections (for node graph)
stream_connection_gauge = Gauge(
    'stream_connection',
    'Connection weight between streams (based on consumer groups)',
    ['source_stream', 'target_stream', 'consumer_group']
)

# Sacred Order activity
sacred_order_activity_gauge = Gauge(
    'sacred_order_activity',
    'Activity level per Sacred Order',
    ['sacred_order']
)

# Exporter health
exporter_scrapes_total = Counter(
    'redis_streams_exporter_scrapes_total',
    'Total number of scrapes'
)

exporter_scrape_duration = Gauge(
    'redis_streams_exporter_scrape_duration_seconds',
    'Duration of last scrape'
)

# =============================================================================
# REDIS STREAMS COLLECTOR
# =============================================================================

class RedisStreamsCollector:
    """Collects metrics from Redis Streams."""
    
    def __init__(self, host: str, port: int, db: int = 0):
        self.redis_client = redis.StrictRedis(
            host=host, port=port, db=db, decode_responses=True
        )
        self._last_stream_lengths: Dict[str, int] = {}
        self._last_consumer_positions: Dict[tuple, int] = {}
        self._last_scrape_time: float = 0
        
        # Sacred Orders mapping for activity tracking
        self.sacred_orders = {
            'memory': ['memory.coherence', 'memory.write', 'memory.sync'],
            'vault': ['vault.archive', 'vault.snapshot', 'vault.backup'],
            'orthodoxy': ['orthodoxy.audit', 'orthodoxy.validation', 'orthodoxy.surveillance'],
            'babel': ['babel.sentiment', 'babel.translation', 'babel.knowledge'],
            'codex': ['codex.discovery', 'codex.enrichment', 'codex.technical'],
            'pattern': ['pattern_weavers.pattern', 'pattern_weavers.analysis'],
            'neural': ['neural_engine.screening', 'neural_engine.ranking']
        }
        
    def collect_metrics(self):
        """Collect all metrics from Redis Streams."""
        start_time = time.time()
        
        try:
            # Get all stream keys
            stream_keys = self._get_all_streams()
            logger.debug(f"Found {len(stream_keys)} streams")
            
            for stream in stream_keys:
                try:
                    # Stream length
                    length = self.redis_client.xlen(stream)
                    stream_length_gauge.labels(stream=stream).set(length)
                    
                    # Track published events (delta from last scrape)
                    if stream in self._last_stream_lengths:
                        delta = length - self._last_stream_lengths[stream]
                        if delta > 0:
                            cognitive_bus_events_published_counter.labels(
                                channel=stream, 
                                event_type="publish"
                            ).inc(delta)
                    self._last_stream_lengths[stream] = length
                    
                    # Consumer groups metrics
                    self._collect_consumer_group_metrics(stream)
                    
                except Exception as e:
                    logger.error(f"Error collecting metrics for stream {stream}: {e}")
            
            # Calculate and export derived metrics
            self._calculate_event_rates(stream_keys)
            self._calculate_sacred_order_activity(stream_keys)
            self._calculate_stream_connections()
            
            # Record scrape metrics
            duration = time.time() - start_time
            exporter_scrape_duration.set(duration)
            exporter_scrapes_total.inc()
            self._last_scrape_time = time.time()
            
            logger.info(f"Collected metrics for {len(stream_keys)} streams in {duration:.3f}s")
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
    
    def _get_all_streams(self) -> List[str]:
        """Get all Redis Stream keys."""
        streams = []
        for key in self.redis_client.scan_iter(match="*", count=1000):
            if self.redis_client.type(key) == 'stream':
                streams.append(key)
        return streams
    
    def _collect_consumer_group_metrics(self, stream: str):
        """Collect consumer group metrics for a stream."""
        try:
            # Get consumer groups info
            groups_info = self.redis_client.xinfo_groups(stream)
            
            for group in groups_info:
                group_name = group['name']
                pending = group['pending']
                last_delivered_id = group['last-delivered-id']
                
                # Pending messages
                stream_pending_messages_gauge.labels(
                    stream=stream, 
                    consumer_group=group_name
                ).set(pending)
                
                # Consumer lag (approximate)
                try:
                    stream_info = self.redis_client.xinfo_stream(stream)
                    last_entry_id = stream_info['last-generated-id']
                    
                    # Compare IDs (simplified: use timestamp part)
                    lag = self._calculate_lag(last_entry_id, last_delivered_id)
                    stream_consumer_lag_gauge.labels(
                        stream=stream,
                        consumer_group=group_name
                    ).set(lag)
                    
                except Exception as e:
                    logger.debug(f"Cannot calculate lag for {stream}:{group_name}: {e}")
                
                # Track consumed events (approximation from last-delivered-id)
                # Note: This is not perfectly accurate but gives directional data
                try:
                    delivered_ms = int(last_delivered_id.split('-')[0])
                    key = (stream, group_name)
                    
                    if key in self._last_consumer_positions:
                        if delivered_ms > self._last_consumer_positions[key]:
                            # Consumer advanced, increment counter
                            # (we can't know exact count, so increment by 1)
                            listener_consumed_counter.labels(
                                consumer_group=group_name,
                                stream=stream
                            ).inc()
                    
                    self._last_consumer_positions[key] = delivered_ms
                    
                except Exception:
                    pass
                    
        except redis.exceptions.ResponseError:
            # No consumer groups for this stream
            pass
        except Exception as e:
            logger.debug(f"Error collecting consumer group metrics for {stream}: {e}")
    
    def _calculate_lag(self, last_id: str, delivered_id: str) -> int:
        """Calculate lag between two stream IDs (simplified)."""
        try:
            # Redis Stream ID format: timestamp-sequence
            last_ms = int(last_id.split('-')[0])
            delivered_ms = int(delivered_id.split('-')[0])
            
            # Lag in milliseconds (simplified)
            lag_ms = last_ms - delivered_ms
            return max(0, lag_ms)
        except Exception:
            return 0
    
    def _calculate_event_rates(self, streams: List[str]):
        """Calculate event publishing rates for each stream."""
        for stream in streams:
            if stream in self._last_stream_lengths:
                current_length = self.redis_client.xlen(stream)
                previous_length = self._last_stream_lengths[stream]
                
                # Calculate rate (events per second)
                time_delta = time.time() - self._last_scrape_time if self._last_scrape_time > 0 else 1
                rate = max(0, (current_length - previous_length) / time_delta)
                
                # Map stream to job/service
                job = self._map_stream_to_job(stream)
                cognitive_bus_event_rate_gauge.labels(stream=stream, job=job).set(rate)
    
    def _calculate_sacred_order_activity(self, streams: List[str]):
        """Calculate activity level for each Sacred Order."""
        activity = {order: 0 for order in self.sacred_orders.keys()}
        
        for stream in streams:
            for order, patterns in self.sacred_orders.items():
                if any(pattern in stream for pattern in patterns):
                    length = self.redis_client.xlen(stream)
                    activity[order] += length
        
        for order, count in activity.items():
            sacred_order_activity_gauge.labels(sacred_order=order).set(count)
    
    def _calculate_stream_connections(self):
        """Calculate connections between streams via consumer groups for node graph."""
        # Get all consumer groups and their streams
        connections: Dict[tuple, int] = {}
        
        for key in self.redis_client.scan_iter(match="*", count=100):
            if self.redis_client.type(key) == 'stream':
                try:
                    groups = self.redis_client.xinfo_groups(key)
                    for group in groups:
                        group_name = group['name']
                        
                        # Create synthetic connections based on consumer group patterns
                        # e.g., if "vault_keeper" consumes from "memory.write.completed",
                        # create connection memory -> vault
                        source_order = self._extract_order_from_stream(key)
                        target_order = self._extract_order_from_consumer(group_name)
                        
                        if source_order and target_order and source_order != target_order:
                            conn_key = (source_order, target_order, group_name)
                            connections[conn_key] = connections.get(conn_key, 0) + 1
                
                except Exception:
                    pass
        
        # Export connections
        for (source, target, group), weight in connections.items():
            stream_connection_gauge.labels(
                source_stream=source, 
                target_stream=target,
                consumer_group=group
            ).set(weight)
    
    def _map_stream_to_job(self, stream: str) -> str:
        """Map stream name to Sacred Order job name."""
        for order, patterns in self.sacred_orders.items():
            if any(pattern in stream for pattern in patterns):
                return f"{order}_orders"
        return "unknown"
    
    def _extract_order_from_stream(self, stream: str) -> str:
        """Extract Sacred Order from stream name."""
        for order in self.sacred_orders.keys():
            if order in stream.lower():
                return order
        return ""
    
    def _extract_order_from_consumer(self, consumer: str) -> str:
        """Extract Sacred Order from consumer group name."""
        consumer_lower = consumer.lower()
        for order in self.sacred_orders.keys():
            if order in consumer_lower:
                return order
        return ""

# =============================================================================
# FLASK APP
# =============================================================================

app = Flask(__name__)
collector = RedisStreamsCollector(REDIS_HOST, REDIS_PORT, REDIS_DB)

@app.route("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    # Collect fresh metrics
    collector.collect_metrics()
    
    # Return Prometheus format
    return Response(generate_latest(REGISTRY), mimetype="text/plain")

@app.route("/health")
def health():
    """Health check endpoint."""
    try:
        collector.redis_client.ping()
        return {"status": "healthy", "redis": "connected"}, 200
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 503

# =============================================================================
# MAIN
# =============================================================================

def main():
    logger.info("=" * 60)
    logger.info("Redis Streams Prometheus Exporter")
    logger.info("=" * 60)
    logger.info(f"Redis: {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
    logger.info(f"Exporter port: {EXPORTER_PORT}")
    logger.info(f"Scrape interval: {SCRAPE_INTERVAL}s")
    logger.info("=" * 60)
    
    # Test Redis connection
    try:
        collector.redis_client.ping()
        logger.info("✅ Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        logger.error("Exiting...")
        return
    
    # Initial metrics collection
    collector.collect_metrics()
    
    # Start Flask server
    logger.info(f"🚀 Starting metrics server on port {EXPORTER_PORT}")
    app.run(host="0.0.0.0", port=EXPORTER_PORT, debug=False)

if __name__ == "__main__":
    main()
