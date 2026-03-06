"""
Update Manager CLI (User Interface)

Command-line interface for `vit` command.

Components:
- main.py: Entry point (argparse/click)
- commands/: Command implementations (update, upgrade, plan, rollback)
- formatters.py: Output formatting (tables, colors, JSON)
"""

__all__ = ["cli_main"]


def cli_main():
    """Lazy import to avoid runpy double-import warnings."""
    from .main import cli_main as _cli_main

    return _cli_main()
