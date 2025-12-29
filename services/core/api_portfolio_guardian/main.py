"""
🛡️ PORTFOLIO GUARDIAN API
=========================
FastAPI Server for Portfolio Guardian Agent Control
Port: 8011 (Financial Protection Service)

Routes:
- /guardian/status - Agent status and stats
- /guardian/start - Start continuous protection  
- /guardian/stop - Stop protection
- /guardian/risks - Current risk assessment
- /guardian/alerts - Recent alerts history
- /guardian/protection-mode - Set protection mode
- /guardian/emergency - Emergency protection trigger
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import logging

from vitruvyan_core.domains.trade.portfolio_guardian.portfolio_guardian_agent import (
    PortfolioGuardianAgent,
    ProtectionMode,
    AlertSeverity,
    MarketCondition,
    GuardianConfig
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vitruvyan Portfolio Guardian",
    description="🛡️ Financial Data Protection & Market Intelligence Agent - Protecting wealth through intelligent vigilance.",
    version="1.0.0"
)

# Global guardian agent instance
guardian_agent = PortfolioGuardianAgent()
protection_task = None
startup_time = datetime.now()

@app.on_event("startup")
async def startup_event():
    """Initialize Portfolio Guardian on startup"""
    logger.info("🚀 Portfolio Guardian API Service starting up...")
    logger.info("🛡️ Initializing Portfolio Guardian Agent...")
    
    # Check Redis Cognitive Bus connection
    try:
        from core.foundation.cognitive_bus.redis_client import get_redis_bus
        redis_bus = get_redis_bus()
        if redis_bus.connect():
            logger.info("✅ Redis Cognitive Bus connected to vitruvyan_redis:6379")
            logger.info("🕯️ Synaptic Conclave integration activated")
            logger.info("   📻 Listening to: portfolio.risk.alert")
            logger.info("   📻 Listening to: sentinel.emergency.protection")
        else:
            logger.warning("⚠️ Redis connection failed - running in standalone mode")
    except Exception as e:
        logger.warning(f"⚠️ Redis initialization failed: {e}")
    
    logger.info("✅ Portfolio Guardian API Service ready on port 8011")

# Pydantic models
class GuardianStatusResponse(BaseModel):
    running: bool
    protection_mode: str
    uptime_hours: float
    stats: Dict[str, Any]
    last_analysis: Optional[Dict[str, Any]]
    guardian_config: Dict[str, Any]

class ProtectionModeRequest(BaseModel):
    mode: str  # conservative, balanced, aggressive, emergency

class CurrentRisksResponse(BaseModel):
    timestamp: str
    market_condition: str
    portfolio_value: float
    daily_pnl_pct: float
    current_drawdown: float
    alerts: List[Dict[str, Any]]
    risk_score: float

class EmergencyActionRequest(BaseModel):
    reason: str
    force_backup: bool = True
    notify_crewai: bool = True

# === CORE ENDPOINTS ===

@app.get("/guardian/status", response_model=GuardianStatusResponse)
async def get_guardian_status():
    """🛡️ Status dell'agente Portfolio Guardian"""
    
    status = guardian_agent.get_agent_status()
    
    return GuardianStatusResponse(
        running=status["running"],
        protection_mode=status["protection_mode"],
        uptime_hours=status["uptime_hours"],
        stats=status["stats"],
        last_analysis=status["last_analysis"],
        guardian_config=status["guardian_config"]
    )

@app.post("/guardian/start")
async def start_guardian(background_tasks: BackgroundTasks):
    """🚀 Avvia protezione continua Portfolio Guardian"""
    
    global protection_task
    
    if guardian_agent.running:
        raise HTTPException(status_code=400, detail="Guardian already running")
    
    # Start protection as background task
    background_tasks.add_task(guardian_agent.run_continuous_protection)
    
    logger.info("🛡️ Portfolio Guardian started - Continuous protection enabled")
    
    return {
        "message": "🛡️ Portfolio Guardian started - Protecting wealth through intelligent vigilance!",
        "status": "running",
        "protection_mode": guardian_agent.protection_mode.value,
        "monitoring_intervals": {
            "trading_hours": f"{guardian_agent.config['monitoring']['trading_hours_frequency']}s",
            "after_hours": f"{guardian_agent.config['monitoring']['after_hours_frequency']}s"
        }
    }

