"""
CI/CD integration for Update Manager.

This package provides CI gates to prevent breaking releases:
- contract_validator: Validate UPDATE_SYSTEM_CONTRACT compliance
- pytest_integration: Pytest markers and fixtures for compatibility tests
- release_blocker: Block releases based on compatibility test results
"""

from .contract_validator import ContractValidator, ValidationError, discover_verticals
from .pytest_integration import compatibility_test
from .release_blocker import ReleaseBlocker, BlockingReason

__all__ = [
    "ContractValidator",
    "ValidationError",
    "discover_verticals",
    "compatibility_test",
    "ReleaseBlocker",
    "BlockingReason",
]
