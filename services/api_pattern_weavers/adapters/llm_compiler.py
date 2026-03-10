"""
Pattern Weavers — LLM Compiler Adapter (LIVELLO 2)
===================================================

Orchestrates semantic compilation:
1. Selects domain plugin from registry
2. Builds LLM prompt (system + user)
3. Calls LLMAgent.complete_json() (I/O)
4. Delegates parsing to LLMCompilerConsumer (pure)
5. Runs domain plugin validation

This is the ONLY file that touches LLMAgent in the PW service.

> **Last updated**: Feb 24, 2026 18:00 UTC

Author: Vitruvyan Core Team
Version: 3.0.0
"""

import logging
import time
import uuid
from typing import Any, Dict, Optional

try:
    from contracts.pattern_weavers import (
        CompileRequest,
        CompileResponse,
        ISemanticPlugin,
        OntologyPayload,
    )
    from core.cognitive.pattern_weavers.consumers.llm_compiler import (
        LLMCompilerConsumer,
    )
    from core.cognitive.pattern_weavers.governance.semantic_plugin import (
        SemanticPluginRegistry,
        get_plugin_registry,
    )
except ModuleNotFoundError:
    from contracts.pattern_weavers import (
        CompileRequest,
        CompileResponse,
        ISemanticPlugin,
        OntologyPayload,
    )
    from core.cognitive.pattern_weavers.consumers.llm_compiler import (
        LLMCompilerConsumer,
    )
    from core.cognitive.pattern_weavers.governance.semantic_plugin import (
        SemanticPluginRegistry,
        get_plugin_registry,
    )

logger = logging.getLogger(__name__)


class LLMCompilerAdapter:
    """
    LIVELLO 2 adapter: LLM-based semantic compilation.

    Lifecycle:
    1. Service startup → register domain plugins via ``register_plugin()``
    2. Request → ``compile()`` → select plugin → LLM call → parse → validate → respond

    Feature flag: ``PATTERN_WEAVERS_V3``
        "1" = /compile endpoint active (default: "0")
    """

    def __init__(self, registry: Optional[SemanticPluginRegistry] = None):
        self._registry = registry or get_plugin_registry()
        self._consumer = LLMCompilerConsumer()
        self._llm_agent = None
        self._compile_count = 0
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

    def register_plugin(self, plugin: ISemanticPlugin) -> None:
        """Register a domain semantic plugin."""
        self._registry.register(plugin)

    def compile(self, request: CompileRequest) -> CompileResponse:
        """
        Compile a user query into OntologyPayload.

        Flow:
            1. Resolve domain plugin
            2. Build user prompt (query text)
            3. Call LLM with plugin's system prompt
            4. Parse LLM response via consumer
            5. Run plugin.validate_payload()
            6. Return CompileResponse
        """
        request_id = str(uuid.uuid4())
        start = time.monotonic()

        # 1. Resolve plugin
        plugin = self._registry.resolve_domain(request.domain)
        domain_name = plugin.get_domain_name()

        logger.info(
            f"LLMCompiler: compiling query [{request_id[:8]}] "
            f"domain={domain_name} len={len(request.query)}"
        )

        try:
            # 2. Build prompt
            system_prompt = plugin.get_system_prompt()
            user_prompt = self._build_user_prompt(request)

            # 3. Call LLM
            llm_start = time.monotonic()
            llm_response = self.llm_agent.complete_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.0,
                max_tokens=1000,
            )
            llm_ms = (time.monotonic() - llm_start) * 1000

            # 4. Parse via pure consumer
            result = self._consumer.process({
                "llm_response": llm_response,
                "raw_query": request.query,
                "domain": domain_name,
                "compile_meta": {
                    "request_id": request_id,
                    "llm_time_ms": round(llm_ms, 2),
                    "method": "llm",
                    "domain": domain_name,
                    "model": getattr(self.llm_agent, "default_model", "unknown"),
                },
            })

            if not result.success:
                logger.error(
                    f"LLMCompiler: consumer failed [{request_id[:8]}]: {result.errors}"
                )
                return self._fallback_response(
                    request, request_id, start, f"consumer_error: {result.errors}"
                )

            # 5. Validate with plugin
            payload_dict = result.data["payload"]
            payload = OntologyPayload.model_validate(payload_dict)
            payload = plugin.validate_payload(payload)

            elapsed_ms = (time.monotonic() - start) * 1000
            self._compile_count += 1

            fallback_used = bool(
                payload.compile_metadata.get("fallback", False)
            )
            if fallback_used:
                self._fallback_count += 1

            logger.info(
                f"LLMCompiler: done [{request_id[:8]}] "
                f"gate={payload.gate.verdict.value} "
                f"entities={len(payload.entities)} "
                f"intent={payload.intent_hint} "
                f"elapsed={elapsed_ms:.0f}ms"
            )

            return CompileResponse(
                request_id=request_id,
                payload=payload,
                fallback_used=fallback_used,
                processing_time_ms=round(elapsed_ms, 2),
            )

        except Exception as e:
            logger.error(
                f"LLMCompiler: exception [{request_id[:8]}]: {e}",
                exc_info=True,
            )
            return self._fallback_response(request, request_id, start, str(e))

    # ─── Stats ───────────────────────────────────────────────

    @property
    def stats(self) -> Dict[str, Any]:
        """Adapter statistics."""
        return {
            "compile_count": self._compile_count,
            "fallback_count": self._fallback_count,
            "registered_domains": self._registry.registered_domains,
        }

    def check_health(self) -> bool:
        """Check if LLM is reachable."""
        try:
            return self.llm_agent is not None
        except Exception:
            return False

    # ─── Internals ───────────────────────────────────────────

    @staticmethod
    def _build_user_prompt(request: CompileRequest) -> str:
        """Build user prompt from compile request."""
        parts = [f"Query: {request.query}"]
        if request.language != "auto":
            parts.append(f"Language hint: {request.language}")
        if request.context:
            parts.append(f"Context: {request.context}")
        return "\n".join(parts)

    def _fallback_response(
        self,
        request: CompileRequest,
        request_id: str,
        start_time: float,
        error: str,
    ) -> CompileResponse:
        """Create fallback CompileResponse when LLM fails entirely."""
        elapsed_ms = (time.monotonic() - start_time) * 1000
        self._fallback_count += 1

        # Use consumer's fallback mechanism
        result = self._consumer.process({
            "llm_response": "{}",  # Empty triggers fallback
            "raw_query": request.query,
            "domain": request.domain if request.domain != "auto" else "generic",
            "compile_meta": {
                "request_id": request_id,
                "method": "fallback",
                "error": error,
            },
        })

        payload = OntologyPayload.model_validate(result.data["payload"])

        return CompileResponse(
            request_id=request_id,
            payload=payload,
            fallback_used=True,
            processing_time_ms=round(elapsed_ms, 2),
        )


# ─── Singleton ───────────────────────────────────────────────

_compiler_adapter: Optional[LLMCompilerAdapter] = None


def get_compiler_adapter() -> LLMCompilerAdapter:
    """Get the LLM compiler adapter singleton."""
    global _compiler_adapter
    if _compiler_adapter is None:
        _compiler_adapter = LLMCompilerAdapter()
    return _compiler_adapter


__all__ = [
    "LLMCompilerAdapter",
    "get_compiler_adapter",
]
