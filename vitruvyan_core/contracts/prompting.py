"""
Prompting Contract — Core DTO and Interfaces
==============================================

Defines the programmatic interfaces for the prompt governance system.

These are the types that standardize prompt resolution, policy enforcement,
and audit trail across the entire Vitruvyan OS runtime.

Services and LangGraph nodes import these to request and consume prompts
through the canonical PromptAgent gateway.

Author: vitruvyan-core
Date: March 10, 2026
Contract Version: 1.0.0

Usage:
    from contracts.prompting import PromptRequest, PromptResolution, PromptPolicy
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── PromptPolicy ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PromptPolicy:
    """
    Non-negotiable prompt constraints.

    The core defines the structure. Verticals fill it with domain-specific
    values (e.g., "no legal advice", "cite evidence first").

    All flags default to False — opt-in by the vertical.
    """

    must_declare_limitations: bool = False
    must_cite_evidence: bool = False
    must_stay_in_domain: bool = False
    required_disclaimers: Dict[str, str] = field(default_factory=dict)
    forbidden_claims: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_constraints(self) -> bool:
        """True if any constraint is active."""
        return (
            self.must_declare_limitations
            or self.must_cite_evidence
            or self.must_stay_in_domain
            or bool(self.required_disclaimers)
            or bool(self.forbidden_claims)
        )


# Default policy: no constraints (backward compatible).
DEFAULT_POLICY = PromptPolicy()


# ── PromptRequest ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PromptRequest:
    """
    Input for prompt resolution via PromptAgent.

    Describes what prompt is needed. The PromptAgent resolves it against
    the PromptRegistry and applies policy.
    """

    domain: str = "generic"
    scenario: str = ""
    language: str = "en"
    assistant_name: str = "Vitruvyan"
    template_vars: Dict[str, str] = field(default_factory=dict)
    policy: PromptPolicy = field(default_factory=PromptPolicy)
    version_override: Optional[str] = None


# ── PromptResolution ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PromptResolution:
    """
    Output of prompt resolution.

    Contains the fully composed system prompt plus all metadata needed
    for audit trail, caching, and observability.
    """

    system_prompt: str
    domain: str
    scenario: str
    language: str
    version: str
    prompt_id: str
    prompt_hash: str
    estimated_tokens: int
    policy_applied: bool = False
    fallback_used: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_audit_dict(self) -> Dict[str, Any]:
        """Structured metadata for logging and audit trail."""
        return {
            "prompt_id": self.prompt_id,
            "prompt_hash": self.prompt_hash,
            "domain": self.domain,
            "scenario": self.scenario,
            "language": self.language,
            "version": self.version,
            "estimated_tokens": self.estimated_tokens,
            "policy_applied": self.policy_applied,
            "fallback_used": self.fallback_used,
        }


# ── Utility ──────────────────────────────────────────────────────────────────

def compute_prompt_hash(text: str) -> str:
    """Deterministic SHA-256 hash of prompt text (first 12 hex chars)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def build_prompt_id(domain: str, scenario: str, version: str) -> str:
    """Build a deterministic prompt identifier."""
    scenario_part = f".{scenario}" if scenario else ""
    return f"prompt.{domain}{scenario_part}.v{version}"
