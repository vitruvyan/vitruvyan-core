#!/usr/bin/env python3
"""
🔐 Vault Keepers - Sacred Cognitive Bus Listener
Divine event subscription for knowledge preservation and versioning
Listens to archival events in the sacred cognitive realm
"""

import asyncio
import json
import logging
import requests
from typing import Dict, Any
import redis.asyncio as redis
from datetime import datetime
import os

logger = logging.getLogger("VaultKeepersListener")

class VaultKeepersCognitiveBusListener:
    """🔐 Sacred listener for archival events in Vault Keepers"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://omni_redis:6379')
        self.redis_client = None
        self.pubsub = None
        self.running = False
        
        # Sacred vault channels - Divine archival subscriptions
        self.sacred_channels = [
            "vault.archive.requested",      # Archive creation requests
            "vault.restore.requested",      # Version restoration requests
            "vault.snapshot.requested",     # System snapshot requests
            "orthodoxy.audit.completed",    # Store audit results
            "neural_engine.screening.completed"  # Archive screening results
        ]
        
    async def initialize_sacred_connection(self):
        """🔐 Initialize divine Redis connection to sacred cognitive realm"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.pubsub = self.redis_client.pubsub()
            
            # Subscribe to all sacred channels
            for channel in self.sacred_channels:
                await self.pubsub.subscribe(channel)
                logger.info(f"🔐 Subscribed to sacred channel: {channel}")
            
            logger.info("🔐 Vault Keepers connected to divine cognitive bus")
            return True
            
        except Exception as e:
            logger.error(f"🔐 Sacred connection failed: {e}")
            return False
    
    async def begin_sacred_listening(self):
        """🔐 Begin sacred listening for divine archival events"""
        if not await self.initialize_sacred_connection():
            return
            
        self.running = True
        logger.info("🔐 Vault Keepers listener activated - Preserving sacred knowledge...")
        
        # Heartbeat task for health monitoring
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        try:
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    await self.handle_sacred_message(message)
        except Exception as e:
            logger.error(f"🔐 Sacred listener error: {e}")
        finally:
            heartbeat_task.cancel()
            await self.sacred_cleanup()
    
    async def _heartbeat_loop(self):
        """💓 Heartbeat logger - confirms listener is alive every 60s"""
        while self.running:
            try:
                await asyncio.sleep(60)
                logger.info("💓 Vault Keepers listener heartbeat - Redis connection active, listening on channels: " + 
                           ", ".join(self.sacred_channels))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"💓 Heartbeat error: {e}")
    
    async def handle_sacred_message(self, message):
        """🔐 Handle sacred messages from divine cognitive channels"""
        channel = message['channel'].decode('utf-8')
        
        if channel == "vault.archive.requested":
            await self.handle_archive_request(message['data'])
        elif channel == "vault.restore.requested":
            await self.handle_restore_request(message['data'])
        elif channel == "vault.snapshot.requested":
            await self.handle_snapshot_request(message['data'])
        elif channel == "orthodoxy.audit.completed":
            await self.handle_audit_archival(message['data'])
        elif channel == "neural_engine.screening.completed":
            await self.handle_screening_archival(message['data'])
        else:
            logger.warning(f"🔐 Unknown sacred channel: {channel}")
    
    async def handle_archive_request(self, data: bytes):
        """🔐 Handle archive creation requests"""
        try:
            payload = json.loads(data.decode('utf-8'))
            entity_type = payload.get('entity_type')
            entity_id = payload.get('entity_id')
            
            logger.info(f"🔐 Archive request received: {entity_type}/{entity_id}")
            
            # Call Vault Keepers API to create archive
            response = requests.post(
                "http://localhost:8007/vault/archive",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"🔐 Archive created successfully: {entity_type}/{entity_id}")
                await self.publish_archive_completed(payload, response.json())
            else:
                logger.error(f"🔐 Archive creation failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"🔐 Archive request error: {e}")
    
    async def handle_restore_request(self, data: bytes):
        """🔐 Handle version restoration requests"""
        try:
            payload = json.loads(data.decode('utf-8'))
            logger.info(f"🔐 Restore request received: version {payload.get('version_id')}")
            # Implementation here
        except Exception as e:
            logger.error(f"🔐 Restore request error: {e}")
    
    async def handle_snapshot_request(self, data: bytes):
        """🔐 Handle system snapshot requests"""
        try:
            payload = json.loads(data.decode('utf-8'))
            logger.info(f"🔐 Snapshot request received")
            # Implementation here
        except Exception as e:
            logger.error(f"🔐 Snapshot request error: {e}")
    
    async def handle_audit_archival(self, data: bytes):
        """🔐 Handle audit results archival"""
        try:
            payload = json.loads(data.decode('utf-8'))
            logger.info(f"🔐 Archiving audit results: {payload.get('audit_id')}")
            # Implementation here
        except Exception as e:
            logger.error(f"🔐 Audit archival error: {e}")
    
    async def handle_screening_archival(self, data: bytes):
        """🔐 Handle screening results archival"""
        try:
            payload = json.loads(data.decode('utf-8'))
            logger.info(f"🔐 Archiving screening results: run_id {payload.get('run_id')}")
            # Implementation here
        except Exception as e:
            logger.error(f"🔐 Screening archival error: {e}")
    
    async def publish_archive_completed(self, request: Dict, result: Dict):
        """🔐 Publish archive completion event"""
        try:
            event = {
                "event_type": "vault.archive.completed",
                "entity_type": request.get('entity_type'),
                "entity_id": request.get('entity_id'),
                "archive_id": result.get('archive_id'),
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis_client.publish(
                "vault.archive.completed",
                json.dumps(event)
            )
            
            logger.info(f"🔐 Published vault.archive.completed")
            
        except Exception as e:
            logger.error(f"🔐 Event publishing error: {e}")
    
    async def sacred_cleanup(self):
        """🔐 Sacred cleanup of divine Redis connections"""
        try:
            if self.pubsub:
                for channel in self.sacred_channels:
                    await self.pubsub.unsubscribe(channel)
                await self.pubsub.close()
            if self.redis_client:
                await self.redis_client.close()
            logger.info("🔐 Sacred connections to divine realm cleaned up")
        except Exception as e:
            logger.error(f"🔐 Sacred cleanup error: {e}")


def main():
    """Start Vault Keepers listener"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    listener = VaultKeepersCognitiveBusListener()
    
    try:
        asyncio.run(listener.begin_sacred_listening())
    except KeyboardInterrupt:
        logger.info("🔐 Vault Keepers listener stopped by user")


if __name__ == "__main__":
    main()
