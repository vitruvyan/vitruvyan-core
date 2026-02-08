#!/usr/bin/env python3
"""
NarrativeEngine — Explanation Generation Consumer (Temporal Cortex)
===================================================================

Epistemic Order: DISCOURSE
Sacred Order: Narrative Weaver (#6)
Consumer Type: ADVISORY

Biological Model: Temporal cortex
- Language processing and meaning generation
- Converts quantitative analysis into human narratives
- Integrates VEEEngine for explainability

Subscriptions:
- analysis.complete → Generate explanations for completed analyses
- orthodoxy.verdict.* → Explain verdicts in natural language
- comparison.complete → Generate comparison narratives
- screening.complete → Generate ranking explanations

Capabilities:
- Ticker analysis narratives (VEE 3-level)
- Comparison explanations
- Screening/ranking explanations
- Orthodoxy verdict translations

Author: Vitruvyan Cognitive Architecture  
Date: January 20, 2026  
Phase: 5 (Specialized Consumers)
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

from vitruvyan_core.core.synaptic_conclave.consumers.base_consumer import (
    BaseConsumer,
    ConsumerConfig,
    ConsumerType,
    ProcessResult
)
from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamEvent
from vitruvyan_core.core.synaptic_conclave.events.event_envelope import CognitiveEvent, TransportEvent, EventAdapter
from vitruvyan_core.core.synaptic_conclave.consumers.working_memory import WorkingMemory
from core.logic.vitruvyan_proprietary.vee.vee_engine import VEEEngine

logger = logging.getLogger("NarrativeEngine")


@dataclass
class NarrativeResult:
    """
    Result from narrative generation.
    
    Attributes:
        event_id: Original event ID that triggered narrative
        narrative_type: Type of narrative generated
        summary: Brief narrative (Level 1)
        detailed: Operational narrative (Level 2)
        technical: Technical narrative with z-scores (Level 3)
        confidence: Generation confidence (0-1)
        language: Language used (en, it, es, etc.)
        metadata: Additional context
    """
    event_id: str
    narrative_type: str  # "ticker", "comparison", "screening", "verdict"
    summary: str
    detailed: Optional[str] = None
    technical: Optional[str] = None
    confidence: float = 0.8
    language: str = "en"
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class NarrativeEngine(BaseConsumer):
    """
    Advisory consumer for explanation generation.
    
    Like temporal cortex: processes language, generates meaning,
    converts quantitative data into human-readable narratives.
    
    Integration:
    - VEEEngine for financial analysis explanations
    - Multi-level narrative depth (summary/detailed/technical)
    - Multilingual support (EN/IT/ES via VEE)
    - Context-aware via working memory
    """
    
    def __init__(
        self,
        redis_url: str = "redis://vitruvyan_redis:6379",
        vee_engine: Optional[VEEEngine] = None
    ):
        """
        Initialize NarrativeEngine consumer.
        
        Args:
            redis_url: Redis connection URL
            vee_engine: Optional VEEEngine instance (creates new if None)
        """
        # Configure consumer
        config = ConsumerConfig(
            name="narrative_engine",
            consumer_type=ConsumerType.ADVISORY,  # Can timeout without breaking system
            subscriptions=[
                "analysis.complete",       # Single ticker analysis
                "comparison.complete",     # Multi-ticker comparison
                "screening.complete",      # Ranking/screening results
                "orthodoxy.verdict.*",     # Orthodoxy verdicts (all types)
                "portfolio.analysis.complete"  # Portfolio analysis
            ],
            confidence_threshold=0.6,
            timeout_ms=5000  # 5s timeout for narrative generation
        )
        
        super().__init__(config)
        
        # Initialize VEE Engine
        self.vee = vee_engine or VEEEngine()
        
        # Initialize working memory (Redis-backed)
        self.memory = WorkingMemory(
            consumer_name="narrative_engine",
            ttl_seconds=3600  # Remember context for 1 hour
        )
        
        # Connect to Redis
        asyncio.create_task(self.memory.connect(redis_url))
        
        logger.info(f"✍️ NarrativeEngine initialized")
        logger.info(f"   Subscriptions: {', '.join(config.subscriptions)}")
        logger.info(f"   VEE Engine: {self.vee.__class__.__name__}")
        logger.info(f"   Timeout: {config.timeout_ms}ms")
    
    async def process(self, event: CognitiveEvent) -> ProcessResult:
        """
        Process incoming events and generate narratives.
        
        Routing:
        - analysis.complete → generate_ticker_narrative()
        - comparison.complete → generate_comparison_narrative()
        - screening.complete → generate_screening_narrative()
        - orthodoxy.verdict.* → generate_verdict_narrative()
        
        Args:
            event: Incoming stream event
            
        Returns:
            StreamEvent with narrative result, or None if uncertain
        """
        # Convert TransportEvent to CognitiveEvent if needed
        if isinstance(event, TransportEvent):
            event = EventAdapter.transport_to_cognitive(event)
        
        event_type = event.type if hasattr(event, 'type') else event.stream
        
        try:
            # Remember event context
            await self._remember_event_context(event)
            
            # Route to appropriate handler
            if "analysis" in event_type and "complete" in event_type:
                result = await self.generate_ticker_narrative(event)
            elif "comparison" in event_type and "complete" in event_type:
                result = await self.generate_comparison_narrative(event)
            elif "screening" in event_type and "complete" in event_type:
                result = await self.generate_screening_narrative(event)
            elif "orthodoxy" in event_type and "verdict" in event_type:
                result = await self.generate_verdict_narrative(event)
            elif "portfolio:analysis:complete" in event_type:
                result = await self.generate_portfolio_narrative(event)
            else:
                logger.warning(f"⚠️ Unhandled event type: {event_type}")
                return None
            
            # Check confidence
            if result.confidence < self.config.confidence_threshold:
                logger.warning(
                    f"⚠️ Low confidence narrative ({result.confidence:.2f}), "
                    f"escalating to governance"
                )
                return await self.escalate(
                    event,
                    reason=f"Narrative confidence {result.confidence:.2f} below threshold"
                )
            
            # Emit result
            return ProcessResult.emit(event.child(
                event_type="narratives.generated",
                payload=result.to_dict(),
                source=self.config.name
            ))
            
        except Exception as e:
            logger.error(f"❌ Narrative generation failed: {e}")
            # Advisory consumer - can fail without breaking system
            return None
    
    async def generate_ticker_narrative(self, event: CognitiveEvent) -> NarrativeResult:
        """
        Generate narrative for single ticker analysis.
        
        Uses VEEEngine.explain_ticker() for 3-level explanation:
        - Level 1 (Summary): Conversational, non-technical
        - Level 2 (Detailed): Operational analysis
        - Level 3 (Technical): Z-scores explicit
        
        Args:
            event: Event with ticker analysis data
            
        Returns:
            NarrativeResult with 3-level narratives
        """
        payload = event.payload
        ticker = payload.get("ticker")
        kpi = payload.get("kpi", {})  # Numerical panel data
        language = payload.get("language", "en")
        
        if not ticker or not kpi:
            logger.warning(f"⚠️ Missing ticker or KPI data in event {event.id}")
            return NarrativeResult(
                event_id=event.id,
                narrative_type="ticker",
                summary="Insufficient data for narrative generation.",
                confidence=0.3,
                language=language
            )
        
        try:
            # Call VEE Engine for explanation
            vee_result = await asyncio.to_thread(
                self.vee.explain_ticker,
                ticker,
                kpi
            )
            
            return NarrativeResult(
                event_id=event.id,
                narrative_type="ticker",
                summary=vee_result.get("summary", ""),
                detailed=vee_result.get("detailed", ""),
                technical=vee_result.get("technical", ""),
                confidence=0.9,  # VEE is highly reliable
                language=language,
                metadata={"ticker": ticker, "vee_version": "2.0"}
            )
            
        except Exception as e:
            logger.error(f"❌ VEE explain_ticker failed: {e}")
            return NarrativeResult(
                event_id=event.id,
                narrative_type="ticker",
                summary=f"Error generating narrative for {ticker}.",
                confidence=0.2,
                language=language
            )
    
    async def generate_comparison_narrative(self, event: CognitiveEvent) -> NarrativeResult:
        """
        Generate narrative for ticker comparison.
        
        Uses VEEEngine.explain_comparison() for contrastive analysis.
        
        Args:
            event: Event with comparison data
            
        Returns:
            NarrativeResult with comparison narrative
        """
        payload = event.payload
        comparison_matrix = payload.get("comparison_matrix", {})
        language = payload.get("language", "en")
        
        if not comparison_matrix:
            logger.warning(f"⚠️ Missing comparison_matrix in event {event.id}")
            return NarrativeResult(
                event_id=event.id,
                narrative_type="comparison",
                summary="Insufficient comparison data.",
                confidence=0.3,
                language=language
            )
        
        try:
            # Extract tickers from comparison_matrix
            tickers = list(comparison_matrix.keys())
            
            # Call VEE Engine for comparison explanation
            vee_result = await asyncio.to_thread(
                self.vee.explain_comparison,
                tickers,
                comparison_matrix
            )
            
            return NarrativeResult(
                event_id=event.id,
                narrative_type="comparison",
                summary=vee_result.get("summary", ""),
                detailed=vee_result.get("detailed", ""),
                technical=vee_result.get("technical", ""),
                confidence=0.9,
                language=language,
                metadata={
                    "tickers": list(comparison_matrix.keys()),
                    "vee_version": "2.0"
                }
            )
            
        except Exception as e:
            logger.error(f"❌ VEE explain_comparison failed: {e}")
            return NarrativeResult(
                event_id=event.id,
                narrative_type="comparison",
                summary="Error generating comparison narrative.",
                confidence=0.2,
                language=language
            )
    
    async def generate_screening_narrative(self, event: CognitiveEvent) -> NarrativeResult:
        """
        Generate narrative for screening/ranking results.
        
        Uses VEEEngine.explain_screening() for ranking explanation.
        
        Args:
            event: Event with screening data
            
        Returns:
            NarrativeResult with screening narrative
        """
        payload = event.payload
        screening_data = payload.get("screening_data", [])
        language = payload.get("language", "en")
        
        if not screening_data:
            logger.warning(f"⚠️ Missing screening_data in event {event.id}")
            return NarrativeResult(
                event_id=event.id,
                narrative_type="screening",
                summary="Insufficient screening data.",
                confidence=0.3,
                language=language
            )
        
        try:
            # Call VEE Engine for screening explanation
            vee_result = await asyncio.to_thread(
                self.vee.explain_screening,
                screening_data=screening_data,
                language=language
            )
            
            return NarrativeResult(
                event_id=event.id,
                narrative_type="screening",
                summary=vee_result.get("summary", ""),
                detailed=vee_result.get("detailed", ""),
                technical=vee_result.get("technical", ""),
                confidence=0.9,
                language=language,
                metadata={
                    "num_tickers": len(screening_data),
                    "vee_version": "2.0"
                }
            )
            
        except Exception as e:
            logger.error(f"❌ VEE explain_screening failed: {e}")
            return NarrativeResult(
                event_id=event.id,
                narrative_type="screening",
                summary="Error generating screening narrative.",
                confidence=0.2,
                language=language
            )
    
    async def generate_verdict_narrative(self, event: CognitiveEvent) -> NarrativeResult:
        """
        Generate narrative for Orthodoxy verdict.
        
        Translates technical verdicts into human-readable explanations.
        Handles: blessed, purified, heretical, non_liquet, clarification_needed
        
        Args:
            event: Event with verdict data
            
        Returns:
            NarrativeResult with verdict explanation
        """
        payload = event.payload
        verdict_status = payload.get("status", "unknown")
        language = payload.get("language", "en")
        
        # Simple template-based narrative (no VEE needed for verdicts)
        narratives = {
            "en": {
                "blessed": "Analysis validated - all checks passed.",
                "purified": "Analysis corrected - minor issues resolved.",
                "heretical": "Analysis rejected - hallucination detected.",
                "non_liquet": "Insufficient certainty - explicit uncertainty declared.",
                "clarification_needed": "Query ambiguous - please clarify."
            },
            "it": {
                "blessed": "Analisi validata - tutti i controlli superati.",
                "purified": "Analisi corretta - problemi minori risolti.",
                "heretical": "Analisi rifiutata - allucinazione rilevata.",
                "non_liquet": "Certezza insufficiente - incertezza esplicita.",
                "clarification_needed": "Query ambigua - chiarire la richiesta."
            }
        }
        
        lang_dict = narratives.get(language, narratives["en"])
        summary = lang_dict.get(verdict_status, f"Unknown verdict: {verdict_status}")
        
        return NarrativeResult(
            event_id=event.id,
            narrative_type="verdict",
            summary=summary,
            confidence=0.95,  # Template-based, high confidence
            language=language,
            metadata={"verdict_status": verdict_status}
        )
    
    async def generate_portfolio_narrative(self, event: CognitiveEvent) -> NarrativeResult:
        """
        Generate narrative for portfolio analysis.
        
        Uses VEEEngine.explain_portfolio() for portfolio-level explanation.
        
        Args:
            event: Event with portfolio data
            
        Returns:
            NarrativeResult with portfolio narrative
        """
        payload = event.payload
        portfolio_data = payload.get("portfolio_data", {})
        language = payload.get("language", "en")
        
        if not portfolio_data:
            logger.warning(f"⚠️ Missing portfolio_data in event {event.id}")
            return NarrativeResult(
                event_id=event.id,
                narrative_type="portfolio",
                summary="Insufficient portfolio data.",
                confidence=0.3,
                language=language
            )
        
        try:
            # Call VEE Engine for portfolio explanation
            vee_result = await asyncio.to_thread(
                self.vee.explain_portfolio,
                portfolio_data=portfolio_data,
                language=language
            )
            
            return NarrativeResult(
                event_id=event.id,
                narrative_type="portfolio",
                summary=vee_result.get("summary", ""),
                detailed=vee_result.get("detailed", ""),
                technical=vee_result.get("technical", ""),
                confidence=0.9,
                language=language,
                metadata={
                    "num_holdings": len(portfolio_data.get("holdings", [])),
                    "vee_version": "2.0"
                }
            )
            
        except Exception as e:
            logger.error(f"❌ VEE explain_portfolio failed: {e}")
            return NarrativeResult(
                event_id=event.id,
                narrative_type="portfolio",
                summary="Error generating portfolio narrative.",
                confidence=0.2,
                language=language
            )
    
    async def _remember_event_context(self, event: CognitiveEvent) -> None:
        """
        Store event context in working memory for future reference.
        
        Enables context-aware narrative generation across events.
        
        Args:
            event: Event to remember
        """
        try:
            # Store last event type
            await self.memory.remember(
                key="context:last_event_type",
                value=event.type
            )
            
            # Store last event ID
            await self.memory.remember(
                key="context:last_event_id",
                value=event.id
            )
            
            # Store correlation ID for tracking
            if event.correlation_id:
                await self.memory.remember(
                    key=f"correlation:{event.correlation_id}",
                    value={
                        "event_id": event.id,
                        "event_type": event.type,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to store event context: {e}")


# Example standalone usage
if __name__ == "__main__":
    async def main():
        # Initialize consumer
        engine = NarrativeEngine()
        
        # Test ticker narrative
        test_event = CognitiveEvent(
            stream="vitruvyan:analysis:complete",
            event_id=f"{int(time.time() * 1000)}-0",
            emitter="neural_engine",
            payload={
                "ticker": "AAPL",
                "kpi": {
                    "composite_z": 1.25,
                    "momentum_z": 1.5,
                    "trend_z": 1.0,
                    "volatility_z": 0.8,
                    "sentiment_z": 0.9,
                    "fundamental_z": 1.2
                },
                "language": "en"
            },
            timestamp=datetime.utcnow().isoformat(),
            correlation_id="test-123"
        )
        
        result = await engine.process(test_event)
        
        if result:
            print("✅ Narrative generated:")
            print(json.dumps(result.payload, indent=2))
        else:
            print("❌ No narrative generated (low confidence or error)")
    
    asyncio.run(main())
