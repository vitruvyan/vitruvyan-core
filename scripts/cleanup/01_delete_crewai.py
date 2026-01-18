#!/usr/bin/env python3
"""
PHASE 1: Delete CrewAI completely
No replacement needed - LangGraph + Docker services = sufficient
"""

import os
import shutil
from pathlib import Path

# Repository root
REPO_ROOT = Path(__file__).parent.parent.parent

# Folders to delete entirely
FOLDERS_TO_DELETE = [
    "vitruvyan_core/core/orchestration/crewai",
    "services/core/api_crewai",
]

# Files to delete
FILES_TO_DELETE = [
    "vitruvyan_core/core/governance/vault_keepers/chamberlain_crewai_backup.py",
    "vitruvyan_core/core/orchestration/langgraph/node/crew_node.py",
]

def delete_folders():
    """Delete CrewAI folders"""
    deleted = []
    for folder in FOLDERS_TO_DELETE:
        path = REPO_ROOT / folder
        if path.exists():
            shutil.rmtree(path)
            deleted.append(str(path))
            print(f"✓ Deleted folder: {folder}")
        else:
            print(f"- Folder not found (already deleted?): {folder}")
    return deleted

def delete_files():
    """Delete CrewAI-specific files"""
    deleted = []
    for file in FILES_TO_DELETE:
        path = REPO_ROOT / file
        if path.exists():
            path.unlink()
            deleted.append(str(path))
            print(f"✓ Deleted file: {file}")
        else:
            print(f"- File not found (already deleted?): {file}")
    return deleted

def main():
    print("=" * 60)
    print("PHASE 1: DELETE CREWAI")
    print("=" * 60)
    print()
    
    print("Deleting folders...")
    deleted_folders = delete_folders()
    print()
    
    print("Deleting files...")
    deleted_files = delete_files()
    print()
    
    print("=" * 60)
    print(f"SUMMARY: Deleted {len(deleted_folders)} folders, {len(deleted_files)} files")
    print("=" * 60)
    
    return len(deleted_folders) + len(deleted_files)

if __name__ == "__main__":
    main()
