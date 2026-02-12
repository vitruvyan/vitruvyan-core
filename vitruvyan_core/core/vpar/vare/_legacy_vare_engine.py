# core/algorithms/vare_engine.py
"""
⚠️ VARE - Vitruvyan Adaptive Risk Engine

Calcola profili di rischio multi-dimensionali per ticker e portfolio.
Non suggerisce decisioni ma fornisce metriche di rischio explainable.

Principi:
- Explainability: ogni punteggio di rischio è tracciabile
- Safety: mai raccomandazioni dirette, solo analisi del rischio
- Composability: funziona standalone o come nodo LangGraph
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import yfinance as yf
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# Memory adapter for PostgreSQL/Qdrant integration
try:
    from .algorithm_memory_adapter import store_vare_result
except ImportError:
    def store_vare_result(result) -> bool:
        return False


@dataclass 
class VAREResult:
    """Risultato dell'analisi VARE per un ticker"""
    ticker: str
    timestamp: datetime
    
    # Risk scores (0-100, higher = more risky)
    market_risk: float
    volatility_risk: float
    liquidity_risk: float
    correlation_risk: float
    
    # Composite risk score
    overall_risk: float
    risk_category: str  # "LOW", "MODERATE", "HIGH", "EXTREME"
    
    # Risk factors breakdown
    risk_factors: Dict[str, Any]
    
    # Explainability
    explanation: Dict[str, str]
    
    # Confidence in assessment
    confidence: float


