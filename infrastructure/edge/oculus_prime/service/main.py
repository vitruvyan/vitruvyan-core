"""Compatibility entrypoint for Oculus Prime service.

Canonical runtime service lives in `services/api_edge_oculus_prime`.
This module is kept to avoid breaking legacy imports/commands.
"""

from services.api_edge_oculus_prime.main import app

__all__ = ["app"]
