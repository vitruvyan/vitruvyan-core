"""
🗺️ VITRUVYAN CODEX HUNTERS
============================
Digital archaeologists tracking lost data across the financial dark ages

"No codex left unfound" - The Hunter's Creed

Architecture:
- BaseHunter: Foundation class with expedition logic
- Tracker: Multi-source codex discovery (yfinance, Reddit, Google News, FRED)
- Restorer: Damaged page restoration and normalization
- Binder: Permanent archive preservation (PostgreSQL + Qdrant)
- Inspector: Authenticity verification and integrity checking (TODO)
- Expedition Planner: Time-based expedition scheduling (TODO)
- Cartographer: Discovery mapping and reporting (TODO)
- Expedition Leader: Central coordination and orchestration (TODO)
- ConclaveIntegration: Event-driven integration with Synaptic Conclave (PHASE 4.5)
- EventHunter: Synaptic Conclave Bridge - Real-time event processing and expedition orchestration

Integration:
- PostgresAgent: SQL Archive operations
- QdrantAgent: Vector Vault operations
- Cognitive Bus: Expedition event communication
- Audit Engine: Discovery reporting and health monitoring

Event Protocol:
- codex.discovered → manuscript found in archives
- page.restored → damaged pages cleaned and repaired
- volume.bound → codex bound and stored permanently
- authenticity.verified → codex authenticity confirmed
- expedition.scheduled → new expedition planned
- discovery.mapped → findings cartographed
"""

from .hunter import BaseHunter, CodexEvent
from .tracker import Tracker
from .restorer import Restorer
from .binder import Binder

# Import core hunters (Sacred Orders #1-9)
from .inspector import Inspector
from .scholastic import Scholastic
from .scribe import Scribe
from .fundamentalist import Fundamentalist
from .cassandra import Cassandra

# Import orchestration hunters
from .expedition_planner import ExpeditionPlanner
from .cartographer import Cartographer
from .expedition_leader import ExpeditionLeader

# PHASE 4.5 - Synaptic Conclave Integration
from .conclave_cycle import ConclaveIntegration
from .event_hunter import EventHunter

__all__ = [
    'BaseHunter',
    'CodexEvent',
    'Tracker',
    'Restorer',
    'Binder',
    'Inspector',
    'Scholastic',
    'Scribe',
    'Fundamentalist',
    'Cassandra',
    'ExpeditionPlanner',
    'Cartographer',
    'ExpeditionLeader',
    'ConclaveIntegration',
    'EventHunter',
]

__version__ = '1.0.0'
__author__ = 'Vitruvyan Team'
__description__ = 'Codex Hunters - Digital Archaeology for Financial Data Preservation'
__motto__ = 'No codex left unfound'
