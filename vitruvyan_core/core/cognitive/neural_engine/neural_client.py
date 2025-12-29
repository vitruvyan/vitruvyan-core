"""
Neural Engine HTTP Client
Calls the Neural Engine API for ranking and analysis.
"""
import os
import requests
from typing import Any, Dict, List, Optional

DEFAULT_BASE = os.getenv("NE_BASE_URL", "http://vitruvyan_api_neural:8003")


def _try_post(url: str, payload: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e), "base_url": url, "payload": payload}


def get_ne_ranking(
    profile: str = "short_spec",
    top_k: int = 10,
    filters: Optional[Dict[str, Any]] = None,
    mode: str = "discovery",
    tickers: Optional[List[str]] = None,
    sector: Optional[str] = None,
    risk_tolerance: Optional[str] = None,
    momentum_breakout: bool = False,
    value_screening: bool = False,
    divergence_detection: bool = False,
    multi_timeframe_filter: bool = False,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Call Neural Engine. Always returns a dict (never raises).
    
    Args:
        profile: Ranking profile (balanced_mid, momentum_focus, etc.)
        top_k: Number of results
        filters: Additional filters
        mode: Operating mode:
            - "discovery": Top K from entire universe (default)
            - "analyze": Analyze ONLY requested tickers
            - "comparative": Requested tickers + top K alternatives
            - "sector": Top K from a specific sector
        tickers: List of tickers to analyze (used in mode=analyze/comparative)
        sector: Sector filter (e.g., 'Technology', 'Healthcare')
        risk_tolerance: Risk level ('low', 'medium', 'high')
        momentum_breakout: If True, filter only strong momentum tickers (momentum_z > 2.0)
        value_screening: If True, filter only undervalued stocks
        divergence_detection: If True, filter only tickers with price-RSI divergence
        multi_timeframe_filter: If True, filter only tickers with bullish consensus across timeframes
        timeout: HTTP request timeout
    """
    payload = {
        "profile": profile,
        "top_k": top_k,
        "mode": mode,
        "momentum_breakout": momentum_breakout,
        "value_screening": value_screening,
        "divergence_detection": divergence_detection,
        "multi_timeframe_filter": multi_timeframe_filter,
    }
    
    if tickers:
        payload["tickers"] = tickers
    
    if sector:
        payload["sector"] = sector
    
    if risk_tolerance:
        payload["risk_tolerance"] = risk_tolerance
    
    if filters:
        payload["filters"] = filters

    # Primary endpoint
    url = f"{DEFAULT_BASE}/neural"
    res = _try_post(url, payload, timeout)
    if "error" not in res:
        return res

    # Fallback for DNS errors - try localhost
    if any(x in res["error"] for x in ["Name or service not known", "Temporary failure in name resolution"]):
        url_fallback = "http://localhost:8003/neural"
        res = _try_post(url_fallback, payload, timeout)
    
    return res
