"""
Orthodoxy Wardens — Governance Engine

Rule definitions, classifiers, verdict rendering, and workflow declarations.

This package is the DECISION CORE of the Orthodoxy Wardens.
Everything here is pure — no I/O, no network, no database.

Components:
    rule.py            — Rule + RuleSet frozen dataclasses (35 default rules)
    classifier.py      — ASTClassifier (Python AST) + PatternClassifier (DEPRECATED)
    llm_classifier.py  — LLMClassifier (LLM-first semantic analysis, PRIMARY)
    verdict_engine.py  — VerdictEngine: Findings → Verdict + LogDecision
    workflow.py        — Declarative workflow definitions (frozen data)

Usage:
    from vitruvyan_core.core.governance.orthodoxy_wardens.governance import (
        Rule, RuleSet, DEFAULT_RULESET,
        LLMClassifier, ASTClassifier,
        VerdictEngine, ScoringWeights,
        Workflow, WorkflowStep, FULL_AUDIT_WORKFLOW, QUICK_VALIDATION_WORKFLOW,
    )
"""

from .rule import Rule, RuleSet, DEFAULT_RULESET, DEFAULT_RULES
from .classifier import ASTClassifier
from .classifier import PatternClassifier, classify_text  # DEPRECATED — backward compat
from .llm_classifier import LLMClassifier
from .verdict_engine import VerdictEngine, ScoringWeights, DEFAULT_WEIGHTS
from .workflow import (
    Workflow,
    WorkflowStep,
    FULL_AUDIT_WORKFLOW,
    QUICK_VALIDATION_WORKFLOW,
    AVAILABLE_WORKFLOWS,
)

__all__ = [
    # Rules
    "Rule",
    "RuleSet",
    "DEFAULT_RULES",
    "DEFAULT_RULESET",
    # Classification (LLMClassifier = primary, ASTClassifier = structural)
    "ASTClassifier",
    "LLMClassifier",
    # DEPRECATED (retained for backward compatibility)
    "PatternClassifier",
    "classify_text",
    # Verdict
    "VerdictEngine",
    "ScoringWeights",
    "DEFAULT_WEIGHTS",
    # Workflows
    "Workflow",
    "WorkflowStep",
    "FULL_AUDIT_WORKFLOW",
    "QUICK_VALIDATION_WORKFLOW",
    "AVAILABLE_WORKFLOWS",
]
