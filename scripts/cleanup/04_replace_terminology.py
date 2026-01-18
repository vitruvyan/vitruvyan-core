#!/usr/bin/env python3
"""
PHASE 4: Replace financial terminology with domain-agnostic terms
Uses regex for safe string replacement (not AST - too complex for this)
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).parent.parent.parent

# Terminology mapping (ORDER MATTERS - longer patterns first)
REPLACEMENTS: Dict[str, str] = {
    # === COMPOUND VARIABLE/FUNCTION NAMES (before simple words) ===
    # Longer patterns MUST come first
    r'_extract_tickers_from_ne_output': '_extract_entities_from_output',
    r'_extract_ticker_from_vague_query': '_extract_entity_from_vague_query',
    r'_is_valid_ticker': '_is_valid_entity',
    r'invalidate_cache_for_tickers': 'invalidate_cache_for_entities',
    r'get_active_tickers': 'get_active_entities',
    r'explain_ticker': 'explain_entity',
    r'ticker_disambiguation': 'entity_disambiguation',
    r'ticker_validation': 'entity_validation',
    r'ticker_choice': 'entity_choice',
    r'at_risk_tickers': 'at_risk_entities',
    r'extracted_tickers': 'extracted_entities',
    r'top_tickers': 'top_entities',
    r'tickers_list': 'entities_list',
    r'ticker_names': 'entity_names',
    r'ticker_vee': 'entity_vee',
    r'has_ticker': 'has_entity',
    r'has_tickers': 'has_entities',
    r'current_ticker': 'current_entity',
    r'current_tickers': 'current_entities',
    r'context_tickers': 'context_entities',
    r'validated_tickers': 'validated_entities',
    r'for_ticker': 'for_entity',
    r'single_ticker': 'single_entity',
    r'multi_ticker': 'multi_entity',
    r'ticker_data': 'entity_data',
    r'ticker_str': 'entity_str',
    r'ticker_context': 'entity_context',
    r'ticker_resolver': 'entity_resolver',
    r'ticker_node': 'entity_node',
    
    # === SIMPLE WORD BOUNDARIES (after compounds) ===
    r'\bticker\b': 'entity_id',
    r'\btickers\b': 'entity_ids',
    r'\bTicker\b': 'EntityId',
    r'\bTickers\b': 'EntityIds',
    r'\bTICKER\b': 'ENTITY_ID',
    r'\bTICKERS\b': 'ENTITY_IDS',
    
    # Stock -> Entity (careful with word boundaries)
    r'\bstock\b': 'entity',
    r'\bStock\b': 'Entity',
    r'\bSTOCK\b': 'ENTITY',
    r'\bstocks\b': 'entities',
    r'\bStocks\b': 'Entities',
    
    # Portfolio -> Collection
    r'\bportfolio\b': 'collection',
    r'\bPortfolio\b': 'Collection',
    r'\bPORTFOLIO\b': 'COLLECTION',
    r'\bportfolios\b': 'collections',
    
    # Example tickers -> generic
    r'"AAPL"': '"EXAMPLE_ENTITY_1"',
    r"'AAPL'": "'EXAMPLE_ENTITY_1'",
    r'"NVDA"': '"EXAMPLE_ENTITY_2"',
    r"'NVDA'": "'EXAMPLE_ENTITY_2'",
    r'"TSLA"': '"EXAMPLE_ENTITY_3"',
    r"'TSLA'": "'EXAMPLE_ENTITY_3'",
    r'"MSFT"': '"EXAMPLE_ENTITY_4"',
    r"'MSFT'": "'EXAMPLE_ENTITY_4'",
    r'"GOOGL"': '"EXAMPLE_ENTITY_5"',
    r"'GOOGL'": "'EXAMPLE_ENTITY_5'",
}

# File extensions to process
EXTENSIONS = {'.py', '.yaml', '.yml', '.json', '.md'}

# Directories to skip
SKIP_DIRS = {
    '.git', 
    '__pycache__', 
    'node_modules', 
    '.venv', 
    'venv',
    'cleanup',  # Don't modify cleanup scripts themselves
}

# Files to skip
SKIP_FILES = {
    'CLEANUP_AUDIT_JAN18.md',  # Audit doc should keep original terms
    'TECHNICAL_DEBT_AUDIT.md',
    'CREWAI_DEPRECATION_PLAN.md',
}

def should_process_file(path: Path) -> bool:
    """Check if file should be processed"""
    # Skip non-matching extensions
    if path.suffix not in EXTENSIONS:
        return False
    
    # Skip specific files
    if path.name in SKIP_FILES:
        return False
    
    # Skip directories
    for skip_dir in SKIP_DIRS:
        if skip_dir in path.parts:
            return False
    
    return True

def replace_in_file(file_path: Path) -> Tuple[bool, int]:
    """
    Replace financial terms in a file.
    Returns (modified, replacements_count)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  ! Error reading {file_path}: {e}")
        return False, 0
    
    original_content = content
    total_replacements = 0
    
    for pattern, replacement in REPLACEMENTS.items():
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0:
            content = new_content
            total_replacements += count
    
    if total_replacements > 0:
        try:
            file_path.write_text(content, encoding='utf-8')
            return True, total_replacements
        except Exception as e:
            print(f"  ! Error writing {file_path}: {e}")
            return False, 0
    
    return False, 0

def find_all_files() -> List[Path]:
    """Find all files to process"""
    files = []
    for root, dirs, filenames in os.walk(REPO_ROOT):
        # Skip directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for filename in filenames:
            file_path = Path(root) / filename
            if should_process_file(file_path):
                files.append(file_path)
    
    return files

def main():
    print("=" * 60)
    print("PHASE 4: REPLACE FINANCIAL TERMINOLOGY")
    print("=" * 60)
    print()
    
    print("Terminology mapping:")
    for old, new in list(REPLACEMENTS.items())[:10]:
        print(f"  {old} → {new}")
    print(f"  ... and {len(REPLACEMENTS) - 10} more")
    print()
    
    files = find_all_files()
    print(f"Found {len(files)} files to scan")
    print()
    
    modified_files = []
    total_replacements = 0
    
    for file_path in files:
        modified, count = replace_in_file(file_path)
        if modified:
            rel_path = file_path.relative_to(REPO_ROOT)
            modified_files.append((rel_path, count))
            total_replacements += count
    
    print("Modified files:")
    for rel_path, count in modified_files:
        print(f"  ✓ {rel_path} ({count} replacements)")
    
    print()
    print("=" * 60)
    print(f"SUMMARY: Modified {len(modified_files)} files, {total_replacements} total replacements")
    print("=" * 60)
    
    return len(modified_files)

if __name__ == "__main__":
    main()
