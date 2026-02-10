"""
Codex Hunters - Legacy Archive
==============================

⚠️ FROZEN ARCHIVE - DO NOT MODIFY

This directory contains the pre-refactoring implementation
of Codex Hunters with finance-specific logic (yfinance, praw, etc.).

These files are preserved for:
1. Reference during domain-specific reimplementation
2. Historical documentation
3. Gradual migration of functionality

DO NOT import from this module in new code.
Use the refactored consumers in `../consumers/` instead.

Files in this archive:
- base_hunter.py: Original BaseHunter with Redis integration
- tracker.py: yfinance/praw/news data fetching
- restorer.py: yfinance-specific normalization
- binder.py: Hardcoded collection names (market_data, etc.)
- inspector.py: Finance-specific table references
- scribe.py, cartographer.py, expedition_*.py: Orchestration

Migration status: February 2026
"""

# Intentionally empty - do not add imports
# Legacy code should not be imported by new consumers
