# core/algorithms/orchestrator.py
"""
🎼 Vitruvyan Core Algorithms Orchestrator

Sistema di orchestrazione per i 4 moduli Core Algorithms:
- VEE: Explainability Engine (già esistente)
- VHSW: Historical Strength Window  
- VARE: Adaptive Risk Engine
- VMFL: Multi-Factor Learning

Fornisce interfacce unificate e composizione avanzata.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from dataclasses import dataclass

# Import existing VEE
from core.cognitive.vee_engine import explain_entity

# Import new engines
from .vhsw_engine import VHSWEngine, VHSWResult
from .vare_engine import VAREEngine, VAREResult  
from .vmfl_engine import VMFLEngine, VMFLResult


@dataclass
class ComprehensiveAnalysis:
    """Risultato completo dell'analisi Vitruvyan Core"""
    entity_id: str
    timestamp: datetime
    
    # Individual engine results
    explainability: Dict[str, str]  # VEE results
    historical_strength: VHSWResult  # VHSW results
    risk_profile: VAREResult         # VARE results
    multi_factor: VMFLResult         # VMFL results
    
    # Composite insights
    overall_score: float             # 0-100 composite score
    recommendation_category: str     # "AVOID", "CAUTION", "NEUTRAL", "INTEREST", "STRONG_INTEREST"
    
    # Key insights
    strengths: List[str]
    weaknesses: List[str]
    key_factors: List[str]
    
    # Confidence metrics
    analysis_confidence: float
    data_quality: str


