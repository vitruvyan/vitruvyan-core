"""
Pattern Weavers Redis Listener — Cognitive Bus Integration

Epistemic Order: REASON (Semantic Layer)
Sacred Order: Pattern Weavers

Listens for weaving events on Redis Cognitive Bus and processes them.

Channels:
- pattern_weavers:weave_request → Trigger semantic weaving
- pattern_weavers:weave_response → Publish weaving results

Author: Sacred Orders
Created: November 9, 2025
"""

import json
import redis
import time
from typing import Dict, Any
import os

from vitruvyan_core.core.cognitive.pattern_weavers.weaver_engine import PatternWeaverEngine
from vitruvyan_core.core.foundation.persistence.postgres_agent import PostgresAgent


class PatternWeaversListener:
    """
    Redis listener for Pattern Weavers Cognitive Bus integration.
    
    Subscribes to:
    - pattern_weavers:weave_request
    
    Publishes to:
    - pattern_weavers:weave_response
    - cognitive_bus:events (Sacred Orders events)
    """
    
    def __init__(
        self,
        redis_host: str = None,
        redis_port: int = None,
        redis_db: int = 0
    ):
        """
        Initialize Pattern Weavers Redis listener.
        
        Args:
            redis_host: Redis host (default from env)
            redis_port: Redis port (default from env)
            redis_db: Redis database number
        """
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "vitruvyan_redis")
        self.redis_port = redis_port or int(os.getenv("REDIS_PORT", 6379))
        self.redis_db = redis_db
        
        # Initialize Redis client
        self.redis_client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            decode_responses=True
        )
        
        # Initialize Pattern Weaver engine
        self.weaver = PatternWeaverEngine()
        
        # Initialize PostgreSQL agent for logging
        self.postgres = PostgresAgent()
        
        # Channels
        self.request_channel = "pattern_weavers:weave_request"
        self.response_channel = "pattern_weavers:weave_response"
        self.events_channel = "cognitive_bus:events"
        
        print(f"🕸️ Pattern Weavers Listener initialized")
        print(f"   Redis: {self.redis_host}:{self.redis_port}")
        print(f"   Request channel: {self.request_channel}")
        print(f"   Response channel: {self.response_channel}")
    
    def _publish_event(self, event_type: str, payload: Dict[str, Any]):
        """
        Publish event to cognitive_bus:events channel.
        
        Args:
            event_type: Type of event (e.g., "weaving_completed")
            payload: Event payload data
        """
        event = {
            "sacred_order": "pattern_weavers",
            "event_type": event_type,
            "timestamp": time.time(),
            "payload": payload
        }
        
        try:
            self.redis_client.publish(
                self.events_channel,
                json.dumps(event)
            )
        except Exception as e:
            print(f"⚠️ Failed to publish event: {e}")
    
    def _handle_weave_request(self, message: Dict[str, Any]):
        """
        Handle weave request from Redis.
        
        Args:
            message: Request message with query_text, user_id, etc.
        """
        request_id = message.get("request_id", "unknown")
        query_text = message.get("query_text", "")
        user_id = message.get("user_id", "unknown")
        top_k = message.get("top_k", 5)
        similarity_threshold = message.get("similarity_threshold", 0.6)
        
        print(f"🕸️ Weave request {request_id}: '{query_text[:50]}...'")
        
        start_time = time.time()
        
        try:
            # Execute weaving
            result = self.weaver.weave(
                query_text=query_text,
                user_id=user_id,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )
            
            # Add request_id to result
            result["request_id"] = request_id
            result["status"] = "success"
            
            # Publish response
            self.redis_client.publish(
                self.response_channel,
                json.dumps(result)
            )
            
            # Publish event to cognitive bus
            self._publish_event("weaving_completed", {
                "request_id": request_id,
                "user_id": user_id,
                "concepts_found": len(result.get("concepts", [])),
                "patterns_found": len(result.get("patterns", [])),
                "latency_ms": result.get("latency_ms", 0)
            })
            
            latency = (time.time() - start_time) * 1000
            print(f"✅ Weave request {request_id} completed in {latency:.2f}ms")
            print(f"   Concepts: {result.get('concepts', [])}")
        
        except Exception as e:
            print(f"❌ Weave request {request_id} failed: {e}")
            
            # Publish error response
            error_result = {
                "request_id": request_id,
                "status": "error",
                "error": str(e),
                "concepts": [],
                "patterns": [],
                "risk_profile": {}
            }
            
            self.redis_client.publish(
                self.response_channel,
                json.dumps(error_result)
            )
            
            # Publish error event
            self._publish_event("weaving_failed", {
                "request_id": request_id,
                "user_id": user_id,
                "error": str(e)
            })
    
    def listen(self):
        """
        Start listening to Redis channels.
        
        Blocking operation that runs until interrupted.
        """
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(self.request_channel)
        
        print(f"🕸️ Pattern Weavers Listener started")
        print(f"   Listening on: {self.request_channel}")
        print(f"   Publishing to: {self.response_channel}")
        print(f"   Broadcasting to: {self.events_channel}")
        print("   Waiting for weave requests...")
        
        # Publish startup event
        self._publish_event("listener_started", {
            "redis_host": self.redis_host,
            "redis_port": self.redis_port,
            "channels": [self.request_channel]
        })
        
        try:
            for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        self._handle_weave_request(data)
                    
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Invalid JSON in message: {e}")
                    
                    except Exception as e:
                        print(f"❌ Error handling message: {e}")
        
        except KeyboardInterrupt:
            print("\n🛑 Pattern Weavers Listener shutting down...")
            
            # Publish shutdown event
            self._publish_event("listener_stopped", {
                "reason": "manual_shutdown"
            })
            
            pubsub.unsubscribe()
            pubsub.close()
        
        except Exception as e:
            print(f"❌ Fatal error in listener: {e}")
            
            # Publish error event
            self._publish_event("listener_error", {
                "error": str(e)
            })
            
            raise


def main():
    """Main entry point for Pattern Weavers listener."""
    print("=" * 60)
    print("🕸️ PATTERN WEAVERS — COGNITIVE BUS LISTENER")
    print("=" * 60)
    print()
    
    listener = PatternWeaversListener()
    listener.listen()


if __name__ == "__main__":
    main()
