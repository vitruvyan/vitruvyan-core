"""
Orthodoxy Wardens — LLM Classifier

LLM-first semantic classification. Zero regex. Follows the Nuclear Option:
"LLM (primary, ~95% accuracy) → non_liquet fallback (degraded, honest uncertainty)"

When the LLM is unavailable the classifier returns an empty Finding tuple and
signals uncertainty — the VerdictEngine then renders non_liquet rather than
pretending regex patterns could do the job.

The classifier asks the LLM to analyze text for governance categories
(security, performance, quality, hallucination) and returns typed Findings
with severity, category, and explanations. The prompt is structured to
produce deterministic JSON output.

Sacred Order: Truth & Governance
Layer: Foundational (governance)
Pure domain: imports LLMAgent for TYPE HINT only. Actual instance is
injected via set_llm_agent() at service-layer boot.

Created: Mar 08, 2026
"""

import json
import logging
import uuid
from typing import Optional, Tuple, Dict, Any, List

from ..domain.finding import Finding

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — the LLM's role as semantic auditor
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an epistemic governance auditor for the Vitruvyan OS.
Your task is to analyze text (LLM outputs, code, narratives) for governance issues.

Analyze the text for these categories:
- **security**: Exposed credentials, injection patterns, unsafe commands, secrets in output, data leakage
- **performance**: Unbounded operations, memory leaks, N+1 patterns, missing pagination
- **quality**: Incomplete implementations, bare exception handlers, debug artifacts left in output
- **hallucination**: Fabricated data, false certainty about unknowns, invented citations, contradictions

For each issue found, provide:
- severity: "critical" | "high" | "medium" | "low"
- category: one of the four above
- message: concise description of the issue
- evidence: the relevant excerpt from the text (max 100 chars)

Respond ONLY with a JSON object:
{
  "findings": [
    {
      "severity": "critical",
      "category": "security",
      "message": "Hardcoded database password exposed in output",
      "evidence": "password = \"admin123\""
    }
  ]
}

If the text has NO governance issues, respond: {"findings": []}
Be precise. Do not hallucinate issues. Only report real problems you can evidence."""


# ---------------------------------------------------------------------------
# LLMClassifier
# ---------------------------------------------------------------------------

class LLMClassifier:
    """
    Semantic classifier using LLM for governance analysis.

    Replaces PatternClassifier (regex) as the PRIMARY classification engine.
    When LLM is unavailable, returns empty findings and sets a flag so the
    VerdictEngine can render non_liquet (honest uncertainty).

    Usage:
        classifier = LLMClassifier()
        classifier.set_llm_agent(get_llm_agent())

        findings, llm_available = classifier.classify(text)
        if not llm_available:
            # VerdictEngine should render non_liquet
            pass
    """

    def __init__(self):
        self._llm = None

    def set_llm_agent(self, llm_agent) -> None:
        """Inject LLMAgent instance (called at service-layer boot)."""
        self._llm = llm_agent

    @property
    def available(self) -> bool:
        """Whether the LLM is configured and reachable."""
        return self._llm is not None

    def classify(self, text: str) -> Tuple[Tuple[Finding, ...], bool]:
        """
        Classify text using LLM semantic understanding.

        Args:
            text: Content to analyze (LLM output, code, narrative)

        Returns:
            Tuple of (findings, llm_available):
              - findings: Tuple[Finding, ...] — governance issues found
              - llm_available: bool — False means LLM was unavailable,
                caller should treat result as uncertain
        """
        if not text or not text.strip():
            return (), True

        if not self._llm:
            logger.warning("[LLM_CLASSIFIER] LLM not available — returning empty (non_liquet)")
            return (), False

        try:
            prompt = f"Analyze the following text for governance issues:\n\n---\n{text[:3000]}\n---"

            result = self._llm.complete_json(
                prompt=prompt,
                system_prompt=_SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=800,
            )

            findings = self._parse_findings(result)
            return findings, True

        except Exception as e:
            logger.error(f"[LLM_CLASSIFIER] Classification failed: {e}")
            return (), False

    def _parse_findings(self, result: Dict[str, Any]) -> Tuple[Finding, ...]:
        """Parse LLM JSON response into Finding objects."""
        raw_findings = result.get("findings", [])
        if not isinstance(raw_findings, list):
            return ()

        parsed = []
        for item in raw_findings:
            try:
                severity = item.get("severity", "medium")
                category = item.get("category", "quality")
                message = item.get("message", "Unspecified issue")
                evidence = item.get("evidence", "")

                # Validate against Finding's allowed values
                if severity not in ("critical", "high", "medium", "low"):
                    severity = "medium"
                if category not in ("security", "performance", "quality", "hallucination"):
                    category = "quality"

                finding_type = "violation" if severity in ("critical", "high") else "warning"

                parsed.append(Finding(
                    finding_id=str(uuid.uuid4())[:12],
                    finding_type=finding_type,
                    severity=severity,
                    category=category,
                    message=f"[LLM] {message}",
                    source_rule="llm_semantic",
                    context=(
                        ("evidence", str(evidence)[:100]),
                        ("classifier", "llm"),
                    ),
                ))
            except (ValueError, KeyError) as e:
                logger.debug(f"[LLM_CLASSIFIER] Skipping invalid finding: {e}")
                continue

        return tuple(parsed)
