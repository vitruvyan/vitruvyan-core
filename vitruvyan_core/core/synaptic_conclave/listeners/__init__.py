"""
🗝️ Synaptic Conclave Listeners
================================
Sacred listeners for Divine Synaptic Conclave events

This package contains business logic for all Sacred Order listeners.
Each listener handles domain-specific events from the Synaptic Conclave.

Architecture Principle:
-----------------------
Business logic lives HERE (synaptic_conclave/listeners/), NOT in docker/services/.
Docker services contain only thin entrypoints (<50 lines) that:
1. Import listener from this package
2. Wrap with ListenerAdapter (for legacy listeners)
3. Start async loop

Migration Date: February 5-6, 2026
Rationale: Separation of concerns - docker for deployment, synaptic_conclave for code.

Listeners:
----------
- LangGraphStreamsListener: Collection monitoring workflows (native streams)
"""

# ⚠️ NO CENTRALIZED IMPORTS - Prevents transitive dependency issues
# Each entrypoint imports directly: from vitruvyan_core.core.synaptic_conclave.listeners.codex_hunters import ...
# This avoids loading all listener dependencies (e.g., aiohttp) when only one listener is needed.

# Available listeners (import directly from submodules):
# - langgraph.LangGraphStreamsListener

__all__ = ["LangGraphStreamsListener"]
