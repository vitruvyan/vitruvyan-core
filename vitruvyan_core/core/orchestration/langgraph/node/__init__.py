"""
vitruvyan_os.core.orchestration.langgraph.node
===============================================

LangGraph Execution Nodes

This package contains 31 execution nodes that form the LangGraph state machine.
Each node performs a specific task in the conversational workflow.

Key Nodes:
----------
- intent_detection_node: GPT-3.5 + Babel sentiment + regex cascade
- entity_resolver_node: Nuclear Option LLM entity_id extraction (95% accuracy)
- exec_node: Neural Engine execution router
- compose_node: Response narrative composition
- emotion_detector: Babel Gardens emotion detection
- can_node: Conversational Autonomous Navigator
- vault_node: Vault Keepers archival
- orthodoxy_node: Orthodoxy Wardens validation
- codex_hunters_node: Data collection trigger

Version: 3.0.0 (Feb 14, 2026)
"""

__version__ = '3.0.0'
