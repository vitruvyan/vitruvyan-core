"""
Vitruvyan Core — Parser ABC & Context Detection
================================================

Abstract base class for domain-specific parsing of user input.
The Parser is responsible for extracting domain-specific slots from user input.

Hierarchy:
---------
- Parser (ABC) - defines contract for parsing user input
- BaseParser - provides common utilities (contextual detection, slot merging)
- FinanceParser - extracts budget, horizon, tickers (in finance vertical)
- SupportParser - extracts urgency, category, priority (in support vertical)

Design Philosophy:
-----------------
- Language parsing is PERCEPTION responsibility (Sacred Order)
- Intent detection is delegated to intent_detection_node (LLM-first)
- Entity extraction is delegated to entity_resolver_node (LLM-first)
- Parser focuses on DOMAIN SLOTS (budget, horizon, etc)

Author: Vitruvyan Core Team
Created: February 10, 2026
Status: PRODUCTION
"""

import re
import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ===========================================================================
# DATA CLASSES
# ===========================================================================

@dataclass
class ParsedSlots:
    """
    Container for parsed slots from user input.
    
    Domain-agnostic fields:
    - input_text: Original user input (always preserved)
    - context_entities: Entities from context (fallback for entity_resolver)
    - semantic_matches: Qdrant matches from semantic_grounding_node
    - is_contextual: Whether query references previous context
    
    Domain-specific fields are in slots dict:
    - Finance: budget, horizon, companies
    - Support: urgency, category, priority
    - Custom domains add their own slots
    """
    input_text: str
    context_entities: List[str] = field(default_factory=list)
    semantic_matches: List[Dict[str, Any]] = field(default_factory=list)
    is_contextual: bool = False
    slots: Dict[str, Any] = field(default_factory=dict)
    
    def to_state_update(self) -> Dict[str, Any]:
        """Convert parsed slots to state dict update."""
        update = {
            "input_text": self.input_text,
            "context_entities": self.context_entities,
            "semantic_matches": self.semantic_matches,
            "is_contextual": self.is_contextual,
        }
        update.update(self.slots)
        return update


# ===========================================================================
# ABSTRACT BASE CLASS
# ===========================================================================

class Parser(ABC):
    """
    Abstract base class for domain-specific input parsing.
    
    Implement this in your domain to extract domain-specific slots
    from user input. The parser is called early in the graph to
    populate state fields for downstream nodes.
    
    Example implementation:
    
        class FinanceParser(Parser):
            def extract_slots(self, text: str, language: str = "auto") -> Dict[str, Any]:
                return {
                    "budget": self._extract_budget(text),
                    "horizon": self._extract_horizon(text),
                    "companies": self._extract_companies(text),
                }
                
            def validate_entity(self, entity_id: str) -> bool:
                return self._is_valid_ticker(entity_id)
    """
    
    @abstractmethod
    def extract_slots(self, text: str, language: str = "auto") -> Dict[str, Any]:
        """
        Extract domain-specific slots from user input.
        
        Args:
            text: User input text (raw)
            language: ISO 639-1 language code or "auto" for detection
            
        Returns:
            Dict of slot_name → value (e.g., {"budget": 5000, "horizon": "medium"})
        """
        ...
    
    @abstractmethod
    def validate_entity(self, entity_id: str) -> bool:
        """
        Validate if an entity ID exists in the domain's data store.
        
        Args:
            entity_id: Entity identifier to validate
            
        Returns:
            True if entity exists, False otherwise
        """
        ...
    
    def get_company_map(self) -> Dict[str, str]:
        """
        Return mapping of company names to entity IDs.
        
        Override in domain to provide entity resolution.
        Default returns empty dict (no resolution).
        
        Returns:
            Dict[company_name → entity_id] (lowercase keys)
        """
        return {}


# ===========================================================================
# BASE IMPLEMENTATION (common utilities)
# ===========================================================================

