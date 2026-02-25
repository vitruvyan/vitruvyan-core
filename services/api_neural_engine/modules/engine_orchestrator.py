# api_neural_engine/modules/engine_orchestrator.py
"""
Engine Orchestrator - Bridge between FastAPI and domain-agnostic Neural Engine.
"""

import logging
import os
import time
from typing import Dict, List, Optional, Any

import pandas as pd

from vitruvyan_core.core.neural_engine import NeuralEngine
from vitruvyan_core.contracts import IDataProvider, IScoringStrategy, IFilterStrategy
from .response_builder import ResponseBuilder
from ..adapters.persistence import NeuralEnginePersistence
from ..config import (
    DOMAIN,
    DEFAULT_STRATIFICATION_MODE,
    NE_CACHE_TTL_SECONDS,
)

logger = logging.getLogger(__name__)


class EngineOrchestrator:
    """Orchestrator for Neural Engine API operations."""

    def __init__(self):
        self.engine: Optional[NeuralEngine] = None
        self.data_provider: Optional[IDataProvider] = None
        self.scoring_strategy: Optional[IScoringStrategy] = None
        self.filter_strategy: Optional[IFilterStrategy] = None
        self._cache: Dict[str, Any] = {}
        self._initialized = False
        self._domain = DOMAIN
        self._default_stratification_mode = DEFAULT_STRATIFICATION_MODE
        self._cache_ttl_seconds = NE_CACHE_TTL_SECONDS
        self._persist_enabled = os.getenv("NE_PERSIST_RESULTS", "0") == "1"
        self._persistence: Optional[NeuralEnginePersistence] = None

    async def initialize(self):
        logger.info("🔧 Initializing Engine Orchestrator (domain=%s)...", self._domain)
        try:
            if self._domain == "finance":
                from vitruvyan_core.domains.finance.neural_engine import (
                    TickerDataProvider,
                    FinancialScoringStrategy,
                    FinancialFilterStrategy,
                )

                self.data_provider = TickerDataProvider()
                self.scoring_strategy = FinancialScoringStrategy()
                self.filter_strategy = FinancialFilterStrategy()
                logger.info("✅ Loaded finance provider + scoring + filter strategy")
            elif self._domain == "mock":
                from vitruvyan_core.core.neural_engine.domain_examples import (
                    MockDataProvider,
                    MockScoringStrategy,
                )

                self.data_provider = MockDataProvider(num_entities=100)
                self.scoring_strategy = MockScoringStrategy()
                self.filter_strategy = None
                logger.info("✅ Loaded mock domain provider + scoring strategy")
            else:
                raise ValueError(f"Unsupported DOMAIN='{self._domain}'")

            self.engine = self._build_engine(self._default_stratification_mode)
            if self._persist_enabled:
                self._persistence = NeuralEnginePersistence()

            self._initialized = True
            logger.info(
                "✅ Engine Orchestrator initialized (domain=%s, stratification=%s, cache_ttl=%ss)",
                self._domain,
                self._default_stratification_mode,
                self._cache_ttl_seconds,
            )
        except Exception as e:
            logger.error("❌ Failed to initialize Engine Orchestrator: %s", e)
            raise

    async def shutdown(self):
        logger.info("🛑 Shutting down Engine Orchestrator...")
        self._cache.clear()
        self._initialized = False

    async def screen(
        self,
        profile: str,
        entity_ids: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        stratification_mode: str = "global",
        risk_tolerance: str = "medium",
        mode: str = "discovery",
        sector: Optional[str] = None,
        momentum_breakout: bool = False,
        value_screening: bool = False,
        divergence_detection: bool = False,
        multi_timeframe_filter: bool = False,
        smart_money_flow: bool = False,
        earnings_safety_days: Optional[int] = None,
        portfolio_diversification: Optional[List[str]] = None,
        macro_factor: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self._initialized:
            raise RuntimeError("Orchestrator not initialized")

        start_time = time.time()

        filters = dict(filters or {})
        if sector:
            filters["sector"] = sector

        advanced_filters = {
            "mode": mode,
            "sector": sector,
            "momentum_breakout": momentum_breakout,
            "value_screening": value_screening,
            "divergence_detection": divergence_detection,
            "multi_timeframe_filter": multi_timeframe_filter,
            "smart_money_flow": smart_money_flow,
            "earnings_safety_days": earnings_safety_days,
            "portfolio_diversification": portfolio_diversification or [],
            "macro_factor": macro_factor,
        }

        cache_key = (
            f"screen:{profile}:{entity_ids}:{filters}:{top_k}:{stratification_mode}:{risk_tolerance}:"
            f"{advanced_filters}"
        )

        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self._cache_ttl_seconds:
                logger.info("✅ Cache hit for %s", cache_key)
                return cached_data

        try:
            effective_mode = self._normalize_stratification_mode(stratification_mode)
            engine = self.engine
            if not engine or engine.stratification_mode != effective_mode:
                engine = self._build_engine(effective_mode)

            # Run without top-k first to allow full filter pass.
            result = engine.run(
                profile=profile,
                entity_ids=entity_ids,
                filters=filters,
                top_k=None,
                risk_tolerance=risk_tolerance,
            )

            ranked_df = result["ranked_entities"].copy()
            filter_diag: Dict[str, Any] = {}

            if self.filter_strategy and self._domain == "finance":
                ranked_df, filter_diag = self.filter_strategy.apply_filters(
                    ranked_df,
                    filters=advanced_filters,
                    context={"profile": profile, "risk_tolerance": risk_tolerance},
                )

                if not ranked_df.empty:
                    # Re-rank after filtering and apply guardrails/type caps.
                    ranked_df = engine.ranker.rank_entities(
                        ranked_df,
                        score_column="composite_score",
                        entity_id_column="entity_id",
                        top_k=None,
                    )
                    stocks_top, etf_top, fund_top = self.filter_strategy.apply_guardrails_and_topk(
                        ranked_df,
                        top_k=top_k,
                        bypass_sector_cap=(mode == "analyze"),
                    )
                    ranked_df = (
                        [stocks_top, etf_top, fund_top]
                        if any(not x.empty for x in [stocks_top, etf_top, fund_top])
                        else [ranked_df.head(top_k)]
                    )
                    ranked_df = (
                        ranked_df[0]
                        if len(ranked_df) == 1
                        else pd.concat(ranked_df, ignore_index=True)
                    )
                    if not ranked_df.empty:
                        ranked_df = engine.ranker.rank_entities(
                            ranked_df,
                            score_column="composite_score",
                            entity_id_column="entity_id",
                            top_k=top_k,
                        )
                else:
                    ranked_df = ranked_df.head(0)
            else:
                ranked_df = engine.ranker.rank_entities(
                    ranked_df,
                    score_column="composite_score",
                    entity_id_column="entity_id",
                    top_k=top_k,
                )

            response = ResponseBuilder.build_screen_response(
                ranked_df=ranked_df,
                profile=profile,
                top_k=top_k,
                stratification_mode=effective_mode,
                profile_weights=result.get("profile_weights", {}),
                total_entities=result.get("metadata", {}).get("total_entities", len(ranked_df)),
                processing_time_ms=(time.time() - start_time) * 1000,
                statistics=result.get("statistics"),
                screening_criteria={
                    "profile": profile,
                    "mode": mode,
                    "sector": sector,
                    "risk_tolerance": risk_tolerance,
                    "filters": advanced_filters,
                    "diagnostics": filter_diag,
                },
            )

            if self._persist_enabled and self._persistence:
                run_id = self._persistence.persist_screen_result(response)
                if run_id is not None:
                    response["run_id"] = run_id

            self._cache[cache_key] = (response, time.time())
            return response

        except Exception as e:
            logger.error("❌ Screening failed: %s", e)
            raise

    async def rank(
        self,
        feature_name: str,
        entity_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        higher_is_better: bool = True,
    ) -> Dict[str, Any]:
        if not self._initialized:
            raise RuntimeError("Orchestrator not initialized")

        start_time = time.time()

        universe = self.data_provider.get_universe()
        if entity_ids:
            universe = universe[universe["entity_id"].isin(entity_ids)]

        features = self.data_provider.get_features(
            entity_ids=universe["entity_id"].tolist(),
            feature_names=[feature_name],
        )

        merged = universe.merge(features, on="entity_id")
        if feature_name not in merged.columns:
            raise ValueError(f"Feature '{feature_name}' not available for current domain")
        merged = merged.dropna(subset=[feature_name]).copy()
        merged = merged.sort_values(by=feature_name, ascending=not higher_is_better)

        if top_k:
            merged = merged.head(top_k)

        merged["rank"] = range(1, len(merged) + 1)

        n = len(merged)
        if n > 0:
            merged["percentile"] = ((n - merged["rank"] + 1) / n * 100).round(1)
            merged["bucket"] = merged["percentile"].apply(
                lambda p: "top" if p >= 70 else ("middle" if p >= 30 else "bottom")
            )
        else:
            merged["percentile"] = pd.Series(dtype=float)
            merged["bucket"] = pd.Series(dtype=str)

        return ResponseBuilder.build_rank_response(
            ranked_df=merged,
            feature_name=feature_name,
            higher_is_better=higher_is_better,
            processing_time_ms=(time.time() - start_time) * 1000,
        )

    async def get_available_profiles(self) -> List[Dict[str, str]]:
        if not self._initialized:
            raise RuntimeError("Orchestrator not initialized")

        profiles = self.scoring_strategy.get_available_profiles()
        return [
            {
                "name": p,
                "description": self.scoring_strategy.get_profile_metadata(p).get(
                    "description",
                    f"Scoring profile: {p}",
                ),
            }
            for p in profiles
        ]

    async def health_check(self) -> bool:
        return self._initialized

    async def check_data_provider(self) -> bool:
        if not self.data_provider:
            return False
        try:
            universe = self.data_provider.get_universe()
            return len(universe) > 0
        except Exception as e:
            logger.error("❌ Data provider health check failed: %s", e)
            return False

    async def check_scoring_strategy(self) -> bool:
        if not self.scoring_strategy:
            return False
        try:
            profiles = self.scoring_strategy.get_available_profiles()
            return len(profiles) > 0
        except Exception as e:
            logger.error("❌ Scoring strategy health check failed: %s", e)
            return False

    def _build_engine(self, stratification_mode: str) -> NeuralEngine:
        return NeuralEngine(
            data_provider=self.data_provider,
            scoring_strategy=self.scoring_strategy,
            stratification_mode=stratification_mode,
            enable_time_decay=False,
        )

    @staticmethod
    def _normalize_stratification_mode(mode: str) -> str:
        normalized = (mode or "global").strip().lower()
        if normalized == "sector":
            normalized = "stratified"
        if normalized not in {"global", "stratified", "composite"}:
            return "global"
        return normalized
