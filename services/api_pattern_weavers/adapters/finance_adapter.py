"""
Finance Vertical Adapter
========================

Loads finance-specific components when PATTERN_DOMAIN=finance.
Wires domain code (LIVELLO 1) with service infrastructure (LIVELLO 2).
"""

from importlib import resources
from pathlib import Path
import logging
from typing import Any, Dict, List, Optional

from core.cognitive.pattern_weavers.domain.config import TaxonomyConfig

from ..config import get_config

logger = logging.getLogger(__name__)


class FinanceAdapter:
    """
    Finance vertical adapter for Pattern Weavers.

    Provides:
    - Financial context detection
    - Sector resolution using sector_mappings table
    - Finance taxonomy loading/stats
    - Finance-specific score adjustment
    """

    def __init__(self):
        self._context_detector = None
        self._sector_resolver = None
        self._weave_config = None
        self._taxonomy = None
        self._taxonomy_path = self._resolve_taxonomy_path()

    @property
    def context_detector(self):
        if self._context_detector is None:
            try:
                from domains.finance.pattern_weavers.financial_context import FinancialContextDetector
            except ModuleNotFoundError:
                from core.domains.finance.pattern_weavers.financial_context import (
                    FinancialContextDetector,
                )

            self._context_detector = FinancialContextDetector()
        return self._context_detector

    @property
    def sector_resolver(self):
        if self._sector_resolver is None:
            try:
                from domains.finance.pattern_weavers.sector_resolver import SectorResolver
            except ModuleNotFoundError:
                from core.domains.finance.pattern_weavers.sector_resolver import (
                    SectorResolver,
                )
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
    def weave_config(self):
        if self._weave_config is None:
            try:
                from domains.finance.pattern_weavers.weave_config import FinanceWeaveConfig
            except ModuleNotFoundError:
                from core.domains.finance.pattern_weavers.weave_config import (
                    FinanceWeaveConfig,
                )

            self._weave_config = FinanceWeaveConfig()
        return self._weave_config

    @property
    def taxonomy(self) -> TaxonomyConfig:
        if self._taxonomy is not None:
            return self._taxonomy

        if self._taxonomy_path:
            self._taxonomy = TaxonomyConfig.from_yaml(Path(self._taxonomy_path))
        else:
            self._taxonomy = TaxonomyConfig()

        return self._taxonomy

    @property
    def taxonomy_path(self) -> str:
        return self._taxonomy_path

    def detect_financial_context(self, text: str, language: str = "auto") -> Dict[str, Any]:
        return self.context_detector.is_financial(text, language)

    def resolve_sector(self, query: str, language: str = "auto") -> Optional[Dict[str, Any]]:
        if not self.sector_resolver:
            return None
        return self.sector_resolver.resolve_sector(query, language)

    def score_matches(self, matches: List[Dict[str, Any]], is_financial: bool) -> List[Dict[str, Any]]:
        try:
            from domains.finance.pattern_weavers.weave_config import get_category_boost
        except ModuleNotFoundError:
            from core.domains.finance.pattern_weavers.weave_config import (
                get_category_boost,
            )

        cfg = self.weave_config
        scored: List[Dict[str, Any]] = []

        for match in matches:
            base_score = float(match.get("score", 0.0))
            category = (match.get("category") or "").lower()
            boost = get_category_boost(category=category, is_financial=is_financial)
            adjusted_score = min(cfg.max_adjusted_score, base_score * boost)

            enriched = dict(match)
            enriched["base_score"] = round(base_score, 6)
            enriched["boost"] = round(boost, 4)
            enriched["score"] = round(adjusted_score, 6)
            scored.append(enriched)

        scored.sort(key=lambda item: item.get("score", 0.0), reverse=True)
        return scored

    def get_taxonomy_stats(self) -> Dict[str, Any]:
        taxonomy = self.taxonomy
        categories = list(taxonomy.categories.keys())
        total_entries = sum(len(items) for items in taxonomy.categories.values())
        return {
            "categories": categories,
            "total_entries": total_entries,
            "taxonomy_path": self.taxonomy_path,
        }

    def _resolve_taxonomy_path(self) -> str:
        config_path = get_config().taxonomy_path
        if config_path and Path(config_path).exists():
            return config_path

        try:
            candidate = resources.files("domains.finance.pattern_weavers").joinpath(
                "taxonomy_finance.yaml"
            )
            if candidate.is_file():
                return str(candidate)
        except Exception:
            try:
                candidate = resources.files(
                    "vitruvyan_core.domains.finance.pattern_weavers"
                ).joinpath("taxonomy_finance.yaml")
                if candidate.is_file():
                    return str(candidate)
            except Exception:
                pass

        candidates = [
            Path(__file__).resolve().parents[3]
            / "vitruvyan_core/domains/finance/pattern_weavers/taxonomy_finance.yaml",
            Path(__file__).resolve().parents[2]
            / "domains/finance/pattern_weavers/taxonomy_finance.yaml",
            Path("/app/vitruvyan_core/domains/finance/pattern_weavers/taxonomy_finance.yaml"),
            Path("/app/domains/finance/pattern_weavers/taxonomy_finance.yaml"),
        ]
        for path in candidates:
            if path.exists():
                return str(path)

        logger.warning("Finance taxonomy YAML not found in candidates: %s", candidates)
        return ""


_finance_adapter: Optional[FinanceAdapter] = None


def is_finance_enabled() -> bool:
    """Check whether finance vertical is active."""
    return get_config().service.pattern_domain == "finance"


def get_finance_adapter() -> Optional[FinanceAdapter]:
    """
    Get finance adapter singleton when PATTERN_DOMAIN=finance.
    Returns None in non-finance mode.
    """
    global _finance_adapter
    if not is_finance_enabled():
        return None

    if _finance_adapter is None:
        _finance_adapter = FinanceAdapter()
        logger.info("Finance vertical adapter loaded (PATTERN_DOMAIN=finance)")

    return _finance_adapter
