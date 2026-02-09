"""
🏛️ ORTHODOXY WARDENS - Sacred Compliance & Divine Order API
Theological guardians of system orthodoxy, ensuring sacred architecture compliance
and maintaining the divine harmony of the Vitruvyan realm.

Sacred Roles:
- Confessor: Hears system sins and validates compliance confessions
- Penitent: Performs remediation rituals and purification rites  
- Chronicler: Records sacred events and maintains divine documentation
- Inquisitor: Investigates heretical code and architectural blasphemy
- Abbot: Oversees sacred operations and provides divine guidance
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import logging
from datetime import datetime, timedelta
import os
import sys
import json

# Add to path for imports
sys.path.append('/app')

# Sacred Theological Agents (refactored to governance/orthodoxy_wardens)
from core.governance.orthodoxy_wardens.confessor_agent import AutonomousAuditAgent  # Sacred Confessor
from core.governance.orthodoxy_wardens.chronicler_agent import SystemMonitor  # Chronicler
from core.governance.orthodoxy_wardens.inquisitor_agent import ComplianceValidator  # Inquisitor
from core.governance.orthodoxy_wardens.penitent_agent import AutoCorrector  # Penitent
# LLM interface for sacred reasoning
from core.llm.llm_interface import LLMInterface
# Standard Vitruvyan agents
from core.agents.postgres_agent import PostgresAgent
from api_orthodoxy_wardens.core.orthodoxy_db_manager import OrthodoxyDatabaseManager

# Import Pydantic schemas (FASE 2 - Feb 9, 2026)
from api_orthodoxy_wardens.models.schemas import (
    DivineHealthResponse,
    ConfessionRequest,
    OrthodoxyStatusResponse
)

# 🕯️ SYNAPTIC CONCLAVE INTEGRATION - Redis Streams Cognitive Bus (Refactored Feb 2026)
from core.synaptic_conclave.transport.streams import StreamBus
from core.synaptic_conclave.events.event_envelope import CognitiveEvent
import threading
import asyncio

# Import Sacred Roles & Event Handlers from api_orthodoxy_wardens.core/ (P1 FASE 3 - Feb 8, 2026)
# FIXED: Import path must include service package (api_orthodoxy_wardens) not just core/
from api_orthodoxy_wardens.core.roles import (
    SacredRole,
    OrthodoxConfessor,
    OrthodoxPenitent,
    OrthodoxChronicler,
    OrthodoxInquisitor,
    OrthodoxAbbot
)
from api_orthodoxy_wardens.core import event_handlers  # Import module for dependency injection
from api_orthodoxy_wardens.core.event_handlers import (
    handle_audit_request,
    handle_heresy_detection,
    handle_system_events
)
from api_orthodoxy_wardens.core.workflows import (
    run_confession_workflow,
    run_purification_ritual,
    divine_surveillance_monitoring,
    set_agents
)

# Import API routes (FASE 2 - Task 1.4 - Feb 9, 2026)
from api_orthodoxy_wardens.api.routes import router

# Import monitoring utilities (FASE 2 - Task 1.5 - Feb 9, 2026)
from api_orthodoxy_wardens.monitoring.health import setup_synaptic_conclave_listeners

# Import sacred extensions
# Legacy audit_engine imports (refactored into orthodoxy_wardens agents)
# from core.audit_engine.audit_database_manager import AuditDatabaseManager as OrthodoxyDatabaseManager
# from core.audit_engine.audit_vector_manager import AuditVectorManager as OrthodoxyVectorManager 
# from core.audit_engine.audit_analytics import AuditAnalytics as OrthodoxyAnalytics
# from core.orthodoxy_engine.sacred_guardrails import SacredArchitecturalGuardrails
# from core.orthodoxy_engine.divine_healing_integrator import DivineHealingIntegrator

# Configure sacred logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OrthodoxyWardens")

# =============================================================================
# SACRED THEOLOGICAL ROLES - NOW IMPORTED FROM core/roles.py (P1 FASE 3)
# =============================================================================
# Sacred Roles moved to services/governance/api_orthodoxy_wardens/core/roles.py
# for better separation of business logic from deployment code.
# Import above: from core.roles import (...)

# FastAPI app - Sacred Portal
app = FastAPI(
    title="🏛️ Vitruvyan Orthodoxy Wardens",
    description="Sacred guardians of system orthodoxy and divine architectural compliance",
    version="1.0.0"
)

# Include API routes (FASE 2 - Task 1.4 - Feb 9, 2026)
app.include_router(router)

# Sacred Divine Council - Initialize theological roles
confessor_agent = None  # Hears system confessions and validates compliance
penitent_agent = None   # Performs remediation and purification rituals
chronicler_agent = None # Records sacred events and divine documentation
inquisitor_agent = None # Investigates heretical code and blasphemy
abbot_agent = None      # Oversees sacred operations and provides guidance
llm_interface = None

# Global Sacred Order instances
sacred_confessor = None
sacred_penitent = None
sacred_chronicler = None
sacred_inquisitor = None
sacred_abbot = None

# =============================================================================
# SYNAPTIC CONCLAVE EVENT HANDLERS - NOW IMPORTED FROM core/event_handlers.py
# =============================================================================
# Event handlers moved to services/governance/api_orthodoxy_wardens/core/event_handlers.py
# for better separation and testability.
# Import above: from core.event_handlers import (handle_audit_request, handle_heresy_detection, handle_system_events)

# =============================================================================
# SYNAPTIC CONCLAVE LISTENER SETUP - MOVED TO monitoring/health.py (FASE 2 - Task 1.5 - Feb 9, 2026)
# =============================================================================
# Functions setup_synaptic_conclave_listeners() and _consume_channel() have been extracted
# to services/governance/api_orthodoxy_wardens/monitoring/health.py and imported above.

# Sacred extension components
orthodoxy_db_manager = None
orthodoxy_vector_manager = None
orthodoxy_analytics = None
divine_healing_integrator = None
sacred_guardrails = None

# =============================================================================
# SACRED INITIALIZATION & DIVINE BLESSING
# =============================================================================

@app.on_event("startup")
async def sacred_initialization():
    global confessor_agent, penitent_agent, chronicler_agent, inquisitor_agent, abbot_agent
    global llm_interface, orthodoxy_db_manager, orthodoxy_vector_manager
    global orthodoxy_analytics, divine_healing_integrator, sacred_guardrails
    
    logger.info("🏛️ Initializing the Sacred Order of Orthodoxy Wardens...")
    
    # Check for test mode
    test_mode = os.getenv("VITRUVYAN_TEST_MODE", "false").lower() == "true"
    
    try:
        # Initialize Divine LLM Interface
        llm_interface = LLMInterface()
        
        if test_mode:
            logger.warning("⚠️ RUNNING IN TEST MODE - Database and Redis connections disabled")
            # Create mock objects for testing
            postgres_agent = None
            orthodoxy_db_manager = None
            orthodoxy_vector_manager = None
            orthodoxy_analytics = None
        else:
            # Initialize Sacred PostgreSQL connection
            postgres_agent = PostgresAgent()
            
            # Initialize Orthodoxy Database Manager (✅ ENABLED 2026-02-09)
            try:
                orthodoxy_db_manager = OrthodoxyDatabaseManager()
                logger.info("✅ Orthodoxy Database Manager initialized")
            except Exception as e:
                logger.error(f"💀 Failed to initialize OrthodoxyDatabaseManager: {e}")
                orthodoxy_db_manager = None
            
            # TODO: Future implementations
            # orthodoxy_vector_manager = OrthodoxyVectorManager()
            # orthodoxy_analytics = OrthodoxyAnalytics()
            orthodoxy_vector_manager = None
            orthodoxy_analytics = None
        # TODO: Create proper theological components later
        # sacred_guardrails = SacredArchitecturalGuardrails()
        # divine_healing_integrator = DivineHealingIntegrator(orthodoxy_db_manager, sacred_guardrails)
        
        # Initialize the Sacred Divine Council (using existing agents as theological foundation)
        if test_mode:
            logger.warning("⚠️ Using mock agents for test mode")
            confessor_agent = None
            penitent_agent = None
            chronicler_agent = None
            inquisitor_agent = None
            abbot_agent = None
        else:
            confessor_agent = AutonomousAuditAgent(
                config={
                    "llm_interface": llm_interface,
                    "db_manager": orthodoxy_db_manager,
                    "role": "Sacred Confessor - Hears confessions and validates compliance"
                }
            )
            
            penitent_agent = AutoCorrector()
            
            chronicler_agent = SystemMonitor()
            
            inquisitor_agent = ComplianceValidator(llm_interface=llm_interface)
            
            abbot_agent = AutonomousAuditAgent(
                config={
                    "llm_interface": llm_interface,
                    "db_manager": orthodoxy_db_manager,
                    "role": "Sacred Abbot - Oversees sacred operations and provides divine guidance"
                }
            )
        
        # Initialize Sacred Roles (Cognitive Integration)
        global sacred_confessor, sacred_penitent, sacred_chronicler, sacred_inquisitor, sacred_abbot
        
        sacred_confessor = OrthodoxConfessor()
        sacred_penitent = OrthodoxPenitent()
        sacred_chronicler = OrthodoxChronicler()
        sacred_inquisitor = OrthodoxInquisitor()
        sacred_abbot = OrthodoxAbbot()
        
        # P1 FASE 3 (Feb 8, 2026): Inject Sacred Roles into event handlers for dependency injection
        event_handlers.inject_sacred_roles(
            confessor=sacred_confessor,
            penitent=sacred_penitent,
            chronicler=sacred_chronicler,
            inquisitor=sacred_inquisitor,
            abbot=sacred_abbot
        )
        
        # Setup Synaptic Conclave integration (async call to start background listeners)
        if not test_mode:
            await setup_synaptic_conclave_listeners()
            logger.info("🕯️ Synaptic Conclave integration activated")
        else:
            logger.warning("⚠️ Synaptic Conclave disabled in test mode")
        
        logger.info("✨ Sacred Divine Council initialized successfully")
        logger.info("🏛️ The Orthodoxy Wardens stand ready to guard sacred architecture")
        logger.info("🧠 Cognitive integration with Synaptic Conclave established")
        
    except Exception as e:
        logger.error(f"💀 Failed to initialize Sacred Council: {e}")
        raise

# =============================================================================
# SACRED API ENDPOINTS - REFACTORED TO api/routes.py (FASE 2 - Task 1.4 - Feb 9, 2026)
# =============================================================================
# All 14 endpoints have been extracted to services/governance/api_orthodoxy_wardens/api/routes.py
# and included via app.include_router(router) above.
#
# Endpoints moved:
#   - /divine-health (GET)
#   - /confession/initiate (POST)
#   - /conclave/audit-request (POST)
#   - /conclave/status (GET)
#   - /conclave/test-confession-cycle (POST)
#   - /confession/{confession_id}/status (GET)
#   - /sacred-records/recent (GET)
#   - /divine-surveillance/realm-status (GET)
#   - /sacred-healing/initiate-purification (POST)
#   - /orthodoxy/sacred-validation (GET)
#   - /orthodoxy/heresy-detection (GET)
#   - /sacred-boundaries/validate-service-sanctity (POST)
#   - /sacred-dependencies/divine-consistency-check (POST)
#   - /sacred-harmony/async-sync-conflicts (GET)

# =============================================================================
# SACRED ENTRY POINT - DIVINE PORTAL ACTIVATION
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🏛️ Activating Sacred Portal of the Orthodoxy Wardens...")
    
    # Start divine surveillance monitoring
    asyncio.create_task(divine_surveillance_monitoring())
    
    logger.info("👁️ Divine surveillance initiated - The Inquisitor's eternal watch begins")
    logger.info("🏛️ Sacred Portal listening on divine frequency 8006")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8006,
        log_level="info"
    )