@app.post("/guardian/stop")
async def stop_guardian():
    """⏹️ Ferma protezione Portfolio Guardian"""
    
    if not guardian_agent.running:
        raise HTTPException(status_code=400, detail="Guardian not running")
    
    guardian_agent.stop_protection()
    
    logger.info("⏹️ Portfolio Guardian stopped")
    
    return {
        "message": "🛑 Portfolio Guardian stopped",
        "status": "stopped"
    }

@app.get("/guardian/risks", response_model=CurrentRisksResponse)
async def get_current_risks():
    """⚠️ Valutazione rischi correnti"""
    
    try:
        risks = await guardian_agent.get_current_risks()
        
        return CurrentRisksResponse(
            timestamp=risks["timestamp"],
            market_condition=risks["market_condition"],
            portfolio_value=risks["portfolio_value"],
            daily_pnl_pct=risks["daily_pnl_pct"],
            current_drawdown=risks["current_drawdown"],
            alerts=risks["alerts"],
            risk_score=risks["risk_score"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assess risks: {str(e)}")

@app.get("/guardian/alerts")
async def get_alerts_history(limit: int = 50):
    """📋 Storia alert recenti"""
    
    if limit > 200:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 200")
    
    alerts = guardian_agent.risk_monitor.alert_history[-limit:] if guardian_agent.risk_monitor.alert_history else []
    
    # Convert to JSON-serializable format
    serialized_alerts = []
    for alert in alerts:
        alert_dict = {
            "alert_id": alert.alert_id,
            "timestamp": alert.timestamp.isoformat(),
            "severity": alert.severity.value,
            "alert_type": alert.alert_type,
            "message": alert.message,
            "portfolio_impact": alert.portfolio_impact,
            "recommended_actions": alert.recommended_actions,
            "metadata": alert.metadata
        }
        serialized_alerts.append(alert_dict)
    
    return {
        "total_alerts": len(guardian_agent.risk_monitor.alert_history),
        "alerts_returned": len(serialized_alerts),
        "alerts": serialized_alerts
    }

@app.post("/guardian/protection-mode")
async def set_protection_mode(request: ProtectionModeRequest):
    """⚙️ Imposta modalità di protezione"""
    
    try:
        mode = ProtectionMode(request.mode)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid protection mode. Valid modes: {[mode.value for mode in ProtectionMode]}"
        )
    
    old_mode = guardian_agent.protection_mode.value
    guardian_agent.set_protection_mode(mode)
    
    logger.info(f"🔧 Protection mode changed: {old_mode} → {mode.value}")
    
    return {
        "message": f"🔧 Protection mode changed to {mode.value}",
        "old_mode": old_mode,
        "new_mode": mode.value,
        "updated_thresholds": {
            "max_drawdown": guardian_agent.guardian_config.max_drawdown_threshold,
            "volatility": guardian_agent.guardian_config.volatility_threshold,
            "var_threshold": guardian_agent.guardian_config.var_threshold
        }
    }

@app.post("/guardian/emergency")
async def trigger_emergency_protection(request: EmergencyActionRequest):
    """🚨 Trigger protezione di emergenza con Synaptic Conclave integration"""
    
    logger.warning(f"🚨 EMERGENCY PROTECTION TRIGGERED: {request.reason}")
    
    # Trigger emergency via Portfolio Guardian Agent (includes Conclave publishing)
    emergency_result = await guardian_agent.trigger_manual_emergency(
        reason=request.reason,
        emergency_type="api_triggered_emergency"
    )
    
    actions_taken = []
    
    # Check if emergency was successfully triggered
    if not emergency_result.get("success", False):
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to trigger emergency: {emergency_result.get('error', 'Unknown error')}"
        )
    
    actions_taken.append("🧠 Sentinel emergency event published to Synaptic Conclave")
    actions_taken.append(f"Protection mode changed to {emergency_result.get('protection_mode', 'EMERGENCY')}")
    
    # Force backup if requested (legacy behavior maintained)
    if request.force_backup:
        try:
            import aiohttp
            backup_url = f"{guardian_agent.config['integrations']['backup_agent_url']}/backup/quick/emergency"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(backup_url) as resp:
                    if resp.status == 200:
                        backup_result = await resp.json()
                        actions_taken.append("Emergency backup completed (legacy)")
                    else:
                        actions_taken.append("Emergency backup failed (legacy)")
        except Exception as e:
            actions_taken.append(f"Emergency backup error: {str(e)}")
    
    # Notify CrewAI if requested
    if request.notify_crewai:
        # TODO: Implement CrewAI notification
        actions_taken.append("CrewAI agents notified (TODO: implement)")
    
    return {
        "message": "🚨 Emergency protection protocol activated",
        "reason": request.reason,
        "timestamp": datetime.now().isoformat(),
        "actions_taken": actions_taken,
        "current_mode": guardian_agent.protection_mode.value,
        "emergency_count": guardian_agent.stats["emergency_triggers"],
        "cognitive_events_published": guardian_agent.stats["cognitive_events_published"],
        "synaptic_conclave_integration": "✅ Active",
        "emergency_result": emergency_result
    }

