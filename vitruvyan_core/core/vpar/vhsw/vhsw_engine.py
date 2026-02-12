# core/algorithms/vhsw_engine.py
"""
🔍 VHSW - Vitruvyan Historical Strength Window

Analizza la forza storica di un ticker attraverso finestre temporali multiple.
Non produce segnali BUY/SELL ma indica "momentum", "stability", "volatility".

Principi:
- Explainability: ogni punteggio è tracciabile e spiegabile
- Safety: mai decisioni dirette, solo indicatori informativi
- Composability: funziona standalone o come nodo LangGraph
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import yfinance as yf
from dataclasses import dataclass

# Memory adapter for PostgreSQL/Qdrant integration
try:
    from .algorithm_memory_adapter import store_vhsw_result
except ImportError:
    def store_vhsw_result(result) -> bool:
        return False


@dataclass
class VHSWResult:
    """Risultato dell'analisi VHSW per un ticker"""
    ticker: str
    timestamp: datetime
    
    # Metriche di forza storica (0-100)
    momentum_score: float
    stability_score: float
    volatility_score: float
    trend_strength: float
    
    # Finestre temporali analizzate
    windows_analyzed: List[str]
    
    # Explainability
    explanation: Dict[str, str]
    technical_details: Dict[str, Any]
    
    # Confidence level (0-1)
    confidence: float


