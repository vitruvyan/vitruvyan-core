"""
Orthodoxy Wardens — Verdict Engine

The VerdictEngine is the JUDGE. It takes a collection of Findings
(observations from the Classifier) and renders a Verdict.

It implements the decision logic extracted from:
  - code_analyzer._calculate_risk_level (critical/high/medium count thresholds)
  - inquisitor.generate_compliance_report (weighted scoring)

The engine is pure: (findings, ruleset) → Verdict
No I/O. No network. No database. No side effects.

The judge is never the executioner. — philosophy/charter.md

Sacred Order: Truth & Governance
Layer: Foundational (governance)
"""

from dataclasses import dataclass
from typing import Optional

from ..domain.finding import Finding
from ..domain.verdict import Verdict
from ..domain.log_decision import LogDecision


# =============================================================================
# Scoring Weights — extracted from inquisitor compliance report scoring
# =============================================================================

@dataclass(frozen=True)
class ScoringWeights:
    """
    Configurable weights for violation severity scoring.

    Extracted from inquisitor_agent.py generate_compliance_report():
        critical  × 0.30 penalty per violation
        high      × 0.15 penalty per violation
        medium    × 0.05 penalty per violation
        low       × 0.01 penalty per violation

    The base score starts at 100.0 and is reduced by penalties.
    """

    critical: float = 0.30
    high: float = 0.15
    medium: float = 0.05
    low: float = 0.01

    # Threshold: below this score → heretical
    heretical_threshold: float = 50.0
    # Threshold: below this score → purified (needs attention)
    purified_threshold: float = 80.0
    # Minimum confidence when all rules matched
    min_confidence: float = 0.3
    # Maximum confidence when no issues found
    max_confidence: float = 0.98


DEFAULT_WEIGHTS = ScoringWeights()


# =============================================================================
# VerdictEngine — Core decision engine
# =============================================================================