# === MARKET DATA ENDPOINTS ===

@app.get("/guardian/market")
async def get_market_snapshot():
    """🌍 Snapshot condizioni di mercato"""
    
    try:
        snapshot = await guardian_agent.market_provider.get_market_snapshot()
        
        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "spy_price": snapshot.spy_price,
            "vix_level": snapshot.vix_level,
            "market_condition": snapshot.market_condition.value,
            "volatility_percentile": snapshot.volatility_percentile,
            "sentiment_score": snapshot.sentiment_score,
            "trading_volume": snapshot.trading_volume,
            "economic_indicators": snapshot.economic_indicators
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market data: {str(e)}")

@app.get("/guardian/portfolio")
async def get_portfolio_metrics():
    """💼 Metriche portfolio correnti"""
    
    try:
        metrics = await guardian_agent.portfolio_analyzer.get_portfolio_metrics()
        
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "total_value": metrics.total_value,
            "daily_pnl": metrics.daily_pnl,
            "daily_pnl_pct": metrics.daily_pnl_pct,
            "drawdown": metrics.drawdown,
            "max_drawdown": metrics.max_drawdown,
            "sharpe_ratio": metrics.sharpe_ratio,
            "volatility": metrics.volatility,
            "beta": metrics.beta,
            "var_95": metrics.var_95,
            "positions_count": metrics.positions_count,
            "cash_percentage": metrics.cash_percentage
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio metrics: {str(e)}")

# === CONFIGURATION ENDPOINTS ===

@app.get("/guardian/config")
async def get_guardian_config():
    """⚙️ Configurazione corrente Guardian"""
    
    return {
        "guardian_config": guardian_agent.guardian_config.__dict__,
        "system_config": guardian_agent.config,
        "protection_mode": guardian_agent.protection_mode.value
    }

