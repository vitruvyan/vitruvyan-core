"""
🧠 CREWAI ORCHESTRATION FRAMEWORK
==================================
Domain-Neutral CrewAI Template for Vitruvyan Core

This module provides domain-neutral templates and infrastructure for
CrewAI multi-agent orchestration, ready to be extended for specific domains.

Architecture:
- base_tool.py: Abstract tool interface
- base_agent.py: Template agent examples
- event_bridge.py: Redis Cognitive Bus integration
- cognitive_wrapper.py: Orchestration wrapper
- logging_utils.py: PostgreSQL logging utilities

Usage Pattern:
1. Import templates from this module
2. Create domain-specific implementations in vitruvyan_core/domains/<domain>/crewai/
3. Extend BaseTool for custom domain tools
4. Use EventBridge for Redis pub/sub integration
5. Use CognitiveOrchestrator for crew execution

Example:
    from core.orchestration.crewai import BaseTool, EventBridge
    
    class LegalDocumentTool(BaseTool):
        def _run(self, input: dict) -> dict:
            # Domain-specific logic here
            pass

Author: Vitruvian Development Team
Created: 2025-12-29 - Phase 1D CrewAI Template Migration
"""

from .base_tool import BaseTool
from .logging_utils import log_to_postgres

__all__ = [
    "BaseTool",
    "log_to_postgres",
]
