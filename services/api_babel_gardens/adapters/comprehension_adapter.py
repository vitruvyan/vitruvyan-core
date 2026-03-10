"""
Babel Gardens — Comprehension Adapter (LIVELLO 2)
=================================================

Orchestrates unified semantic comprehension:
1. Selects domain plugin from ComprehensionPluginRegistry
2. Builds unified LLM prompt (ontology + semantics in one call)
3. Calls LLMAgent.complete_json() (I/O)
4. Delegates parsing to ComprehensionConsumer (pure LIVELLO 1)
5. Runs domain plugin validation

This is the ONLY file that calls LLM for comprehension.

> **Last updated**: Feb 26, 2026 14:00 UTC

Author: Vitruvyan Core Team
Version: 1.0.0
"""

import logging
import time
import uuid
from typing import Any, Dict, Optional

try:
    from contracts.comprehension import (
        ComprehendRequest,
        ComprehendResponse,
        ComprehensionResult,
        IComprehensionPlugin,
    )
    from core.cognitive.babel_gardens.consumers.comprehension_consumer import (
        ComprehensionConsumer,
    )
    from core.cognitive.babel_gardens.governance.signal_registry import (
        ComprehensionPluginRegistry,
        get_comprehension_registry,
    )
except ModuleNotFoundError:
    from contracts.comprehension import (
        ComprehendRequest,
        ComprehendResponse,
        ComprehensionResult,
        IComprehensionPlugin,
    )
    from core.cognitive.babel_gardens.consumers.comprehension_consumer import (
        ComprehensionConsumer,
    )
    from core.cognitive.babel_gardens.governance.signal_registry import (
        ComprehensionPluginRegistry,
        get_comprehension_registry,
    )

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Unified system prompt template
# ─────────────────────────────────────────────────────────────

_UNIFIED_SYSTEM_PROMPT = """\
You are a unified language comprehension engine for a multilingual AI system.
Given a user query, produce a SINGLE JSON object with two sections:
1. "ontology" — WHAT the query is about (entities, intent, domain gate)
2. "semantics" — HOW the query is expressed (sentiment, emotion, style)

You MUST respond with ONLY valid JSON (no markdown, no explanation).
The top-level structure is:
{{
  "ontology": {{ ... }},
  "semantics": {{ ... }}
}}

Rules:
- Detect language automatically — you understand ALL languages
- Consider cultural norms (Italian expressiveness, Japanese understatement, etc.)
- Sarcasm/irony MUST be detected and reflected in BOTH ontology AND semantics
- Factual/neutral queries get neutral sentiment with low magnitude
- Extract ALL identifiable entities even if confidence is moderate

{ontology_section}

{semantics_section}
"""


