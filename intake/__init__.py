"""
Compatibility namespace for Intake modules.

Canonical location:
    infrastructure/edge/intake

This shim keeps legacy imports (e.g. `intake.core...`) operational
after relocating the intake module under infrastructure/edge.
"""

from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_EDGE_INTAKE = _ROOT.parent / "infrastructure" / "edge" / "intake"

if _EDGE_INTAKE.exists():
    __path__.append(str(_EDGE_INTAKE))  # type: ignore[name-defined]

