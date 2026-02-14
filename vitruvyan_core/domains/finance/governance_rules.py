"""
Finance Domain — Governance Compliance Rules
=============================================

Domain-specific compliance rules for the finance vertical.

These rules detect regulatory violations specific to financial advisory:
- Prescriptive language (MiFID, FINRA compliance)
- Unsupported claims about performance
- Misleading market predictions
- Financial advice disguised as analysis

Loaded by GovernanceRuleRegistry when GOVERNANCE_DOMAIN="finance".

Author: Vitruvyan Core Team
Created: February 14, 2026
Status: PRODUCTION
Version: 1.0
"""

from core.governance.orthodoxy_wardens.governance.rule import Rule


def get_domain_rules() -> tuple:
    """
    Return finance-specific compliance rules.

    Called by GovernanceRuleRegistry.register_domain("finance").
    """
    rules = []

    _compliance = [
        # Prescriptive language — CRITICAL (MiFID/FINRA)
        ("compliance.prescriptive.001", r"\b(buy now|sell now|must buy|must sell)\b",
         "critical", "Direct buy/sell instruction"),
        ("compliance.prescriptive.002", r"\b(guaranteed|sure thing|risk-free|can't lose)\b",
         "critical", "Guaranteed outcome claim"),
        ("compliance.prescriptive.003", r"\b(definitely|certainly) (buy|sell|invest)\b",
         "critical", "Certain outcome instruction"),

        # Unsupported claims — HIGH
        ("compliance.unsupported.001", r"\b(100% accurate|never wrong|always profitable)\b",
         "high", "Impossible accuracy claim"),
        ("compliance.unsupported.002", r"\b(get rich quick|easy money|instant profit)\b",
         "high", "Get-rich-quick language"),
        ("compliance.unsupported.003", r"\b(guaranteed returns|no risk)\b",
         "high", "No-risk guarantee"),

        # Misleading statements — HIGH
        ("compliance.misleading.001",
         r"\b(will definitely|will certainly) (rise|fall|increase|decrease)\b",
         "high", "Certain prediction about market direction"),
        ("compliance.misleading.002", r"\b(impossible to lose|cannot fail)\b",
         "high", "Impossibility claim"),
        ("compliance.misleading.003", r"\b(unlimited profit|infinite returns)\b",
         "high", "Unlimited upside promise"),

        # Financial advice patterns
        ("compliance.advice.001", r"\b(you should|you must) (buy|sell|invest)\b",
         "high", "Direct financial advice"),
        ("compliance.advice.002", r"\b(recommendation|advice): (buy|sell)\b",
         "high", "Explicit recommendation"),
        ("compliance.advice.003", r"\b(strong buy|strong sell)\b",
         "medium", "Brokerage-style rating language"),

        # Improper disclaimers — MEDIUM
        ("compliance.disclaimer.001",
         r"not financial advice.*but.*(?:buy|sell|invest)",
         "medium", "Disclaimer contradicted by advice"),
        ("compliance.disclaimer.002",
         r"disclaimer.*however.*(?:recommend|suggest)",
         "medium", "Disclaimer negated by recommendation"),

        # Finance-specific hallucination
        ("compliance.hallucination.001",
         r"\b(proven|mathematical certainty|scientifically proven)\b.*\b(stock|market|invest)\b",
         "high", "False certainty claim about financial markets"),
    ]

    for rule_id, pattern, severity, desc in _compliance:
        rules.append(Rule(
            rule_id=rule_id,
            category="compliance",
            subcategory=rule_id.split(".")[1],
            severity=severity,
            pattern=pattern,
            description=desc,
        ))

    return tuple(rules)
