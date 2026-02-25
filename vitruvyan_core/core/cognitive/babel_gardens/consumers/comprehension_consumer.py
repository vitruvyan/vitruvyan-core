"""
Babel Gardens — Comprehension Consumer
=======================================

Pure consumer that PARSES LLM output into ComprehensionResult.
Does NOT call LLM — that is LIVELLO 2's responsibility.

Receives: raw JSON (dict or str) from unified LLM call + metadata
Returns:  ProcessResult with validated ComprehensionResult

LIVELLO 1 — Pure Python, no I/O.

> **Last updated**: Feb 26, 2026 14:00 UTC

Author: Vitruvyan Core Team
Version: 1.0.0
"""

import json
import logging
import time
from typing import Any, Dict

from .base import BaseConsumer, ProcessResult

try:
    from contracts.comprehension import (
        ComprehensionResult,
        EmotionPayload,
        LinguisticPayload,
        SemanticPayload,
        SentimentPayload,
    )
    from contracts.pattern_weavers import (
        DomainGate,
        GateVerdict,
        OntologyPayload,
    )
except ModuleNotFoundError:
    from vitruvyan_core.contracts.comprehension import (
        ComprehensionResult,
        EmotionPayload,
        LinguisticPayload,
        SemanticPayload,
        SentimentPayload,
    )
    from vitruvyan_core.contracts.pattern_weavers import (
        DomainGate,
        GateVerdict,
        OntologyPayload,
    )

logger = logging.getLogger(__name__)


class ComprehensionConsumer(BaseConsumer):
    """
    Pure consumer: parse unified LLM JSON → ComprehensionResult.

    Input data keys:
        llm_response  : str | dict — Raw JSON from unified LLM call
        raw_query     : str        — Original user query
        domain        : str        — Domain plugin name used
        meta          : dict       — Processing metadata to embed

    Output ProcessResult.data keys:
        result        : dict       — ComprehensionResult.model_dump()
        parse_errors  : list[str]  — Any non-fatal parse issues
    """

    def process(self, data: Dict[str, Any]) -> ProcessResult:
        """Parse unified LLM response into validated ComprehensionResult."""
        start = time.monotonic()

        errors = self.validate_input(data, ["llm_response", "raw_query"])
        if errors:
            self._record_error()
            return ProcessResult(
                success=False,
                data={"result": None, "parse_errors": errors},
                errors=errors,
            )

        raw_response = data["llm_response"]
        raw_query = data["raw_query"]
        domain = data.get("domain", "generic")
        meta = data.get("meta", {})
        parse_warnings: list[str] = []

        try:
            # Step 1: Parse JSON
            if isinstance(raw_response, str):
                parsed = self._extract_json(raw_response)
            elif isinstance(raw_response, dict):
                parsed = raw_response
            else:
                raise ValueError(
                    f"llm_response must be str or dict, got {type(raw_response).__name__}"
                )

            # Step 2: Build ComprehensionResult from parsed LLM output
            result = self._build_result(parsed, raw_query, domain, meta, parse_warnings)

            elapsed_ms = (time.monotonic() - start) * 1000
            # Inject parse time
            result_meta = dict(result.comprehension_metadata)
            result_meta["parse_time_ms"] = round(elapsed_ms, 2)
            result = result.model_copy(update={"comprehension_metadata": result_meta})

            self._record_success()
            return ProcessResult(
                success=True,
                data={
                    "result": result.model_dump(),
                    "parse_errors": parse_warnings,
                },
                processing_time_ms=elapsed_ms,
            )

        except json.JSONDecodeError as e:
            error_msg = f"JSON parse error: {e}"
            logger.warning(f"ComprehensionConsumer: {error_msg}")
            self._record_error()
            return self._fallback_result(raw_query, domain, meta, error_msg, start)

        except Exception as e:
            error_msg = f"Validation error: {e}"
            logger.warning(f"ComprehensionConsumer: {error_msg}")
            self._record_error()
            return self._fallback_result(raw_query, domain, meta, error_msg, start)

    def _build_result(
        self,
        parsed: dict,
        raw_query: str,
        domain: str,
        meta: dict,
        warnings: list,
    ) -> ComprehensionResult:
        """Build ComprehensionResult from parsed LLM dict."""

        # --- Ontology section ---
        ontology_data = parsed.get("ontology", {})
        if not isinstance(ontology_data, dict):
            ontology_data = {}
            warnings.append("ontology section missing or invalid, using defaults")

        # Inject raw_query + metadata
        ontology_data["raw_query"] = raw_query
        ontology_data.setdefault("compile_metadata", meta)

        # Ensure gate.domain
        gate = ontology_data.get("gate", {})
        if isinstance(gate, dict) and gate.get("domain", "generic") == "generic" and domain != "generic":
            gate["domain"] = domain
            ontology_data["gate"] = gate

        try:
            ontology = OntologyPayload.model_validate(ontology_data)
        except Exception as e:
            warnings.append(f"ontology validation degraded: {e}")
            ontology = OntologyPayload(
                raw_query=raw_query,
                gate=DomainGate(
                    verdict=GateVerdict.AMBIGUOUS,
                    domain=domain,
                    confidence=0.0,
                    reasoning=f"Parse degraded: {e}",
                ),
                compile_metadata=meta,
            )

        # --- Semantics section ---
        semantics_data = parsed.get("semantics", {})
        if not isinstance(semantics_data, dict):
            semantics_data = {}
            warnings.append("semantics section missing or invalid, using defaults")

        try:
            semantics = SemanticPayload.model_validate(semantics_data)
        except Exception as e:
            warnings.append(f"semantics validation degraded: {e}")
            semantics = SemanticPayload()

        # --- Top-level fields ---
        language = parsed.get("language") or ontology.language or "en"

        return ComprehensionResult(
            ontology=ontology,
            semantics=semantics,
            raw_query=raw_query,
            language=language,
            comprehension_metadata={
                **meta,
                "domain": domain,
                "parse_warnings": warnings,
            },
        )

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract JSON from LLM output (handles fences, leading text)."""
        text = text.strip()

        # Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Code fences
        if "```" in text:
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

        # First { ... last }
        first = text.find("{")
        last = text.rfind("}")
        if first != -1 and last > first:
            try:
                return json.loads(text[first:last + 1])
            except json.JSONDecodeError:
                pass

        raise json.JSONDecodeError("No valid JSON found in LLM response", text, 0)

    @staticmethod
    def _fallback_result(
        raw_query: str,
        domain: str,
        meta: dict,
        error_msg: str,
        start_time: float,
    ) -> ProcessResult:
        """Create minimal valid ComprehensionResult when LLM output is unparseable."""
        elapsed_ms = (time.monotonic() - start_time) * 1000

        fallback = ComprehensionResult(
            ontology=OntologyPayload(
                gate=DomainGate(
                    verdict=GateVerdict.AMBIGUOUS,
                    domain=domain,
                    confidence=0.0,
                    reasoning=f"LLM parse fallback: {error_msg}",
                ),
                raw_query=raw_query,
                compile_metadata={**meta, "fallback": True, "error": error_msg},
            ),
            semantics=SemanticPayload(),
            raw_query=raw_query,
            comprehension_metadata={
                **meta,
                "fallback": True,
                "error": error_msg,
                "parse_time_ms": round(elapsed_ms, 2),
            },
        )

        return ProcessResult(
            success=True,  # Degraded but still valid
            data={
                "result": fallback.model_dump(),
                "parse_errors": [error_msg],
            },
            errors=[error_msg],
            processing_time_ms=elapsed_ms,
        )
