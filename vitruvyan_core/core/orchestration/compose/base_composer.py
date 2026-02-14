# vitruvyan_core/core/orchestration/compose/base_composer.py
"""
BaseComposer ABC for domain-agnostic response composition.

This coordinates ResponseFormatter and SlotFiller from the domain plugin
to produce the final response, while handling generic concerns like:
- Slot merging
- Conversational routing
- Language detection
- UX metadata
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from core.orchestration.compose.response_formatter import (
    ResponseFormatter,
    FormattedResponse,
    ConversationType,
    GenericResponseFormatter,
)
from core.orchestration.compose.slot_filler import (
    SlotFiller,
    SlotBundle,
    GenericSlotFiller,
)

if TYPE_CHECKING:
    from core.orchestration.graph_engine import GraphPlugin


@dataclass
class ComposerResult:
    """
    Result from the compose operation.
    
    This is the standardized output that compose_node produces,
    combining generic response fields with domain-specific data.
    """
    # Response action
    action: str = "answer"  # "answer", "clarify", "info", "error"
    
    # Core response fields
    narrative: str = ""
    conversation_type: str = "conversational"
    
    # Slot-filling fields
    needed_slots: List[str] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)
    
    # Domain-specific fields (from ResponseFormatter)
    domain_data: Dict[str, Any] = field(default_factory=dict)
    
    # Explainability (multi-level)
    explainability: Dict[str, Any] = field(default_factory=dict)
    
    # UX metadata (emotion, language, cultural context)
    ux_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Entity tracking
    entity_ids: List[str] = field(default_factory=list)
    
    # Semantic/fallback flags
    semantic_fallback: bool = False
    
    # User context
    user_id: Optional[str] = None
    
    # Raw output for debugging/advanced use
    raw_output: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for graph state."""
        result = {
            "action": self.action,
            "narrative": self.narrative,
            "conversation_type": self.conversation_type,
            "needed_slots": self.needed_slots,
            "questions": self.questions,
            "semantic_fallback": self.semantic_fallback,
            "proposed_changes": [],  # Preserved for compatibility
            "explainability": self.explainability,
            "entity_ids": self.entity_ids,
        }
        
        # Add optional fields if present
        if self.user_id:
            result["user_id"] = self.user_id
        if self.domain_data:
            result.update(self.domain_data)
        if self.ux_metadata:
            result["_ux_metadata"] = self.ux_metadata
        if self.raw_output:
            result["raw_output"] = self.raw_output
            
        return result


