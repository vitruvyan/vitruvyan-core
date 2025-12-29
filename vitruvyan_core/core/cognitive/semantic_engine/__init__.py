"""
Semantic Engine — Cognitive Tier 1
Sacred Order: Perception (Order I)

Intent-based semantic parsing engine for user input understanding.
Extracts tickers, budget, horizon, and semantic intent from natural language.

Architecture:
- Intent Module: classify_intents, extract_horizon
- Entity Module: extract_tickers, extract_amount, extract_sector
- Retrieval Module: find_similar_phrases (Qdrant semantic search)
- Enrichment Module: enrich_entities (company name resolution)
- Routing Module: decide_strategy (intent → execution path)
- Formatting Module: clean_text (input normalization)

Dependencies:
- Foundation Tier 0: PostgresAgent (db_params), QdrantAgent
- Cognitive Tier 1: Babel Gardens (optional, for multilingual)

Main Entry Point:
- parse_user_input(text: str) -> Dict[str, Any]

Supported Languages: 84 (via Babel Gardens integration)
"""

from .semantic_engine import parse_user_input

__all__ = ["parse_user_input"]
__version__ = "2.0.0"
__sacred_order__ = "Perception (Order I)"
