"""
🏛️ Orthodoxy Wardens - Sacred Workflows
Orchestration logic for confession, purification, and surveillance workflows.

Extracted from main.py (FASE 2 - Feb 9, 2026)
"""

import logging
import asyncio
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger("OrthodoxyWardens.Workflows")

# Global references to sacred agents (initialized in monitoring/health.py)
confessor_agent = None
penitent_agent = None
chronicler_agent = None
inquisitor_agent = None
orthodoxy_db_manager = None


def set_agents(confessor, penitent, chronicler, inquisitor, db_manager):
    """Initialize global agent references (called from startup)"""
    global confessor_agent, penitent_agent, chronicler_agent, inquisitor_agent, orthodoxy_db_manager
    confessor_agent = confessor
    penitent_agent = penitent
    chronicler_agent = chronicler
    inquisitor_agent = inquisitor
    orthodoxy_db_manager = db_manager


async def run_confession_workflow(confession_state: Dict):
    """🏛️ Run complete sacred confession workflow with divine judgment"""
    
    try:
        logger.info(f"🏛️ Beginning sacred confession: {confession_state['confession_id']}")
        
        # Update status in sacred database
        await orthodoxy_db_manager.update_confession_status(
            confession_state['confession_id'], 
            "confessing", 
            divine_results={"confession_started_at": datetime.now().isoformat()}
        )
        
        # Confessor hears the confession
        confession_results = await confessor_agent.hear_system_confession(confession_state)
        
        # If sins are found, assign to Penitent for purification
        if confession_results.get("requires_penance", False):
            confession_state["assigned_warden"] = "penitent"
            confession_state["sacred_status"] = "penance_assigned"
            
            # Penitent performs purification rituals
            penance_results = await penitent_agent.perform_penance_rituals(confession_state)
            confession_results.update(penance_results)
        
        # Chronicler records the sacred events
        await chronicler_agent.record_sacred_confession(confession_state, confession_results)
        
        # Save final sacred results
        await orthodoxy_db_manager.update_confession_status(
            confession_state['confession_id'],
            "absolution_granted" if confession_results.get("absolved", False) else "penance_required",
            divine_results={
                "confession_completed_at": datetime.now().isoformat(),
                "divine_results": confession_results
            }
        )
        
        logger.info(f"✨ Sacred confession completed: {confession_state['confession_id']}")
        
    except Exception as e:
        logger.error(f"💀 Sacred confession failed: {e}")
        
        # Update status as divine judgment failed
        await orthodoxy_db_manager.update_confession_status(
            confession_state['confession_id'],
            "divine_judgment_failed", 
            divine_results={
                "confession_completed_at": datetime.now().isoformat(),
                "sacred_error": str(e)
            }
        )


async def run_purification_ritual(purification_state: Dict):
    """✨ Run sacred purification ritual - Penitent cleanses system sins"""
    
    try:
        logger.info(f"✨ Beginning sacred purification: {purification_state['purification_id']}")
        
        # Penitent performs system purification
        purification_results = await penitent_agent.perform_system_purification(purification_state)
        
        # Chronicler records the sacred ritual
        await chronicler_agent.record_purification_ritual(purification_state, purification_results)
        
        logger.info(f"✨ Sacred purification completed: {purification_results}")
        
    except Exception as e:
        logger.error(f"💀 Sacred purification failed: {e}")


async def divine_surveillance_monitoring():
    """👁️ Divine surveillance task - Inquisitor's eternal watch"""
    
    while True:
        try:
            # Wait for divine surveillance interval
            await asyncio.sleep(600)  # 10 minutes - The divine eye sees all
            
            # Trigger scheduled divine inspection
            scheduled_confession = {
                "confession_id": f"divine_inspection_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "confession_type": "scheduled_divine_inspection",
                "sacred_scope": "complete_realm",
                "urgency": "divine_routine",
                "confession_results": {},
                "orthodoxy_score": 0.0,
                "penance_actions": [],
                "purification_rituals": [],
                "divine_insights": {},
                "sacred_notifications": [],
                "status": "confessing",
                "assigned_warden": "inquisitor"
            }
            
            # Run scheduled divine confession
            await run_confession_workflow(scheduled_confession)
            
            logger.info("👁️ Divine surveillance completed - The sacred realm has been inspected")
            
        except Exception as e:
            logger.error(f"💀 Divine surveillance error: {e}")
