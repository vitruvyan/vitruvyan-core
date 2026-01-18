#!/usr/bin/env python3
"""
CLEANUP ORCHESTRATOR
Runs all cleanup phases in sequence with confirmation
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent

PHASES = [
    ("01_delete_crewai.py", "Delete CrewAI completely"),
    ("02_remove_crewai_imports.py", "Remove CrewAI imports from files"),
    ("03_delete_financial_specific.py", "Delete financial-specific files"),
    ("04_replace_terminology.py", "Replace financial terminology"),
]

def run_phase(script_name: str, description: str, dry_run: bool = False) -> bool:
    """Run a cleanup phase"""
    script_path = SCRIPTS_DIR / script_name
    
    if not script_path.exists():
        print(f"✗ Script not found: {script_name}")
        return False
    
    print(f"\n{'='*60}")
    print(f"PHASE: {description}")
    print(f"Script: {script_name}")
    print(f"{'='*60}\n")
    
    if dry_run:
        print("[DRY RUN] Would execute this phase")
        return True
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=SCRIPTS_DIR.parent.parent,  # repo root
            capture_output=False,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"✗ Error running {script_name}: {e}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Vitruvyan-Core Cleanup Orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without doing it")
    parser.add_argument("--phase", type=int, help="Run only specific phase (1-4)")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompts")
    args = parser.parse_args()
    
    print("=" * 60)
    print("VITRUVYAN-CORE CLEANUP ORCHESTRATOR")
    print("=" * 60)
    print()
    print("This will clean the repository by:")
    print("  1. Deleting CrewAI completely")
    print("  2. Removing CrewAI imports from remaining files")
    print("  3. Deleting financial-specific files (Mercator)")
    print("  4. Replacing financial terminology (ticker→entity_id, etc.)")
    print()
    
    if args.dry_run:
        print("*** DRY RUN MODE - No changes will be made ***")
        print()
    
    if not args.yes and not args.dry_run:
        confirm = input("Proceed? [y/N] ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            return 1
    
    # Run phases
    phases_to_run = PHASES
    if args.phase:
        if 1 <= args.phase <= len(PHASES):
            phases_to_run = [PHASES[args.phase - 1]]
        else:
            print(f"Invalid phase: {args.phase}. Must be 1-{len(PHASES)}")
            return 1
    
    success_count = 0
    for script_name, description in phases_to_run:
        if run_phase(script_name, description, dry_run=args.dry_run):
            success_count += 1
    
    print()
    print("=" * 60)
    print(f"CLEANUP COMPLETE: {success_count}/{len(phases_to_run)} phases successful")
    print("=" * 60)
    print()
    print("NEXT STEPS:")
    print("  1. Review changes: git diff")
    print("  2. Run tests: pytest")
    print("  3. Use Grok for remaining 20-30% (edge cases, decisions)")
    print("  4. Commit: git add -A && git commit -m 'chore: Core cleanup'")
    
    return 0 if success_count == len(phases_to_run) else 1

if __name__ == "__main__":
    sys.exit(main())
