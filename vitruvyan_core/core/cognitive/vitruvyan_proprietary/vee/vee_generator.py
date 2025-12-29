# core/logic/vitruvyan_proprietary/vee/vee_generator.py
"""
📝 VEE Generator - Spiegazioni Multilivello

Genera spiegazioni stratificate in linguaggio naturale:
- Summary: Spiegazione concisa per utenti generali
- Technical: Dettagli tecnici per analisti 
- Detailed: Analisi completa per esperti

Principi:
- Linguaggio naturale e accessibile
- Personalizzazione per profilo utente
- Consistenza narrativa
- Zero bias nelle raccomandazioni
"""

import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from .vee_analyzer import AnalysisResult


@dataclass
class ExplanationLevels:
    """Spiegazioni multilivello per un ticker"""
    ticker: str
    timestamp: datetime
    
    # Tre livelli di spiegazione
    summary: str      # Conciso, per tutti
    technical: str    # Dettagliato, per analisti
    detailed: str     # Completo, per esperti
    
    # Metadata
    language: str
    confidence_note: str
    profile_adapted: bool
    
    # Context enrichment
    contextualized: Optional[str] = None
    historical_reference: Optional[str] = None
    
    # PR-C: VSGS Semantic Grounding (3-layer explainability)
    semantic_grounded: Optional[str] = None  # Synthesis of semantic_matches texts
    epistemic_trace: Optional[List[str]] = None  # trace_ids from grounding events


