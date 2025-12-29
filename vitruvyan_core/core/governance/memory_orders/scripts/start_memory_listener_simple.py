#!/usr/bin/env python3
"""
🧠 Memory Orders - Simple Redis Listener
EPOCH II - PHASE 4.9

Direct Redis listener for testing Memory Orders events
"""

import asyncio
import logging
import os
import sys
import redis.asyncio as redis
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Start simple Memory Orders listener"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    logger.info(f"🧠 Starting Memory Orders Listener... ({redis_url})")
    
    try:
        # Connect to Redis
        client = redis.from_url(redis_url)
        pubsub = client.pubsub()
        
        # Subscribe to Memory Orders channels
        await pubsub.subscribe("memory.write.requested", "memory.read.requested", "memory.vector.match.requested")
        logger.info("✅ Subscribed to Memory Orders channels")
        logger.info("   - memory.write.requested")
        logger.info("   - memory.read.requested")
        logger.info("   - memory.vector.match.requested")
        logger.info("\n👂 Listening... (Ctrl+C to stop)\n")
        
        # Listen for events
        async for message in pubsub.listen():
            if message["type"] == "message":
                channel = message["channel"].decode("utf-8")
                try:
                    data = json.loads(message["data"].decode("utf-8"))
                    logger.info(f"📨 Event: {channel}")
                    logger.info(f"   Payload: {json.dumps(data, indent=2)[:200]}...")
                except Exception as e:
                    logger.error(f"   Error: {e}")
                    
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping listener...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
