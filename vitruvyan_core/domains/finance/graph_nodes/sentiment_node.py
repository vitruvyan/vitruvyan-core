"""
Finance Domain — Sentiment Node
=================================

Ticker-based sentiment enrichment via Babel Gardens unified API.
Analyzes sentiment for each ticker using real phrases or user input as context.

Pipeline position: decide → sentiment → output_normalizer
Triggered when: intent="sentiment" OR as enrichment after screener

State inputs:
    - tickers: list     — Ticker symbols to analyze
    - input_text: str   — User query (fallback context)
    - intent: str       — User intent

State outputs:
    - sentiment: dict   — {ticker: {sentiment_raw, sentiment_tag, confidence, ...}}

External calls:
    - POST {BABEL_GARDENS_URL}/v1/sentiment/batch

Author: Vitruvyan Finance Vertical
Created: February 24, 2026
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)

# Babel Gardens service URL
BABEL_GARDENS_URL = os.getenv(
    "BABEL_GARDENS_URL", "http://vitruvyan_babel_gardens:8004"
)
BABEL_FUSION_MODE = os.getenv("BABEL_GARDENS_FUSION_MODE", "enhanced")


def sentiment_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sentiment enrichment for finance tickers via Babel Gardens.

    For each ticker:
      1. Build context text (user input + ticker symbol)
      2. Call Babel Gardens /v1/sentiment/batch
      3. Normalize scores from [0,1] → [-1,1]
      4. Store enriched sentiment in state
    """
    tickers = state.get("tickers", [])

    if not tickers:
        logger.info("[sentiment_node] No tickers, skipping")
        return state

    logger.info(f"[sentiment_node] Analyzing sentiment for {len(tickers)} tickers")

    user_input = state.get("input_text", "").strip()
    enriched: Dict[str, Dict[str, Any]] = {}

    # Build context texts for each ticker
    texts: List[str] = []
    for tk in tickers:
        if user_input:
            texts.append(f"{user_input} {tk}")
        else:
            texts.append(f"{tk} stock market analysis sentiment")

    # Call Babel Gardens batch API
    payload = {
        "texts": texts,
        "language": "auto",
        "fusion_mode": BABEL_FUSION_MODE,
        "use_cache": False,
    }

    try:
        url = f"{BABEL_GARDENS_URL}/v1/sentiment/batch"
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()

        data = resp.json()
        results = data.get("results", [])
        now = datetime.utcnow()

        for idx, tk in enumerate(tickers):
            if idx >= len(results):
                logger.warning(f"[sentiment_node] Missing result for {tk}")
                continue

            result = results[idx]
            sentiment_data = result.get("sentiment", {})

            # Extract score (0.0–1.0) and label
            raw_score = sentiment_data.get("score", 0.5)
            label = sentiment_data.get("label", "neutral").lower()
            confidence = result.get("confidence", 0.0)
            language = result.get("language", "en")

            # Normalize to [-1, 1] range
            normalized = (raw_score - 0.5) * 2

            # Extract fusion metadata if available
            model_fusion = result.get("model_fusion", {})
            fusion_boost = model_fusion.get("confidence_boost", 0.0)
            embedding_used = "embedding" in model_fusion.get("models_used", [])

            enriched[tk] = {
                "ticker": tk,
                "sentiment_raw": round(normalized, 4),
                "sentiment_tag": label,
                "sentiment_at": now.isoformat(),
                "confidence": round(confidence, 4),
                "fusion_boost": round(fusion_boost, 4),
                "embedding_used": embedding_used,
                "language": language,
            }

            logger.debug(
                f"[sentiment_node] {tk}: score={normalized:.3f}, "
                f"tag={label}, conf={confidence:.3f}"
            )

        logger.info(
            f"[sentiment_node] Enriched {len(enriched)}/{len(tickers)} tickers"
        )

    except httpx.TimeoutException:
        logger.warning("[sentiment_node] Babel Gardens timeout")
        state["error"] = "Sentiment analysis timeout"

    except httpx.HTTPStatusError as e:
        logger.error(
            f"[sentiment_node] Babel Gardens HTTP {e.response.status_code}"
        )
        state["error"] = f"Sentiment API error: {e.response.status_code}"

    except Exception as e:
        logger.error(f"[sentiment_node] Error: {e}")
        state["error"] = f"Sentiment error: {e}"

    state["sentiment"] = enriched
    return state
