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
- compose_node: VEE + ConversationalLLM narrative fusion
- sentiment_node: Babel Gardens sentiment analysis
- portfolio_node: Collection Guardian risk monitoring
- vault_node: Vault Keepers archival
- orthodoxy_node: Orthodoxy Wardens validation
- sentinel_node: Sentinel alerts
- crew_node: CrewAI orchestration
- codex_hunters_node: Data collection trigger

Version: 2.0.0
"""

__version__ = '2.0.0'
