"""
    💓 The Pulse of the Synaptic Conclave
Heartbeat monitoring and system vitality

The Pulse maintains the rhythm of the cognitive organism,
ensuring all Orders remain connected and responsive.
"""
    
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import structlog

from .heart import get_heart
from .herald import get_herald
from .scribe import get_scribe

logger = structlog.get_logger("conclave.pulse")


class ConclavePulse:
    """
    The Pulse manages system heartbeat and vitality monitoring.
    """
    
    def __init__(self, pulse_interval: int = 30):
        self.pulse_interval = pulse_interval  # seconds
        self.is_beating = False
        self.heartbeat_count = 0
        self.last_pulse: Optional[datetime] = None
        self.pulse_task: Optional[asyncio.Task] = None
        
        # Vitality tracking
        self.daily_events = 0
        self.last_daily_reset = datetime.utcnow().date()
    
    async def start_beating(self):
        """
        Start the system heartbeat pulse.
        """
        if self.is_beating:
            logger.warning("💓 Pulse already beating")
            return
        
        self.is_beating = True
        self.pulse_task = asyncio.create_task(self._pulse_loop())
        
        logger.info(
            "💓 Conclave Pulse started beating",
            interval_seconds=self.pulse_interval
        )
    
    async def stop_beating(self):
        """
        Stop the system heartbeat pulse.
        """
        self.is_beating = False
        
        if self.pulse_task:
            self.pulse_task.cancel()
            try:
                await self.pulse_task
            except asyncio.CancelledError:
                pass
        
        logger.info("💤 Conclave Pulse stopped")
    
    async def _pulse_loop(self):
        """
        Main pulse loop - runs every pulse_interval seconds.
        """
        try:
            while self.is_beating:
                await self._emit_heartbeat()
                await asyncio.sleep(self.pulse_interval)
                
        except asyncio.CancelledError:
            logger.info("💓 Pulse loop cancelled")
            raise
        except Exception as e:
            logger.error("💔 Pulse loop error", error=str(e))
            self.is_beating = False
    
    async def _emit_heartbeat(self):
        """
        Emit a single heartbeat event.
        """
        try:
            # Reset daily counter if needed
            today = datetime.utcnow().date()
            if today != self.last_daily_reset:
                self.daily_events = 0
                self.last_daily_reset = today
            
            # Get system vitals (all async - must await!)
            herald = await get_herald()  # ✅ Fixed: added await
            heart = await get_heart()
            scribe = await get_scribe()  # ✅ Fixed: added await
            
            # Check Order health
            order_health = await herald.check_order_health()
            heart_vitals = await heart.get_vitals()  # ✅ Fixed: get_vitals() not get_vital_signs()
            
            # Count active Orders
            active_orders = sum(1 for status in order_health.values() 
                              if status.get("status") == "alive")
            
            # Prepare heartbeat payload
            heartbeat_payload = {
                "heartbeat_count": self.heartbeat_count,
                "active_orders": active_orders,
                "total_orders": len(order_health),
                "total_events_today": self.daily_events,
                "redis_status": "connected" if heart_vitals["redis_connected"] else "disconnected",
                "system_load": await self._get_system_load(),
                "pulse_interval": self.pulse_interval,
                "uptime_seconds": self._get_uptime_seconds(),
                "order_health_summary": {
                    name: status.get("status", "unknown") 
                    for name, status in order_health.items()
                }
            }
            
            # Emit heartbeat event to Redis (for real-time monitoring)
            await heart.publish_event("conclave", "pulse", heartbeat_payload)
            
            # Update pulse state
            self.heartbeat_count += 1
            self.last_pulse = datetime.utcnow()
            self.daily_events += 1
            
            # Log vital signs (both print for Docker logs visibility and structured logging)
            print(f"💓 [PULSE] Heartbeat #{self.heartbeat_count} | Orders: {active_orders}/10 alive | Load: {heartbeat_payload.get('system_load', 0):.3f}")
            logger.info(
                "💓 Heartbeat emitted successfully",
                beat=self.heartbeat_count,
                active_orders=active_orders,
                redis_ok=heart_vitals["redis_connected"],
                events_today=self.daily_events
            )
            
            # Check for critical issues
            await self._check_vitality(order_health, heart_vitals)
            
        except Exception as e:
            logger.error(f"💔 Failed to emit heartbeat: {e}")
            # Add retry delay to prevent tight error loops
            await asyncio.sleep(5)
    
    async def _check_vitality(self, order_health: Dict[str, Any], heart_vitals: Dict[str, Any]):
        """
        Check system vitality and emit alerts if needed.
        """
        critical_issues = []
        
        # Check Redis connectivity
        if not heart_vitals["redis_connected"]:
            critical_issues.append("Redis connection lost")
        
        # Check critical Orders
        critical_orders = ["babel", "orthodoxy", "conclave"]
        for order in critical_orders:
            if order in order_health:
                status = order_health[order].get("status")
                if status != "alive":
                    critical_issues.append(f"Critical Order '{order}' is {status}")
        
        # Check if too many Orders are down
        alive_count = sum(1 for status in order_health.values() 
                         if status.get("status") == "alive")
        total_count = len(order_health)
        
        if alive_count < total_count * 0.5:  # Less than 50% alive
            critical_issues.append(f"Only {alive_count}/{total_count} Orders responsive")
        
        # Emit critical health events if needed
        if critical_issues:
            heart = await get_heart()
            await heart.publish_event("system", "health.critical", {
                "component": "conclave_pulse",
                "issues": critical_issues,
                "severity": len(critical_issues),
                "suggested_action": "check_order_logs_and_restart_services",
                "alive_orders": alive_count,
                "total_orders": total_count
            })
            
            logger.error(
                "🚨 Critical system health issues detected",
                issues=critical_issues,
                alive_orders=alive_count
            )
    
    async def _get_system_load(self) -> float:
        """
        Get approximate system load.
        """
        try:
            # Simple approximation based on recent events
            # In a real implementation, this would check CPU/memory
            return min(self.daily_events / 1000.0, 1.0)
        except:
            return 0.0
    
    def _get_uptime_seconds(self) -> int:
        """
        Get system uptime in seconds.
        """
        if self.last_pulse:
            uptime = datetime.utcnow() - (self.last_pulse - timedelta(seconds=self.pulse_interval * self.heartbeat_count))
            return int(uptime.total_seconds())
        return 0
    
    async def get_pulse_status(self) -> Dict[str, Any]:
        """
        Get current pulse status and vitals.
        """
        return {
            "is_beating": self.is_beating,
            "heartbeat_count": self.heartbeat_count,
            "pulse_interval": self.pulse_interval,
            "last_pulse": self.last_pulse.isoformat() if self.last_pulse else None,
            "daily_events": self.daily_events,
            "last_daily_reset": self.last_daily_reset.isoformat(),
            "uptime_seconds": self._get_uptime_seconds(),
            "estimated_system_load": await self._get_system_load()
        }
    
    async def force_heartbeat(self) -> bool:
        """
        Force an immediate heartbeat emission.
        """
        try:
            await self._emit_heartbeat()
            logger.info("💓 Forced heartbeat emitted")
            return True
        except Exception as e:
            logger.error("💔 Failed to force heartbeat", error=str(e))
            return False


# Global Pulse instance
_pulse: Optional[ConclavePulse] = None

async def get_pulse() -> ConclavePulse:
    """
    Get the global Pulse instance.
    """
    global _pulse
    if _pulse is None:
        _pulse = ConclavePulse()
    return _pulse

async def start_system_pulse(interval: int = 30):
    """
    Start the system-wide pulse.
    """
    pulse = await get_pulse()
    await pulse.start_beating()

async def stop_system_pulse():
    """
    Stop the system-wide pulse.
    """
    pulse = await get_pulse()
    await pulse.stop_beating()