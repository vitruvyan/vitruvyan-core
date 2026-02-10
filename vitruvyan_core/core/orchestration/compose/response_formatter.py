# vitruvyan_core/core/orchestration/compose/response_formatter.py
"""
ResponseFormatter ABC for domain-specific response formatting.

Domains inject their formatting logic (verdicts, gauges, matrices, etc.)
through this interface while keeping the core compose_node agnostic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class ConversationType(Enum):
    """
    Base conversation types that domains can extend.
    
    Domains may define their own conversation types, but should map
    them to these base types when possible for consistent UX.
    """
    SINGLE_ENTITY = "single_entity"      # One entity, detailed analysis
    MULTI_ENTITY = "multi_entity"        # Comparison across entities
    ONBOARDING = "onboarding"            # First-time user flow
    CONVERSATIONAL = "conversational"    # General Q&A, no specific entity
    SLOT_FILLING = "slot_filling"        # Clarifying missing information
    NO_DATA = "no_data"                  # No data available
    ERROR = "error"                      # Error state


@dataclass
class FormattedResponse:
    """
    Domain-formatted response that gets merged into compose_node output.
    
    The core compose_node handles the generic response structure,
    and FormattedResponse adds domain-specific fields.
    """
    # Required fields
    conversation_type: ConversationType
    narrative: str
    
    # Optional domain-specific fields (plugin adds what it needs)
    domain_data: Dict[str, Any] = field(default_factory=dict)
    
    # Standard UX fields (optional)
    verdict: Optional[Dict[str, Any]] = None
    gauge: Optional[Dict[str, Any]] = None
    comparison_matrix: Optional[List[Dict[str, Any]]] = None
    cards: Optional[List[Dict[str, Any]]] = None


class RawEngineOutput(TypedDict, total=False):
    """
    Structure for raw output from domain-specific engines (e.g., Neural Engine).
    
    Domains define their own output shape, but this provides common fields.
    """
    ranking: Dict[str, List[Dict[str, Any]]]  # e.g., {"entities": [...], "etf": [...]}
    semantic_fallback: bool
    answer: str


class ResponseFormatter(ABC):
    """
    Abstract base class for domain-specific response formatting.
    
    Each domain plugin (finance, health, etc.) provides its own implementation
    that knows how to format raw engine output into user-facing responses.
    
    Design philosophy:
    - Core compose_node handles generic flow (slot merging, routing, UX)
    - ResponseFormatter handles domain-specific presentation
    - Domains can define their own conversation types, verdicts, gauges, etc.
    
    Example usage in FinancePlugin:
    
        class FinanceResponseFormatter(ResponseFormatter):
            def detect_conversation_type(self, state, raw_output):
                # Finance-specific detection (analysis, comparison, allocation)
                ...
            
            def format_single_entity(self, entity_id, data, lang, state):
                # Finance verdict + gauge
                ...
    """
    
    @abstractmethod
    def detect_conversation_type(
        self,
        state: Dict[str, Any],
        raw_output: Optional[RawEngineOutput] = None,
    ) -> ConversationType:
        """
        Detect the conversation type based on state and raw output.
        
        Args:
            state: Current graph state with intent, entity_ids, etc.
            raw_output: Optional raw output from domain engine
            
        Returns:
            ConversationType indicating how to format the response
        """
        pass
    
    @abstractmethod
    def format_single_entity(
        self,
        entity_id: str,
        entity_data: Dict[str, Any],
        language: str,
        state: Dict[str, Any],
    ) -> FormattedResponse:
        """
        Format response for single-entity analysis.
        
        Args:
            entity_id: The entity being analyzed
            entity_data: Raw data for this entity (scores, factors, etc.)
            language: ISO language code (en, it, es, etc.)
            state: Full graph state for context
            
        Returns:
            FormattedResponse with narrative, verdict, gauge, etc.
        """
        pass
    
    @abstractmethod
    def format_multi_entity(
        self,
        entity_ids: List[str],
        raw_output: RawEngineOutput,
        language: str,
        state: Dict[str, Any],
    ) -> FormattedResponse:
        """
        Format response for multi-entity comparison.
        
        Args:
            entity_ids: Entities being compared
            raw_output: Raw output containing data for all entities
            language: ISO language code
            state: Full graph state for context
            
        Returns:
            FormattedResponse with narrative, comparison_matrix, etc.
        """
        pass
    
    @abstractmethod
    def format_onboarding(
        self,
        language: str,
        state: Dict[str, Any],
    ) -> FormattedResponse:
        """
        Format onboarding response for new users.
        
        Args:
            language: ISO language code
            state: Full graph state for context
            
        Returns:
            FormattedResponse with cards for onboarding wizard
        """
        pass
    
    def format_no_data(
        self,
        language: str,
        state: Dict[str, Any],
    ) -> FormattedResponse:
        """
        Format response when no data is available.
        
        Default implementation provides a generic message.
        Domains can override to add domain-specific messaging.
        
        Args:
            language: ISO language code
            state: Full graph state for context
            
        Returns:
            FormattedResponse with no-data message
        """
        messages = {
            "en": "Data is not currently available. Please try again shortly.",
            "it": "I dati non sono momentaneamente disponibili. Riprova tra poco.",
            "es": "Los datos no están disponibles. Vuelve a intentarlo en breve.",
            "fr": "Les données ne sont pas disponibles. Réessayez bientôt.",
            "de": "Daten sind derzeit nicht verfügbar. Bitte versuchen Sie es später erneut.",
            "pt": "Os dados não estão disponíveis no momento. Tente novamente em breve.",
        }
        return FormattedResponse(
            conversation_type=ConversationType.NO_DATA,
            narrative=messages.get(language, messages["en"]),
        )
    
    def format_error(
        self,
        error: Exception,
        language: str,
        state: Dict[str, Any],
    ) -> FormattedResponse:
        """
        Format error response.
        
        Default implementation provides a generic error message.
        
        Args:
            error: The exception that occurred
            language: ISO language code
            state: Full graph state for context
            
        Returns:
            FormattedResponse with error message
        """
        messages = {
            "en": "An error occurred. Please try again.",
            "it": "Si è verificato un errore. Riprova.",
            "es": "Se produjo un error. Inténtalo de nuevo.",
            "fr": "Une erreur s'est produite. Réessayez.",
            "de": "Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.",
            "pt": "Ocorreu um erro. Tente novamente.",
        }
        return FormattedResponse(
            conversation_type=ConversationType.ERROR,
            narrative=messages.get(language, messages["en"]),
            domain_data={"error": str(error)},
        )


class GenericResponseFormatter(ResponseFormatter):
    """
    Generic response formatter for domains without custom formatting.
    
    Provides basic formatting that works for any domain, using
    the raw output directly without domain-specific transformations.
    """
    
    def detect_conversation_type(
        self,
        state: Dict[str, Any],
        raw_output: Optional[RawEngineOutput] = None,
    ) -> ConversationType:
        """Detect conversation type based on entity count."""
        entity_ids = state.get("entity_ids", [])
        
        if not entity_ids:
            return ConversationType.CONVERSATIONAL
        elif len(entity_ids) == 1:
            return ConversationType.SINGLE_ENTITY
        else:
            return ConversationType.MULTI_ENTITY
    
    def format_single_entity(
        self,
        entity_id: str,
        entity_data: Dict[str, Any],
        language: str,
        state: Dict[str, Any],
    ) -> FormattedResponse:
        """Format single entity with basic narrative."""
        return FormattedResponse(
            conversation_type=ConversationType.SINGLE_ENTITY,
            narrative=f"Analysis for {entity_id}.",
            domain_data={"entity_id": entity_id, "data": entity_data},
        )
    
    def format_multi_entity(
        self,
        entity_ids: List[str],
        raw_output: RawEngineOutput,
        language: str,
        state: Dict[str, Any],
    ) -> FormattedResponse:
        """Format multi-entity with basic comparison."""
        return FormattedResponse(
            conversation_type=ConversationType.MULTI_ENTITY,
            narrative=f"Comparison of {len(entity_ids)} entities.",
            domain_data={"entity_ids": entity_ids},
        )
    
    def format_onboarding(
        self,
        language: str,
        state: Dict[str, Any],
    ) -> FormattedResponse:
        """Format basic onboarding."""
        messages = {
            "en": "Welcome! What would you like to explore?",
            "it": "Benvenuto! Cosa vorresti esplorare?",
            "es": "¡Bienvenido! ¿Qué te gustaría explorar?",
        }
        return FormattedResponse(
            conversation_type=ConversationType.ONBOARDING,
            narrative=messages.get(language, messages["en"]),
        )
