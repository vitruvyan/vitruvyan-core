"""
Update Manager Engine (Business Logic)

Pure library code. Zero I/O (console/network handled by CLI layer).
Testable with pytest (no Docker/Redis/Postgres dependencies).

Components:
- registry.py: GitHub Releases API client
- compatibility.py: Version validation (SemVer, manifest parsing)
- planner.py: Upgrade plan generation
- executor.py: Apply/rollback execution
- models.py: Data structures (Release, Plan, Result)
"""

from .registry import ReleaseRegistry
from .compatibility import CompatibilityChecker
from .planner import UpgradePlanner
from .executor import UpgradeExecutor
from .models import Release, CompatibilityResult, UpgradePlan

__all__ = [
    "ReleaseRegistry",
    "CompatibilityChecker",
    "UpgradePlanner",
    "UpgradeExecutor",
    "Release",
    "CompatibilityResult",
    "UpgradePlan",
]


class UpdateEngine:
    """
    Facade for update operations (library API).
    
    Example:
        engine = UpdateEngine()
        result = engine.check_compatibility()
        if result.is_compatible:
            plan = engine.plan_upgrade("1.2.0")
            engine.apply_upgrade(plan)
    """
    
    def __init__(self):
        self.registry = ReleaseRegistry()
        self.compatibility = CompatibilityChecker()
        self.planner = UpgradePlanner()
        self.executor = UpgradeExecutor()
    
    def check_compatibility(self):
        """Check if upgrade is possible (read-only)."""
        raise NotImplementedError("Phase 1 implementation")
    
    def plan_upgrade(self, target_version: str):
        """Generate upgrade plan."""
        raise NotImplementedError("Phase 2 implementation")
    
    def apply_upgrade(self, plan):
        """Execute upgrade (with rollback on failure)."""
        raise NotImplementedError("Phase 2 implementation")
    
    def rollback(self):
        """Revert to previous version."""
        raise NotImplementedError("Phase 2 implementation")
