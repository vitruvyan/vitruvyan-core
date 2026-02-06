#!/usr/bin/env python3
"""
🧩 MCP LISTENER - Model Context Protocol Bridge
===============================================
Sacred Order: TRUTH (Epistemic Governance Layer)

The MCP Listener bridges Model Context Protocol requests to Vitruvyan's
Sacred Orders architecture. It listens for MCP actions on the Redis Cognitive Bus
and forwards them to the appropriate epistemic components.

"Epistemic continuity through protocol neutrality" - MCP Listener's Creed

Architecture:
- Redis Cognitive Bus integration for MCP action requests
- Sacred Orders compliance (no AI logic, pure infrastructure)
- Event logging and forwarding to stub handlers
- Heartbeat monitoring for system observability

Channels:
- conclave.mcp.actions → MCP action requests
- cognitive_bus:events → Sacred Orders event broadcasting

Author: Sacred Orders - TRUTH
Created: 2026-01-01
"""

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

import redis

# Configure logging following Sacred Orders pattern
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [MCP_LISTENER] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class MCPListener:
    """
    MCP Listener - Model Context Protocol Bridge

    Sacred Order: TRUTH
    Epistemic Layer: Epistemic Governance

    Listens for MCP action requests on Redis Cognitive Bus and forwards
    them to Sacred Orders components. Maintains epistemic neutrality by
    avoiding any AI/decision logic - pure infrastructure bridge.

    Channels:
    - Subscribes: conclave.mcp.actions
    - Publishes: cognitive_bus:events
    """

    def __init__(self,
                 redis_host: str = None,
                 redis_port: int = None,
                 redis_db: int = 0):
        """
        Initialize MCP Listener following Sacred Orders pattern.

        Args:
            redis_host: Redis host (default from env REDIS_HOST)
            redis_port: Redis port (default from env REDIS_PORT)
            redis_db: Redis database number
        """
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "vitruvyan_redis")
        self.redis_port = redis_port or int(os.getenv("REDIS_PORT", 6379))
        self.redis_db = redis_db

        # Redis client initialization (Sacred Orders pattern)
        self.redis_client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            decode_responses=True
        )

        # Channel configuration
        self.request_channel = "conclave.mcp.actions"
        self.events_channel = "cognitive_bus:events"

        # Listener state
        self.listening = False
        self.start_time = None
        self.event_count = 0

        logger.info("🧩 MCP Listener initialized")
        logger.info(f"   Redis: {self.redis_host}:{self.redis_port}")
        logger.info(f"   Request channel: {self.request_channel}")
        logger.info(f"   Events channel: {self.events_channel}")

    def _publish_event(self, event_type: str, payload: Dict[str, Any]):
        """
        Publish event to cognitive_bus:events channel.

        Following Sacred Orders event publishing pattern.

        Args:
            event_type: Type of event (e.g., "mcp_action_received")
            payload: Event payload data
        """
        event = {
            "sacred_order": "truth",
            "epistemic_layer": "governance",
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload
        }

        try:
            self.redis_client.publish(
                self.events_channel,
                json.dumps(event)
            )
            logger.debug(f"📡 Published {event_type} event to {self.events_channel}")
        except Exception as e:
            logger.error(f"❌ Failed to publish event {event_type}: {e}")

    def _handle_mcp_action(self, message: Dict[str, Any]):
        """
        Handle MCP action request from Redis.

        Logs every received event with timestamp, channel, and raw payload
        as required. Forwards to stub handler (no business logic).

        Args:
            message: MCP action message
        """
        # Log every received event (MANDATORY requirement)
        timestamp = datetime.utcnow().isoformat()
        logger.info(f"📨 [{timestamp}] Received MCP action on channel '{self.request_channel}'")
        logger.info(f"   Raw payload: {json.dumps(message, indent=2)}")

        # Extract message components
        action = message.get("action", "unknown")
        parameters = message.get("parameters", {})
        request_id = message.get("request_id", "unknown")
        user_id = message.get("user_id", "unknown")

        logger.info(f"   Action: {action}")
        logger.info(f"   Request ID: {request_id}")
        logger.info(f"   User ID: {user_id}")

        # Publish reception event to Sacred Orders
        self._publish_event("mcp_action_received", {
            "action": action,
            "request_id": request_id,
            "user_id": user_id,
            "parameters": parameters,
            "received_at": timestamp
        })

        # Forward to stub handler (no business logic - pure infrastructure)
        try:
            result = self._process_mcp_action_stub(action, parameters, request_id, user_id)

            # Publish processing result
            self._publish_event("mcp_action_processed", {
                "action": action,
                "request_id": request_id,
                "user_id": user_id,
                "result": result,
                "processed_at": datetime.utcnow().isoformat()
            })

            logger.info(f"✅ MCP action '{action}' processed successfully")

        except Exception as e:
            logger.error(f"❌ Error processing MCP action '{action}': {e}")

            # Publish error event
            self._publish_event("mcp_action_error", {
                "action": action,
                "request_id": request_id,
                "user_id": user_id,
                "error": str(e),
                "error_at": datetime.utcnow().isoformat()
            })

        # Update event count
        self.event_count += 1

    def _process_mcp_action_stub(self, action: str, parameters: Dict[str, Any],
                                request_id: str, user_id: str) -> Dict[str, Any]:
        """
        Stub handler for MCP actions.

        NO BUSINESS LOGIC - Pure infrastructure forwarding.
        In production, this would forward to appropriate Sacred Orders components.

        Args:
            action: MCP action name
            parameters: Action parameters
            request_id: Request identifier
            user_id: User identifier

        Returns:
            Stub processing result
        """
        # Log forwarding (epistemic observability)
        logger.info(f"🔄 Forwarding MCP action '{action}' to Sacred Orders (stub)")

        # Stub result - in production this would call actual components
        result = {
            "status": "stub_processed",
            "action": action,
            "request_id": request_id,
            "user_id": user_id,
            "parameters": parameters,
            "processed_at": datetime.utcnow().isoformat(),
            "note": "This is a stub handler - no actual processing performed"
        }

        # Simulate processing time (remove in production)
        time.sleep(0.1)

        return result

    def _emit_heartbeat(self):
        """
        Emit heartbeat log every 30 seconds.

        Shows listener is alive, Redis connection healthy, subscribed channel.
        """
        if not self.listening:
            return

        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
        uptime_str = f"{uptime_seconds:.0f}s"

        # Check Redis connection health
        try:
            self.redis_client.ping()
            redis_status = "healthy"
        except Exception as e:
            redis_status = f"unhealthy: {e}"

        logger.info("💓 MCP Listener heartbeat")
        logger.info(f"   Status: alive")
        logger.info(f"   Uptime: {uptime_str}")
        logger.info(f"   Redis: {redis_status}")
        logger.info(f"   Channel: {self.request_channel}")
        logger.info(f"   Events processed: {self.event_count}")

    def start_listening(self):
        """
        Start listening for MCP actions on Redis Cognitive Bus.

        Following Sacred Orders lifecycle pattern:
        - Connect to Redis
        - Subscribe to channel
        - Start listening loop
        - Handle graceful shutdown
        """
        logger.info("🚀 Starting MCP Listener - Model Context Protocol Bridge...")
        logger.info("=" * 60)

        try:
            # Test Redis connection
            self.redis_client.ping()
            logger.info("✅ Redis Cognitive Bus connection established")

            # Setup pubsub
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe(self.request_channel)

            # Mark as listening
            self.listening = True
            self.start_time = datetime.utcnow()

            logger.info("🧩 MCP Listener active")
            logger.info(f"   Listening on: {self.request_channel}")
            logger.info(f"   Broadcasting to: {self.events_channel}")
            logger.info("   Waiting for MCP actions...")
            logger.info("=" * 60)

            # Publish startup event
            self._publish_event("listener_started", {
                "redis_host": self.redis_host,
                "redis_port": self.redis_port,
                "channel": self.request_channel,
                "started_at": self.start_time.isoformat()
            })

            # Setup signal handlers for graceful shutdown (disabled for now)
            # signal.signal(signal.SIGINT, self._signal_handler)
            # signal.signal(signal.SIGTERM, self._signal_handler)

            # Heartbeat timer
            last_heartbeat = time.time()

            # Main listening loop
            for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        self._handle_mcp_action(data)

                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ Invalid JSON in MCP message: {e}")
                        logger.warning(f"   Raw message: {message.get('data', 'N/A')}")

                    except Exception as e:
                        logger.error(f"❌ Error handling MCP message: {e}")

                # Emit heartbeat every 30 seconds
                current_time = time.time()
                if current_time - last_heartbeat >= 30:
                    self._emit_heartbeat()
                    last_heartbeat = current_time

        except KeyboardInterrupt:
            logger.info("\n🛑 MCP Listener shutting down (manual interrupt)...")

        except Exception as e:
            logger.error(f"❌ Fatal error in MCP listener: {e}")
            self._publish_event("listener_error", {
                "error": str(e),
                "error_at": datetime.utcnow().isoformat()
            })
            raise

        finally:
            self._shutdown()

    def stop_listening(self):
        """
        Stop listening for MCP actions.

        Following Sacred Orders shutdown pattern.
        """
        logger.info("🛑 Stopping MCP Listener...")
        self.listening = False

    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals gracefully.

        Following Sacred Orders signal handling pattern.
        """
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        logger.info(f"\n📡 Received {signal_name} - initiating graceful shutdown...")
        self.stop_listening()

    def _shutdown(self):
        """
        Perform graceful shutdown cleanup.

        Following Sacred Orders cleanup pattern.
        """
        try:
            # Publish shutdown event
            self._publish_event("listener_stopped", {
                "reason": "graceful_shutdown",
                "events_processed": self.event_count,
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0,
                "stopped_at": datetime.utcnow().isoformat()
            })

            logger.info("✅ MCP Listener shutdown complete")
            logger.info(f"   Total events processed: {self.event_count}")

        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")


def main():
    """Main entry point for MCP Listener."""
    print("=" * 60)
    print("🧩 MCP LISTENER — MODEL CONTEXT PROTOCOL BRIDGE")
    print("Sacred Order: TRUTH")
    print("=" * 60)
    print()

    # Create and start listener
    listener = MCPListener()
    listener.start_listening()


if __name__ == "__main__":
    main()