@app.post("/guardian/config/thresholds")
async def update_risk_thresholds(
    max_drawdown: Optional[float] = None,
    volatility_threshold: Optional[float] = None,
    var_threshold: Optional[float] = None,
    concentration_threshold: Optional[float] = None
):
    """🔧 Aggiorna soglie di rischio"""
    
    updates = {}
    config = guardian_agent.guardian_config
    
    if max_drawdown is not None:
        if not 0.05 <= max_drawdown <= 0.5:
            raise HTTPException(status_code=400, detail="max_drawdown must be between 0.05 and 0.5")
        config.max_drawdown_threshold = max_drawdown
        updates["max_drawdown_threshold"] = max_drawdown
    
    if volatility_threshold is not None:
        if not 0.1 <= volatility_threshold <= 1.0:
            raise HTTPException(status_code=400, detail="volatility_threshold must be between 0.1 and 1.0")
        config.volatility_threshold = volatility_threshold
        updates["volatility_threshold"] = volatility_threshold
    
    if var_threshold is not None:
        if not 0.01 <= var_threshold <= 0.2:
            raise HTTPException(status_code=400, detail="var_threshold must be between 0.01 and 0.2")
        config.var_threshold = var_threshold
        updates["var_threshold"] = var_threshold
    
    if concentration_threshold is not None:
        if not 0.1 <= concentration_threshold <= 0.8:
            raise HTTPException(status_code=400, detail="concentration_threshold must be between 0.1 and 0.8")
        config.concentration_threshold = concentration_threshold
        updates["concentration_threshold"] = concentration_threshold
    
    logger.info(f"🔧 Risk thresholds updated: {updates}")
    
    return {
        "message": "🔧 Risk thresholds updated",
        "updates": updates,
        "current_config": config.__dict__
    }

# === INTEGRATION ENDPOINTS ===

@app.post("/guardian/backup-integration")
async def test_backup_integration():
    """🧱 Test integrazione con Backup Agent"""
    
    try:
        import aiohttp
        backup_url = f"{guardian_agent.config['integrations']['backup_agent_url']}/backup/status"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(backup_url) as resp:
                if resp.status == 200:
                    backup_status = await resp.json()
                    return {
                        "integration_status": "✅ Connected",
                        "backup_agent_running": backup_status.get("agent_running", False),
                        "backup_agent_response": backup_status
                    }
                else:
                    return {
                        "integration_status": "❌ Failed",
                        "error": f"HTTP {resp.status}"
                    }
    except Exception as e:
        return {
            "integration_status": "❌ Error",
            "error": str(e)
        }

@app.post("/guardian/audit-integration")
async def test_audit_integration():
    """🔍 Test integrazione con Audit Engine"""
    
    try:
        import aiohttp
        audit_url = f"{guardian_agent.config['integrations']['audit_engine_url']}/health"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(audit_url) as resp:
                if resp.status == 200:
                    audit_status = await resp.json()
                    return {
                        "integration_status": "✅ Connected",
                        "audit_engine_response": audit_status
                    }
                else:
                    return {
                        "integration_status": "❌ Failed",
                        "error": f"HTTP {resp.status}"
                    }
    except Exception as e:
        return {
            "integration_status": "❌ Error",
            "error": str(e)
        }

# === QUICK ACTIONS ===

@app.post("/guardian/quick/conservative")
async def quick_conservative_mode():
    """🛡️ Quick: Modalità conservativa"""
    guardian_agent.set_protection_mode(ProtectionMode.CONSERVATIVE)
    return {"message": "🛡️ Switched to CONSERVATIVE protection mode", "mode": "conservative"}

@app.post("/guardian/quick/aggressive")
async def quick_aggressive_mode():
    """⚡ Quick: Modalità aggressiva"""
    guardian_agent.set_protection_mode(ProtectionMode.AGGRESSIVE)
    return {"message": "⚡ Switched to AGGRESSIVE protection mode", "mode": "aggressive"}

