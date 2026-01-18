# core/logic/vitruvyan_proprietary/vee/vee_analyzer.py
"""
🔍 VEE Analyzer - Pattern Recognition per KPI Finanziari

Analizza i KPI tecnici ricevuti da agenti e identifica:
- Segnali chiave e pattern significativi
- Fattori dominanti nell'analisi
- Intensità e direzione dei segnali
- Correlazioni e anomalie

Principi:
- Analisi puramente quantitativa dei dati
- Identificazione deterministica dei pattern
- Scoring normalizzato per comparabilità
"""

import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from vitruvyan_core.domains.explainability_contract import ExplainabilityProvider


@dataclass
class AnalysisResult:
    """Risultato dell'analisi KPI"""
    entity_id: str  # Changed from entity_id
    timestamp: datetime
    
    # Segnali identificati
    signals: List[str]
    signal_strengths: Dict[str, float]  # 0-1 intensity
    
    # Fattore dominante
    dominant_factor: str
    dominant_strength: float
    
    # Metriche composite
    overall_intensity: float    # 0-1 overall signal strength
    sentiment_direction: str    # "positive", "negative", "neutral"
    confidence_level: float     # 0-1 confidence in analysis
    
    # Pattern specifici
    patterns: List[str]
    anomalies: List[str]
    
    # Metadata per explainability
    kpi_count: int
    missing_indicators: List[str]


