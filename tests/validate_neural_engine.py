#!/usr/bin/env python3
"""
Validation script for Neural Engine Core structure.

Verifies that all required files exist and have the expected structure.
"""

import os
import sys
from pathlib import Path

def validate_structure():
    """Validate Neural Engine Core file structure."""
    
    base_path = Path(__file__).parent / "vitruvyan_core" / "core" / "cognitive" / "neural_engine"
    
    required_files = {
        "contracts.py": ["AbstractFactor", "NormalizerStrategy", "AggregationProfile"],
        "context.py": ["EvaluationContext"],
        "result.py": ["FactorContribution", "EntityEvaluation", "EvaluationResult"],
        "registry.py": ["FactorRegistry", "ProfileRegistry", "NormalizerRegistry"],
        "orchestrator.py": ["EvaluationOrchestrator"],
        "normalizers/zscore.py": ["ZScoreNormalizer"],
        "normalizers/minmax.py": ["MinMaxNormalizer"],
        "normalizers/rank.py": ["RankNormalizer"],
        "utils/math.py": ["winsorize", "time_decay", "safe_divide"],
    }
    
    print("🔍 Validating Neural Engine Core structure...\n")
    
    all_valid = True
    
    for file_path, expected_symbols in required_files.items():
        full_path = base_path / file_path
        
        if not full_path.exists():
            print(f"❌ Missing: {file_path}")
            all_valid = False
            continue
        
        # Read file content
        with open(full_path, 'r') as f:
            content = f.read()
        
        # Check for expected symbols
        missing = []
        for symbol in expected_symbols:
            if symbol not in content:
                missing.append(symbol)
        
        if missing:
            print(f"⚠️  {file_path}: missing {', '.join(missing)}")
            all_valid = False
        else:
            print(f"✅ {file_path}: {', '.join(expected_symbols)}")
    
    print("\n📊 Structure Validation:")
    
    # Count lines
    total_lines = 0
    for file_path in required_files.keys():
        full_path = base_path / file_path
        if full_path.exists():
            with open(full_path, 'r') as f:
                lines = len(f.readlines())
                total_lines += lines
    
    print(f"   Total lines (core files): {total_lines}")
    
    if total_lines < 470:
        print(f"   ⚠️  Below target of 470 lines")
    elif total_lines > 600:
        print(f"   ⚠️  Above target of 600 lines (possible overengineering)")
    else:
        print(f"   ✅ Within acceptable range (470-600 lines)")
    
    print("\n" + "="*60)
    
    if all_valid:
        print("✅ All validations passed!")
        return 0
    else:
        print("❌ Some validations failed")
        return 1


if __name__ == "__main__":
    sys.exit(validate_structure())
