"""
Prompt Agent — Canonical Gateway for Prompt Resolution
=======================================================

Thin orchestrator that receives a PromptRequest, queries the
PromptRegistry, applies policy, and returns a PromptResolution.

Follows the same singleton pattern as PostgresAgent, QdrantAgent, LLMAgent.

Author: vitruvyan-core
Date: March 10, 2026

Usage:
    from core.agents.prompt_agent import get_prompt_agent

    agent = get_prompt_agent()
    resolution = agent.resolve(PromptRequest(
        domain="generic",
        scenario="analysis",
        language="it",
    ))
    # resolution.system_prompt  → the prompt text
    # resolution.prompt_id      → "prompt.generic.analysis.v1.0"
    # resolution.prompt_hash    → "a3f8b2c1d4e5"
    # resolution.to_audit_dict()→ structured metadata for logging
"""

from __future__ import annotations

import logging
from typing import Optional

from vitruvyan_core.contracts.prompting import (
    DEFAULT_POLICY,
    PromptPolicy,
    PromptRequest,
    PromptResolution,
    compute_prompt_hash,
)
from vitruvyan_core.core.llm.prompts.policy import apply_policy
from vitruvyan_core.core.llm.prompts.registry import PromptRegistry

logger = logging.getLogger(__name__)


class PromptAgent:
    """
    Canonical gateway for prompt resolution.

    Responsibilities:
    - Query the PromptRegistry
    - Apply policy constraints
    - Return PromptResolution with audit metadata

    Does NOT:
    - Call the LLM
    - Duplicate LLMAgent logic
    - Contain business logic
    """

    _instance: Optional[PromptAgent] = None

    def __new__(cls) -> PromptAgent:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.info("PromptAgent initialized")
        return cls._instance

    # ── Public API ───────────────────────────────────────────────────────

    def resolve(self, request: PromptRequest) -> PromptResolution:
        """
        Resolve a prompt request into a fully composed PromptResolution.

        Steps:
        1. Query PromptRegistry for identity + scenario
        2. Apply policy constraints (disclaimers, evidence, domain boundary)
        3. Recompute hash and token estimate after policy application
        4. Return PromptResolution with full audit metadata
        """
        # Merge assistant_name into template_vars
        template_vars = dict(request.template_vars)
        template_vars.setdefault("assistant_name", request.assistant_name)
        template_vars.setdefault("domain_description", request.domain)

        # Resolve from registry
        resolution = PromptRegistry.resolve(
            domain=request.domain,
            scenario=request.scenario,
            language=request.language,
            **template_vars,
        )

        # Apply policy if constraints are active
        policy = request.policy
        if policy.has_constraints:
            prompt_with_policy = apply_policy(
                resolution.system_prompt,
                policy,
                request.language,
            )
            # Recompute hash and tokens after policy modification
            return PromptResolution(
                system_prompt=prompt_with_policy,
                domain=resolution.domain,
                scenario=resolution.scenario,
                language=resolution.language,
                version=resolution.version,
                prompt_id=resolution.prompt_id,
                prompt_hash=compute_prompt_hash(prompt_with_policy),
                estimated_tokens=max(1, int(len(prompt_with_policy.split()) * 1.3)),
                policy_applied=True,
                fallback_used=resolution.fallback_used,
            )

        return resolution

    def resolve_identity(
        self,
        domain: str = "generic",
        language: str = "en",
        policy: Optional[PromptPolicy] = None,
        **template_vars,
    ) -> PromptResolution:
        """Convenience: resolve identity-only prompt (no scenario)."""
        return self.resolve(PromptRequest(
            domain=domain,
            language=language,
            policy=policy or DEFAULT_POLICY,
            template_vars=template_vars,
        ))


# ── Singleton factory ────────────────────────────────────────────────────────

def get_prompt_agent() -> PromptAgent:
    """
    Get the singleton PromptAgent instance.

    Usage:
        from core.agents.prompt_agent import get_prompt_agent

        agent = get_prompt_agent()
        resolution = agent.resolve(request)
    """
    return PromptAgent()


__all__ = [
    "PromptAgent",
    "get_prompt_agent",
]
