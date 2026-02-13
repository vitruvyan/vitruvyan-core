"""
Sentiment Fusion Module — LLM-First Textual Sentiment Analysis (Nuclear Option)

Epistemic Order: PERCEPTION (Linguistic Reasoning)
Architecture: LLM-first with heuristic graceful degradation

Golden Rule (copilot-instructions.md):
  "LLM-first, never heuristics-first (Nuclear Option): linguistic understanding
   MUST delegate to LLM as primary engine. Regex/keyword/pattern-matching are
   ONLY allowed as graceful-degradation fallback when LLM is unavailable."

Cascade:
  PRIORITY 1: LLM (GPT-4o-mini, temperature=0, JSON mode)
    - Understands ANY language, context, irony, domain
    - Granular sentiment (label + score + aspects)
    - ~95% accuracy, ~$0.0002/call
  PRIORITY 2: Heuristic Fallback (if LLM unavailable)
    - Punctuation/keyword-based polarity estimation
    - ~55% accuracy, 0 cost
    - ONLY for graceful degradation, NEVER as primary path

Domain-Agnostic:
  The module does NOT assume finance, healthcare, or any vertical.
  Domain-specific sentiment (e.g., market sentiment) is handled by
  domain plugins / GraphPlugin overrides — NOT here.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ── LLM System Prompt ──
SENTIMENT_SYSTEM_PROMPT = """You are a sentiment analysis engine for a multilingual AI system.
Analyze the user's text and determine its sentiment.

You MUST respond with ONLY a valid JSON object (no markdown, no explanation):
{
  "label": "<positive|negative|neutral|mixed>",
  "score": <-1.0 to 1.0>,
  "magnitude": <0.0 to 1.0>,
  "aspects": [
    {"aspect": "<topic/aspect>", "sentiment": "<positive|negative|neutral>", "score": <-1.0 to 1.0>}
  ],
  "reasoning": "<brief explanation>",
  "language_detected": "<ISO 639-1 language code>"
}

