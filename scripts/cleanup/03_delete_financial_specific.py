#!/usr/bin/env python3
"""
PHASE 3: Delete financial-specific files/folders
These are Mercator-specific and don't belong in core
"""

import os
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent

# Folders to delete (financial-specific)
FOLDERS_TO_DELETE = [
    # Codex Hunters financial backfills
    "vitruvyan_core/core/governance/codex_hunters/backfill",
    "vitruvyan_core/core/governance/codex_hunters/scripts",
    "vitruvyan_core/core/governance/codex_hunters/tests",
    
    # Neural Engine (financial-specific)
    "vitruvyan_core/core/cognitive/neural_engine",
    
    # Financial services
    "services/core/api_portfolio_guardian",
    "services/core/api_neural_engine",
]

# Files to delete (financial-specific)
FILES_TO_DELETE = [
    # Codex Hunters financial modules
    "vitruvyan_core/core/governance/codex_hunters/cassandra.py",
    "vitruvyan_core/core/governance/codex_hunters/scholastic.py",
    "vitruvyan_core/core/governance/codex_hunters/fundamentalist.py",
    
    # Financial proprietary engines (OBSOLETE: moved to core/vpar/, migrated from mercator)
    # "vitruvyan_core/core/cognitive/vitruvyan_proprietary/vare_engine.py",
    # "vitruvyan_core/core/cognitive/vitruvyan_proprietary/vhsw_engine.py",
    # "vitruvyan_core/core/cognitive/vitruvyan_proprietary/vmfl_engine.py",
    # "vitruvyan_core/core/cognitive/vitruvyan_proprietary/vwre_engine.py",
    
    # Financial LangGraph nodes
    "vitruvyan_core/core/orchestration/langgraph/node/portfolio_node.py",
    "vitruvyan_core/core/orchestration/langgraph/node/screener_node.py",
    "vitruvyan_core/core/orchestration/langgraph/node/sentiment_node.py",
    "vitruvyan_core/core/orchestration/langgraph/node/ticker_resolver_node.py",
    "vitruvyan_core/core/orchestration/langgraph/utilities/llm_ticker_extractor.py",
    
    # Financial persistence
    "vitruvyan_core/core/foundation/persistence/factor_explanations.py",
    "vitruvyan_core/core/foundation/persistence/factor_access.py",
    "vitruvyan_core/core/foundation/persistence/factor_persistence.py",
    "vitruvyan_core/core/foundation/persistence/sentiment_persistence_qdrant.py",
    "vitruvyan_core/core/foundation/persistence/sentiment_persistence.py",
    "vitruvyan_core/core/foundation/persistence/sentiment_access.py",
    "vitruvyan_core/core/foundation/persistence/trend_access.py",
    "vitruvyan_core/core/foundation/persistence/import_seed_dataset.py",
    "vitruvyan_core/core/foundation/cache/neural_cache.py",
    
    # Financial semantic modules
    "vitruvyan_core/core/cognitive/semantic_engine/semantic_modules/data/reddit_scraper.py",
]

def delete_folders():
    """Delete financial-specific folders"""
    deleted = []
    for folder in FOLDERS_TO_DELETE:
        path = REPO_ROOT / folder
        if path.exists():
            shutil.rmtree(path)
            deleted.append(folder)
            print(f"✓ Deleted folder: {folder}")
        else:
            print(f"- Folder not found: {folder}")
    return deleted

def delete_files():
    """Delete financial-specific files"""
    deleted = []
    for file in FILES_TO_DELETE:
        path = REPO_ROOT / file
        if path.exists():
            path.unlink()
            deleted.append(file)
            print(f"✓ Deleted file: {file}")
        else:
            print(f"- File not found: {file}")
    return deleted

def main():
    print("=" * 60)
    print("PHASE 3: DELETE FINANCIAL-SPECIFIC FILES")
    print("=" * 60)
    print()
    
    print("Deleting financial-specific folders...")
    deleted_folders = delete_folders()
    print()
    
    print("Deleting financial-specific files...")
    deleted_files = delete_files()
    print()
    
    print("=" * 60)
    print(f"SUMMARY: Deleted {len(deleted_folders)} folders, {len(deleted_files)} files")
    print("=" * 60)
    
    return len(deleted_folders) + len(deleted_files)

if __name__ == "__main__":
    main()