class VAREEngine:
    """
    Vitruvyan Adaptive Risk Engine
    
    Analizza rischio multi-dimensionale:
    - Market Risk: correlazione con mercato generale
    - Volatility Risk: volatilità storica e rolling
    - Liquidity Risk: volume trading e bid-ask spread
    - Correlation Risk: correlazione con altri asset risk-on/risk-off
    """
    
    def __init__(self):
        self.market_proxy = "SPY"  # S&P 500 as market proxy
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        self.lookback_days = 252  # 1 year for risk calculations
        
        # Risk thresholds (adjustable via EPOCH V adaptation)
        self.risk_thresholds = {
            'LOW': 25,
            'MODERATE': 50, 
            'HIGH': 75,
            'EXTREME': 100
        }
        
        # Adaptation tracking
        self.adaptation_history = []
    
    def analyze_ticker(self, ticker: str, 
                      benchmark_ticker: Optional[str] = None) -> VAREResult:
        """
        Analizza il profilo di rischio di un ticker
        
        Args:
            ticker: Symbol del ticker
            benchmark_ticker: Benchmark personalizzato (default: SPY)
            
        Returns:
            VAREResult con metriche di rischio
        """
        try:
            benchmark = benchmark_ticker or self.market_proxy
            
            # Fetch data for ticker and benchmark
            ticker_data, benchmark_data = self._fetch_comparative_data(ticker, benchmark)
            
            if ticker_data.empty:
                return self._create_error_result(ticker, "No ticker data available")
            
            # Calculate individual risk components
            market_risk = self._calculate_market_risk(ticker_data, benchmark_data)
            volatility_risk = self._calculate_volatility_risk(ticker_data)
            liquidity_risk = self._calculate_liquidity_risk(ticker_data)
            correlation_risk = self._calculate_correlation_risk(ticker_data, benchmark_data)
            
            # Calculate overall risk score
            overall_risk = self._calculate_overall_risk(
                market_risk, volatility_risk, liquidity_risk, correlation_risk
            )
            
            # Determine risk category
            risk_category = self._determine_risk_category(overall_risk)
            
            # Generate risk factors breakdown
            risk_factors = self._generate_risk_factors(
                ticker_data, benchmark_data, market_risk, 
                volatility_risk, liquidity_risk, correlation_risk
            )
            
            # Generate explanations
            explanation = self._generate_explanation(
                ticker, market_risk, volatility_risk, 
                liquidity_risk, correlation_risk, overall_risk, risk_category
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(ticker_data, benchmark_data)
            
            result = VAREResult(
                ticker=ticker,
                timestamp=datetime.now(),
                market_risk=market_risk,
                volatility_risk=volatility_risk,
                liquidity_risk=liquidity_risk,
                correlation_risk=correlation_risk,
                overall_risk=overall_risk,
                risk_category=risk_category,
                risk_factors=risk_factors,
                explanation=explanation,
                confidence=confidence
            )
            
            # Store result in PostgreSQL/Qdrant
            try:
                store_vare_result(result)
            except Exception as e:
                # Don't fail analysis if storage fails
                pass
            
            return result
            
        except Exception as e:
            return self._create_error_result(ticker, str(e))
    
    # =====================================================================
    # EPOCH V - ADAPTIVE METHODS
    # =====================================================================
    
    def adjust(self, parameter: str, delta: float) -> bool:
        """
        🔧 EPOCH V: Adjust VARE parameters dynamically
        
        Called by Orthodoxy Adaptation Listener when metrics degrade.
        Modifies risk thresholds to adapt system behavior.
        
        Args:
            parameter: Parameter to adjust ('volatility_threshold', 'market_threshold', 'liquidity_threshold')
            delta: Adjustment value (positive = increase sensitivity, negative = decrease)
        
        Returns:
            bool: True if adjustment successful
            
        Example:
            # If event loss rate too high, reduce volatility sensitivity
            engine.adjust('volatility_threshold', -0.1)  # Make volatility less impactful
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            original_thresholds = self.risk_thresholds.copy()
            
            if parameter == 'volatility_threshold':
                # Adjust all thresholds proportionally
                for key in ['LOW', 'MODERATE', 'HIGH', 'EXTREME']:
                    self.risk_thresholds[key] += delta * 10
                    # Clamp to reasonable bounds
                    self.risk_thresholds[key] = max(10, min(100, self.risk_thresholds[key]))
            
            elif parameter == 'market_threshold':
                # Adjust only MODERATE and HIGH (market risk focus)
                self.risk_thresholds['MODERATE'] += delta * 15
                self.risk_thresholds['HIGH'] += delta * 15
                self.risk_thresholds['MODERATE'] = max(20, min(80, self.risk_thresholds['MODERATE']))
                self.risk_thresholds['HIGH'] = max(40, min(90, self.risk_thresholds['HIGH']))
            
            elif parameter == 'liquidity_threshold':
                # Adjust only EXTREME (liquidity crisis focus)
                self.risk_thresholds['EXTREME'] += delta * 5
                self.risk_thresholds['EXTREME'] = max(70, min(100, self.risk_thresholds['EXTREME']))
            
            else:
                logger.warning(f"VARE: Unknown parameter '{parameter}', no adjustment made")
                return False
            
            # Log adaptation
            adaptation_event = {
                'timestamp': datetime.utcnow().isoformat(),
                'parameter': parameter,
                'delta': delta,
                'thresholds_before': original_thresholds,
                'thresholds_after': self.risk_thresholds.copy()
            }
            self.adaptation_history.append(adaptation_event)
            
            logger.info(f"✅ VARE adjusted: {parameter} by {delta:+.2f}")
            logger.info(f"   Thresholds: {self.risk_thresholds}")
            
            # Publish event to Vault Keepers via Redis
            self._log_adaptation_to_vault(parameter, delta, adaptation_event)
            
            # Store in PostgreSQL for Grafana dashboard
            self._store_adaptation_in_db(parameter, delta, original_thresholds)
            
            return True
        
        except Exception as e:
            logger.error(f"❌ VARE adjustment failed for {parameter}: {e}")
            return False
    
    def _log_adaptation_to_vault(self, parameter: str, delta: float, event: Dict):
        """Log adaptation event to Vault Keepers via Redis"""
        try:
            from core.cognitive_bus.transport.redis_client import get_redis_bus, CognitiveEvent
            
            redis_bus = get_redis_bus()
            if redis_bus.is_connected():
                cognitive_event = CognitiveEvent(
                    event_type="vare.parameter.adjusted",
                    emitter="vare_engine",
                    target="vault_keepers",
                    payload={
                        'parameter': parameter,
                        'delta': delta,
                        'thresholds_after': self.risk_thresholds,
                        'timestamp': event['timestamp']
                    },
                    timestamp=event['timestamp']
                )
                redis_bus.publish_event(cognitive_event)
        except Exception as e:
            # Don't fail adjustment if logging fails
            import logging
            logging.getLogger(__name__).warning(f"Failed to log adaptation to Vault: {e}")
    
    def _store_adaptation_in_db(self, parameter: str, delta: float, original_thresholds: Dict):
        """Store adaptation in PostgreSQL for Grafana dashboard tracking"""
        try:
            import psycopg2
            import os
            
            # Calculate old/new values based on parameter type
            if parameter == 'volatility_threshold':
                old_value = original_thresholds.get('MODERATE', 50)
                new_value = self.risk_thresholds.get('MODERATE', 50)
            elif parameter == 'market_threshold':
                old_value = original_thresholds.get('HIGH', 75)
                new_value = self.risk_thresholds.get('HIGH', 75)
            elif parameter == 'liquidity_threshold':
                old_value = original_thresholds.get('EXTREME', 100)
                new_value = self.risk_thresholds.get('EXTREME', 100)
            else:
                old_value = 0
                new_value = 0
            
            # Generate reason description
            reason = f"Autonomous adaptation triggered by EPOCH V metrics monitoring (delta: {delta:+.2f})"
            
            # Connect and insert
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                database=os.getenv("POSTGRES_DB", "vitruvyan"),
                user=os.getenv("POSTGRES_USER", "vitruvyan_user"),
                password=os.getenv("POSTGRES_PASSWORD")
            )
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO vare_adaptations (parameter, old_value, new_value, delta, reason)
                VALUES (%s, %s, %s, %s, %s)
            """, (parameter, old_value, new_value, delta, reason))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            import logging
            logging.getLogger(__name__).info(f"📊 VARE adaptation stored in PostgreSQL (ID logged)")
            
        except Exception as e:
            # Don't fail adjustment if DB logging fails
            import logging
            logging.getLogger(__name__).warning(f"Failed to store adaptation in PostgreSQL: {e}")
    
    def get_adaptation_history(self) -> List[Dict]:
        """Get history of all VARE adaptations"""
        return self.adaptation_history
    
    def reset_thresholds(self):
        """Reset thresholds to default values"""
        self.risk_thresholds = {
            'LOW': 25,
            'MODERATE': 50, 
            'HIGH': 75,
            'EXTREME': 100
        }
        self.adaptation_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'reset_thresholds',
            'thresholds_after': self.risk_thresholds.copy()
        })


