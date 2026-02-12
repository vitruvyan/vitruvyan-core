# core/algorithms/vmfl_engine.py
"""
🧠 VMFL - Vitruvyan Multi-Factor Learning

Sistema di apprendimento multi-fattoriale che combina indicatori tecnici,
fondamentali e sentiment per generare insight compositi.

Principi:
- Explainability: ogni fattore e peso è trasparente
- Safety: mai segnali diretti di trading, solo analisi fattoriale
- Composability: moduli componibili per diversi use case
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import yfinance as yf
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# Memory adapter for PostgreSQL/Qdrant integration
try:
    from .algorithm_memory_adapter import store_vmfl_result
except ImportError:
    def store_vmfl_result(result) -> bool:
        return False


@dataclass
class VMFLResult:
    """Risultato dell'analisi VMFL per un ticker"""
    ticker: str
    timestamp: datetime
    
    # Factor scores (0-100)
    technical_score: float
    fundamental_score: float
    sentiment_score: float
    momentum_score: float
    
    # Composite scores
    composite_score: float
    strength_category: str  # "WEAK", "NEUTRAL", "STRONG", "VERY_STRONG"
    
    # Factor breakdown
    factor_weights: Dict[str, float]
    factor_details: Dict[str, Any]
    
    # Learning insights
    pattern_signals: List[str]
    
    # Explainability
    explanation: Dict[str, str]
    
    # Confidence
    confidence: float


