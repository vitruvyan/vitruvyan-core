"""
🏰 VITRUVYAN VAULT KEEPERS
==========================
Custodes Thesauri - The Guardians of Digital Treasure

"No treasure left unguarded"

Like the legendary keepers of Carcassonne who protected royal treasures from raiders,
the Vault Keepers safeguard Vitruvyan's digital memory against the ravages of time.
Each backup is an oath of fidelity to the future.

THE FORTRESS CREW:
==================

🔍 The Sentinel    - "Vigil Arcis"        - Watches for threats and changes
📚 The Archivist   - "Custos Librorum"    - Seals knowledge in archives  
🐎 The Courier     - "Nuntius Expeditus"  - Swift bearer of treasures
⚖️ The Chamberlain - "Camerarius Magnus"  - Master of records and integrity

VAULT EVENT PROTOCOL:
====================
- treasure.detected    → Changes spotted by Sentinel
- scroll.sealed        → Archive created by Archivist
- courier.departed     → Upload initiated by Courier  
- vault.secured        → Backup verified by Chamberlain
- treasure.corrupted   → Integrity violation detected
- fortress.sealed      → Full system backup complete

ARCHITECTURE:
=============
Built on the proven foundation of Vitruvyan agents:
- PostgresAgent: Fortress Records (backup_history table)
- QdrantAgent: Vector Vault (semantic backups)
- CrewAI: Multi-agent coordination system
- FastAPI: Royal decree endpoints (/vault/*)

MOTTO: "Sicut custodes Carcassonensis thesauros a praedoribus, 
        nos memoriam digitalem Vitruviani custodimus"

VERSION: 1.0 - October 2025
THEME: Medieval Fortress Keepers  
STATUS: Production Ready 🏰
"""

from .keeper import (
    BaseKeeper,
    VaultEvent,
    BackupMode,
    VaultConfig
)

from .sentinel import SentinelAgent
from .archivist import ArchivistAgent  
from .courier import CourierAgent
from .chamberlain import ChamberlainAgent

__all__ = [
    # Core Architecture
    "BaseKeeper",
    "VaultEvent", 
    "BackupMode",
    "VaultConfig",
    
    # The Fortress Crew
    "SentinelAgent",     # The Watchful Guardian
    "ArchivistAgent",    # The Knowledge Sealer
    "CourierAgent",      # The Swift Bearer
    "ChamberlainAgent",  # The Record Master
]

# Vault Keepers Creed
KEEPERS_CREED = """
Like the custodians of Carcassonne's treasure who protected royal riches from raiders,
we guard Vitruvyan's digital memory against time's erosion.
Every backup is a covenant with tomorrow.

No treasure left unguarded.
No memory left vulnerable.
No future left uncertain.
"""

# Event Types Registry
VAULT_EVENTS = {
    "treasure.detected": "Sentinel spotted changes requiring backup",
    "scroll.sealed": "Archivist compressed and secured archive", 
    "courier.departed": "Courier initiated cloud transfer",
    "vault.secured": "Chamberlain verified backup integrity",
    "treasure.corrupted": "Chamberlain detected corruption", 
    "fortress.sealed": "Complete system backup finalized"
}

print("🏰 Vitruvyan Vault Keepers initialized - No treasure left unguarded! ⚔️")