class VerdictEngine:
    """
    Renders a Verdict from a collection of Findings.

    The engine applies weighted scoring to determine:
    1. A compliance score (0-100)
    2. A status determination (blessed/purified/heretical/non_liquet)
    3. A confidence level (0.0-1.0)
    4. A LogDecision (should this verdict be persisted?)

    Usage:
        from ..governance.classifier import classify_text
        from ..governance.rule import DEFAULT_RULESET

        findings = classify_text("override safety check now", DEFAULT_RULESET)
        engine = VerdictEngine()
        verdict = engine.render(findings, DEFAULT_RULESET)
        log_decision = engine.decide_logging(verdict)
    """

    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.weights = weights or DEFAULT_WEIGHTS

    def render(
        self,
        findings: tuple,
        ruleset,
        confession_id: Optional[str] = None,
    ) -> Verdict:
        """
        Render a Verdict from Findings.

        Args:
            findings: Tuple of Finding objects from Classifier
            ruleset: The RuleSet that was used (for version tagging)
            confession_id: Optional reference to triggering Confession

        Returns:
            Verdict object with status, confidence, and findings attached
        """
        # Count by severity
        counts = self._count_by_severity(findings)
        critical = counts.get("critical", 0)
        high = counts.get("high", 0)
        medium = counts.get("medium", 0)
        low = counts.get("low", 0)
        total_findings = len(findings)

        # Calculate compliance score (100 base, subtract penalties)
        score = self._calculate_score(counts)

        # Determine status
        status = self._determine_status(score, counts)

        # Calculate confidence
        confidence = self._calculate_confidence(total_findings, ruleset)

        # Build a human-readable explanation
        explanation = self._build_message(status, score, counts)

        # Create Verdict using domain factory methods
        if status == "blessed":
            return Verdict.blessed(
                findings=findings,
                confidence=confidence,
                explanation=explanation,
                ruleset_version=ruleset.version_tag,
            )
        elif status == "purified":
            return Verdict.purified(
                findings=findings,
                confidence=confidence,
                explanation=explanation,
                ruleset_version=ruleset.version_tag,
            )
        elif status == "heretical":
            return Verdict.heretical(
                findings=findings,
                confidence=confidence,
                explanation=explanation,
                ruleset_version=ruleset.version_tag,
            )
        else:
            # non_liquet — insufficient data to decide
            return Verdict.non_liquet(
                findings=findings,
                confidence=confidence,
                what_we_know=(f"Score: {score:.1f}/100", f"{total_findings} finding(s)"),
                what_is_uncertain=("Insufficient rules or coverage for definitive judgment",),
                uncertainty_sources=("limited_ruleset", "pattern_coverage"),
                best_guess=status,
                ruleset_version=ruleset.version_tag,
            )

    def decide_logging(self, verdict: Verdict) -> LogDecision:
        """
        Decide whether a Verdict should be logged and at what level.

        Extracted from chronicler_agent decision logic.
        The Chronicler is now a LogDecision engine — it decides,
        the service layer executes the actual persistence.

        Args:
            verdict: Verdict to evaluate

        Returns:
            LogDecision indicating whether/how to log
        """
        if verdict.status == "heretical":
            return LogDecision.critical_audit(
                category="orthodoxy.heretical",
                reason=(
                    f"Heretical verdict: {verdict.critical_count} critical, "
                    f"{len(verdict.findings)} total findings"
                ),
            )
        elif verdict.status == "purified":
            return LogDecision.standard(
                category="orthodoxy.purified",
                reason=(
                    f"Purified verdict: {len(verdict.findings)} findings, "
                    f"confidence {verdict.confidence:.2f}"
                ),
            )
        elif verdict.status == "blessed" and len(verdict.findings) == 0:
            return LogDecision.skip(
                reason="Clean blessed verdict — no findings to log"
            )
        else:
            # blessed with minor findings or non_liquet
            return LogDecision.standard(
                category=f"orthodoxy.{verdict.status}",
                reason=f"{len(verdict.findings)} finding(s), confidence {verdict.confidence:.2f}",
            )

    # ─────────────────────────────────────────────────────────────
    # Private scoring methods
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _count_by_severity(findings: tuple) -> dict:
        """Count findings by severity level."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in findings:
            if f.severity in counts:
                counts[f.severity] += 1
        return counts

    def _calculate_score(self, counts: dict) -> float:
        """
        Calculate compliance score from 100 base.

        Extracted from inquisitor_agent.generate_compliance_report:
        score = 100 - Σ(count_i × weight_i × 100)
        """
        penalty = (
            counts.get("critical", 0) * self.weights.critical
            + counts.get("high", 0) * self.weights.high
            + counts.get("medium", 0) * self.weights.medium
            + counts.get("low", 0) * self.weights.low
        ) * 100

        return max(0.0, 100.0 - penalty)

    def _determine_status(self, score: float, counts: dict) -> str:
        """
        Determine verdict status from score and findings.

        Logic extracted from code_analyzer._calculate_risk_level:
        - Any critical finding → heretical (regardless of score)
        - Score < heretical_threshold → heretical
        - Score < purified_threshold → purified
        - No findings → blessed
        - Otherwise → blessed (with findings attached)
        """
        # Hard rule: any critical → heretical
        if counts.get("critical", 0) > 0:
            return "heretical"

        # Score-based determination
        if score < self.weights.heretical_threshold:
            return "heretical"
        elif score < self.weights.purified_threshold:
            return "purified"
        else:
            return "blessed"

    def _calculate_confidence(self, finding_count: int, ruleset) -> float:
        """
        Calculate confidence in the verdict.

        Higher confidence when:
        - More rules matched (more data points)
        - RuleSet has good coverage

        Lower confidence when:
        - Very few rules active (small ruleset)
        - No findings at all (could mean clean OR poor rules)
        """
        active = ruleset.active_count
        if active == 0:
            return self.weights.min_confidence

        # Base confidence from rule coverage
        if finding_count == 0:
            # No findings: confidence depends on how many rules checked
            # More rules checked with no findings → higher confidence
            coverage_factor = min(active / 30.0, 1.0)  # 30+ rules = full coverage
            return 0.5 + coverage_factor * (self.weights.max_confidence - 0.5)
        else:
            # Findings present: confidence depends on finding/rule ratio
            ratio = min(finding_count / active, 1.0)
            return 0.6 + ratio * (self.weights.max_confidence - 0.6)

    @staticmethod
    def _build_message(status: str, score: float, counts: dict) -> str:
        """Build human-readable verdict summary."""
        parts = [f"Status: {status}, Score: {score:.1f}/100"]

        issue_parts = []
        for sev in ("critical", "high", "medium", "low"):
            count = counts.get(sev, 0)
            if count > 0:
                issue_parts.append(f"{count} {sev}")

        if issue_parts:
            parts.append(f"Issues: {', '.join(issue_parts)}")
        else:
            parts.append("No issues found")

        return " | ".join(parts)
