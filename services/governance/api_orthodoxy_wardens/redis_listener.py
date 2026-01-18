#!/usr/bin/env python3
"""
⚖️ Orthodoxy Wardens - Sacred Cognitive Bus Listener
Divine event subscription for epistemic integrity and compliance monitoring
Listens to audit and validation events in the sacred cognitive realm
"""

import asyncio
import json
import logging
import requests
from typing import Dict, Any
import redis.asyncio as redis
from datetime import datetime
import os

logger = logging.getLogger("OrthodoxyWardensListener")

class OrthodoxyWardensCognitiveBusListener:
    """⚖️ Sacred listener for audit and validation events in Orthodoxy Wardens"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://omni_redis:6379')
        self.redis_client = None
        self.pubsub = None
        self.running = False
        
        # Sacred orthodoxy channels - Divine audit subscriptions
        self.sacred_channels = [
            "orthodoxy.audit.requested",           # Audit initiation requests
            "orthodoxy.validation.requested",      # Validation requests
            "neural_engine.screening.completed",   # Validate screening results
            "babel.sentiment.completed",           # Validate sentiment scores
            "memory.write.completed",              # Audit memory writes
            "vee.explanation.completed",           # Validate VEE outputs
            "langgraph.response.completed"         # Audit final responses
        ]
        
    async def initialize_sacred_connection(self):
        """⚖️ Initialize divine Redis connection to sacred cognitive realm"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.pubsub = self.redis_client.pubsub()
            
            # Subscribe to all sacred channels
            for channel in self.sacred_channels:
                await self.pubsub.subscribe(channel)
                logger.info(f"⚖️ Subscribed to sacred channel: {channel}")
            
            logger.info("⚖️ Orthodoxy Wardens connected to divine cognitive bus")
            return True
            
        except Exception as e:
            logger.error(f"⚖️ Sacred connection failed: {e}")
            return False
    
    async def begin_sacred_listening(self):
        """⚖️ Begin sacred listening for divine audit events"""
        if not await self.initialize_sacred_connection():
            return
            
        self.running = True
        logger.info("⚖️ Orthodoxy Wardens listener activated - Guarding epistemic integrity...")
        
        # Heartbeat task for health monitoring
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        try:
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    await self.handle_sacred_message(message)
        except Exception as e:
            logger.error(f"⚖️ Sacred listener error: {e}")
        finally:
            heartbeat_task.cancel()
            await self.sacred_cleanup()
    
    async def _heartbeat_loop(self):
        """💓 Heartbeat logger - confirms listener is alive every 60s"""
        while self.running:
            try:
                await asyncio.sleep(60)
                logger.info("💓 Orthodoxy Wardens listener heartbeat - Redis connection active, listening on channels: " + 
                           ", ".join(self.sacred_channels))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"💓 Heartbeat error: {e}")
    
    async def handle_sacred_message(self, message):
        """⚖️ Handle sacred messages from divine cognitive channels"""
        channel = message['channel'].decode('utf-8')
        
        try:
            data = json.loads(message['data'].decode('utf-8'))
            
            if channel == "orthodoxy.audit.requested":
                await self.handle_audit_request(data)
            elif channel == "orthodoxy.validation.requested":
                await self.handle_validation_request(data)
            elif channel == "neural_engine.screening.completed":
                await self.handle_screening_validation(data)
            elif channel == "babel.sentiment.completed":
                await self.handle_sentiment_validation(data)
            elif channel == "memory.write.completed":
                await self.handle_memory_audit(data)
            elif channel == "vee.explanation.completed":
                await self.handle_vee_validation(data)
            elif channel == "langgraph.response.completed":
                await self.handle_response_audit(data)
                
        except json.JSONDecodeError as e:
            logger.error(f"⚖️ Invalid JSON in message from {channel}: {e}")
        except Exception as e:
            logger.error(f"⚖️ Error handling message from {channel}: {e}")
    
    async def handle_audit_request(self, data: Dict[str, Any]):
        """⚖️ Process audit initiation requests"""
        logger.info(f"⚖️ Audit requested: {data.get('audit_type', 'unknown')}")
        
        try:
            # Call local audit API endpoint
            response = requests.post(
                "http://localhost:8006/audit/run",
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"⚖️ Audit completed successfully: {data.get('correlation_id')}")
                # Publish completion event
                await self.redis_client.publish(
                    "orthodoxy.audit.completed",
                    json.dumps({
                        "correlation_id": data.get("correlation_id"),
                        "audit_result": response.json(),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                )
            else:
                logger.error(f"⚖️ Audit failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"⚖️ Audit execution error: {e}")
    
    async def handle_validation_request(self, data: Dict[str, Any]):
        """⚖️ Process validation requests"""
        logger.info(f"⚖️ Validation requested: {data.get('validation_type', 'unknown')}")
        
        try:
            response = requests.post(
                "http://localhost:8006/validate",
                json=data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"⚖️ Validation result: {result.get('status')}")
                
                # Publish validation result
                await self.redis_client.publish(
                    "orthodoxy.validation.completed",
                    json.dumps({
                        "correlation_id": data.get("correlation_id"),
                        "validation_result": result,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                )
                
        except Exception as e:
            logger.error(f"⚖️ Validation error: {e}")
    
    async def handle_screening_validation(self, data: Dict[str, Any]):
        """⚖️ Validate Neural Engine screening results"""
        logger.info(f"⚖️ Screening validation: {data.get('entity_id', 'unknown')}")
        # Implement validation logic here
    
    async def handle_sentiment_validation(self, data: Dict[str, Any]):
        """⚖️ Validate Babel Gardens sentiment scores"""
        logger.info(f"⚖️ Sentiment validation: {data.get('entity_id', 'unknown')}")
        # Implement validation logic here
    
    async def handle_memory_audit(self, data: Dict[str, Any]):
        """⚖️ Audit memory write operations"""
        logger.info(f"⚖️ Memory write audit: {data.get('operation', 'unknown')}")
        # Implement audit logic here
    
    async def handle_vee_validation(self, data: Dict[str, Any]):
        """⚖️ Validate VEE explanation outputs"""
        logger.info(f"⚖️ VEE validation: {data.get('entity_id', 'unknown')}")
        # Implement validation logic here
    
    async def handle_response_audit(self, data: Dict[str, Any]):
        """⚖️ Audit final LangGraph responses"""
        logger.info(f"⚖️ Response audit: {data.get('user_id', 'unknown')}")
        # Implement audit logic here
    
    async def sacred_cleanup(self):
        """⚖️ Sacred cleanup on listener shutdown"""
        self.running = False
        
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
            
        if self.redis_client:
            await self.redis_client.close()
            
        logger.info("⚖️ Orthodoxy Wardens listener shutdown complete")

async def start_orthodoxy_listener():
    """⚖️ Start the Orthodoxy Wardens sacred cognitive bus listener"""
    listener = OrthodoxyWardensCognitiveBusListener()
    await listener.begin_sacred_listening()

if __name__ == "__main__":
    asyncio.run(start_orthodoxy_listener())
