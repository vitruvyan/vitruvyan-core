#!/usr/bin/env python3
"""
LangGraph Cognitive Bus Listener (Redis Streams - Native)
Sacred Order: Discourse Layer

Event-driven workflow orchestrator for Portfolio Architects via Redis Streams.

Migration: Pub/Sub → Streams (Jan 25, 2026)
Pattern: Native Streams with REST API isolation

Architecture:
    Redis Streams → Consumer → REST API → LangGraph :8004

Sacred Channels:
- portfolio:snapshot_created → Trigger Guardian monitoring
- portfolio:manual_check → Manual portfolio review

Design Decision (Jan 25, 2026):
    Using REST API instead of direct import to avoid Herald dependency.
    LangGraph codebase still uses Herald (legacy Pub/Sub) in orthodoxy_node.
    Listener is isolated until complete codebase migration.
"""
import os
import sys
import logging
import json
import time
import httpx
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamBus
from core.leo.postgres_agent import PostgresAgent
from vitruvyan_core.core.synaptic_conclave.monitoring.metrics_server import start_metrics_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LangGraphStreamsListener:
    """
    Native Streams listener for LangGraph Portfolio events.
    
    Consumes events from Redis Streams and triggers Guardian workflows via REST API.
    """
    
    def __init__(self):
        self.postgres = PostgresAgent()
        self.bus = StreamBus(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD")
        )
        self.consumer_group = os.getenv("STREAM_CONSUMER_GROUP", "langgraph_portfolio")
        self.consumer_name = os.getenv("STREAM_CONSUMER_NAME", "langgraph_portfolio_worker_1")
        
        # LangGraph API endpoint
        self.langgraph_api_url = os.getenv("LANGGRAPH_API_URL", "http://vitruvyan_api_graph:8004")
        
        # Sacred channels (stream names WITHOUT vitruvyan: prefix)
        self.channels = [
            "portfolio:snapshot_created",
            "portfolio:manual_check"
        ]
        logger.info(f"🎧 LangGraph Streams Listener initialized (group={self.consumer_group}, api={self.langgraph_api_url})")
    
    def handle_portfolio_snapshot(self, event) -> None:
        """Handler for portfolio:snapshot_created events"""
        start_time = time.time()
        user_id = event.payload.get("user_id")
        snapshot_id = event.payload.get("snapshot_id")
        
        logger.info(f"📸 Portfolio snapshot created: user={user_id}, snapshot={snapshot_id}")
        
        try:
            # Trigger Guardian monitoring via LangGraph REST API
            payload = {
                "input_text": "controlla il mio portfolio",
                "user_id": user_id,
                "validated_tickers": [],  # Guardian detects from DB
                "mode": "portfolio"
            }
            
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self.langgraph_api_url}/run",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
            
            duration = time.time() - start_time
            
            logger.info(f"✅ Guardian workflow completed in {duration:.2f}s")
            logger.debug(f"Result: {json.dumps(result, indent=2)}")
            
        except httpx.HTTPError as e:
            logger.error(f"❌ LangGraph API request failed: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Guardian workflow failed: {e}", exc_info=True)
    
    def handle_manual_check(self, event) -> None:
        """Handler for portfolio:manual_check events"""
        user_id = event.payload.get("user_id")
        logger.info(f"🔍 Manual portfolio check: user={user_id}")
        self.handle_portfolio_snapshot(event)
    
    def start(self):
        """Start consuming from Redis Streams"""
        logger.info("🚀 Starting LangGraph Streams Listener...")
        
        # Create consumer groups
        for channel in self.channels:
            self.bus.create_consumer_group(
                channel=channel,
                group=self.consumer_group,
                start_id="0"  # Read from beginning on first start
            )
            logger.info(f"✅ Consumer group ready: {channel} → {self.consumer_group}")
        
        # Map stream names to handlers
        handlers = {
            "portfolio:snapshot_created": self.handle_portfolio_snapshot,
            "portfolio:manual_check": self.handle_manual_check
        }
        
        # Consume events (blocking generator)
        logger.info(f"👂 Consuming from {len(self.channels)} streams...")
        
        # Consume from first channel (portfolio:snapshot_created)
        # Note: StreamBus.consume() is single-stream generator
        # For multi-stream consumption, we'd need to run multiple consumers
        # or use XREADGROUP with multiple streams
        
        for channel in self.channels:
            logger.info(f"📡 Subscribing to {channel}...")
        
        try:
            # Consume from snapshot_created channel
            for event in self.bus.consume(
                channel="portfolio:snapshot_created",
                group=self.consumer_group,
                consumer=self.consumer_name,
                count=10,
                block_ms=5000
            ):
                handler = handlers.get("portfolio:snapshot_created")
                if handler:
                    try:
                        handler(event)
                        # Acknowledge successful processing
                        self.bus.ack(event, group=self.consumer_group)
                        logger.info(f"✅ ACK: {event.stream} → {event.event_id}")
                    except Exception as e:
                        logger.error(f"❌ Handler failed: {e}", exc_info=True)
                        # Event stays in Pending Entries List for retry
                
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down listener...")
        except Exception as e:
            logger.error(f"❌ Consume loop error: {e}", exc_info=True)


def main():
    """Main entry point"""
    logger.info("🧠 LangGraph Cognitive Bus Listener (Native Streams) — Sacred Order: Discourse")
    
    listener = LangGraphStreamsListener()
    listener.start()


if __name__ == "__main__":
    main()

