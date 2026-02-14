"""
Orthodoxy Wardens — Rule and RuleSet Domain Objects

Rules are DATA, not behavior. They define WHAT to look for, not HOW to look.
A RuleSet is a frozen, versioned collection of Rules loaded from config.
After creation, a RuleSet is immutable — every verdict references the exact
RuleSet version that produced it, creating a complete audit trail.

Extracted from:
  - code_analyzer.py: compliance_patterns, security_patterns, performance_patterns
  - inquisitor_agent.py: compliance_rules

Sacred Order: Truth & Governance
Layer: Foundational (governance)
"""

from dataclasses import dataclass
from hashlib import sha256
from typing import Optional


# =============================================================================
# Rule — A single compliance/quality/security check definition
# =============================================================================

@dataclass(frozen=True)
class Rule:
    """
    Immutable definition of a single check.

    A Rule says "look for THIS pattern in THAT category and escalate at THIS severity."
    It does NOT execute the check — that's the Classifier's job.

    Attributes:
        rule_id: Unique identifier (e.g., "compliance.prescriptive_language.001")
        category: Domain of the rule
            - "compliance": Regulatory (MiFID, FINRA, prescriptive language)
            - "security": Vulnerability detection (secrets, injection)
            - "performance": Efficiency issues (loops, leaks)
            - "quality": Code quality (long lines, bare except)
            - "data_quality": Missing/impossible values
            - "hallucination": LLM fabrication detection
        subcategory: Finer classification within category
            (e.g., "prescriptive_language", "hardcoded_secrets")
        severity: Finding severity when this rule matches
            - "critical", "high", "medium", "low"
        pattern: Regex pattern string (compiled at match time, not creation)
        description: Human-readable explanation of what this rule catches
        enabled: Whether this rule is active (allows disabling without removal)
    """

    rule_id: str
    category: str
    subcategory: str
    severity: str
    pattern: str
    description: str
    enabled: bool = True

    _VALID_CATEGORIES = frozenset({
        "compliance", "security", "performance",
        "quality", "data_quality", "hallucination",
    })
    _VALID_SEVERITIES = frozenset({"critical", "high", "medium", "low"})

    def __post_init__(self):
        if self.category not in self._VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{self.category}'. "
                f"Must be one of: {self._VALID_CATEGORIES}"
            )
        if self.severity not in self._VALID_SEVERITIES:
            raise ValueError(
                f"Invalid severity '{self.severity}'. "
                f"Must be one of: {self._VALID_SEVERITIES}"
            )


# =============================================================================
# RuleSet — Frozen, versioned collection of Rules
# =============================================================================

@dataclass(frozen=True)
class RuleSet:
    """
    Immutable, versioned collection of Rules.

    After loading from config, a RuleSet NEVER changes. Every Verdict references
    the RuleSet version (checksum) that produced it, enabling full audit replay.

    Attributes:
        version: Human-readable version string (e.g., "v2.3")
        rules: Frozen tuple of Rule objects
        checksum: SHA-256 of serialized rules (computed automatically)
        description: What this ruleset covers
    """

    version: str
    rules: tuple  # Tuple[Rule, ...]
    checksum: str
    description: str = ""

    @classmethod
    def create(cls, version: str, rules: tuple, description: str = "") -> "RuleSet":
        """
        Factory method — computes checksum automatically.

        Usage:
            ruleset = RuleSet.create(
                version="v2.3",
                rules=(rule_1, rule_2, rule_3),
                description="Financial compliance + security rules"
            )
        """
        # Compute deterministic checksum from rule data
        raw = "|".join(
            f"{r.rule_id}:{r.pattern}:{r.severity}:{r.enabled}"
            for r in sorted(rules, key=lambda r: r.rule_id)
        )
        checksum = sha256(raw.encode("utf-8")).hexdigest()[:16]
        return cls(
            version=version,
            rules=rules,
            checksum=checksum,
            description=description,
        )

    @property
    def active_rules(self) -> tuple:
        """Only enabled rules."""
        return tuple(r for r in self.rules if r.enabled)

    @property
    def rule_count(self) -> int:
        return len(self.rules)

    @property
    def active_count(self) -> int:
        return len(self.active_rules)

    def rules_by_category(self, category: str) -> tuple:
        """Get active rules filtered by category."""
        return tuple(r for r in self.active_rules if r.category == category)

    def rules_by_severity(self, severity: str) -> tuple:
        """Get active rules filtered by severity."""
        return tuple(r for r in self.active_rules if r.severity == severity)

    @property
    def version_tag(self) -> str:
        """Version string for Verdict.ruleset_version (includes checksum)."""
        return f"ruleset_{self.version}_{self.checksum}"


# =============================================================================
# DEFAULT RULESET — Extracted from code_analyzer.py + inquisitor_agent.py
# =============================================================================
# These are the BUILT-IN rules. Production deployments can override via config.
# Every rule has a unique ID following: <category>.<subcategory>.<NNN>