class VitruvyanCoreOrchestrator:
    """
    Orchestratore principale per i Vitruvyan Core Algorithms
    
    Combina tutti e 4 i moduli per analisi comprehensive:
    - Coordina l'esecuzione sequenziale o parallela
    - Genera insights compositi
    - Fornisce spiegazioni unificate
    """
    
    def __init__(self):
        self.vhsw_engine = VHSWEngine()
        self.vare_engine = VAREEngine()
        self.vmfl_engine = VMFLEngine()
        
        # Composite scoring weights
        self.composite_weights = {
            'historical_strength': 0.25,
            'risk_adjustment': 0.30,  # Higher weight for risk
            'multi_factor': 0.35,
            'explainability_bonus': 0.10
        }
    
    def analyze_comprehensive(self, entity_id: str, 
                            config: Optional[Dict] = None) -> ComprehensiveAnalysis:
        """
        Esegue analisi comprehensive con tutti i 4 motori
        
        Args:
            entity_id: Symbol del entity_id da analizzare
            config: Configurazione personalizzata per i motori
            
        Returns:
            ComprehensiveAnalysis con tutti i risultati combinati
        """
        try:
            print(f"\n🎼 [ORCHESTRATOR] Avvio analisi comprehensive per {entity_id}")
            
            config = config or {}
            
            # Execute all engines
            print("📊 Esecuzione motori di analisi...")
            
            # 1. VEE - Explainability (mock KPI data for demo)
            kpi_data = {'price': 'current_market_price', 'analysis': 'in_progress'}
            explainability = explain_entity(entity_id, kpi_data)
            
            # 2. VHSW - Historical Strength
            vhsw_config = config.get('vhsw', {})
            historical_strength = self.vhsw_engine.analyze_entity(entity_id, vhsw_config.get('windows'))
            
            # 3. VARE - Risk Engine  
            vare_config = config.get('vare', {})
            risk_profile = self.vare_engine.analyze_entity(entity_id, vare_config.get('benchmark'))
            
            # 4. VMFL - Multi-Factor Learning
            vmfl_config = config.get('vmfl', {})
            multi_factor = self.vmfl_engine.analyze_entity(
                entity_id, 
                vmfl_config.get('weights'),
                vmfl_config.get('fundamental_data')
            )
            
            # Generate composite analysis
            print("🔗 Combinazione risultati...")
            composite_analysis = self._generate_composite_analysis(
                entity_id, explainability, historical_strength, risk_profile, multi_factor
            )
            
            print(f"✅ [ORCHESTRATOR] Analisi comprehensive completata per {entity_id}")
            return composite_analysis
            
        except Exception as e:
            print(f"❌ [ORCHESTRATOR] Errore nell'analisi di {entity_id}: {e}")
            return self._create_error_analysis(entity_id, str(e))
    
    async def analyze_comprehensive_async(self, entity_id: str, 
                                        config: Optional[Dict] = None) -> ComprehensiveAnalysis:
        """Versione asincrona dell'analisi comprehensive"""
        # For now, just call sync version
        # In future, could parallelize engine calls
        return self.analyze_comprehensive(entity_id, config)
    
    def analyze_batch(self, entity_ids: List[str], 
                     config: Optional[Dict] = None) -> Dict[str, ComprehensiveAnalysis]:
        """
        Analizza un batch di entity_id
        
        Args:
            entity_ids: Lista di entity_id symbols
            config: Configurazione condivisa
            
        Returns:
            Dict mapping entity_id -> ComprehensiveAnalysis
        """
        results = {}
        
        print(f"\n🎼 [ORCHESTRATOR] Avvio analisi batch per {len(entity_ids)} entity_ids")
        
        for i, entity_id in enumerate(entity_ids, 1):
            print(f"📈 [{i}/{len(entity_ids)}] Analisi {entity_id}...")
            try:
                results[entity_id] = self.analyze_comprehensive(entity_id, config)
            except Exception as e:
                print(f"❌ Errore per {entity_id}: {e}")
                results[entity_id] = self._create_error_analysis(entity_id, str(e))
        
        print(f"✅ [ORCHESTRATOR] Completata analisi batch: {len(results)} risultati")
        return results
    
    def _generate_composite_analysis(self, entity_id: str, explainability: Dict,
                                   historical_strength: VHSWResult,
                                   risk_profile: VAREResult,
                                   multi_factor: VMFLResult) -> ComprehensiveAnalysis:
        """Genera analisi composita combinando tutti i risultati"""
        
        # Calculate composite score
        overall_score = self._calculate_composite_score(
            historical_strength, risk_profile, multi_factor
        )
        
        # Determine recommendation category
        recommendation_category = self._determine_recommendation_category(
            overall_score, risk_profile.overall_risk, multi_factor.composite_score
        )
        
        # Extract strengths and weaknesses
        strengths, weaknesses = self._extract_strengths_weaknesses(
            historical_strength, risk_profile, multi_factor
        )
        
        # Identify key factors
        key_factors = self._identify_key_factors(
            historical_strength, risk_profile, multi_factor
        )
        
        # Calculate analysis confidence
        analysis_confidence = self._calculate_analysis_confidence(
            historical_strength, risk_profile, multi_factor
        )
        
        # Determine data quality
        data_quality = self._assess_data_quality(analysis_confidence)
        
        return ComprehensiveAnalysis(
            entity_id=entity_id,
            timestamp=datetime.now(),
            explainability=explainability,
            historical_strength=historical_strength,
            risk_profile=risk_profile,
            multi_factor=multi_factor,
            overall_score=overall_score,
            recommendation_category=recommendation_category,
            strengths=strengths,
            weaknesses=weaknesses,
            key_factors=key_factors,
            analysis_confidence=analysis_confidence,
            data_quality=data_quality
        )
    
    def _calculate_composite_score(self, vhsw: VHSWResult, vare: VAREResult, vmfl: VMFLResult) -> float:
        """Calcola punteggio composito ponderato"""
        
        # Normalize VHSW momentum to 0-100 scale
        vhsw_normalized = (vhsw.momentum_score + vhsw.stability_score + vhsw.trend_strength) / 3
        
        # Risk adjustment (invert risk score - higher risk = lower score)  
        risk_adjusted = 100 - vare.overall_risk
        
        # VMFL composite score (already 0-100)
        vmfl_score = vmfl.composite_score
        
        # Explainability bonus (based on confidence levels)
        explainability_bonus = (vhsw.confidence + vare.confidence + vmfl.confidence) * 100 / 3
        
        # Calculate weighted composite
        composite = (
            vhsw_normalized * self.composite_weights['historical_strength'] +
            risk_adjusted * self.composite_weights['risk_adjustment'] +
            vmfl_score * self.composite_weights['multi_factor'] +
            explainability_bonus * self.composite_weights['explainability_bonus']
        )
        
        return float(min(100, max(0, composite)))
    
    def _determine_recommendation_category(self, composite_score: float, 
                                         risk_score: float, factor_score: float) -> str:
        """Determina categoria di raccomandazione basata su score multipli"""
        
        # High risk override
        if risk_score > 80:
            return "AVOID"
        
        # Score-based categorization with risk adjustment
        if composite_score >= 75 and risk_score < 60:
            return "STRONG_INTEREST"
        elif composite_score >= 60 and risk_score < 70:
            return "INTEREST"
        elif composite_score >= 40 and risk_score < 80:
            return "NEUTRAL"
        elif composite_score >= 25:
            return "CAUTION"
        else:
            return "AVOID"
    
    def _extract_strengths_weaknesses(self, vhsw: VHSWResult, vare: VAREResult, 
                                    vmfl: VMFLResult) -> tuple[List[str], List[str]]:
        """Estrae punti di forza e debolezza"""
        strengths = []
        weaknesses = []
        
        # VHSW strengths/weaknesses
        if vhsw.momentum_score > 70:
            strengths.append(f"Forte momentum storico ({vhsw.momentum_score:.0f}/100)")
        elif vhsw.momentum_score < 30:
            weaknesses.append(f"Momentum storico debole ({vhsw.momentum_score:.0f}/100)")
        
        if vhsw.stability_score > 70:
            strengths.append(f"Alta stabilità ({vhsw.stability_score:.0f}/100)")
        elif vhsw.stability_score < 30:
            weaknesses.append(f"Bassa stabilità ({vhsw.stability_score:.0f}/100)")
        
        # VARE strengths/weaknesses  
        if vare.overall_risk < 30:
            strengths.append(f"Basso profilo di rischio ({vare.risk_category})")
        elif vare.overall_risk > 70:
            weaknesses.append(f"Alto profilo di rischio ({vare.risk_category})")
        
        if vare.liquidity_risk < 30:
            strengths.append("Buona liquidità")
        elif vare.liquidity_risk > 70:
            weaknesses.append("Liquidità limitata")
        
        # VMFL strengths/weaknesses
        if vmfl.technical_score > 70:
            strengths.append("Indicatori tecnici favorevoli")
        elif vmfl.technical_score < 30:
            weaknesses.append("Indicatori tecnici sfavorevoli")
        
        if vmfl.momentum_score > 70:
            strengths.append("Momentum positivo")
        elif vmfl.momentum_score < 30:
            weaknesses.append("Momentum negativo")
        
        return strengths, weaknesses
    
    def _identify_key_factors(self, vhsw: VHSWResult, vare: VAREResult, vmfl: VMFLResult) -> List[str]:
        """Identifica i fattori chiave dell'analisi"""
        factors = []
        
        # Most influential factor scores
        factor_scores = {
            'Momentum Storico': vhsw.momentum_score,
            'Stabilità': vhsw.stability_score,
            'Rischio Mercato': 100 - vare.market_risk,  # Invert for clarity
            'Rischio Volatilità': 100 - vare.volatility_risk,
            'Analisi Tecnica': vmfl.technical_score,
            'Multi-Factor Score': vmfl.composite_score
        }
        
        # Sort by impact (highest and lowest)
        sorted_factors = sorted(factor_scores.items(), key=lambda x: abs(x[1] - 50), reverse=True)
        
        # Take top 3 most impactful factors
        for factor_name, score in sorted_factors[:3]:
            if score > 60:
                factors.append(f"{factor_name}: Positivo ({score:.0f})")
            elif score < 40:
                factors.append(f"{factor_name}: Negativo ({score:.0f})")
            else:
                factors.append(f"{factor_name}: Neutrale ({score:.0f})")
        
        # Add pattern insights from VMFL
        if vmfl.pattern_signals:
            factors.extend(vmfl.pattern_signals[:2])  # Top 2 patterns
        
        return factors
    
    def _calculate_analysis_confidence(self, vhsw: VHSWResult, vare: VAREResult, vmfl: VMFLResult) -> float:
        """Calcola confidenza complessiva dell'analisi"""
        confidences = [vhsw.confidence, vare.confidence, vmfl.confidence]
        return float(sum(confidences) / len(confidences))
    
    def _assess_data_quality(self, confidence: float) -> str:
        """Valuta qualità dei dati basata sulla confidenza"""
        if confidence >= 0.8:
            return "EXCELLENT"
        elif confidence >= 0.6:
            return "GOOD"
        elif confidence >= 0.4:
            return "FAIR"
        else:
            return "LIMITED"
    
    def _create_error_analysis(self, entity_id: str, error_msg: str) -> ComprehensiveAnalysis:
        """Crea analisi di errore"""
        from .vhsw_engine import VHSWEngine
        from .vare_engine import VAREEngine
        from .vmfl_engine import VMFLEngine
        
        error_vhsw = VHSWEngine()._create_error_result(entity_id, error_msg)
        error_vare = VAREEngine()._create_error_result(entity_id, error_msg)
        error_vmfl = VMFLEngine()._create_error_result(entity_id, error_msg)
        
        return ComprehensiveAnalysis(
            entity_id=entity_id,
            timestamp=datetime.now(),
            explainability={'summary': f'Errore: {error_msg}', 'technical': '', 'detailed': ''},
            historical_strength=error_vhsw,
            risk_profile=error_vare,
            multi_factor=error_vmfl,
            overall_score=0,
            recommendation_category="AVOID",
            strengths=[],
            weaknesses=[f"Errore nell'analisi: {error_msg}"],
            key_factors=[],
            analysis_confidence=0.0,
            data_quality="ERROR"
        )


