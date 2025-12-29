# api_neural_engine/api_server.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Set

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Carica .env dell'host (montato nel container)
load_dotenv("/home/caravaggio/vitruvyan/.env")

LOG_TO_FILE = os.getenv("NE_LOG_TO_FILE", "0") == "1"
LOG_PATH = os.getenv("NE_LOG_PATH", "/tmp/neural_engine_api.log")
LOG_LEVEL = os.getenv("NE_LOG_LEVEL", "INFO").upper()
log_kw = dict(level=getattr(logging, LOG_LEVEL, logging.INFO), format="%(asctime)s [%(levelname)s] %(message)s")
if LOG_TO_FILE:
    logging.basicConfig(filename=LOG_PATH, **log_kw)
else:
    logging.basicConfig(**log_kw)
logger = logging.getLogger("neural_engine_api")

# Import core NE
from core.cognitive.neural_engine import engine_core as ne  # noqa: E402

app = FastAPI(
    title="Vitruvyan Neural Engine API",
    description="API dedicata al Neural Engine (ranking multifattore con explainability)",
    version="1.1.0",
)

@app.get("/health")
async def health_check():
    """Health check endpoint for container monitoring"""
    return {
        "status": "healthy",
        "service": "neural_engine",
        "timestamp": datetime.now().isoformat(),
        "version": "1.1.0"
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

class NeuralEngineRequest(BaseModel):
    profile: str = Field(default="short_spec", description="Scoring profile (defines weights)")
    top_k: int = Field(default=5, ge=1, le=100, description="Maximum number of ranked items per bucket")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters (e.g. universe=[...])")
    tickers: Optional[List[str]] = Field(default=None, description="List of tickers to analyze (if specified, overrides the universe)")
    mode: str = Field(default="discovery", description="Mode: 'discovery', 'analyze', 'comparative', 'sector'")
    sector: Optional[str] = Field(default=None, description="Sector filter (e.g. 'Technology', 'Healthcare')")
    risk_tolerance: Optional[str] = Field(default=None, description="Risk tolerance: 'low', 'medium', 'high'")
    momentum_breakout: bool = Field(default=False, description="Function F: Filter only tickers with strong momentum breakout (momentum_z > 2.0)")
    value_screening: bool = Field(default=False, description="Function G: Filter only undervalued stocks (value > 0.5, quality > 0)")
    divergence_detection: bool = Field(default=False, description="Function H: Filter only tickers with price-RSI divergence (contrarian signals)")
    multi_timeframe_filter: bool = Field(default=False, description="Function I: Filter only tickers with bullish consensus across timeframes (mtf_consensus > 0.3)")
    portfolio_diversification: Optional[List[str]] = Field(default=None, description="Function J: Portfolio tickers for correlation filtering (returns tickers with avg_correlation < 0.3)")
    macro_factor: Optional[str] = Field(default=None, description="Function K: Macro factor filter ('inflation'|'rates'|'volatility'|'dollar')")
    time_decay_weighting: bool = Field(default=False, description="Function L: Apply exponential time decay exp(-days_old/30) to z-scores")
    smart_money_flow: bool = Field(default=False, description="Function P: Filter tickers with institutional accumulation (dark_pool_z > 1.5)")
    earnings_safety_days: Optional[int] = Field(default=None, description="Earnings Safety: Exclude tickers with earnings within N days (e.g., 7)")

REQUIRED_FACTOR_COLS: List[str] = ["momentum_z", "trend_z", "vola_z", "sentiment_z"]

def _compute_partial_results(ranked_df, stocks_top):
    """
    Returns (is_partial: bool, diag: dict) to understand what is missing in the Top-K.
    Handles stocks_top as a list of dicts or DataFrame.
    """
    required_cols = REQUIRED_FACTOR_COLS
    diag = {"top_tickers": [], "missing_cols": [], "nan_counts": {}}
    try:
        top_tickers = []
        if isinstance(stocks_top, list):
            for s in stocks_top:
                if isinstance(s, dict) and s.get("ticker"):
                    top_tickers.append(s["ticker"])
        elif hasattr(stocks_top, "columns"):
            if "ticker" in stocks_top.columns:
                top_tickers = [str(t) for t in stocks_top["ticker"].dropna().tolist()]
        diag["top_tickers"] = top_tickers

        if len(top_tickers) == 0:
            diag["reason"] = "empty_top"
            return True, diag

        sub = ranked_df[ranked_df["ticker"].isin(top_tickers)]

        for col in required_cols:
            if col not in sub.columns:
                diag["missing_cols"].append(col)

        for col in required_cols:
            if col in sub.columns:
                diag["nan_counts"][col] = int(sub[col].isna().sum())
            else:
                diag["nan_counts"][col] = None

        is_partial = bool(diag["missing_cols"]) or any(
            (diag["nan_counts"][c] or 0) > 0 for c in required_cols
        )
        return is_partial, diag
    except Exception as e:
        diag["reason"] = f"exception:{e}"
        return True, diag

def _run_neural_engine(
    profile: str = "short_spec", 
    top_k: int = 5, 
    filters: Optional[dict] = None,
    mode: str = "discovery",
    tickers: Optional[List[str]] = None,
    sector: Optional[str] = None,
    risk_tolerance: Optional[str] = None,
    momentum_breakout: bool = False,
    value_screening: bool = False,
    divergence_detection: bool = False,
    multi_timeframe_filter: bool = False,
    portfolio_diversification: Optional[List[str]] = None,
    macro_factor: Optional[str] = None,
    time_decay_weighting: bool = False,
    smart_money_flow: bool = False,
    earnings_safety_days: Optional[int] = None
) -> Dict[str, Any]:
    """
    NUOVO: Usa run_ne_once con supporto mode (analyze/discovery/comparative/sector), risk adjustment, 
    e tutte le Functions F-P (momentum, value, divergence, multi-timeframe, portfolio diversification, 
    macro sensitivity, time decay, smart money flow, earnings safety).
    """
    # Prepara tickers per run_ne_once
    if tickers:
        tickers_list = tickers
    elif filters and filters.get("tickers"):
        tickers_list = filters["tickers"]
    else:
        tickers_list = []
    
    # Chiamata diretta a run_ne_once con mode, sector, risk_tolerance e Functions F-P + Earnings Safety
    resp = ne.run_ne_once(
        profile=profile,
        tickers=tickers_list,
        top_k=top_k,
        mode=mode,
        sector=sector,
        risk_tolerance=risk_tolerance,
        momentum_breakout=momentum_breakout,
        value_screening=value_screening,
        divergence_detection=divergence_detection,
        multi_timeframe_filter=multi_timeframe_filter,
        portfolio_diversification=portfolio_diversification,
        macro_factor=macro_factor,
        time_decay_weighting=time_decay_weighting,
        smart_money_flow=smart_money_flow,
        earnings_safety_days=earnings_safety_days
    )
    
    return resp

@app.get("/", include_in_schema=False)
def _root():
    return {"service": "neural_engine", "version": app.version}

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "neural_engine",
        "db_host": os.getenv("POSTGRES_HOST", "undefined"),
        "db_db": os.getenv("POSTGRES_DB", "undefined"),
    }

