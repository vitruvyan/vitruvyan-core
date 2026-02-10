"""
Legacy Archive - Pattern Weavers LIVELLO 1
==========================================

⚠️ FROZEN ARCHIVE - DO NOT MODIFY ⚠️

This directory contains pre-refactoring code that was archived during
the SACRED_ORDER_PATTERN migration in February 2026.

Files archived:
- weaver_engine.py (430 lines): Original weaving engine with Qdrant/httpx I/O
- weaver_node.py (99 lines): LangGraph node integration
- weaver_client.py (114 lines): HTTP client for API calls
- redis_listener.py (247 lines): Redis pubsub listener
- schemas.py (57 lines): Original Pydantic schemas
- schemas_old/: Original schemas directory
- config_old/: Original YAML configuration (domain-specific)

Total: ~947 lines of legacy code

Purpose: Historical reference and migration verification.
Status: Read-only, frozen, never import in production.

Migration Date: February 2026
New Structure: See parent directory (domain/, consumers/, events/, etc.)

Key changes in v2.0.0:
- Removed hardcoded finance-specific taxonomy (Banking, Healthcare, etc.)
- Taxonomy now loaded from configuration file
- Pure consumers have zero I/O dependencies
- All domain values configurable via PatternConfig
"""

__all__ = []  # Nothing should be imported from here
