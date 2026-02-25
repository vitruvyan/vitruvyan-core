"""
Shadow Trading Node — Finance Domain
=====================================

LangGraph node for executing shadow (paper) trading orders.

Translates shadow_buy/shadow_sell intents into HTTP calls to the
Shadow Traders API. Includes Orthodoxy pre-trade validation.

Pipeline position:
  decide (route=shadow_buy|shadow_sell) → shadow_trading → output_normalizer

Intents handled:
  - shadow_buy  → POST /shadow/buy
  - shadow_sell → POST /shadow/sell

State inputs:
  - intent: str ("shadow_buy" or "shadow_sell")
  - tickers: List[str] (single ticker, MVP)
  - quantity: int (number of shares)
  - user_id: str
  - input_text: str (original query)

State outputs:
  - shadow_trade_result: Dict (order execution result)
  - portfolio_updated: bool (True if order filled)

Author: Ported from vitruvyan upstream (Jan 3, 2026)
Adapted: February 24, 2026 (mercator domain pattern)
Status: PRODUCTION
"""

import os
import logging
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)

SHADOW_TRADERS_URL = os.getenv(
    "SHADOW_TRADERS_URL", "http://vitruvyan_shadow_traders:8020"
)


def shadow_trading_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute shadow trading order from LangGraph state.

    Flow:
    1. Validate intent (shadow_buy / shadow_sell)
    2. Extract ticker + quantity from state
    3. Orthodoxy pre-trade check (fail-safe: proceeds on error)
    4. Call Shadow Traders API
    5. Return result in state
    """
    intent = (state.get("intent") or "").lower()

    if intent not in ("buy", "sell", "shadow_buy", "shadow_sell"):
        logger.debug(f"[shadow_trading] Not a shadow trading intent: {intent}")
        return state  # passthrough

    logger.info(f"[shadow_trading] Activated: intent={intent}")

    tickers = state.get("tickers", [])
    quantity = state.get("quantity")
    user_id = state.get("user_id")
    input_text = state.get("input_text", "")

    # --- validation -------------------------------------------------------
    if not tickers:
        return {
            **state,
            "shadow_trade_result": {
                "status": "rejected",
                "message": "Missing ticker. Example: 'buy 100 AAPL'",
            },
        }

    if not quantity or quantity <= 0:
        return {
            **state,
            "shadow_trade_result": {
                "status": "rejected",
                "message": "Missing or invalid quantity. Example: 'buy 100 AAPL'",
            },
        }

    if not user_id:
        return {
            **state,
            "shadow_trade_result": {
                "status": "rejected",
                "message": "User authentication required",
            },
        }

    ticker = tickers[0]  # MVP: single ticker
    side = "buy" if "buy" in intent else "sell"

    # --- Orthodoxy pre-trade check (fail-safe) ----------------------------
    try:
        pre_check_url = f"{SHADOW_TRADERS_URL}/pre_trade_check"
        pre_check_payload = {
            "user_id": user_id,
            "ticker": ticker,
            "quantity": quantity,
            "side": side,
            "reason": f"Shadow trading: {intent}",
            "input_text": input_text,
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(pre_check_url, json=pre_check_payload)

        if resp.status_code == 200:
            result = resp.json()
            orthodoxy_status = result.get("orthodoxy_status", "unknown")
            approved = result.get("approved", False)
            concerns = result.get("concerns", [])
            vee_narrative = result.get("vee_narrative", "")

            logger.info(
                f"[shadow_trading] Orthodoxy: {orthodoxy_status.upper()} approved={approved}"
            )

            if orthodoxy_status == "heretical" or not approved:
                logger.warning(
                    f"[shadow_trading] Trade REJECTED: {', '.join(concerns)}"
                )
                return {
                    **state,
                    "shadow_trade_result": {
                        "status": "rejected",
                        "message": f"Trade rejected by Orthodoxy: {', '.join(concerns)}",
                        "orthodoxy_status": orthodoxy_status,
                        "vee_narrative": vee_narrative,
                        "concerns": concerns,
                    },
                    "portfolio_updated": False,
                }
        else:
            logger.warning(
                f"[shadow_trading] Pre-trade check HTTP {resp.status_code} — proceeding"
            )
    except Exception as exc:
        logger.warning(f"[shadow_trading] Pre-trade check failed: {exc} — proceeding")

    # --- Execute trade ----------------------------------------------------
    try:
        endpoint = f"{SHADOW_TRADERS_URL}/shadow/{side}"
        payload = {
            "user_id": user_id,
            "ticker": ticker,
            "quantity": quantity,
            "reason": f"Shadow trading: {intent}",
            "input_text": input_text,
        }

        logger.info(f"[shadow_trading] {side.upper()} {quantity} {ticker}")

        with httpx.Client(timeout=30.0) as client:
            response = client.post(endpoint, json=payload)

        if response.status_code == 200:
            result = response.json()
            logger.info(f"[shadow_trading] OK: {result.get('message', 'filled')}")
            return {
                **state,
                "shadow_trade_result": result,
                "portfolio_updated": result.get("status") == "filled",
            }
        else:
            error_msg = response.text
            logger.error(f"[shadow_trading] API error: {error_msg}")
            return {
                **state,
                "shadow_trade_result": {
                    "status": "rejected",
                    "message": f"Shadow Broker error: {error_msg}",
                },
            }

    except httpx.TimeoutException:
        logger.error("[shadow_trading] API timeout")
        return {
            **state,
            "shadow_trade_result": {
                "status": "rejected",
                "message": "Shadow Broker service unavailable (timeout)",
            },
        }
    except Exception as exc:
        logger.error(f"[shadow_trading] Error: {exc}")
        return {
            **state,
            "shadow_trade_result": {
                "status": "rejected",
                "message": f"Shadow trade failed: {exc}",
            },
        }
