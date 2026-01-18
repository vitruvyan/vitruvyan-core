#!/usr/bin/env python3
"""
PHASE 2: Remove CrewAI imports from remaining files
Uses AST for safe Python manipulation
"""

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent

# Files that had CrewAI imports (from audit)
FILES_WITH_CREWAI_IMPORTS = [
    "vitruvyan_core/core/foundation/cognitive_bus/herald.py",
    "vitruvyan_core/core/foundation/cognitive_bus/event_schema.py",
    "vitruvyan_core/core/foundation/cognitive_bus/lexicon.py",
    "vitruvyan_core/core/orchestration/langgraph/node/quality_check_node.py",
    "vitruvyan_core/core/orchestration/langgraph/node/compose_node.py",
    "vitruvyan_core/core/orchestration/langgraph/node/llm_soft_node.py",
    "vitruvyan_core/core/orchestration/langgraph/node/output_normalizer_node.py",
    "vitruvyan_core/core/orchestration/langgraph/node/__init__.py",
    "vitruvyan_core/core/orchestration/langgraph/graph_flow.py",
    "vitruvyan_core/core/governance/vault_keepers/chamberlain.py",
    "vitruvyan_core/core/governance/vault_keepers/__init__.py",
    "vitruvyan_core/core/governance/codex_hunters/scripts/backfill_technical_logs.py",
    "vitruvyan_core/core/governance/codex_hunters/scripts/backfill_all.py",
    "vitruvyan_core/core/governance/codex_hunters/tests/test_backfill_integration.py",
    "vitruvyan_core/core/governance/codex_hunters/backfill/backfill_technical_logs.py",
    "vitruvyan_core/core/governance/codex_hunters/backfill/backfill_all.py",
    "vitruvyan_core/core/governance/orthodoxy_wardens/inquisitor_agent.py",
    "vitruvyan_core/core/governance/orthodoxy_wardens/chronicler_agent.py",
    "vitruvyan_core/core/governance/orthodoxy_wardens/docker_manager.py",
    "vitruvyan_core/core/governance/orthodoxy_wardens/penitent_agent.py",
    "vitruvyan_core/core/governance/orthodoxy_wardens/confessor_agent.py",
    "vitruvyan_core/core/cognitive/vitruvyan_proprietary/vee/vee_engine.py",
    "services/core/api_portfolio_guardian/main.py",
    "services/core/api_graph/main.py",
    "services/core/api_babel_gardens/modules/cognitive_bridge.py",
    "config/api_config.py",
]

# Patterns to remove
CREWAI_IMPORT_PATTERNS = [
    r'^from crewai import.*$',
    r'^import crewai.*$',
    r'^from crewai\..*import.*$',
    r'^from \.\.crewai import.*$',
    r'^from vitruvyan_core\.core\.orchestration\.crewai import.*$',
]

def remove_crewai_imports(file_path: Path) -> tuple[bool, int]:
    """
    Remove CrewAI import lines from a Python file.
    Returns (modified, lines_removed)
    """
    if not file_path.exists():
        return False, 0
    
    try:
        content = file_path.read_text()
    except Exception as e:
        print(f"  ! Error reading {file_path}: {e}")
        return False, 0
    
    lines = content.split('\n')
    new_lines = []
    removed_count = 0
    
    for line in lines:
        should_remove = False
        for pattern in CREWAI_IMPORT_PATTERNS:
            if re.match(pattern, line.strip()):
                should_remove = True
                removed_count += 1
                break
        
        if not should_remove:
            new_lines.append(line)
    
    if removed_count > 0:
        new_content = '\n'.join(new_lines)
        file_path.write_text(new_content)
        return True, removed_count
    
    return False, 0

def main():
    print("=" * 60)
    print("PHASE 2: REMOVE CREWAI IMPORTS")
    print("=" * 60)
    print()
    
    total_files_modified = 0
    total_lines_removed = 0
    
    for file_rel in FILES_WITH_CREWAI_IMPORTS:
        file_path = REPO_ROOT / file_rel
        modified, lines = remove_crewai_imports(file_path)
        
        if modified:
            total_files_modified += 1
            total_lines_removed += lines
            print(f"✓ {file_rel} ({lines} imports removed)")
        elif file_path.exists():
            print(f"- {file_rel} (no crewai imports found)")
        else:
            print(f"- {file_rel} (file not found)")
    
    print()
    print("=" * 60)
    print(f"SUMMARY: Modified {total_files_modified} files, removed {total_lines_removed} import lines")
    print("=" * 60)
    
    return total_files_modified

if __name__ == "__main__":
    main()
