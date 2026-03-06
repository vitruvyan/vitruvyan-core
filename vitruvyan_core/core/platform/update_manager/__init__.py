"""
Vitruvyan Core Update Manager

Industry-standard update system for Core + Verticals (apt/pip/dnf pattern).

Architecture:
- engine/: Business logic (compatibility, planning, execution)
- cli/: User interface (vit command)
- tests/: Unit + functional tests

Usage (Library):
    from core.platform.update_manager.engine import UpdateEngine
    
    engine = UpdateEngine()
    result = engine.check_compatibility()
    if result.is_compatible:
        plan = engine.plan_upgrade("1.2.0")
        engine.apply_upgrade(plan)

Usage (CLI):
    $ vit update
    $ vit upgrade
    $ vit rollback

Contract: docs/contracts/platform/UPDATE_SYSTEM_CONTRACT_V1.md
"""

from .engine import UpdateEngine

__version__ = "0.1.0"
__all__ = ["UpdateEngine", "cli_main"]


def cli_main():
    """
    Lazy CLI entrypoint import.

    Keeps package-level imports safe for library/CI callers even if CLI-only
    modules are temporarily unavailable.
    """
    from .cli.main import cli_main as _cli_main

    return _cli_main()