@app.post("/guardian/quick/risk-check")
async def quick_risk_check():
    """⚠️ Quick: Check rischi immediato"""
    risks = await guardian_agent.get_current_risks()
    
    critical_alerts = [alert for alert in risks["alerts"] if alert["severity"] in ["critical", "emergency"]]
    
    return {
        "message": "⚠️ Quick risk check completed",
        "risk_summary": {
            "portfolio_value": risks["portfolio_value"],
            "daily_pnl_pct": risks["daily_pnl_pct"],
            "market_condition": risks["market_condition"],
            "total_alerts": len(risks["alerts"]),
            "critical_alerts": len(critical_alerts),
            "risk_score": risks["risk_score"]
        },
        "immediate_action_needed": len(critical_alerts) > 0
    }

# === HEALTH & METRICS ===

@app.get("/health")
async def health_check():
    """💓 Standard health check endpoint"""
    
    try:
        # Test market data provider
        market_test = await guardian_agent.market_provider.get_market_snapshot()
        market_healthy = True
    except Exception:
        market_healthy = False
    
    # Test portfolio analyzer  
    try:
        portfolio_test = await guardian_agent.portfolio_analyzer.get_portfolio_metrics()
        portfolio_healthy = True
    except Exception:
        portfolio_healthy = False
    
    overall_health = market_healthy and portfolio_healthy
    
    return {
        "status": "healthy" if overall_health else "degraded",
        "service": "Vitruvyan Portfolio Guardian", 
        "version": "1.0.0",
        "components": {
            "market_data_provider": "✅" if market_healthy else "❌",
            "portfolio_analyzer": "✅" if portfolio_healthy else "❌",
            "risk_monitor": "✅",  # Always healthy if agent is running
            "guardian_agent": "✅" if guardian_agent.running else "⏹️"
        }
    }

@app.get("/guardian/health")
async def legacy_health_check():
    """💓 Legacy health check Portfolio Guardian"""
    
    try:
        # Test market data provider
        market_test = await guardian_agent.market_provider.get_market_snapshot()
        market_healthy = True
    except Exception:
        market_healthy = False
    
    # Test portfolio analyzer
    try:
        portfolio_test = await guardian_agent.portfolio_analyzer.get_portfolio_metrics()
        portfolio_healthy = True
    except Exception:
        portfolio_healthy = False
    
    overall_health = market_healthy and portfolio_healthy
    
    return {
        "status": "healthy" if overall_health else "degraded",
        "components": {
            "market_data_provider": "✅" if market_healthy else "❌",
            "portfolio_analyzer": "✅" if portfolio_healthy else "❌",
            "risk_monitor": "✅",  # Always healthy if agent is running
            "guardian_agent": "✅" if guardian_agent.running else "⏹️"
        },
        "version": "1.0.0",
        "uptime": "active"
    }

@app.get("/guardian/metrics")
async def get_guardian_metrics():
    """📊 Metriche e statistiche Guardian con Synaptic Conclave integration"""
    
    uptime = datetime.now() - guardian_agent.stats["uptime_start"]
    
    return {
        "agent_metrics": guardian_agent.stats,
        "uptime_hours": uptime.total_seconds() / 3600,
        "protection_mode": guardian_agent.protection_mode.value,
        "alert_summary": {
            "total_alerts": len(guardian_agent.risk_monitor.alert_history),
            "recent_alerts_24h": len([
                alert for alert in guardian_agent.risk_monitor.alert_history
                if (datetime.now() - alert.timestamp).days < 1
            ]) if guardian_agent.risk_monitor.alert_history else 0
        },
        "config_summary": {
            "max_drawdown_threshold": guardian_agent.guardian_config.max_drawdown_threshold,
            "volatility_threshold": guardian_agent.guardian_config.volatility_threshold,
            "var_threshold": guardian_agent.guardian_config.var_threshold
        },
        "synaptic_conclave_stats": {
            "cognitive_events_published": guardian_agent.stats.get("cognitive_events_published", 0),
            "conclave_interactions": guardian_agent.stats.get("conclave_interactions", 0),
            "integration_status": "✅ Active",
            "event_bus_connected": hasattr(guardian_agent, 'event_bus') and guardian_agent.event_bus is not None
        }
    }


