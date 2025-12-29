"""
Simplified Graph Audit Monitor
Basic monitoring without external dependencies
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class SimpleGraphAuditMonitor:
    """
    Simplified audit monitoring for LangGraph execution
    Provides basic monitoring without external dependencies
    """
    
    def __init__(self):
        self.monitoring_active = False
        self.session_id = None
        self.performance_metrics = {}
        self.execution_count = 0
        
    async def start_monitoring_session(self, context: str = "graph_api"):
        """Start a new monitoring session"""
        try:
            self.session_id = f"monitor_{int(datetime.now().timestamp())}"
            self.monitoring_active = True
            self.performance_metrics = {
                "session_start": datetime.now().isoformat(),
                "context": context,
                "executions": 0
            }
            
            logger.info(f"🔍 Started simple audit monitoring session {self.session_id}")
            
            # Re-enable background monitoring (simple monitor is safe)
            asyncio.create_task(self._background_monitor())
            logger.info("🔍 Simple background monitoring re-enabled (no external dependencies)")
            
        except Exception as e:
            logger.error(f"Failed to start simple audit monitoring: {e}")
    
    async def stop_monitoring_session(self):
        """Stop the current monitoring session"""
        if self.session_id:
            self.monitoring_active = False
            
            logger.info(f"✅ Stopped simple audit monitoring session {self.session_id}")
            logger.info(f"📊 Final metrics: {self.performance_metrics}")
            self.session_id = None
    
    @asynccontextmanager
    async def monitor_graph_execution(self, context: Dict[str, Any]):
        """Context manager for monitoring a single graph execution"""
        start_time = time.time()
        execution_id = f"exec_{int(start_time)}"
        
        try:
            logger.info(f"🔍 Monitoring graph execution {execution_id}")
            
            # Increment execution counter
            self.execution_count += 1
            self.performance_metrics["executions"] = self.execution_count
            
            yield execution_id
            
        except Exception as e:
            # Log execution error
            logger.error(f"Graph execution {execution_id} failed: {e}")
            
            # Record error metrics
            if "errors" not in self.performance_metrics:
                self.performance_metrics["errors"] = []
            
            self.performance_metrics["errors"].append({
                "execution_id": execution_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            raise
            
        finally:
            # Calculate execution metrics
            execution_time = time.time() - start_time
            
            # Update performance metrics
            if "execution_times" not in self.performance_metrics:
                self.performance_metrics["execution_times"] = []
                
            self.performance_metrics["execution_times"].append({
                "execution_id": execution_id,
                "duration": execution_time,
                "timestamp": datetime.now().isoformat()
            })
            
            # Log performance
            if execution_time > 30:
                logger.warning(f"⚠️ Slow execution detected: {execution_time:.2f}s for {execution_id}")
            else:
                logger.info(f"✅ Execution {execution_id} completed in {execution_time:.2f}s")
    
    async def _background_monitor(self):
        """Background monitoring loop"""
        logger.info("🔍 Starting simple background monitoring")
        
        while self.monitoring_active:
            try:
                # Update timestamp
                self.performance_metrics["last_check"] = datetime.now().isoformat()
                
                # Log periodic status
                logger.info(f"📊 Monitoring status: {self.execution_count} executions processed")
                
                await asyncio.sleep(600)  # Check every 10 minutes (reasonable for simple monitor)
                
            except Exception as e:
                logger.error(f"Background monitoring error: {e}")
                await asyncio.sleep(60)
        
        logger.info("🔍 Simple background monitoring stopped")

    async def _portainer_heartbeat(self):
        """Lightweight heartbeat to prevent Portainer auto-restart"""
        logger.info("💓 Starting Portainer heartbeat (anti-restart)")
        
        heartbeat_count = 0
        while self.monitoring_active:
            try:
                # Increment heartbeat counter to show activity
                heartbeat_count += 1
                self.performance_metrics["heartbeat_count"] = heartbeat_count
                self.performance_metrics["last_heartbeat"] = datetime.now().isoformat()
                
                # Log heartbeat every 10 cycles (20 minutes)
                if heartbeat_count % 10 == 0:
                    logger.info(f"💓 Heartbeat #{heartbeat_count} - Container active for Portainer")
                
                # Check every 10 minutes (600s) - reasonable monitoring interval  
                await asyncio.sleep(600)
                
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(60)
        
        logger.info("💓 Portainer heartbeat stopped")


# Global monitor instance
simple_graph_monitor = SimpleGraphAuditMonitor()


async def initialize_simple_graph_monitoring():
    """Initialize simple graph monitoring on API startup"""
    await simple_graph_monitor.start_monitoring_session("graph_api_startup")


async def shutdown_simple_graph_monitoring():
    """Shutdown simple graph monitoring on API shutdown"""
    await simple_graph_monitor.stop_monitoring_session()


def get_simple_graph_monitor():
    """Get the global simple graph monitor instance"""
    return simple_graph_monitor