class ComprehensionAdapter:
    """
    LIVELLO 2 adapter: unified LLM-based comprehension.

    One LLM call produces both ontology (PW v3) + semantics (BG).
    Replaces separate /compile + /emotion calls.

    Feature flag: ``BABEL_COMPREHENSION_V3``
        "1" = /comprehend endpoint active (default: "0")
    """

    def __init__(self, registry: Optional[ComprehensionPluginRegistry] = None):
        self._registry = registry or get_comprehension_registry()
        self._consumer = ComprehensionConsumer(config=None)
        self._llm_agent = None
        self._comprehend_count = 0
        self._fallback_count = 0

    # ─── Lazy LLM agent ─────────────────────────────────────

    @property
    def llm_agent(self):
        """Lazy-load LLMAgent singleton."""
        if self._llm_agent is None:
            try:
                from core.agents.llm_agent import get_llm_agent
            except ModuleNotFoundError:
                from core.agents.llm_agent import get_llm_agent
            self._llm_agent = get_llm_agent()
        return self._llm_agent

    # ─── Public API ──────────────────────────────────────────

    def register_plugin(self, plugin: IComprehensionPlugin) -> None:
        """Register a domain comprehension plugin."""
        self._registry.register(plugin)

    def comprehend(self, request: ComprehendRequest) -> ComprehendResponse:
        """
        Comprehend a user query in one unified LLM call.

        Flow:
            1. Resolve domain plugin
            2. Build unified prompt (ontology + semantics sections)
            3. Call LLM with unified system prompt
            4. Parse via ComprehensionConsumer (pure)
            5. Run plugin.validate_result()
            6. Return ComprehendResponse
        """
        request_id = str(uuid.uuid4())
        start = time.monotonic()

        # 1. Resolve plugin
        plugin = self._registry.resolve(request.domain)
        domain_name = plugin.get_domain_name()

        logger.info(
            f"Comprehension: query [{request_id[:8]}] "
            f"domain={domain_name} len={len(request.query)}"
        )

        try:
            # 2. Build unified prompt
            system_prompt = self._build_system_prompt(plugin)
            user_prompt = self._build_user_prompt(request)

            # 3. Call LLM (single call for both ontology + semantics)
            llm_start = time.monotonic()
            llm_response = self.llm_agent.complete_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.0,
                max_tokens=1500,
            )
            llm_ms = (time.monotonic() - llm_start) * 1000

            # 4. Parse via pure consumer
            result = self._consumer.process({
                "llm_response": llm_response,
                "raw_query": request.query,
                "domain": domain_name,
                "meta": {
                    "request_id": request_id,
                    "llm_time_ms": round(llm_ms, 2),
                    "method": "unified_llm",
                    "domain": domain_name,
                    "model": getattr(self.llm_agent, "default_model", "unknown"),
                },
            })

            if not result.success:
                logger.error(
                    f"Comprehension: consumer failed [{request_id[:8]}]: {result.errors}"
                )
                return self._fallback_response(
                    request, request_id, start, f"consumer_error: {result.errors}"
                )

            # 5. Validate with plugin
            comp = ComprehensionResult.model_validate(result.data["result"])
            comp = plugin.validate_result(comp)

            elapsed_ms = (time.monotonic() - start) * 1000
            self._comprehend_count += 1

            fallback_used = bool(comp.comprehension_metadata.get("fallback", False))
            if fallback_used:
                self._fallback_count += 1

            logger.info(
                f"Comprehension: done [{request_id[:8]}] "
                f"gate={comp.ontology.gate.verdict.value} "
                f"entities={len(comp.ontology.entities)} "
                f"sentiment={comp.semantics.sentiment.label} "
                f"emotion={comp.semantics.emotion.primary} "
                f"elapsed={elapsed_ms:.0f}ms"
            )

            return ComprehendResponse(
                request_id=request_id,
                result=comp,
                fallback_used=fallback_used,
                processing_time_ms=round(elapsed_ms, 2),
            )

        except Exception as e:
            logger.error(
                f"Comprehension: exception [{request_id[:8]}]: {e}",
                exc_info=True,
            )
            return self._fallback_response(request, request_id, start, str(e))

    # ─── Stats ───────────────────────────────────────────────

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "comprehend_count": self._comprehend_count,
            "fallback_count": self._fallback_count,
            "registered_domains": self._registry.registered_domains,
        }

    def check_health(self) -> bool:
        try:
            return self.llm_agent is not None
        except Exception:
            return False

    # ─── Internals ───────────────────────────────────────────

    @staticmethod
    def _build_system_prompt(plugin: IComprehensionPlugin) -> str:
        """Build unified system prompt from plugin sections."""
        return _UNIFIED_SYSTEM_PROMPT.format(
            ontology_section=plugin.get_ontology_prompt_section(),
            semantics_section=plugin.get_semantics_prompt_section(),
        )

    @staticmethod
    def _build_user_prompt(request: ComprehendRequest) -> str:
        """Build user prompt from request."""
        parts = [f"Query: {request.query}"]
        if request.language != "auto":
            parts.append(f"Language hint: {request.language}")
        if request.context:
            import json
            parts.append(f"Context: {json.dumps(request.context, ensure_ascii=False)}")
        return "\n".join(parts)

    def _fallback_response(
        self,
        request: ComprehendRequest,
        request_id: str,
        start_time: float,
        error: str,
    ) -> ComprehendResponse:
        """Create fallback response when LLM fails entirely."""
        elapsed_ms = (time.monotonic() - start_time) * 1000
        self._fallback_count += 1

        # Use consumer's fallback mechanism
        result = self._consumer.process({
            "llm_response": "{}",
            "raw_query": request.query,
            "domain": request.domain if request.domain != "auto" else "generic",
            "meta": {"request_id": request_id, "method": "fallback", "error": error},
        })

        comp = ComprehensionResult.model_validate(result.data["result"])

        return ComprehendResponse(
            request_id=request_id,
            result=comp,
            fallback_used=True,
            processing_time_ms=round(elapsed_ms, 2),
        )
