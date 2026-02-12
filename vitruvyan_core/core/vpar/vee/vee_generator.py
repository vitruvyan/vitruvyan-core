"""
VEE Generator 3.0 — Domain-agnostic narrative generation.

Converts AnalysisResult into multi-level natural language explanations
using templates provided by ExplainabilityProvider.

Contains ZERO internal templates. All narrative structures come from the
provider contract. The generator is a pure rendering engine:
  variables = prepare(analysis, provider)
  text = render(provider.templates, variables)
"""

import random
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from .types import AnalysisResult, ExplanationLevels

logger = logging.getLogger(__name__)


class VEEGenerator:
    """Multi-level explanation generator. All templates from provider."""

    def generate(self, analysis: AnalysisResult, provider,
                 profile: Optional[Dict[str, Any]] = None,
                 semantic_context: Optional[List[Dict[str, Any]]] = None
                 ) -> ExplanationLevels:
        """Generate multi-level explanations from analysis result.

        Args:
            analysis: AnalysisResult from VEEAnalyzer
            provider: ExplainabilityProvider with templates
            profile: Optional user profile (expertise level)
            semantic_context: Optional VSGS semantic matches
        """
        try:
            templates = provider.get_explanation_templates()
            variables = self._prepare_variables(analysis, provider)
            level = self._extract_level(profile)

            summary = self._render(
                templates.summary_variants or [templates.summary_template],
                variables)
            technical = self._render(
                templates.technical_variants or [templates.technical_template],
                variables)
            detailed = self._render(
                templates.detailed_variants or [templates.detailed_template],
                variables)
            detailed = self._adapt_for_level(detailed, level, analysis)

            confidence_note = self._confidence_note(analysis.overall_confidence)

            # VSGS semantic grounding
            semantic_grounded = None
            epistemic_trace = None
            if semantic_context:
                semantic_grounded = self._semantic_synthesis(semantic_context)
                epistemic_trace = [
                    m.get("trace_id") for m in semantic_context
                    if m.get("trace_id")
                ]

            return ExplanationLevels(
                entity_id=analysis.entity_id,
                timestamp=datetime.now(),
                summary=summary,
                technical=technical,
                detailed=detailed,
                confidence_note=confidence_note,
                profile_adapted=profile is not None,
                semantic_grounded=semantic_grounded,
                epistemic_trace=epistemic_trace,
            )
        except Exception as e:
            logger.error(f"Generation failed for {analysis.entity_id}: {e}")
            return self._error_explanation(analysis.entity_id, str(e))

    # ── Variable preparation ─────────────────────────────────────────────────

    def _prepare_variables(self, analysis: AnalysisResult,
                           provider) -> Dict[str, Any]:
        """Prepare template variables from analysis result."""
        entity_ref = provider.format_entity_reference(analysis.entity_id)

        signals_text = (", ".join(analysis.signals[:3])
                        if analysis.signals else "mixed signals")

        dominant_factor = analysis.primary_factor

        secondary = [name for name, _ in analysis.dominant_factors[1:3]] \
            if len(analysis.dominant_factors) > 1 else []
        secondary_factors = ", ".join(secondary) if secondary else "secondary factors"

        patterns_text = ""
        if analysis.patterns:
            patterns_text = ("Key patterns: "
                             + ", ".join(analysis.patterns[:2]) + ". ")

        return {
            "entity_id": analysis.entity_id,
            "entity_reference": entity_ref,
            "signals_text": signals_text,
            "dominant_factor": dominant_factor,
            "secondary_factors": secondary_factors,
            "intensity": analysis.overall_intensity,
            "direction": analysis.direction or "neutral",
            "signals_summary": (", ".join(analysis.signals[:2])
                                if len(analysis.signals) > 1 else signals_text),
            "patterns_text": patterns_text,
            "confidence_text": self._confidence_note(analysis.overall_confidence),
        }

    # ── Template rendering ───────────────────────────────────────────────────

    def _render(self, templates: List[str],
                variables: Dict[str, Any]) -> str:
        """Render a randomly-selected template with variables."""
        fallback = "{entity_reference}: analysis pending."
        template = random.choice(templates) if templates else fallback
        try:
            return template.format(**variables)
        except KeyError:
            ref = variables.get("entity_reference",
                                variables.get("entity_id", "Entity"))
            signals = variables.get("signals_text", "analysis pending")
            return f"{ref}: {signals}."

    def _extract_level(self, profile: Optional[Dict[str, Any]]) -> str:
        """Extract user expertise level from profile."""
        if not profile:
            return "intermediate"
        level = profile.get(
            "level", profile.get("expertise", "intermediate")
        ).lower()
        if level in ("beginner", "basic", "novice"):
            return "beginner"
        elif level in ("expert", "advanced", "professional"):
            return "expert"
        return "intermediate"

    def _adapt_for_level(self, text: str, level: str,
                         analysis: AnalysisResult) -> str:
        """Adapt detailed explanation for user expertise level."""
        if level == "expert":
            quantitative = (
                f" Quantitative: intensity {analysis.overall_intensity:.2f}, "
                f"confidence {analysis.overall_confidence:.2f}, "
                f"data coverage: {analysis.metrics_count} metrics."
            )
            return text + quantitative
        return text

    # ── Confidence ───────────────────────────────────────────────────────────

    def _confidence_note(self, confidence: float) -> str:
        """Generate confidence note text."""
        if confidence >= 0.8:
            return "High reliability analysis."
        elif confidence >= 0.6:
            return "Moderate reliability analysis."
        return "Limited reliability analysis."

    # ── VSGS Integration ─────────────────────────────────────────────────────

    def _semantic_synthesis(self,
                            semantic_context: List[Dict[str, Any]]) -> str:
        """Synthesize VSGS semantic grounding context."""
        top = semantic_context[:3]
        parts = [f"Semantically grounded on {len(top)} prior context(s):"]
        for i, match in enumerate(top, 1):
            text = match.get("text", "").strip()[:120]
            score = match.get("score", 0.0)
            parts.append(f"{i}. (similarity: {score:.2f}) \"{text}\"")
        return "\n".join(parts)

    # ── Error fallback ───────────────────────────────────────────────────────

    def _error_explanation(self, entity_id: str,
                           error: str) -> ExplanationLevels:
        """Create error explanation."""
        return ExplanationLevels(
            entity_id=entity_id,
            timestamp=datetime.now(),
            summary=f"Explanation unavailable for {entity_id}: {error}",
            technical="Unable to process analysis data.",
            detailed=f"Technical error during explanation generation: {error}",
            confidence_note="Analysis unavailable.",
        )
