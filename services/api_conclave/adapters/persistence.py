"""
🕯 Synaptic Conclave — Persistence Adapter (LIVELLO 2)

The ONLY file in this service that would touch databases.
Currently a minimal stub: the Conclave is an Epistemic Observatory
that observes events, not a data producer.

Future: Chronicle high-level event statistics to PostgreSQL.

"Il Conclave osserva, non scrive. Ma quando scriverà, lo farà solo qui."
Follows SERVICE_PATTERN.md (LIVELLO 2).
"""

import logging

logger = logging.getLogger("Conclave.Persistence")


class PersistenceAdapter:
    """
    Placeholder I/O boundary for Synaptic Conclave.

    Currently the Conclave has no direct database writes.
    This stub exists to:
    1. Maintain SERVICE_PATTERN.md structural compliance
    2. Provide a clear extension point for future persistence needs
    3. Keep all I/O decisions in one place

    Future candidates:
    - Chronicle event statistics to PostgreSQL
    - Archive significant cognitive events to Qdrant
    """

    def __init__(self, pg=None, qdrant=None):
        self._pg = pg
        self._qdrant = qdrant
        logger.debug("PersistenceAdapter initialized (stub — no active I/O)")