# LangGraph Node Integration
    
    def _fetch_comparative_data(self, ticker: str, benchmark: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Scarica dati per ticker e benchmark"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days + 50)  # Extra buffer
            
            # Fetch ticker data
            ticker_stock = yf.Ticker(ticker)
            ticker_data = ticker_stock.history(start=start_date, end=end_date)
            
            # Fetch benchmark data
            benchmark_stock = yf.Ticker(benchmark)
            benchmark_data = benchmark_stock.history(start=start_date, end=end_date)
            
            return ticker_data, benchmark_data
            
        except Exception:
            return pd.DataFrame(), pd.DataFrame()
    
    def _calculate_market_risk(self, ticker_data: pd.DataFrame, benchmark_data: pd.DataFrame) -> float:
        """Calcola rischio di mercato tramite beta e correlazione"""
        if ticker_data.empty or benchmark_data.empty:
            return 50  # Neutral risk if no data
        
        try:
            # Calculate returns
            ticker_returns = ticker_data['Close'].pct_change().dropna()
            benchmark_returns = benchmark_data['Close'].pct_change().dropna()
            
            # Align data
            common_dates = ticker_returns.index.intersection(benchmark_returns.index)
            if len(common_dates) < 30:
                return 50
            
            ticker_aligned = ticker_returns.loc[common_dates]
            benchmark_aligned = benchmark_returns.loc[common_dates]
            
            # Calculate beta
            covariance = np.cov(ticker_aligned, benchmark_aligned)[0, 1]
            benchmark_variance = np.var(benchmark_aligned)
            
            if benchmark_variance == 0:
                beta = 1.0
            else:
                beta = covariance / benchmark_variance
            
            # Convert beta to risk score (0-100)
            # Beta = 1: neutral (50), Beta > 1: higher risk, Beta < 1: lower risk
            if beta <= 0:
                market_risk = 20  # Defensive
            elif beta <= 0.5:
                market_risk = 30
            elif beta <= 1.0:
                market_risk = 40 + (beta - 0.5) * 20  # 40-50
            elif beta <= 1.5:
                market_risk = 50 + (beta - 1.0) * 30  # 50-65
            elif beta <= 2.0:
                market_risk = 65 + (beta - 1.5) * 25  # 65-77.5
            else:
                market_risk = min(95, 77.5 + (beta - 2.0) * 10)
            
            return float(market_risk)
            
        except Exception:
            return 50
    
    def _calculate_volatility_risk(self, ticker_data: pd.DataFrame) -> float:
        """Calcola rischio di volatilità"""
        if ticker_data.empty:
            return 50
        
        try:
            returns = ticker_data['Close'].pct_change().dropna()
            
            if len(returns) < 30:
                return 50
            
            # Calculate annualized volatility
            daily_vol = returns.std()
            annual_vol = daily_vol * np.sqrt(252)
            
            # Convert to risk score (0-100)
            # Typical stock volatility ranges: 10-80%+
            if annual_vol <= 0.15:  # <= 15%
                vol_risk = 20
            elif annual_vol <= 0.25:  # <= 25%
                vol_risk = 35
            elif annual_vol <= 0.35:  # <= 35%
                vol_risk = 50
            elif annual_vol <= 0.50:  # <= 50%
                vol_risk = 70
            else:  # > 50%
                vol_risk = min(95, 80 + (annual_vol - 0.5) * 40)
            
            return float(vol_risk)
            
        except Exception:
            return 50
    
    def _calculate_liquidity_risk(self, ticker_data: pd.DataFrame) -> float:
        """Calcola rischio di liquidità basato su volume"""
        if ticker_data.empty:
            return 50
        
        try:
            volumes = ticker_data['Volume'].dropna()
            
            if len(volumes) < 30:
                return 60  # Higher risk if insufficient data
            
            # Calculate average daily volume
            avg_volume = volumes.mean()
            
            # Volume-based risk assessment
            if avg_volume >= 1_000_000:  # High liquidity
                liquidity_risk = 20
            elif avg_volume >= 500_000:  # Good liquidity
                liquidity_risk = 30
            elif avg_volume >= 100_000:  # Moderate liquidity
                liquidity_risk = 45
            elif avg_volume >= 50_000:   # Lower liquidity
                liquidity_risk = 60
            else:  # Low liquidity
                liquidity_risk = 80
            
            # Adjust for volume consistency
            volume_cv = volumes.std() / avg_volume if avg_volume > 0 else 1
            consistency_penalty = min(20, volume_cv * 25)
            
            final_risk = min(95, liquidity_risk + consistency_penalty)
            
            return float(final_risk)
            
        except Exception:
            return 60
    
    def _calculate_correlation_risk(self, ticker_data: pd.DataFrame, benchmark_data: pd.DataFrame) -> float:
        """Calcola rischio di correlazione con mercato"""
        if ticker_data.empty or benchmark_data.empty:
            return 50
        
        try:
            # Calculate returns
            ticker_returns = ticker_data['Close'].pct_change().dropna()
            benchmark_returns = benchmark_data['Close'].pct_change().dropna()
            
            # Align data
            common_dates = ticker_returns.index.intersection(benchmark_returns.index)
            if len(common_dates) < 30:
                return 50
            
            ticker_aligned = ticker_returns.loc[common_dates]
            benchmark_aligned = benchmark_returns.loc[common_dates]
            
            # Calculate correlation
            correlation = np.corrcoef(ticker_aligned, benchmark_aligned)[0, 1]
            
            if np.isnan(correlation):
                return 50
            
            # Convert correlation to risk score
            # High correlation = higher systematic risk during market stress
            abs_corr = abs(correlation)
            
            if abs_corr <= 0.3:  # Low correlation - diversification benefit
                corr_risk = 25
            elif abs_corr <= 0.5:  # Moderate correlation
                corr_risk = 40
            elif abs_corr <= 0.7:  # High correlation
                corr_risk = 60
            else:  # Very high correlation
                corr_risk = 80
            
            # Negative correlation gets slight risk reduction (hedging potential)
            if correlation < -0.5:
                corr_risk *= 0.8
            
            return float(corr_risk)
            
        except Exception:
            return 50
    
    def _calculate_overall_risk(self, market_risk: float, volatility_risk: float,
                              liquidity_risk: float, correlation_risk: float) -> float:
        """Calcola punteggio di rischio complessivo ponderato"""
        weights = {
            'market': 0.25,
            'volatility': 0.35,
            'liquidity': 0.25,
            'correlation': 0.15
        }
        
        overall = (
            market_risk * weights['market'] +
            volatility_risk * weights['volatility'] +
            liquidity_risk * weights['liquidity'] +
            correlation_risk * weights['correlation']
        )
        
        return float(overall)
    
    def _determine_risk_category(self, overall_risk: float) -> str:
        """Determina categoria di rischio"""
        if overall_risk <= self.risk_thresholds['LOW']:
            return "LOW"
        elif overall_risk <= self.risk_thresholds['MODERATE']:
            return "MODERATE"
        elif overall_risk <= self.risk_thresholds['HIGH']:
            return "HIGH"
        else:
            return "EXTREME"
    
    def _generate_risk_factors(self, ticker_data: pd.DataFrame, benchmark_data: pd.DataFrame,
                             market_risk: float, volatility_risk: float,
                             liquidity_risk: float, correlation_risk: float) -> Dict[str, Any]:
        """Genera dettagli sui fattori di rischio"""
        factors = {}
        
        try:
            # Market factors
            ticker_returns = ticker_data['Close'].pct_change().dropna()
            if not ticker_returns.empty:
                factors['annual_volatility'] = float(ticker_returns.std() * np.sqrt(252))
                factors['max_drawdown'] = float(self._calculate_max_drawdown(ticker_data['Close']))
            
            # Volume factors
            if 'Volume' in ticker_data.columns:
                factors['avg_daily_volume'] = int(ticker_data['Volume'].mean())
                factors['volume_consistency'] = float(
                    ticker_data['Volume'].std() / ticker_data['Volume'].mean()
                    if ticker_data['Volume'].mean() > 0 else 0
                )
            
            # Price factors
            if not ticker_data.empty:
                current_price = ticker_data['Close'].iloc[-1]
                price_52w_high = ticker_data['Close'].rolling(252).max().iloc[-1]
                price_52w_low = ticker_data['Close'].rolling(252).min().iloc[-1]
                
                factors['current_price'] = float(current_price)
                factors['distance_from_52w_high'] = float((price_52w_high - current_price) / price_52w_high)
                factors['distance_from_52w_low'] = float((current_price - price_52w_low) / price_52w_low)
            
        except Exception as e:
            factors['calculation_error'] = str(e)
        
        return factors
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calcola maximum drawdown"""
        try:
            peak = prices.expanding().max()
            drawdown = (prices - peak) / peak
            return abs(drawdown.min())
        except Exception:
            return 0.0
    
    def _generate_explanation(self, ticker: str, market_risk: float, volatility_risk: float,
                            liquidity_risk: float, correlation_risk: float,
                            overall_risk: float, risk_category: str) -> Dict[str, str]:
        """Genera spiegazioni human-readable"""
        
        # Risk level descriptions
        risk_desc = {
            "LOW": "basso rischio",
            "MODERATE": "rischio moderato", 
            "HIGH": "alto rischio",
            "EXTREME": "rischio estremo"
        }
        
        # Identify primary risk factors
        risks = {
            'volatilità': volatility_risk,
            'mercato': market_risk,
            'liquidità': liquidity_risk,
            'correlazione': correlation_risk
        }
        
        primary_risk = max(risks, key=risks.get)
        primary_value = risks[primary_risk]
        
        # Summary
        summary = (f"{ticker} presenta {risk_desc[risk_category]} "
                  f"(punteggio: {overall_risk:.0f}/100). "
                  f"Fattore principale: rischio di {primary_risk} ({primary_value:.0f}).")
        
        # Technical
        technical = (f"Breakdown rischi: Mercato {market_risk:.0f}, "
                    f"Volatilità {volatility_risk:.0f}, "
                    f"Liquidità {liquidity_risk:.0f}, "
                    f"Correlazione {correlation_risk:.0f}.")
        
        # Detailed
        detailed_factors = []
        if volatility_risk > 60:
            detailed_factors.append("volatilità elevata")
        if liquidity_risk > 60:
            detailed_factors.append("liquidità limitata")
        if market_risk > 70:
            detailed_factors.append("alta esposizione al mercato")
        if correlation_risk > 70:
            detailed_factors.append("forte correlazione sistemica")
        
        detailed = (f"Analisi dettagliata: categoria di rischio {risk_category}. "
                   f"Fattori critici: {', '.join(detailed_factors) if detailed_factors else 'nessuno'}.")
        
        return {
            'summary': summary,
            'technical': technical,
            'detailed': detailed
        }
    
    def _calculate_confidence(self, ticker_data: pd.DataFrame, benchmark_data: pd.DataFrame) -> float:
        """Calcola livello di confidenza dell'analisi"""
        confidence_factors = []
        
        # Data availability
        if len(ticker_data) >= 200:
            confidence_factors.append(1.0)
        elif len(ticker_data) >= 100:
            confidence_factors.append(0.8)
        elif len(ticker_data) >= 50:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.3)
        
        # Benchmark data
        if len(benchmark_data) >= 200:
            confidence_factors.append(1.0)
        elif len(benchmark_data) >= 100:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.5)
        
        # Volume data availability
        if 'Volume' in ticker_data.columns and ticker_data['Volume'].notna().sum() > 100:
            confidence_factors.append(1.0)
        else:
            confidence_factors.append(0.7)
        
        return float(np.mean(confidence_factors))
    
    def _create_error_result(self, ticker: str, error_msg: str) -> VAREResult:
        """Crea risultato di errore"""
        return VAREResult(
            ticker=ticker,
            timestamp=datetime.now(),
            market_risk=50,
            volatility_risk=50,
            liquidity_risk=70,  # Higher default for unknown liquidity
            correlation_risk=50,
            overall_risk=55,
            risk_category="MODERATE",
            risk_factors={'error': error_msg},
            explanation={
                'summary': f"Errore nell'analisi rischio di {ticker}: {error_msg}",
                'technical': "Impossibile calcolare metriche di rischio",
                'detailed': f"Dettagli errore: {error_msg}"
            },
            confidence=0.0
        )


