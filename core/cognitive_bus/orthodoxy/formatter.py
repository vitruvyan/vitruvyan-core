"""
🏛️ SOCRATIC RESPONSE FORMATTER - Convert non_liquet to User-Friendly Narratives

Sacred Order #5: Truth & Governance
Formats Orthodoxy verdicts into natural language, especially "I don't know" responses.

The key to Socratic dialogue: admitting uncertainty with dignity.
"""

from typing import Dict, Any, Optional
from .verdicts import OrthodoxyVerdict, OrthodoxyStatus


class SocraticResponseFormatter:
    """
    Converts Orthodoxy verdicts into user-friendly natural language.
    
    Especially important for non_liquet verdicts:
    - Admit uncertainty explicitly
    - Provide partial knowledge transparently
    - Explain WHY we're uncertain
    - Offer best guess with caveats
    
    This prevents the "confident hallucination" problem.
    """
    
    def __init__(self, language: str = "en"):
        """
        Initialize formatter.
        
        Args:
            language: Language code (en, it, es, fr, de, etc.)
        """
        self.language = language
        
        # Language templates (extend for multilingual)
        self.templates = {
            "en": {
                "non_liquet_intro": "I need to be honest: I don't have enough information to give you a definitive answer.",
                "what_we_know": "What I can tell you:",
                "what_is_uncertain": "What remains uncertain:",
                "why_uncertain": "Why I'm uncertain:",
                "best_guess_intro": "Based on what I know, my best estimate is:",
                "best_guess_warning": "⚠️ Please note: This is an educated guess, not a validated result.",
                "confidence_low": "My confidence in this answer is low ({confidence:.0%}).",
                "blessed_intro": "I'm confident in this analysis:",
                "heretical_intro": "I cannot provide this result because it contains errors:",
                "clarification_intro": "I need clarification before I can answer:"
            },
            "it": {
                "non_liquet_intro": "Devo essere onesto: non ho abbastanza informazioni per darti una risposta definitiva.",
                "what_we_know": "Quello che posso dirti:",
                "what_is_uncertain": "Ciò che resta incerto:",
                "why_uncertain": "Perché sono incerto:",
                "best_guess_intro": "Basandomi su quello che so, la mia stima migliore è:",
                "best_guess_warning": "⚠️ Nota bene: Questa è una stima ragionata, non un risultato validato.",
                "confidence_low": "La mia confidenza in questa risposta è bassa ({confidence:.0%}).",
                "blessed_intro": "Sono sicuro di questa analisi:",
                "heretical_intro": "Non posso fornire questo risultato perché contiene errori:",
                "clarification_intro": "Ho bisogno di chiarimenti prima di rispondere:"
            }
        }
    
    def format_verdict(self, verdict: OrthodoxyVerdict) -> str:
        """
        Convert verdict to natural language.
        
        Args:
            verdict: Orthodoxy verdict to format
            
        Returns:
            Natural language response
        """
        if verdict.status == "non_liquet":
            return self._format_non_liquet(verdict)
        elif verdict.status == "blessed":
            return self._format_blessed(verdict)
        elif verdict.status == "heretical":
            return self._format_heretical(verdict)
        elif verdict.status == "clarification_needed":
            return self._format_clarification_needed(verdict)
        elif verdict.status == "purified":
            return self._format_purified(verdict)
        else:
            return "Unknown verdict status."
    
    def _format_non_liquet(self, verdict: OrthodoxyVerdict) -> str:
        """
        Format non_liquet verdict (CRITICAL FOR SOCRATIC PATTERN).
        
        Structure:
        1. Admit uncertainty honestly
        2. Provide partial knowledge
        3. Explain uncertainty sources
        4. Offer best guess with caveats
        """
        t = self.templates.get(self.language, self.templates["en"])
        
        parts = []
        
        # 1. Honest admission
        parts.append(t["non_liquet_intro"])
        parts.append("")
        
        # 2. Partial knowledge
        if verdict.what_we_know:
            parts.append(f"**{t['what_we_know']}**")
            for item in verdict.what_we_know:
                parts.append(f"- {item}")
            parts.append("")
        
        # 3. Uncertainty
        if verdict.what_is_uncertain:
            parts.append(f"**{t['what_is_uncertain']}**")
            for item in verdict.what_is_uncertain:
                parts.append(f"- {item}")
            parts.append("")
        
        # 4. Why uncertain
        if verdict.uncertainty_sources:
            parts.append(f"**{t['why_uncertain']}**")
            for source in verdict.uncertainty_sources:
                parts.append(f"- {source}")
            parts.append("")
        
        # 5. Best guess (with caveats)
        if verdict.best_guess:
            parts.append(t["best_guess_intro"])
            parts.append("")
            # Format best guess (implementation specific to content type)
            parts.append(self._format_best_guess(verdict.best_guess))
            parts.append("")
            parts.append(t["best_guess_warning"])
            if verdict.best_guess_caveats:
                for caveat in verdict.best_guess_caveats:
                    parts.append(f"  - {caveat}")
        
        # 6. Confidence disclaimer
        parts.append("")
        parts.append(t["confidence_low"].format(confidence=verdict.confidence))
        
        return "\n".join(parts)
    
    def _format_blessed(self, verdict: OrthodoxyVerdict) -> str:
        """Format blessed verdict (standard approval)."""
        t = self.templates.get(self.language, self.templates["en"])
        return f"{t['blessed_intro']}\n\n{self._format_output(verdict.approved_output)}"
    
    def _format_heretical(self, verdict: OrthodoxyVerdict) -> str:
        """Format heretical verdict (rejection)."""
        t = self.templates.get(self.language, self.templates["en"])
        
        parts = [t["heretical_intro"]]
        if verdict.violations:
            for violation in verdict.violations:
                parts.append(f"- {violation}")
        if verdict.rejection_reason:
            parts.append(f"\nReason: {verdict.rejection_reason}")
        
        return "\n".join(parts)
    
    def _format_clarification_needed(self, verdict: OrthodoxyVerdict) -> str:
        """Format clarification_needed verdict."""
        t = self.templates.get(self.language, self.templates["en"])
        
        parts = [t["clarification_intro"]]
        parts.append("")
        
        if verdict.clarification_questions:
            for question in verdict.clarification_questions:
                parts.append(f"- {question}")
        
        if verdict.ambiguous_elements:
            parts.append("\nAmbiguous elements:")
            for element in verdict.ambiguous_elements:
                parts.append(f"- {element}")
        
        return "\n".join(parts)
    
    def _format_purified(self, verdict: OrthodoxyVerdict) -> str:
        """Format purified verdict (corrected output)."""
        parts = ["The output has been corrected:"]
        parts.append("")
        
        if verdict.original_issues:
            parts.append("Original issues:")
            for issue in verdict.original_issues:
                parts.append(f"- {issue}")
            parts.append("")
        
        if verdict.corrections_applied:
            parts.append("Corrections applied:")
            for correction in verdict.corrections_applied:
                parts.append(f"- {correction}")
        
        return "\n".join(parts)
    
    def _format_output(self, output: Optional[Dict[str, Any]]) -> str:
        """Format output dictionary (implementation specific)."""
        if not output:
            return ""
        
        # Basic formatting - can be extended based on output type
        return str(output)
    
    def _format_best_guess(self, best_guess: Dict[str, Any]) -> str:
        """Format best guess dictionary (implementation specific)."""
        # Basic formatting - can be extended based on content type
        return str(best_guess)


# Convenience function for quick formatting
def format_verdict_to_text(verdict: OrthodoxyVerdict, language: str = "en") -> str:
    """
    Quick utility to format verdict to text.
    
    Args:
        verdict: Orthodoxy verdict to format
        language: Language code (en, it, es, etc.)
        
    Returns:
        Natural language response
    """
    formatter = SocraticResponseFormatter(language=language)
    return formatter.format_verdict(verdict)
