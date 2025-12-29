"""
LEO — Foundation Tier 0
Database & Vector Store Agents (PostgreSQL + Qdrant + Alembic)

CRITICAL: 12 service imports depend on PostgresAgent
          5 service imports depend on QdrantAgent
          AlchemistAgent provides schema migration capabilities
"""

# Relative imports for Docker compatibility
from .postgres_agent import PostgresAgent
from .qdrant_agent import QdrantAgent
from .alchemist_agent import AlchemistAgent

# Data Access Layers
from .factor_access import (
    get_latest_factors,
    get_factors_for_date,
)
from .sentiment_access import (
    get_latest_sentiments,
    get_latest_sentiment_for_ticker,
)
from .macro_access import (
    get_latest_macro,
)
from .trend_access import (
    get_latest_trends,
    get_latest_trend_for_ticker,
)

# Data Persistence Layers
from .factor_persistence import (
    save_factor_score,
)
from .sentiment_persistence import (
    save_sentiment_score,
)
from .macro_persistence import (
    save_macro_outlook,
)

__all__ = [
    # Core Agents (CRITICAL)
    "PostgresAgent",
    "QdrantAgent",
    "AlchemistAgent",
    # Data Access
    "get_latest_factors",
    "get_factors_for_date",
    "get_latest_sentiments",
    "get_latest_sentiment_for_ticker",
    "get_latest_macro",
    "get_latest_trends",
    "get_latest_trend_for_ticker",
    # Data Persistence
    "save_factor_score",
    "save_sentiment_score",
    "save_macro_outlook",
]
