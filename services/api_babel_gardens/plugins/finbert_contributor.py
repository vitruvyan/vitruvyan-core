"""
FinBERT Signal Contributor — Comprehension Engine v3
====================================================

Wraps FinanceSignalsPlugin (FinBERT model) as an ISignalContributor
for the Comprehension Engine signal fusion pipeline.

LIVELLO 2 — Service layer (instantiates HuggingFace model).

Architecture:
  ComprehensionAdapter (LLM call) → Layer 1 signals
  FinBERTContributor (this) → Layer 2 signals (domain-specific)
  SignalFusionAdapter → Fuses L1 + L2 signals

> **Last updated**: Feb 28, 2026 12:00 UTC
"""

import logging
import time
from typing import Dict, List, Optional

try:
    from contracts.comprehension import ISignalContributor, SignalEvidence
except ModuleNotFoundError:
    from vitruvyan_core.contracts.comprehension import ISignalContributor, SignalEvidence

logger = logging.getLogger(__name__)


class FinBERTContributor(ISignalContributor):
    """
    FinBERT-based signal contributor for finance domain.

    Wraps the existing FinanceSignalsPlugin to extract:
    - sentiment_valence: [-1, 1] market sentiment polarity
    - market_fear_index: [0, 1] market stress indicator
    - volatility_perception: [0, 1] perceived volatility

    Lazy-loads the model — first call triggers FinBERT download.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
    ):
        self._model_name = model_name
        self._device = device
        self._plugin = None
        self._signal_config = None

    @property
    def _signals_plugin(self):
        """Lazy-load FinanceSignalsPlugin."""
        if self._plugin is None:
            from ..plugins.finance_signals import FinanceSignalsPlugin

            self._plugin = FinanceSignalsPlugin(
                model_name=self._model_name,
                device=self._device,
            )
        return self._plugin

    @property
    def _config(self):
        """Lazy-load finance signal config YAML."""
        if self._signal_config is not None:
            return self._signal_config

        try:
            from importlib import resources
            from core.cognitive.babel_gardens.domain import load_config_from_yaml

            candidate = resources.files("domains.finance.babel_gardens").joinpath(
                "signals_finance.yaml"
            )
            if candidate.is_file():
                self._signal_config = load_config_from_yaml(str(candidate))
                return self._signal_config
        except Exception:
            pass

        # Fallback paths for local dev
        from pathlib import Path
        from core.cognitive.babel_gardens.domain import load_config_from_yaml

        candidates = [
            Path(__file__).resolve().parents[3]
            / "vitruvyan_core/domains/finance/babel_gardens/signals_finance.yaml",
            Path(__file__).resolve().parents[2]
            / "domains/finance/babel_gardens/signals_finance.yaml",
            Path("/app/domains/finance/babel_gardens/signals_finance.yaml"),
        ]

        for yaml_path in candidates:
            if yaml_path.exists():
                self._signal_config = load_config_from_yaml(str(yaml_path))
                return self._signal_config

        logger.warning("Finance signals YAML not found")
        return None

    def get_contributor_name(self) -> str:
        return "finbert"

    def get_signal_names(self) -> List[str]:
        return ["sentiment_valence", "market_fear_index", "volatility_perception"]

    def is_available(self) -> bool:
        """Check if FinBERT model can be loaded."""
        try:
            # Check if transformers is importable (don't load model yet)
            import importlib
            importlib.import_module("transformers")
            return True
        except ImportError:
            logger.debug("FinBERTContributor unavailable: transformers not installed")
            return False

    def contribute(self, text: str, context: Optional[Dict] = None) -> List[SignalEvidence]:
        """
        Extract finance signals via FinBERT.

        Args:
            text: Input text to analyze
            context: Optional context (language, detected entities, etc.)

        Returns:
            List of SignalEvidence from FinBERT model
        """
        config = self._config
        if not config:
            logger.warning("FinBERTContributor: no signal config, returning empty")
            return []

        start = time.perf_counter()

        try:
            results = self._signals_plugin.extract_signals(text, config)
        except Exception as exc:
            logger.error("FinBERTContributor extraction failed: %s", exc)
            return []

        elapsed_ms = (time.perf_counter() - start) * 1000

        evidences = []
        for result in results:
            evidence = SignalEvidence(
                signal_name=result.signal_name,
                value=result.value,
                confidence=result.confidence,
                source="finbert",
                method=result.extraction_trace.get("method", "model:finbert"),
                extraction_trace=result.extraction_trace,
                metadata={
                    **(result.metadata or {}),
                    "contributor": "finbert",
                    "total_extraction_time_ms": round(elapsed_ms, 2),
                },
            )
            evidences.append(evidence)

        logger.debug(
            "FinBERTContributor: extracted %d signals in %.1fms",
            len(evidences),
            elapsed_ms,
        )
        return evidences


__all__ = ["FinBERTContributor"]
