"""
Orthodoxy Wardens — Sacred Order API (LIVELLO 2 Entry Point)

Thin FastAPI shell.  All logic delegated to:
  - api/routes.py            HTTP endpoints
  - adapters/bus_adapter.py  Pure domain pipeline (LIVELLO 1)
  - adapters/persistence.py  Database I/O
  - monitoring/health.py     Synaptic Conclave listeners
  - core/roles.py            Sacred Roles (legacy event-driven)
  - core/workflows.py        Workflow orchestration (legacy)
"""

import logging
import os
import sys

from fastapi import FastAPI

sys.path.append("/app")

# --- Service-layer imports ---------------------------------------------------
from api_orthodoxy_wardens.api.routes import router
from api_orthodoxy_wardens.config import settings
from api_orthodoxy_wardens.monitoring.health import setup_synaptic_conclave_listeners
from api_orthodoxy_wardens.adapters.bus_adapter import OrthodoxyBusAdapter
from api_orthodoxy_wardens.core import event_handlers
from api_orthodoxy_wardens.core.roles import (
    OrthodoxConfessor, OrthodoxPenitent, OrthodoxChronicler,
    OrthodoxInquisitor, OrthodoxAbbot,
)
from api_orthodoxy_wardens.core.workflows import set_agents

# --- Legacy agents (routes.py reads these via `import __main__`) -------------
from core.governance.orthodoxy_wardens.confessor_agent import AutonomousAuditAgent
from core.governance.orthodoxy_wardens._legacy.chronicler_agent import SystemMonitor
from core.governance.orthodoxy_wardens.inquisitor_agent import ComplianceValidator
from core.governance.orthodoxy_wardens.penitent_agent import AutoCorrector
from core.llm.llm_interface import LLMInterface
from core.agents.postgres_agent import PostgresAgent
from api_orthodoxy_wardens.core.orthodoxy_db_manager import OrthodoxyDatabaseManager

# --- Logging -----------------------------------------------------------------
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger("OrthodoxyWardens")

# --- App ---------------------------------------------------------------------
app = FastAPI(title="Orthodoxy Wardens", version="2.0.0")
app.include_router(router)

# --- Module globals (routes.py reads via `import __main__`) ------------------
confessor_agent = penitent_agent = chronicler_agent = None
inquisitor_agent = abbot_agent = llm_interface = None
orthodoxy_db_manager = orthodoxy_vector_manager = None
orthodoxy_analytics = sacred_guardrails = divine_healing_integrator = None
sacred_confessor = sacred_penitent = sacred_chronicler = None
sacred_inquisitor = sacred_abbot = None
bus_adapter: OrthodoxyBusAdapter | None = None


# --- Startup -----------------------------------------------------------------
@app.on_event("startup")
async def startup():
    global confessor_agent, penitent_agent, chronicler_agent
    global inquisitor_agent, abbot_agent, llm_interface
    global orthodoxy_db_manager, bus_adapter

    test_mode = os.getenv("VITRUVYAN_TEST_MODE", "false").lower() == "true"
    logger.info("Initializing Orthodoxy Wardens (test_mode=%s)", test_mode)

    # Pure domain pipeline (LIVELLO 1) — always available
    bus_adapter = OrthodoxyBusAdapter()

    # Legacy agents (backward compat for routes.py)
    if not test_mode:
        llm_interface = LLMInterface()
        try:
            orthodoxy_db_manager = OrthodoxyDatabaseManager()
        except Exception as exc:
            logger.error("OrthodoxyDatabaseManager init failed: %s", exc)

        confessor_agent = AutonomousAuditAgent(config={
            "llm_interface": llm_interface,
            "db_manager": orthodoxy_db_manager, "role": "Confessor",
        })
        penitent_agent = AutoCorrector()
        chronicler_agent = SystemMonitor()
        inquisitor_agent = ComplianceValidator(llm_interface=llm_interface)
        abbot_agent = AutonomousAuditAgent(config={
            "llm_interface": llm_interface,
            "db_manager": orthodoxy_db_manager, "role": "Abbot",
        })
        set_agents(confessor_agent, penitent_agent, chronicler_agent,
                   inquisitor_agent, orthodoxy_db_manager)

    # Sacred Roles → event handler injection + module globals for routes.py
    global sacred_confessor, sacred_penitent, sacred_chronicler
    global sacred_inquisitor, sacred_abbot
    sacred_confessor = OrthodoxConfessor()
    sacred_penitent = OrthodoxPenitent()
    sacred_chronicler = OrthodoxChronicler()
    sacred_inquisitor = OrthodoxInquisitor()
    sacred_abbot = OrthodoxAbbot()
    event_handlers.inject_sacred_roles(
        confessor=sacred_confessor, penitent=sacred_penitent,
        chronicler=sacred_chronicler, inquisitor=sacred_inquisitor,
        abbot=sacred_abbot,
    )

    # Synaptic Conclave listeners
    if not test_mode:
        await setup_synaptic_conclave_listeners()

    logger.info("Orthodoxy Wardens ready (bus_adapter=%s)", bus_adapter is not None)


# --- Entry point -------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.SERVICE_PORT, log_level="info")