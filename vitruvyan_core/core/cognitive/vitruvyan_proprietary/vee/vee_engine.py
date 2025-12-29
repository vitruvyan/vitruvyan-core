# core/logic/vitruvyan_proprietary/vee/vee_engine.py
"""
🧠 VEE Engine 2.0 - Vitruvyan Explainability Engine

Orchestratore principale del sistema di explainability multilivello.
Integra analisi, generazione, memoria e fallback CrewAI in un flusso coerente.

Evoluzione completa del VEE originale:
- Analisi avanzata dei KPI (vee_analyzer)
- Generazione spiegazioni multilivello (vee_generator)  
- Memoria storica e consistency (vee_memory_adapter)
- Fallback robusto per CrewAI
- Persistenza automatica delle spiegazioni

Principi VEE 2.0:
- Explainability: Ogni output completamente tracciabile
- Safety: Nessuna raccomandazione di investimento
- Composability: Integrazione seamless con LangGraph
- Reliability: Fallback multipli per robustezza
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import os

from .vee_analyzer import VEEAnalyzer, AnalysisResult, analyze_kpi
from .vee_generator import VEEGenerator, ExplanationLevels, generate_explanation
from .vee_memory_adapter import VEEMemoryAdapter, HistoricalExplanation

# PR-C: VSGS metrics and audit logging (optional)
try:
    from core.monitoring.vsgs_metrics import record_vee_generation
except ImportError:
    def record_vee_generation(*args, **kwargs):
        pass  # Stub if monitoring not available

# from core.cognitive.neural_engine.schemas import StrategyProfile, TickerScore  # TODO: Fix deprecated import
# from core.cognitive.vitruvyan_proprietary.vee.vee_layers import VEELayer  # TODO: Module not found
# from core.cognitive.vitruvyan_proprietary.vee.vee_narrative import VEENarrative  # TODO: Module not found
# from core.cognitive.vitruvyan_proprietary.vee.vee_memory import VEEMemory  # TODO: Module not found
# from core.logging.audit import audit  # TODO: Fix deprecated import

# Type aliases for missing imports
StrategyProfile = Dict[str, Any]
TickerScore = Dict[str, Any]

# Soft-import CrewAI fallback
try:
    from core.agents.explainability_agent import explain_with_motley_style
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    def explain_with_motley_style(ticker: str, kpi: dict, profile: dict = None) -> dict:
        return {
            "summary": f"Spiegazione semplificata per {ticker}.",
            "technical": f"KPI disponibili: {list(kpi.keys()) if isinstance(kpi, dict) else 'N/A'}",
            "detailed": "Explainability completa non disponibile in questo container (crew non caricato)."
        }


class VEEEngine:
    """
    Vitruvyan Explainability Engine 2.0
    
    Orchestratore principale che coordina:
    1. Analisi KPI e pattern recognition
    2. Generazione spiegazioni multilivello
    3. Integrazione memoria storica
    4. Fallback CrewAI per robustezza
    5. Persistenza automatica
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize sub-engines
        self.analyzer = VEEAnalyzer()
        self.generator = VEEGenerator()
        self.memory = VEEMemoryAdapter()
        
        # Configuration
        self.auto_store = True  # Automatically store explanations
        self.use_memory_context = True  # Enrich with historical context
        self.fallback_to_crewai = True  # Use CrewAI as fallback
        
        self.logger.info("VEE Engine 2.0 initialized")
    
    def explain_ticker(self, ticker: str, kpi: Dict[str, Any], 
                      profile: Optional[Dict[str, Any]] = None,
                      semantic_context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, str]:
        """
        Entry point principale per explainability multilivello
        
        Args:
            ticker: Symbol del ticker da spiegare
            kpi: KPI e metriche da analizzare
            profile: Profilo utente per personalizzazione
            semantic_context: VSGS semantic matches (PR-C) from grounding_node
            
        Returns:
            Dict con spiegazioni multilivello compatibile con sistema esistente
        """
        try:
            self.logger.info(f"Starting VEE 2.0 explanation for {ticker}")
            
            # Phase 1: Analyze KPI and identify patterns
            analysis = self.analyzer.analyze_kpi(ticker, kpi)
            self.logger.debug(f"Analysis completed for {ticker}: {len(analysis.signals)} signals identified")
            
            # Phase 2: Generate explanations (PR-C: pass semantic_context)
            explanations = self.generator.generate_explanation(analysis, profile, semantic_context)
            self.logger.debug(f"Explanations generated for {ticker} in {explanations.language}")
            
            # PR-C: Record VEE generation metrics + audit logging
            layers_generated = ["summary", "technical", "detailed"]
            if explanations.semantic_grounded:
                layers_generated.append("semantic_grounded")
            if explanations.epistemic_trace:
                layers_generated.append("epistemic_trace")
            
            # Record Prometheus metric
            user_id = profile.get("user_id", "unknown") if profile else "unknown"
            record_vee_generation(
                ticker=ticker,
                layers=len(layers_generated),
                semantic_grounding=bool(semantic_context),
                user_id=user_id
            )
            
            # Audit log (disabled - TODO: Fix audit import)
            trace_id = profile.get("trace_id", os.urandom(8).hex()) if profile else os.urandom(8).hex()
            # audit(
            #     agent="vee_generation",
            #     payload={
            #         "ticker": ticker,
            #         "layers": layers_generated,
            #         "semantic_grounding": bool(semantic_context),
            #         "semantic_matches": len(semantic_context) if semantic_context else 0,
            #         "kpi_count": analysis.kpi_count if hasattr(analysis, 'kpi_count') else 0
            #     },
            #     trace_id=trace_id,
            #     user_id=user_id
            # )
            
            # Phase 3: Enrich with historical context (if enabled)
            if self.use_memory_context:
                try:
                    historical = self.memory.retrieve_similar_explanations(
                        ticker, analysis, explanations.language
                    )
                    if historical:
                        explanations = self.memory.enrich_with_context(explanations, historical)
                        self.logger.debug(f"Enriched with {len(historical)} historical references")
                except Exception as e:
                    self.logger.warning(f"Memory context enrichment failed for {ticker}: {e}")
            
            # Phase 4: Store explanation (if enabled)
            if self.auto_store:
                try:
                    stored = self.memory.store_explanation(analysis, explanations)
                    if stored:
                        self.logger.debug(f"Explanation stored for {ticker}")
                    else:
                        self.logger.warning(f"Failed to store explanation for {ticker}")
                except Exception as e:
                    self.logger.warning(f"Storage failed for {ticker}: {e}")
            
            # Phase 5: Format output for compatibility
            result = self._format_for_compatibility(explanations)
            
            self.logger.info(f"VEE 2.0 explanation completed for {ticker}")
            return result
            
        except Exception as e:
            self.logger.error(f"VEE 2.0 failed for {ticker}: {e}")
            return self._fallback_explanation(ticker, kpi, profile, str(e))
    
    def explain_comprehensive(self, ticker: str, kpi: Dict[str, Any],
                            profile: Optional[Dict[str, Any]] = None,
                            semantic_context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Spiegazione comprehensive con tutti i dettagli VEE 2.0
        
        Args:
            ticker: Symbol del ticker
            kpi: KPI da analizzare
            profile: Profilo utente
            semantic_context: VSGS semantic matches (PR-C)
            
        Returns:
            Dict completo con analisi, spiegazioni, e metadata
        """
        try:
            # Full VEE 2.0 pipeline
            analysis = self.analyzer.analyze_kpi(ticker, kpi)
            explanations = self.generator.generate_explanation(analysis, profile, semantic_context)
            
            # Get historical context
            historical = []
            if self.use_memory_context:
                try:
                    historical = self.memory.retrieve_similar_explanations(
                        ticker, analysis, explanations.language
                    )
                    explanations = self.memory.enrich_with_context(explanations, historical)
                except Exception as e:
                    self.logger.warning(f"Historical context failed: {e}")
            
            # Store if enabled
            if self.auto_store:
                try:
                    self.memory.store_explanation(analysis, explanations)
                except Exception as e:
                    self.logger.warning(f"Storage failed: {e}")
            
            # Return comprehensive result
            return {
                # Standard compatibility format
                "summary": explanations.summary,
                "technical": explanations.technical,
                "detailed": explanations.detailed,
                
                # VEE 2.0 extended information
                "vee_analysis": {
                    "signals": analysis.signals,
                    "dominant_factor": analysis.dominant_factor,
                    "sentiment_direction": analysis.sentiment_direction,
                    "confidence_level": analysis.confidence_level,
                    "overall_intensity": analysis.overall_intensity,
                    "patterns": analysis.patterns,
                    "anomalies": analysis.anomalies
                },
                
                "vee_metadata": {
                    "language": explanations.language,
                    "profile_adapted": explanations.profile_adapted,
                    "confidence_note": explanations.confidence_note,
                    "timestamp": explanations.timestamp.isoformat(),
                    "historical_count": len(historical),
                    "contextualized": explanations.contextualized is not None
                },
                
                "vee_context": {
                    "contextualized_text": explanations.contextualized,
                    "historical_reference": explanations.historical_reference,
                    "kpi_coverage": analysis.kpi_count,
                    "missing_indicators": analysis.missing_indicators
                }
            }
            
        except Exception as e:
            self.logger.error(f"Comprehensive explanation failed for {ticker}: {e}")
            return self._fallback_comprehensive(ticker, kpi, profile, str(e))
    
    def get_explanation_insights(self, ticker: str, days: int = 30) -> Dict[str, Any]:
        """
        Ottieni insights dalle spiegazioni storiche
        
        Args:
            ticker: Symbol del ticker
            days: Giorni da analizzare
            
        Returns:
            Dict con trend e statistiche
        """
        try:
            trends = self.memory.get_explanation_trends(ticker, days)
            return trends
        except Exception as e:
            self.logger.error(f"Failed to get insights for {ticker}: {e}")
            return {}
    
    def analyze_kpi_only(self, ticker: str, kpi: Dict[str, Any]) -> AnalysisResult:
        """
        Solo analisi KPI senza generazione spiegazioni
        
        Args:
            ticker: Symbol del ticker
            kpi: KPI da analizzare
            
        Returns:
            AnalysisResult con pattern e segnali
        """
        return self.analyzer.analyze_kpi(ticker, kpi)
    
    def generate_explanation_only(self, analysis: AnalysisResult,
                                profile: Optional[Dict[str, Any]] = None,
                                semantic_context: Optional[List[Dict[str, Any]]] = None) -> ExplanationLevels:
        """
        Solo generazione spiegazioni da analisi esistente
        
        Args:
            analysis: AnalysisResult dall'analyzer
            profile: Profilo utente
            semantic_context: VSGS semantic matches (PR-C)
            
        Returns:
            ExplanationLevels con spiegazioni multilivello
        """
        return self.generator.generate_explanation(analysis, profile, semantic_context)
    
    def _format_for_compatibility(self, explanations: ExplanationLevels) -> Dict[str, str]:
        """Formatta output per compatibilità con sistema esistente (PR-C: include semantic grounding)"""
        result = {
            "summary": explanations.summary,
            "technical": explanations.technical,
            "detailed": explanations.detailed
        }
        
        # Add contextualized info if available
        if explanations.contextualized:
            result["contextualized"] = explanations.contextualized
        
        # PR-C: Add VSGS semantic grounding layers
        if explanations.semantic_grounded:
            result["semantic_grounded"] = explanations.semantic_grounded
        
        if explanations.epistemic_trace:
            result["epistemic_trace"] = ", ".join(explanations.epistemic_trace)
        
        return result
    
    def _fallback_explanation(self, ticker: str, kpi: Dict[str, Any],
                            profile: Optional[Dict[str, Any]], error: str) -> Dict[str, str]:
        """Fallback usando CrewAI o spiegazione di errore"""
        self.logger.warning(f"Using fallback explanation for {ticker}: {error}")
        
        # Try CrewAI fallback if available and enabled
        if self.fallback_to_crewai and CREWAI_AVAILABLE:
            try:
                return explain_with_motley_style(ticker, kpi, profile)
            except Exception as crewai_error:
                self.logger.error(f"CrewAI fallback also failed for {ticker}: {crewai_error}")
        
        # Final fallback - deterministic error explanation
        language = 'en' if profile and profile.get('lang') == 'en' else 'it'
        
        if language == 'it':
            return {
                "summary": f"Analisi di {ticker} non disponibile a causa di errore tecnico.",
                "technical": f"Errore nel processamento dei KPI: {error}",
                "detailed": f"Il sistema VEE 2.0 ha riscontrato un errore durante l'analisi di {ticker}. "
                           f"Dettagli tecnici: {error}. Si raccomanda di riprovare più tardi o "
                           f"verificare la qualità dei dati di input."
            }
        else:
            return {
                "summary": f"Analysis of {ticker} unavailable due to technical error.",
                "technical": f"Error processing KPIs: {error}",
                "detailed": f"VEE 2.0 system encountered an error during {ticker} analysis. "
                           f"Technical details: {error}. Please retry later or "
                           f"verify input data quality."
            }
    
    def _fallback_comprehensive(self, ticker: str, kpi: Dict[str, Any],
                               profile: Optional[Dict[str, Any]], error: str) -> Dict[str, Any]:
        """Fallback comprehensive con struttura completa"""
        basic_fallback = self._fallback_explanation(ticker, kpi, profile, error)
        
        return {
            "summary": basic_fallback["summary"],
            "technical": basic_fallback["technical"],
            "detailed": basic_fallback["detailed"],
            
            "vee_analysis": {
                "signals": ["errore di sistema"],
                "dominant_factor": "errore tecnico",
                "sentiment_direction": "neutral",
                "confidence_level": 0.0,
                "overall_intensity": 0.0,
                "patterns": [],
                "anomalies": [error]
            },
            
            "vee_metadata": {
                "language": 'en' if profile and profile.get('lang') == 'en' else 'it',
                "profile_adapted": False,
                "confidence_note": "Analisi non disponibile per errore tecnico",
                "timestamp": datetime.now().isoformat(),
                "historical_count": 0,
                "contextualized": False
            },
            
            "vee_context": {
                "contextualized_text": None,
                "historical_reference": None,
                "kpi_coverage": 0,
                "missing_indicators": ["sistema non disponibile"]
            }
        }


# Compatibility function with original interface
def explain_ticker(ticker: str, kpi: Dict[str, Any], 
                  profile: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Funzione di compatibilità con l'interfaccia VEE originale
    
    Args:
        ticker: Symbol del ticker
        kpi: KPI e metriche da analizzare
        profile: Profilo utente opzionale
        
    Returns:
        Dict con summary, technical, detailed (formato originale)
    """
    engine = VEEEngine()
    return engine.explain_ticker(ticker, kpi, profile)


# LangGraph Node Integration
def vee_explainability_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo LangGraph per VEE 2.0 Explainability
    
    Input state keys:
    - tickers: List[str] - ticker symbols
    - kpi_results: Dict[str, Dict] - KPI per ticker
    - user_profile: Dict (optional) - profilo utente
    - vee_config: Dict (optional) - configurazione VEE
    
    Output state keys:
    - vee_explanations: Dict[str, Dict] - spiegazioni per ticker
    """
    print(f"\n🧠 [VEE 2.0] Avvio Explainability Engine")
    
    tickers = state.get('tickers', [])
    kpi_results = state.get('kpi_results', {})
    user_profile = state.get('user_profile', {})
    vee_config = state.get('vee_config', {})
    
    if not tickers:
        print("⚠️ Nessun ticker nello stato → skip VEE")
        return state
    
    engine = VEEEngine()
    
    # Apply configuration
    if 'auto_store' in vee_config:
        engine.auto_store = vee_config['auto_store']
    if 'use_memory_context' in vee_config:
        engine.use_memory_context = vee_config['use_memory_context']
    
    explanations = {}
    
    for ticker in tickers:
        try:
            print(f"🧠 Generazione spiegazioni per {ticker}...")
            
            # Get KPI for this ticker
            ticker_kpi = kpi_results.get(ticker, {})
            
            # Generate comprehensive explanation
            explanation = engine.explain_comprehensive(ticker, ticker_kpi, user_profile)
            explanations[ticker] = explanation
            
            # Log key insights
            vee_meta = explanation.get('vee_metadata', {})
            confidence = explanation.get('vee_analysis', {}).get('confidence_level', 0)
            
            print(f"✅ {ticker}: {vee_meta.get('language', 'it')} explanation "
                  f"(confidence: {confidence:.2f}, "
                  f"contextualized: {vee_meta.get('contextualized', False)})")
                  
        except Exception as e:
            print(f"❌ Errore VEE per {ticker}: {e}")
            # Store error explanation
            explanations[ticker] = engine._fallback_comprehensive(ticker, {}, user_profile, str(e))
    
    # Update state
    state['vee_explanations'] = explanations
    
    print(f"🧠 [VEE 2.0] Completate spiegazioni per {len(explanations)} tickers\n")
    return state


if __name__ == "__main__":
    # Test VEE Engine 2.0
    engine = VEEEngine()
    
    # Test data
    test_kpi = {
        'momentum_z': 0.8,
        'vola_z': -0.5,
        'sentiment_z': 0.3,
        'technical_score': 65,
        'risk_score': 45,
        'composite_score': 70
    }
    
    test_profile = {
        'lang': 'it',
        'level': 'intermediate'
    }
    
    print("=== VEE Engine 2.0 Test ===")
    
    # Test standard explanation
    result = engine.explain_ticker("AAPL", test_kpi, test_profile)
    print(f"Summary: {result['summary']}")
    print(f"Technical: {result['technical']}")
    print(f"Detailed: {result['detailed'][:200]}...")
    
    # Test comprehensive explanation
    comprehensive = engine.explain_comprehensive("AAPL", test_kpi, test_profile)
    print(f"\nVEE Analysis Signals: {comprehensive['vee_analysis']['signals']}")
    print(f"Dominant Factor: {comprehensive['vee_analysis']['dominant_factor']}")
    print(f"Confidence: {comprehensive['vee_analysis']['confidence_level']:.2f}")
    print(f"Language: {comprehensive['vee_metadata']['language']}")
    
    # Test insights
    insights = engine.get_explanation_insights("AAPL", days=30)
    if insights:
        print(f"\nInsights: {insights}")
    else:
        print("\nNo historical insights available")