class VEEGenerator:
    """
    Multi-level explanation generator
    
    Converts analysis results into natural language:
    - Template-based generation for consistency
    - User profile personalization
    - English-only templates (translations via Babel Gardens if needed)
    - Linguistic variation for naturalness
    """
    
    def __init__(self):
        # English-only templates for all explanation levels
        self.templates = {
            'summary': {
                'positive': [
                    "{ticker} shows {signals_text} with {dominant_factor} as the prevailing element.",
                    "Analysis of {ticker} highlights {signals_text}, dominated by {dominant_factor}.",
                    "{ticker} displays {signals_text}, primarily characterized by {dominant_factor}."
                ],
                'negative': [
                    "{ticker} exhibits {signals_text} with {dominant_factor} as a critical factor.",
                    "Analysis of {ticker} reveals {signals_text}, negatively influenced by {dominant_factor}.",
                    "{ticker} demonstrates {signals_text}, primarily penalized by {dominant_factor}."
                ],
                'neutral': [
                    "{ticker} presents {signals_text} in a context of {dominant_factor}.",
                    "Analysis of {ticker} shows {signals_text} with {dominant_factor} as neutral element.",
                    "{ticker} exhibits {signals_text}, characterized by {dominant_factor}."
                ]
            },
            'technical': {
                'base': [
                    "Technical analysis of {ticker}: {dominant_factor} emerges as prevailing factor (intensity: {intensity:.1%}). Relevant parameters: {signals_summary}. Sentiment direction: {sentiment_direction}.",
                    "Technical breakdown {ticker}: {dominant_factor} dominates analysis with {intensity:.1%} intensity. Signals identified: {signals_summary}. Overall sentiment: {sentiment_direction}.",
                    "Technical assessment {ticker}: {dominant_factor} represents main driver (strength: {intensity:.1%}). Significant metrics: {signals_summary}. Orientation: {sentiment_direction}."
                ]
            },
            'detailed': {
                'comprehensive': [
                    "In-depth analysis of {ticker}: Performance reflects a complex balance between various factors. {dominant_factor} emerges as dominant element with {intensity:.1%} intensity, followed by {secondary_factors}. {patterns_text} {confidence_text} This analysis provides no direct buy/sell indications but represents an objective assessment of current state.",
                    "Detailed study {ticker}: Technical-fundamental framework highlights {dominant_factor} as main driver (intensity {intensity:.1%}). {patterns_text} Current configuration suggests {sentiment_direction} sentiment with {secondary_factors} as complementary factors. {confidence_text} Interpretive caution is recommended with no direct action based solely on this analysis.",
                    "Comprehensive assessment {ticker}: Multidimensional analysis identifies {dominant_factor} as prevailing factor (strength {intensity:.1%}). {patterns_text} The {sentiment_direction} sentiment is supported by {secondary_factors}. {confidence_text} This evaluation is purely informational and does not constitute investment recommendation."
                ]
            }
        }
        
        # English-only term translations (no language variants)
        self.translations = {
            'positive': 'positive',
            'negative': 'negative',
            'neutral': 'neutral',
            'momentum': 'momentum',
            'sentiment': 'sentiment', 
            'risk': 'risk profile',
            'volatility': 'volatility',
            'technical': 'technical factor',
            'strength': 'relative strength'
        }
    
    def generate_explanation(self, analysis: AnalysisResult, 
                           profile: Optional[Dict[str, Any]] = None,
                           semantic_context: Optional[List[Dict[str, Any]]] = None) -> ExplanationLevels:
        """
        Genera spiegazioni multilivello da risultato di analisi
        
        Args:
            analysis: AnalysisResult dall'analyzer
            profile: Profilo utente per personalizzazione
            semantic_context: VSGS semantic matches (PR-C) - list of dicts with keys:
                             text (str), score (float), trace_id (str), language (str)
            
        Returns:
            ExplanationLevels con spiegazioni stratificate + semantic grounding (PR-C)
        """
        try:
            # Extract profile preferences (language removed - always EN)
            user_level = self._extract_user_level(profile)
            
            # Prepare content variables
            content_vars = self._prepare_content_variables(analysis)
            
            # Generate explanations at different levels
            summary = self._generate_summary(analysis, content_vars)
            technical = self._generate_technical(analysis, content_vars)
            detailed = self._generate_detailed(analysis, content_vars, user_level)
            
            # Confidence note
            confidence_note = self._generate_confidence_text(analysis.confidence_level)
            
            # PR-C: VSGS Semantic Grounding Layer (3-layer explainability)
            semantic_grounded = None
            epistemic_trace = None
            
            if semantic_context and len(semantic_context) > 0:
                # Layer 2: Semantic synthesis (combine semantic_matches texts)
                semantic_grounded = self._generate_semantic_synthesis(semantic_context)
                
                # Layer 3: Epistemic trace (extract trace_ids)
                epistemic_trace = [m.get("trace_id") for m in semantic_context if m.get("trace_id")]
            
            # Return structured explanation levels
            return ExplanationLevels(
                ticker=analysis.ticker,
                timestamp=datetime.now(),
                summary=summary,
                technical=technical,
                detailed=detailed,
                language='en',  # Always English
                confidence_note=confidence_note,
                profile_adapted=profile is not None,
                semantic_grounded=semantic_grounded,  # PR-C: VSGS layer 2
                epistemic_trace=epistemic_trace  # PR-C: VSGS layer 3
            )
            
        except Exception as e:
            return self._create_error_explanation(analysis.ticker, str(e), profile)
    
    def _extract_user_level(self, profile: Optional[Dict[str, Any]]) -> str:
        """Extract expertise level from user profile"""
        if not profile:
            return 'intermediate'
        
        level = profile.get('level', profile.get('expertise', 'intermediate')).lower()
        
        if level in ['beginner', 'basic', 'novice']:
            return 'beginner'
        elif level in ['expert', 'advanced', 'professional']:
            return 'expert'
        else:
            return 'intermediate'
    
    def _prepare_content_variables(self, analysis: AnalysisResult) -> Dict[str, Any]:
        """Prepare variables for templating (English only)"""
        
        # Signals text
        if analysis.signals and analysis.signals[0] != "no relevant signals":
            signals_text = ", ".join(analysis.signals[:3])  # Max 3 signals for readability
        else:
            signals_text = "mixed signals"
        
        # Dominant factor translation
        dominant_factor = analysis.dominant_factor
        for key, translation in self.translations.items():
            if key in dominant_factor.lower():
                dominant_factor = translation
                break
        
        # Secondary factors (from signal strengths)
        secondary_factors = []
        sorted_strengths = sorted(analysis.signal_strengths.items(), 
                                key=lambda x: x[1], reverse=True)[1:3]  # Top 2 secondary
        
        for factor, strength in sorted_strengths:
            if factor in self.translations:
                secondary_factors.append(self.translations[factor])
            else:
                secondary_factors.append(factor)
        
        secondary_text = ", ".join(secondary_factors) if secondary_factors else "secondary factors"
        
        # Patterns text
        if analysis.patterns:
            patterns_text = "Key patterns: " + ", ".join(analysis.patterns[:2]) + ". "
        else:
            patterns_text = ""
        
        # Sentiment direction translation
        sentiment_direction = self.translations.get(analysis.sentiment_direction, analysis.sentiment_direction)
        
        return {
            'ticker': analysis.ticker,
            'signals_text': signals_text,
            'dominant_factor': dominant_factor,
            'secondary_factors': secondary_text,
            'intensity': analysis.overall_intensity,
            'sentiment_direction': sentiment_direction,
            'signals_summary': ", ".join(analysis.signals[:2]) if len(analysis.signals) > 1 else signals_text,
            'patterns_text': patterns_text,
            'confidence_level': analysis.confidence_level
        }
    
    def _generate_summary(self, analysis: AnalysisResult, content_vars: Dict) -> str:
        """Generate summary explanation (English only)"""
        sentiment_key = analysis.sentiment_direction
        templates = self.templates['summary'][sentiment_key]
        
        template = random.choice(templates)
        return template.format(**content_vars)
    
    def _generate_technical(self, analysis: AnalysisResult, content_vars: Dict) -> str:
        """Generate technical explanation (English only)"""
        templates = self.templates['technical']['base']
        template = random.choice(templates)
        
        return template.format(**content_vars)
    
    def _generate_detailed(self, analysis: AnalysisResult, content_vars: Dict, 
                          user_level: str) -> str:
        """Generate detailed explanation (English only)"""
        templates = self.templates['detailed']['comprehensive']
        template = random.choice(templates)
        
        # Add confidence text
        confidence_text = self._generate_confidence_text(analysis.confidence_level)
        content_vars['confidence_text'] = confidence_text
        
        detailed = template.format(**content_vars)
        
        # Adapt for user level (English only)
        if user_level == 'beginner':
            # Simplify for beginners
            detailed = self._simplify_for_beginners(detailed)
        elif user_level == 'expert':
            # Add technical depth for experts
            detailed = self._enhance_for_experts(detailed, analysis)
        
        return detailed
    
    def _generate_confidence_text(self, confidence: float) -> str:
        """Generate confidence text for detailed explanation (English only)"""
        if confidence >= 0.8:
            return "The analysis shows high reliability. "
        elif confidence >= 0.6:
            return "The analysis shows moderate reliability. "
        else:
            return "The analysis shows limited reliability. "
    
    def _simplify_for_beginners(self, detailed: str) -> str:
        """Simplify language for beginners (English only)"""
        # Simplify English technical terms
        simplified = detailed.replace("multidimensional", "comprehensive")
        simplified = simplified.replace("configuration", "situation")
        simplified = simplified.replace("prevailing factor", "main factor")
        return simplified
    
    def _enhance_for_experts(self, detailed: str, analysis: AnalysisResult) -> str:
        """Enhance analysis for experts (English only)"""
        expert_addition = f" Quantitative metrics: overall intensity {analysis.overall_intensity:.2f}, " \
                        f"confidence {analysis.confidence_level:.2f}, " \
                        f"data coverage: {analysis.kpi_count} indicators."
        
        return detailed + expert_addition
    
    def _create_error_explanation(self, ticker: str, error_msg: str, 
                                profile: Optional[Dict[str, Any]]) -> ExplanationLevels:
        """Create error explanation (English only)"""
        summary = f"Error in explanation generation for {ticker}: {error_msg}"
        technical = "Unable to process analysis data."
        detailed = f"A technical error occurred during explanation generation. Details: {error_msg}"
        confidence_note = "Analysis unavailable due to technical error."
        
        return ExplanationLevels(
            ticker=ticker,
            timestamp=datetime.now(),
            summary=summary,
            technical=technical,
            detailed=detailed,
            language='en',  # Always English
            confidence_note=confidence_note,
            profile_adapted=False,
            semantic_grounded=None,  # PR-C: No semantic grounding on error
            epistemic_trace=None  # PR-C: No trace on error
        )
    
    def _generate_semantic_synthesis(self, semantic_context: List[Dict[str, Any]]) -> str:
        """
        PR-C: Generate semantic synthesis from VSGS semantic_matches
        
        Args:
            semantic_context: List of semantic matches with keys:
                             text (str), score (float), language (str)
        
        Returns:
            Synthesized text explaining semantic grounding sources
        """
        if not semantic_context or len(semantic_context) == 0:
            return "No semantic grounding available."
        
        # Extract top-3 matches (already sorted by score in grounding_node)
        top_matches = semantic_context[:3]
        
        # Build synthesis text
        synthesis_parts = []
        synthesis_parts.append(f"This analysis is semantically grounded on {len(top_matches)} prior context(s):")
        
        for i, match in enumerate(top_matches, 1):
            text = match.get("text", "").strip()
            score = match.get("score", 0.0)
            match_lang = match.get("language", "unknown")
            
            # Truncate long texts
            if len(text) > 120:
                text = text[:120] + "..."
            
            synthesis_parts.append(f"{i}. [{match_lang}] (similarity: {score:.2f}) \"{text}\"")
        
        synthesis_parts.append(
            "The model integrated these semantic references to provide contextually coherent explanations."
        )
        
        return "\n".join(synthesis_parts)