Rules:
- score: -1.0 = very negative, 0.0 = neutral, 1.0 = very positive
- magnitude: strength of sentiment expression (0.0 = flat/factual, 1.0 = intense)
- aspects: extract up to 3 key aspects/topics with per-aspect sentiment
- mixed: use when text contains both positive AND negative sentiment
- Detect language automatically — you understand ALL languages.
- Consider cultural norms and context.
- Sarcasm/irony: "perfetto, un altro errore" = negative, not positive.
- Factual statements with no opinion = neutral with low magnitude.
"""


class SentimentFusionModule:
    """LLM-first sentiment analysis with heuristic graceful degradation."""

    def __init__(self):
        self.name = "sentiment_fusion"
        self.version = "2.0.0"
        self.max_batch_size = 25
        self._llm = None  # Lazy initialization

    def _get_llm(self):
        """Lazy-load LLMAgent singleton (avoids import at module load)."""
        if self._llm is None:
            try:
                from core.agents.llm_agent import get_llm_agent
                self._llm = get_llm_agent()
                logger.info("📊 SentimentFusion: LLMAgent connected (LLM-first mode)")
            except Exception as e:
                logger.warning(f"📊 SentimentFusion: LLMAgent unavailable ({e}), heuristic-only mode")
        return self._llm

    async def analyze(
        self,
        text: str,
        language: str = "auto",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of a single text — LLM primary, heuristic fallback.

        Returns dict with label, score, magnitude, aspects, metadata.
        """
        start_time = datetime.now()

        if not text or not text.strip():
            return self._empty_response("Empty input", start_time)

        # ── PRIORITY 1: LLM (Nuclear Option) ──
        llm = self._get_llm()
        if llm is not None:
            try:
                result = self._analyze_via_llm(llm, text, language, context)
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                result["metadata"] = {
                    "language": result.pop("language_detected", language),
                    "processing_time_ms": round(elapsed_ms, 2),
                    "models_used": ["llm_gpt4o_mini"],
                    "method": "llm_primary",
                    "fallback_used": False,
                }
                return result
            except Exception as e:
                logger.warning(f"📊 LLM sentiment analysis failed ({e}), falling back to heuristic")

        # ── PRIORITY 2: Heuristic Fallback (graceful degradation only) ──
        logger.info("📊 Using heuristic fallback for sentiment (degraded mode)")
        result = self._analyze_via_heuristic(text)
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        result["metadata"] = {
            "language": language,
            "processing_time_ms": round(elapsed_ms, 2),
            "models_used": ["heuristic_fallback"],
            "method": "heuristic_fallback",
            "fallback_used": True,
        }
        return result

    async def analyze_batch(
        self,
        texts: List[str],
        language: str = "auto",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze sentiment for a batch of texts.

        Processes each text through the same LLM-first cascade.
        """
        start_time = datetime.now()

        if not texts:
            return {"status": "error", "results": [], "error": "No texts provided"}

        if len(texts) > self.max_batch_size:
            return {
                "status": "error",
                "results": [],
                "error": f"Batch size {len(texts)} exceeds limit {self.max_batch_size}",
            }

        results = []
        for text in texts:
            result = await self.analyze(text, language, context)
            results.append({
                "text": text[:100],  # Truncate for response readability
                "label": result.get("label", "neutral"),
                "score": result.get("score", 0.0),
                "magnitude": result.get("magnitude", 0.0),
                "aspects": result.get("aspects", []),
                "error": result.get("error"),
            })

        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        valid_scores = [r["score"] for r in results if r["score"] != 0.0]
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

        return {
            "status": "success",
            "results": results,
            "summary": {
                "total": len(results),
                "avg_score": round(avg_score, 3),
                "positive": sum(1 for r in results if r["score"] > 0.1),
                "negative": sum(1 for r in results if r["score"] < -0.1),
                "neutral": sum(1 for r in results if -0.1 <= r["score"] <= 0.1),
            },
            "metadata": {
                "processing_time_ms": round(elapsed_ms, 2),
                "batch_size": len(texts),
            },
        }

    # ── PRIMARY: LLM Analysis ──

    def _analyze_via_llm(
        self,
        llm,
        text: str,
        language: str,
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Call LLM for sentiment analysis (Nuclear Option — primary engine)."""
        prompt = f"Analyze the sentiment of this text:\n\n\"{text}\""
        if language and language != "auto":
            prompt += f"\n\n(Language hint: {language})"
        if context:
            prompt += f"\n\nConversation context: {json.dumps(context, ensure_ascii=False)}"

        result = llm.complete_json(
            prompt=prompt,
            system_prompt=SENTIMENT_SYSTEM_PROMPT,
            temperature=0.0,
            max_tokens=300,
        )

        # Validate and normalize LLM response
        label = result.get("label", "neutral")
        if label not in ("positive", "negative", "neutral", "mixed"):
            label = "neutral"

        score = float(result.get("score", 0.0))
        score = max(-1.0, min(1.0, score))

        magnitude = float(result.get("magnitude", 0.5))
        magnitude = max(0.0, min(1.0, magnitude))

        aspects = result.get("aspects", [])
        if not isinstance(aspects, list):
            aspects = []

        return {
            "status": "success",
            "label": label,
            "score": score,
            "magnitude": magnitude,
            "aspects": aspects[:5],  # Cap at 5 aspects
            "reasoning": result.get("reasoning", "LLM classification"),
            "language_detected": result.get("language_detected", "unknown"),
            "error": None,
        }

    # ── FALLBACK: Heuristic Analysis (graceful degradation only) ──

    def _analyze_via_heuristic(self, text: str) -> Dict[str, Any]:
        """
        Basic heuristic sentiment — ONLY for graceful degradation.

        Uses punctuation density, exclamation marks, question marks,
        and a minimal keyword set. Intentionally low-accuracy (~55%).
        """
        text_lower = text.lower().strip()

        # Simple polarity signals
        positive_signals = 0
        negative_signals = 0

        # Exclamation = intensity (could be positive or negative)
        excl_count = text.count("!")
        quest_count = text.count("?")

        # Minimal keyword lists — intentionally small
        _POS = ["thank", "grazie", "perfect", "great", "love", "excellent",
                "good", "happy", "fantastic", "wonderful", "bravo", "bene"]
        _NEG = ["error", "errore", "problem", "fail", "bad", "hate", "wrong",
                "terrible", "awful", "disgusting", "broken", "worst", "bug"]

        for w in _POS:
            if w in text_lower:
                positive_signals += 1
        for w in _NEG:
            if w in text_lower:
                negative_signals += 1

        # Crude score
        if positive_signals > negative_signals:
            label = "positive"
            score = min(0.5, 0.2 * positive_signals)
        elif negative_signals > positive_signals:
            label = "negative"
            score = max(-0.5, -0.2 * negative_signals)
        else:
            label = "neutral"
            score = 0.0

        magnitude = min(1.0, (excl_count * 0.15) + (abs(positive_signals - negative_signals) * 0.1))

        return {
            "status": "success",
            "label": label,
            "score": round(score, 2),
            "magnitude": round(magnitude, 2),
            "aspects": [],
            "reasoning": "Heuristic fallback (degraded mode — LLM unavailable)",
            "error": None,
        }

    # ── Helpers ──

    def _empty_response(self, reason: str, start_time: datetime) -> Dict[str, Any]:
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        return {
            "status": "success",
            "label": "neutral",
            "score": 0.0,
            "magnitude": 0.0,
            "aspects": [],
            "reasoning": reason,
            "error": None,
            "metadata": {
                "language": "unknown",
                "processing_time_ms": round(elapsed_ms, 2),
                "models_used": [],
                "method": "none",
                "fallback_used": False,
            },
        }
