"""
Enterprise Domain — Governance Compliance Rules
================================================

Domain-specific compliance rules for the Enterprise vertical.

These rules intercept:
- Unauthorized access to sensitive ERP data patterns
- False precision on financial projections
- Unfounded claims about business performance
- PII/GDPR concerns in employee data responses
- Tax/legal advice that should be referred to professionals

Loaded by GovernanceRuleRegistry when GOVERNANCE_DOMAIN="enterprise".

Vertical: Enterprise
Contract: VERTICAL_CONTRACT_V1

Created: March 2026
"""

from core.governance.orthodoxy_wardens.governance.rule import Rule


def get_domain_rules() -> list:
    """
    Return enterprise-specific compliance rules.

    Called by GovernanceRuleRegistry.register_domain("enterprise").
    """
    rules = []

    # ------------------------------------------------------------------
    # 1. Financial claims — no guaranteed projections
    # ------------------------------------------------------------------
    _financial_claims = [
        ("enterprise.finance.001",
         r"\b(garantito|guaranteed|sicuramente|definitely)\s+(crescita|growth|profitto|profit|fatturato|revenue)\b",
         "high",
         "Guaranteed financial outcome — not admissible for business analysis"),
        ("enterprise.finance.002",
         r"\b(il fatturato sarà|revenue will be|profitto previsto|projected profit)\s+\d+",
         "high",
         "Specific financial projection without disclaimer — add uncertainty qualifier"),
    ]

    # ------------------------------------------------------------------
    # 2. Legal/tax — must redirect to professionals
    # ------------------------------------------------------------------
    _legal_tax = [
        ("enterprise.legal.001",
         r"\b(devi pagare|you must pay|obbligo fiscale|tax obligation)\s+(IVA|VAT|IRPEF|IRES)\b",
         "high",
         "Tax obligation claim — redirect to certified accountant"),
        ("enterprise.legal.002",
         r"\b(è legale|is legal|è illegale|is illegal|violazione contrattuale|breach of contract)\b",
         "high",
         "Legal determination — redirect to legal counsel"),
    ]

    # ------------------------------------------------------------------
    # 3. PII / GDPR — sensitive employee data
    # ------------------------------------------------------------------
    _pii_gdpr = [
        ("enterprise.gdpr.001",
         r"\b(stipendio di|salary of|RAL di|compensation of)\s+[A-Z][a-z]+",
         "critical",
         "Individual salary disclosure — GDPR sensitive, requires authorization"),
        ("enterprise.gdpr.002",
         r"\b(codice fiscale|tax ID|IBAN|bank account)\s+(di|of|per|for)\b",
         "critical",
         "Personal financial identifier disclosure — GDPR Article 9"),
    ]

    for category, group in [
        ("compliance", _financial_claims),
        ("compliance", _legal_tax),
        ("security", _pii_gdpr),
    ]:
        for rule_id, pattern, severity, description in group:
            rules.append(Rule(
                rule_id=rule_id,
                category=category,
                subcategory=rule_id.rsplit(".", 1)[0],
                severity=severity,
                pattern=pattern,
                description=description,
            ))

    return rules
