"""
Orthodoxy Wardens — Sacred Order API (LIVELLO 2)
FastAPI bootstrap. Logic delegated to adapters/.
"""
import logging
import os
import sys
from fastapi import FastAPI

sys.path.append("/app")

from api_orthodoxy_wardens.api.routes import router
from api_orthodoxy_wardens.config import settings
from api_orthodoxy_wardens.monitoring.health import setup_synaptic_conclave_listeners, metrics_endpoint
from api_orthodoxy_wardens.adapters.bus_adapter import OrthodoxyBusAdapter
from api_orthodoxy_wardens.adapters import event_handlers
from api_orthodoxy_wardens.adapters.roles import (
    OrthodoxConfessor, OrthodoxPenitent, OrthodoxChronicler, OrthodoxInquisitor, OrthodoxAbbot
)
from api_orthodoxy_wardens.adapters.workflows import set_agents
from core.governance.orthodoxy_wardens._legacy.confessor_agent import AutonomousAuditAgent
from core.governance.orthodoxy_wardens._legacy.inquisitor_agent import ComplianceValidator
from core.governance.orthodoxy_wardens._legacy.penitent_agent import AutoCorrector
from core.agents.llm_agent import get_llm_agent
from core.agents.postgres_agent import PostgresAgent
from api_orthodoxy_wardens.adapters.orthodoxy_db_manager import OrthodoxyDatabaseManager

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger("OrthodoxyWardens")

app = FastAPI(title="Orthodoxy Wardens", version="2.0.0")
app.include_router(router)

# Module globals (routes.py reads via `import __main__`)
confessor_agent = penitent_agent = chronicler_agent = inquisitor_agent = abbot_agent = None
llm_interface = orthodoxy_db_manager = orthodoxy_vector_manager = None
orthodoxy_analytics = sacred_guardrails = divine_healing_integrator = None
sacred_confessor = sacred_penitent = sacred_chronicler = sacred_inquisitor = sacred_abbot = None
bus_adapter: OrthodoxyBusAdapter | None = None

@app.on_event("startup")
async def startup():
    global confessor_agent, penitent_agent, chronicler_agent, inquisitor_agent, abbot_agent
    global llm_interface, orthodoxy_db_manager, bus_adapter, sacred_confessor, sacred_penitent
    global sacred_chronicler, sacred_inquisitor, sacred_abbot

    test_mode = os.getenv("VITRUVYAN_TEST_MODE", "false").lower() == "true"
    logger.info("Initializing Orthodoxy Wardens (test_mode=%s)", test_mode)

    bus_adapter = OrthodoxyBusAdapter()

    if not test_mode:
        llm_agent = get_llm_agent()
        try:
            orthodoxy_db_manager = OrthodoxyDatabaseManager()
        except Exception as exc:
            logger.error("OrthodoxyDatabaseManager init failed: %s", exc)

        confessor_agent = AutonomousAuditAgent(config={
            "db_manager": orthodoxy_db_manager, "role": "Confessor"
        })
        penitent_agent = AutoCorrector()
        chronicler_agent = None  # SystemMonitor removed (legacy)
        inquisitor_agent = ComplianceValidator(llm_interface=llm_agent)
        abbot_agent = AutonomousAuditAgent(config={
            "db_manager": orthodoxy_db_manager, "role": "Abbot"
        })
        set_agents(confessor_agent, penitent_agent, chronicler_agent, inquisitor_agent, orthodoxy_db_manager)

        sacred_confessor = OrthodoxConfessor()
        sacred_penitent = OrthodoxPenitent()
        sacred_chronicler = OrthodoxChronicler()
        sacred_inquisitor = OrthodoxInquisitor()
        sacred_abbot = OrthodoxAbbot()
        event_handlers.inject_sacred_roles(
            confessor=sacred_confessor, penitent=sacred_penitent, chronicler=sacred_chronicler,
            inquisitor=sacred_inquisitor, abbot=sacred_abbot
        )
        await setup_synaptic_conclave_listeners()
    else:
        logger.info("TEST_MODE: Skipping Sacred Roles + Conclave")

    logger.info("Orthodoxy Wardens ready")


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    return await metrics_endpoint()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.SERVICE_PORT, log_level="info")