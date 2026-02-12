"""
VEE Engine 3.0 — Vitruvyan Explainability Engine

Domain-agnostic orchestrator for multi-level explainability.
All domain semantics injected via ExplainabilityProvider contract.

Pipeline:
  1. Analyze   → VEEAnalyzer  (normalize, signal, pattern detection)
  2. Generate  → VEEGenerator (template-based narrative from provider)
  3. Enrich    → VEEMemory    (historical context enrichment)
  4. Store     → VEEMemory    (persistence for future enrichment)
  5. Format    → Output       (dict-compatible output)

Contains ZERO domain knowledge. No default providers.
Callers MUST supply an ExplainabilityProvider — no assumptions about domain.
"""

import logging
from typing import Dict, List, Any, Optional

from .types import AnalysisResult, ExplanationLevels
from .vee_analyzer import VEEAnalyzer
from .vee_generator import VEEGenerator
from .vee_memory_adapter import VEEMemoryAdapter

logger = logging.getLogger(__name__)

# Optional VSGS metrics (non-critical)
try:
    from core.monitoring.vsgs_metrics import record_vee_generation
except ImportError:
    def record_vee_generation(**kwargs):
        pass


class VEEEngine:
    """
    Vitruvyan Explainability Engine 3.0

    Domain-agnostic pipeline. Requires an ExplainabilityProvider.
    No defaults, no fallbacks to any specific domain.
    """

    def __init__(self, auto_store: bool = True, use_memory: bool = True,
                 domain_tag: str = ""):
        self.analyzer = VEEAnalyzer()
        self.generator = VEEGenerator()
        self.memory = VEEMemoryAdapter(domain_tag=domain_tag)
        self.auto_store = auto_store
        self.use_memory = use_memory
        logger.info("VEE Engine 3.0 initialized (domain_tag=%s)", domain_tag)

    def explain(self, entity_id: str, metrics: Dict[str, Any],
                provider, profile: Optional[Dict[str, Any]] = None,
                semantic_context: Optional[List[Dict[str, Any]]] = None
                ) -> Dict[str, str]:
        """Standard explanation — returns dict compatible with existing system.

        Args:
            entity_id: Entity being explained
            metrics: Raw metrics dict {metric_name: value}
            provider: ExplainabilityProvider instance (REQUIRED)
            profile: Optional user profile for level adaptation
            semantic_context: Optional VSGS semantic matches
        """
        try:
            analysis = self.analyzer.analyze(entity_id, metrics, provider)
            explanations = self.generator.generate(
                analysis, provider, profile, semantic_context)

            if self.use_memory:
                explanations = self._enrich(entity_id, analysis, explanations)

            if self.auto_store:
                self._store(analysis, explanations)

            record_vee_generation(
                entity_id=entity_id,
                intensity=analysis.overall_intensity,
                confidence=analysis.overall_confidence,
            )

            return self._format(explanations)
        except Exception as e:
            logger.error(f"VEE explain failed for {entity_id}: {e}")
            return self._fallback(entity_id, str(e))

    def explain_comprehensive(self, entity_id: str, metrics: Dict[str, Any],
                              provider,
                              profile: Optional[Dict[str, Any]] = None,
                              semantic_context: Optional[List[Dict[str, Any]]] = None
                              ) -> Dict[str, Any]:
        """Full explanation with analysis metadata for API/debug use."""
        try:
            analysis = self.analyzer.analyze(entity_id, metrics, provider)
            explanations = self.generator.generate(
                analysis, provider, profile, semantic_context)

            historical = []
            if self.use_memory:
                historical = self._get_historical(entity_id)
                explanations = self.memory.enrich(explanations, historical)

            if self.auto_store:
                self._store(analysis, explanations)

            return {
                "summary": explanations.summary,
                "technical": explanations.technical,
                "detailed": explanations.detailed,
                "analysis": {
                    "signals": analysis.signals,
                    "dominant_factors": [
                        {"factor": f, "strength": s}
                        for f, s in analysis.dominant_factors
                    ],
                    "direction": analysis.direction,
                    "overall_intensity": analysis.overall_intensity,
                    "confidence": analysis.confidence,
                    "patterns": analysis.patterns,
                    "anomalies": analysis.anomalies,
                },
                "metadata": {
                    "profile_adapted": explanations.profile_adapted,
                    "confidence_note": explanations.confidence_note,
                    "timestamp": explanations.timestamp.isoformat(),
                    "historical_count": len(historical),
                    "metrics_count": analysis.metrics_count,
                    "missing_dimensions": analysis.missing_dimensions,
                },
                "context": {
                    "contextualized": explanations.contextualized,
                    "historical_reference": explanations.historical_reference,
                    "semantic_grounded": explanations.semantic_grounded,
                    "epistemic_trace": explanations.epistemic_trace,
                },
            }
        except Exception as e:
            logger.error(f"VEE comprehensive failed for {entity_id}: {e}")
            return {
                "summary": f"Analysis unavailable: {e}",
                "technical": "",
                "detailed": "",
            }

    def analyze_only(self, entity_id: str, metrics: Dict[str, Any],
                     provider) -> AnalysisResult:
        """Run analysis phase only (no generation/storage)."""
        return self.analyzer.analyze(entity_id, metrics, provider)

    # ── Internal pipeline steps ──────────────────────────────────────────────

    def _enrich(self, entity_id: str, analysis: AnalysisResult,
                explanations: ExplanationLevels) -> ExplanationLevels:
        """Phase 3: Enrich with historical context."""
        try:
            historical = self.memory.retrieve(entity_id)
            if historical:
                explanations = self.memory.enrich(explanations, historical)
                logger.debug("Enriched %s with %d historical refs",
                             entity_id, len(historical))
        except Exception as e:
            logger.warning(f"Memory enrichment failed: {e}")
        return explanations

    def _get_historical(self, entity_id: str):
        """Get historical explanations for comprehensive mode."""
        try:
            return self.memory.retrieve(entity_id)
        except Exception:
            return []

    def _store(self, analysis: AnalysisResult,
               explanations: ExplanationLevels):
        """Phase 4: Persist explanation."""
        try:
            self.memory.store(analysis, explanations)
        except Exception as e:
            logger.warning(f"Storage failed: {e}")

    def _format(self, explanations: ExplanationLevels) -> Dict[str, str]:
        """Phase 5: Format for system compatibility."""
        result = {
            "summary": explanations.summary,
            "technical": explanations.technical,
            "detailed": explanations.detailed,
        }
        if explanations.contextualized:
            result["contextualized"] = explanations.contextualized
        if explanations.semantic_grounded:
            result["semantic_grounded"] = explanations.semantic_grounded
        if explanations.epistemic_trace:
            result["epistemic_trace"] = ", ".join(explanations.epistemic_trace)
        return result

    def _fallback(self, entity_id: str, error: str) -> Dict[str, str]:
        """Deterministic fallback on failure."""
        return {
            "summary": f"Analysis of {entity_id} unavailable: {error}",
            "technical": f"Error processing metrics: {error}",
            "detailed": (f"VEE encountered an error for {entity_id}. "
                         f"Details: {error}. Retry later."),
        }
