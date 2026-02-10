"""
🔬 Scribe - The Renaissance Technical Analyst

Named after the medieval scribes who meticulously documented and analyzed texts,
this Codex Hunter transforms raw market data into actionable technical indicators.

Historical Context:
Renaissance scribes were the quantitative analysts of their time, applying
mathematical precision to illuminate patterns hidden in ancient manuscripts.
Just as they decoded classical texts, Scribe decodes price action.

Responsibilities:
- Calculate trend indicators (SMA20, SMA50, SMA200)
- Compute momentum signals (RSI, ROC, MACD)
- Measure volatility metrics (ATR, Standard Deviation)
- Store results in PostgreSQL via existing logger infrastructure

Integration Strategy:
Uses existing loggers (trend_logger, momentum_logger, volatility_logger) to
maintain consistency with legacy backfill scripts while avoiding modifications
to PostgresAgent.
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime

# Import dual-memory loggers (PostgreSQL + Qdrant)
# These extend the legacy loggers with vector storage
from vitruvyan_core.domains.trade.logger.trend_logger_qdrant import log_trend_result
from vitruvyan_core.domains.trade.logger.momentum_logger_qdrant import log_momentum_result
from vitruvyan_core.domains.trade.logger.volatility_logger_qdrant import log_volatility_result

logger = logging.getLogger(__name__)


class Scribe:
    """
    Technical indicator calculation engine for Codex Hunters.
    
    Converts normalized OHLCV data into trend, momentum, and volatility signals
    using pandas-ta library. Stores results via existing logger infrastructure.
    """
    
    def __init__(self, user_id: str = "scribe"):
        """
        Initialize Scribe hunter.
        
        Args:
            user_id: Identifier for logging attribution (default: "scribe")
        """
        self.user_id = user_id
        self.name = "Scribe"
        logger.info(f"🔬 {self.name} initialized (user_id={user_id})")
    
    def execute(
        self,
        normalized_data: List[Dict[str, Any]],
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Calculate technical indicators for normalized market data.
        
        Args:
            normalized_data: List of entity_id dictionaries from Restorer
                Expected structure:
                {
                    "entity_id": "EXAMPLE_ENTITY_1",
                    "history": [
                        {"date": "2024-01-01", "open": 100, "high": 105, 
                         "low": 99, "close": 103, "volume": 1000000},
                        ...
                    ],
                    "source": "yfinance"
                }
            batch_size: Number of entity_ids to process before checkpointing
        
        Returns:
            {
                "processed": int,
                "successful": int,
                "failed": int,
                "errors": List[Dict],
                "duration_seconds": float
            }
        """
        start_time = datetime.now()
        results = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "errors": [],
            "entities_processed": []
        }
        
        logger.info(f"🔬 Scribe starting expedition on {len(normalized_data)} entity_ids")
        
        for idx, entity_data in enumerate(normalized_data):
            entity_id = entity_data.get("entity_id", "UNKNOWN")
            
            try:
                # Validate required data
                if "history" not in entity_data or not entity_data["history"]:
                    raise ValueError(f"No history data for {entity_id}")
                
                # Calculate all indicators
                indicators = self._calculate_indicators(entity_data)
                
                if indicators:
                    # Store using existing loggers
                    self._store_trend(entity_id, indicators["trend"])
                    self._store_momentum(entity_id, indicators["momentum"])
                    self._store_volatility(entity_id, indicators["volatility"])
                    
                    results["successful"] += 1
                    results["entities_processed"].append(entity_id)
                    logger.info(f"✅ {entity_id} indicators calculated and stored")
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "entity_id": entity_id,
                        "error": "Insufficient data for indicator calculation"
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "entity_id": entity_id,
                    "error": str(e)
                })
                logger.error(f"❌ Error processing {entity_id}: {e}", exc_info=True)
            
            results["processed"] += 1
            
            # Checkpoint progress
            if (idx + 1) % batch_size == 0:
                logger.info(f"📊 Checkpoint: {idx + 1}/{len(normalized_data)} entity_ids processed")
        
        duration = (datetime.now() - start_time).total_seconds()
        results["duration_seconds"] = duration
        
        logger.info(
            f"🔬 Scribe expedition complete: "
            f"{results['successful']}/{results['processed']} successful "
            f"in {duration:.2f}s"
        )
        
        return results
    
    def _calculate_indicators(
        self,
        entity_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate all technical indicators using pandas-ta.
        
        Args:
            entity_data: Normalized entity_id data from Restorer
        
        Returns:
            Dictionary with trend, momentum, volatility sections or None
        """
        entity_id = entity_data.get("entity_id", "UNKNOWN")
        history = entity_data.get("history", [])
        
        # Convert to DataFrame
        df = pd.DataFrame(history)
        
        # Ensure required columns
        required_cols = ["date", "open", "high", "low", "close", "volume"]
        if not all(col in df.columns for col in required_cols):
            logger.warning(f"Missing required columns for {entity_id}")
            return None
        
        # Convert date to datetime
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        
        # Need at least 200 days for SMA200
        if len(df) < 200:
            logger.warning(f"{entity_id} has only {len(df)} days (need 200 for SMA200)")
            return None
        
        # Calculate all indicators using pandas-ta
        try:
            # Trend: SMA20, SMA50, SMA200
            df.ta.sma(length=20, append=True)
            df.ta.sma(length=50, append=True)
            df.ta.sma(length=200, append=True)
            
            # Momentum: RSI, ROC, MACD
            df.ta.rsi(length=14, append=True)
            df.ta.roc(length=12, append=True)
            df.ta.macd(fast=12, slow=26, signal=9, append=True)
            
            # Volatility: ATR, Standard Deviation
            df.ta.atr(length=14, append=True)
            df.ta.stdev(length=20, append=True)
            
        except Exception as e:
            logger.error(f"pandas-ta calculation error for {entity_id}: {e}")
            return None
        
        # Get latest values (most recent row)
        latest = df.iloc[-1]
        
        # Extract calculated values with safe handling
        sma_20 = latest.get('SMA_20', np.nan)
        sma_50 = latest.get('SMA_50', np.nan)
        sma_200 = latest.get('SMA_200', np.nan)
        rsi_14 = latest.get('RSI_14', np.nan)
        roc_12 = latest.get('ROC_12', np.nan)
        macd = latest.get('MACD_12_26_9', np.nan)
        macd_signal = latest.get('MACDs_12_26_9', np.nan)
        macd_hist = latest.get('MACDh_12_26_9', np.nan)
        atr_14 = latest.get('ATRr_14', np.nan)
        stdev_20 = latest.get('STDEV_20', np.nan)
        close = latest.get('close', 0)
        
        # Validate we have data
        if pd.isna([sma_20, sma_50, sma_200]).any():
            logger.warning(f"{entity_id}: SMA values contain NaN")
            return None
        
        # Build result structure
        return {
            "trend": {
                "entity_id": entity_id,
                "trend": {
                    "short": self._determine_trend(close, sma_20),
                    "medium": self._determine_trend(close, sma_50),
                    "long": self._determine_trend(close, sma_200)
                },
                "indicators": {
                    "SMA20": float(sma_20),
                    "SMA50": float(sma_50),
                    "SMA200": float(sma_200),
                    "price": float(close)
                }
            },
            "momentum": {
                "entity_id": entity_id,
                "horizon": "medium",
                "rsi": float(rsi_14) if not pd.isna(rsi_14) else None,
                "roc": float(roc_12) if not pd.isna(roc_12) else 0.0,
                "macd": float(macd) if not pd.isna(macd) else 0.0,
                "macd_signal": float(macd_signal) if not pd.isna(macd_signal) else 0.0,
                "macd_histogram": float(macd_hist) if not pd.isna(macd_hist) else 0.0,
                "roc_trend": "positive" if (not pd.isna(roc_12) and roc_12 > 0) else "negative",
                "macd_trend": "bullish" if (not pd.isna(macd) and not pd.isna(macd_signal) and macd > macd_signal) else "bearish"
            },
            "volatility": {
                "entity_id": entity_id,
                "horizon": "medium",
                "atr": float(atr_14) if not pd.isna(atr_14) else 0.0,
                "stdev": float(stdev_20) if not pd.isna(stdev_20) else 0.0,
                "signal": self._determine_volatility_signal(atr_14),
                "summary": f"ATR: {atr_14:.2f}%, StdDev: {stdev_20:.2f}" if not pd.isna([atr_14, stdev_20]).any() else "Insufficient data"
            }
        }
    
    def _determine_trend(self, price: float, sma: float) -> str:
        """
        Determine trend direction based on price vs SMA.
        
        Args:
            price: Current close price
            sma: Simple Moving Average value
        
        Returns:
            "uptrend", "downtrend", or "sideways"
        """
        if pd.isna(price) or pd.isna(sma):
            return "sideways"
        
        diff_pct = ((price - sma) / sma) * 100
        
        if diff_pct > 2.0:
            return "uptrend"
        elif diff_pct < -2.0:
            return "downtrend"
        else:
            return "sideways"
    
    def _determine_volatility_signal(self, atr: float) -> str:
        """
        Categorize volatility level.
        
        Args:
            atr: Average True Range (percentage)
        
        Returns:
            "low", "medium", or "high"
        """
        if pd.isna(atr):
            return "unknown"
        
        if atr < 3.0:
            return "low"
        elif atr < 8.0:
            return "medium"
        else:
            return "high"
    
    def _store_trend(self, entity_id: str, trend_data: Dict[str, Any]) -> None:
        """
        Store trend indicators using existing trend_logger.
        
        Args:
            entity_id: Entity entity_id symbol
            trend_data: Trend section from _calculate_indicators
        """
        try:
            log_trend_result(self.user_id, entity_id, trend_data)
            logger.debug(f"📈 Trend data logged for {entity_id}")
        except Exception as e:
            logger.error(f"Failed to log trend for {entity_id}: {e}")
            raise
    
    def _store_momentum(self, entity_id: str, momentum_data: Dict[str, Any]) -> None:
        """
        Store momentum indicators using existing momentum_logger.
        
        Args:
            entity_id: Entity entity_id symbol
            momentum_data: Momentum section from _calculate_indicators
        """
        try:
            log_momentum_result(self.user_id, momentum_data)
            logger.debug(f"📊 Momentum data logged for {entity_id}")
        except Exception as e:
            logger.error(f"Failed to log momentum for {entity_id}: {e}")
            raise
    
    def _store_volatility(self, entity_id: str, volatility_data: Dict[str, Any]) -> None:
        """
        Store volatility indicators using existing volatility_logger.
        
        Args:
            entity_id: Entity entity_id symbol
            volatility_data: Volatility section from _calculate_indicators
        """
        try:
            log_volatility_result(self.user_id, entity_id, volatility_data)
            logger.debug(f"📉 Volatility data logged for {entity_id}")
        except Exception as e:
            logger.error(f"Failed to log volatility for {entity_id}: {e}")
            raise


if __name__ == "__main__":
    # Example usage (for testing)
    logging.basicConfig(level=logging.INFO)
    
    # Mock normalized data
    mock_data = [{
        "entity_id": "EXAMPLE_ENTITY_1",
        "history": [
            {"date": f"2024-{i//30+1:02d}-{i%30+1:02d}", "open": 150+i*0.1, 
             "high": 152+i*0.1, "low": 149+i*0.1, "close": 151+i*0.1, "volume": 1000000}
            for i in range(250)  # 250 days of data
        ],
        "source": "yfinance"
    }]
    
    scribe = Scribe()
    result = scribe.execute(mock_data)
    print(f"\n🔬 Scribe Test Result:\n{result}")