class BaseComposer(ABC):
    """
    Base class for response composition.
    
    Coordinates between domain-specific ResponseFormatter and SlotFiller
    while handling generic concerns (language, emotion, UX).
    
    The composition pipeline:
    1. Merge slots from state
    2. Check for slot-filling needs (via SlotFiller)
    3. Handle conversational routing (non-entity queries)
    4. Detect conversation type (via ResponseFormatter)
    5. Format response (via ResponseFormatter)
    6. Inject UX metadata
    
    Subclasses can override individual steps while using the base flow.
    """
    
    def __init__(
        self,
        response_formatter: Optional[ResponseFormatter] = None,
        slot_filler: Optional[SlotFiller] = None,
    ):
        """
        Initialize the composer.
        
        Args:
            response_formatter: Domain-specific response formatter
            slot_filler: Domain-specific slot filler
        """
        self.response_formatter = response_formatter or GenericResponseFormatter()
        self.slot_filler = slot_filler or GenericSlotFiller()
    
    @classmethod
    def from_plugin(cls, plugin: "GraphPlugin") -> "BaseComposer":
        """
        Create a composer from a GraphPlugin.
        
        Args:
            plugin: The domain plugin
            
        Returns:
            Configured BaseComposer (or subclass)
        """
        # Try to get formatter and filler from plugin
        formatter = None
        filler = None
        
        if hasattr(plugin, "get_response_formatter"):
            formatter = plugin.get_response_formatter()
        if hasattr(plugin, "get_slot_filler"):
            filler = plugin.get_slot_filler()
        
        return cls(response_formatter=formatter, slot_filler=filler)
    
    def compose(
        self,
        state: Dict[str, Any],
        raw_output: Optional[Dict[str, Any]] = None,
    ) -> ComposerResult:
        """
        Main composition method.
        
        Args:
            state: Current graph state
            raw_output: Optional raw output from domain engine
            
        Returns:
            ComposerResult with the composed response
        """
        # Extract common fields
        language = self._get_language(state)
        entity_ids = state.get("entity_ids", [])
        intent = state.get("intent", "")
        user_id = state.get("user_id")
        
        # 1. Merge slots
        merged_slots = self._merge_slots(state)
        
        # 2. Check for missing slots
        missing_slots = self.slot_filler.check_missing_slots(merged_slots, intent)
        if missing_slots:
            return self._compose_slot_filling(missing_slots, language, state, user_id)
        
        # 3. Detect conversation type
        conversation_type = self.response_formatter.detect_conversation_type(
            state, raw_output
        )
        
        # 4. Format based on conversation type
        formatted = self._format_by_type(
            conversation_type,
            entity_ids,
            raw_output,
            language,
            state,
        )
        
        # 5. Build result with UX metadata
        return self._build_result(
            formatted,
            state,
            entity_ids,
            user_id,
            raw_output,
        )
    
    def _merge_slots(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge slots from various state fields.
        
        Override this to customize slot merging for your domain.
        """
        slots = state.get("slots", {})
        return {**slots}
    
    def _get_language(self, state: Dict[str, Any]) -> str:
        """
        Get the language from state.
        
        Defaults to English if not set.
        """
        return state.get("detected_language") or state.get("language") or "en"
    
    def _compose_slot_filling(
        self,
        missing_slots: List[str],
        language: str,
        state: Dict[str, Any],
        user_id: Optional[str],
    ) -> ComposerResult:
        """
        Compose a slot-filling response.
        """
        bundle = self.slot_filler.generate_bundled_questions(
            missing_slots, language, state
        )
        
        return ComposerResult(
            action="clarify",
            narrative=bundle.bundled_question,
            conversation_type=ConversationType.SLOT_FILLING.value,
            needed_slots=missing_slots,
            questions=[bundle.bundled_question],
            semantic_fallback=True,
            explainability={
                "simple": f"Missing slots: {', '.join(missing_slots)}",
                "technical": f"Slot filling for intent: {state.get('intent')}",
                "detailed": bundle.chain_of_thought or "",
            },
            user_id=user_id,
        )
    
    def _format_by_type(
        self,
        conversation_type: ConversationType,
        entity_ids: List[str],
        raw_output: Optional[Dict[str, Any]],
        language: str,
        state: Dict[str, Any],
    ) -> FormattedResponse:
        """
        Dispatch to the appropriate formatter method.
        """
        if conversation_type == ConversationType.SINGLE_ENTITY:
            entity_id = entity_ids[0] if entity_ids else ""
            entity_data = self._extract_entity_data(entity_id, raw_output)
            return self.response_formatter.format_single_entity(
                entity_id, entity_data, language, state
            )
        
        elif conversation_type == ConversationType.MULTI_ENTITY:
            return self.response_formatter.format_multi_entity(
                entity_ids, raw_output or {}, language, state
            )
        
        elif conversation_type == ConversationType.ONBOARDING:
            return self.response_formatter.format_onboarding(language, state)
        
        elif conversation_type == ConversationType.NO_DATA:
            return self.response_formatter.format_no_data(language, state)
        
        elif conversation_type == ConversationType.ERROR:
            return self.response_formatter.format_error(
                Exception("Unknown error"), language, state
            )
        
        else:
            # Conversational or unknown - return basic response
            return FormattedResponse(
                conversation_type=conversation_type,
                narrative=state.get("summary", ""),
            )
    
    def _extract_entity_data(
        self,
        entity_id: str,
        raw_output: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Extract data for a specific entity from raw output.
        
        Override this for domain-specific extraction.
        """
        if not raw_output:
            return {}
        
        ranking = raw_output.get("ranking", {})
        for group in ["entities", "etf", "funds", "items"]:
            items = ranking.get(group, [])
            for item in items:
                if item.get("entity_id") == entity_id:
                    return item
        
        return {}
    
    def _build_result(
        self,
        formatted: FormattedResponse,
        state: Dict[str, Any],
        entity_ids: List[str],
        user_id: Optional[str],
        raw_output: Optional[Dict[str, Any]],
    ) -> ComposerResult:
        """
        Build the final ComposerResult from formatted response.
        """
        # Collect UX metadata
        ux_metadata = {
            "emotion_detected": state.get("emotion_detected"),
            "emotion_confidence": state.get("emotion_confidence"),
            "emotion_intensity": state.get("emotion_intensity"),
            "cultural_context": state.get("cultural_context"),
            "detected_language": state.get("detected_language"),
        }
        
        # Build domain data from formatted response
        domain_data = formatted.domain_data.copy()
        if formatted.verdict:
            domain_data["final_verdict"] = formatted.verdict
        if formatted.gauge:
            domain_data["gauge"] = formatted.gauge
        if formatted.comparison_matrix:
            domain_data["comparison_matrix"] = formatted.comparison_matrix
        if formatted.cards:
            domain_data["onboarding_cards"] = formatted.cards
        
        return ComposerResult(
            action="answer",
            narrative=formatted.narrative,
            conversation_type=formatted.conversation_type.value if isinstance(formatted.conversation_type, ConversationType) else str(formatted.conversation_type),
            entity_ids=entity_ids,
            domain_data=domain_data,
            ux_metadata=ux_metadata,
            user_id=user_id,
            raw_output=raw_output,
            explainability={
                "simple": formatted.narrative[:200] if formatted.narrative else "",
                "technical": f"Conversation type: {formatted.conversation_type}",
                "detailed": raw_output if raw_output else {},
            },
        )


class GenericComposer(BaseComposer):
    """
    Generic composer using GenericResponseFormatter and GenericSlotFiller.
    
    Used when no domain plugin is registered.
    """
    
    def __init__(self):
        super().__init__(
            response_formatter=GenericResponseFormatter(),
            slot_filler=GenericSlotFiller(),
        )
