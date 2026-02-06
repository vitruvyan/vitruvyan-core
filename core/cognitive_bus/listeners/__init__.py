"""
🗝️ Cognitive Bus Listeners
==========================
Sacred listeners for Divine Cognitive Bus events

This package contains business logic for all Sacred Order listeners.
Each listener handles domain-specific events from the cognitive bus.

Architecture Principle:
-----------------------
Business logic lives HERE (cognitive_bus/listeners/), NOT in docker/services/.
Docker services contain only thin entrypoints (<50 lines) that:
1. Import listener from this package
2. Wrap with ListenerAdapter (for legacy listeners)
3. Start async loop

Migration Date: February 5, 2026
Rationale: Separation of concerns - docker for deployment, cognitive_bus for code.

Listeners:
----------
- CodexHuntersCognitiveBusListener: Data collection expeditions
- BabelGardensCognitiveBusListener: Multilingual sentiment/emotion analysis
- ShadowTradersCognitiveBusListener: Shadow trading execution
- VaultKeepersCognitiveBusListener: Knowledge preservation and versioning
- MCPListener: Model Context Protocol bridge
- LangGraphStreamsListener: Portfolio monitoring workflows (native streams)
"""

# ⚠️ NO CENTRALIZED IMPORTS - Prevents transitive dependency issues
# Each entrypoint imports directly: from core.cognitive_bus.listeners.codex_hunters import ...
# This avoids loading all listener dependencies (e.g., aiohttp) when only one listener is needed.

# Available listeners (import directly from submodules):
# - codex_hunters.CodexHuntersCognitiveBusListener
# - babel_gardens.BabelGardensCognitiveBusListener
# - shadow_traders.ShadowTradersCognitiveBusListener
# - vault_keepers.VaultKeepersCognitiveBusListener
# - mcp.MCPListener
# - langgraph.LangGraphStreamsListener

__all__ = [
    'CodexHuntersCognitiveBusListener',
    'BabelGardensCognitiveBusListener',
    'ShadowTradersCognitiveBusListener',
    'VaultKeepersCognitiveBusListener',
    'MCPListener',
    'LangGraphStreamsListener',
]
