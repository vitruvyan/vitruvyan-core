#!/usr/bin/env python3
"""
📝 LOGGING UTILS - DOMAIN-NEUTRAL POSTGRESQL LOGGING
===================================================
Generic PostgreSQL logging utilities for CrewAI operations

This module provides domain-neutral logging functions that work with
PostgresAgent to persist CrewAI execution events, decisions, and metrics.

Uses existing log_agent table schema:
- agent (text, NOT NULL): Agent/component name
- ticker (text, nullable): Entity identifier (domain-specific)
- payload_json (jsonb, nullable): Event details and metadata
- created_at (timestamp, NOT NULL, default now())

Usage Pattern:
    from core.orchestration.crewai import log_to_postgres
    from core.foundation.persistence.postgres_agent import PostgresAgent
    
    postgres = PostgresAgent()
    log_to_postgres(
        postgres_agent=postgres,
        agent_name="DocumentAnalyzer",
        action="contract_analyzed",
        details={"contract_id": "CTR-123", "clauses": 15}
    )

Author: Vitruvian Development Team
Created: 2025-12-29 - Migrated from domains/trade/crewai/postgres_logging_utils.py
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def log_to_postgres(
    postgres_agent: Any,
    agent_name: str,
    action: str,
    details: Dict[str, Any],
    entity_id: str = None
) -> bool:
    """
    Log CrewAI event to PostgreSQL using existing log_agent table schema
    
    Args:
        postgres_agent: Instance of PostgresAgent
        agent_name: Name of the agent/component logging
        action: Action being logged (e.g., "analysis_started")
        details: Dictionary of additional details and metadata
        entity_id: Optional entity identifier (replaces "ticker" in finance domain)
        
    Returns:
        bool: True if successful, False otherwise
        
    Example:
        log_to_postgres(
            postgres_agent=postgres,
            agent_name="RiskAnalyzer",
            action="risk_assessed",
            details={"risk_level": "medium", "score": 0.65},
            entity_id="ENTITY-123"
        )
    """
    # Validate agent_name is not None or empty
    if not agent_name or agent_name.strip() == "":
        logger.error(f"❌ agent_name is None or empty! action={action}")
        return False
    
    try:
        # Build payload with action and all details
        payload = {
            "action": action,
            **(details or {})
        }
        
        with postgres_agent.connection.cursor() as cur:
            # Insert using existing log_agent schema
            # Note: "ticker" column used generically for entity_id
            cur.execute("""
                INSERT INTO log_agent (agent, ticker, payload_json)
                VALUES (%s, %s, %s::jsonb)
            """, (
                agent_name.strip(),
                entity_id,
                json.dumps(payload)
            ))
        
        postgres_agent.connection.commit()
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ PostgreSQL log failed ({agent_name}/{action}): {e}")
        try:
            postgres_agent.connection.rollback()
        except:
            pass
        return False


def extend_postgres_agent():
    """
    Extend PostgresAgent class with log_agent_execution method
    
    This function patches PostgresAgent to add the log_agent_execution
    method used by legacy CrewAI code. Call this on module import.
    
    Note: Only needed for backward compatibility with existing code.
    New code should use log_to_postgres() directly.
    """
    try:
        from core.foundation.persistence.postgres_agent import PostgresAgent
        
        def log_agent_execution(self, agent_name: str, action: str, details: Dict[str, Any]) -> bool:
            """Log agent execution event (backward compatibility wrapper)"""
            return log_to_postgres(self, agent_name, action, details)
        
        # Add method to PostgresAgent class
        if not hasattr(PostgresAgent, 'log_agent_execution'):
            PostgresAgent.log_agent_execution = log_agent_execution
            logger.info("✅ PostgresAgent extended with log_agent_execution method")
    except ImportError:
        logger.warning("⚠️ Could not import PostgresAgent for patching")
    except Exception as e:
        logger.warning(f"⚠️ Failed to extend PostgresAgent: {e}")


# Auto-apply patch when module is imported (backward compatibility)
extend_postgres_agent()
