# core/langgraph/node/sentiment_node.py

import datetime
import httpx
import os
from core.foundation.persistence.postgres_agent import PostgresAgent
from core.foundation.persistence.qdrant_agent import QdrantAgent
from core.foundation.persistence.sentiment_persistence import save_sentiment_score
from core.foundation.persistence.sentiment_persistence_qdrant import save_sentiment_dual  # 🌿 Dual-memory support
from core.orchestration.langgraph.shared.state_preserv import preserve_ux_state  # 🎭 UX state preservation

FRESHNESS_HOURS = 24

# 🌿 Babel Gardens Unified API (PHASE 1 Migration)
# Replaced legacy vitruvyan_api_sentiment:8001 with Babel Gardens unified service
SENTIMENT_API_URL = os.getenv("SENTIMENT_API_URL", "http://vitruvyan_babel_gardens:8009")
BABEL_FUSION_ENABLED = os.getenv("BABEL_GARDENS_FUSION_ENABLED", "true").lower() == "true"
BABEL_FUSION_MODE = os.getenv("BABEL_GARDENS_FUSION_MODE", "enhanced")


@preserve_ux_state
def run_sentiment_node(state: dict) -> dict:
    """
    Enriches state with sentiment for each ticker.
    Versione ottimizzata: usa l'endpoint batch del Sentiment Engine.
    """
    tickers = state.get("tickers", [])
    print(f"\n{'🎭'*40}")
    print(f"🎭 [SENTIMENT_NODE] ===== ENTRY =====")
    print(f"🎭 Tickers to process: {tickers}")
    print(f"🎭 Intent: {state.get('intent')}")
    print(f"🎭 Route: {state.get('route')}")
    print(f"🎭 State keys: {list(state.keys())}")
    print(f"{'🎭'*40}\n")
    
    print(f"\n🔎 [sentiment_node] Avvio nodo, tickers={tickers}")
    print("✅ SENTIMENT NODE ESEGUITO con tickers:", tickers)


    if not tickers:
        print("⚠️ Nessun ticker nello stato → skip sentiment_node")
        return state

    pg = PostgresAgent()
    enriched = {}
    stale_tickers = []

    # 1. Controllo cache in DB
    for ticker in tickers:
        print(f"\n➡️ Processing ticker={ticker}")
        row = None
        try:
            with pg.connection.cursor() as cur:
                cur.execute("""
                    SELECT ticker, combined_score, sentiment_tag, created_at
                    FROM sentiment_scores
                    WHERE ticker = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (ticker,))
                row = cur.fetchone()
        except Exception as e:
            print(f"❌ Errore query sentiment_scores per {ticker}: {e}")

        if row:
            _, score, tag, created_at = row
            age_hours = (datetime.datetime.now() - created_at).total_seconds() / 3600
            print(f"   ↪ trovato in DB: score={score}, tag={tag}, at={created_at} (età {age_hours:.1f}h)")
            if age_hours < FRESHNESS_HOURS:
                enriched[ticker] = {
                    "ticker": ticker,
                    "sentiment_raw": score,
                    "sentiment_tag": tag,
                    "sentiment_at": created_at.isoformat()
                }
                print(f"   ✅ uso DB (fresco < {FRESHNESS_HOURS}h)")
            else:
                stale_tickers.append(ticker)
        else:
            stale_tickers.append(ticker)

    # 2. Batch API call per i ticker mancanti o stantii
    if stale_tickers:
        print(f"\n🔄 Chiamata Sentiment API batch per tickers={stale_tickers} ...")
        
        # 🌿 Babel Gardens Unified Sentiment API (PHASE 1)
        # Always use Babel Gardens - fusion is built-in
        endpoint = "/v1/sentiment/batch"
        
        # 🔥 FIX: Use actual user input_text for sentiment analysis, not generic ticker text
        user_input = state.get("input_text", "").strip()
        if user_input:
            # Use user's actual text for each ticker context
            texts_to_analyze = [f"{user_input} {tk}" for tk in stale_tickers]
            print(f"   📝 Using user input text: '{user_input}'")
        else:
            # Fallback to ticker-only if no input_text
            texts_to_analyze = [f"{tk} stock market sentiment analysis" for tk in stale_tickers]
            print(f"   ⚠️ No input_text, using generic ticker text")
        
        # Prepare texts for Babel Gardens sentiment analysis
        request_payload = {
            "texts": texts_to_analyze,
            "language": "auto",
            "fusion_mode": BABEL_FUSION_MODE if BABEL_FUSION_ENABLED else "standard",
            "use_cache": True
        }
        print(f"   🌿 Using Babel Gardens unified sentiment (fusion_mode: {request_payload['fusion_mode']})")
        
        try:
            url = f"{SENTIMENT_API_URL}{endpoint}"
            resp = httpx.post(url, json=request_payload, timeout=60)
            print(f"✅ Sentiment API batch status={resp.status_code}")

            if resp.status_code == 200:
                response_data = resp.json()
                created_at = datetime.datetime.now()

                # 🌿 Parse Babel Gardens unified response
                # Format: {"status": "success", "results": [{...}, {...}]}
                results_list = response_data.get("results", [])
                
                for idx, tk in enumerate(stale_tickers):
                    if idx >= len(results_list):
                        print(f"   ⚠️ Missing result for {tk}")
                        continue
                    
                    result = results_list[idx]
                    
                    # Extract sentiment data from Babel Gardens response
                    # Format: {"sentiment": {"label": "positive", "score": 0.85}, "confidence": 0.85}
                    sentiment_data_raw = result.get("sentiment", {})
                    
                    # Get score and label from Babel Gardens format
                    combined = sentiment_data_raw.get("score", 0.0)  # Babel Gardens score (0.0-1.0)
                    tag = sentiment_data_raw.get("label", "neutral").lower()  # "positive", "negative", "neutral"
                    confidence = result.get("confidence", 0.0)
                    
                    # Convert score to [-1, 1] range for database compatibility
                    # positive: 0.5-1.0 → 0.0-1.0, negative: 0.0-0.5 → -1.0-0.0, neutral: ~0.5 → 0.0
                    if tag == "positive":
                        combined = (combined - 0.5) * 2  # Map 0.5-1.0 to 0.0-1.0
                    elif tag == "negative":
                        combined = (combined - 0.5) * 2  # Map 0.0-0.5 to -1.0-0.0
                    else:  # neutral
                        combined = 0.0
                    
                    # Extract fusion metadata if available
                    model_fusion = result.get("model_fusion", {})
                    fusion_boost = model_fusion.get("confidence_boost", 0.0)
                    embedding_used = "embedding" in model_fusion.get("models_used", [])
                    
                    print(f"   🌿 {tk}: score={combined:.3f}, tag={tag}, conf={confidence:.3f}, fusion_boost={fusion_boost:.3f}, embedding={embedding_used}")
                    
                    # 🌿 DUAL-MEMORY WRITE: PostgreSQL + Qdrant (PHASE A3.2)
                    # Store in PostgreSQL + Qdrant (phrases_fused, sentiment_embeddings)
                    dual_success = save_sentiment_dual(
                        ticker=tk,
                        combined_score=combined,
                        sentiment_tag=tag,
                        user_text=user_input,  # Use actual user input for semantic embedding
                        confidence=confidence,
                        fusion_boost=fusion_boost,
                        embedding_used=embedding_used
                    )
                    print(f"   🌿 save_sentiment_dual {tk} executed: {dual_success}")

                    sentiment_data = {
                        "ticker": tk,
                        "sentiment_raw": combined,
                        "sentiment_tag": tag,
                        "sentiment_at": created_at.isoformat(),
                        "confidence": confidence,
                        "fusion_boost": fusion_boost,
                        "embedding_used": embedding_used
                    }
                    enriched[tk] = sentiment_data

                    # Deduplication save
                    try:
                        dedupe_key = f"{tk}_{created_at.isoformat()}_babel"
                        save_sentiment_score(
                            ticker=tk,
                            score=combined,
                            sentiment_tag=tag,
                            dedupe_key=dedupe_key
                        )
                        print(f"   💾 save_sentiment_score eseguito per {tk}")
                    except Exception as e:
                        print(f"   ⚠️ Errore save_sentiment_score per {tk}: {e}")

            else:
                print(f"   ❌ API batch status={resp.status_code}, body={resp.text}")
        except Exception as e:
            print(f"   ❌ Errore chiamata Sentiment API batch: {e}")

    # 3. Update state
    state["sentiment"] = enriched
    print(f"\n🔎 [sentiment_node] Stato finale aggiornato con sentiment={enriched}\n")
    return state
