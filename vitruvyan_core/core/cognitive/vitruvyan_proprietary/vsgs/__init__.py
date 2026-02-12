"""
VSGS — Vitruvyan Semantic Grounding System

Proprietary semantic context enrichment engine.
Embedding generation → Qdrant semantic search → State enrichment → Audit logging.

Components:
    - vsgs_engine.py:   Core logic (embed, search, enrich)
    - vsgs_metrics.py:  Prometheus metric definitions
    - vsgs_sync.py:     PostgreSQL ↔ Qdrant synchronization

Architecture:
    LIVELLO 1 (Pure domain): This module
    LIVELLO 2 (Adapter):     orchestration/langgraph/node/semantic_grounding_node.py

Status: ACTIVE — Production since Nov 2025
"""

__all__ = []

__version__ = "1.0.0"
__author__ = "Vitruvyan AI Team"
