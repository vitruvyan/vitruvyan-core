"""
Babel Gardens Plugins — Vertical-Specific Signal Extractors

This package contains domain-specific implementations that wrap ML models
to produce SignalExtractionResult outputs conforming to the domain-agnostic
SignalSchema specification.

LIVELLO 2 (Infrastructure):
- Plugins live in SERVICE layer (not core domain)
- They instantiate HuggingFace models, call APIs, run inference
- They translate model outputs → SignalExtractionResult

Structure:
- finance_signals.py: FinBERT → sentiment_valence, market_fear_index
- cybersecurity_signals.py: SecBERT → threat_severity, exploit_imminence
- maritime_signals.py: MaritimeBERT → delay_severity, route_viability
- base_plugin.py: Abstract plugin interface (optional)

Sacred Law: "Signals are inferred, never invented"
All extractions must provide explainability traces for Orthodoxy Wardens.

Plugin loading is conditional — each vertical plugin is imported only if
its module is present. This allows deploying Babel Gardens without every
vertical installed.
"""

__all__: list[str] = []

# --- Finance vertical (FinBERT-based signals) ---
try:
    from .finance_signals import (
        FinanceSignalsPlugin,
        extract_finance_signals,
    )
    __all__ += ["FinanceSignalsPlugin", "extract_finance_signals"]
except ImportError:
    pass

# --- Cybersecurity vertical (SecBERT-based signals) ---
# Uncomment when cybersecurity_signals.py is ready:
# try:
#     from .cybersecurity_signals import CybersecuritySignalsPlugin
#     __all__ += ["CybersecuritySignalsPlugin"]
# except ImportError:
#     pass

# --- Maritime vertical (MaritimeBERT-based signals) ---
# Uncomment when maritime_signals.py is ready:
# try:
#     from .maritime_signals import MaritimeSignalsPlugin
#     __all__ += ["MaritimeSignalsPlugin"]
# except ImportError:
#     pass
