"""
Compatibility namespace for Oculus Prime modules.

Canonical location:
    infrastructure/edge/oculus_prime

This shim enables imports such as `oculus_prime.core...`.
"""

from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_EDGE_OCULUS_PRIME = _ROOT.parent / "infrastructure" / "edge" / "oculus_prime"

if _EDGE_OCULUS_PRIME.exists():
    __path__.append(str(_EDGE_OCULUS_PRIME))  # type: ignore[name-defined]
