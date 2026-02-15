"""
Core middleware — shared FastAPI middleware components.

Auth middleware is opt-in: set VITRUVYAN_AUTH_ENABLED=true to activate.
"""

from core.middleware.auth import AuthMiddleware

__all__ = ["AuthMiddleware"]