class VHSWEngine:
    """
    Vitruvyan Historical Strength Window Engine
    
    Analizza la performance storica attraverso finestre multiple:
    - Short term (1-3 mesi)
    - Medium term (3-12 mesi) 
    - Long term (1-3 anni)
    """
    
    def __init__(self):
        self.windows = {
            'short': {'months': 3, 'weight': 0.4},
            'medium': {'months': 12, 'weight': 0.4}, 
            'long': {'months': 36, 'weight': 0.2}
        }
        
    def analyze_ticker(self, ticker: str, 
                      custom_windows: Optional[Dict] = None) -> VHSWResult:
        """
        Analizza la forza storica di un ticker
        
        Args:
            ticker: Symbol del ticker (es. 'AAPL')
            custom_windows: Finestre personalizzate (opzionale)
            
        Returns:
            VHSWResult con metriche e spiegazioni
        """
        try:
            # Use custom windows if provided
            windows = custom_windows or self.windows
            
            # Download historical data
            stock_data = self._fetch_historical_data(ticker, max(
                w['months'] for w in windows.values()
            ))
            
            if stock_data.empty:
                return self._create_error_result(ticker, "No data available")
            
            # Calculate metrics for each window
            window_results = {}
            for window_name, window_config in windows.items():
                window_results[window_name] = self._analyze_window(
                    stock_data, window_config['months'], window_config['weight']
                )
            
            # Aggregate results
            momentum_score = self._calculate_weighted_average(
                window_results, 'momentum', windows
            )
            stability_score = self._calculate_weighted_average(
                window_results, 'stability', windows
            )
            volatility_score = self._calculate_weighted_average(
                window_results, 'volatility', windows
            )
            trend_strength = self._calculate_trend_strength(window_results)
            
            # Generate explanations
            explanation = self._generate_explanation(
                ticker, momentum_score, stability_score, 
                volatility_score, trend_strength, window_results
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(window_results, stock_data)
            
            result = VHSWResult(
                ticker=ticker,
                timestamp=datetime.now(),
                momentum_score=momentum_score,
                stability_score=stability_score,
                volatility_score=volatility_score,
                trend_strength=trend_strength,
                windows_analyzed=list(windows.keys()),
                explanation=explanation,
                technical_details=window_results,
                confidence=confidence
            )
            
            # Store result in PostgreSQL/Qdrant
            try:
                store_vhsw_result(result)
            except Exception as e:
                # Don't fail analysis if storage fails
                pass
            
            return result
            
        except Exception as e:
            return self._create_error_result(ticker, str(e))
    
    def _fetch_historical_data(self, ticker: str, months: int) -> pd.DataFrame:
        """Scarica dati storici per il numero di mesi specificato"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)
            
            stock = yf.Ticker(ticker)
            data = stock.history(start=start_date, end=end_date)
            
            return data
        except Exception:
            return pd.DataFrame()
    
    def _analyze_window(self, data: pd.DataFrame, months: int, weight: float) -> Dict[str, float]:
        """Analizza una finestra temporale specifica"""
        # Get data for this window
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        # Make cutoff_date timezone-aware if data index is timezone-aware
        if data.index.tz is not None:
            cutoff_date = cutoff_date.replace(tzinfo=data.index.tz)
        window_data = data[data.index >= cutoff_date]
        
        if window_data.empty:
            return {'momentum': 0, 'stability': 0, 'volatility': 50, 'data_points': 0}
        
        # Calculate metrics
        prices = window_data['Close']
        
        # Momentum: % change from start to end
        momentum_pct = ((prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]) * 100
        momentum_score = min(100, max(0, 50 + momentum_pct))  # Normalize to 0-100
        
        # Stability: inverse of coefficient of variation
        cv = prices.std() / prices.mean() if prices.mean() > 0 else 1
        stability_score = max(0, 100 - (cv * 100))
        
        # Volatility: rolling std normalized
        volatility = prices.rolling(window=min(20, len(prices))).std().mean()
        volatility_score = min(100, (volatility / prices.mean()) * 100) if prices.mean() > 0 else 50
        
        return {
            'momentum': momentum_score, 
            'stability': stability_score,
            'volatility': volatility_score,
            'data_points': len(window_data),
            'start_price': prices.iloc[0],
            'end_price': prices.iloc[-1],
            'avg_price': prices.mean(),
            'price_change_pct': momentum_pct
        }
    
    def _calculate_weighted_average(self, window_results: Dict, metric: str, windows: Dict) -> float:
        """Calcola la media ponderata di una metrica attraverso le finestre"""
        weighted_sum = 0
        total_weight = 0
        
        for window_name, results in window_results.items():
            if window_name in windows and results['data_points'] > 0:
                weight = windows[window_name]['weight']
                weighted_sum += results[metric] * weight
                total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0
    
    def _calculate_trend_strength(self, window_results: Dict) -> float:
        """Calcola la forza del trend confrontando le finestre"""
        momentum_scores = [r['momentum'] for r in window_results.values() if r['data_points'] > 0]
        
        if len(momentum_scores) < 2:
            return 50
        
        # Trend strength: consistency across windows
        momentum_std = np.std(momentum_scores)
        trend_strength = max(0, 100 - momentum_std)
        
        return trend_strength
    
    def _generate_explanation(self, ticker: str, momentum: float, stability: float,
                            volatility: float, trend_strength: float, 
                            window_results: Dict) -> Dict[str, str]:
        """Genera spiegazioni human-readable"""
        
        # Summary explanation
        if momentum > 70:
            momentum_desc = "forte momentum positivo"
        elif momentum > 30:
            momentum_desc = "momentum neutrale"
        else:
            momentum_desc = "momentum negativo"
            
        if stability > 70:
            stability_desc = "alta stabilità"
        elif stability > 30:
            stability_desc = "stabilità moderata"
        else:
            stability_desc = "bassa stabilità"
        
        summary = (f"{ticker} mostra {momentum_desc} con {stability_desc}. "
                  f"Forza del trend: {trend_strength:.0f}/100.")
        
        # Technical explanation
        windows_info = []
        for window_name, results in window_results.items():
            if results['data_points'] > 0:
                change_pct = results.get('price_change_pct', 0)
                windows_info.append(f"{window_name}: {change_pct:+.1f}%")
        
        technical = (f"Analisi su finestre: {', '.join(windows_info)}. "
                    f"Volatilità media: {volatility:.1f}/100.")
        
        # Detailed explanation
        detailed_parts = []
        for window_name, results in window_results.items():
            if results['data_points'] > 0:
                detailed_parts.append(
                    f"Finestra {window_name}: {results['data_points']} giorni, "
                    f"da ${results['start_price']:.2f} a ${results['end_price']:.2f}"
                )
        
        detailed = "Dettagli finestre: " + "; ".join(detailed_parts)
        
        return {
            'summary': summary,
            'technical': technical, 
            'detailed': detailed
        }
    
    def _calculate_confidence(self, window_results: Dict, stock_data: pd.DataFrame) -> float:
        """Calcola il livello di confidenza dell'analisi"""
        data_quality_score = 0
        total_windows = len(window_results)
        
        for results in window_results.values():
            if results['data_points'] > 50:  # Sufficient data
                data_quality_score += 1
            elif results['data_points'] > 20:  # Some data
                data_quality_score += 0.5
        
        # Normalize to 0-1
        confidence = data_quality_score / total_windows if total_windows > 0 else 0
        
        # Adjust for total data availability
        if len(stock_data) > 200:
            confidence *= 1.0
        elif len(stock_data) > 50:
            confidence *= 0.8
        else:
            confidence *= 0.5
            
        return min(1.0, confidence)
    
    def _create_error_result(self, ticker: str, error_msg: str) -> VHSWResult:
        """Crea un risultato di errore"""
        return VHSWResult(
            ticker=ticker,
            timestamp=datetime.now(),
            momentum_score=0,
            stability_score=0,
            volatility_score=50,
            trend_strength=0,
            windows_analyzed=[],
            explanation={
                'summary': f"Errore nell'analisi di {ticker}: {error_msg}",
                'technical': "Dati insufficienti per l'analisi",
                'detailed': f"Dettagli errore: {error_msg}"
            },
            technical_details={},
            confidence=0.0
        )


# LangGraph Node Integration
def vhsw_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo LangGraph per VHSW Engine
    
    Input state keys:
    - tickers: List[str] - ticker symbols to analyze
    - vhsw_config: Dict (optional) - custom configuration
    
    Output state keys:
    - vhsw_results: Dict[str, VHSWResult] - results per ticker
    """
    print(f"\n🔍 [VHSW] Avvio analisi Historical Strength Window")
    
    tickers = state.get('tickers', [])
    config = state.get('vhsw_config', {})
    
    if not tickers:
        print("⚠️ Nessun ticker nello stato → skip VHSW")
        return state
    
    engine = VHSWEngine()
    results = {}
    
    for ticker in tickers:
        try:
            print(f"🔍 Analisi VHSW per {ticker}...")
            result = engine.analyze_ticker(ticker, config.get('windows'))
            results[ticker] = result
            
            print(f"✅ {ticker}: momentum={result.momentum_score:.1f}, "
                  f"stability={result.stability_score:.1f}, confidence={result.confidence:.2f}")
                  
        except Exception as e:
            print(f"❌ Errore VHSW per {ticker}: {e}")
            results[ticker] = engine._create_error_result(ticker, str(e))
    
    # Update state
    state['vhsw_results'] = results
    
    print(f"🔍 [VHSW] Completata analisi per {len(results)} tickers\n")
    return state


if __name__ == "__main__":
    # Test standalone
    engine = VHSWEngine()
    result = engine.analyze_ticker("AAPL")
    
    print(f"=== VHSW Test Results for {result.ticker} ===")
    print(f"Momentum: {result.momentum_score:.1f}/100")
    print(f"Stability: {result.stability_score:.1f}/100") 
    print(f"Volatility: {result.volatility_score:.1f}/100")
    print(f"Trend Strength: {result.trend_strength:.1f}/100")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"\nSummary: {result.explanation['summary']}")