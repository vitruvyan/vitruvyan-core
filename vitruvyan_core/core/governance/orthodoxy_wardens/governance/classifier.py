"""
Orthodoxy Wardens — Pattern Classifier

The Classifier is the workhorse of the governance engine.
It takes TEXT and a RULESET, matches patterns, and produces FINDINGS.
It decides NOTHING — it merely OBSERVES. The VerdictEngine decides.

Pure function: (text, ruleset) → tuple[Finding, ...]
No I/O. No network. No database. No side effects.

Extracted from:
  - code_analyzer.py: _check_compliance, _check_security, _check_performance,
                       _check_code_quality, _check_ast_structure
  - inquisitor_agent.py: _validate_with_patterns

Sacred Order: Truth & Governance
Layer: Foundational (governance)
"""

import ast
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from ..domain.finding import Finding


# =============================================================================
# PatternClassifier — Regex-based classification
# =============================================================================

class PatternClassifier:
    """
    Classifies text against a RuleSet, producing Findings.

    This is the ONLY class that compiles and matches regex patterns.
    It is stateless — the same (text, ruleset) always produces the same Findings.

    Usage:
        from ..governance.rule import DEFAULT_RULESET

        classifier = PatternClassifier()
        findings = classifier.classify("buy now AAPL guaranteed returns", DEFAULT_RULESET)
        # → tuple of Finding objects for each matched rule
    """

    def classify(self, text: str, ruleset) -> tuple:
        """
        Match all active rules against text.

        Args:
            text: Content to analyze (LLM output, code, narrative)
            ruleset: RuleSet containing rules to apply

        Returns:
            Tuple of Finding objects for every matched rule.
            Empty tuple if no rules match (clean text).
        """
        findings = []
        for rule in ruleset.active_rules:
            try:
                matches = re.findall(rule.pattern, text, re.IGNORECASE)
            except re.error:
                # Invalid regex in rule definition → report as anomaly
                findings.append(Finding(
                    finding_id=str(uuid.uuid4())[:12],
                    finding_type="anomaly",
                    severity="medium",
                    category="quality",
                    message=f"Invalid regex in rule {rule.rule_id}: {rule.pattern}",
                    source_rule=rule.rule_id,
                    context=(
                        ("error_type", "invalid_regex"),
                        ("pattern", rule.pattern),
                    ),
                ))
                continue

            if matches:
                # Create one Finding per matched rule (not per match instance)
                context_entries = [
                    ("match_count", str(len(matches))),
                    ("first_match", str(matches[0])[:100]),
                    ("pattern", rule.pattern),
                    ("rule_description", rule.description),
                ]

                # Determine finding_type from severity
                finding_type = (
                    "violation" if rule.severity in ("critical", "high")
                    else "warning"
                )

                findings.append(Finding(
                    finding_id=str(uuid.uuid4())[:12],
                    finding_type=finding_type,
                    severity=rule.severity,
                    category=rule.category,
                    message=(
                        f"[{rule.rule_id}] {rule.description}: "
                        f"{len(matches)} occurrence(s) found"
                    ),
                    source_rule=rule.rule_id,
                    context=tuple(context_entries),
                ))

        return tuple(findings)

    def classify_by_category(
        self, text: str, ruleset, category: str
    ) -> tuple:
        """Classify text against rules of a specific category only."""
        from .rule import RuleSet  # Avoid circular at module load

        filtered_rules = ruleset.rules_by_category(category)
        if not filtered_rules:
            return ()

        # Build a temporary RuleSet with filtered rules
        filtered_set = RuleSet.create(
            version=ruleset.version,
            rules=filtered_rules,
            description=f"Filtered: {category} only",
        )
        return self.classify(text, filtered_set)


# =============================================================================
# ASTClassifier — AST-based structural analysis (Python code only)
# =============================================================================