class VEEAnalyzer:
    """
    Analizzatore avanzato per KPI finanziari
    
    Identifica pattern e segnali da diversi tipi di input:
    - Z-scores da Neural Engine
    - Metriche da Risk Engine (VARE)
    - Scores da Multi-Factor Learning (VMFL) 
    - Sentiment da agenti esterni
    - Momentum e trend indicators
    """
    
    def __init__(self):
        # Thresholds per classificazione segnali
        self.signal_thresholds = {
            'weak': 0.3,
            'moderate': 0.6,
            'strong': 0.8,
            'extreme': 0.95
        }
        
        # Mapping dei KPI alle categorie semantiche
        self.kpi_categories = {
            'momentum': ['momentum_z', 'momentum_score', 'trend_strength'],
            'volatility': ['vola_z', 'volatility_risk', 'volatility_score'],
            'sentiment': ['sentiment_z', 'sentiment_score', 'market_sentiment'],
            'risk': ['risk_score', 'overall_risk', 'market_risk', 'liquidity_risk'],
            'technical': ['technical_score', 'rsi', 'macd', 'bollinger'],
            'fundamental': ['fundamental_score', 'pe_ratio', 'revenue_growth'],
            'strength': ['composite_score', 'historical_strength', 'stability_score']
        }
        
        # Pattern recognition rules
        self.pattern_rules = {
            'bullish_momentum': lambda kpi: self._check_bullish_momentum(kpi),
            'bearish_momentum': lambda kpi: self._check_bearish_momentum(kpi),
            'high_volatility': lambda kpi: self._check_high_volatility(kpi),
            'risk_elevation': lambda kpi: self._check_risk_elevation(kpi),
            'sentiment_divergence': lambda kpi: self._check_sentiment_divergence(kpi),
            'technical_breakout': lambda kpi: self._check_technical_breakout(kpi)
        }
    
    def analyze_metrics(self, entity_id: str, metrics: Dict[str, Any], 
                       explainability_provider: ExplainabilityProvider) -> AnalysisResult:
        """
        Analizza le metriche e identifica pattern significativi
        
        Args:
            entity_id: ID dell'entità (domain-agnostic)
            metrics: Dictionary con metriche da analizzare
            explainability_provider: Domain provider per categorie e descrizioni
            
        Returns:
            AnalysisResult con analisi completa
        """
        try:
            if not metrics or not isinstance(metrics, dict):
                return self._create_empty_result(entity_id, "Empty or invalid metrics data")
            
            # Get domain-specific categories and descriptions
            signal_descriptions = explainability_provider.get_signal_descriptions()
            factor_categories = explainability_provider.get_factor_categories()
            
            # Normalize and clean metrics data
            normalized_metrics = self._normalize_metrics(metrics)
            
            # Identify signals by category using domain descriptions
            signals, signal_strengths = self._identify_signals_domain_aware(
                normalized_metrics, signal_descriptions
            )
            
            # Find dominant factor using domain categories
            dominant_factor, dominant_strength = self._find_dominant_factor_domain_aware(
                normalized_metrics, factor_categories
            )
            
            # Calculate overall metrics
            overall_intensity = self._calculate_overall_intensity(signal_strengths)
            sentiment_direction = self._determine_sentiment_direction(normalized_metrics)
            confidence_level = self._calculate_confidence(normalized_metrics, signals)
            
            # Identify patterns and anomalies
            patterns = self._identify_patterns(normalized_metrics)
            anomalies = self._identify_anomalies(normalized_metrics)
            
            # Metadata
            metrics_count = len([k for k, v in metrics.items() if v is not None])
            missing_indicators = self._identify_missing_indicators(metrics)
            
            return AnalysisResult(
                entity_id=entity_id,
                timestamp=datetime.now(),
                signals=signals,
                signal_strengths=signal_strengths,
                dominant_factor=dominant_factor,
                dominant_strength=dominant_strength,
                overall_intensity=overall_intensity,
                sentiment_direction=sentiment_direction,
                confidence_level=confidence_level,
                patterns=patterns,
                anomalies=anomalies,
                kpi_count=metrics_count,
                missing_indicators=missing_indicators
            )
            
        except Exception as e:
            return self._create_error_result(entity_id, str(e))
    
    def _normalize_kpi(self, kpi: Dict[str, Any]) -> Dict[str, float]:
        """Normalizza i KPI in valori 0-1 per analisi uniforme"""
        normalized = {}
        
        for key, value in kpi.items():
            if value is None:
                continue
                
            try:
                # Convert to float
                if isinstance(value, (int, float)):
                    num_value = float(value)
                elif isinstance(value, str):
                    # Try to extract numeric value from string
                    import re
                    match = re.search(r'-?\d+\.?\d*', value)
                    if match:
                        num_value = float(match.group())
                    else:
                        continue
                else:
                    continue
                
                # Normalize based on key type
                if '_z' in key.lower():
                    # Z-scores: normalize using tanh to 0-1
                    normalized[key] = (np.tanh(num_value / 2) + 1) / 2
                elif 'score' in key.lower():
                    # Scores typically 0-100, normalize to 0-1
                    if num_value <= 1:
                        normalized[key] = abs(num_value)  # Already 0-1
                    else:
                        normalized[key] = min(1.0, abs(num_value) / 100.0)
                elif 'risk' in key.lower():
                    # Risk metrics: higher = more risky, normalize and invert for signal strength
                    if num_value <= 1:
                        normalized[key] = 1 - abs(num_value)
                    else:
                        normalized[key] = 1 - min(1.0, abs(num_value) / 100.0)
                elif 'ratio' in key.lower():
                    # Ratios: normalize using sigmoid
                    normalized[key] = 1 / (1 + np.exp(-num_value / 10))
                else:
                    # Generic normalization
                    if abs(num_value) <= 1:
                        normalized[key] = abs(num_value)
                    elif abs(num_value) <= 100:
                        normalized[key] = abs(num_value) / 100.0
                    else:
                        normalized[key] = min(1.0, abs(num_value) / 1000.0)
                        
            except Exception:
                continue
        
        return normalized
    
    def _identify_signals(self, normalized_kpi: Dict[str, float]) -> Tuple[List[str], Dict[str, float]]:
        """Identifica segnali significativi dai KPI normalizzati"""
        signals = []
        strengths = {}
        
        # Group KPIs by category and analyze
        for category, kpi_keys in self.kpi_categories.items():
            category_values = []
            category_keys = []
            
            for key in kpi_keys:
                if key in normalized_kpi:
                    category_values.append(normalized_kpi[key])
                    category_keys.append(key)
            
            if not category_values:
                continue
                
            # Calculate category strength
            avg_strength = np.mean(category_values)
            max_strength = max(category_values)
            
            # Determine signal intensity (English only)
            if max_strength >= self.signal_thresholds['strong']:
                intensity = 'strong'
                signal_strength = max_strength
            elif max_strength >= self.signal_thresholds['moderate']:
                intensity = 'moderate'
                signal_strength = avg_strength
            elif max_strength >= self.signal_thresholds['weak']:
                intensity = 'weak'
                signal_strength = avg_strength
            else:
                continue
            
            # Create semantic signal description (English only)
            if category == 'momentum':
                if avg_strength > 0.6:
                    signals.append(f"{intensity} positive momentum")
                else:
                    signals.append(f"{intensity} neutral momentum")
            elif category == 'volatility':
                if avg_strength < 0.4:  # Low volatility (inverted for risk)
                    signals.append(f"{intensity} elevated volatility")
                else:
                    signals.append(f"{intensity} contained volatility")
            elif category == 'sentiment':
                if avg_strength > 0.6:
                    signals.append(f"{intensity} positive sentiment")
                elif avg_strength < 0.4:
                    signals.append(f"{intensity} negative sentiment")
                else:
                    signals.append(f"{intensity} neutral sentiment")
            elif category == 'risk':
                if avg_strength < 0.4:  # High risk (inverted)
                    signals.append(f"{intensity} elevated risk profile")
                else:
                    signals.append(f"{intensity} contained risk profile")
            elif category == 'technical':
                if avg_strength > 0.6:
                    signals.append(f"{intensity} favorable technical indicators")
                else:
                    signals.append(f"{intensity} mixed technical indicators")
            elif category == 'strength':
                if avg_strength > 0.6:
                    signals.append(f"{intensity} overall strength")
            
            strengths[category] = signal_strength
        
        return signals, strengths
    
    def _find_dominant_factor(self, normalized_kpi: Dict[str, float]) -> Tuple[str, float]:
        """Identifica il fattore dominante nell'analisi"""
        if not normalized_kpi:
            return "no factor", 0.0
        
        # Find KPI with highest absolute value
        dominant_key = max(normalized_kpi.keys(), key=lambda k: normalized_kpi[k])
        dominant_value = normalized_kpi[dominant_key]
        
        # Map to semantic category (English only)
        semantic_factor = "technical factor"
        for category, keys in self.kpi_categories.items():
            if dominant_key in keys:
                if category == 'momentum':
                    semantic_factor = "momentum"
                elif category == 'volatility':
                    semantic_factor = "volatility"
                elif category == 'sentiment':
                    semantic_factor = "sentiment"
                elif category == 'risk':
                    semantic_factor = "risk profile"
                elif category == 'technical':
                    semantic_factor = "technical analysis"
                elif category == 'fundamental':
                    semantic_factor = "fundamentals"
                elif category == 'strength':
                    semantic_factor = "relative strength"
                break
        
        return semantic_factor, dominant_value
    
    def _calculate_overall_intensity(self, signal_strengths: Dict[str, float]) -> float:
        """Calcola l'intensità complessiva dei segnali"""
        if not signal_strengths:
            return 0.0
        
        # Weighted average of signal strengths
        weights = {
            'momentum': 0.25,
            'risk': 0.25,
            'sentiment': 0.20,
            'technical': 0.15,
            'volatility': 0.10,
            'strength': 0.05
        }
        
        weighted_sum = 0
        total_weight = 0
        
        for category, strength in signal_strengths.items():
            weight = weights.get(category, 0.1)
            weighted_sum += strength * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _determine_sentiment_direction(self, normalized_kpi: Dict[str, float]) -> str:
        """Determina la direzione complessiva del sentiment"""
        positive_indicators = []
        negative_indicators = []
        
        for key, value in normalized_kpi.items():
            if 'momentum' in key or 'strength' in key or 'technical' in key:
                if value > 0.6:
                    positive_indicators.append(value)
                elif value < 0.4:
                    negative_indicators.append(value)
            elif 'risk' in key or 'volatility' in key:
                # These are inverted - high risk/volatility is negative
                if value < 0.4:
                    negative_indicators.append(1 - value)
                elif value > 0.6:
                    positive_indicators.append(value)
            elif 'sentiment' in key:
                if value > 0.6:
                    positive_indicators.append(value)
                elif value < 0.4:
                    negative_indicators.append(value)
        
        pos_strength = np.mean(positive_indicators) if positive_indicators else 0
        neg_strength = np.mean(negative_indicators) if negative_indicators else 0
        
        if pos_strength > neg_strength + 0.1:
            return "positive"
        elif neg_strength > pos_strength + 0.1:
            return "negative"
        else:
            return "neutral"
    
    def _calculate_confidence(self, normalized_kpi: Dict[str, float], signals: List[str]) -> float:
        """Calcola il livello di confidenza nell'analisi"""
        confidence_factors = []
        
        # Data availability
        if len(normalized_kpi) >= 5:
            confidence_factors.append(0.9)
        elif len(normalized_kpi) >= 3:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)
        
        # Signal consistency
        if len(signals) >= 3:
            confidence_factors.append(0.8)
        elif len(signals) >= 1:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.3)
        
        # Value range consistency
        values = list(normalized_kpi.values())
        if values:
            std_dev = np.std(values)
            if std_dev < 0.2:  # High consistency
                confidence_factors.append(0.9)
            elif std_dev < 0.4:  # Moderate consistency
                confidence_factors.append(0.7)
            else:  # Low consistency
                confidence_factors.append(0.5)
        
        return float(np.mean(confidence_factors))
    
    def _identify_patterns(self, normalized_kpi: Dict[str, float]) -> List[str]:
        """Identifica pattern specifici nei dati"""
        patterns = []
        
        for pattern_name, rule_func in self.pattern_rules.items():
            try:
                if rule_func(normalized_kpi):
                    # Convert pattern name to human readable
                    if pattern_name == 'bullish_momentum':
                        patterns.append("bullish trend in progress")
                    elif pattern_name == 'bearish_momentum':
                        patterns.append("bearish trend in progress")
                    elif pattern_name == 'high_volatility':
                        patterns.append("high volatility phase")
                    elif pattern_name == 'risk_elevation':
                        patterns.append("risk profile elevation")
                    elif pattern_name == 'sentiment_divergence':
                        patterns.append("divergence between sentiment and price action")
                    elif pattern_name == 'technical_breakout':
                        patterns.append("potential technical breakout")
            except Exception:
                continue
        
        return patterns
    
    def _identify_anomalies(self, normalized_kpi: Dict[str, float]) -> List[str]:
        """Identifica anomalie nei dati"""
        anomalies = []
        
        values = list(normalized_kpi.values())
        if not values:
            return anomalies
        
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        # Check for extreme values
        for key, value in normalized_kpi.items():
            if abs(value - mean_val) > 2 * std_val and std_val > 0.1:
                if value > mean_val:
                    anomalies.append(f"{key} significativamente elevato")
                else:
                    anomalies.append(f"{key} significativamente basso")
        
        return anomalies
    
    def _identify_missing_indicators(self, kpi: Dict[str, Any]) -> List[str]:
        """Identifica indicatori mancanti per completezza"""
        expected_indicators = [
            'momentum_score', 'technical_score', 'sentiment_score',
            'risk_score', 'volatility_score'
        ]
        
        missing = []
        for indicator in expected_indicators:
            if indicator not in kpi or kpi[indicator] is None:
                missing.append(indicator)
        
        return missing
    
    # Pattern recognition rule functions
    def _check_bullish_momentum(self, kpi: Dict[str, float]) -> bool:
        """Check for bullish momentum pattern"""
        momentum_keys = ['momentum_z', 'momentum_score', 'trend_strength']
        momentum_values = [kpi.get(k, 0) for k in momentum_keys if k in kpi]
        return len(momentum_values) > 0 and np.mean(momentum_values) > 0.7
    
    def _check_bearish_momentum(self, kpi: Dict[str, float]) -> bool:
        """Check for bearish momentum pattern"""
        momentum_keys = ['momentum_z', 'momentum_score', 'trend_strength']
        momentum_values = [kpi.get(k, 0) for k in momentum_keys if k in kpi]
        return len(momentum_values) > 0 and np.mean(momentum_values) < 0.3
    
    def _check_high_volatility(self, kpi: Dict[str, float]) -> bool:
        """Check for high volatility pattern"""
        vol_keys = ['vola_z', 'volatility_risk', 'volatility_score']
        vol_values = [kpi.get(k, 0) for k in vol_keys if k in kpi]
        # For volatility, low normalized values indicate high volatility (inverted)
        return len(vol_values) > 0 and np.mean(vol_values) < 0.4
    
    def _check_risk_elevation(self, kpi: Dict[str, float]) -> bool:
        """Check for elevated risk pattern"""
        risk_keys = ['risk_score', 'overall_risk', 'market_risk']
        risk_values = [kpi.get(k, 0) for k in risk_keys if k in kpi]
        return len(risk_values) > 0 and np.mean(risk_values) < 0.3  # Low normalized = high risk
    
    def _check_sentiment_divergence(self, kpi: Dict[str, float]) -> bool:
        """Check for sentiment-price divergence"""
        sentiment = kpi.get('sentiment_z', 0.5)
        momentum = kpi.get('momentum_z', 0.5)
        return abs(sentiment - momentum) > 0.4
    
    def _check_technical_breakout(self, kpi: Dict[str, float]) -> bool:
        """Check for technical breakout pattern"""
        technical = kpi.get('technical_score', 0.5)
        momentum = kpi.get('momentum_score', 0.5)
        return technical > 0.8 and momentum > 0.7
    
    def _create_empty_result(self, entity_id: str, reason: str) -> AnalysisResult:
        """Crea risultato vuoto per dati mancanti"""
        return AnalysisResult(
            entity_id=entity_id,
            timestamp=datetime.now(),
            signals=["no relevant signals"],
            signal_strengths={},
            dominant_factor="no factor",
            dominant_strength=0.0,
            overall_intensity=0.0,
            sentiment_direction="neutral",
            confidence_level=0.0,
            patterns=[],
            anomalies=[],
            kpi_count=0,
            missing_indicators=[reason]
        )
    
    def _create_error_result(self, entity_id: str, error_msg: str) -> AnalysisResult:
        """Crea risultato di errore"""
        return AnalysisResult(
            entity_id=entity_id,
            timestamp=datetime.now(),
            signals=[f"errore analisi: {error_msg}"],
            signal_strengths={},
            dominant_factor="errore",
            dominant_strength=0.0,
            overall_intensity=0.0,
            sentiment_direction="neutral",
            confidence_level=0.0,
            patterns=[],
            anomalies=[error_msg],
            kpi_count=0,
            missing_indicators=[]
        )
    
    # Domain-aware methods for explainability provider integration
    
    def _normalize_metrics(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Normalizza le metriche in valori 0-1 per analisi uniforme (domain-agnostic)"""
        return self._normalize_kpi(metrics)  # Reuse existing logic
    
    def _identify_signals_domain_aware(self, normalized_metrics: Dict[str, float], 
                                      signal_descriptions: Dict[str, str]) -> Tuple[List[str], Dict[str, float]]:
        """Identifica segnali significativi usando descrizioni domain-specific"""
        signals = []
        strengths = {}
        
        # Create dynamic categories from factor mappings (reverse lookup)
        category_to_keys = {}
        for metric_key in normalized_metrics.keys():
            # Try to find category for this metric (this is simplified - in practice
            # the provider would give us category groupings)
            category = "technical"  # Default fallback
            for cat_name in signal_descriptions.keys():
                if cat_name.lower() in metric_key.lower():
                    category = cat_name
                    break
            
            if category not in category_to_keys:
                category_to_keys[category] = []
            category_to_keys[category].append(metric_key)
        
        # Analyze each category
        for category, metric_keys in category_to_keys.items():
            category_values = [normalized_metrics[key] for key in metric_keys if key in normalized_metrics]
            
            if not category_values:
                continue
                
            # Calculate category strength
            avg_strength = np.mean(category_values)
            max_strength = max(category_values)
            
            # Determine signal intensity
            if max_strength >= self.signal_thresholds['strong']:
                intensity = 'strong'
                signal_strength = max_strength
            elif max_strength >= self.signal_thresholds['moderate']:
                intensity = 'moderate'
                signal_strength = avg_strength
            elif max_strength >= self.signal_thresholds['weak']:
                intensity = 'weak'
                signal_strength = avg_strength
            else:
                continue
            
            # Create semantic signal description using domain descriptions
            category_desc = signal_descriptions.get(category, f"{category} indicators")
            
            if avg_strength > 0.6:
                signals.append(f"{intensity} positive {category_desc}")
            elif avg_strength < 0.4:
                signals.append(f"{intensity} negative {category_desc}")
            else:
                signals.append(f"{intensity} neutral {category_desc}")
            
            strengths[category] = signal_strength
        
        return signals, strengths
    
    def _find_dominant_factor_domain_aware(self, normalized_metrics: Dict[str, float], 
                                          factor_categories: Dict[str, str]) -> Tuple[str, float]:
        """Identifica il fattore dominante usando categorie domain-specific"""
        if not normalized_metrics:
            return "no factor", 0.0
        
        # Find metric with highest absolute value
        dominant_key = max(normalized_metrics.keys(), key=lambda k: normalized_metrics[k])
        dominant_value = normalized_metrics[dominant_key]
        
        # Map to semantic category using domain provider
        semantic_factor = factor_categories.get(dominant_key, "technical factor")
        
        return semantic_factor, dominant_value


# Convenience function for standalone usage
def analyze_kpi(entity_id: str, kpi: Dict[str, Any]) -> AnalysisResult:
    """
    Convenience function per analisi KPI standalone
    
    Args:
        entity_id: Entity identifier (domain-agnostic)
        kpi: Dictionary con KPI da analizzare
        
    Returns:
        AnalysisResult con analisi completa
    """
    from vitruvyan_core.domains.finance_explainability_provider import FinanceExplainabilityProvider
    
    analyzer = VEEAnalyzer()
    provider = FinanceExplainabilityProvider()
    return analyzer.analyze_metrics(entity_id, kpi, provider)


if __name__ == "__main__":
    # Test standalone
    test_kpi = {
        'momentum_z': 0.8,
        'vola_z': -0.5,
        'sentiment_z': 0.3,
        'technical_score': 65,
        'risk_score': 45,
        'composite_score': 70
    }
    
    result = analyze_kpi("EXAMPLE_ENTITY_1", test_kpi)
    
    print(f"=== VEE Analyzer Test Results for {result.entity_id} ===")
    print(f"Signals: {', '.join(result.signals)}")
    print(f"Dominant Factor: {result.dominant_factor} (strength: {result.dominant_strength:.2f})")
    print(f"Overall Intensity: {result.overall_intensity:.2f}")
    print(f"Sentiment Direction: {result.sentiment_direction}")
    print(f"Confidence: {result.confidence_level:.2f}")
    print(f"Patterns: {', '.join(result.patterns)}")
    if result.anomalies:
        print(f"Anomalies: {', '.join(result.anomalies)}")