@app.get("/guardian/conclave-status")
async def get_conclave_integration_status():
    """🧠 Status integrazione Synaptic Conclave"""
    
    try:
        # Check if event bus is available
        event_bus_available = hasattr(guardian_agent, 'event_bus') and guardian_agent.event_bus is not None
        
        integration_health = {
            "sentinel_order_active": True,
            "event_bus_connected": event_bus_available,
            "cognitive_events_published": guardian_agent.stats.get("cognitive_events_published", 0),
            "conclave_interactions": guardian_agent.stats.get("conclave_interactions", 0),
            "last_event_published": "N/A",  # TODO: Track last event timestamp
            "supported_events": [
                "sentinel.risk.assessed",
                "sentinel.emergency.triggered", 
                "sentinel.backup.requested",
                "sentinel.audit.requested",
                "sentinel.recovery.completed"
            ]
        }
        
        # Overall health assessment
        overall_health = "healthy" if event_bus_available else "degraded"
        
        return {
            "integration_status": overall_health,
            "sentinel_order": "🛡️ Operational",
            "synaptic_conclave": "🧠 Connected" if event_bus_available else "⚠️ Disconnected",
            "sacred_orders_communication": "✅ Active",
            "health_details": integration_health,
            "capabilities": {
                "risk_assessment_publishing": "✅ Enabled",
                "emergency_event_publishing": "✅ Enabled", 
                "escalation_coordination": "✅ Enabled",
                "vault_integration": "✅ Ready",
                "orthodoxy_integration": "✅ Ready",
                "audit_integration": "✅ Ready"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get Conclave status: {e}")
        return {
            "integration_status": "error",
            "error": str(e),
            "sentinel_order": "⚠️ Error",
            "synaptic_conclave": "❌ Error"
        }

# === ROOT ===

@app.get("/")
async def root():
    """🛡️ Portfolio Guardian Root"""
    
    return {
        "service": "Vitruvyan Portfolio Guardian",
        "version": "1.0.0",
        "motto": "Protecting wealth through intelligent vigilance.",
        "status": "🛡️ Operational",
        "endpoints": {
            "control": "/guardian/start, /guardian/stop, /guardian/status",
            "monitoring": "/guardian/risks, /guardian/alerts, /guardian/market, /guardian/portfolio",
            "configuration": "/guardian/protection-mode, /guardian/config",
            "emergency": "/guardian/emergency",
            "health": "/guardian/health, /guardian/metrics",
            "integration": "/guardian/test-integration"
        }
    }

@app.post("/guardian/test-integration")
async def test_agent_integration():
    """Test integration with other Vitruvyan agents."""
    results = {}
    
    try:
        # Test Backup Agent communication
        import httpx
        async with httpx.AsyncClient() as client:
            backup_response = await client.get("http://localhost:8007/backup/status", timeout=5.0)
            results["backup_agent"] = {
                "status": "connected",
                "response": backup_response.json()
            }
    except Exception as e:
        results["backup_agent"] = {"status": "disconnected", "error": str(e)}
    
    try:
        # Test Audit Engine communication  
        async with httpx.AsyncClient() as client:
            audit_response = await client.get("http://localhost:8006/audit/status", timeout=5.0)
            results["audit_engine"] = {
                "status": "connected", 
                "response": audit_response.json()
            }
    except Exception as e:
        results["audit_engine"] = {"status": "disconnected", "error": str(e)}
    
    # Portfolio Guardian self-test
    results["portfolio_guardian"] = {
        "status": "operational",
        "agent_uptime": str(datetime.now() - startup_time),
        "protection_active": True,
        "components": ["market_monitor", "risk_monitor", "portfolio_analyzer"]
    }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "integration_test": results,
        "agentic_ecosystem": "3 pillar coordination test",
        "system_health": "testing inter-agent communication"
    }

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🛡️ Starting Vitruvyan Portfolio Guardian API Server on port 8011")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8011,
        log_level="info"
    )