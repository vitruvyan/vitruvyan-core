"""
VEE Analyzer 3.0 — Domain-agnostic metric analysis.

All domain knowledge comes from ExplainabilityProvider:
  - Normalization rules  → provider.get_normalization_rules()
  - Analysis dimensions  → provider.get_analysis_dimensions()
  - Pattern rules        → provider.get_pattern_rules()
  - Intensity weights    → provider.get_intensity_weights()
  - Confidence criteria  → provider.get_confidence_criteria()

This module contains ZERO hardcoded domain concepts.
No kpi_categories, no pattern_rules, no weights, no finance terms.
"""

import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

import numpy as np

from .types import AnalysisResult

logger = logging.getLogger(__name__)


class VEEAnalyzer:
    """Domain-agnostic metric analyzer. All semantics injected via provider."""

    def analyze(self, entity_id: str, metrics: Dict[str, Any],
                provider) -> AnalysisResult:
        """Analyze metrics using provider-defined dimensions and rules.

        Args:
            entity_id: Entity being analyzed
            metrics: Raw metric dict (keys are metric names, values are numbers)
            provider: ExplainabilityProvider instance

        Returns:
            AnalysisResult with signals, factors, patterns, confidence
        """
        if not metrics:
            return self._empty_result(entity_id, "no metrics provided")

        try:
            # Fetch domain configuration from provider
            norm_rules = provider.get_normalization_rules()
            dimensions = provider.get_analysis_dimensions()
            pattern_rules = provider.get_pattern_rules()
            weights = provider.get_intensity_weights()
            criteria = provider.get_confidence_criteria()

            # Phase 1: Normalize all metrics to 0-1
            normalized = self._normalize(metrics, norm_rules)
            if not normalized:
                return self._empty_result(entity_id, "no normalizable metrics")

            # Phase 2: Identify signals by dimension
            signals, strengths = self._identify_signals(normalized, dimensions)

            # Phase 3: Find dominant factors
            dominant = self._find_dominant(normalized, dimensions)

            # Phase 4: Calculate composites
            intensity = self._calc_intensity(strengths, weights)
            direction = self._calc_direction(normalized, dimensions)
            confidence = self._calc_confidence(normalized, signals, criteria)

            # Phase 5: Detect patterns and anomalies
            patterns = self._detect_patterns(normalized, pattern_rules)
            anomalies = self._detect_anomalies(normalized)

            # Missing dimensions
            present = {d.name for d in dimensions
                       if any(k in normalized for k in d.metric_keys)}
            missing = [d.name for d in dimensions if d.name not in present]

            return AnalysisResult(
                entity_id=entity_id,
                timestamp=datetime.now(),
                signals=signals if signals else ["no significant signals"],
                signal_strengths=strengths,
                dominant_factors=dominant,
                overall_intensity=intensity,
                direction=direction,
                confidence=confidence,
                patterns=patterns,
                anomalies=anomalies,
                metrics_count=len([v for v in metrics.values() if v is not None]),
                missing_dimensions=missing,
            )
        except Exception as e:
            logger.error(f"Analysis failed for {entity_id}: {e}")
            return self._empty_result(entity_id, str(e))

    # ── Phase 1: Normalization ───────────────────────────────────────────────

    def _normalize(self, metrics: Dict[str, Any],
                   rules: list) -> Dict[str, float]:
        """Normalize metrics to 0-1 using provider rules."""
        normalized = {}
        for key, value in metrics.items():
            if value is None:
                continue
            try:
                val = float(value)
            except (ValueError, TypeError):
                continue

            rule = self._find_rule(key, rules)
            if rule:
                n = self._apply_rule(val, rule)
            else:
                n = self._generic_normalize(val)

            normalized[key] = max(0.0, min(1.0, n))
        return normalized

    def _find_rule(self, key: str, rules: list):
        """Find normalization rule matching a metric key by substring."""
        for rule in rules:
            if rule.metric_pattern in key:
                return rule
        return None

    def _apply_rule(self, value: float, rule) -> float:
        """Apply a normalization rule to a raw value."""
        if rule.method == "zscore_tanh":
            n = (np.tanh(value / 2) + 1) / 2
        elif rule.method == "linear_100":
            n = min(1.0, abs(value) / 100.0) if abs(value) > 1 else abs(value)
        elif rule.method == "linear_custom":
            span = rule.max_value - rule.min_value
            n = (value - rule.min_value) / span if span > 0 else 0.5
        elif rule.method == "sigmoid":
            n = 1 / (1 + np.exp(-value / 10))
        else:
            n = self._generic_normalize(value)

        return (1.0 - n) if rule.invert else n

    def _generic_normalize(self, value: float) -> float:
        """Fallback normalization for metrics without explicit rules."""
        v = abs(value)
        if v <= 1:
            return v
        elif v <= 100:
            return v / 100.0
        else:
            return min(1.0, v / 1000.0)

    # ── Phase 2: Signal identification ───────────────────────────────────────

    def _identify_signals(self, normalized: Dict[str, float],
                          dimensions: list) -> Tuple[List[str], Dict[str, float]]:
        """Identify signals per analysis dimension."""
        signals = []
        strengths = {}

        for dim in dimensions:
            values = [normalized[k] for k in dim.metric_keys if k in normalized]
            if not values:
                continue

            avg = float(np.mean(values))
            peak = float(max(values))

            if peak >= 0.8:
                intensity_label = "strong"
                strength = peak
            elif peak >= 0.6:
                intensity_label = "moderate"
                strength = avg
            elif peak >= 0.3:
                intensity_label = "weak"
                strength = avg
            else:
                continue

            # Direction hint based on dimension semantics
            if dim.direction == "higher_better":
                qualifier = "positive" if avg > 0.6 else ("negative" if avg < 0.4 else "neutral")
            elif dim.direction == "lower_better":
                qualifier = "positive" if avg < 0.4 else ("negative" if avg > 0.6 else "neutral")
            else:
                qualifier = "notable"

            signals.append(f"{intensity_label} {qualifier} {dim.display_name}")
            strengths[dim.name] = strength

        return signals, strengths

    # ── Phase 3: Dominant factors ────────────────────────────────────────────

    def _find_dominant(self, normalized: Dict[str, float],
                       dimensions: list) -> List[Tuple[str, float]]:
        """Find dominant factors with co-dominance support."""
        dim_strengths = []

        for dim in dimensions:
            values = [normalized[k] for k in dim.metric_keys if k in normalized]
            if not values:
                continue
            strength = float(max(values))
            dim_strengths.append((dim.display_name, strength))

        if not dim_strengths:
            return [("unknown", 0.0)]

        dim_strengths.sort(key=lambda x: x[1], reverse=True)

        # Co-dominance: include all factors within 10% of the top
        top = dim_strengths[0][1]
        threshold = top * 0.9
        dominant = [(n, s) for n, s in dim_strengths if s >= threshold]

        return dominant if dominant else [dim_strengths[0]]

    # ── Phase 4: Composites ──────────────────────────────────────────────────

    def _calc_intensity(self, strengths: Dict[str, float],
                        weights: Dict[str, float]) -> float:
        """Calculate weighted overall intensity."""
        if not strengths:
            return 0.0

        weighted_sum = 0.0
        total_weight = 0.0
        for dim_name, strength in strengths.items():
            w = weights.get(dim_name, 1.0)
            weighted_sum += strength * w
            total_weight += w

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _calc_direction(self, normalized: Dict[str, float],
                        dimensions: list) -> Optional[str]:
        """Calculate overall direction from dimension semantics."""
        positive = 0
        negative = 0

        for dim in dimensions:
            values = [normalized[k] for k in dim.metric_keys if k in normalized]
            if not values:
                continue
            avg = float(np.mean(values))

            if dim.direction == "higher_better":
                if avg > 0.6:
                    positive += 1
                elif avg < 0.4:
                    negative += 1
            elif dim.direction == "lower_better":
                if avg < 0.4:
                    positive += 1
                elif avg > 0.6:
                    negative += 1

        if positive > negative + 1:
            return "positive"
        elif negative > positive + 1:
            return "negative"
        return "neutral"

    def _calc_confidence(self, normalized: Dict[str, float],
                         signals: List[str], criteria) -> Dict[str, float]:
        """Calculate multi-dimensional confidence."""
        conf = {}

        # Data completeness
        n = len(normalized)
        if n >= criteria.min_metrics_high:
            conf["data_completeness"] = 0.9
        elif n >= criteria.min_metrics_moderate:
            conf["data_completeness"] = 0.7
        else:
            conf["data_completeness"] = 0.4

        # Signal clarity
        s = len(signals)
        if s >= criteria.min_signals_high:
            conf["signal_clarity"] = 0.85
        elif s >= 1:
            conf["signal_clarity"] = 0.6
        else:
            conf["signal_clarity"] = 0.3

        # Value consistency
        values = list(normalized.values())
        if values:
            std = float(np.std(values))
            if std < criteria.consistency_threshold:
                conf["consistency"] = 0.9
            elif std < 0.4:
                conf["consistency"] = 0.7
            else:
                conf["consistency"] = 0.5
        else:
            conf["consistency"] = 0.0

        # Overall
        conf["overall"] = float(np.mean(list(conf.values())))
        return conf

    # ── Phase 5: Patterns & anomalies ────────────────────────────────────────

    def _detect_patterns(self, normalized: Dict[str, float],
                         pattern_rules: list) -> List[str]:
        """Detect patterns using provider-defined rules."""
        patterns = []
        for rule in pattern_rules:
            try:
                if rule.condition and rule.condition(normalized):
                    patterns.append(rule.display_text)
            except Exception:
                continue
        return patterns

    def _detect_anomalies(self, normalized: Dict[str, float]) -> List[str]:
        """Detect statistical anomalies (domain-agnostic, pure math)."""
        anomalies = []
        values = list(normalized.values())
        keys = list(normalized.keys())
        if len(values) < 3:
            return anomalies

        mean = float(np.mean(values))
        std = float(np.std(values))
        if std < 0.05:
            return anomalies

        for i, (key, value) in enumerate(zip(keys, values)):
            if abs(value - mean) > 2 * std:
                label = "unusually high" if value > mean else "unusually low"
                anomalies.append(f"{key} is {label}")

        return anomalies

    # ── Empty result ─────────────────────────────────────────────────────────

    def _empty_result(self, entity_id: str, reason: str) -> AnalysisResult:
        """Create empty result for missing/invalid data."""
        return AnalysisResult(
            entity_id=entity_id,
            timestamp=datetime.now(),
            signals=[reason],
            signal_strengths={},
            dominant_factors=[("unknown", 0.0)],
            overall_intensity=0.0,
            confidence={"overall": 0.0},
            metrics_count=0,
            missing_dimensions=[reason],
        )
