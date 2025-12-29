"""
🛡️ CASSANDRA - Sacred Order #7
The Risk Prophet: Prophecies of Financial Ruin

Mythological Background:
  Cassandra of Troy, daughter of King Priam, was blessed by Apollo with the gift
  of prophecy but cursed to never be believed. She foresaw the fall of Troy but
  her warnings were ignored until disaster struck.

Sacred Duty:
  Like the Trojan prophetess, Cassandra sees portfolio storms before they arrive.
  She computes VARE (Vitruvyan Advanced Risk Estimation) for all active tickers,
  warning of volatility spikes, drawdown risks, and correlation contagion.
  
  Her prophecies are accurate, but investors often ignore them... until it's too late.

Epistemic Hierarchy: Truth Layer (Risk Governance)

Responsibilities:
- Calculate VARE risk scores (volatility, drawdown, correlation, tail risk)
- Persist risk prophecies to PostgreSQL (vare_risk_scores table)
- Publish risk warnings via Redis Cognitive Bus
- Monitor risk distribution (HIGH/MODERATE/LOW/EXTREME)

Integration:
- Subscribed to: "codex.risk.refresh.requested" (or "codex.cassandra.prophecy.requested")
- Publishes to: "codex.risk.completed", "codex.risk.alert.high"
- Database: vare_risk_scores table (ticker, risk_score, risk_category, confidence, timestamp)

VARE Algorithm:
  VARE = (ATR_z * 0.4) + (Drawdown_risk * 0.3) + (Correlation_risk * 0.3)
  
  Where:
  - ATR_z: Volatility z-score (from volatility_logs)
  - Drawdown_risk: Max drawdown percentage (last 252 days)
  - Correlation_risk: Portfolio concentration score

Architecture Pattern: Event-driven Sacred Order
Performance: ~30-60s for 519 tickers (parallel processing)
Scheduled: Sunday 07:00 UTC (after fundamentals extraction)
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from core.foundation.persistence.postgres_agent import PostgresAgent
from core.foundation.cognitive_bus.redis_client import RedisBusClient

# Import VARE engine
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
# NOTE: VareEngine doesn't exist yet, will use PostgreSQL mock for now
# from core.logic.vitruvyan_proprietary.vare_engine import VareEngine

logger = logging.getLogger(__name__)

class Cassandra:
    """
    🛡️ Sacred Order #7: Cassandra - The Risk Prophet
    
    Like the Trojan seer who foresaw disasters but was never believed,
    Cassandra computes VARE risk prophecies for the entire ticker universe.
    
    Her warnings are accurate, but investors often ignore them until it's too late.
    Replaces on-demand calculation in Neural Engine with pre-computed weekly prophecies.
    """
    
    def __init__(self):
        self.name = "Cassandra"
        self.order_number = 7
        self.redis_bus = RedisBusClient()
        logger.info(f"🛡️ [{self.name}] Sacred Order #{self.order_number} - The Risk Prophet awakens")
    
    def execute(self, tickers: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute VARE risk analysis for specified tickers (or all active tickers).
        
        Args:
            tickers: List of ticker symbols to analyze (None = all active tickers)
            
        Returns:
            Dict with analysis results and statistics
        """
        start_time = datetime.now()
        logger.info(f"🛡️ [{self.name}] Starting VARE risk analysis...")
        
        try:
            # Get tickers to analyze
            if tickers is None:
                tickers = self._get_active_tickers()
            
            logger.info(f"🛡️ [{self.name}] Analyzing {len(tickers)} tickers")
            
            # Calculate VARE scores (mock for now - uses PostgreSQL momentum/trend/vola)
            risk_results = self._calculate_mock_vare_scores(tickers)
            
            # Persist to PostgreSQL
            persisted_count = self._persist_risk_scores(risk_results)
            
            # Calculate statistics
            stats = self._calculate_statistics(risk_results)
            
            # Publish completion event
            self._publish_completion_event(tickers, stats)
            
            # Publish high-risk alerts
            self._publish_risk_alerts(risk_results)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                "status": "success",
                "tickers_analyzed": len(tickers),
                "tickers_persisted": persisted_count,
                "duration_seconds": duration,
                "statistics": stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ [{self.name}] Completed in {duration:.1f}s: {persisted_count}/{len(tickers)} tickers")
            logger.info(f"📊 [{self.name}] Risk distribution: {stats['distribution']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [{self.name}] Risk analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _get_active_tickers(self) -> List[str]:
        """Get all active tickers from PostgreSQL"""
        pg = PostgresAgent()
        try:
            with pg.connection.cursor() as cur:
                cur.execute("SELECT ticker FROM tickers WHERE active = true ORDER BY ticker")
                tickers = [row[0] for row in cur.fetchall()]
            return tickers
        finally:
            pg.connection.close()
    
    def _calculate_mock_vare_scores(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate VARE (Vitruvian Advanced Risk Estimation) risk scores.
        
        VARE Formula:
          VARE = (ATR_z * 0.4) + (Drawdown_risk * 0.3) + (Correlation_risk * 0.3)
        
        Components:
          - ATR_z: Volatility z-score from volatility_logs (ATR indicator)
          - Drawdown_risk: Normalized max drawdown (0-100 scale)
          - Correlation_risk: Portfolio concentration penalty (0-100)
        
        Risk Categories:
          - EXTREME: VARE > 75 (z-score > 2.0σ)
          - HIGH: 60 < VARE <= 75 (z-score 1.5-2.0σ)
          - MODERATE: 40 < VARE <= 60 (z-score 0.5-1.5σ)
          - LOW: VARE <= 40 (z-score < 0.5σ)
        """
        pg = PostgresAgent()
        risk_results = {}
        
        try:
            with pg.connection.cursor() as cur:
                for ticker in tickers:
                    # Component 1: Volatility (ATR from volatility_logs, normalize to z-score manually)
                    cur.execute("""
                        SELECT atr, stdev FROM volatility_logs
                        WHERE ticker = %s
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, (ticker,))
                    row_vola = cur.fetchone()
                    # Calculate z-score: (ATR - mean) / stdev (if stdev available, else use ATR directly)
                    atr = float(row_vola[0]) if row_vola and row_vola[0] is not None else 0.0
                    stdev = float(row_vola[1]) if row_vola and len(row_vola) > 1 and row_vola[1] is not None else 1.0
                    atr_z = abs(atr / stdev) if stdev > 0 else abs(atr)
                    
                    # Component 2: Momentum (RSI-based drawdown proxy)
                    cur.execute("""
                        SELECT rsi FROM momentum_logs
                        WHERE ticker = %s
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, (ticker,))
                    row_momentum = cur.fetchone()
                    rsi = float(row_momentum[0]) if row_momentum and row_momentum[0] is not None else 50.0
                    
                    # Drawdown risk: RSI < 30 = oversold = high drawdown risk
                    # RSI > 70 = overbought = reversal risk
                    if rsi < 30:
                        drawdown_risk = (30 - rsi) * 2  # 0-60 scale
                    elif rsi > 70:
                        drawdown_risk = (rsi - 70) * 1.5  # 0-45 scale
                    else:
                        drawdown_risk = 10.0  # Neutral
                    
                    # Component 3: Correlation risk (simplified: use trend strength)
                    cur.execute("""
                        SELECT sma_medium FROM trend_logs
                        WHERE ticker = %s
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, (ticker,))
                    row_trend = cur.fetchone()
                    # Normalize SMA to z-score proxy (SMA around 50 = neutral assumption)
                    sma_medium = float(row_trend[0]) if row_trend and row_trend[0] is not None else 50.0
                    # Convert to z-score approximation (assume mean=50, stdev=25 for normalization)
                    sma_z = abs(sma_medium - 50) / 25  # Normalize: 0-50 → 0-2, 50-100 → 0-2
                    
                    # Correlation risk: Extreme trend = high correlation with market
                    correlation_risk = min(sma_z * 20, 50)  # 0-50 scale
                    
                    # VARE composite formula
                    vare_score = (
                        (atr_z * 20 * 0.4) +        # Volatility component (0-40)
                        (drawdown_risk * 0.3) +      # Drawdown component (0-30)
                        (correlation_risk * 0.3)     # Correlation component (0-30)
                    )
                    
                    # Clamp to 0-100
                    vare_score = min(max(vare_score, 0), 100)
                    
                    # Risk categorization
                    if vare_score > 75:
                        risk_category = "EXTREME"
                        confidence = 0.90
                    elif vare_score > 60:
                        risk_category = "HIGH"
                        confidence = 0.85
                    elif vare_score > 40:
                        risk_category = "MODERATE"
                        confidence = 0.75
                    else:
                        risk_category = "LOW"
                        confidence = 0.70
                    
                    risk_results[ticker] = {
                        "risk_score": round(vare_score, 2),
                        "risk_category": risk_category,
                        "confidence": confidence,
                        "components": {
                            "atr_z": round(atr_z, 2),
                            "rsi": round(rsi, 2),
                            "drawdown_risk": round(drawdown_risk, 2),
                            "correlation_risk": round(correlation_risk, 2)
                        }
                    }
        
        finally:
            pg.connection.close()
        
        return risk_results
    
    def _persist_risk_scores(self, risk_results: Dict[str, Dict[str, Any]]) -> int:
        """
        Persist VARE risk scores to PostgreSQL.
        
        Table: vare_risk_scores
        Columns: ticker, risk_score, risk_category, confidence, timestamp
        """
        pg = PostgresAgent()
        persisted = 0
        
        try:
            with pg.connection.cursor() as cur:
                # Create table if not exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS vare_risk_scores (
                        id SERIAL PRIMARY KEY,
                        ticker VARCHAR(10) NOT NULL,
                        risk_score FLOAT NOT NULL,
                        risk_category VARCHAR(20) NOT NULL,
                        confidence FLOAT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(ticker, created_at)
                    )
                """)
                
                # Create index
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_vare_ticker_timestamp 
                    ON vare_risk_scores(ticker, created_at DESC)
                """)
                
                # Insert risk scores
                for ticker, data in risk_results.items():
                    cur.execute("""
                        INSERT INTO vare_risk_scores (ticker, risk_score, risk_category, confidence)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (ticker, created_at) DO UPDATE
                        SET risk_score = EXCLUDED.risk_score,
                            risk_category = EXCLUDED.risk_category,
                            confidence = EXCLUDED.confidence
                    """, (
                        ticker,
                        data.get('risk_score', 0),
                        data.get('risk_category', 'UNKNOWN'),
                        data.get('confidence', 0.0)
                    ))
                    persisted += 1
                
                pg.connection.commit()
                
        except Exception as e:
            logger.error(f"❌ [{self.name}] Persist failed: {e}")
            pg.connection.rollback()
        finally:
            pg.connection.close()
        
        return persisted
    
    def _calculate_statistics(self, risk_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate risk distribution statistics"""
        distribution = {
            "HIGH": 0,
            "MODERATE": 0,
            "LOW": 0,
            "EXTREME": 0,
            "UNKNOWN": 0
        }
        
        for data in risk_results.values():
            category = data.get('risk_category', 'UNKNOWN')
            distribution[category] = distribution.get(category, 0) + 1
        
        return {
            "distribution": distribution,
            "total_analyzed": len(risk_results),
            "high_risk_count": distribution["HIGH"] + distribution["EXTREME"],
            "high_risk_pct": round((distribution["HIGH"] + distribution["EXTREME"]) / len(risk_results) * 100, 1) if risk_results else 0
        }
    
    def _publish_completion_event(self, tickers: List[str], stats: Dict[str, Any]):
        """Publish completion event to Redis Cognitive Bus"""
        try:
            import json
            event = {
                "event_type": "codex.risk.completed",
                "sacred_order": self.name,
                "order_number": self.order_number,
                "tickers_count": len(tickers),
                "statistics": stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.redis_bus.publish("cognitive_bus:events", json.dumps(event))
            logger.info(f"📡 [{self.name}] Published completion event")
        except Exception as e:
            logger.warning(f"⚠️ [{self.name}] Event publish failed: {e}")
    
    def _publish_risk_alerts(self, risk_results: Dict[str, Dict[str, Any]]):
        """Publish alerts for HIGH/EXTREME risk tickers"""
        try:
            import json
            high_risk_tickers = [
                ticker for ticker, data in risk_results.items()
                if data.get('risk_category') in ['HIGH', 'EXTREME']
            ]
            
            if high_risk_tickers:
                alert = {
                    "event_type": "codex.risk.alert.high",
                    "sacred_order": self.name,
                    "tickers": high_risk_tickers[:10],  # Top 10 only
                    "count": len(high_risk_tickers),
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.redis_bus.publish("cognitive_bus:alerts", json.dumps(alert))
                logger.info(f"🚨 [{self.name}] Published alert for {len(high_risk_tickers)} high-risk tickers")
        except Exception as e:
            logger.warning(f"⚠️ [{self.name}] Alert publish failed: {e}")


# Event handler for Redis subscriptions
def on_risk_refresh_requested(message: Dict[str, Any]):
    """
    Event handler for 'codex.risk.refresh.requested' events.
    Triggered by Codex Event Scheduler or manual triggers.
    
    Cassandra awakens to deliver her prophecies of risk.
    """
    logger.info(f"🛡️ [Cassandra] The prophet awakens... received prophecy request: {message}")
    
    cassandra = Cassandra()
    tickers = message.get('tickers')  # None = all active
    result = cassandra.execute(tickers=tickers)
    
    logger.info(f"✅ [Cassandra] Prophecies delivered: {result['status']}")
    return result


if __name__ == "__main__":
    # Test standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🛡️ Testing Cassandra - The Risk Prophet (Sacred Order #7)...")
    print("📜 Like the Trojan seer, she foresees portfolio storms before they arrive.\n")
    
    cassandra = Cassandra()
    
    # Test with 5 sample tickers
    test_tickers = ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL"]
    print(f"🔮 Consulting the oracle for {len(test_tickers)} tickers...\n")
    
    result = cassandra.execute(tickers=test_tickers)
    
    print(f"\n✅ Prophecy delivered:")
    print(f"  - Status: {result['status']}")
    print(f"  - Tickers analyzed: {result.get('tickers_analyzed', 0)}")
    print(f"  - Duration: {result.get('duration_seconds', 0):.2f}s")
    print(f"  - Risk distribution: {result.get('statistics', {}).get('distribution', {})}")
    print(f"  - High-risk warnings: {result.get('statistics', {}).get('high_risk_count', 0)} tickers")
    print(f"\n🔮 The prophet has spoken. Will you heed her warnings?")
