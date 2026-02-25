"""
Finance Vertical Adapter
========================

Loads finance-specific components when BABEL_DOMAIN=finance.
Wires domain code (LIVELLO 1) with service infrastructure (LIVELLO 2).
"""

from pathlib import Path
from importlib import resources
import logging
from typing import Any, Dict, List, Optional

from ..config import get_config

logger = logging.getLogger(__name__)


class FinanceAdapter:
    """
    Finance vertical adapter for Babel Gardens.

    Provides:
    - Finance signal extraction (FinBERT + lexicon)
    - GICS sector resolution
    - Financial context detection
    - Finance-specific fusion weights
    """

    def __init__(self):
        self._signals_plugin = None
        self._sector_resolver = None
        self._context_detector = None
        self._sentiment_config = None
        self._signal_config = None

    @property
    def signals_plugin(self):
        """Lazy-load `FinanceSignalsPlugin`."""
        if self._signals_plugin is None:
            from ..plugins.finance_signals import FinanceSignalsPlugin

            self._signals_plugin = FinanceSignalsPlugin()
        return self._signals_plugin

    @property
    def sector_resolver(self):
        """Lazy-load `SectorResolver` with injected `PostgresAgent.fetch`."""
        if self._sector_resolver is None:
            from domains.finance.babel_gardens.sector_resolver import SectorResolver
            from .persistence import get_persistence

            persistence = get_persistence()
            if persistence.pg_agent:
                self._sector_resolver = SectorResolver(
                    db_fetcher=persistence.pg_agent.fetch,
                )
            else:
                logger.warning("SectorResolver unavailable: PostgresAgent not ready")
        return self._sector_resolver

    @property
    def context_detector(self):
        """Lazy-load `FinancialContextDetector`."""
        if self._context_detector is None:
            from domains.finance.babel_gardens.financial_context import FinancialContextDetector

            self._context_detector = FinancialContextDetector()
        return self._context_detector

    @property
    def sentiment_config(self):
        """Lazy-load `FinanceSentimentConfig`."""
        if self._sentiment_config is None:
            from domains.finance.babel_gardens.sentiment_config import FinanceSentimentConfig

            self._sentiment_config = FinanceSentimentConfig()
        return self._sentiment_config

    @property
    def signal_config(self):
        """Lazy-load finance signal schema YAML."""
        if self._signal_config is not None:
            return self._signal_config

        from core.cognitive.babel_gardens.domain import load_config_from_yaml

        # Prefer package resources when the `domains` package is importable.
        try:
            candidate = resources.files("domains.finance.babel_gardens").joinpath(
                "signals_finance.yaml"
            )
            if candidate.is_file():
                self._signal_config = load_config_from_yaml(str(candidate))
                return self._signal_config
        except Exception:
            pass

        # Fallback for local source-tree execution.
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

        logger.warning("Finance signals YAML not found in candidates: %s", candidates)
        return None

    def extract_finance_signals(self, text: str) -> List[Dict[str, Any]]:
        """Extract all configured finance signals and serialize response payload."""
        if not self.signal_config:
            return []

        results = self.signals_plugin.extract_signals(text, self.signal_config)
        return [
            {
                "signal_name": result.signal_name,
                "value": result.value,
                "confidence": result.confidence,
                "extraction_trace": result.extraction_trace,
                "metadata": result.metadata,
            }
            for result in results
        ]

    def detect_financial_context(self, text: str, language: str = "auto") -> Dict[str, Any]:
        """Detect whether text is finance-related."""
        return self.context_detector.is_financial(text, language)

    def resolve_sector(self, query: str, language: str = "auto") -> Optional[Dict[str, Any]]:
        """Resolve GICS sector from multilingual query."""
        if not self.sector_resolver:
            return None
        return self.sector_resolver.resolve_sector(query, language)

    def get_fusion_weights(self, language: str, text: str) -> Dict[str, float]:
        """Return context-adjusted finance fusion weights."""
        from domains.finance.babel_gardens.sentiment_config import get_finance_model_boost

        ctx = self.detect_financial_context(text, language)
        return get_finance_model_boost(language, ctx["is_financial"])


_finance_adapter: Optional[FinanceAdapter] = None


def is_finance_enabled() -> bool:
    """Check whether finance vertical is active."""
    return get_config().service.babel_domain == "finance"


def get_finance_adapter() -> Optional[FinanceAdapter]:
    """
    Get finance adapter singleton when `BABEL_DOMAIN=finance`.
    Returns `None` in non-finance mode.
    """
    global _finance_adapter
    if not is_finance_enabled():
        return None

    if _finance_adapter is None:
        _finance_adapter = FinanceAdapter()
        logger.info("Finance vertical adapter loaded (BABEL_DOMAIN=finance)")

    return _finance_adapter
