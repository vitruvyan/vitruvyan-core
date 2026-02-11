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
"""

from .finance_signals import (
    FinanceSignalsPlugin,
    extract_finance_signals,
)

__all__ = [
    "FinanceSignalsPlugin",
    "extract_finance_signals",
]