# LangGraph Node Integration
def vare_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo LangGraph per VARE Engine
    
    Input state keys:
    - tickers: List[str] - ticker symbols to analyze
    - vare_config: Dict (optional) - custom configuration
    
    Output state keys:
    - vare_results: Dict[str, VAREResult] - risk results per ticker
    """
    print(f"\n⚠️ [VARE] Avvio analisi Adaptive Risk Engine")
    
    tickers = state.get('tickers', [])
    config = state.get('vare_config', {})
    
    if not tickers:
        print("⚠️ Nessun ticker nello stato → skip VARE")
        return state
    
    engine = VAREEngine()
    results = {}
    
    for ticker in tickers:
        try:
            print(f"⚠️ Analisi rischio per {ticker}...")
            
            benchmark = config.get('benchmark_ticker')
            result = engine.analyze_ticker(ticker, benchmark)
            results[ticker] = result
            
            print(f"✅ {ticker}: rischio {result.risk_category} "
                  f"({result.overall_risk:.0f}/100), confidence={result.confidence:.2f}")
                  
        except Exception as e:
            print(f"❌ Errore VARE per {ticker}: {e}")
            results[ticker] = engine._create_error_result(ticker, str(e))
    
    # Update state
    state['vare_results'] = results
    
    print(f"⚠️ [VARE] Completata analisi rischio per {len(results)} tickers\n")
    return state


if __name__ == "__main__":
    # Test standalone
    engine = VAREEngine()
    result = engine.analyze_ticker("AAPL")
    
    print(f"=== VARE Test Results for {result.ticker} ===")
    print(f"Overall Risk: {result.overall_risk:.1f}/100 ({result.risk_category})")
    print(f"Market Risk: {result.market_risk:.1f}")
    print(f"Volatility Risk: {result.volatility_risk:.1f}")
    print(f"Liquidity Risk: {result.liquidity_risk:.1f}")
    print(f"Correlation Risk: {result.correlation_risk:.1f}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"\nSummary: {result.explanation['summary']}")