class VMFLEngine:
    """
    Vitruvyan Multi-Factor Learning Engine
    
    Combina multiple dimensioni di analisi:
    - Technical: RSI, MACD, Moving Averages, Volume patterns
    - Fundamental: P/E, Revenue growth, Debt ratios (quando disponibili)
    - Sentiment: Price action, Momentum, Volatility patterns
    - Momentum: Trend strength, Breakout patterns, Support/Resistance
    """
    
    def __init__(self):
        # Default factor weights (can be adaptive)
        self.default_weights = {
            'technical': 0.35,
            'fundamental': 0.25,
            'sentiment': 0.20,
            'momentum': 0.20
        }
        
        # Lookback periods
        self.lookback_days = 252  # 1 year
        self.short_ma = 20
        self.long_ma = 50
        
        # Strength thresholds
        self.strength_thresholds = {
            'WEAK': 30,
            'NEUTRAL': 50,
            'STRONG': 70,
            'VERY_STRONG': 85
        }
    
    def analyze_ticker(self, ticker: str, 
                      custom_weights: Optional[Dict[str, float]] = None,
                      fundamental_data: Optional[Dict] = None) -> VMFLResult:
        """
        Analizza ticker con approccio multi-fattoriale
        
        Args:
            ticker: Symbol del ticker
            custom_weights: Pesi personalizzati per i fattori
            fundamental_data: Dati fondamentali esterni (opzionale)
            
        Returns:
            VMFLResult con analisi multi-fattoriale
        """
        try:
            weights = custom_weights or self.default_weights
            
            # Fetch historical data
            stock_data = self._fetch_stock_data(ticker)
            
            if stock_data.empty:
                return self._create_error_result(ticker, "No data available")
            
            # Calculate individual factor scores
            technical_score = self._calculate_technical_score(stock_data)
            fundamental_score = self._calculate_fundamental_score(ticker, fundamental_data)
            sentiment_score = self._calculate_sentiment_score(stock_data)
            momentum_score = self._calculate_momentum_score(stock_data)
            
            # Calculate composite score
            composite_score = (
                technical_score * weights['technical'] +
                fundamental_score * weights['fundamental'] +
                sentiment_score * weights['sentiment'] +
                momentum_score * weights['momentum']
            )
            
            # Determine strength category
            strength_category = self._determine_strength_category(composite_score)
            
            # Generate factor details
            factor_details = self._generate_factor_details(stock_data, ticker)
            
            # Identify pattern signals
            pattern_signals = self._identify_patterns(stock_data)
            
            # Generate explanations
            explanation = self._generate_explanation(
                ticker, technical_score, fundamental_score, 
                sentiment_score, momentum_score, composite_score, 
                strength_category, pattern_signals
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(stock_data, factor_details)
            
            result = VMFLResult(
                ticker=ticker,
                timestamp=datetime.now(),
                technical_score=technical_score,
                fundamental_score=fundamental_score,
                sentiment_score=sentiment_score,
                momentum_score=momentum_score,
                composite_score=composite_score,
                strength_category=strength_category,
                factor_weights=weights,
                factor_details=factor_details,
                pattern_signals=pattern_signals,
                explanation=explanation,
                confidence=confidence
            )
            
            # Store result in PostgreSQL/Qdrant
            try:
                store_vmfl_result(result)
            except Exception as e:
                # Don't fail analysis if storage fails
                pass
            
            return result
            
        except Exception as e:
            return self._create_error_result(ticker, str(e))
    
    def _fetch_stock_data(self, ticker: str) -> pd.DataFrame:
        """Scarica dati storici completi"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days + 100)
            
            stock = yf.Ticker(ticker)
            data = stock.history(start=start_date, end=end_date)
            
            return data
        except Exception:
            return pd.DataFrame()
    
    def _calculate_technical_score(self, data: pd.DataFrame) -> float:
        """Calcola punteggio tecnico basato su indicatori multipli"""
        if data.empty or len(data) < 50:
            return 50
        
        try:
            scores = []
            
            # RSI Score
            rsi = self._calculate_rsi(data['Close'])
            if not rsi.empty:
                current_rsi = rsi.iloc[-1]
                # RSI scoring: 30-70 is neutral, <30 oversold (potential up), >70 overbought (potential down)
                if 40 <= current_rsi <= 60:
                    rsi_score = 60  # Neutral zone
                elif 30 <= current_rsi < 40:
                    rsi_score = 70  # Potentially oversold
                elif 60 < current_rsi <= 70:
                    rsi_score = 40  # Potentially overbought
                elif current_rsi < 30:
                    rsi_score = 80  # Oversold
                else:  # RSI > 70
                    rsi_score = 20  # Overbought
                
                scores.append(rsi_score)
            
            # Moving Average Score
            if len(data) >= self.long_ma:
                current_price = data['Close'].iloc[-1]
                sma_20 = data['Close'].rolling(self.short_ma).mean().iloc[-1]
                sma_50 = data['Close'].rolling(self.long_ma).mean().iloc[-1]
                
                ma_score = 50  # Base neutral
                if current_price > sma_20 > sma_50:
                    ma_score = 75  # Strong uptrend
                elif current_price > sma_20:
                    ma_score = 65  # Moderate uptrend
                elif current_price < sma_20 < sma_50:
                    ma_score = 25  # Strong downtrend
                elif current_price < sma_20:
                    ma_score = 35  # Moderate downtrend
                
                scores.append(ma_score)
            
            # MACD Score
            macd, macd_signal = self._calculate_macd(data['Close'])
            if not macd.empty and not macd_signal.empty:
                current_macd = macd.iloc[-1]
                current_signal = macd_signal.iloc[-1]
                
                if current_macd > current_signal:
                    macd_score = 65  # Bullish crossover
                else:
                    macd_score = 35  # Bearish crossover
                
                scores.append(macd_score)
            
            # Volume Trend Score
            if 'Volume' in data.columns:
                volume_ma = data['Volume'].rolling(20).mean()
                current_volume = data['Volume'].iloc[-1]
                avg_volume = volume_ma.iloc[-1]
                
                if current_volume > avg_volume * 1.5:
                    volume_score = 70  # High volume - strong interest
                elif current_volume > avg_volume:
                    volume_score = 60  # Above average volume
                else:
                    volume_score = 40  # Below average volume
                
                scores.append(volume_score)
            
            # Bollinger Bands Score
            bb_upper, bb_lower = self._calculate_bollinger_bands(data['Close'])
            if not bb_upper.empty and not bb_lower.empty:
                current_price = data['Close'].iloc[-1]
                current_upper = bb_upper.iloc[-1]
                current_lower = bb_lower.iloc[-1]
                
                bb_position = (current_price - current_lower) / (current_upper - current_lower)
                
                if bb_position > 0.8:
                    bb_score = 30  # Near upper band - potentially overbought
                elif bb_position < 0.2:
                    bb_score = 70  # Near lower band - potentially oversold
                else:
                    bb_score = 50  # Middle range
                
                scores.append(bb_score)
            
            return float(np.mean(scores)) if scores else 50
            
        except Exception:
            return 50
    
    def _calculate_fundamental_score(self, ticker: str, external_data: Optional[Dict] = None) -> float:
        """Calcola punteggio fondamentale"""
        if external_data:
            # Use provided fundamental data
            return self._score_fundamental_data(external_data)
        
        try:
            # Try to fetch basic fundamental data via yfinance
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info:
                return 50  # Neutral if no data
            
            scores = []
            
            # P/E Ratio scoring
            pe_ratio = info.get('trailingPE')
            if pe_ratio and pe_ratio > 0:
                if 10 <= pe_ratio <= 20:
                    scores.append(70)  # Reasonable valuation
                elif 5 <= pe_ratio < 10 or 20 < pe_ratio <= 30:
                    scores.append(60)  # Acceptable valuation
                elif pe_ratio < 5:
                    scores.append(40)   # Potentially undervalued or problematic
                else:  # pe_ratio > 30
                    scores.append(30)   # Potentially overvalued
            
            # Revenue Growth
            revenue_growth = info.get('revenueGrowth')
            if revenue_growth is not None:
                if revenue_growth > 0.15:  # >15% growth
                    scores.append(80)
                elif revenue_growth > 0.05:  # 5-15% growth
                    scores.append(65)
                elif revenue_growth > 0:    # Positive growth
                    scores.append(55)
                else:                       # Negative growth
                    scores.append(30)
            
            # Profit Margins
            profit_margin = info.get('profitMargins')
            if profit_margin is not None:
                if profit_margin > 0.20:    # >20% margin
                    scores.append(75)
                elif profit_margin > 0.10:  # 10-20% margin
                    scores.append(65)
                elif profit_margin > 0.05:  # 5-10% margin
                    scores.append(55)
                elif profit_margin > 0:     # Positive margin
                    scores.append(45)
                else:                       # Negative margin
                    scores.append(25)
            
            # Return on Equity
            roe = info.get('returnOnEquity')
            if roe is not None:
                if roe > 0.20:      # >20% ROE
                    scores.append(80)
                elif roe > 0.15:    # 15-20% ROE
                    scores.append(70)
                elif roe > 0.10:    # 10-15% ROE
                    scores.append(60)
                elif roe > 0:       # Positive ROE
                    scores.append(50)
                else:               # Negative ROE
                    scores.append(25)
            
            return float(np.mean(scores)) if scores else 50
            
        except Exception:
            return 50  # Fallback to neutral
    
    def _calculate_sentiment_score(self, data: pd.DataFrame) -> float:
        """Calcola punteggio sentiment basato su price action"""
        if data.empty or len(data) < 30:
            return 50
        
        try:
            scores = []
            
            # Price momentum over different periods
            current_price = data['Close'].iloc[-1]
            
            # 5-day momentum
            if len(data) >= 5:
                price_5d = data['Close'].iloc[-5]
                momentum_5d = (current_price - price_5d) / price_5d
                scores.append(50 + momentum_5d * 200)  # Convert to 0-100 scale
            
            # 20-day momentum
            if len(data) >= 20:
                price_20d = data['Close'].iloc[-20]
                momentum_20d = (current_price - price_20d) / price_20d
                scores.append(50 + momentum_20d * 100)
            
            # Volatility sentiment (lower volatility = higher sentiment)
            returns = data['Close'].pct_change().dropna()
            if len(returns) > 20:
                volatility = returns.rolling(20).std().iloc[-1]
                vol_score = max(20, 80 - volatility * 1000)  # Inverse relationship
                scores.append(vol_score)
            
            # High-Low sentiment (closing near highs = positive sentiment)
            if len(data) >= 20:
                recent_data = data.tail(20)
                high_low_position = (current_price - recent_data['Low'].min()) / (
                    recent_data['High'].max() - recent_data['Low'].min()
                )
                hl_score = high_low_position * 100
                scores.append(hl_score)
            
            # Ensure scores are within 0-100 range
            clipped_scores = [max(0, min(100, score)) for score in scores]
            
            return float(np.mean(clipped_scores)) if clipped_scores else 50
            
        except Exception:
            return 50
    
    def _calculate_momentum_score(self, data: pd.DataFrame) -> float:
        """Calcola punteggio momentum con pattern recognition"""
        if data.empty or len(data) < 50:
            return 50
        
        try:
            scores = []
            
            # Trend consistency
            prices = data['Close']
            sma_10 = prices.rolling(10).mean()
            sma_20 = prices.rolling(20).mean()
            sma_50 = prices.rolling(50).mean()
            
            if len(sma_50.dropna()) > 0:
                current_sma_10 = sma_10.iloc[-1]
                current_sma_20 = sma_20.iloc[-1]
                current_sma_50 = sma_50.iloc[-1]
                
                if current_sma_10 > current_sma_20 > current_sma_50:
                    trend_score = 80  # Strong uptrend
                elif current_sma_10 > current_sma_20:
                    trend_score = 65  # Moderate uptrend
                elif current_sma_10 < current_sma_20 < current_sma_50:
                    trend_score = 20  # Strong downtrend
                else:
                    trend_score = 50  # Mixed/sideways
                
                scores.append(trend_score)
            
            # Breakout momentum (price vs recent resistance)
            if len(data) >= 50:
                recent_high = data['High'].tail(50).max()
                current_price = data['Close'].iloc[-1]
                
                if current_price >= recent_high * 0.98:  # Near or above recent high
                    breakout_score = 75
                elif current_price >= recent_high * 0.95:
                    breakout_score = 65
                elif current_price <= recent_high * 0.85:  # Well below recent high
                    breakout_score = 35
                else:
                    breakout_score = 50
                
                scores.append(breakout_score)
            
            # Volume-price momentum
            if 'Volume' in data.columns and len(data) >= 20:
                recent_data = data.tail(20)
                price_change = (recent_data['Close'].iloc[-1] - recent_data['Close'].iloc[0]) / recent_data['Close'].iloc[0]
                volume_ratio = recent_data['Volume'].mean() / data['Volume'].tail(100).mean()
                
                if price_change > 0 and volume_ratio > 1.2:
                    vp_score = 75  # Positive price move with high volume
                elif price_change > 0:
                    vp_score = 60  # Positive price move
                elif price_change < 0 and volume_ratio > 1.2:
                    vp_score = 25  # Negative price move with high volume
                else:
                    vp_score = 45  # Weak momentum
                
                scores.append(vp_score)
            
            return float(np.mean(scores)) if scores else 50
            
        except Exception:
            return 50
    
    def _generate_factor_details(self, data: pd.DataFrame, ticker: str) -> Dict[str, Any]:
        """Genera dettagli sui fattori calcolati"""
        details = {}
        
        try:
            current_price = data['Close'].iloc[-1]
            details['current_price'] = float(current_price)
            
            # Technical indicators
            rsi = self._calculate_rsi(data['Close'])
            if not rsi.empty:
                details['rsi'] = float(rsi.iloc[-1])
            
            # Moving averages
            if len(data) >= 50:
                details['sma_20'] = float(data['Close'].rolling(20).mean().iloc[-1])
                details['sma_50'] = float(data['Close'].rolling(50).mean().iloc[-1])
            
            # Volume
            if 'Volume' in data.columns:
                details['avg_volume_20d'] = int(data['Volume'].tail(20).mean())
                details['current_volume'] = int(data['Volume'].iloc[-1])
            
            # Price levels
            details['52w_high'] = float(data['High'].tail(252).max()) if len(data) >= 252 else float(data['High'].max())
            details['52w_low'] = float(data['Low'].tail(252).min()) if len(data) >= 252 else float(data['Low'].min())
            
            # Volatility
            returns = data['Close'].pct_change().dropna()
            if len(returns) >= 20:
                details['volatility_20d'] = float(returns.tail(20).std() * np.sqrt(252))
            
        except Exception as e:
            details['calculation_error'] = str(e)
        
        return details
    
    def _identify_patterns(self, data: pd.DataFrame) -> List[str]:
        """Identifica pattern di prezzo significativi"""
        patterns = []
        
        try:
            if len(data) < 50:
                return patterns
            
            current_price = data['Close'].iloc[-1]
            
            # Support/Resistance breaks
            recent_high = data['High'].tail(50).max()
            recent_low = data['Low'].tail(50).min()
            
            if current_price >= recent_high * 0.995:
                patterns.append("Breakout sopra resistenza recente")
            
            if current_price <= recent_low * 1.005:
                patterns.append("Breakdown sotto supporto recente")
            
            # Moving average patterns
            if len(data) >= 50:
                sma_20 = data['Close'].rolling(20).mean().iloc[-1]
                sma_50 = data['Close'].rolling(50).mean().iloc[-1]
                
                if current_price > sma_20 > sma_50:
                    patterns.append("Trend rialzista confermato")
                elif current_price < sma_20 < sma_50:
                    patterns.append("Trend ribassista confermato")
            
            # Volume patterns
            if 'Volume' in data.columns and len(data) >= 20:
                current_volume = data['Volume'].iloc[-1]
                avg_volume = data['Volume'].tail(20).mean()
                
                if current_volume > avg_volume * 2:
                    patterns.append("Volume eccezionalmente elevato")
                elif current_volume < avg_volume * 0.3:
                    patterns.append("Volume molto basso")
            
            # Volatility patterns
            returns = data['Close'].pct_change().dropna()
            if len(returns) >= 20:
                recent_vol = returns.tail(5).std()
                avg_vol = returns.tail(20).std()
                
                if recent_vol > avg_vol * 1.5:
                    patterns.append("Volatilità in aumento")
                elif recent_vol < avg_vol * 0.5:
                    patterns.append("Volatilità in diminuzione")
            
        except Exception:
            pass
        
        return patterns
    
    def _generate_explanation(self, ticker: str, technical: float, fundamental: float,
                            sentiment: float, momentum: float, composite: float,
                            strength_category: str, patterns: List[str]) -> Dict[str, str]:
        """Genera spiegazioni comprehensive"""
        
        # Identify dominant factors
        factors = {
            'tecnico': technical,
            'fondamentale': fundamental,
            'sentiment': sentiment,
            'momentum': momentum
        }
        
        strongest_factor = max(factors, key=factors.get)
        strongest_value = factors[strongest_factor]
        
        # Summary
        summary = (f"{ticker} presenta forza {strength_category.lower()} "
                  f"(score composito: {composite:.0f}/100). "
                  f"Fattore dominante: {strongest_factor} ({strongest_value:.0f}).")
        
        # Technical
        technical_desc = (f"Breakdown fattori: Tecnico {technical:.0f}, "
                         f"Fondamentale {fundamental:.0f}, "
                         f"Sentiment {sentiment:.0f}, "
                         f"Momentum {momentum:.0f}.")
        
        # Detailed
        pattern_text = f"Pattern identificati: {', '.join(patterns)}" if patterns else "Nessun pattern significativo"
        detailed = (f"Analisi dettagliata: categoria {strength_category}. "
                   f"{pattern_text}. "
                   f"Confidenza nell'analisi basata su disponibilità dati completa.")
        
        return {
            'summary': summary,
            'technical': technical_desc,
            'detailed': detailed
        }
    
    def _determine_strength_category(self, composite_score: float) -> str:
        """Determina categoria di forza"""
        if composite_score >= self.strength_thresholds['VERY_STRONG']:
            return "VERY_STRONG"
        elif composite_score >= self.strength_thresholds['STRONG']:
            return "STRONG"
        elif composite_score >= self.strength_thresholds['NEUTRAL']:
            return "NEUTRAL"
        else:
            return "WEAK"
    
    def _calculate_confidence(self, data: pd.DataFrame, factor_details: Dict) -> float:
        """Calcola confidenza dell'analisi"""
        confidence_factors = []
        
        # Data sufficiency
        if len(data) >= 200:
            confidence_factors.append(1.0)
        elif len(data) >= 100:
            confidence_factors.append(0.8)
        elif len(data) >= 50:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.3)
        
        # Indicator availability
        available_indicators = sum([
            'rsi' in factor_details,
            'sma_20' in factor_details,
            'avg_volume_20d' in factor_details,
            'volatility_20d' in factor_details
        ])
        
        confidence_factors.append(available_indicators / 4.0)
        
        # Error handling
        if 'calculation_error' in factor_details:
            confidence_factors.append(0.5)
        else:
            confidence_factors.append(1.0)
        
        return float(np.mean(confidence_factors))
    
    # Technical indicator calculation helpers
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcola RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        except Exception:
            return pd.Series()
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
        """Calcola MACD e signal line"""
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd = ema_fast - ema_slow
            macd_signal = macd.ewm(span=signal).mean()
            return macd, macd_signal
        except Exception:
            return pd.Series(), pd.Series()
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series]:
        """Calcola Bollinger Bands"""
        try:
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            return upper_band, lower_band
        except Exception:
            return pd.Series(), pd.Series()
    
    def _score_fundamental_data(self, data: Dict) -> float:
        """Scoring di dati fondamentali esterni"""
        # Implementazione per dati fondamentali personalizzati
        scores = []
        
        if 'pe_ratio' in data:
            pe = data['pe_ratio']
            if 10 <= pe <= 20:
                scores.append(70)
            elif 5 <= pe <= 30:
                scores.append(55)
            else:
                scores.append(40)
        
        if 'revenue_growth' in data:
            growth = data['revenue_growth']
            if growth > 0.15:
                scores.append(80)
            elif growth > 0:
                scores.append(60)
            else:
                scores.append(30)
        
        return float(np.mean(scores)) if scores else 50
    
    def _create_error_result(self, ticker: str, error_msg: str) -> VMFLResult:
        """Crea risultato di errore"""
        return VMFLResult(
            ticker=ticker,
            timestamp=datetime.now(),
            technical_score=50,
            fundamental_score=50,
            sentiment_score=50,
            momentum_score=50,
            composite_score=50,
            strength_category="NEUTRAL",
            factor_weights=self.default_weights,
            factor_details={'error': error_msg},
            pattern_signals=[],
            explanation={
                'summary': f"Errore nell'analisi multi-fattoriale di {ticker}: {error_msg}",
                'technical': "Impossibile calcolare fattori",
                'detailed': f"Dettagli errore: {error_msg}"
            },
            confidence=0.0
        )


