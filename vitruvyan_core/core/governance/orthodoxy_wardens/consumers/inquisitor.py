"""
Orthodoxy Wardens — Inquisitor (Sacred Role)

The Inquisitor is the EXAMINER of the tribunal.
It takes a Confession and the text/code to examine, applies the governance
engine (LLMClassifier + ASTClassifier), and produces Findings.

The Inquisitor does NOT render a verdict — it gathers evidence.

Input:  Confession + text/code to examine
Output: tuple[Finding, ...]

Extracted from: inquisitor_agent.py (compliance_check, pattern matching)

Sacred Order: Truth & Governance
Layer: Foundational (consumers)
"""

import uuid
from typing import Any, Optional, Tuple

from .base import SacredRole
from ..domain.confession import Confession
from ..domain.finding import Finding
from ..governance import (
    PatternClassifier,
    ASTClassifier,
    RuleSet,
    DEFAULT_RULESET,
    classify_text,
)
from ..governance.llm_classifier import LLMClassifier


class InquisitorResult:
    """
    Immutable result of an Inquisitor examination.

    Bundles findings with metadata about the examination process.
    """

    __slots__ = (
        "_confession_id",
        "_findings",
        "_rules_applied",
        "_text_examined",
        "_code_examined",
        "_llm_available",
    )

    def __init__(
        self,
        confession_id: str,
        findings: Tuple[Finding, ...],
        rules_applied: int,
        text_examined: bool,
        code_examined: bool,
        llm_available: bool = True,
    ):
        object.__setattr__(self, "_confession_id", confession_id)
        object.__setattr__(self, "_findings", findings)
        object.__setattr__(self, "_rules_applied", rules_applied)
        object.__setattr__(self, "_text_examined", text_examined)
        object.__setattr__(self, "_code_examined", code_examined)
        object.__setattr__(self, "_llm_available", llm_available)

    def __setattr__(self, name, value):
        raise AttributeError("InquisitorResult is frozen")

    @property
    def confession_id(self) -> str:
        return self._confession_id

    @property
    def findings(self) -> Tuple[Finding, ...]:
        return self._findings

    @property
    def rules_applied(self) -> int:
        return self._rules_applied

    @property
    def text_examined(self) -> bool:
        return self._text_examined

    @property
    def code_examined(self) -> bool:
        return self._code_examined

    @property
    def llm_available(self) -> bool:
        return self._llm_available

    @property
    def has_violations(self) -> bool:
        return any(f.finding_type == "violation" for f in self._findings)

    @property
    def has_critical(self) -> bool:
        return any(f.severity == "critical" for f in self._findings)

    @property
    def finding_count(self) -> int:
        return len(self._findings)

    @property
    def violations(self) -> Tuple[Finding, ...]:
        return tuple(f for f in self._findings if f.finding_type == "violation")

    @property
    def warnings(self) -> Tuple[Finding, ...]:
        return tuple(f for f in self._findings if f.finding_type == "warning")

    def findings_by_category(self, category: str) -> Tuple[Finding, ...]:
        return tuple(f for f in self._findings if f.category == category)

    def findings_by_severity(self, severity: str) -> Tuple[Finding, ...]:
        return tuple(f for f in self._findings if f.severity == severity)

    def __repr__(self) -> str:
        return (
            f"InquisitorResult(confession='{self._confession_id}', "
            f"findings={self.finding_count}, violations={len(self.violations)})"
        )


class Inquisitor(SacredRole):
    """
    Examiner — applies governance rules to produce Findings.

    The Inquisitor receives a Confession plus the content to examine,
    and applies LLMClassifier (for text) and ASTClassifier (for code)
    to produce a tuple of Findings.

    Configuration:
        ruleset: RuleSet to use (default: DEFAULT_RULESET)
        examine_code: Whether to apply AST analysis (default: True)

    Usage:
        inquisitor = Inquisitor()
        result = inquisitor.process({
            "confession": confession,
            "text": "some output to examine",
            "code": "import os; os.system('rm -rf /')"
        })
        # result.findings → tuple of Findings
    """

    def __init__(
        self,
        ruleset: Optional[RuleSet] = None,
        examine_code: bool = True,
    ):
        self._ruleset = ruleset or DEFAULT_RULESET
        self._examine_code = examine_code
        self._llm_classifier = LLMClassifier()
        self._ast_classifier = ASTClassifier() if examine_code else None

    @property
    def role_name(self) -> str:
        return "inquisitor"

    @property
    def description(self) -> str:
        return "Examiner: applies governance rules to text/code, produces Findings"

    @property
    def ruleset(self) -> RuleSet:
        return self._ruleset

    def can_handle(self, event: Any) -> bool:
        """
        Accept dicts containing a 'confession' or 'text' key,
        or a Confession directly.
        """
        if isinstance(event, Confession):
            return True
        if isinstance(event, dict):
            return "confession" in event or "text" in event or "code" in event
        return False

    def process(self, event: Any) -> InquisitorResult:
        """
        Examine content and produce Findings.

        Args:
            event: dict with keys:
                - confession: Confession (required for ID tracking)
                - text: str (text to examine, e.g. LLM output)
                - code: str (Python source to examine via AST)
              OR a Confession directly (examines metadata as text)

        Returns:
            InquisitorResult with all findings
        """
        if isinstance(event, Confession):
            return self._examine(
                confession_id=event.confession_id,
                text=str(event.metadata) if event.metadata else "",
                code=None,
            )

        if not isinstance(event, dict):
            raise ValueError(
                f"Inquisitor expects dict or Confession, got {type(event).__name__}"
            )

        confession = event.get("confession")
        confession_id = (
            confession.confession_id
            if isinstance(confession, Confession)
            else event.get("confession_id", "unknown")
        )

        text = event.get("text", "")
        code = event.get("code")

        return self._examine(
            confession_id=confession_id,
            text=text,
            code=code,
        )

    def set_llm_agent(self, llm_agent) -> None:
        """Inject LLMAgent at service-layer boot."""
        self._llm_classifier.set_llm_agent(llm_agent)

    def _examine(
        self,
        confession_id: str,
        text: str,
        code: Optional[str],
    ) -> InquisitorResult:
        """Core examination logic — LLM-first, no regex."""
        all_findings = []
        text_examined = False
        code_examined = False
        llm_available = True

        # --- Text examination (LLMClassifier — primary, semantic) ---
        if text and text.strip():
            llm_findings, llm_available = self._llm_classifier.classify(text)
            all_findings.extend(llm_findings)
            text_examined = True

        # --- Code examination (ASTClassifier — structural, deterministic) ---
        if code and code.strip() and self._ast_classifier is not None:
            try:
                code_findings = self._ast_classifier.classify(code)
                all_findings.extend(code_findings)
                code_examined = True
            except SyntaxError:
                all_findings.append(
                    Finding(
                        finding_id=f"ast_{uuid.uuid4().hex[:8]}",
                        finding_type="warning",
                        severity="medium",
                        category="quality",
                        message="Code could not be parsed for AST analysis (SyntaxError)",
                        source_rule="ast.syntax_check",
                        context=(("code_length", len(code)),),
                    )
                )
                code_examined = True

        return InquisitorResult(
            confession_id=confession_id,
            findings=tuple(all_findings),
            rules_applied=self._ruleset.active_count,
            text_examined=text_examined,
            code_examined=code_examined,
            llm_available=llm_available,
        )
