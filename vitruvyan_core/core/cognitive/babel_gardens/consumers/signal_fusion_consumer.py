"""
Babel Gardens — Signal Fusion Consumer
=======================================

Pure consumer that fuses Layer 1 (LLM comprehension) signals with
Layer 2 (domain model) signals into FusionResult objects.

LIVELLO 1 — Pure Python, no I/O. Math/logic only.

Fusion strategies:
    weighted    — Weighted average of evidence values
    bayesian    — Bayesian posterior update
    llm_arbitrated — Marks for LIVELLO 2 LLM arbitration (not computed here)

> **Last updated**: Feb 26, 2026 14:00 UTC

Author: Vitruvyan Core Team
Version: 1.0.0
"""

import logging
import math
import time
from typing import Any, Dict, List, Optional

from .base import BaseConsumer, ProcessResult

try:
    from contracts.comprehension import (
        ComprehensionResult,
        FusionContributor,
        FusionResult,
        FusionStrategy,
        SignalEvidence,
    )
except ModuleNotFoundError:
    from core.cognitive.babel_gardens.domain import (
        ComprehensionResult,
        FusionContributor,
        FusionResult,
        FusionStrategy,
        SignalEvidence,
    )

logger = logging.getLogger(__name__)


class SignalFusionConsumer(BaseConsumer):
    """
    Pure consumer: fuse multiple signal evidences into FusionResults.

    Input data keys:
        comprehension : dict           — ComprehensionResult.model_dump()
        evidences     : list[dict]     — List of SignalEvidence.model_dump()
        strategy      : str            — FusionStrategy value
        weights       : dict[str,float] — Optional per-source weight overrides

    Output ProcessResult.data keys:
        results       : list[dict]     — List of FusionResult.model_dump()
    """

    def process(self, data: Dict[str, Any]) -> ProcessResult:
        """Fuse signal evidences into FusionResults."""
        start = time.monotonic()

        errors = self.validate_input(data, ["comprehension"])
        if errors:
            self._record_error()
            return ProcessResult(success=False, data={"results": []}, errors=errors)

        try:
            comprehension = ComprehensionResult.model_validate(data["comprehension"])

            raw_evidences = data.get("evidences", [])
            evidences = [SignalEvidence.model_validate(e) for e in raw_evidences]

            strategy_str = data.get("strategy", FusionStrategy.WEIGHTED.value)
            strategy = FusionStrategy(strategy_str)

            weight_overrides: Dict[str, float] = data.get("weights", {})

            # Extract Layer 1 signals from ComprehensionResult
            l1_evidences = self._extract_l1_signals(comprehension)

            # Combine L1 + L2
            all_evidences = l1_evidences + evidences

            # Group by signal dimension (e.g. "sentiment", "emotion")
            groups = self._group_by_dimension(all_evidences)

            # Fuse each group
            results: List[Dict[str, Any]] = []
            for dimension, group_evidences in groups.items():
                fusion = self._fuse_group(
                    dimension, group_evidences, strategy, weight_overrides
                )
                results.append(fusion.model_dump())

            elapsed_ms = (time.monotonic() - start) * 1000
            self._record_success()

            return ProcessResult(
                success=True,
                data={"results": results},
                processing_time_ms=elapsed_ms,
            )

        except Exception as e:
            error_msg = f"Fusion error: {e}"
            logger.warning(f"SignalFusionConsumer: {error_msg}")
            self._record_error()
            return ProcessResult(
                success=False,
                data={"results": []},
                errors=[error_msg],
                processing_time_ms=(time.monotonic() - start) * 1000,
            )

    def _extract_l1_signals(self, comprehension: ComprehensionResult) -> List[SignalEvidence]:
        """Extract SignalEvidence objects from Layer 1 ComprehensionResult."""
        signals: List[SignalEvidence] = []
        sem = comprehension.semantics

        # Sentiment as evidence
        if sem.sentiment.label != "neutral" or sem.sentiment.score != 0.0:
            signals.append(SignalEvidence(
                signal_name="sentiment",
                value=sem.sentiment.score,
                confidence=sem.sentiment.confidence,
                source="llm_comprehension",
                method="unified_llm_call",
                extraction_trace={
                    "label": sem.sentiment.label,
                    "magnitude": sem.sentiment.magnitude,
                    "reasoning": sem.sentiment.reasoning,
                },
            ))

        # Emotion as evidence (map to -1..1 intensity scale)
        if sem.emotion.primary != "neutral":
            # Map emotion to valence: positive emotions → +, negative → -
            _POSITIVE_EMOTIONS = {"excited", "confident", "satisfied", "hopeful", "happy", "joy", "playful"}
            _NEGATIVE_EMOTIONS = {"frustrated", "anxious", "angry", "fearful", "sad", "disgusted", "skeptical"}

            emotion_val = sem.emotion.intensity
            if sem.emotion.primary in _NEGATIVE_EMOTIONS:
                emotion_val = -emotion_val

            signals.append(SignalEvidence(
                signal_name="emotion",
                value=emotion_val,
                confidence=sem.emotion.confidence,
                source="llm_comprehension",
                method="unified_llm_call",
                extraction_trace={
                    "primary": sem.emotion.primary,
                    "secondary": sem.emotion.secondary,
                    "cultural_context": sem.emotion.cultural_context,
                    "reasoning": sem.emotion.reasoning,
                },
            ))

        return signals

    @staticmethod
    def _group_by_dimension(evidences: List[SignalEvidence]) -> Dict[str, List[SignalEvidence]]:
        """Group evidences by signal_name dimension."""
        groups: Dict[str, List[SignalEvidence]] = {}
        for ev in evidences:
            groups.setdefault(ev.signal_name, []).append(ev)
        return groups

    def _fuse_group(
        self,
        dimension: str,
        evidences: List[SignalEvidence],
        strategy: FusionStrategy,
        weight_overrides: Dict[str, float],
    ) -> FusionResult:
        """Fuse a group of evidences for one signal dimension."""

        if strategy == FusionStrategy.WEIGHTED:
            return self._fuse_weighted(dimension, evidences, weight_overrides)
        elif strategy == FusionStrategy.BAYESIAN:
            return self._fuse_bayesian(dimension, evidences, weight_overrides)
        elif strategy == FusionStrategy.LLM_ARBITRATED:
            # LLM arbitration requires I/O — mark for LIVELLO 2 handling
            return FusionResult(
                signal_name=dimension,
                fused_value=0.0,
                fused_label="pending_arbitration",
                fused_confidence=0.0,
                strategy_used=FusionStrategy.LLM_ARBITRATED,
                contributors=[
                    FusionContributor(
                        evidence=ev,
                        applied_weight=weight_overrides.get(ev.source, 1.0),
                    )
                    for ev in evidences
                ],
                reasoning="Deferred to LIVELLO 2 LLM arbitration",
            )
        else:
            return self._fuse_weighted(dimension, evidences, weight_overrides)

    @staticmethod
    def _fuse_weighted(
        dimension: str,
        evidences: List[SignalEvidence],
        weight_overrides: Dict[str, float],
    ) -> FusionResult:
        """Confidence-weighted average fusion."""
        contributors: List[FusionContributor] = []
        weighted_sum = 0.0
        total_weight = 0.0

        for ev in evidences:
            # Weight = confidence × override (if any)
            w = ev.confidence * weight_overrides.get(ev.source, 1.0)
            weighted_sum += ev.value * w
            total_weight += w
            contributors.append(FusionContributor(evidence=ev, applied_weight=round(w, 4)))

        fused_value = weighted_sum / total_weight if total_weight > 0 else 0.0
        fused_confidence = min(1.0, total_weight / len(evidences)) if evidences else 0.0

        # Derive label from fused value
        fused_label = "neutral"
        if fused_value > 0.15:
            fused_label = "positive"
        elif fused_value < -0.15:
            fused_label = "negative"

        return FusionResult(
            signal_name=dimension,
            fused_value=round(fused_value, 4),
            fused_label=fused_label,
            fused_confidence=round(fused_confidence, 4),
            strategy_used=FusionStrategy.WEIGHTED,
            contributors=contributors,
            reasoning=f"Weighted fusion of {len(evidences)} signals, total_weight={total_weight:.4f}",
        )

    @staticmethod
    def _fuse_bayesian(
        dimension: str,
        evidences: List[SignalEvidence],
        weight_overrides: Dict[str, float],
    ) -> FusionResult:
        """
        Bayesian posterior update fusion.

        Treats each evidence as a likelihood update on a prior.
        Prior: uniform (0.5). Each evidence shifts posterior based on
        its confidence-weighted value.
        """
        contributors: List[FusionContributor] = []

        # Start with uniform prior (log-odds = 0)
        log_odds = 0.0

        for ev in evidences:
            w = ev.confidence * weight_overrides.get(ev.source, 1.0)
            # Map value from [-1, 1] to probability [0.01, 0.99]
            p = max(0.01, min(0.99, (ev.value + 1.0) / 2.0))
            # Log-odds update weighted by confidence
            update = w * math.log(p / (1.0 - p))
            log_odds += update
            contributors.append(FusionContributor(evidence=ev, applied_weight=round(w, 4)))

        # Convert back to probability, then to [-1, 1] range
        posterior = 1.0 / (1.0 + math.exp(-log_odds))
        fused_value = (posterior * 2.0) - 1.0
        fused_confidence = min(1.0, abs(log_odds) / 3.0)  # Confidence from conviction strength

        fused_label = "neutral"
        if fused_value > 0.15:
            fused_label = "positive"
        elif fused_value < -0.15:
            fused_label = "negative"

        return FusionResult(
            signal_name=dimension,
            fused_value=round(fused_value, 4),
            fused_label=fused_label,
            fused_confidence=round(fused_confidence, 4),
            strategy_used=FusionStrategy.BAYESIAN,
            contributors=contributors,
            reasoning=f"Bayesian fusion of {len(evidences)} signals, log_odds={log_odds:.4f}",
        )
