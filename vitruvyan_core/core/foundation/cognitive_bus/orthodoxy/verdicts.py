"""
🏛️ ORTHODOXY VERDICTS - Socratic Epistemic Judgments

Sacred Order #5: Truth & Governance
Formal verdict system with explicit "non_liquet" (not proven) capability.

The Socratic heart of Vitruvyan — we can say "I don't know".
"""

from dataclasses import dataclass, field
from typing import Literal, List, Optional, Dict, Any
from datetime import datetime

OrthodoxyStatus = Literal[
    "blessed",              # Output valid, high confidence
    "purified",             # Output corrected, errors removed
    "heretical",            # Output rejected, hallucination/violation
    "non_liquet",           # "Not proven" — explicit uncertainty (SOCRATIC)
    "clarification_needed"  # Input ambiguous, clarification requested
]

@dataclass
class OrthodoxyVerdict:
    """
    The formal verdict from Orthodoxy Wardens.
    This is the Socratic heart of Vitruvyan — we can explicitly declare uncertainty.
    
    Five possible states:
    1. blessed: Output approved, high confidence
    2. purified: Output corrected, errors removed
    3. heretical: Output rejected, hallucination/violation detected
    4. non_liquet: "Not proven" — we have partial knowledge but insufficient confidence
    5. clarification_needed: Input too ambiguous, user clarification required
    
    The "non_liquet" status is philosophically critical:
    - Distinguishes "don't know" from "wrong"
    - Provides partial knowledge when available
    - Admits uncertainty sources explicitly
    - Offers best guess with caveats
    
    This prevents hallucination: if confidence is low, we SAY SO.
    """
    status: OrthodoxyStatus
    confidence: float  # 0.0 to 1.0
    
    # For "blessed" - the approved output
    approved_output: Optional[Dict[str, Any]] = None
    
    # For "purified" - what was corrected
    original_issues: Optional[List[str]] = None
    corrections_applied: Optional[List[str]] = None
    
    # For "heretical" - why rejected
    rejection_reason: Optional[str] = None
    violations: Optional[List[str]] = None
    
    # For "non_liquet" - the Socratic response (CRITICAL FOR PHASE 3)
    what_we_know: Optional[List[str]] = None              # Partial knowledge available
    what_is_uncertain: Optional[List[str]] = None         # Explicit uncertainty sources
    uncertainty_sources: Optional[List[str]] = None       # Why we're uncertain
    best_guess: Optional[Dict[str, Any]] = None           # Partial result (if any)
    best_guess_caveats: Optional[List[str]] = None        # Warnings about best guess
    
    # For "clarification_needed"
    clarification_questions: Optional[List[str]] = None
    ambiguous_elements: Optional[List[str]] = None
    
    # Audit trail
    warden_id: str = "warden_primary"
    timestamp: Optional[datetime] = field(default_factory=datetime.utcnow)
    processing_time_ms: int = 0
    event_ids_evaluated: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert verdict to dictionary for JSON serialization."""
        return {
            "status": self.status,
            "confidence": self.confidence,
            "approved_output": self.approved_output,
            "original_issues": self.original_issues,
            "corrections_applied": self.corrections_applied,
            "rejection_reason": self.rejection_reason,
            "violations": self.violations,
            "what_we_know": self.what_we_know,
            "what_is_uncertain": self.what_is_uncertain,
            "uncertainty_sources": self.uncertainty_sources,
            "best_guess": self.best_guess,
            "best_guess_caveats": self.best_guess_caveats,
            "clarification_questions": self.clarification_questions,
            "ambiguous_elements": self.ambiguous_elements,
            "warden_id": self.warden_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "processing_time_ms": self.processing_time_ms,
            "event_ids_evaluated": self.event_ids_evaluated
        }
    
    @staticmethod
    def blessed(output: Dict[str, Any], confidence: float = 0.95, warden_id: str = "warden_primary") -> "OrthodoxyVerdict":
        """Factory method for blessed verdict."""
        return OrthodoxyVerdict(
            status="blessed",
            confidence=confidence,
            approved_output=output,
            warden_id=warden_id
        )
    
    @staticmethod
    def non_liquet(
        what_we_know: List[str],
        what_is_uncertain: List[str],
        uncertainty_sources: List[str],
        best_guess: Optional[Dict[str, Any]] = None,
        confidence: float = 0.3,
        warden_id: str = "warden_primary"
    ) -> "OrthodoxyVerdict":
        """
        Factory method for non_liquet verdict (SOCRATIC).
        
        This is the Socratic "I don't know" — explicit uncertainty admission.
        
        Args:
            what_we_know: Facts we can assert with high confidence
            what_is_uncertain: Elements we cannot verify
            uncertainty_sources: Why we're uncertain (data missing, ambiguous, conflicting)
            best_guess: Partial result if available (with caveats)
            confidence: Overall confidence (typically <0.5 for non_liquet)
            warden_id: Identifier of the warden issuing verdict
        """
        return OrthodoxyVerdict(
            status="non_liquet",
            confidence=confidence,
            what_we_know=what_we_know,
            what_is_uncertain=what_is_uncertain,
            uncertainty_sources=uncertainty_sources,
            best_guess=best_guess,
            best_guess_caveats=[
                "This is a best guess, not a validated result",
                f"Confidence: {confidence:.1%}",
                "Uncertainty explicitly acknowledged"
            ] if best_guess else None,
            warden_id=warden_id
        )
    
    @staticmethod
    def heretical(
        rejection_reason: str,
        violations: List[str],
        confidence: float = 0.9,
        warden_id: str = "warden_primary"
    ) -> "OrthodoxyVerdict":
        """Factory method for heretical verdict (rejection)."""
        return OrthodoxyVerdict(
            status="heretical",
            confidence=confidence,
            rejection_reason=rejection_reason,
            violations=violations,
            warden_id=warden_id
        )
    
    @staticmethod
    def clarification_needed(
        ambiguous_elements: List[str],
        clarification_questions: List[str],
        confidence: float = 0.1,
        warden_id: str = "warden_primary"
    ) -> "OrthodoxyVerdict":
        """Factory method for clarification_needed verdict."""
        return OrthodoxyVerdict(
            status="clarification_needed",
            confidence=confidence,
            ambiguous_elements=ambiguous_elements,
            clarification_questions=clarification_questions,
            warden_id=warden_id
        )


# Utility functions for verdict handling

def is_uncertain(verdict: OrthodoxyVerdict) -> bool:
    """Check if verdict represents uncertainty (non_liquet or clarification_needed)."""
    return verdict.status in ["non_liquet", "clarification_needed"]

def is_rejected(verdict: OrthodoxyVerdict) -> bool:
    """Check if verdict represents rejection (heretical)."""
    return verdict.status == "heretical"

def is_approved(verdict: OrthodoxyVerdict) -> bool:
    """Check if verdict represents approval (blessed or purified)."""
    return verdict.status in ["blessed", "purified"]
