"""
Pattern Weavers — LLM Compiler Consumer
========================================

Pure consumer that PARSES LLM output into OntologyPayload.
Does NOT call LLM — that is LIVELLO 2's responsibility.

Receives: raw JSON string from LLM + metadata
Returns:  ProcessResult with validated OntologyPayload

LIVELLO 1 — Pure Python, no I/O.

> **Last updated**: Feb 24, 2026 18:00 UTC

Author: Vitruvyan Core Team
Version: 3.0.0
"""

import json
import logging
import time
from typing import Any, Dict

from .base import BaseConsumer, ProcessResult

try:
    from contracts.pattern_weavers import (
        DomainGate,
        GateVerdict,
        OntologyEntity,
        OntologyPayload,
    )
except ModuleNotFoundError:
    from vitruvyan_core.contracts.pattern_weavers import (
        DomainGate,
        GateVerdict,
        OntologyEntity,
        OntologyPayload,
    )

logger = logging.getLogger(__name__)


class LLMCompilerConsumer(BaseConsumer):
    """
    Pure consumer: parse LLM JSON response → OntologyPayload.

    Input data keys:
        llm_response  : str | dict — Raw JSON from LLM (string or already parsed)
        raw_query     : str        — Original user query
        domain        : str        — Domain plugin name used
        compile_meta  : dict       — Processing metadata to embed

    Output ProcessResult.data keys:
        payload       : dict       — OntologyPayload.model_dump()
        parse_errors  : list[str]  — Any non-fatal parse issues
    """

    def process(self, data: Dict[str, Any]) -> ProcessResult:
        """Parse LLM response into validated OntologyPayload."""
        start = time.monotonic()

        # Validate required fields
        errors = self.validate_input(data, ["llm_response", "raw_query"])
        if errors:
            self._record_error()
            return ProcessResult(
                success=False,
                data={"payload": None, "parse_errors": errors},
                errors=errors,
            )

        raw_response = data["llm_response"]
        raw_query = data["raw_query"]
        domain = data.get("domain", "generic")
        compile_meta = data.get("compile_meta", {})

        parse_warnings: list[str] = []

        try:
            # Step 1: Parse JSON (string → dict)
            if isinstance(raw_response, str):
                parsed = self._extract_json(raw_response)
            elif isinstance(raw_response, dict):
                parsed = raw_response
            else:
                raise ValueError(
                    f"llm_response must be str or dict, got {type(raw_response).__name__}"
                )

            # Step 2: Inject metadata not produced by LLM
            parsed["raw_query"] = raw_query
            parsed["compile_metadata"] = {
                **compile_meta,
                "parse_time_ms": 0.0,  # updated below
            }

            # Step 3: Ensure gate.domain matches requested domain
            if "gate" in parsed and isinstance(parsed["gate"], dict):
                if parsed["gate"].get("domain", "generic") == "generic" and domain != "generic":
                    parsed["gate"]["domain"] = domain

            # Step 4: Validate via Pydantic (extra="forbid")
            payload = OntologyPayload.model_validate(parsed)

            elapsed_ms = (time.monotonic() - start) * 1000
            # Update metadata with actual parse time
            meta = dict(payload.compile_metadata)
            meta["parse_time_ms"] = round(elapsed_ms, 2)
            payload = payload.model_copy(update={"compile_metadata": meta})

            self._record_success()
            return ProcessResult(
                success=True,
                data={
                    "payload": payload.model_dump(),
                    "parse_errors": parse_warnings,
                },
                warnings=parse_warnings,
                processing_time_ms=int(elapsed_ms),
            )

        except json.JSONDecodeError as e:
            error_msg = f"JSON parse error: {e}"
            logger.warning(f"LLMCompilerConsumer: {error_msg}")
            self._record_error()
            return self._fallback_result(
                raw_query, domain, compile_meta, error_msg, start
            )

        except Exception as e:
            error_msg = f"Validation error: {e}"
            logger.warning(f"LLMCompilerConsumer: {error_msg}")
            self._record_error()
            return self._fallback_result(
                raw_query, domain, compile_meta, error_msg, start
            )

    # ─── Helpers ─────────────────────────────────────────────

    @staticmethod
    def _extract_json(text: str) -> dict:
        """
        Extract JSON from LLM output.

        Handles:
        - Pure JSON string
        - JSON wrapped in ```json ... ``` fences
        - JSON with leading/trailing text
        """
        text = text.strip()

        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from code fences
        if "```" in text:
            # Find content between fences
            parts = text.split("```")
            for part in parts:
                candidate = part.strip()
                if candidate.startswith("json"):
                    candidate = candidate[4:].strip()
                if candidate.startswith("{"):
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        continue

        # Try finding first { ... last }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(text[first_brace : last_brace + 1])
            except json.JSONDecodeError:
                pass

        raise json.JSONDecodeError("No valid JSON found in LLM response", text, 0)

    @staticmethod
    def _fallback_result(
        raw_query: str,
        domain: str,
        compile_meta: dict,
        error_msg: str,
        start_time: float,
    ) -> ProcessResult:
        """Create a minimal valid OntologyPayload when LLM output is unparseable."""
        elapsed_ms = (time.monotonic() - start_time) * 1000

        fallback_payload = OntologyPayload(
            gate=DomainGate(
                verdict=GateVerdict.AMBIGUOUS,
                domain=domain,
                confidence=0.0,
                reasoning=f"LLM parse fallback: {error_msg}",
            ),
            entities=[],
            intent_hint="unknown",
            topics=[],
            sentiment_hint="neutral",
            temporal_context="real_time",
            language="en",
            complexity="simple",
            raw_query=raw_query,
            compile_metadata={
                **compile_meta,
                "fallback": True,
                "fallback_reason": error_msg,
                "parse_time_ms": round(elapsed_ms, 2),
            },
        )

        return ProcessResult(
            success=True,  # Degraded but valid
            data={
                "payload": fallback_payload.model_dump(),
                "parse_errors": [error_msg],
            },
            warnings=[f"Fallback payload used: {error_msg}"],
            processing_time_ms=int(elapsed_ms),
        )


__all__ = ["LLMCompilerConsumer"]
