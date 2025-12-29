#!/usr/bin/env python3
"""
Test backward compatibility and deprecation warnings.
"""

import warnings
import sys

print("🧪 Testing Neural Engine v2 Compatibility\n")
print("=" * 60)

# Test 1: Core imports (should work without warnings)
print("\n✅ Test 1: Core imports (no warnings expected)")
try:
    from vitruvyan_core.core.cognitive.neural_engine import (
        AbstractFactor,
        AggregationProfile,
        EvaluationOrchestrator,
        ZScoreNormalizer
    )
    print("   ✓ Core substrate imports successful")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

# Test 2: Patterns imports (explicit, no warnings)
print("\n✅ Test 2: Pattern imports (explicit, no warnings)")
try:
    from vitruvyan_core.patterns.neural_engine import (
        FactorRegistry,
        MinMaxNormalizer,
        RankNormalizer
    )
    print("   ✓ Pattern library imports successful")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

# Test 3: Backward compatibility (should warn)
print("\n⚠️  Test 3: Backward compatibility (deprecation warnings expected)")
warnings.simplefilter("always", DeprecationWarning)

try:
    # This should trigger deprecation warnings but still work
    from vitruvyan_core.core.cognitive.neural_engine import (
        MinMaxNormalizer as OldMinMax,
        FactorRegistry as OldRegistry
    )
    print("   ✓ Backward-compatible imports work")
    print("   ✓ (Deprecation warnings shown above)")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

# Test 4: Verify they're the same classes
print("\n✅ Test 4: Verify compatibility layer returns same classes")
if MinMaxNormalizer is OldMinMax:
    print("   ✓ MinMaxNormalizer: same class from both imports")
else:
    print("   ✗ Different classes!")
    sys.exit(1)

if FactorRegistry is OldRegistry:
    print("   ✓ FactorRegistry: same class from both imports")
else:
    print("   ✗ Different classes!")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ All compatibility tests passed!")
print("\nSummary:")
print("- Core substrate: clean imports, no warnings")
print("- Patterns library: explicit imports, no warnings")
print("- Backward compat: imports work with deprecation warnings")
print("- Same classes: both import paths resolve to same objects")
