"""
Babel Gardens — Signal Fusion Adapter (LIVELLO 2)
=================================================

Orchestrates Layer 3 signal fusion:
1. Collects evidences from all registered signal contributors (Layer 2)
2. Delegates fusion to SignalFusionConsumer (pure LIVELLO 1)
3. Optionally runs LLM arbitration for conflicting signals

> **Last updated**: Feb 26, 2026 14:00 UTC

Author: Vitruvyan Core Team
Version: 1.0.0
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

try:
    from contracts.comprehension import (
        ComprehensionResult,
        FuseRequest,
        FuseResponse,
        FusionResult,
        FusionStrategy,
        SignalEvidence,
    )
    from core.cognitive.babel_gardens.consumers.signal_fusion_consumer import (
        SignalFusionConsumer,
    )
    from core.cognitive.babel_gardens.governance.signal_registry import (
        SignalContributorRegistry,
        get_signal_contributor_registry,
    )
except ModuleNotFoundError:
    from contracts.comprehension import (
        ComprehensionResult,
        FuseRequest,
        FuseResponse,
        FusionResult,
        FusionStrategy,
        SignalEvidence,
    )
    from core.cognitive.babel_gardens.consumers.signal_fusion_consumer import (
        SignalFusionConsumer,
    )
    from core.cognitive.babel_gardens.governance.signal_registry import (
        SignalContributorRegistry,
        get_signal_contributor_registry,
    )

logger = logging.getLogger(__name__)


class SignalFusionAdapter:
    """
    LIVELLO 2 adapter: signal fusion orchestration.

    Collects Layer 2 domain evidences, runs Layer 3 fusion,
    and optionally arbitrates via LLM for conflicting signals.
    """

    def __init__(self, registry: Optional[SignalContributorRegistry] = None):
        self._registry = registry or get_signal_contributor_registry()
        self._consumer = SignalFusionConsumer(config=None)
        self._fuse_count = 0

    def fuse(self, request: FuseRequest) -> FuseResponse:
        """
        Full fusion pipeline:
        1. Run all registered contributors → List[SignalEvidence]
        2. Merge with request.evidences (pre-computed)
        3. Delegate to SignalFusionConsumer
        4. If LLM arbitration needed, call LLM
        """
        request_id = str(uuid.uuid4())
        start = time.monotonic()

        try:
            # 1. Collect Layer 2 evidences from contributors
            contributor_evidences = self._collect_evidences(
                request.comprehension.raw_query,
                {"domain": request.comprehension.ontology.gate.domain},
            )

            # 2. Merge with pre-computed evidences
            all_evidences = request.evidences + contributor_evidences

            # 3. Delegate to pure consumer
            result = self._consumer.process({
                "comprehension": request.comprehension.model_dump(),
                "evidences": [e.model_dump() for e in all_evidences],
                "strategy": request.strategy.value,
                "weights": request.weights,
            })

            if not result.success:
                logger.error(f"SignalFusion: consumer failed [{request_id[:8]}]: {result.errors}")
                elapsed_ms = (time.monotonic() - start) * 1000
                return FuseResponse(
                    request_id=request_id,
                    results=[],
                    processing_time_ms=round(elapsed_ms, 2),
                )

            # 4. Parse fusion results
            fusion_results = [
                FusionResult.model_validate(r) for r in result.data.get("results", [])
            ]

            # 5. Handle LLM arbitration if needed
            arbitration_needed = [
                r for r in fusion_results
                if r.strategy_used == FusionStrategy.LLM_ARBITRATED
                and r.fused_label == "pending_arbitration"
            ]
            if arbitration_needed:
                fusion_results = self._run_llm_arbitration(
                    fusion_results, request.comprehension, request_id
                )

            elapsed_ms = (time.monotonic() - start) * 1000
            self._fuse_count += 1

            logger.info(
                f"SignalFusion: done [{request_id[:8]}] "
                f"fused={len(fusion_results)} signals "
                f"contributors={len(contributor_evidences)} "
                f"elapsed={elapsed_ms:.0f}ms"
            )

            return FuseResponse(
                request_id=request_id,
                results=fusion_results,
                processing_time_ms=round(elapsed_ms, 2),
            )

        except Exception as e:
            logger.error(f"SignalFusion: exception [{request_id[:8]}]: {e}", exc_info=True)
            elapsed_ms = (time.monotonic() - start) * 1000
            return FuseResponse(
                request_id=request_id,
                results=[],
                processing_time_ms=round(elapsed_ms, 2),
            )

    def _collect_evidences(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[SignalEvidence]:
        """Run all available contributors and collect evidences."""
        evidences: List[SignalEvidence] = []

        for contributor in self._registry.get_available():
            try:
                contrib_start = time.monotonic()
                signals = contributor.contribute(text, context)
                contrib_ms = (time.monotonic() - contrib_start) * 1000

                for signal in signals:
                    # Inject timing metadata
                    enriched = signal.model_copy(
                        update={
                            "extraction_trace": {
                                **signal.extraction_trace,
                                "contributor": contributor.get_contributor_name(),
                                "extraction_time_ms": round(contrib_ms, 2),
                            }
                        }
                    )
                    evidences.append(enriched)

                logger.debug(
                    f"Contributor '{contributor.get_contributor_name()}' "
                    f"produced {len(signals)} signals in {contrib_ms:.0f}ms"
                )

            except Exception as e:
                logger.warning(
                    f"Contributor '{contributor.get_contributor_name()}' failed: {e}"
                )
                continue

        return evidences

    def _run_llm_arbitration(
        self,
        results: List[FusionResult],
        comprehension: ComprehensionResult,
        request_id: str,
    ) -> List[FusionResult]:
        """
        Run LLM arbitration for conflicting signals.

        Replaces 'pending_arbitration' results with LLM-resolved verdicts.
        """
        try:
            from core.agents.llm_agent import get_llm_agent
        except ModuleNotFoundError:
            from core.agents.llm_agent import get_llm_agent

        try:
            llm = get_llm_agent()
        except Exception as e:
            logger.warning(f"LLM arbitration unavailable: {e}")
            return results

        import json

        arbitrated: List[FusionResult] = []
        for r in results:
            if r.strategy_used == FusionStrategy.LLM_ARBITRATED and r.fused_label == "pending_arbitration":
                try:
                    prompt = (
                        f"Arbitrate conflicting {r.signal_name} signals.\n"
                        f"Query: {comprehension.raw_query}\n"
                        f"Contributors:\n"
                    )
                    for c in r.contributors:
                        prompt += (
                            f"  - {c.evidence.source}: value={c.evidence.value}, "
                            f"confidence={c.evidence.confidence}\n"
                        )
                    prompt += (
                        "\nReturn JSON: {\"fused_value\": <float>, "
                        "\"fused_label\": \"<label>\", \"reasoning\": \"<brief>\"}"
                    )

                    llm_result = llm.complete_json(
                        prompt=prompt,
                        system_prompt="You arbitrate conflicting signals. Return ONLY valid JSON.",
                        temperature=0.0,
                        max_tokens=200,
                    )

                    arbitrated.append(r.model_copy(update={
                        "fused_value": float(llm_result.get("fused_value", 0.0)),
                        "fused_label": llm_result.get("fused_label", "neutral"),
                        "fused_confidence": 0.7,
                        "reasoning": llm_result.get("reasoning", "LLM arbitrated"),
                    }))
                except Exception as e:
                    logger.warning(f"LLM arbitration failed for {r.signal_name}: {e}")
                    arbitrated.append(r)
            else:
                arbitrated.append(r)

        return arbitrated

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "fuse_count": self._fuse_count,
            "registered_contributors": self._registry.registered_names,
        }
