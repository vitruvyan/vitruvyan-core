"""
Update Manager CLI (User Interface)

Command-line interface for `vit` command.

Components:
- main.py: Entry point (argparse/click)
- commands/: Command implementations (update, upgrade, plan, rollback)
- formatters.py: Output formatting (tables, colors, JSON)
"""

from .main import cli_main

__all__ = ["cli_main"]