def _build_default_rules() -> tuple:
    """Build the default rule set — GENERIC rules only (domain-agnostic).

    Domain-specific compliance rules (finance, healthcare, legal, etc.)
    are loaded via GovernanceRuleRegistry from ``domains/<domain>/governance_rules.py``.
    """
    rules = []

    # ─────────────────────────────────────────────────────────────
    # SECURITY rules (from code_analyzer) — DOMAIN-AGNOSTIC
    # ─────────────────────────────────────────────────────────────
    _security = [
        ("security.secrets.001", r"password\s*=\s*['\"][^'\"]+['\"]",
         "critical", "Hardcoded password"),
        ("security.secrets.002", r"api_key\s*=\s*['\"][^'\"]+['\"]",
         "critical", "Hardcoded API key"),
        ("security.secrets.003", r"secret\s*=\s*['\"][^'\"]+['\"]",
         "critical", "Hardcoded secret"),
        ("security.secrets.004", r"token\s*=\s*['\"][^'\"]+['\"]",
         "critical", "Hardcoded token"),
        ("security.injection.001", r"execute\s*\(\s*['\"].*%s.*['\"]",
         "high", "Potential SQL injection (string interpolation)"),
        ("security.injection.002", r"query\s*=\s*['\"].*\+.*['\"]",
         "high", "Potential SQL injection (string concatenation)"),
        ("security.injection.003", r"SELECT.*\+.*FROM",
         "high", "Potential SQL injection (SELECT concat)"),
        ("security.command.001", r"os\.system\s*\(\s*.*\+",
         "high", "Potential command injection (os.system)"),
        ("security.command.002", r"subprocess\.(call|run|Popen)\s*\(\s*.*\+",
         "high", "Potential command injection (subprocess)"),
    ]
    for rule_id, pattern, severity, desc in _security:
        rules.append(Rule(
            rule_id=rule_id,
            category="security",
            subcategory=rule_id.split(".")[1],
            severity=severity,
            pattern=pattern,
            description=desc,
        ))

    # ─────────────────────────────────────────────────────────────
    # PERFORMANCE rules (from code_analyzer)
    # ─────────────────────────────────────────────────────────────
    _performance = [
        ("performance.loops.001", r"while\s+True\s*:",
         "high", "Infinite loop (while True)"),
        ("performance.loops.002", r"for.*in.*while\s+True",
         "high", "Nested infinite loop"),
        ("performance.leaks.001", r"open\s*\([^)]*\)(?!\s*with)",
         "medium", "File opened without context manager"),
        ("performance.leaks.002", r"connect\s*\([^)]*\)(?!\s*with)",
         "medium", "Connection without context manager"),
        ("performance.style.001", r"for.*in.*range\(len\(",
         "low", "Inefficient iteration (range(len()))"),
        ("performance.style.002", r"time\.sleep\(0\)",
         "low", "Busy wait (sleep(0))"),
    ]
    for rule_id, pattern, severity, desc in _performance:
        rules.append(Rule(
            rule_id=rule_id,
            category="performance",
            subcategory=rule_id.split(".")[1],
            severity=severity,
            pattern=pattern,
            description=desc,
        ))

    # ─────────────────────────────────────────────────────────────
    # QUALITY rules (from code_analyzer — non-regex, marker patterns)
    # ─────────────────────────────────────────────────────────────
    _quality = [
        ("quality.comments.001", r"\b(TODO|FIXME|HACK|XXX)\b",
         "low", "TODO/FIXME marker found"),
        ("quality.logging.001", r"\bprint\s*\(",
         "low", "Print statement (use logging instead)"),
        ("quality.exceptions.001", r"except\s*:",
         "medium", "Bare except clause (catches everything)"),
    ]
    for rule_id, pattern, severity, desc in _quality:
        rules.append(Rule(
            rule_id=rule_id,
            category="quality",
            subcategory=rule_id.split(".")[1],
            severity=severity,
            pattern=pattern,
            description=desc,
        ))

    # ─────────────────────────────────────────────────────────────
    # HALLUCINATION rules — DOMAIN-AGNOSTIC (LLM output validation)
    # ─────────────────────────────────────────────────────────────
    _hallucination = [
        ("hallucination.numeric.001",
         r"\$\s*\d+\s*(trillion|quadrillion)",
         "critical", "Unrealistic monetary figure (trillions+)"),
        ("hallucination.numeric.002",
         r"\b\d{4,}%\s*(growth|return|increase)",
         "high", "Unrealistic percentage (1000%+ growth/return)"),
        ("hallucination.certainty.001",
         r"\b(proven|mathematical certainty|scientifically proven)\b.*\b(outcome|result|prediction)\b",
         "high", "False certainty claim about outcomes"),
    ]
    for rule_id, pattern, severity, desc in _hallucination:
        rules.append(Rule(
            rule_id=rule_id,
            category="hallucination",
            subcategory=rule_id.split(".")[1],
            severity=severity,
            pattern=pattern,
            description=desc,
        ))

    return tuple(rules)


# The canonical default RuleSet — importable as a constant
DEFAULT_RULES: tuple = _build_default_rules()

DEFAULT_RULESET: RuleSet = RuleSet.create(
    version="v1.0",
    rules=DEFAULT_RULES,
    description=(
        "Default Orthodoxy Wardens ruleset (domain-agnostic). "
        "Generic rules only: security (9), performance (6), "
        "quality (3), hallucination (3). Total: 21 rules. "
        "Domain-specific compliance rules loaded via GovernanceRuleRegistry."
    ),
)