# LangGraph Node Integration
def vmfl_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo LangGraph per VMFL Engine
    
    Input state keys:
    - tickers: List[str] - ticker symbols to analyze
    - vmfl_config: Dict (optional) - custom weights and config
    - fundamental_data: Dict (optional) - external fundamental data
    
    Output state keys:
    - vmfl_results: Dict[str, VMFLResult] - multi-factor results per ticker
    """
    print(f"\n🧠 [VMFL] Avvio analisi Multi-Factor Learning")
    
    tickers = state.get('tickers', [])
    config = state.get('vmfl_config', {})
    fundamental_data = state.get('fundamental_data', {})
    
    if not tickers:
        print("⚠️ Nessun ticker nello stato → skip VMFL")
        return state
    
    engine = VMFLEngine()
    results = {}
    
    for ticker in tickers:
        try:
            print(f"🧠 Analisi multi-factor per {ticker}...")
            
            # Get ticker-specific config
            custom_weights = config.get('weights')
            ticker_fundamentals = fundamental_data.get(ticker)
            
            result = engine.analyze_ticker(ticker, custom_weights, ticker_fundamentals)
            results[ticker] = result
            
            print(f"✅ {ticker}: {result.strength_category} "
                  f"(composito: {result.composite_score:.0f}/100), "
                  f"confidence={result.confidence:.2f}")
                  
        except Exception as e:
            print(f"❌ Errore VMFL per {ticker}: {e}")
            results[ticker] = engine._create_error_result(ticker, str(e))
    
    # Update state
    state['vmfl_results'] = results
    
    print(f"🧠 [VMFL] Completata analisi multi-factor per {len(results)} tickers\n")
    return state


if __name__ == "__main__":
    # Test standalone
    engine = VMFLEngine()
    result = engine.analyze_ticker("AAPL")
    
    print(f"=== VMFL Test Results for {result.ticker} ===")
    print(f"Composite Score: {result.composite_score:.1f}/100 ({result.strength_category})")
    print(f"Technical: {result.technical_score:.1f}")
    print(f"Fundamental: {result.fundamental_score:.1f}")
    print(f"Sentiment: {result.sentiment_score:.1f}")
    print(f"Momentum: {result.momentum_score:.1f}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Patterns: {', '.join(result.pattern_signals)}")
    print(f"\nSummary: {result.explanation['summary']}")