@app.post("/neural-engine")
def neural_engine_endpoint(request: NeuralEngineRequest):
    try:
        logger.info(f"POST /neural-engine profile={request.profile} top_k={request.top_k} mode={request.mode} tickers={request.tickers} sector={request.sector} risk_tolerance={request.risk_tolerance} momentum_breakout={request.momentum_breakout} value_screening={request.value_screening} divergence_detection={request.divergence_detection} multi_timeframe_filter={request.multi_timeframe_filter} portfolio_diversification={request.portfolio_diversification} macro_factor={request.macro_factor} time_decay_weighting={request.time_decay_weighting} smart_money_flow={request.smart_money_flow} earnings_safety_days={request.earnings_safety_days}")
        
        resp = _run_neural_engine(
            profile=request.profile,
            top_k=request.top_k,
            filters=request.filters,
            mode=request.mode,
            tickers=request.tickers,
            sector=request.sector,
            risk_tolerance=request.risk_tolerance,
            momentum_breakout=request.momentum_breakout,
            value_screening=request.value_screening,
            divergence_detection=request.divergence_detection,
            multi_timeframe_filter=request.multi_timeframe_filter,
            portfolio_diversification=request.portfolio_diversification,
            macro_factor=request.macro_factor,
            time_decay_weighting=request.time_decay_weighting,
            smart_money_flow=request.smart_money_flow,
            earnings_safety_days=request.earnings_safety_days
        )
        
        return JSONResponse(content=resp)
    except Exception as e:
        logger.exception("Neural Engine API error")
        return JSONResponse(status_code=500, content={"error": "neural_engine_error", "detail": str(e)})