# Convenience function for standalone usage
def generate_explanation(ticker: str, analysis: AnalysisResult, 
                        profile: Optional[Dict[str, Any]] = None,
                        semantic_context: Optional[List[Dict[str, Any]]] = None) -> ExplanationLevels:
    """
    Convenience function for standalone explanation generation
    
    Args:
        ticker: Ticker symbol (for compatibility)
        analysis: AnalysisResult from analyzer
        profile: Optional user profile
        semantic_context: VSGS semantic matches (PR-C)
        
    Returns:
        ExplanationLevels with multi-level explanations + semantic grounding
    """
    generator = VEEGenerator()
    return generator.generate_explanation(analysis, profile, semantic_context)


if __name__ == "__main__":
    # Test standalone - requires vee_analyzer
    from .vee_analyzer import analyze_kpi
    
    # Test KPI data
    test_kpi = {
        'momentum_z': 0.8,
        'sentiment_z': 0.3,
        'technical_score': 65,
        'risk_score': 45
    }
    
    # Analyze first
    analysis = analyze_kpi("AAPL", test_kpi)
    
    # Generate explanations
    generator = VEEGenerator()
    
    # Test Italian
    explanations_it = generator.generate_explanation(analysis, {'lang': 'it', 'level': 'intermediate'})
    
    print(f"=== VEE Generator Test Results for {explanations_it.ticker} (IT) ===")
    print(f"Summary: {explanations_it.summary}")
    print(f"Technical: {explanations_it.technical}")
    print(f"Detailed: {explanations_it.detailed}")
    print(f"Confidence: {explanations_it.confidence_note}")
    
    # Test English
    explanations_en = generator.generate_explanation(analysis, {'lang': 'en', 'level': 'expert'})
    
    print(f"\n=== VEE Generator Test Results for {explanations_en.ticker} (EN) ===")
    print(f"Summary: {explanations_en.summary}")
    print(f"Technical: {explanations_en.technical}")
    print(f"Detailed: {explanations_en.detailed}")
    print(f"Confidence: {explanations_en.confidence_note}")