class ASTClassifier:
    """
    Classifies Python source code structural issues via AST analysis.

    Extracted from code_analyzer._check_ast_structure.
    Catches things regex cannot: eval/exec usage, excessive function complexity,
    global variable mutation.

    No I/O. Takes source code string, returns Findings.
    """

    # Configurable thresholds
    MAX_FUNCTION_ARGS: int = 6
    MAX_NESTING_DEPTH: int = 4

    def classify(self, source_code: str) -> tuple:
        """
        Analyze Python source code AST for structural issues.

        Args:
            source_code: Raw Python source code string

        Returns:
            Tuple of Finding objects for structural issues found.
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return (Finding(
                finding_id=str(uuid.uuid4())[:12],
                finding_type="anomaly",
                severity="medium",
                category="quality",
                message=f"Syntax error prevents AST analysis: {e}",
                source_rule="ast.syntax.error",
                context=(("line", str(e.lineno or 0)),),
            ),)

        findings = []

        for node in ast.walk(tree):
            # Check for eval/exec usage
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name in ("eval", "exec"):
                    findings.append(Finding(
                        finding_id=str(uuid.uuid4())[:12],
                        finding_type="violation",
                        severity="critical",
                        category="security",
                        message=(
                            f"Dangerous function '{func_name}()' used "
                            f"at line {node.lineno}"
                        ),
                        source_rule=f"ast.dangerous_call.{func_name}",
                        context=(
                            ("line", str(node.lineno)),
                            ("function", func_name),
                        ),
                    ))

            # Check for global variable mutation
            if isinstance(node, ast.Global):
                findings.append(Finding(
                    finding_id=str(uuid.uuid4())[:12],
                    finding_type="warning",
                    severity="medium",
                    category="quality",
                    message=(
                        f"Global variable mutation at line {node.lineno}: "
                        f"{', '.join(node.names)}"
                    ),
                    source_rule="ast.global_mutation",
                    context=(
                        ("line", str(node.lineno)),
                        ("variables", ", ".join(node.names)),
                    ),
                ))

            # Check for functions with too many arguments
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                arg_count = len(node.args.args)
                if arg_count > self.MAX_FUNCTION_ARGS:
                    findings.append(Finding(
                        finding_id=str(uuid.uuid4())[:12],
                        finding_type="warning",
                        severity="medium",
                        category="quality",
                        message=(
                            f"Function '{node.name}' has {arg_count} arguments "
                            f"(max {self.MAX_FUNCTION_ARGS}) at line {node.lineno}"
                        ),
                        source_rule="ast.excessive_args",
                        context=(
                            ("line", str(node.lineno)),
                            ("function", node.name),
                            ("arg_count", str(arg_count)),
                            ("threshold", str(self.MAX_FUNCTION_ARGS)),
                        ),
                    ))

                # Check nesting depth inside functions
                max_depth = self._calculate_nesting_depth(node)
                if max_depth > self.MAX_NESTING_DEPTH:
                    findings.append(Finding(
                        finding_id=str(uuid.uuid4())[:12],
                        finding_type="warning",
                        severity="medium",
                        category="quality",
                        message=(
                            f"Function '{node.name}' has nesting depth {max_depth} "
                            f"(max {self.MAX_NESTING_DEPTH}) at line {node.lineno}"
                        ),
                        source_rule="ast.deep_nesting",
                        context=(
                            ("line", str(node.lineno)),
                            ("function", node.name),
                            ("depth", str(max_depth)),
                            ("threshold", str(self.MAX_NESTING_DEPTH)),
                        ),
                    ))

        return tuple(findings)

    @staticmethod
    def _get_call_name(node: ast.Call) -> str:
        """Extract function name from Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    @staticmethod
    def _calculate_nesting_depth(node: ast.AST, current_depth: int = 0) -> int:
        """Recursive nesting depth calculator."""
        max_depth = current_depth
        nesting_nodes = (
            ast.If, ast.For, ast.While, ast.With,
            ast.Try, ast.AsyncFor, ast.AsyncWith,
        )
        for child in ast.iter_child_nodes(node):
            if isinstance(child, nesting_nodes):
                child_depth = ASTClassifier._calculate_nesting_depth(
                    child, current_depth + 1
                )
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = ASTClassifier._calculate_nesting_depth(
                    child, current_depth
                )
                max_depth = max(max_depth, child_depth)
        return max_depth


# =============================================================================
# Convenience function — classify text with default ruleset
# =============================================================================

def classify_text(text: str, ruleset=None) -> tuple:
    """
    One-shot convenience function.

    Args:
        text: Content to analyze
        ruleset: Optional RuleSet (uses DEFAULT_RULESET if None)

    Returns:
        Tuple of Finding objects
    """
    from .rule import DEFAULT_RULESET

    if ruleset is None:
        ruleset = DEFAULT_RULESET
    return PatternClassifier().classify(text, ruleset)