class BaseParser(Parser):
    """
    Base parser implementation with common utilities.
    
    Provides:
    - Contextual reference detection (LLM-first with fallback)
    - Vague query detection (heuristics)
    - Slot merging from semantic history
    
    Subclasses must implement:
    - extract_slots(): domain-specific slot extraction
    - validate_entity(): domain-specific entity validation
    """
    
    def detect_contextual_reference(self, text: str) -> bool:
        """
        Detect if query references previous context.
        
        Uses GPT-3.5 for semantic understanding with heuristic fallback.
        This is domain-agnostic (language patterns, not domain concepts).
        
        Examples:
        - "come prima ma con ENTITY_1" → True
        - "What about ENTITY_2?" → True
        - "Analyze ENTITY_3" → False
        
        Returns:
            True if contextual reference detected
        """
        if not text or len(text.strip()) < 3:
            return False
        
        txt_lower = text.lower()
        
        # Quick heuristic: Very short queries with follow-up markers
        follow_up_markers = ['e ', 'and ', 'what ', 'how ', 'vs ', 'anche']
        if len(text.strip()) < 15 and any(word in txt_lower for word in follow_up_markers):
            return True
        
        # Use GPT-3.5 for semantic detection (fast + accurate)
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            prompt = f"""Does this query refer to previous context or is it a follow-up question?

Query: "{text}"

Answer ONLY "yes" or "no".

Examples:
- "E ENTITY_1?" → yes (follow-up)
- "E se lo confronto con Microsoft?" → yes (comparison to previous)
- "Analyze ENTITY_2" → no (standalone)
- "what about Tesla?" → yes (follow-up)
- "come prima ma con ENTITY_3" → yes (explicit reference)
- "Quali sono i migliori titoli tech?" → no (standalone)

Answer:"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0.0
            )
            
            answer = response.choices[0].message.content.strip().lower()
            is_contextual = answer.startswith("yes") or answer.startswith("sì") or answer.startswith("si")
            
            logger.info(f"🤖 [Contextual Detection] Query: '{text[:50]}...' → {answer}")
            return is_contextual
            
        except Exception as e:
            logger.warning(f"⚠️ [Contextual Detection] LLM failed, using heuristic: {e}")
            # Fallback: Simple heuristic
            return any(word in txt_lower for word in [
                'come prima', 'stesso', 'anche', 'e se', 'confronto', 
                'rispetto', 'what about', 'how about', 'compared to'
            ])
    
    def detect_vague_query(self, text: str) -> bool:
        """
        Detect vague queries where entity extraction may have failed.
        
        Examples:
        - "E ENTITY_1?" → True (Italian conjunction + entity)
        - "What about ENTITY_2?" → True
        - "ENTITY_3?" → True (solo entity)
        
        Returns:
            True if query looks vague but has clear entity intent
        """
        if not text:
            return False
        
        txt = text.strip().lower()
        
        patterns = [
            r"^\s*e\s+\w+",           # "E EXAMPLE?" (Italian conjunction)
            r"what about",            # "What about Example?"
            r"how about",             # "How about Example?"
            r"come prima",            # "Come prima ma con EXAMPLE"
            r"anche\s+\w+",           # "anche EXAMPLE"
            r"^\s*[A-Z]{2,5}\s*\??$"  # Solo entity_id: "EXAMPLE?"
        ]
        return any(re.search(p, txt, re.IGNORECASE) for p in patterns)
    
    def extract_entity_from_vague_query(self, text: str) -> List[str]:
        """
        Extract entity ID from vague query when main extraction fails.
        
        Returns:
            List of entity IDs (usually 1, or empty if extraction fails)
        """
        if not text:
            return []
        
        # Pattern 1: "E ENTITY?" or "What about ENTITY?"
        m = re.search(r"\b(e|and|what about|how about|anche)\s+([A-Z]{1,10})\b", text, re.IGNORECASE)
        if m:
            potential = m.group(2).upper()
            if self.validate_entity(potential):
                return [potential]
        
        # Pattern 2: Solo entity "EXAMPLE?"
        m = re.search(r"^([A-Z]{1,10})\??$", text.strip())
        if m:
            potential = m.group(1).upper()
            if self.validate_entity(potential):
                return [potential]
        
        # Pattern 3: Company name extraction via get_company_map()
        company_map = self.get_company_map()
        for company, entity_id in company_map.items():
            if company in text.lower():
                if self.validate_entity(entity_id):
                    return [entity_id]
        
        return []
    
    def merge_slots_from_context(
        self,
        current_slots: Dict[str, Any],
        context_slots: Dict[str, Any],
        history_slots: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge slots with priority: current > context > history.
        
        Args:
            current_slots: Slots extracted from current input
            context_slots: Slots from contextual reference (if query is follow-up)
            history_slots: Slots from semantic history (last conversation)
            
        Returns:
            Merged slots dict
        """
        merged = {}
        
        # Get all possible slot keys
        all_keys = set(current_slots.keys()) | set(context_slots.keys()) | set(history_slots.keys())
        
        for key in all_keys:
            # Priority: current > context > history
            value = current_slots.get(key) or context_slots.get(key) or history_slots.get(key)
            if value is not None:
                merged[key] = value
        
        return merged
    
    def parse(self, state: Dict[str, Any]) -> ParsedSlots:
        """
        Main parsing entrypoint.
        
        Orchestrates:
        1. Extract domain-specific slots from input
        2. Detect contextual references
        3. Merge with semantic history
        4. Handle vague query resolution
        
        Args:
            state: Current graph state
            
        Returns:
            ParsedSlots with all extracted data
        """
        user_input = state.get("input_text", "")
        semantic_matches = state.get("semantic_matches", [])
        
        # 1. Extract domain-specific slots
        language = state.get("language", "auto")
        current_slots = self.extract_slots(user_input, language)
        
        # 2. Detect contextual reference
        is_contextual = self.detect_contextual_reference(user_input)
        
        # 3. Get context from semantic history
        context_slots = {}
        history_slots = {}
        
        if semantic_matches:
            history_slots = semantic_matches[0]  # Most similar = first
            if is_contextual:
                context_slots = history_slots
        
        # 4. Merge slots
        merged_slots = self.merge_slots_from_context(
            current_slots, context_slots, history_slots
        )
        
        # 5. Handle vague query resolution
        context_entities = context_slots.get("entity_ids", []) or history_slots.get("entity_ids", [])
        
        if self.detect_vague_query(user_input):
            vague_entities = self.extract_entity_from_vague_query(user_input)
            if vague_entities:
                context_entities = vague_entities
        
        return ParsedSlots(
            input_text=user_input,
            context_entities=context_entities,
            semantic_matches=semantic_matches,
            is_contextual=is_contextual,
            slots=merged_slots,
        )


# ===========================================================================
# GENERIC (NO-OP) PARSER
# ===========================================================================

class GenericParser(BaseParser):
    """
    Generic parser that extracts no domain-specific slots.
    
    Use this as a placeholder when no domain-specific parsing is needed,
    or as a fallback when no domain plugin is configured.
    """
    
    def extract_slots(self, text: str, language: str = "auto") -> Dict[str, Any]:
        """No domain-specific slots to extract."""
        return {}
    
    def validate_entity(self, entity_id: str) -> bool:
        """No entity validation in generic parser."""
        return True


# ===========================================================================
# EXPORTS
# ===========================================================================

__all__ = [
    "Parser",
    "BaseParser",
    "GenericParser",
    "ParsedSlots",
]
