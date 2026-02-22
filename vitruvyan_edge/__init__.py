# Last updated: Feb 22, 2026 16:30 UTC
"""
Vitruvyan Edge — Multi-Module Pluggable Ingestion Layer.

Package contenitore per moduli edge pluggabili nel core.
Ogni modulo è indipendente e comunica con vitruvyan_core via StreamBus.

Modules:
    - oculus_prime: Multi-modal intake gateway (documents, images, audio, video, CAD, GIS)
    - dse_cps: (planned) DSE-CPS engine integration
"""

__version__ = "1.0.0"

EDGE_MODULES = [
    "oculus_prime",
    # "dse_cps",       # planned
    # "stream_intake", # planned
]
