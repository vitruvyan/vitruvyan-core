# vitruvyan_core/core/orchestration/compose/slot_filler.py
"""
SlotFiller ABC for domain-specific slot filling questions.

Domains define their own slots and how to generate human-friendly
questions to fill them. The core compose_node uses this interface
to generate clarification questions without knowing the domain.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SlotQuestion:
    """
    A question to fill a missing slot.
    
    Attributes:
        slot_name: The slot being filled (e.g., "time_horizon")
        question: Human-friendly question text
        options: Optional list of suggested options
        context: Additional context for the question
        is_required: Whether this slot is required to proceed
    """
    slot_name: str
    question: str
    options: Optional[List[str]] = None
    context: Optional[str] = None
    is_required: bool = True


@dataclass
class SlotBundle:
    """
    Bundled questions for multiple slots.
    
    Used when asking about multiple slots in a single turn
    to reduce conversation turns.
    """
    slots: List[str]
    questions: List[SlotQuestion]
    bundled_question: str  # Single question covering all slots
    chain_of_thought: Optional[str] = None  # Reasoning recap


class SlotDefinition:
    """
    Definition of a slot that can be filled.
    
    Attributes:
        name: Slot identifier (e.g., "time_horizon")
        display_name: Human-friendly name
        description: Description of what this slot captures
        valid_values: Optional list of valid values
        default_value: Optional default if not provided
        required_for_intents: Intents that require this slot
    """
    
    def __init__(
        self,
        name: str,
        display_name: str,
        description: str = "",
        valid_values: Optional[List[str]] = None,
        default_value: Optional[Any] = None,
        required_for_intents: Optional[List[str]] = None,
    ):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.valid_values = valid_values
        self.default_value = default_value
        self.required_for_intents = required_for_intents or []


class SlotFiller(ABC):
    """
    Abstract base class for domain-specific slot filling.
    
    Each domain defines its own slots and how to generate questions
    that are culturally and emotionally appropriate.
    
    Design philosophy:
    - Slots are domain-specific (finance has "risk_tolerance", health has "symptom_duration")
    - Questions should be adapted to language, emotion, and user context
    - Bundling reduces conversation turns while maintaining clarity
    
    Example usage in FinancePlugin:
    
        class FinanceSlotFiller(SlotFiller):
            def get_slot_definitions(self):
                return [
                    SlotDefinition("risk_tolerance", "Risk Profile", ...),
                    SlotDefinition("time_horizon", "Investment Horizon", ...),
                ]
            
            def generate_question(self, slot, language, state):
                # Emotion-aware question generation
                ...
    """
    
    @abstractmethod
    def get_slot_definitions(self) -> List[SlotDefinition]:
        """
        Return all slot definitions for this domain.
        
        Returns:
            List of SlotDefinition objects
        """
        pass
    
    @abstractmethod
    def check_missing_slots(
        self,
        current_slots: Dict[str, Any],
        intent: str,
    ) -> List[str]:
        """
        Check which required slots are missing for the given intent.
        
        Args:
            current_slots: Currently filled slots
            intent: The detected intent
            
        Returns:
            List of missing slot names
        """
        pass
    
    @abstractmethod
    def generate_question(
        self,
        slot_name: str,
        language: str,
        state: Dict[str, Any],
    ) -> SlotQuestion:
        """
        Generate a human-friendly question for a missing slot.
        
        Args:
            slot_name: The slot to ask about
            language: ISO language code
            state: Full graph state for context (emotion, history, etc.)
            
        Returns:
            SlotQuestion with the generated question
        """
        pass
    
    def generate_bundled_questions(
        self,
        missing_slots: List[str],
        language: str,
        state: Dict[str, Any],
    ) -> SlotBundle:
        """
        Generate a bundled question for multiple missing slots.
        
        Default implementation creates individual questions and
        concatenates them. Domains can override for more natural bundling.
        
        Args:
            missing_slots: List of missing slot names
            language: ISO language code
            state: Full graph state for context
            
        Returns:
            SlotBundle with bundled questions
        """
        questions = [
            self.generate_question(slot, language, state)
            for slot in missing_slots
        ]
        
        # Simple bundling - concatenate questions
        bundled = " ".join(q.question for q in questions)
        
        return SlotBundle(
            slots=missing_slots,
            questions=questions,
            bundled_question=bundled,
        )
    
    def generate_chain_of_thought(
        self,
        current_slots: Dict[str, Any],
        missing_slots: List[str],
        state: Dict[str, Any],
    ) -> str:
        """
        Generate a chain-of-thought recap of what we know.
        
        This helps users understand why we're asking for more info.
        Default implementation is generic; domains should override.
        
        Args:
            current_slots: Currently filled slots
            missing_slots: What we still need
            state: Full graph state for context
            
        Returns:
            Chain-of-thought text explaining the situation
        """
        filled = [f"{k}={v}" for k, v in current_slots.items() if v is not None]
        
        if filled:
            return f"I understand: {', '.join(filled)}. To help further, I need: {', '.join(missing_slots)}."
        else:
            return f"I need some information to assist you: {', '.join(missing_slots)}."


class GenericSlotFiller(SlotFiller):
    """
    Generic slot filler that works without domain-specific slots.
    
    Used as a fallback when no domain plugin is registered.
    """
    
    def get_slot_definitions(self) -> List[SlotDefinition]:
        """No predefined slots in generic filler."""
        return []
    
    def check_missing_slots(
        self,
        current_slots: Dict[str, Any],
        intent: str,
    ) -> List[str]:
        """No required slots in generic filler."""
        return []
    
    def generate_question(
        self,
        slot_name: str,
        language: str,
        state: Dict[str, Any],
    ) -> SlotQuestion:
        """Generate a basic question for any slot."""
        messages = {
            "en": f"Could you please provide {slot_name}?",
            "it": f"Potresti fornire {slot_name}?",
            "es": f"¿Podrías proporcionar {slot_name}?",
            "fr": f"Pourriez-vous fournir {slot_name}?",
            "de": f"Könnten Sie bitte {slot_name} angeben?",
            "pt": f"Você poderia fornecer {slot_name}?",
        }
        return SlotQuestion(
            slot_name=slot_name,
            question=messages.get(language, messages["en"]),
        )
