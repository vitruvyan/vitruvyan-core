"""
CI/CD integration for Update Manager.

This package provides CI gates to prevent breaking releases:
- contract_validator: Validate UPDATE_SYSTEM_CONTRACT compliance
- pytest_integration: Pytest markers and fixtures for compatibility tests
- release_blocker: Block releases based on compatibility test results
"""

from .contract_validator import ContractValidator, ValidationError, discover_verticals
from .pytest_integration import compatibility_test

__all__ = [
    "ContractValidator",
    "ValidationError",
    "discover_verticals",
    "compatibility_test",
    "ReleaseBlocker",
    "BlockingReason",
]


def __getattr__(name):
    """Lazy-load heavy modules to avoid runpy duplicate-import warnings."""
    if name in {"ReleaseBlocker", "BlockingReason"}:
        from .release_blocker import ReleaseBlocker, BlockingReason

        return {"ReleaseBlocker": ReleaseBlocker, "BlockingReason": BlockingReason}[name]
    raise AttributeError(name)
