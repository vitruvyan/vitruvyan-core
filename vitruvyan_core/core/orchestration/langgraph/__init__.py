"""
vitruvyan_os.core.orchestration.langgraph
==========================================

Sacred Order: Orchestration (Order II)
Tier: 2 - Orchestration Layer

LangGraph-based conversational workflow orchestration for Vitruvyan AI Trading Advisor.

Architecture:
-------------
This module implements the LangGraph state machine that orchestrates all conversational
flows, intent detection, execution routing, and response composition.

Components:
-----------
- graph_flow.py: StateGraph definition with 25+ nodes
- graph_runner.py: Graph execution engine (run_graph, run_graph_once)
- node/: 31 execution nodes (intent_detection, exec, compose, sentiment, etc)
- memory/: Conversation context management
- shared/: State preservation utilities

Key Nodes:
----------
- intent_detection_node: LLM-first intent classification
- entity_resolver_node: Nuclear Option LLM entity_id extraction
- exec_node: Neural Engine execution orchestrator
- compose_node: VEE + LLM narrative fusion
- sentiment_node: Babel Gardens sentiment analysis
- portfolio_node: Collection Guardian integration
- vault_node: Vault Keepers archival
- orthodoxy_node: Orthodoxy Wardens validation

Dependencies:
-------------
- Foundation Tier 0: persistence, cognitive_bus, llm, cache
- Cognitive Tier 1: babel_gardens, semantic_engine

Version: 2.0.0
Migrated: Day 4 (vitruvyan-os)
"""

from .graph_flow import build_graph
from .graph_runner import run_graph, run_graph_once
from .memory import merge_slots

__all__ = [
    'build_graph',
    'run_graph',
    'run_graph_once',
    'merge_slots',
]

__version__ = '2.0.0'
__sacred_order__ = 'Orchestration (Order II)'
__tier__ = 2