# LangGraph Node Integration
def vitruvyan_core_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo LangGraph per l'orchestratore Vitruvyan Core
    
    Input state keys:
    - entity_ids: List[str] - entity_id symbols to analyze
    - core_config: Dict (optional) - configuration for all engines
    
    Output state keys:
    - vitruvyan_core_results: Dict[str, ComprehensiveAnalysis] - comprehensive results
    """
    print(f"\n🎼 [VITRUVYAN_CORE] Avvio analisi comprehensive")
    
    entity_ids = state.get('entity_ids', [])
    config = state.get('core_config', {})
    
    if not entity_ids:
        print("⚠️ Nessun entity_id nello stato → skip Vitruvyan Core")
        return state
    
    orchestrator = VitruvyanCoreOrchestrator()
    
    if len(entity_ids) == 1:
        # Single entity_id analysis
        entity_id = entity_ids[0]
        print(f"🎼 Analisi comprehensive per {entity_id}...")
        result = orchestrator.analyze_comprehensive(entity_id, config)
        results = {entity_id: result}
    else:
        # Batch analysis
        print(f"🎼 Analisi batch per {len(entity_ids)} entity_ids...")
        results = orchestrator.analyze_batch(entity_ids, config)
    
    # Update state
    state['vitruvyan_core_results'] = results
    
    # Summary logging
    for entity_id, result in results.items():
        print(f"✅ {entity_id}: {result.recommendation_category} "
              f"(score: {result.overall_score:.0f}/100, "
              f"confidence: {result.analysis_confidence:.2f})")
    
    print(f"🎼 [VITRUVYAN_CORE] Completata analisi per {len(results)} entity_ids\n")
    return state


if __name__ == "__main__":
    # Test comprehensive analysis
    orchestrator = VitruvyanCoreOrchestrator()
    
    print("=== Testing Vitruvyan Core Orchestrator ===")
    result = orchestrator.analyze_comprehensive("EXAMPLE_ENTITY_1")
    
    print(f"\n🎯 Comprehensive Analysis for {result.entity_id}")
    print(f"Overall Score: {result.overall_score:.1f}/100")
    print(f"Recommendation: {result.recommendation_category}")
    print(f"Analysis Confidence: {result.analysis_confidence:.2f}")
    print(f"Data Quality: {result.data_quality}")
    
    print(f"\n💪 Strengths:")
    for strength in result.strengths:
        print(f"  • {strength}")
    
    print(f"\n⚠️ Weaknesses:")
    for weakness in result.weaknesses:
        print(f"  • {weakness}")
    
    print(f"\n🔑 Key Factors:")
    for factor in result.key_factors:
        print(f"  • {factor}")
    
    print(f"\n📊 Individual Engine Scores:")
    print(f"  Historical Strength: {result.historical_strength.momentum_score:.0f}/100")
    print(f"  Risk Profile: {100-result.risk_profile.overall_risk:.0f}/100 (risk-adjusted)")
    print(f"  Multi-Factor: {result.multi_factor.composite_score:.0f}/100")